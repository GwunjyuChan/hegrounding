"""Offline comparison against frozen human labels; separate from paid inference."""
import io
import json
from datetime import datetime
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
from PIL import Image, ImageDraw
from compare_grounding_methods import cell, costs, diagnose, draw_geometry
from run_atlas_vlm import SYSTEM, digest, read_package


def load(path):
    return json.loads(path.read_text())


def main():
    complete = load(HERE / "completed.json")
    if not complete["completed_all_tasks"]:
        raise SystemExit("Incomplete API run: inspect preserved attempts; no full comparison generated")
    old = HERE.parent / "zurich10_20260916_162847"
    methods = {"qwen_native": HERE.parent / "zurich10_native_pixels_20261007",
               "gpt5": old / "gpt5", "gpt6_astra": HERE}
    manifest, png, tasks, instruction = read_package(HERE / "input.zip")
    assert (HERE / "input.zip").read_bytes() == (old / "input.zip").read_bytes()
    gold_path = old / "gold_snapshot.json"
    gold = load(gold_path)
    assert gold["map"]["version"] == manifest["map_version"]
    assert gold["map"]["image_sha256"] == manifest["image_sha256"]
    labels = {a["event_id"]: a for a in gold["annotations"]}
    expected = {t["event_id"]: t for t in tasks}
    excluded = set(load(HERE / "manifest.json")["spatial_exclusions_declared_before_run"])
    rows, summaries = {}, {}
    for method, directory in methods.items():
        result = load(directory / "predictions.json")
        attempts = [json.loads(line) for line in (directory / "predictions.attempts.jsonl").read_text().splitlines()]
        assert len(attempts) == 10 and {a["event_id"] for a in attempts} == set(expected)
        assert result["map_version"] == manifest["map_version"]
        for a in attempts:
            assert a["image_sha256"] == manifest["image_sha256"]
            assert a["task"] == expected[a["event_id"]]
            assert a["instruction"] == SYSTEM + instruction
            assert a["max_output_tokens"] == 4096
        predictions = {p["event_id"]: p for p in result["predictions"]}
        errors = {e["event_id"]: e for e in result["errors"]}
        assert set(predictions).isdisjoint(errors) and set(predictions) | set(errors) == set(expected)
        rows[method] = {}
        for eid in expected:
            diagnostic = diagnose(labels[eid], predictions.get(eid), errors.get(eid), eid in excluded)
            diagnostic["geometry"] = predictions.get(eid, {}).get("geometry")
            rows[method][eid] = diagnostic
        points = [r["distance_to_gold_px"] for r in rows[method].values() if r["gold_type"] == "point" and "distance_to_gold_px" in r]
        polygons = [r for r in rows[method].values() if "point_inside_gold" in r]
        summaries[method] = {"valid": sum(p["geometry"] is not None for p in predictions.values()),
            "abstained": sum(p["geometry"] is None for p in predictions.values()), "errors": len(errors),
            "point_n": len(points), "point_mean_px": statistics.mean(points) if points else None,
            "point_median_px": statistics.median(points) if points else None,
            "point_in_polygon": {"hits": sum(p["point_inside_gold"] for p in polygons), "n": len(polygons)},
            "cost": costs(attempts), "returned_models": sorted({a.get("response_model", result["model"]) for a in attempts}),
            "incomplete_responses": [a["event_id"] for a in attempts if a.get("response_status") == "incomplete"]}
    pairs = {}
    for baseline in ("qwen_native", "gpt5"):
        ids = [eid for eid in expected if all(rows[m][eid]["gold_type"] == "point" and "distance_to_gold_px" in rows[m][eid]
                                              for m in (baseline, "gpt6_astra"))]
        pair = {"event_ids": ids, "n": len(ids)}
        if ids:
            for m in (baseline, "gpt6_astra"):
                values = [rows[m][eid]["distance_to_gold_px"] for eid in ids]
                pair[m] = {"mean_px": statistics.mean(values), "median_px": statistics.median(values)}
            before, after = pair[baseline]["mean_px"], pair["gpt6_astra"]["mean_px"]
            differences = [rows["gpt6_astra"][eid]["distance_to_gold_px"] - rows[baseline][eid]["distance_to_gold_px"] for eid in ids]
            pair.update(mean_error_reduction_percent=100 * (before-after) / before if before else None,
                        improved=sum(d < -1e-9 for d in differences), worsened=sum(d > 1e-9 for d in differences))
        pairs[baseline] = pair
    out = HERE / "review"
    out.mkdir(exist_ok=False)
    (out / "gold_snapshot.json").write_bytes(gold_path.read_bytes())
    report = {"metrics_kind": "provisional_pixel_diagnostics_not_benchmark_accuracy", "map": manifest,
              "gold_sha256": digest(gold_path.read_bytes()), "excluded": sorted(excluded),
              "summaries": summaries, "paired_points": pairs, "rows": rows}
    (out / "diagnostics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    background = Image.open(io.BytesIO(png)).convert("RGB")
    colors = {"qwen_native": "#16805d", "gpt5": "#9761b8", "gpt6_astra": "#287be0"}
    contact = Image.new("RGB", (2130, 5 * 435), "white")
    for index, eid in enumerate(expected):
        comparison = Image.new("RGB", (2130, 870), "white")
        draw = ImageDraw.Draw(comparison)
        for col, method in enumerate(methods):
            layer = background.copy()
            draw_geometry(layer, labels[eid]["geometry"], "#cf3f49")
            draw_geometry(layer, rows[method][eid]["geometry"], colors[method])
            layer.thumbnail((690, 780))
            x = 10 + col * 710
            comparison.paste(layer, (x, 65))
            draw.text((x, 8), f"{eid} | {method} | {rows[method][eid]['status']}", fill="black")
            draw.text((x, 26), "Red: frozen human GT; other color: model prediction", fill="black")
            distance = rows[method][eid].get("distance_to_gold_px")
            caption = f"Distance to gold: {distance:.1f} px" if distance is not None else "No point-distance score"
            if eid in excluded:
                caption = "GT REVIEW NEEDED: excluded from spatial scoring"
            draw.text((x, 44), caption, fill="black")
        comparison.save(out / f"{eid}_comparison.png")
        comparison.thumbnail((1065, 435))
        contact.paste(comparison, ((index % 2) * 1065, (index // 2) * 435))
    contact.save(out / "all_comparisons.png")
    finished = datetime.fromisoformat(complete["finished_at"]).astimezone().isoformat()
    lines = ["# Zurich Ten Questions: GPT-6 Astra Comparison", "", "**[高清交互对比：逐题、同步缩放、原像素导出](comparison.html)**", "", "**[中文详细报告：附图、逐题误差与模型能力分析](../../../../../ZURICH_MODEL_COMPARISON_REPORT_2026-10-08.md)**", "", f"Completed (local time): {finished}. Run started 2026-10-07.", "",
        "## Controls", "",
        "Same frozen ten passages/questions, prompt, original 1538x1754 PNG and 4096-token output limit as GPT-5. No gold or deployment map was sent. No tools, coordinate repair, retries or answer selection.",
        "GPT-6 API uses provider-default image detail/reasoning, as did GPT-5. Original PNG bytes are sent unchanged; server-side image processing is not verified. Native Qwen uses a padded 1568x1760 canvas with no resampling. This is not an identical vision-token or reasoning-compute budget comparison.",
        "Z0009 (road question vs point gold) and Z0010 (city question vs retreat-line gold) are predeclared exclusions. Z0003 is outside the frozen map and tests abstention. Human labels remain provisional.", "",
        "## Summary", "", "| Model | Valid geometry | Abstained | Errors | Valid point n | Mean px | Median px | Point in polygon | Seconds |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for method, s in summaries.items():
        mean = f"{s['point_mean_px']:.1f}" if s['point_n'] else "N/A"
        median = f"{s['point_median_px']:.1f}" if s['point_n'] else "N/A"
        poly = s['point_in_polygon']
        lines.append(f"| {method} | {s['valid']}/10 | {s['abstained']} | {s['errors']} | {s['point_n']} | {mean} | {median} | {poly['hits']}/{poly['n']} | {s['cost']['seconds']:.1f} |")
    lines += ["", "Valid geometry is not accuracy. Means above may use different successful subsets; use paired comparisons below.", "", "## Paired Point Comparisons", ""]
    for baseline, p in pairs.items():
        lines.append(f"- GPT-6 Astra vs {baseline}: n={p['n']}, IDs: {', '.join(p['event_ids'])}.")
        if p['n']:
            lines.append(f"  Mean error: {p[baseline]['mean_px']:.1f} -> {p['gpt6_astra']['mean_px']:.1f} px; reduction {p['mean_error_reduction_percent']:.1f}%. Improved {p['improved']}, worsened {p['worsened']}.")
    lines += ["", "## Per Question", "", "| Event | Qwen native | GPT-5 | GPT-6 Astra | Image |", "|---|---|---|---|---|"]
    for eid in expected:
        lines.append(f"| {eid} | " + " | ".join(cell(rows[m][eid]) for m in methods) + f" | [{eid}]({eid}_comparison.png) |")
    lines += ["", "## Limits and Audit", "",
        "GPT-6 Astra returned medium reasoning effort in all ten response metadata records. All API responses completed; Z0001 failed local geometry validation because it returned coordinates [311,100] instead of [[311,100]]. It was not repaired or retried. Z0005 returned a polygon against point gold and is therefore not included in point-distance means. Missing/truncated reasoning text is not treated as an answer.",
        "Single map and one run per model, provisional gold, historical baselines, and provider-default inference settings do not establish general model superiority. Paired success-only error omits failures; always read coverage and error counts together. The API token budget includes reasoning, and truncated responses are retained as failures.",
        "No current website layers or human annotations were changed. These results belong only to the frozen map version.", "",
        "| Model | Input tokens | Output tokens | Total tokens |", "|---|---:|---:|---:|"]
    for m, s in summaries.items():
        c = s['cost']
        lines.append(f"| {m} | {c['input_tokens']} | {c['output_tokens']} | {c['total_tokens']} |")
    lines += ["", "- [Predictions](../predictions.json)", "- [Raw responses and usage](../predictions.attempts.jsonl)",
        "- [Run settings](../manifest.json)", "- [Structured diagnostics](diagnostics.json)",
        "- [All comparison images](all_comparisons.png)", "",
        "Model API documentation: https://developers.openai.com/api/docs/models/gpt-6-astra", ""]
    (out / "RESULTS.md").write_text("\n".join(lines))
    print(json.dumps({"summaries": summaries, "paired_points": pairs}, indent=2))


if __name__ == "__main__":
    main()
