"""Offline diagnostics on the frozen package; never changes gold or model output."""
import io
import json
import math
from pathlib import Path
import statistics
import zipfile

import matplotlib
matplotlib.use("Agg")
from matplotlib.path import Path as PolygonPath
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
gold = json.loads((HERE / "gold_snapshot.json").read_text())
review = json.loads((HERE / "review_snapshot.json").read_text())
labels = {r["event_id"]: r for r in gold["annotations"]}
with zipfile.ZipFile(HERE / "input.zip") as archive:
    background = Image.open(io.BytesIO(archive.read("map.png"))).convert("RGB")
    tasks = [json.loads(s) for s in archive.read("tasks.jsonl").decode().splitlines()]


def point_distance(point, geom):
    if geom["type"] == "point":
        return math.dist(point, geom["coordinates"][0])
    coords = geom["coordinates"]
    vertices = coords + coords[:1] if geom["type"] == "polygon" else coords
    distances = []
    p = np.asarray(point, dtype=float)
    for a, b in zip(vertices, vertices[1:]):
        a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        v = b - a
        t = np.clip(np.dot(p-a, v) / np.dot(v, v), 0, 1) if np.dot(v, v) else 0
        distances.append(float(np.linalg.norm(p - a - t*v)))
    distance = min(distances)
    if geom["type"] == "polygon" and (PolygonPath(vertices).contains_point(point) or distance < 1e-9):
        return 0.0
    return distance


def measure(ann, prediction):
    g = ann["geometry"]
    if prediction is None:
        return {"abstained": True}
    if prediction["type"] == "point":
        distance = point_distance(prediction["coordinates"][0], g)
        result = {"distance_to_gold_px": distance,
                  "distance_fraction_of_diagonal": distance / math.hypot(*background.size)}
        if g["type"] == "polygon":
            result["point_inside_gold"] = distance == 0
        else:
            result["within_saved_tolerance"] = distance <= ann["tolerance_px"]
        return result
    if g["type"] == prediction["type"] == "polygon":
        masks = []
        for geom in (g, prediction):
            im = Image.new("1", background.size)
            ImageDraw.Draw(im).polygon([tuple(p) for p in geom["coordinates"]], fill=1)
            masks.append(np.asarray(im, dtype=bool))
        union = np.count_nonzero(masks[0] | masks[1])
        return {"raster_iou_diagnostic": float(np.count_nonzero(masks[0] & masks[1]) / union) if union else None}
    return {"unscored_geometry_pair": [g["type"], prediction["type"]]}


def draw_geometry(image, geom, color):
    if not geom:
        return
    d = ImageDraw.Draw(image)
    pts = [tuple(p) for p in geom["coordinates"]]
    if geom["type"] == "point":
        x, y = pts[0]
        d.line([(x-12, y), (x+12, y)], fill=color, width=5)
        d.line([(x, y-12), (x, y+12)], fill=color, width=5)
    else:
        d.line(pts + pts[:1] if geom["type"] == "polygon" else pts, fill=color, width=5)


# Sanity cases prevent accidental closed-line distances and boundary exclusion.
assert point_distance([3, 4], {"type": "point", "coordinates": [[0, 0]]}) == 5
assert point_distance([5, 5], {"type": "line", "coordinates": [[0, 0], [10, 0], [10, 10]]}) == 5
assert point_distance([0, 5], {"type": "polygon", "coordinates": [[0, 0], [10, 0], [10, 10], [0, 10]]}) == 0

runs = {}
diagnostics = {}
for key in ("gpt5", "qwen3vl8b"):
    run = json.loads((HERE / key / "predictions.json").read_text())
    assert run["map_version"] == gold["map"]["version"]
    runs[key] = run
    predictions = {r["event_id"]: r for r in run["predictions"]}
    attempts = [json.loads(s) for s in (HERE / key / "predictions.attempts.jsonl").read_text().splitlines()]
    assert {a["event_id"] for a in attempts} == set(labels)
    assert len(attempts) == len(tasks)
    expected_tasks = {t["event_id"]: t for t in tasks}
    for attempt in attempts:
        assert attempt["image_sha256"] == gold["map"]["image_sha256"]
        assert attempt["task"] == expected_tasks[attempt["event_id"]]
    rows = []
    for task in tasks:
        eid = task["event_id"]
        ann = labels[eid]
        row = {"event_id": eid, "gold_status": ann["status"],
               "gold_type": ann["geometry"]["type"] if ann["geometry"] else None}
        if eid not in predictions:
            row["call_or_parse_error"] = True
        else:
            p = predictions[eid]["geometry"]
            row["prediction_type"] = p["type"] if p else None
            if ann["status"] == "outside_map":
                row["outside_map_abstention"] = p is None
            elif eid in review["exclude_from_spatial_summary"]:
                row["excluded_reason"] = review["exclude_from_spatial_summary"][eid]
            elif ann["status"] == "accepted":
                row.update(measure(ann, p))
        rows.append(row)
    points = [r["distance_to_gold_px"] for r in rows if r["gold_type"] == "point" and "distance_to_gold_px" in r]
    polys = [r for r in rows if "point_inside_gold" in r]
    diagnostics[key] = {"model": run["model"], "rows": rows, "errors": run["errors"],
        "summary": {"attempts": len(attempts), "valid_geometry": sum(p["geometry"] is not None for p in predictions.values()),
                    "abstained": sum(p["geometry"] is None for p in predictions.values()),
                    "point_gold_count": len(points),
                    "point_gold_mean_px": statistics.mean(points) if points else None,
                    "point_gold_median_px": statistics.median(points) if points else None,
                    "point_in_polygon_count": len(polys), "point_in_polygon_hits": sum(r["point_inside_gold"] for r in polys),
                    "elapsed_inference_seconds": sum(a["elapsed_seconds"] for a in attempts)},
        "usage": {k: sum((a.get("usage") or {}).get(k, 0) for a in attempts)
                  for k in ("input_tokens", "output_tokens", "total_tokens")}}

