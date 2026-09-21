"""Compare map inputs visually without inventing cross-map ground truth."""
import io
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
from atlas_store import digest
from compare_grounding_methods import draw_geometry
from run_atlas_vlm import read_package

BASELINE = ROOT / "benchmark/atlas/runs/zurich10_qwen_staged_20260917_012804"
base_manifest, base_image, base_tasks, base_prompt = read_package(BASELINE / "input.zip")
manifest, image, tasks, prompt = read_package(HERE / "input.zip")
assert prompt == base_prompt
assert [(t["event_id"], t["text"], t["question"]) for t in tasks] == [(t["event_id"], t["text"], t["question"]) for t in base_tasks]
assert manifest["map_version"] != base_manifest["map_version"]
assert manifest["image_sha256"] != base_manifest["image_sha256"]
runs = {"geographic": json.loads((BASELINE / "direct/predictions.json").read_text()),
        "reference": json.loads((HERE / "predictions.json").read_text())}
assert runs["reference"]["map_version"] == manifest["map_version"]
assert runs["geographic"]["map_version"] == base_manifest["map_version"]
predictions = {k: {p["event_id"]: p for p in r["predictions"]} for k, r in runs.items()}
attempts = {"geographic": [json.loads(s) for s in (BASELINE / "direct/attempts.jsonl").read_text().splitlines()],
            "reference": [json.loads(s) for s in (HERE / "predictions.attempts.jsonl").read_text().splitlines()]}
for key, rows in attempts.items():
    assert len(rows) == 10 and {a["event_id"] for a in rows} == {t["event_id"] for t in tasks}
    assert all(a["max_output_tokens"] == 4096 for a in rows)
assert attempts["geographic"][0]["local_config"] == attempts["reference"][0]["local_config"]
assert {a["instruction"] for a in attempts["reference"]} == {a["instruction"] for a in attempts["geographic"]}
summary = {k: {"requests": len(attempts[k]), "valid_geometry": sum(p["geometry"] is not None for p in r["predictions"]),
               "abstained": sum(p["geometry"] is None for p in r["predictions"]), "errors": r["errors"],
               "elapsed_seconds": sum(a["elapsed_seconds"] for a in attempts[k]),
               "accuracy": None, "accuracy_unavailable_reason": "No independent gold for reference map; different coordinate systems and map coverage"}
           for k, r in runs.items()}
output = HERE / "review"
output.mkdir(exist_ok=False)
backgrounds = {"geographic": Image.open(io.BytesIO(base_image)).convert("RGB"),
               "reference": Image.open(io.BytesIO(image)).convert("RGB")}
overview = backgrounds["reference"].copy()
records = []
for task in tasks:
    eid = task["event_id"]
    combined = Image.new("RGB", (1420, 850), "white")
    for i, key in enumerate(("geographic", "reference")):
        layer = backgrounds[key].copy()
        prediction = predictions[key].get(eid)
        color = "#16805d" if key == "geographic" else "#9558aa"
        if prediction and prediction["geometry"]:
            draw_geometry(layer, prediction["geometry"], color)
        layer.thumbnail((690, 790))
        combined.paste(layer, (10+i*710, 55))
        status = "ERROR" if prediction is None else "ABSTAINED" if prediction["geometry"] is None else prediction["geometry"]["type"]
        draw = ImageDraw.Draw(combined)
        draw.text((10+i*710, 8), f"{eid} | {key} map | Qwen3-VL | {status}", fill="black")
        draw.text((10+i*710, 26), "Different map coordinates/scales: no cross-map pixel scoring", fill="black")
        if key == "reference":
            draw.text((10+i*710, 40), "Original troop symbols/arrows are INPUT cues, not gold labels", fill="#9558aa")
            if prediction and prediction["geometry"]:
                draw_geometry(overview, prediction["geometry"], "#9558aa")
                x, y = prediction["geometry"]["coordinates"][0]
                ImageDraw.Draw(overview).text((max(0, min(x+10, overview.width-70)), max(0, y-15)), eid, fill="#60008e", stroke_width=1, stroke_fill="white")
    combined.save(output / f"{eid}.png")
    records.append({"event_id": eid, "map_version": manifest["map_version"], "image_sha256": manifest["image_sha256"],
                    "status": "pending", "geometry": None, "tolerance_px": None,
                    "evidence": "", "reviewer": "", "notes": ""})
