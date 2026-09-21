"""Offline direct/two-stage diagnostics; gold never enters model requests."""
from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path
import statistics

from matplotlib.path import Path as PolygonPath
import numpy as np
from PIL import Image, ImageDraw

from atlas_store import digest
from run_atlas_vlm import read_package


def load(path):
    return json.loads(path.read_text())


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def point_distance(point, geometry):
    if geometry["type"] == "point":
        return math.dist(point, geometry["coordinates"][0])
    coords = geometry["coordinates"]
    vertices = coords + coords[:1] if geometry["type"] == "polygon" else coords
    distances = []
    p = np.asarray(point, dtype=float)
    for a, b in zip(vertices, vertices[1:]):
        a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        v = b - a
        denom = np.dot(v, v)
        t = np.clip(np.dot(p-a, v) / denom, 0, 1) if denom else 0
        distances.append(float(np.linalg.norm(p-a-t*v)))
    distance = min(distances)
    if geometry["type"] == "polygon" and (distance < 1e-9 or PolygonPath(vertices).contains_point(point)):
        return 0.0
    return distance


def diagnose(annotation, prediction, error=None, excluded=False):
    row = {"gold_status": annotation["status"] if annotation else "missing",
           "gold_type": annotation["geometry"]["type"] if annotation and annotation["geometry"] else None}
    if error is not None:
        return {**row, "status": "error", "error_type": error["error_type"]}
    if prediction is None:
        return {**row, "status": "missing_output"}
    geometry = prediction["geometry"]
    row.update(status="abstained" if geometry is None else "valid",
               prediction_type=geometry["type"] if geometry else None)
    if excluded:
        return {**row, "excluded_from_spatial_scoring": True}
    if row["gold_status"] == "outside_map":
        return {**row, "outside_map_abstention": geometry is None}
    if row["gold_status"] != "accepted" or geometry is None:
        return row
    if geometry["type"] == "point":
        distance = point_distance(geometry["coordinates"][0], annotation["geometry"])
        row["distance_to_gold_px"] = distance
        if row["gold_type"] == "polygon":
            row["point_inside_gold"] = distance == 0
    else:
        row["unscored_geometry_pair"] = [row["gold_type"], geometry["type"]]
    return row


def costs(attempts):
    return {"calls": sum(not a.get("map_call_skipped", False) for a in attempts),
            "seconds": sum(a["elapsed_seconds"] for a in attempts),
            **{key: sum((a.get("usage") or {}).get(key, 0) for a in attempts)
               for key in ("input_tokens", "output_tokens", "total_tokens")}}


def paired_points(rows):
    common = [r for r in rows if all(r[k].get("gold_type") == "point" and
              "distance_to_gold_px" in r[k] for k in ("direct", "two_stage"))]
    result = {"event_ids": [r["event_id"] for r in common], "n": len(common)}
    if common:
        for key in ("direct", "two_stage"):
            values = [r[key]["distance_to_gold_px"] for r in common]
            result[key] = {"mean_px": statistics.mean(values), "median_px": statistics.median(values)}
        deltas = [r["two_stage"]["distance_to_gold_px"] - r["direct"]["distance_to_gold_px"] for r in common]
        result.update(improved=sum(d < -1e-9 for d in deltas), worsened=sum(d > 1e-9 for d in deltas),
                      tied=sum(abs(d) <= 1e-9 for d in deltas))
    return result


def draw_geometry(image, geometry, color):
    if geometry is None:
        return
    draw = ImageDraw.Draw(image)
    coords = [tuple(p) for p in geometry["coordinates"]]
    if geometry["type"] == "point":
        x, y = coords[0]
        draw.line([(x-12, y), (x+12, y)], fill=color, width=5)
        draw.line([(x, y-12), (x, y+12)], fill=color, width=5)
    else:
        draw.line(coords + coords[:1] if geometry["type"] == "polygon" else coords, fill=color, width=5)


def cell(row):
    if row["status"] in {"error", "missing_output"}:
        return row.get("error_type", "缺少输出")
    if row.get("excluded_from_spatial_scoring"):
        return "已运行，不评分"
    if "outside_map_abstention" in row:
        return "图外拒答" if row["outside_map_abstention"] else "图外仍定位"
    if row["status"] == "abstained":
        return "拒答"
    if "distance_to_gold_px" in row:
        prefix = "区域内" if row.get("point_inside_gold") else "区域外" if "point_inside_gold" in row else "距人工线" if row["gold_type"] == "line" else "距人工点"
        return f"{prefix} {row['distance_to_gold_px']:.1f} px"
    return "几何不同/无可用真值，未评分"


