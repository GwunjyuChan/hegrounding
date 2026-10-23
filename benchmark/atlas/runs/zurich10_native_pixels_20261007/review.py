"""Score completed native-pixel results against the historical frozen gold, never used by inference."""
import io
import json
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
from PIL import Image, ImageDraw
from compare_grounding_methods import diagnose, draw_geometry, cell, costs
from run_atlas_vlm import read_package, digest


def load(path):
    return json.loads(path.read_text())


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


previous = HERE.parent / "zurich10_20260916_162847"
manifest, png, tasks, instruction = read_package(HERE / "input.zip")
config = load(HERE / "manifest.json")
gold_path = previous / "gold_snapshot.json"
gold = load(gold_path)
assert gold["map"]["version"] == manifest["map_version"]
assert gold["map"]["image_sha256"] == manifest["image_sha256"]
assert digest((HERE / "input.zip").read_bytes()) == digest((previous / "input.zip").read_bytes())
labels = {a["event_id"]: a for a in gold["annotations"]}
excluded = set(config["spatial_exclusions_declared_before_run"])
expected = {t["event_id"]: t for t in tasks}
results, summaries, attempts_by_method = {}, {}, {}
for method, directory in (("baseline", previous / "qwen3vl8b"), ("native_pixels", HERE)):
    result = load(directory / "predictions.json")
    attempts = jsonl(directory / "predictions.attempts.jsonl")
    assert len(attempts) == 10 and {a["event_id"] for a in attempts} == set(expected)
    assert result["map_version"] == manifest["map_version"]
    for a in attempts:
        assert a["image_sha256"] == manifest["image_sha256"]
        assert a["task"] == expected[a["event_id"]]
    if method == "native_pixels":
        for a in attempts:
            assert a["preserve_image_pixels"]
            preprocessing = a["usage"]["image_preprocessing"]
            assert preprocessing["processed_size_wh"] == config["padding"]["canvas_size_wh"]
            assert preprocessing["content_scale_xy"] == [1.0, 1.0]
            assert preprocessing["original_rgb_sha256"] == config["padding"]["original_rgb_sha256"]
            assert preprocessing["canvas_rgb_sha256"] == config["padding"]["canvas_rgb_sha256"]
            assert preprocessing["original_pixels_verified"]
            assert a["local_config"]["model_path"] == config["model_path"]
    predictions = {p["event_id"]: p for p in result["predictions"]}
    errors = {e["event_id"]: e for e in result["errors"]}
    assert set(predictions).isdisjoint(errors)
    assert set(predictions) | set(errors) == set(expected)
    results[method] = {eid: diagnose(labels.get(eid), predictions.get(eid), errors.get(eid), eid in excluded) for eid in expected}
    attempts_by_method[method] = attempts
    points = [d["distance_to_gold_px"] for d in results[method].values() if d["gold_type"] == "point" and "distance_to_gold_px" in d]
    polygons = [d for d in results[method].values() if "point_inside_gold" in d]
    summaries[method] = {"valid": sum(p["geometry"] is not None for p in predictions.values()),
        "abstained": sum(p["geometry"] is None for p in predictions.values()), "errors": len(errors),
        "point_n": len(points), "point_mean_px": statistics.mean(points) if points else None,
        "point_median_px": statistics.median(points) if points else None,
        "point_in_polygon": {"hits": sum(d["point_inside_gold"] for d in polygons), "n": len(polygons)},
        "cost": costs(attempts)}
    for eid in expected:
        results[method][eid]["geometry"] = predictions.get(eid, {}).get("geometry")

for old, new in zip(attempts_by_method["baseline"], attempts_by_method["native_pixels"]):
    assert old["event_id"] == new["event_id"]
    assert old["instruction"] == new["instruction"]
paired = [eid for eid in expected if all(results[m][eid]["gold_type"] == "point" and
          "distance_to_gold_px" in results[m][eid] for m in results)]
pair = {"event_ids": paired, "n": len(paired)}
if paired:
    for m in results:
        distances = [results[m][eid]["distance_to_gold_px"] for eid in paired]
        pair[m] = {"mean_px": statistics.mean(distances), "median_px": statistics.median(distances)}
    differences = [results["native_pixels"][eid]["distance_to_gold_px"] - results["baseline"][eid]["distance_to_gold_px"] for eid in paired]
    pair.update(improved=sum(d < -1e-9 for d in differences), worsened=sum(d > 1e-9 for d in differences), tied=sum(abs(d) <= 1e-9 for d in differences))

out = HERE / "review"
out.mkdir(exist_ok=False)
(out / "gold_snapshot.json").write_bytes(gold_path.read_bytes())
report = {"metrics_kind": "provisional_pixel_diagnostics_not_benchmark_accuracy", "map": manifest,
          "gold_sha256": digest(gold_path.read_bytes()), "excluded": sorted(excluded),
          "summaries": summaries, "paired_point_gold": pair, "rows": results,
          "local_configs": {m: a[0]["local_config"] for m, a in attempts_by_method.items()},
          "preprocessing": attempts_by_method["native_pixels"][0]["usage"]["image_preprocessing"]}
