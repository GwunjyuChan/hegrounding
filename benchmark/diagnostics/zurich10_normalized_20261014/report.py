"""Score the finished normalized run against unchanged historical references."""
from __future__ import annotations

import base64
import importlib.util
import io
import json
import math
from pathlib import Path
import statistics

from run import HERE, ROOT, BASELINES, EXCLUDED, SETTINGS, normalized_instruction, parse_normalized, read_json
from run_atlas_vlm import SYSTEM, digest, read_package, task_prompt
from run_qwen_thinking_eval import save
from compare_grounding_methods import diagnose, costs
from PIL import Image, ImageDraw, ImageFont

METHODS = ("qwen_pixel", "qwen_normalized", "gpt6_astra")
NAMES = {"qwen_pixel": "Qwen pixel (historical)", "qwen_normalized": "Qwen normalized (new)", "gpt6_astra": "GPT-6 Astra (historical)"}
COLORS = {"qwen_pixel": "#9a517e", "qwen_normalized": "#087849", "gpt6_astra": "#066ed4"}
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def paired(rows, methods, ids):
    common = [eid for eid in ids if all(rows[m][eid]["gold_type"] == "point" and
                                      "distance_to_gold_px" in rows[m][eid] for m in methods)]
    result = {"event_ids": common, "n": len(common), "models": {}}
    for method in methods:
        values = [rows[method][eid]["distance_to_gold_px"] for eid in common]
        result["models"][method] = {"mean_px": statistics.mean(values) if values else None,
                                    "median_px": statistics.median(values) if values else None}
    return result


def score_text(row):
    if row["status"] == "error":
        return row["error_type"]
    if row.get("excluded_from_spatial_scoring"):
        return "EXCLUDED"
    if "outside_map_abstention" in row:
        return "correct outside-map null" if row["outside_map_abstention"] else "wrong in-map location"
    if row["status"] == "abstained":
        return "null"
    if "point_inside_gold" in row:
        return "inside region" if row["point_inside_gold"] else f"outside region: {row['distance_to_gold_px']:.1f} px"
    if "distance_to_gold_px" in row:
        return f"{row['distance_to_gold_px']:.1f} px"
    return "unscored geometry mismatch"


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def figures(out, background, labels, rows, ids, common):
    helper = import_file("historical_report_figures", BASELINES["gpt6_astra"] / "build_report_figures.py")
    directory = out / "figures"
    directory.mkdir(exist_ok=True)
    crops = {}
    for eid in ids:
        shapes = [labels[eid]["geometry"]] + [rows[m][eid]["geometry"] for m in METHODS]
        pts = [p for g in shapes if g for p in g["coordinates"]]
        if pts:
            left, right = min(p[0] for p in pts), max(p[0] for p in pts)
            top, bottom = min(p[1] for p in pts), max(p[1] for p in pts)
            width = min(background.width, max(1000, math.ceil(right-left)+160))
            height = min(background.height, max(400, math.ceil(bottom-top)+160))
            x0 = max(0, min(background.width-width, math.floor((left+right-width)/2)))
            y0 = max(0, min(background.height-height, math.floor((top+bottom-height)/2)))
        else:
            x0, y0, width, height = 0, 0, background.width, background.height
        crops[eid] = [x0, y0, x0+width, y0+height]
        canvas = Image.new("RGB", (width, height+234), "white")
        canvas.paste(background.crop(crops[eid]), (0, 104))
        draw = ImageDraw.Draw(canvas)
        helper.text(draw, (16, 10), f"{eid} | Zurich event-location comparison", 24)
        helper.text(draw, (16, 45), "Human reference", 17, "#d42846")
        for i, method in enumerate(METHODS):
            helper.text(draw, (205+i*258, 45), NAMES[method], 17, COLORS[method])
        helper.text(draw, (16, 74), f"Native pixels; display crop {crops[eid]}. Red cross/outline: provisional human reference.", 15)
        helper.overlay(draw, labels[eid]["geometry"], (x0, y0), "#d42846", gold=True)
        for method in METHODS:
            helper.overlay(draw, rows[method][eid]["geometry"], (x0, y0), COLORS[method])
        for i, method in enumerate(METHODS):
            helper.text(draw, (16, height+115+i*25), NAMES[method]+": "+score_text(rows[method][eid]), 18, COLORS[method])
        helper.text(draw, (16, height+200), "All model requests used the full map. Invalid output is not drawn. Exclusions are unchanged.", 16)
        canvas.save(directory / f"{eid}.png")
    save(directory / "display_crops.json", crops)
    if common:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)
        for i, method in enumerate(METHODS):
            values = [rows[method][eid]["distance_to_gold_px"] for eid in common]
            bars = ax.bar([j+(i-1)*.25 for j in range(len(common))], values, .24,
                          color=COLORS[method], label=NAMES[method])
            ax.bar_label(bars, fmt="%.1f", padding=4, fontsize=10)
        ax.set_xticks(range(len(common)), common)
        ax.set_ylabel("Distance to provisional human point (pixels)")
        ax.set_title("Same events, same reference: lower error is better", pad=18)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=.18)
        ax.set_axisbelow(True)
        ax.margins(y=.3)
        ax.legend(loc="upper right", frameon=False, fontsize=9)
        fig.savefig(out / "paired_point_errors.png", dpi=170)
        plt.close(fig)