def compare(run_dir, gold_path, excluded):
    if not (run_dir / "completed.json").is_file():
        raise ValueError("Inference has not completed; do not score partial results")
    manifest, png, tasks, _ = read_package(run_dir / "input.zip")
    config = load(run_dir / "manifest.json")
    selected = config["selected_event_ids"]
    tasks = [t for t in tasks if t["event_id"] in selected]
    gold = load(gold_path)
    if (gold["map"]["version"] != manifest["map_version"] or
            gold["map"]["image_sha256"] != manifest["image_sha256"]):
        raise ValueError("Gold and model input map do not match")
    if not set(excluded) <= set(selected):
        raise ValueError("Unknown exclusion ID")
    labels = {a["event_id"]: a for a in gold["annotations"]}
    stage1 = load(run_dir / "stage1/answers.json")
    stage1_attempts = jsonl(run_dir / "stage1/attempts.jsonl")
    predictions, errors, attempts = {}, {}, {}
    summaries = {}
    for method in ("direct", "two_stage"):
        result = load(run_dir / method / "predictions.json")
        assert result["map_version"] == manifest["map_version"]
        predictions[method] = {r["event_id"]: r for r in result["predictions"]}
        errors[method] = {e["event_id"]: e for e in result["errors"]}
        attempts[method] = jsonl(run_dir / method / "attempts.jsonl")
        assert len(attempts[method]) == len(tasks)
        assert {a["event_id"] for a in attempts[method]} == set(selected)
        for a in attempts[method]:
            if not a.get("map_call_skipped"):
                assert a["image_sha256"] == manifest["image_sha256"]
        summaries[method] = {"valid_geometry": sum(p["geometry"] is not None for p in predictions[method].values()),
                             "abstained": sum(p["geometry"] is None for p in predictions[method].values()),
                             "errors": len(errors[method]), "events": len(tasks),
                             "map_cost": costs(attempts[method]),
                             "end_to_end_cost": costs(attempts[method] + (stage1_attempts if method == "two_stage" else []))}
    rows = [{"event_id": t["event_id"], **{m: diagnose(labels.get(t["event_id"]),
             predictions[m].get(t["event_id"]), errors[m].get(t["event_id"]), t["event_id"] in excluded)
             for m in predictions}} for t in tasks]
    for method in summaries:
        poly = [r[method] for r in rows if "point_inside_gold" in r[method]]
        summaries[method]["point_in_polygon"] = {"hits": sum(r["point_inside_gold"] for r in poly), "n": len(poly)}
    result = {"map_version": manifest["map_version"], "excluded_ids": sorted(excluded),
              "gold_sha256": digest(gold_path.read_bytes()), "metrics_kind": "provisional_pixel_diagnostics_not_benchmark_accuracy",
              "rows": rows, "summaries": summaries, "paired_point_gold": paired_points(rows)}
    report_dir = run_dir / "comparison"
    report_dir.mkdir(exist_ok=False)
    (report_dir / "gold_snapshot.json").write_bytes(gold_path.read_bytes())
    (report_dir / "diagnostics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    image = Image.open(io.BytesIO(png)).convert("RGB")
    for t in tasks:
        eid = t["event_id"]
        combined = Image.new("RGB", (1420, 850), "white")
        for i, (method, color) in enumerate((("direct", "#16805d"), ("two_stage", "#9558aa"))):
            layer = image.copy()
            ann = labels.get(eid)
            if ann:
                draw_geometry(layer, ann["geometry"], "#cf3f49")
            p = predictions[method].get(eid)
            if p:
                draw_geometry(layer, p["geometry"], color)
            layer.thumbnail((690, 790))
            combined.paste(layer, (10 + i*710, 55))
            label = "error" if eid in errors[method] else "abstained" if p and p["geometry"] is None else "geometry"
            draw = ImageDraw.Draw(combined)
            draw.text((10+i*710, 8), f"{eid} | Qwen3-VL | {method} | {label}", fill="black")
            draw.text((10+i*710, 26), "Red = saved human; green = direct; purple = two-stage", fill="black")
            if eid in excluded:
                draw.text((10+i*710, 40), "GOLD REVIEW REQUIRED: not spatially scored", fill="red")
        combined.save(report_dir / f"{eid}.png")

    lines = ["# Qwen3-VL：直接定位与两阶段定位", "",
        "## 实验设计", "",
        "- 直接：原文 + 原问题 + 干净底图 → 几何。",
        "- 两阶段：原文 + 原问题 → 地点答案/证据/不确定性；再将这三项 + 原问题 + 同一底图 → 几何。",
        "- 第二步不含完整原文，不共享第一步对话状态；引用证据来自模型输出，不经人工修正。",
        "- 同一本地模型缓存、greedy 解码、图像预处理、定位 prompt 与定位输出预算；交替安排两种方法先后顺序。",
        "- 两阶段多一次调用，并非等计算量对比。原始像素坐标不做缩放纠正，不自动重试。",
        "- 真值只在离线评分进程读取；推理进程不读取人工几何。",
        f"- 底图 `{manifest['map_version']}`；模型 `{config['model']}`；定位上限 {config['map_max_tokens']} token，文本上限 {config['text_max_tokens']} token。", "",
        "## 返回与成本", "", "| 方法 | 有效几何 | 拒答 | 错误 | 调用数 | 总推理耗时（秒） | 总 token |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for method, summary in summaries.items():
        cost = summary["end_to_end_cost"]
        lines.append(f"| {method} | {summary['valid_geometry']}/{len(tasks)} | {summary['abstained']} | {summary['errors']} | {cost['calls']} | {cost['seconds']:.1f} | {cost['total_tokens']} |")
    lines += ["", "耗时不含模型加载/报告绘制；两阶段包含第一步。合法几何不代表位置正确。", "",
              "## 逐条定位诊断", "", "| 事件 | 直接 | 两阶段 |", "|---|---|---|"]
    lines += [f"| {r['event_id']} | {cell(r['direct'])} | {cell(r['two_stage'])} |" for r in rows]
    pair = result["paired_point_gold"]
    lines += ["", "## 配对比较", "", f"共同成功返回点、且人工真值为点的样本：n={pair['n']}，{', '.join(pair['event_ids'])}。"]
    if pair["n"]:
        for method in summaries:
            lines.append(f"- {method}：平均 {pair[method]['mean_px']:.1f} px；中位数 {pair[method]['median_px']:.1f} px。")
        lines.append(f"- 两阶段偏差更小 {pair['improved']} 条，更大 {pair['worsened']} 条，相同 {pair['tied']} 条。")
    for method, summary in summaries.items():
        poly = summary["point_in_polygon"]
        lines.append(f"- {method}：预测点落入人工区域 {poly['hits']}/{poly['n']}（不是多边形 IoU）。")
    lines += ["", "共同成功子集可能有选择偏差，须同时看所有请求的错误/拒答，不能把失败记为零距离。",
              "排除评分事件：" + (", ".join(sorted(excluded)) or "无") + "。", "",
              "排除条目应先复核目标和几何粒度；排除不等于模型错误，具体原因见工作流说明。",
              "范围外条目单独检查拒答；第一步拒答传播到最终输出不等于视觉阶段正确识别了图外地点。",
              "不报告混合几何总准确率或事后挑选命中阈值；点和区域诊断分开，其他几何组合仅展示。",
              "同底图的关联事件和暂定真值不足以证明一般性提升；地图和文本翻译也仍需审核。", "",
              "## 中间地点答案（未经人工修改）", ""]
    for answer in stage1["answers"]:
        lines += [f"### {answer['event_id']}", "", str(answer["answer_location"]), "",
                  "不确定性：" + (answer["uncertainty"] or "未声明"), "", "证据："]
        lines += ["- " + q for q in answer["evidence_quotes"]]
        if answer.get("quote_not_verbatim"):
            lines += ["", "注意：部分引用不是逐字原文，已原样传递，未人工纠正。"]
        lines += ["", "人工审核：待审核", ""]
    lines += ["## 文件", "", "- [结构化诊断](diagnostics.json)、[人工快照](gold_snapshot.json)。",
              "- [直接预测](../direct/predictions.json)、[两阶段预测](../two_stage/predictions.json)。",
              "- [第一步原始回答](../stage1/answers.json)。各阶段 attempts.jsonl 保存实际输入、原始输出、耗时和用量。",
              "- 两份预测 JSON 使用不同方法标签，可分别导入地图集，不覆盖原 Qwen 或 GPT-5 结果。"]
    lines += [f"- [{t['event_id']} 对照图]({t['event_id']}.png)" for t in tasks]
    (report_dir / "RESULTS.md").write_text("\n".join(lines) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--exclude", action="append", default=[])
    args = parser.parse_args()
    result = compare(args.run_dir, args.gold, set(args.exclude))
    print(json.dumps({"summaries": result["summaries"], "paired_point_gold": result["paired_point_gold"]}, indent=2))


if __name__ == "__main__":
    main()
