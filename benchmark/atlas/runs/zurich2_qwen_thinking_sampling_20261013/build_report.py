"""Offline report for the predeclared two-case recommended-sampling diagnostic."""
from __future__ import annotations

import io
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))

from PIL import Image, ImageDraw
from compare_grounding_methods import diagnose
from report_qwen_thinking_eval import load, load_module, read_attempts
from run_atlas_vlm import SYSTEM, digest, parse_geometry, read_package
from run_qwen_thinking_eval import SOURCE, THINKING_GUIDANCE, final_answer, generation_settings, save

RUNS = HERE.parent
PREVIOUS = RUNS / "zurich10_qwen_thinking_20261013"
GPT = RUNS / "zurich10_gpt6_astra_20261007"
CASES = ("Z0003", "Z0004")
METHODS = {
    "thinking_sampling": ("Thinking: recommended sampling", HERE / "thinking"),
    "thinking_4096": ("Thinking: greedy 4096 (previous)", PREVIOUS / "thinking"),
    "thinking_8192": ("Thinking: greedy 8192 (previous)", PREVIOUS / "thinking_8192"),
    "instruct": ("Instruct: greedy 4096 (previous)", PREVIOUS / "instruct"),
    "gpt6": ("GPT-6 Astra (historical)", GPT),
}
COLORS = {"thinking_sampling": "#a54a96", "instruct": "#087849", "gpt6": "#066ed4"}


def status_text(row):
    if row["status"] == "error":
        return row["error_type"]
    if "outside_map_abstention" in row:
        return "Outside-map abstention" if row["outside_map_abstention"] else "Placed an outside-map target"
    if row["status"] == "abstained":
        return "Abstained"
    if "distance_to_gold_px" in row:
        return f"{row['distance_to_gold_px']:.1f} px to provisional human label"
    return "Valid geometry; geometry types differ, not scored"