def viewer(out, report, labels, tasks, png):
    source = import_file("historical_viewer", BASELINES["gpt6_astra"] / "build_viewer.py")
    html = source.TEMPLATE.replace("qwen_native", "qwen_pixel").replace("gpt5", "qwen_normalized")
    html = html.replace("GPT-5", "Qwen normalized").replace("2026-10-07 / 08", "2026-10-14 / historical baselines")
    html = html.replace("Qwen3-VL", "Qwen pixel")
    html = html.replace("#087849", COLORS["qwen_pixel"]).replace("#874bb1", COLORS["qwen_normalized"])
    data = {"tasks": tasks, "rows": report["rows"], "excluded": EXCLUDED, "gold": labels,
            "image": "data:image/png;base64," + base64.b64encode(png).decode()}
    html = html.replace("__LUCIDE__", (ROOT / "benchmark/gui/vendor/lucide.js").read_text())
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("<", "\\u003c"))
    (out / "comparison.html").write_text(html)


def main():
    completion = read_json(HERE / "completed.json")
    assert completion["completed_all_tasks"] and not completion["stopped_on_backend_error"]
    config = read_json(HERE / "manifest.json")
    manifest, png, tasks, original_instruction = read_package(HERE / "input.zip")
    ids = [r["event_id"] for r in tasks]
    expected = {r["event_id"]: r for r in tasks}
    assert config["spatial_exclusions"] == EXCLUDED
    assert digest((HERE / "input.zip").read_bytes()) == config["input_sha256"]
    assert digest((HERE / "PROTOCOL.md").read_bytes()) == config["protocol_sha256"]
    for name, expected_hash in config["source_hashes"].items():
        assert digest((ROOT / name).read_bytes()) == expected_hash
    previous = read_json(BASELINES["gpt6_astra"] / "review/diagnostics.json")
    gold_path = BASELINES["gpt6_astra"] / "review/gold_snapshot.json"
    assert digest(gold_path.read_bytes()) == previous["gold_sha256"]
    gold = read_json(gold_path)
    assert gold["map"]["image_sha256"] == manifest["image_sha256"]
    labels = {r["event_id"]: r for r in gold["annotations"]}
    rows, summaries, logs = {}, {}, {}
    for method in METHODS:
        directory = HERE if method == "qwen_normalized" else BASELINES[method]
        if method != "qwen_normalized":
            for name, expected_hash in config["baseline_hashes"][method].items():
                assert digest((directory / name).read_bytes()) == expected_hash
        result = read_json(directory / "predictions.json")
        attempts = jsonl(directory / ("attempts.jsonl" if method == "qwen_normalized" else "predictions.attempts.jsonl"))
        assert result["map_version"] == manifest["map_version"]
        assert len(attempts) == len(ids) and {a["event_id"] for a in attempts} == set(ids)
        predictions = {p["event_id"]: p for p in result["predictions"]}
        errors = {p["event_id"]: p for p in result["errors"]}
        assert set(predictions).isdisjoint(errors) and set(predictions) | set(errors) == set(ids)
        for a in attempts:
            row = expected[a["event_id"]]
            assert a["image_sha256"] == manifest["image_sha256"] and a["max_output_tokens"] == 4096
            if method == "qwen_normalized":
                assert a["original_task"] == row
                w, h = config["padding"]["canvas_size_wh"]
                assert a["task"] == json.loads(task_prompt({**row, "width": w, "height": h}))
                assert a["instruction"] == SYSTEM + normalized_instruction(original_instruction)
                assert a["generation_kwargs"] == SETTINGS
                prep = a["usage"]["image_preprocessing"]
                assert prep["scale_xy"] == [1.0, 1.0] and prep["original_pixels_verified"]
                assert prep["canvas_rgb_sha256"] == config["padding"]["canvas_rgb_sha256"]
                if a["status"] != "error":
                    assert parse_normalized(a["final_answer"], row, (w, h)) == predictions[row["event_id"]]
            else:
                assert a["task"] == row
                assert a["instruction"] == SYSTEM + original_instruction
        rows[method] = {}
        for eid in ids:
            d = diagnose(labels[eid], predictions.get(eid), errors.get(eid), eid in EXCLUDED)
            d["geometry"] = predictions.get(eid, {}).get("geometry")
            rows[method][eid] = d
        point_values = [r["distance_to_gold_px"] for r in rows[method].values()
                        if r["gold_type"] == "point" and "distance_to_gold_px" in r]
        regions = [r for r in rows[method].values() if "point_inside_gold" in r]
        summaries[method] = {"valid_geometry": sum(p["geometry"] is not None for p in predictions.values()),
            "abstained": sum(p["geometry"] is None for p in predictions.values()), "errors": len(errors),
            "point_n": len(point_values), "point_mean_px": statistics.mean(point_values) if point_values else None,
            "point_median_px": statistics.median(point_values) if point_values else None,
            "region_hits": sum(r["point_inside_gold"] for r in regions), "region_scored": len(regions),
            "outside_map_correct": rows[method]["Z0003"].get("outside_map_abstention", False),
            "cost": costs(attempts)}
        logs[method] = attempts
    comparisons = {"all_three": paired(rows, METHODS, ids),
                   "normalized_vs_gpt6": paired(rows, ("qwen_normalized", "gpt6_astra"), ids),
                   "normalized_vs_pixel": paired(rows, ("qwen_pixel", "qwen_normalized"), ids)}
    p = comparisons["normalized_vs_gpt6"]
    if p["n"]:
        q = p["models"]["qwen_normalized"]["mean_px"]
        g = p["models"]["gpt6_astra"]["mean_px"]
        p.update(qwen_minus_gpt6_mean_px=q-g, qwen_to_gpt6_mean_error_ratio=q/g if g else None,
                 qwen_better_count=sum(rows["qwen_normalized"][eid]["distance_to_gold_px"] < rows["gpt6_astra"][eid]["distance_to_gold_px"] for eid in p["event_ids"]))
    report = {"map": manifest, "gold_sha256": digest(gold_path.read_bytes()), "excluded": EXCLUDED,
              "metrics_kind": "provisional_pixel_diagnostics_not_benchmark_accuracy",
              "summaries": summaries, "paired_points": comparisons, "rows": rows,
              "new_attempts_sha256": digest((HERE / "attempts.jsonl").read_bytes()), "baseline_hashes": config["baseline_hashes"]}
    out = HERE / "review"
    out.mkdir(exist_ok=True)
    save(out / "diagnostics.json", report)
    (out / "gold_snapshot.json").write_bytes(gold_path.read_bytes())
    figures(out, Image.open(io.BytesIO(png)).convert("RGB"), labels, rows, ids, comparisons["all_three"]["event_ids"])
    viewer(out, report, labels, tasks, png)
    lines = ["# Zurich Ten Events: Normalized Qwen vs GPT-6", "", "Run date: 2026-10-14 (Europe/Zurich).", "",
             "[Full-resolution interactive comparison](comparison.html) | [Structured diagnostics](diagnostics.json)", "",
             "## Main Comparison", "", "These are the same ten event questions on ONE map, not ten independent maps. Human references remain provisional.", ""]
    if p["n"]:
        lines += [f"On the {p['n']} common valid point cases ({', '.join(p['event_ids'])}), normalized Qwen mean error is **{q:.1f} px**, versus **{g:.1f} px** for historical GPT-6. Qwen minus GPT-6: **{q-g:+.1f} px**; Qwen is closer on **{p['qwen_better_count']}/{p['n']}** cases.", ""]
    lines += ["![Matched point errors](paired_point_errors.png)", "",
              "Means only cover shared valid point outputs, not all ten questions. Missing, null and non-point outputs are never treated as zero error.", "",
              "## Coverage And Behavior", "", "| Method | Geometry | Null | Errors | Point n | Point mean px | Point median px | Region hits / scored | Outside-map correct | Seconds |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
    for method in METHODS:
        s = summaries[method]
        mean = f"{s['point_mean_px']:.1f}" if s["point_n"] else "N/A"
        median = f"{s['point_median_px']:.1f}" if s["point_n"] else "N/A"
        lines.append(f"| {NAMES[method]} | {s['valid_geometry']}/10 | {s['abstained']} | {s['errors']} | {s['point_n']} | {mean} | {median} | {s['region_hits']}/{s['region_scored']} | {s['outside_map_correct']} | {s['cost']['seconds']:.1f} |")
    lines += ["", "The individual-method means above may cover different questions. Use the matched comparisons below for error differences. Region hits mean point-in-polygon, not polygon IoU.", "",
              "## Interpretation", "",
              "The strong improvement in the earlier isolated printed-label control does not generalize to this full-passage event run. A coordinate contract can help a model report a location it has identified, but does not itself establish that the model selected the correct event, landmark, river bank or map region.", "",
              "This run does not isolate which of those reasoning/grounding steps failed. It also does not show that normalization is inherently harmful: the old pixel baseline is historical, prompt dimensions differ, and some cases improve. Keep both results rather than retroactively converting old pixel answers or selecting successful questions.", "",
              "For the next diagnostic, keep the same map and normalized interface, and compare full-passage event grounding with grounding from a separately extracted location description. Freeze both conditions before inference, preserve spatial qualifiers, and do not provide human coordinates. This would test whether simplifying the textual task helps; it is a proposed follow-up, not a demonstrated fix.", "",
              "## Matched Subsets", ""]
    for name, pair in comparisons.items():
        lines.append(f"- {name}: n={pair['n']}; IDs: {', '.join(pair['event_ids'])}.")
        for method, stats in pair["models"].items():
            if pair["n"]:
                lines.append(f"- {name} / {NAMES[method]}: mean {stats['mean_px']:.1f} px, median {stats['median_px']:.1f} px.")
    lines += ["", "## Per Event", "", "| Event | Qwen pixel | Qwen normalized | GPT-6 | Native-pixel detail |", "|---|---|---|---|---|"]
    for eid in ids:
        lines.append(f"| {eid} | " + " | ".join(score_text(rows[m][eid]) for m in METHODS) + f" | [Detail](figures/{eid}.png) |")
    lines += ["", "## Controls And Limits", "",
              "- New inference is Qwen3-VL-8B-Instruct, official nonquantized weights, FP16/MPS, greedy, seed 0, 4096-token cap; not Thinking mode. The same ten passages and questions are retained.",
              "- The model receives an unscaled 1568 x 1760 canvas containing the 1538 x 1754 original, padded only right/bottom. Outputs explicitly use 0-1000 coordinates; conversion uses actual canvas dimensions and rejects positions outside original content.",
              "- No gold, deployment reference, drawn guide, previous model answer or diagnostic crop enters inference. Display crops are produced only after scoring.",
              "- Z0009/Z0010 retain their previous spatial exclusions; Z0003 separately tests outside-map abstention. Existing output errors and geometry mismatches are not repaired. The full ten questions were attempted regardless of scoring exclusions.",
              "- GPT-6 and Qwen pixel are historical results. New Qwen changes both coordinate instruction and declared prompt dimensions (padded rather than original size). Do not interpret it as an isolated fresh coordinate-only ablation or equal-compute model comparison.",
              "- This one-map pilot has provisional references, shared passages and one run per configuration. It cannot establish general model superiority or overall ten-question accuracy. The previous 32 px label-center control is a different task and is not mixed into these event metrics.",
              "- A difference relative to provisional human geometry is not proof of historical correctness. Manual review must remain independent of which model agrees with the current label.", "",
              "## Audit Files", "", "- [Predeclared protocol](../PROTOCOL.md)", "- [Settings and frozen hashes](../manifest.json)",
              "- [Raw responses, prompts, usage and token IDs](../attempts.jsonl)", "- [Converted pixel predictions](../predictions.json)",
              "- [Unchanged human snapshot](gold_snapshot.json)", "- [Inference runner](../run.py)", ""]
    (out / "RESULTS.md").write_text("\n".join(lines))
    print(json.dumps({"summaries": summaries, "paired_points": comparisons}, indent=2))


if __name__ == "__main__":
    main()
