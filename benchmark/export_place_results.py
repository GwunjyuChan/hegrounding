"""Offline, reproducible review of one completed place-lab batch."""
import argparse
from datetime import datetime
import io
import json
from pathlib import Path
import statistics

from PIL import Image, ImageDraw, ImageFont

from atlas_store import digest, stamp
from compare_grounding_methods import draw_geometry, point_distance


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def render(image, rows, destination):
    width, height = image.size
    gap, top, footer = 24, 70, 90 + len(rows) * 30
    canvas = Image.new("RGB", (width * 2 + gap, height + top + footer), "white")
    font = ImageFont.load_default(size=19)
    title = ImageFont.load_default(size=26)
    for column, (key, color, heading) in enumerate([
            ("gold", "#c43c48", "Human annotation (run-start snapshot)"),
            ("prediction", "#287be0", "Qwen3-VL-8B predictions")]):
        panel = image.copy()
        labels = []
        for number, row in enumerate(rows, 1):
            geometry = (row.get(key) or {}).get("geometry")
            if not geometry:
                continue
            draw_geometry(panel, geometry, color)
            x, y = geometry["coordinates"][0]
            draw = ImageDraw.Draw(panel)
            text = str(number)
            for dx, dy in [(16, -28), (16, 16), (-40, -28), (-40, 16), (16, -60), (16, 44)]:
                bx = max(0, min(width - 44, x + dx))
                by = max(0, min(height - 28, y + dy))
                box = draw.textbbox((bx, by), text, font=font)
                box = (box[0]-3, box[1]-3, box[2]+3, box[3]+3)
                if all(box[2] < b[0] or box[0] > b[2] or box[3] < b[1] or box[1] > b[3] for b in labels):
                    break
            labels.append(box)
            draw.rectangle(box, fill="white", outline=color, width=1)
            draw.text((bx, by), text, font=font, fill=color)
        offset = column * (width + gap)
        canvas.paste(panel, (offset, top))
        ImageDraw.Draw(canvas).text((offset + 18, 22), heading, fill=color, font=title)
    draw = ImageDraw.Draw(canvas)
    y = top + height + 20
    draw.text((18, y), "Printed-label centers | original-image pixels | numbers identify the same target in both panels", font=font, fill="#222222")
    for number, row in enumerate(rows, 1):
        y += 30
        metric = row["comparison"]
        value = "not scored" if metric is None else f"{metric['distance_px']:.1f} px | tolerance {metric['tolerance_px']:g} px | {'HIT' if metric['hit'] else 'MISS'}"
        draw.text((18, y), f"{number:02}  {row['place_name']}", font=font, fill="#222222")
        draw.text((width // 2, y), value, font=font, fill="#222222")
        draw.text((width + gap + 18, y), f"confidence: {row['gold'].get('confidence') if row['gold'] else 'missing'}", font=font, fill="#444444")
    canvas.save(destination)


def export(run):
    state = json.loads((run / "state.json").read_text())
    payload = json.loads((run / "input.json").read_text())
    raw = json.loads((run / "result.json").read_text())
    if state["status"] != "completed" or not state.get("batch"):
        raise ValueError("Select a completed batch run")
    png = (run / "map.png").read_bytes()
    if digest(png) != payload["image_sha256"]:
        raise ValueError("Frozen map hash mismatch")
    image = Image.open(io.BytesIO(png)).convert("RGB")
    selected = state["task_ids"]
    tasks = {t["id"]: t for t in load_jsonl(run.parent.parent / "tasks.jsonl")}
    gold = {}
    for g in load_jsonl(run.parent.parent / "gold.jsonl"):
        if (g["task_id"] in selected and g["map_id"] == state["map_id"] and
                g["map_version"] == state["map_version"] and
                datetime.fromisoformat(g["created_at"]) <= datetime.fromisoformat(state["created_at"])):
            if g["image_sha256"] != payload["image_sha256"]:
                raise ValueError("Gold map hash mismatch")
            if g["task_id"] not in gold or g["created_at"] > gold[g["task_id"]]["created_at"]:
                gold[g["task_id"]] = g
    predictions = {r["task_id"]: r for r in state["results"]}
    if len(predictions) != len(selected) or set(predictions) != set(selected):
        raise ValueError("Incomplete batch")
    rows = []
    for tid in selected:
        t, p, g = tasks[tid], predictions[tid], gold.get(tid)
        if any(r["map_version"] != payload["map_version"] or r["map_id"] != state["map_id"] for r in (t, p)):
            raise ValueError("Mixed map versions")
        metric = None
        if g and g["status"] == "accepted" and g.get("geometry") and p.get("geometry"):
            distance = point_distance(p["geometry"]["coordinates"][0], g["geometry"])
            tolerance = g.get("tolerance_px") or 0
            metric = {"distance_px": distance, "tolerance_px": tolerance, "hit": distance <= tolerance}
        rows.append({"task_id": tid, "place_name": t["place_name"], "task": t,
                     "gold": g, "prediction": p, "comparison": metric})
    scored = [r["comparison"] for r in rows if r["comparison"] is not None]
    summary = {"targets": len(rows), **state["counts"], "scored": len(scored),
        "hits_with_saved_tolerance": sum(r["hit"] for r in scored),
        "hit_rate_with_saved_tolerance": sum(r["hit"] for r in scored) / len(scored) if scored else None,
        "mean_distance_px": statistics.mean(r["distance_px"] for r in scored) if scored else None,
        "median_distance_px": statistics.median(r["distance_px"] for r in scored) if scored else None,
        "elapsed_seconds": state["elapsed_seconds"]}
    destination = run / "review"
    destination.mkdir(exist_ok=False)
    record = {"exported_at": stamp(), "job_id": state["job_id"], "run_created_at": state["created_at"],
        "model": payload["model"], "map_id": state["map_id"], "map_version": state["map_version"],
        "image_sha256": payload["image_sha256"], "image_size_wh": list(image.size),
        "coordinate_mode": payload["coordinate_mode"],
        "gold_policy": "latest_saved_annotation_at_or_before_run_start",
        "metrics_kind": "provisional_label_grounding_diagnostic_not_event_accuracy",
        "summary": summary, "rows": rows, "model_input": payload, "raw_model_result": raw}
    (destination / "experiment.json").write_text(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    render(image, rows, destination / "comparison.png")
    lines = ["# 苏黎世地名批量实验", "", f"- 实验时间（UTC）：{state['created_at']}",
        f"- 导出时间（UTC）：{record['exported_at']}", f"- 批次：`{state['job_id']}`",
        f"- 模型：`{payload['model']}`；底图：{image.width} × {image.height} px。",
        "- 离线整理已有结果，未重新运行模型；左图为人工标注，右图为模型预测。",
        "- 人工答案从追加历史恢复为本批启动前的最后一次保存，不使用后续修订。",
        "- 原始地名拼写保持不变；有效坐标不等于正确定位，此处仅为地名诊断。", "",
        "![人工标注与模型预测对比](comparison.png)", "",
        "[完整实验 JSON](experiment.json) · [模型原始结果](../result.json) · [干净输入底图](../map.png)", "",
        "## 结果", "", f"- 有效坐标：{summary['valid']}/{len(rows)}；拒答：{summary['abstained']}；错误：{summary['error']}。",
        f"- 按各题保存容差命中：{summary['hits_with_saved_tolerance']}/{len(scored)}。容差并非统一阈值，见下表。",
        f"- 含模型加载的整批时间：{state['elapsed_seconds']:.1f} 秒。", "",
        "| 编号 | 原始输入地名 | 置信度 | 误差 px | 容差 px | 命中 |", "|---|---|---:|---:|---:|---|"]
    for i, row in enumerate(rows, 1):
        c, g = row["comparison"], row["gold"]
        values = f"{c['distance_px']:.2f} | {c['tolerance_px']:g} | {'是' if c['hit'] else '否'}" if c else "未评分 | - | -"
        lines.append(f"| {i} | {row['place_name']} | {g.get('confidence') if g else '无'} | {values} |")
    lines += ["", "说明：未审核置信度、较低置信度以及曾查看预测后修改的人工答案均需要进一步独立复核；这些数值不是正式 benchmark 的准确率。", ""]
    (destination / "RESULTS.md").write_text("\n".join(lines))
    return destination, summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    destination, summary = export(args.run.resolve())
    print(destination)
    print(json.dumps(summary, indent=2))