(out / "diagnostics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
background = Image.open(io.BytesIO(png)).convert("RGB")
contact = Image.new("RGB", (1420, 5 * 470), "white")
for index, eid in enumerate(expected):
    comparison = Image.new("RGB", (1420, 870), "white")
    for col, (method, color) in enumerate((("baseline", "#16805d"), ("native_pixels", "#287be0"))):
        layer = background.copy()
        draw_geometry(layer, labels[eid]["geometry"], "#cf3f49")
        draw_geometry(layer, results[method][eid]["geometry"], color)
        layer.thumbnail((690, 780))
        comparison.paste(layer, (10 + col * 710, 65))
        draw = ImageDraw.Draw(comparison)
        draw.text((10 + col * 710, 10), f"{eid} | {method} | {results[method][eid]['status']}", fill="black")
        draw.text((10 + col * 710, 28), "Red: frozen human GT; Green: old; Blue: native pixels", fill="black")
        if eid in excluded:
            draw.text((10 + col * 710, 46), "GT REVIEW NEEDED: excluded from spatial scoring", fill="red")
    comparison.save(out / f"{eid}_comparison.png")
    preview = comparison.copy()
    preview.thumbnail((710, 470))
    contact.paste(preview, ((index % 2) * 710, (index // 2) * 470))
contact.save(out / "all_comparisons.png")
lines = ["# 苏黎世十题：保持底图像素的 Qwen3-VL 重跑", "", "实验日期：2026-10-07。仅本地推理，无付费 API。", "",
    "## 输入与控制", "",
    "- 沿用 9 月 16 日冻结的十题、英文段落、问题、像素提示词、底图和模型缓存，不采用当前网页的新裁切。",
    "- 原图 1538×1754，右侧补白 30 px、底部补白 6 px，画布 1568×1760；原图 RGB 逐字节校验不变。",
    "- 明确设置 do_resize=False，十次处理后的实际尺寸均经日志校验。原点不变，补白区域的输出仍按原图边界拒绝。",
    "- 这里保持的是冻结底图像素，不是恢复原始 PDF/扫描在此前导入或裁切时已丢失的细节。",
    "- 推理不读取 gold。完成后单独用旧人工快照评分；Z0009/Z0010 保留推理但排除主要空间评分，Z0003 单列图外拒答。",
    "- 严格 JSON/几何校验与旧实验一致，不事后猜测坐标制式、缩放坐标或修正答案。", "",
    "## 汇总", "", "| 方法 | 有效几何 | 拒答 | 错误 | 有效点 n | 点误差均值 px | 点误差中位数 px | 点落入区域 | 推理秒数 |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
for m, s in summaries.items():
    mean = f"{s['point_mean_px']:.1f}" if s["point_n"] else "N/A"
    median = f"{s['point_median_px']:.1f}" if s["point_n"] else "N/A"
    poly = s["point_in_polygon"]
    lines.append(f"| {m} | {s['valid']}/10 | {s['abstained']} | {s['errors']} | {s['point_n']} | {mean} | {median} | {poly['hits']}/{poly['n']} | {s['cost']['seconds']:.1f} |")
lines += ["", "有效几何不等于定位正确；不同方法的成功子集可能不同，不把失败记为零误差。", "", "## 逐题", "", "| 事件 | 旧默认预处理 | 保持原像素 | 对比图 |", "|---|---|---|---|"]
for eid in expected:
    lines.append(f"| {eid} | {cell(results['baseline'][eid])} | {cell(results['native_pixels'][eid])} | [{eid}]({eid}_comparison.png) |")
lines += ["", "## 配对点样本", "", f"共同有效点 n={len(paired)}：{', '.join(paired)}。"]
if paired:
    for m in results:
        lines.append(f"- {m}：均值 {pair[m]['mean_px']:.1f} px，中位数 {pair[m]['median_px']:.1f} px。")
    lines.append(f"- 新实验误差更小 {pair['improved']} 条，更大 {pair['worsened']} 条，相同 {pair['tied']} 条。")
lines += ["", "## 本轮解释", "",
    "- 五个共同点样本的平均误差仅从 424.1 降至 418.9 px，约减少 1.2%；并未解决数百像素级错位。",
    "- 有效几何增加的一条是 Z0003：原先输出无效，这次在图外目标上仍给出坐标，不能解释成准确率提升。",
    "- Z0009 连续生成越来越远、明显越界的道路顶点，用满 4096 输出 token 后截断为不完整 JSON；耗时约 357.6 秒。该失败已保留原始回复，未修补为合法答案。",
    "- 模型缓存、MPS/float16、torch 和 transformers 版本与旧记录一致。旧对照实际运行耗时按原始 attempts 重新求和为 189.7 秒，不与另一次两阶段对照的 182.2 秒混用。",
    "- 当前证据不支持把主要定位错误归因于这一轮的轻微 resize，但不排除更大地图或原始扫描到导出底图阶段的分辨率影响。",
    "", "## 限制", "",
    "- 旧对照来自历史运行，没有在今天重新运行默认 resize；软件、设备记录见 diagnostics.json。不能视为严格同期因果实验。",
    "- 原默认预处理仅从 1538×1754 对齐为 1536×1760，没有大幅下采样；本轮测试的是轻微重采样与右/下补白的差异。",
    "- 提示词仍声明原图有效宽高，补白画布略大；因此输入差异不只有是否插值，还包含边界补白。",
    "- 单图十题、暂定 GT 和共同成功子集不足以证明模型普遍提升；人工问题与几何仍需复核。",
    "- 本轮未更新网页图层、当前底图或任何人工记录。导入其他底图版本前必须核对版本，不自动迁移。", "",
    "## 文件", "", "- [完整预测 JSON](../predictions.json)", "- [十次原始响应及预处理日志](../predictions.attempts.jsonl)",
    "- [参数与像素校验](../manifest.json)", "- [保持原像素的模型画布](../model_canvas.png)", "- [结构化诊断](diagnostics.json)",
    "- [所有对比图总览](all_comparisons.png)", "", "图中红色为冻结人工答案；左侧绿色为旧预测，右侧蓝色为本轮预测。对比图为显示而缩小，不是模型输入。", ""]
(out / "RESULTS.md").write_text("\n".join(lines))
print(json.dumps({"summaries": summaries, "paired_points": pair, "report": str(out / "RESULTS.md")}, indent=2))