for task in tasks:
    eid = task["event_id"]
    panels = []
    for key, color in (("gpt5", "#287be0"), ("qwen3vl8b", "#16805d")):
        image = background.copy()
        draw_geometry(image, labels[eid]["geometry"], "#cf3f49")
        pred = next((r for r in runs[key]["predictions"] if r["event_id"] == eid), None)
        if pred:
            draw_geometry(image, pred["geometry"], color)
        image.thumbnail((690, 790))
        panel = Image.new("RGB", (710, 850), "white")
        panel.paste(image, (10, 55))
        label = "ERROR" if pred is None else "abstained" if pred["geometry"] is None else pred["geometry"]["type"]
        ImageDraw.Draw(panel).text((10, 8), f"{eid} | {runs[key]['model']} | {label}", fill="black")
        ImageDraw.Draw(panel).text((10, 26), "Red = saved human label; model = blue / green", fill="black")
        if eid == "Z0010":
            ImageDraw.Draw(panel).text((10, 40), "GOLD TARGET MISMATCH: excluded from spatial scoring", fill="red")
        panels.append(panel)
    combined = Image.new("RGB", (1420, 850), "white")
    for x, panel in enumerate(panels):
        combined.paste(panel, (x*710, 0))
    combined.save(HERE / f"{eid}_comparison.png")

(HERE / "diagnostics.json").write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2) + "\n")
lines = ["# 苏黎世十条候选：GPT-5 / Qwen3-VL 验证", "",
         "本轮是相对人工快照的诊断，不是经过独立验收的 benchmark 精度。", "",
         "## 配置", "",
         f"- 底图版本：`{gold['map']['version']}`；尺寸 {background.width} × {background.height} px。",
         f"- 图片 SHA-256：`{gold['map']['image_sha256']}`。",
         "- 两模型使用同一个 input.zip，含全部十条；与网页默认的 accepted-only 导出不同，另纳入 Z0003 图外拒答对照。",
         "- 模型只收到干净 PNG、英文正文、问题和像素坐标规则；人工答案、审核状态、排除理由及作战图没有发送。",
         "- GPT-5：Responses API，最多 4096 输出 token（含推理），超时 120 秒，不自动重试；调用参数沿用上一轮。",
         "- Qwen/Qwen3-VL-8B-Instruct：本机缓存，Transformers / MPS float16，greedy，最多 4096 新 token。",
         "- 英文翻译及历史定位尚待独立复核；不把同图十条看成十张独立地图。", "",
         "## 执行结果", "",
         "有效几何只表示格式、顶点及图像边界校验通过，不表示位置正确。", "",
         "| 模型 | 请求 | 有效几何 | 拒答 | 调用/解析/几何错误 |", "|---|---:|---:|---:|---:|"]
for key, diagnostic in diagnostics.items():
    s = diagnostic["summary"]
    lines.append(f"| {diagnostic['model']} | {s['attempts']} | {s['valid_geometry']} | {s['abstained']} | {len(diagnostic['errors'])} |")
lines += ["", "## 逐条诊断", "", "距离单位均为原图像素；不同几何类型不合并成一个准确率。",
          "Z0010 在查看模型结果之前已标记为人工目标不匹配，从空间汇总中排除。", "",
          "| ID | 人工标注 | GPT-5 | Qwen3-VL |", "|---|---|---|---|"]


def cell(row):
    if row.get("call_or_parse_error"):
        return "无效输出/生成失败"
    if "outside_map_abstention" in row:
        return "正确拒答" if row["outside_map_abstention"] else "图外仍给出坐标"
    if "excluded_reason" in row:
        return "已运行；人工目标不匹配，不评分"
    if row.get("abstained"):
        return "拒答"
    if "distance_to_gold_px" in row:
        prefix = "区域内" if row.get("point_inside_gold") else "区域外" if "point_inside_gold" in row else "距人工点"
        return f"{prefix} {row['distance_to_gold_px']:.1f} px"
    if "raster_iou_diagnostic" in row:
        return f"区域 IoU {row['raster_iou_diagnostic']:.3f}"
    return "几何类型不同，暂不评分"


