"""Analyze frozen failure-isolation outputs without modifying inference or labels."""
from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path
import statistics
import sys

from run import HERE, ROOT, FONT, NAMES, TILES, parse_answer
from PIL import Image, ImageDraw, ImageFont
from run_atlas_vlm import digest
from run_qwen_thinking_eval import final_answer, save
from run_single import parse_single

COLORS = {"Altstetten": "#1677c8", "ZURICH": "#b66a05", "Regensdorf": "#a72d7e"}


def load(path):
    return json.loads(path.read_text())


def box_distance(point, box):
    x, y = point
    x0, y0, x1, y1 = box
    return math.hypot(max(x0-x, 0, x-x1), max(y0-y, 0, y-y1))


def local_box(box, tile):
    if box is None:
        return None
    x0, y0, x1, y1 = tile
    a, b, c, d = box
    if x0 <= a <= c <= x1 and y0 <= b <= d <= y1:
        return [a-x0, b-y0, c-x0, d-y0]
    return None


def label_metric(point, box):
    if box is None:
        return {"expected_present": False, "point": point, "correct_abstention": point is None}
    result = {"expected_present": True, "point": point, "reference_box": box, "abstained": point is None}
    if point is not None:
        center = [(box[0]+box[2])/2, (box[1]+box[3])/2]
        distance = box_distance(point, box)
        result.update(center_error_px=math.dist(point, center), distance_to_box_px=distance,
                      inside_reference_box=distance == 0)
    return result


def metric_text(row):
    if "error_type" in row:
        return row["error_type"]
    if not row["expected_present"]:
        return "correct absent" if row["correct_abstention"] else "FALSE PRESENT"
    if row["point"] is None:
        return "missed / null"
    return f"{row['center_error_px']:.1f} px center; {row['distance_to_box_px']:.1f} px box"


def annotate(image, boxes, points, title):
    canvas = Image.new("RGB", (max(image.width, 800), image.height+100), "white")
    canvas.paste(image, (0, 72))
    draw = ImageDraw.Draw(canvas)
    draw.text((14, 10), title, font=ImageFont.truetype(FONT, 20), fill="#20272d")
    for index, name in enumerate(NAMES):
        color = COLORS[name]
        draw.text((14+index*255, 40), name, font=ImageFont.truetype(FONT, 16), fill=color)
        box = boxes.get(name)
        if box:
            draw.rectangle((box[0], box[1]+72, box[2], box[3]+72), outline=color, width=2)
        point = points.get(name)
        if point:
            x, y = point[0], point[1]+72
            draw.ellipse((x-9, y-9, x+9, y+9), outline="white", width=5)
            draw.ellipse((x-8, y-8, x+8, y+8), outline=color, width=3)
    draw.text((14, image.height+77), "Boxes: reference text. Circles: predictions. Native image pixels.",
              font=ImageFont.truetype(FONT, 16), fill="#30383d")
    return canvas


def references():
    refs = load(HERE / "reference/labels.json")
    image = Image.open(HERE / "inputs/full.png").convert("RGB")
    boxes = {name: row["box"] for name, row in refs["labels"].items()}
    annotate(image, boxes, {}, "Assistant provisional text-label references").save(HERE / "reference/full_labels.png")
    crop = [700, 150, 1220, 470]
    annotate(image.crop(crop), {name: local_box(box, crop) for name, box in boxes.items()}, {},
             "Reference check: crop origin (700, 150)").save(HERE / "reference/labels_checked.png")


def reconstruct_tiles(rows, prefix="labels_tile_", names=NAMES):
    result = {}
    for name in names:
        candidates, missing = [], []
        for tile, (x0, y0, _, _) in TILES.items():
            row = rows.get(f"{prefix}{tile}", {}).get(name, {"error_type": "unattempted"})
            if "error_type" in row:
                missing.append(tile)
            elif row["point"] is not None:
                candidates.append({"tile": tile, "point": [row["point"][0]+x0, row["point"][1]+y0]})
        result[name] = {"status": "incomplete" if missing else "ambiguous" if len(candidates) > 1 else "unique" if candidates else "abstained",
                        "candidates": candidates, "failed_tiles": missing}
    return result


