"""Independent label-grounding diagnostic: prepare, run, then score after human review."""
from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path
import time
import zipfile

from PIL import Image
from atlas_store import AtlasStore, digest, stamp
from run_atlas_vlm import call_local_qwen, load_local_qwen, parse_geometry, read_package, SYSTEM

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = ROOT / "benchmark/atlas/assets/2ae3fca4eb15dced41f82401.png"
TARGETS = ["ZURICH", "Altstetten", "Albisrieden", "Wollishofen",
           "Kilchberg", "Rüschlikon", "Thalweil", "Horgen"]
MODES = ("pixels", "normalized_1000")


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def instruction(mode):
    base = ("Locate the center of the printed place-name label specified by the question on the map. "
            "Do not locate a settlement symbol, an event, or a military unit. "
            "Return only JSON with event_id and geometry: "
            '{"type":"point","coordinates":[[x,y]]}. '
            "Return geometry: null if the label cannot be identified. "
            "The origin is top left; x increases rightward and y downward. ")
    if mode == "pixels":
        return base + "Use original image pixel coordinates: 0 <= x < width, 0 <= y < height."
    if mode == "normalized_1000":
        return base + ("Use relative coordinates from 0 to 1000 on each axis, NOT original image pixels. "
                       "x=1000 denotes the right image edge; y=1000 denotes the bottom image edge.")
    raise ValueError("Unknown coordinate mode")


def parse_point(raw, row, mode):
    text = raw.strip()
    if text.startswith("```") and text.endswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    payload = json.loads(text)
    geometry = payload.get("geometry") if isinstance(payload, dict) else None
    coords = geometry.get("coordinates") if isinstance(geometry, dict) else None
    repaired = (isinstance(geometry, dict) and geometry.get("type") == "point"
                and isinstance(coords, list) and len(coords) == 2
                and all(type(v) in (int, float) for v in coords))
    if repaired:
        geometry["coordinates"] = [coords]
    raw = json.dumps(payload)
    if mode == "pixels":
        result = parse_geometry(raw, row)
    elif mode == "normalized_1000":
        # Validate relative coordinates before conversion. No heuristic mode detection or clipping.
        result = parse_geometry(raw, {**row, "width": 1001, "height": 1001})
        if result["geometry"]:
            coords = result["geometry"]["coordinates"]
            if any(not 0 <= v <= 1000 for p in coords for v in p):
                raise ValueError("Relative coordinates must be in [0, 1000]")
            coords = [[x / 1000 * row["width"], y / 1000 * row["height"]] for x, y in coords]
            result["geometry"] = AtlasStore.geometry({**result["geometry"], "coordinates": coords},
                                                     row["width"], row["height"])
    else:
        raise ValueError("Unknown coordinate mode")
    if result["geometry"] and result["geometry"]["type"] != "point":
        raise ValueError("Label-center task requires a point")
    result["format_normalization"] = "flat_point_to_singleton" if repaired else None
    return result


def crop_point_to_full(point, crop, output_size):
    """Map a diagnostic crop prediction to the source raster, without rotation."""
    x0, y0, x1, y1 = crop
    w, h = output_size
    x, y = point
    if not all(math.isfinite(v) for v in (*point, *crop, *output_size)) or not (
            0 <= x0 < x1 and 0 <= y0 < y1 and w > 0 and h > 0 and 0 <= x < w and 0 <= y < h):
        raise ValueError("Invalid crop transform")
    return [x0 + x * (x1-x0)/w, y0 + y * (y1-y0)/h]