for i, task in enumerate(tasks):
    eid = task["event_id"]
    ann = labels[eid]
    kind = ann["geometry"]["type"] if ann["geometry"] else ann["status"]
    lines.append(f"| {eid} | {kind} | {cell(diagnostics['gpt5']['rows'][i])} | {cell(diagnostics['qwen3vl8b']['rows'][i])} |")
lines += ["", "## 汇总和限制", ""]
for key, d in diagnostics.items():
    s = d["summary"]
    if s["point_gold_count"]:
        lines.append(f"- {d['model']}：有效点对点 n={s['point_gold_count']}，均值 {s['point_gold_mean_px']:.1f} px，中位数 {s['point_gold_median_px']:.1f} px。失败/拒答不记为零距离。")
    lines.append(f"- {d['model']}：点落入人工区域 {s['point_in_polygon_hits']}/{s['point_in_polygon_count']}；这是点对区域诊断，不是区域 IoU。")
common = [i for i in range(len(tasks)) if all(d["rows"][i].get("gold_type") == "point" and "distance_to_gold_px" in d["rows"][i] for d in diagnostics.values())]
if common:
    ids = ", ".join(tasks[i]["event_id"] for i in common)
    lines += [f"- 两模型都有效的共同点样本（{ids}，n={len(common)}）："]
    for d in diagnostics.values():
        values = [d["rows"][i]["distance_to_gold_px"] for i in common]
        lines.append(f"  {d['model']} 平均 {statistics.mean(values):.1f} px，中位数 {statistics.median(values):.1f} px。此项仅比较成功返回点的交集，存在成功样本筛选偏差。")
lines += ["- 点/线容差全部为 0 px，未设事后阈值，也未使用旧 500 米标准；不报告混合几何总准确率。",
          "- Z0010 问的是 Korsakoff 调动后在利马特河另一侧的城区；当前证据/线条描述 Durasof 的撤退道路，需独立重标。",
          "- Z0009 问道路路段，人工真值却是单点；其点距离仅供排查，不足以验证完整道路定位。",
          "- Z0002 的防守林地与高地、Z0001/Z0006 的接收岸/出发岸仍建议复核；本轮没有替用户改标注。",
          "- 本轮底图、裁切和人工答案不同于五条版本，不能直接把数值变化解释为模型能力变化。", "",
          "## 错误与使用量", ""]
for key, d in diagnostics.items():
    attempts = [json.loads(s) for s in (HERE / key / "predictions.attempts.jsonl").read_text().splitlines()]
    for a in attempts:
        if a["status"] == "error":
            u = a.get("usage") or {}
            note = ""
            if not a.get("raw") and (u.get("output_tokens_details") or {}).get("reasoning_tokens") == a["max_output_tokens"]:
                note = "；输出预算全部用于推理，未返回可解析答案"
            elif a.get("error_type") == "ValueError":
                note = "；请对照原始响应检查几何有效性/越界，不裁剪或缩放修正"
            lines.append(f"- {d['model']} {a['event_id']}：{a['error_type']}{note}。")
    lines.append(f"- {d['model']} token：input={d['usage']['input_tokens']}，output={d['usage']['output_tokens']}，total={d['usage']['total_tokens']}。")
lines += ["", "token 用量不等于账单金额。Qwen 离线推理未调用付费 API。", "",
          "## 文件", "",
          "- [冻结输入包](input.zip)、[人工答案快照](gold_snapshot.json)、[运行前审核说明](review_snapshot.json)。",
          "- [GPT-5 预测](gpt5/predictions.json)、[原始响应](gpt5/predictions.attempts.jsonl)。",
          "- [Qwen 预测](qwen3vl8b/predictions.json)、[原始响应](qwen3vl8b/predictions.attempts.jsonl)。",
          "- [逐项诊断 JSON](diagnostics.json)。",
          "- 对照图：左 GPT-5 蓝色，右 Qwen 绿色，红色为保存的人工答案；无效输出不绘制成有效标注。"]
lines.extend(f"- [{t['event_id']} 对照图]({t['event_id']}_comparison.png)" for t in tasks)
lines += ["", "## 离线重算", "", "```bash",
          "MPLCONFIGDIR=/tmp/hegrounding-mpl .venv/bin/python benchmark/atlas/runs/zurich10_20260916_162847/inspect_run.py",
          "```", "", "此命令仅重建诊断报告与对照图，不调用模型，不改人工标注。"]
(HERE / "RESULTS.md").write_text("\n".join(lines) + "\n")
print(json.dumps(diagnostics, ensure_ascii=False, indent=2))