overview.save(output / "reference_predictions.png")
(output / "reference_gold_template.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")
(output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
lines = ["# 苏黎世作战参考图输入实验", "",
         "## 当前结论", "",
         "已用原始作战参考图对同样十条事件运行 Qwen3-VL 直接定位。**目前无法计算定位准确率的变化**：",
         "参考图尚无独立人工真值，旧答案在另一张图的像素坐标系上，不能直接使用或按宽高比例缩放迁移。",
         "下表是输出有效性，不是定位正确率。", "",
         "| 输入 | 请求数 | 有效几何 | 拒答 | 错误 | 推理耗时（秒） |", "|---|---:|---:|---:|---:|---:|"]
for k, s in summary.items():
    lines.append(f"| {k} | {s['requests']} | {s['valid_geometry']} | {s['abstained']} | {len(s['errors'])} | {s['elapsed_seconds']:.1f} |")
lines += ["", "## 控制与限制", "",
          "- Qwen/Qwen3-VL-8B-Instruct，同一缓存版本、设备与精度、greedy、4096 输出 token 上限；原文、问题、定位 prompt 保持一致。",
          "- baseline 使用刚完成的直接定位运行，不把旧预测伪称为重新调用。只新运行参考图十条，不重跑 GPT-5 或两阶段。",
          "- 原底图为 1538 × 1754；参考图为 2177 × 1699。原始 JPEG 仅无损转换为 PNG，解码后的像素相同，未裁切、增强或重绘。",
          "- 图像改变同时改变了地理覆盖、缩放、绘图风格和军事提示，不能把差异仅归因于部署标记。",
          "- 参考图含部队名称、阵位和箭头，是有答案提示的诊断条件，不是无泄漏测试集。",
          "- Regensdorf 出现在参考图中，Z0003 不能继续沿用旧图的 outside_map 标签。",
          "- 原始部署符号并非每条事件/时刻的真值；特别是首次登陆、后续夺取和撤退不能混为同一时间层。", "",
          "## 人工审核", "",
          "独立入口：<http://127.0.0.1:8768/atlas.html>。主站 8767 的底图、人工标注和预测没有更改。",
          "在独立入口先关闭模型预测图层，按问题在参考图上标注；避免用预测点当真值。",
          "该入口的数据保存在本实验 reference_workspace 内，不是原项目人工标注的替代品。",
          "十条初始均为待审核，既不自动接受，也不继承旧图的范围外判定。",
          "完成后应预先定义各图的合理容差/允许区域，在两图都可定位且目标一致的共同事件上比较命中率。",
          "不能直接比较两种比例尺的像素距离均值；Z0009/Z0010 的原人工答案目标/几何问题也仍需复核。", "",
          "## 输出", "", "- [参考图全部预测概览](reference_predictions.png)",
          "- [原始预测 JSON](../predictions.json)、[逐次原始响应](../predictions.attempts.jsonl)。",
          "- [运行统计](summary.json)、[备用空白真值模板](reference_gold_template.jsonl)。",
          "- 对照图左为原底图预测，右为参考图预测；不是相同地理范围/比例尺的配准图。"]
lines += [f"- [{t['event_id']} 对照图]({t['event_id']}.png)" for t in tasks]
lines += ["", "## 复现", "", "```bash",
          "MPLCONFIGDIR=/tmp/hegrounding-mpl .venv/bin/python benchmark/run_atlas_vlm.py \\",
          "  --input benchmark/atlas/runs/zurich10_reference_20260917_021309/input.zip \\",
          "  --backend qwen-local --model Qwen/Qwen3-VL-8B-Instruct --limit 10 --execute \\",
          "  --output benchmark/atlas/runs/另一个新目录/predictions.json", "```", "",
          "重新打开独立审核服务：", "", "```bash",
          "bash benchmark/run_annotation_gui.sh --port 8768 \\",
          "  --data-root benchmark/atlas/runs/zurich10_reference_20260917_021309/reference_workspace", "```"]
(output / "RESULTS.md").write_text("\n".join(lines) + "\n")
experiment = json.loads((HERE / "experiment.json").read_text())
assert all(digest((ROOT / path).read_bytes()) == expected for path, expected in experiment["main_workspace_unchanged"].items())
print(json.dumps(summary, indent=2))