def prepare(image_path, output):
    from annotation_server import Store

    if output.exists():
        raise ValueError("Choose a new directory; existing annotations are never overwritten")
    png = image_path.read_bytes()
    with Image.open(io.BytesIO(png)) as im:
        if im.format != "PNG":
            raise ValueError("Use a PNG map")
    workspace = output / "workspace"
    (workspace / "maps").mkdir(parents=True)
    (workspace / "benchmark").mkdir()
    (workspace / "maps/diagnostic.png").write_bytes(png)
    records = [{"event_id": f"P{i:03}", "battle_id": "zurich_second_1799",
                "image": "maps/diagnostic.png", "place_name": name,
                "event_text": f"Target printed place-name label: {name}.",
                "target_question": f'Where is the center of the printed label "{name}"?',
                "annotation_caution": "地名文字定位诊断，不是历史事件。请框住文字本身，不标聚落中心；未审核时不评分。"}
               for i, name in enumerate(TARGETS, 1)]
    (workspace / "benchmark/zurich_pilot_10.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    atlas = AtlasStore(Store(workspace))
    mid = next(iter(atlas.groups))
    source = atlas.import_source(png, image_path.name)
    detail = atlas.save_map(mid, {"base_revision": None, "source_id": source["id"],
        "crop": [0, 0, source["width"], source["height"]], "rotation": 0, "max_side": 6000,
        "title": "Zurich 1816 - label grounding diagnostic",
        "provenance": "Usteri 1816; existing geographic base. Printed label centers, not event locations."})
    active = detail["active"]
    asset = atlas.asset_path(active["version"]).read_bytes()
    tasks = [{"event_id": r["event_id"], "map_version": active["version"], "image": "map.png",
              "width": active["width"], "height": active["height"], "text": r["event_text"],
              "question": r["target_question"]} for r in records]
    for mode in MODES:
        with zipfile.ZipFile(output / f"full_{mode}.zip", "x", zipfile.ZIP_DEFLATED) as z:
            z.writestr("map.png", asset)
            z.writestr("manifest.json", json.dumps({"map_version": active["version"],
                "image_sha256": digest(asset), "event_count": len(tasks), "coordinate_system": mode,
                "task_kind": "printed_label_center"}))
            z.writestr("tasks.jsonl", "\n".join(json.dumps(r, ensure_ascii=False) for r in tasks) + "\n")
            z.writestr("prompt.txt", instruction(mode))
    write_json(output / "dataset.json", {"created_at": stamp(), "source_image": str(image_path),
        "source_sha256": digest(png), "map_id": mid, "map_version": active["version"],
        "image_sha256": digest(asset), "targets": TARGETS, "gold_status": "pending_human_review",
        "task_kind": "printed_label_center", "split_group": "zurich_1816_single_map"})
    print(f"Prepared {len(tasks)} pending label targets: {output}")


def run(dataset, output, model_id, limit, max_tokens, execute):
    packages = {mode: read_package(dataset / f"full_{mode}.zip") for mode in MODES}
    a, b = packages.values()
    if a[1:3] != b[1:3] or any(p[0].get("coordinate_system") != m or p[3] != instruction(m)
                              for m, p in packages.items()):
        raise ValueError("Ablation must share the image/tasks and use the declared prompts")
    print(f"{min(limit, len(a[2]))} targets x two coordinate modes; no gold loaded")
    if not execute:
        print("Dry run. Add --execute to load the cached local model.")
        return
    if output.exists():
        raise ValueError("Choose a new output directory")
    output.mkdir(parents=True)
    for mode in MODES:
        (output / f"full_{mode}.zip").write_bytes((dataset / f"full_{mode}.zip").read_bytes())
    local = load_local_qwen(model_id)
    write_json(output / "config.json", {"model": model_id, "local_config": local[2],
        "max_tokens": max_tokens, "image_sha256": a[0]["image_sha256"],
        "map_version": a[0]["map_version"], "created_at": stamp(), "method": "coordinate_prompt_ablation"})
    results = {m: {"map_version": a[0]["map_version"], "model": f"{model_id} [label-{m}]",
                   "coordinate_system": "image_pixels_top_left", "predictions": [], "errors": []} for m in MODES}
    with (output / "attempts.jsonl").open("x", encoding="utf-8") as stream:
        for index, row in enumerate(a[2][:limit]):
            for mode in MODES if index % 2 == 0 else reversed(MODES):
                started = time.monotonic()
                attempt = {"event_id": row["event_id"], "mode": mode, "task": row,
                           "instruction": SYSTEM + packages[mode][3], "image_sha256": a[0]["image_sha256"]}
                try:
                    raw, usage = call_local_qwen(local, a[1], row, packages[mode][3], max_tokens)
                    attempt.update(raw=raw, usage=usage)
                    prediction = parse_point(raw, row, mode)
                    results[mode]["predictions"].append(prediction)
                    attempt.update(status="valid" if prediction["geometry"] else "abstained",
                                   prediction=prediction)
                except Exception as exc:
                    attempt.update(status="error", error_type=type(exc).__name__)
                    results[mode]["errors"].append({"event_id": row["event_id"], "error_type": type(exc).__name__})
                attempt["elapsed_seconds"] = time.monotonic()-started
                stream.write(json.dumps(attempt, ensure_ascii=False, allow_nan=False) + "\n")
                stream.flush()
                write_json(output / f"{mode}.json", results[mode])
                print(f"{row['event_id']} {mode}: {attempt['status']}", flush=True)
    write_json(output / "completed.json", {"created_at": stamp(), "targets": min(limit, len(a[2]))})
    if any(r["errors"] for r in results.values()):
        raise SystemExit(1)


def score(workspace, run_dir, output):
    from annotation_server import Store
    from compare_grounding_methods import point_distance

    if output.exists():
        raise ValueError("Choose a new score output")
    if not (run_dir / "completed.json").exists():
        raise ValueError("Run is incomplete")
    atlas = AtlasStore(Store(workspace))
    config = json.loads((run_dir / "config.json").read_text())
    detail = atlas.detail(next(iter(atlas.groups)))
    active = detail["active"]
    if config["map_version"] != active["version"] or config["image_sha256"] != active["image_sha256"]:
        raise ValueError("Gold belongs to another map")
    gold = {r["event_id"]: r for r in atlas.labels(detail["id"], active["version"]).values()}
    report = {"map_version": active["version"], "gold_snapshot": list(gold.values()), "methods": {}}
    for mode in MODES:
        predictions = json.loads((run_dir / f"{mode}.json").read_text())
        if predictions["map_version"] != active["version"]:
            raise ValueError("Prediction version mismatch")
        rows = {r["event_id"]: r for r in predictions["predictions"]}
        manifest, _, tasks, _ = read_package(run_dir / f"full_{mode}.zip")
        if manifest["image_sha256"] != active["image_sha256"]:
            raise ValueError("Input image mismatch")
        attempted = set(rows) | {r["event_id"] for r in predictions["errors"]}
        eligible = [gold[t["event_id"]] for t in tasks if t["event_id"] in gold and t["event_id"] in attempted
                    and gold[t["event_id"]]["status"] == "accepted"
                    and gold[t["event_id"]].get("confidence") in range(1, 6)
                    and gold[t["event_id"]].get("geometry", {}).get("type") == "polygon"]
        groups = {}
        for name, subset in (("all_reviewed", eligible), ("confidence_5", [g for g in eligible if g["confidence"] == 5])):
            hits = 0
            for g in subset:
                pred = rows.get(g["event_id"], {}).get("geometry")
                hits += bool(pred and pred["type"] == "point" and point_distance(pred["coordinates"][0], g["geometry"]) == 0)
            groups[name] = {"n": len(subset), "hits": hits, "hit_rate": hits/len(subset) if subset else None}
        report["methods"][mode] = groups
    write_json(output, report)
    print(json.dumps(report["methods"], indent=2))


def reparse(source, output):
    """Reparse frozen raw responses; no new model calls or coordinate-mode guessing."""
    if output.exists() or not (source / "completed.json").exists():
        raise ValueError("Source must be complete and output must be new")
    config = json.loads((source / "config.json").read_text())
    output.mkdir(parents=True)
    config.update(reparsed_from=str(source), format_normalization="point [x,y] -> [[x,y]] only")
    write_json(output / "config.json", config)
    for mode in MODES:
        (output / f"full_{mode}.zip").write_bytes((source / f"full_{mode}.zip").read_bytes())
    results = {m: {"map_version": config["map_version"], "model": f"{config['model']} [label-{m}]",
                   "coordinate_system": "image_pixels_top_left", "predictions": [], "errors": []} for m in MODES}
    with (output / "attempts.jsonl").open("x", encoding="utf-8") as stream:
        for line in (source / "attempts.jsonl").read_text().splitlines():
            attempt = json.loads(line)
            attempt["original_status"] = attempt["status"]
            if "error_type" in attempt:
                attempt["original_error_type"] = attempt.pop("error_type")
            mode = attempt["mode"]
            try:
                if "raw" not in attempt:
                    raise ValueError("Original call has no response")
                prediction = parse_point(attempt["raw"], attempt["task"], mode)
                results[mode]["predictions"].append(prediction)
                attempt.update(status="valid" if prediction["geometry"] else "abstained", prediction=prediction)
            except (ValueError, TypeError, KeyError) as exc:
                results[mode]["errors"].append({"event_id": attempt["event_id"], "error_type": type(exc).__name__})
                attempt.update(status="error", error_type=type(exc).__name__)
            stream.write(json.dumps(attempt, ensure_ascii=False) + "\n")
    for mode, data in results.items():
        write_json(output / f"{mode}.json", data)
    write_json(output / "completed.json", {"created_at": stamp(), "source": str(source), "new_model_calls": 0})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("run")
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--model", default="Qwen/Qwen3-VL-8B-Instruct")
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--max-tokens", type=int, default=1024)
    p.add_argument("--execute", action="store_true")
    p = sub.add_parser("score")
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("reparse")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.image, args.output)
    elif args.command == "run":
        if args.limit < 1 or args.max_tokens < 1:
            parser.error("limit/max-tokens must be positive")
        run(args.dataset, args.output, args.model, args.limit, args.max_tokens, args.execute)
    elif args.command == "score":
        score(args.workspace, args.run, args.output)
    else:
        reparse(args.source, args.output)


if __name__ == "__main__":
    main()