def make_figures(report, png, gold):
    drawing = load_module(GPT / "build_report_figures.py", "sampling_report_drawing")
    original = Image.open(io.BytesIO(png)).convert("RGB")
    for eid in CASES:
        points = list((gold[eid].get("geometry") or {}).get("coordinates", []))
        for method in COLORS:
            points.extend((report["rows"][method][eid].get("geometry") or {}).get("coordinates", []))
        points = points or [[0, 0], list(original.size)]
        x0 = max(0, math.floor(min(p[0] for p in points)) - 100)
        y0 = max(0, math.floor(min(p[1] for p in points)) - 100)
        x1 = min(original.width, math.ceil(max(p[0] for p in points)) + 100)
        y1 = min(original.height, math.ceil(max(p[1] for p in points)) + 100)
        width = min(original.width, max(1200, x1 - x0))
        height = min(original.height, max(500, y1 - y0))
        x0 = max(0, min(original.width - width, (x0 + x1 - width) // 2))
        y0 = max(0, min(original.height - height, (y0 + y1 - height) // 2))
        views = {"full": (0, 0, original.width, original.height),
                 "detail": (x0, y0, x0 + width, y0 + height)}
        for name, box in views.items():
            crop = original.crop(box)
            image = Image.new("RGB", (crop.width, crop.height + 158), "white")
            image.paste(crop, (0, 104))
            draw = ImageDraw.Draw(image)
            drawing.text(draw, (16, 10), f"{eid} | Recommended Thinking sampling pilot", 24)
            drawing.text(draw, (16, 45), "Human (provisional)", 17, "#d42846")
            for index, method in enumerate(COLORS):
                label = {"thinking_sampling": "Thinking / sampling", "instruct": "Instruct / previous",
                         "gpt6": "GPT-6 / historical"}[method]
                status = report["rows"][method][eid]["status"]
                if status != "valid":
                    label += ": abstain" if status == "abstained" else ": no answer"
                drawing.text(draw, (240 + index * 320, 45), label, 17, COLORS[method])
                drawing.overlay(draw, report["rows"][method][eid]["geometry"], box[:2], COLORS[method])
            drawing.overlay(draw, gold[eid]["geometry"], box[:2], "#d42846", gold=True)
            drawing.text(draw, (16, 74), f"Native pixels | crop origin ({box[0]}, {box[1]}) | Greedy Thinking had no final answers", 17)
            drawing.text(draw, (16, crop.height + 114), "Cross: provisional human point. Circles/outlines: model outputs. No inferred or repaired coordinates.", 17)
            image.save(HERE / "review" / f"{eid}_{name}.png")
        report["figure_crops"][eid] = views


def main():
    out = HERE / "review"
    manifest, png, tasks, instruction = read_package(SOURCE)
    expected = {t["event_id"]: t for t in tasks}
    config = load(HERE / "thinking/manifest.json")
    assert config["selected_event_ids"] == list(CASES)
    assert config["generation_kwargs"] == generation_settings("thinking", "hf-thinking-vl")
    assert config["seed"] == 0 and config["seed_scope"] == "per_request"
    assert config["input_sha256"] == digest(SOURCE.read_bytes())
    assert config["quantization"] is None and config["inference_dtype"] == "float16"
    gold_path = SOURCE.parent / "gold_snapshot.json"
    gold_data = load(gold_path)
    assert gold_data["map"]["image_sha256"] == manifest["image_sha256"]
    gold = {a["event_id"]: a for a in gold_data["annotations"]}
    report = {"metrics_kind": "exploratory_provisional_diagnostics_not_accuracy", "config": config,
              "gold_sha256": digest(gold_path.read_bytes()), "rows": {}, "audit_hashes": {}, "figure_crops": {}}
    all_attempts = {}
    for method, (_, directory) in METHODS.items():
        assert load(directory / "completed.json")["completed_all_tasks"]
        results = load(directory / "predictions.json")
        assert results["map_version"] == manifest["map_version"]
        predictions = {p["event_id"]: p for p in results["predictions"]}
        attempts = read_attempts(directory / "predictions.attempts.jsonl")
        assert len(attempts) == len({a["event_id"] for a in attempts})
        if method == "thinking_sampling":
            assert len(attempts) == 2
        attempts = {a["event_id"]: a for a in attempts if a["event_id"] in CASES}
        assert set(attempts) == set(CASES)
        all_attempts[method] = attempts
        rows = {}
        for eid, attempt in attempts.items():
            assert attempt["task"] == expected[eid] and attempt["instruction"] == SYSTEM + instruction
            assert attempt["image_sha256"] == manifest["image_sha256"]
            prediction = predictions.get(eid)
            error = {"error_type": attempt["error_type"]} if attempt["status"] == "error" else None
            if prediction is not None:
                answer = attempt["raw"] if method == "gpt6" else final_answer(attempt["raw"], method.startswith("thinking"))
                assert parse_geometry(answer, expected[eid]) == prediction
            if method != "gpt6":
                prep = attempt["usage"]["image_preprocessing"]
                assert prep["original_pixels_verified"] and prep["content_scale_xy"] == [1.0, 1.0]
                assert prep["processed_size_wh"] == [1568, 1760]
                assert attempt["local_config"]["dtype"] == "torch.float16"
            row = diagnose(gold[eid], prediction, error)
            row.update(geometry=prediction["geometry"] if prediction else None,
                       usage=attempt["usage"], elapsed_seconds=attempt["elapsed_seconds"],
                       max_output_tokens=attempt["max_output_tokens"], final_answer=attempt.get("final_answer"))
            if method == "thinking_sampling":
                assert attempt["generation_kwargs"] == config["generation_kwargs"]
                assert attempt["seed"] == config["seed"]
                complete = attempt["status"] in ("valid", "abstained")
                row["completed_within_4096_tokens"] = complete and row["usage"]["output_tokens"] <= 4096
                row["completed_within_8192_tokens"] = complete and row["usage"]["output_tokens"] <= 8192
            rows[eid] = row
        report["rows"][method] = rows
        report["audit_hashes"][method] = digest((directory / "predictions.attempts.jsonl").read_bytes())
    for eid in CASES:
        sample = all_attempts["thinking_sampling"][eid]
        for method in ("thinking_4096", "thinking_8192"):
            previous = all_attempts[method][eid]
            for key in ("rendered_prompt_sha256", "chat_template_sha256"):
                assert sample[key] == previous[key]
            assert sample["usage"]["image_preprocessing"] == previous["usage"]["image_preprocessing"]
            assert sample["local_config"]["revision"] == previous["local_config"]["revision"]
    current = report["rows"]["thinking_sampling"]
    completed = sum(r["status"] in ("valid", "abstained") for r in current.values())
    ended_thinking = sum(r["usage"]["thinking_completed"] for r in current.values())
    report["summary"] = {"selected_cases": list(CASES), "valid_final_answers": completed,
                         "completed_thinking_blocks": ended_thinking,
                         "completed_within_4096_tokens": sum(r["completed_within_4096_tokens"] for r in current.values()),
                         "completed_within_8192_tokens": sum(r["completed_within_8192_tokens"] for r in current.values()),
                         "total_seconds": sum(r["elapsed_seconds"] for r in current.values()),
                         "output_tokens": sum(r["usage"]["output_tokens"] for r in current.values())}
    out.mkdir(exist_ok=True)
    make_figures(report, png, gold)
    save(out / "results.json", report)
    lines = ["# Recommended Thinking Sampling: Two-Case Pilot", "",
             "Run date: 2026-10-13. All inference is local. No new GPT API calls were made.", "",
             "## Main Findings", "",
             f"- Completed thinking blocks: **{ended_thinking}/2**; valid final answers (including abstention): **{completed}/2**.",
             "- The previous greedy Thinking runs produced no final answers for these same cases at either 4096 or 8192 tokens.",
             f"- New final answers completed within 4096 tokens: **{report['summary']['completed_within_4096_tokens']}/2**; within 8192: **{report['summary']['completed_within_8192_tokens']}/2**.",
             f"- New inference time: **{report['summary']['total_seconds'] / 60:.1f} minutes**; generated tokens: **{report['summary']['output_tokens']}**.",
             f"- Z0003: **{status_text(current['Z0003'])}**. Historical GPT-6 abstained for this outside-map target.",
             f"- Z0004: **{status_text(current['Z0004'])}**. Compare Instruct: {status_text(report['rows']['instruct']['Z0004'])}; GPT-6: {status_text(report['rows']['gpt6']['Z0004'])}.",
             "- Output completion and spatial correctness are separate outcomes. Pixel distances below use unchanged, provisional human labels, not verified ground truth.", "",
             "## Configuration", "",
             f"[Pinned Qwen3-VL-8B-Thinking model card, VL settings]({THINKING_GUIDANCE}). Sampling enabled; temperature 1.0, top-p 0.95, top-k 20, repetition penalty 1.0, no presence penalty, maximum 40960 generated tokens.", "",
             "Seed 0 was fixed before inference and reset per request; it is an experimental choice. The official nonquantized checkpoint runs in FP16 on MPS. Source image 1538 x 1754 is padded to 1568 x 1760 without resampling. Model revision, rendered prompts, templates and preprocessing match the earlier greedy Thinking runs.", "",
             "## Paired Results", "",
             "| Case | Method | Generated tokens | Time (s) | Result |",
             "|---|---|---:|---:|---|"]
    for eid in CASES:
        for method, (name, _) in METHODS.items():
            row = report["rows"][method][eid]
            lines.append(f"| {eid} | {name} | {row['usage']['output_tokens']} | {row['elapsed_seconds']:.1f} | {status_text(row)} |")
    lines.extend(["", "GPT-6 token accounting and timing come from a historical remote-provider run; they are not directly comparable hardware-throughput measurements.", "", "## New Outputs", ""])
    for eid in CASES:
        row = current[eid]
        usage = row["usage"]
        lines.extend([f"### {eid}", "", f"Question: {expected[eid].get('question', '(see input package)')}", "",
                      f"Outcome: **{status_text(row)}**. Stop reason: `{usage['stop_reason']}`. Thinking tokens: {usage['thinking_tokens']}; answer-channel tokens: {usage['answer_tokens']} (including terminating tokens).", "",
                      "Final answer only (unfinished reasoning is not treated as an answer):", "", "```json",
                      row["final_answer"] or "null", "```", "",
                      f"![{eid}: native-pixel comparison detail]({eid}_detail.png)", "",
                      f"[Full-size map comparison]({eid}_full.png)", ""])
    lines.extend(["## Interpretation And Limits", "",
                  "This pilot tests whether the model can finish and emit a usable answer under its recommended sampling configuration. It does not establish a ten-question accuracy improvement or a new model ranking. The cases were preselected for diagnostic value and only one seed was used.", "",
                  "Both sampling and the maximum output budget changed. Finishing before the old budget would rule out the larger cap as necessary for that particular sampled answer, but would not by itself establish reliable improvements across tasks or seeds. A result that requires more than 8192 tokens remains confounded by the larger budget.", "",
                  "Z0003 is an outside-map diagnostic. For Z0004, a smaller distance to the old human point is agreement with a provisional annotation, not independent proof of historical correctness. No labels were overwritten and no draft coordinates were rescued.", "",
                  "Visual inspection of the Z0004 figure: the sampled Thinking point at (500, 350) falls on wooded slopes to the left of Altstetten, near Urdorf. The earlier Instruct point is near Schlieren; the historical GPT-6 point is near the Altstetten settlement label. This map-reading observation supports a remaining visual-localization problem, independently of the exact provisional human pixel. It does not independently verify the historical stationing event.", "",
                  "Do not change model rankings using this pilot. First inspect the final answers and maps; then predeclare a broader recommended-sampling run and review disputed human labels.", "",
                  "## Audit Files", "",
                  "- [Pre-run protocol](../PROTOCOL.md)", "- [Machine-readable results and audit hashes](results.json)",
                  "- [Actual run manifest](../thinking/manifest.json)", "- [Prediction JSON](../thinking/predictions.json)",
                  "- Raw outputs, usage and generated token IDs: `../thinking/predictions.attempts.jsonl`.",
                  "- The input ZIP and runner snapshot are preserved in `../thinking/`.", ""])
    (out / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