def coordinate_figure(report, out):
    # This fixed crop is only for display; every prediction used the full image.
    crop = (450, 90, 1020, 410)
    base = Image.open(HERE / "inputs/full.png").convert("RGB").crop(crop)
    canvas = Image.new("RGB", (1212, 940), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.truetype(FONT, 24)
    font = ImageFont.truetype(FONT, 18)
    small = ImageFont.truetype(FONT, 16)
    draw.text((24, 15), "Altstetten: coordinate-format diagnostic", font=title_font, fill="#20272d")
    draw.text((24, 49), "Green box: provisional reference text. Circle: prediction. Error: distance to text center.",
              font=small, fill="#30383d")
    cases = [("Instruct / pixel output", "instruct_labels_full_pixels_s0"),
             ("Instruct / normalized output", "instruct_labels_full_normalized_1000_s0"),
             ("Thinking / pixel output", "single_labels_full_pixels_s0"),
             ("Thinking / normalized output", "single_labels_full_normalized_1000_s0")]
    for index, (title, cid) in enumerate(cases):
        row = report["labels"][cid]["Altstetten"]
        left, top = 24 + index % 2 * 594, 89 + index // 2 * 405
        color = "#a72d7e" if "pixels" in cid else "#1677c8"
        draw.text((left, top), title, font=font, fill="#20272d")
        draw.text((left, top+27), f"Center error: {row['center_error_px']:.1f} px", font=small, fill=color)
        canvas.paste(base, (left, top+55))
        x0, y0, x1, y1 = row["reference_box"]
        draw.rectangle((left+x0-crop[0], top+55+y0-crop[1], left+x1-crop[0], top+55+y1-crop[1]),
                       outline="#087644", width=3)
        x, y = row["point"]
        px, py = left+x-crop[0], top+55+y-crop[1]
        draw.ellipse((px-10, py-10, px+10, py+10), outline="white", width=6)
        draw.ellipse((px-9, py-9, px+9, py+9), outline=color, width=3)
        draw.text((left, top+378), f"Prediction in full-image pixels: ({x:.1f}, {y:.1f})", font=small, fill="#30383d")
    draw.text((24, 906), "Display-only crop. Model input: full 1568 x 1760 unscaled canvas. One label/seed; not event accuracy.",
              font=small, fill="#30383d")
    canvas.save(out / "coordinate_comparison.png")


def main():
    completion = load(HERE / "single/completed.json")
    assert completion["stop_reason"] != "backend_error", "Inspect the backend error before reporting"
    interruption = load(HERE / "run/interruption.json")
    refs = load(HERE / "reference/labels.json")
    synthetic = load(HERE / "reference/synthetic_boxes.json")["boxes"]
    plan = load(HERE / "inputs/plan.json")
    attempts = [json.loads(line) for line in (HERE / "run/attempts.jsonl").read_text().splitlines()]
    assert len(attempts) == interruption["completed_calls"] == 4
    followup = [json.loads(line) for line in (HERE / "single/attempts.jsonl").read_text().splitlines()]
    assert len(followup) == completion["attempted"]
    attempts += followup
    assert load(HERE / "instruct_control/completed.json")["completed_all_tasks"]
    controls = [json.loads(line) for line in (HERE / "instruct_control/attempts.jsonl").read_text().splitlines()]
    assert len(controls) == 4
    attempts += controls
    assert len({a["id"] for a in attempts}) == len(attempts)
    expected = {c["id"]: c for c in plan["calls"]}
    single_plan = load(HERE / "single/plan.json")
    assert digest((HERE / "single/ADAPTATION.snapshot.md").read_bytes()) == single_plan["adaptation_sha256"]
    assert digest((HERE / "reference/labels.json").read_bytes()) == single_plan["reference_sha256_not_sent_to_model"]
    expected.update({c["id"]: c for c in single_plan["calls"]})
    control_plan = load(HERE / "instruct_control/plan.json")
    expected.update({c["id"]: c for c in control_plan["calls"]})
    out = HERE / "review"
    out.mkdir(exist_ok=True)
    (out / "overlays").mkdir(exist_ok=True)
    report = {"reference_status": refs["status"], "reference_sha256": digest((HERE / "reference/labels.json").read_bytes()),
              "audit_sha256": digest((HERE / "run/attempts.jsonl").read_bytes()), "plan_sha256": digest((HERE / "inputs/plan.json").read_bytes()),
              "single_audit_sha256": digest((HERE / "single/attempts.jsonl").read_bytes()),
              "single_plan_sha256": digest((HERE / "single/plan.json").read_bytes()),
              "instruct_control_audit_sha256": digest((HERE / "instruct_control/attempts.jsonl").read_bytes()),
              "original_interruption": interruption, "followup_completion": completion,
              "uncompleted_original_calls": [c["id"] for c in plan["calls"] if c["id"] not in {a["id"] for a in attempts}],
              "text": {}, "labels": {}, "events": {}, "calls": []}
    for a in attempts:
        c = expected[a["id"]]
        assert all(a[k] == v for k, v in c.items())
        instruct = a["id"].startswith("instruct_")
        if instruct:
            counterpart = expected[a["id"].replace("instruct_", "single_", 1)]
            assert a["user"] == counterpart["user"] and a["system"] == counterpart["system"]
            assert a["image"] == counterpart["image"]
        else:
            assert a["generation_kwargs"] == plan["generation_kwargs"]
        if a["status"] == "valid":
            parser = parse_single if a["id"].startswith("single_") or instruct else parse_answer
            assert parser(final_answer(a["raw"], not instruct), c) == a["prediction"]
        usage = a.get("usage", {})
        record = {"id": a["id"], "kind": a["kind"], "seed": a["seed"], "mode": a["mode"], "image": a["image"],
                  "status": a["status"], "error_type": a.get("error_type"), "elapsed_seconds": a["elapsed_seconds"],
                  "usage": usage, "final_answer": a.get("final_answer"), "prediction": a.get("prediction"),
                  "model_edition": "instruct" if instruct else "thinking"}
        report["calls"].append(record)
        if a["kind"] == "text":
            assert usage["image_tokens"] == 0 and usage["image_preprocessing"] is None
            place = a.get("prediction", {}).get("place")
            target = refs["text_answers"][a["event_id"]]
            report["text"][a["event_id"]] = {"status": a["status"], "answer": place, "expected": target,
                                                    "exact_match": isinstance(place, str) and place.casefold().strip() == target.casefold()}
            continue
        prep = usage["image_preprocessing"]
        assert prep["scale_xy"] == [1.0, 1.0] and usage["image_tokens"] == prep["visual_tokens"] > 0
        supplied_image = Image.open(HERE / "inputs" / a["image"]).convert("RGB")
        assert prep["image_rgb_sha256"] == digest(supplied_image.tobytes())
        if a["kind"] == "event":
            reference = refs["event_reference"][a["event_id"]]
            geometry = a.get("prediction", {}).get("geometry")
            row = {"status": a["status"], "error_type": a.get("error_type"), "geometry": geometry,
                   "reference": reference, "mode": a["mode"]}
            if a["status"] == "valid":
                if reference["outside_map"]:
                    row["outside_map_abstention"] = geometry is None
                elif geometry and geometry["type"] == "point":
                    row["distance_to_provisional_event_point_px"] = math.dist(geometry["coordinates"][0], reference["point"])
            report["events"][a["id"]] = row
            continue
        if a["image"] == "synthetic.png":
            boxes = synthetic
        else:
            boxes = {name: r["box"] for name, r in refs["labels"].items()}
            if a["image"].startswith("tile_"):
                tile = TILES[Path(a["image"]).stem.removeprefix("tile_")]
                boxes = {name: local_box(box, tile) for name, box in boxes.items()}
        predictions = {r["name"]: r["point"] for r in a.get("prediction", {}).get("labels", [])}
        rows = {name: {"error_type": a["error_type"], "expected_present": boxes[name] is not None} if a["status"] == "error"
                else label_metric(predictions[name], boxes[name]) for name in a["user"]["names"]}
        report["labels"][a["id"]] = rows
        image = Image.open(HERE / "inputs" / a["image"]).convert("RGB")
        annotate(image, boxes, predictions, a["id"] + (" / NO FINAL ANSWER" if a["status"] == "error" else "")).save(out / "overlays" / (a["id"] + ".png"))
    report["tile_reconstruction"] = reconstruct_tiles(report["labels"], prefix="single_labels_tile_", names=["Altstetten"])
    report["summary"] = {"calls": len(attempts), "original_completed_calls": 4, "followup_completed_calls": len(followup), "instruct_control_calls": 4,
                         "original_interrupted_calls": 1, "valid_final_answers": sum(a["status"] == "valid" for a in attempts),
                         "errors": dict(Counter(a["error_type"] for a in attempts if a["status"] == "error")),
                         "text_exact_matches": sum(r["exact_match"] for r in report["text"].values()),
                         "seconds": sum(a["elapsed_seconds"] for a in attempts),
                         "output_tokens": sum(a["usage"]["output_tokens"] for a in attempts),
                         "label_groups": {}}
    for group, prefix in (("multi_synthetic", "labels_synthetic"), ("single_synthetic", "single_labels_synthetic"),
                          ("single_full", "single_labels_full"), ("instruct_synthetic", "instruct_labels_synthetic"),
                          ("instruct_full", "instruct_labels_full")):
        for mode in ("pixels", "normalized_1000"):
            selected = [r for cid, rs in report["labels"].items() if cid.startswith(f"{prefix}_{mode}_") for r in rs.values()]
            visible = [r for r in selected if r["expected_present"]]
            valid = [r for r in visible if "center_error_px" in r]
            absent = [r for r in selected if not r["expected_present"]]
            report["summary"]["label_groups"][f"{group}::{mode}"] = {
                "visible_queries": len(visible), "returned_points": len(valid),
                "in_reference_box": sum(r["inside_reference_box"] for r in valid),
                "mean_center_error_px": statistics.mean(r["center_error_px"] for r in valid) if valid else None,
                "absent_queries": len(absent), "correct_abstentions": sum(r.get("correct_abstention", False) for r in absent)}
    save(out / "results.json", report)
    coordinate_figure(report, out)
    findings = ["## Diagnostic Findings", "",
                f"- Text extraction: {report['summary']['text_exact_matches']}/2 exact target-place answers. These two questions do not show a text-extraction failure.",
                "- Completion instability occurs even on the synthetic clear-text image. A truncated answer supplies no location-error measurement and cannot prove a visual failure."]
    groups = report["summary"]["label_groups"]
    for prefix, edition in (("single_full", "Thinking"), ("instruct_full", "Instruct control")):
        pixel_error = groups[f"{prefix}::pixels"]["mean_center_error_px"]
        relative_error = groups[f"{prefix}::normalized_1000"]["mean_center_error_px"]
        if pixel_error is not None and relative_error is not None:
            findings.append(f"- {edition}, same full-map Altstetten label: pixel-prompt center error {pixel_error:.1f} px; relative-coordinate prompt {relative_error:.1f} px. This is one label/seed, not a benchmark accuracy change.")
    absent_tiles = [r["Altstetten"] for cid, r in report["labels"].items() if cid.startswith("single_labels_tile_")
                    and "correct_abstention" in r["Altstetten"]]
    if absent_tiles:
        findings.append(f"- Thinking, fixed tiles: {sum(not r['correct_abstention'] for r in absent_tiles)} false-presence predictions among {len(absent_tiles)} completed absent-label tile queries. Whole-map reconstruction is {report['tile_reconstruction']['Altstetten']['status']}; no oracle selects a candidate.")
    findings += ["- The recorded image hashes, nonzero visual-token counts, finite input tensors and unscaled dimensions rule out the specific missing-image/downsampling failures checked here. They do not rule out every internal backend, precision or model issue.",
                 "- These are adaptive exploratory diagnostics. Any remaining model-internal cause is unresolved; do not infer an intrinsic Thinking-vs-Instruct ranking from different decoding/template conditions.", ""]
    lines = ["# Zurich Failure-Isolation Results", "", "Exploratory local Qwen3-VL-8B Thinking and Instruct diagnostics, 2026-10-13.", "",
             "Historical label boxes are assistant-provisional, not verified human gold. Text-center tasks and event-location tasks are scored separately. No old annotations or results were modified.", "",
             "## Main Conclusion", "",
             "The tested coordinate-output convention is a substantial source of error, not just historical-map readability. Fresh Instruct calls using explicit 0-1000 coordinates land inside the Altstetten reference text box on both the synthetic and historical images; pixel-output calls do not. Thinking also improves on the historical-label control, but still misses the reference box. This diagnoses coordinate-instruction compliance as part of the problem, not a universal fix for event grounding.", "",
             "![Full-map predictions shown in a readable display-only crop](coordinate_comparison.png)", "",
             "The green boxes were frozen before these calls but remain assistant-provisional. Crops above are for review only: no crop or reference marker was sent to the model. Row-to-row comparisons also change decoding and chat templates, so this is not a clean Thinking-vs-Instruct ranking.", "",
             "## Execution", "", f"Valid final outputs: **{report['summary']['valid_final_answers']}/{len(attempts)} completed calls**. Text answers matching the target place: **{report['summary']['text_exact_matches']}/2**. Recorded-call inference: **{report['summary']['seconds']/60:.1f} min** (excludes the interrupted call and setup). Tokens: **{report['summary']['output_tokens']}**.", "",
             f"The original 16-call multi-target plan stopped after four complete attempts, during its fifth call. Both multi-target synthetic controls had exhausted 4096 tokens. A declared adaptive follow-up switched to one requested label, retaining the schema, image, settings and budget. Follow-up calls completed: **{len(followup)}/12**; stop reason: **{completion['stop_reason'] or 'all completed'}**. Cancelled/unattempted calls are not model failures or zero-error predictions.", "",
             "Thinking calls share the FP16 checkpoint, official sampling parameters, per-request seed and 4096-token diagnostic budget. Four additional Instruct positive controls use the same image/user/system content with greedy decoding and its own non-thinking chat template. This control is not an isolated checkpoint-only ablation or a model ranking. Input images are verified unscaled, with actual visual-token counts checked. Coordinate modes use the supplied canvas dimensions. Truncated output is not a wrong spatial prediction.", "",
             "## Text Only", "", "| Event | Target | Answer | Exact match |", "|---|---|---|---|"]
    for eid, row in report["text"].items():
        lines.append(f"| {eid} | {row['expected']} | {row['answer']} | {row['exact_match']} |")
    lines += [""] + findings
    lines += ["", "## Label-Center Diagnostics", "", "Center error is to the center of the reference text box; box error is distance to its boundary (zero inside). A missing final output is not scored as zero error.", "",
              "| Call | Altstetten | ZURICH | Regensdorf |", "|---|---|---|---|"]
    for cid, rows in report["labels"].items():
        lines.append(f"| [{cid}](overlays/{cid}.png) | " + " | ".join(metric_text(rows[name]) if name in rows else "not requested" for name in NAMES) + " |")
    lines += ["", "## Full-Image Coordinate Comparison", "", "| Group | Mode | Points / visible queries | In text box | Mean center error (px) | Correct absent / absent queries |", "|---|---|---:|---:|---:|---:|"]
    for key, r in report["summary"]["label_groups"].items():
        group, mode = key.split("::", 1)
        mean = f"{r['mean_center_error_px']:.1f}" if r["mean_center_error_px"] is not None else "N/A"
        lines.append(f"| {group} | {mode} | {r['returned_points']}/{r['visible_queries']} | {r['in_reference_box']} | {mean} | {r['correct_abstentions']}/{r['absent_queries']} |")
    lines += ["", "The completed follow-up uses one seed and one requested label per call. The originally planned two-seed full-map batch comparison was not completed. Means exclude missing/abstained points, so read coverage alongside errors. Do not combine these tasks into one accuracy.", "",
              "## Fixed-Tile Reconstruction", "", "All four tiles are required. Exactly one non-null candidate is required to reconstruct a map-level point. Multiple candidates remain ambiguous; missing/failed tiles yield incomplete. No gold-selected best tile.", "",
              "| Name | Status | Candidates (full-image pixels) |", "|---|---|---|"]
    for name, row in report["tile_reconstruction"].items():
        candidates = "; ".join(f"{c['tile']}: ({c['point'][0]:.1f}, {c['point'][1]:.1f})" for c in row["candidates"]) or "none"
        lines.append(f"| {name} | {row['status']} | {candidates} |")
    lines += ["", "## Original Event Questions", "", "Distances are to the unchanged provisional human EVENT point, not the text label center.", "",
              "| Condition | Final output | Geometry | Result |", "|---|---|---|---|"]
    for cid, row in report["events"].items():
        result = row["error_type"] if row["status"] == "error" else (
            f"outside-map abstention: {row['outside_map_abstention']}" if "outside_map_abstention" in row else
            f"{row['distance_to_provisional_event_point_px']:.1f} px" if "distance_to_provisional_event_point_px" in row else "abstained or unscored geometry")
        lines.append(f"| {cid} | {row['status']} | {json.dumps(row['geometry'])} | {result} |")
    lines += ["", "## Completion And Inputs", "", "| Call | Status | Tokens | Image tokens | Time (s) |", "|---|---|---:|---:|---:|"]
    for row in report["calls"]:
        lines.append(f"| {row['id']} | {row['error_type'] or row['status']} | {row['usage']['output_tokens']} | {row['usage']['image_tokens']} | {row['elapsed_seconds']:.1f} |")
    lines += ["", "## Recommended Next Experiment", "",
              "1. For a new Qwen run, explicitly request 0-1000 coordinates and convert once using the actual supplied image dimensions. Validate bounds and preserve the coordinate mode in every record. Keep previous pixel-output runs unchanged; do not reinterpret old outputs after seeing their errors.",
              "2. Before repeating all event questions, freeze several human-checked label boxes and absent-label controls. Compare both coordinate formats with the same image and inference settings, and use multiple seeds for sampled Thinking. This tests whether the one-label result generalizes.",
              "3. Keep completion rate separate from spatial error. Five Thinking calls exhausted this diagnostic's 4096-token budget, including both normalized event calls. Those two calls cannot establish whether normalization improves event localization. A larger-budget follow-up would test completion, not automatically fix positioning.",
              "4. Require explicit outside-map answers in event evaluation. Regensdorf was correctly extracted from text but was still placed inside this map. Fixed tiling alone is not a solution: the absent BR tile also returned a false location, leaving two candidates.",
              "5. Only after these controls, rerun the ten Zurich events with frozen human-reviewed references. Report answer completion, outside-map detection and event geometry separately. Do not compare this label-center diagnostic directly with historical GPT event-point errors.", "",
              "No production inference code, human annotation, or old experiment result was changed by this diagnostic.", "",
              "## Interpretation Boundaries", "",
              "- Success on text-only questions isolates those particular textual answers, not general historical reasoning ability.",
              "- Synthetic success shows the pipeline/model can use image positions on a simple control. Failure would motivate backend/precision/input checks before blaming historical-map complexity.",
              "- Coordinate effects are assessed within each task; no old pixel output is retrospectively reinterpreted as normalized coordinates.",
              "- Tiling changes search area, context and token count. It does not magnify the source lettering or independently isolate the vision encoder.",
              "- The TR tile also exposes a clipped fragment of the qualified 'unter Altstetten' label. The fixed reference targets the fully visible standalone Altstetten label. This is a tiling ambiguity, not an image-rescaling error; do not silently relabel the reference after seeing predictions.",
              "- One seed, one positive label in the follow-up, and two event questions are insufficient for model rankings or statistical causal claims.",
              "- Official model-card sampling is used, but the 4096-token diagnostic budget is smaller than the model card's recommended 40960 maximum. Incomplete thinking needs a separate completion follow-up, not a claimed location error.", "",
              "## Model Documentation", "",
              "- [Qwen3-VL 2D grounding cookbook](https://github.com/QwenLM/Qwen3-VL/blob/main/cookbooks/2d_grounding.ipynb): normalized 0-1000 coordinate examples.",
              "- [Frozen Thinking model card](https://huggingface.co/Qwen/Qwen3-VL-8B-Thinking/blob/92f3c4b4feadd3a016ef468d103bb5f58b2a2c6b/README.md): recommended sampling and generation budget.", "",
              "## Files", "", "- [Pre-run protocol](../PROTOCOL.md)", "- [Structured results and hashes](results.json)",
              "- [Assistant provisional reference boxes](../reference/labels_checked.png)", "- [Frozen original input plan](../inputs/plan.json)",
              "- [Declared adaptation](../ADAPTATION.md)", "- [Single-target plan](../single/plan.json)",
              "- [Instruct positive-control plan](../instruct_control/plan.json)",
              "- Full final answers and prediction objects are in results.json; raw outputs/token IDs are retained in ../run/attempts.jsonl, ../single/attempts.jsonl and ../instruct_control/attempts.jsonl.", ""]
    (out / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    references()
    if len(sys.argv) < 2 or sys.argv[1] != "references":
        main()
