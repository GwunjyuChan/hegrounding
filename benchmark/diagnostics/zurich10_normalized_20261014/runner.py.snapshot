"""Run frozen Zurich questions with explicit normalized Qwen coordinates."""
from __future__ import annotations

import argparse
import gc
import io
import json
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "benchmark"))

from PIL import Image
from atlas_store import AtlasStore
from run_atlas_vlm import SYSTEM, digest, pad_image_without_resampling, parse_geometry, read_package, task_prompt
from run_qwen_thinking_eval import CACHE, MODELS, SOURCE, final_answer, infer, load_local_qwen, save, stamp

OLD_COORDINATES = "Use original image pixels, origin at top left, x rightward, y downward."
NEW_COORDINATES = (
    "The origin is top left; x increases rightward and y downward. "
    "Use relative coordinates from 0 to 1000 on each axis, NOT pixel coordinates. "
    "The right image edge is x=1000 and the bottom edge is y=1000."
)
BASELINES = {
    "qwen_pixel": ROOT / "benchmark/atlas/runs/zurich10_native_pixels_20261007",
    "gpt6_astra": ROOT / "benchmark/atlas/runs/zurich10_gpt6_astra_20261007",
}
SETTINGS = {"do_sample": False, "max_new_tokens": 4096}
EXCLUDED = ["Z0009", "Z0010"]


def normalized_instruction(instruction):
    if instruction.count(OLD_COORDINATES) != 1:
        raise ValueError("Expected one original coordinate instruction")
    return instruction.replace(OLD_COORDINATES, NEW_COORDINATES)


def parse_normalized(raw, original_row, canvas_size):
    result = parse_geometry(raw, {**original_row, "width": 1001, "height": 1001})
    geometry = result["geometry"]
    if geometry is not None:
        points = geometry["coordinates"]
        if any(not 0 <= value <= 1000 for point in points for value in point):
            raise ValueError("Normalized coordinates must lie in [0,1000]")
        converted = [[x / 1000 * canvas_size[0], y / 1000 * canvas_size[1]] for x, y in points]
        result["geometry"] = AtlasStore.geometry(
            {**geometry, "coordinates": converted}, original_row["width"], original_row["height"])
    return result


def read_json(path):
    return json.loads(path.read_text())


def prepare():
    if (HERE / "manifest.json").exists():
        raise ValueError("Frozen plan already exists")
    manifest, png, tasks, instruction = read_package(SOURCE)
    assert [r["event_id"] for r in tasks] == [f"Z{i:04d}" for i in range(1, 11)]
    original = Image.open(io.BytesIO(png)).convert("RGB")
    canvas, padding = pad_image_without_resampling(original, 32)
    assert original.size == (1538, 1754) and canvas.size == (1568, 1760)
    baseline_hashes = {}
    for key, directory in BASELINES.items():
        assert (directory / "input.zip").read_bytes() == SOURCE.read_bytes()
        baseline_hashes[key] = {name: digest((directory / name).read_bytes()) for name in
                                ("input.zip", "predictions.json", "predictions.attempts.jsonl")}
    for name, data in (("input.zip", SOURCE.read_bytes()), ("map.png", png)):
        (HERE / name).write_bytes(data)
    canvas.save(HERE / "model_canvas.png")
    prompt = normalized_instruction(instruction)
    (HERE / "prompt.txt").write_text(SYSTEM + prompt + "\n")
    save(HERE / "manifest.json", {
        "created_at": stamp(), "client_date": "2026-10-14", "map": manifest,
        "input_sha256": digest(SOURCE.read_bytes()), "padding": padding,
        "selected_event_ids": [r["event_id"] for r in tasks], "model": MODELS["instruct"],
        "generation_kwargs": SETTINGS, "seed": 0, "coordinate_mode": "normalized_1000",
        "conversion": "multiply by actual padded canvas width/height; validate original content bounds",
        "instruction": SYSTEM + prompt, "baseline_hashes": baseline_hashes,
        "spatial_exclusions": EXCLUDED, "outside_map_test": "Z0003",
        "protocol_sha256": digest((HERE / "PROTOCOL.md").read_bytes()),
        "source_hashes": {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in
                          (Path(__file__), ROOT / "benchmark/run_atlas_vlm.py", ROOT / "benchmark/run_qwen_thinking_eval.py")},
        "gold_not_loaded_during_inference": True,
    })
    print("Prepared ten requests; inference has not started")


def run(execute=False):
    config = read_json(HERE / "manifest.json")
    assert digest((HERE / "input.zip").read_bytes()) == config["input_sha256"]
    for name, expected in config["source_hashes"].items():
        assert digest((ROOT / name).read_bytes()) == expected
    manifest, png, tasks, original_instruction = read_package(HERE / "input.zip")
    instruction = normalized_instruction(original_instruction)
    assert config["instruction"] == SYSTEM + instruction
    print(json.dumps({"model": config["model"], "events": len(tasks), "settings": SETTINGS,
                      "coordinate_mode": config["coordinate_mode"]}, indent=2), flush=True)
    if not execute:
        print("Dry run; no model loaded")
        return
    if (HERE / "attempts.jsonl").exists():
        raise ValueError("Never overwrite or retry an existing attempt")
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import torch
    assert torch.backends.mps.is_available() or torch.cuda.is_available(), "GPU required"
    model_id, revision = MODELS["instruct"]
    model_path = CACHE / ("models--" + model_id.replace("/", "--")) / "snapshots" / revision
    local = load_local_qwen(str(model_path))
    assert next(local[0].parameters()).dtype == torch.float16
    ip = local[1].image_processor
    assert ip.patch_size * ip.merge_size == 32
    save(HERE / "local_config.json", {**local[2], "model_id": model_id, "revision": revision,
         "actual_generation_kwargs": SETTINGS, "checkpoint_generation_config": local[0].generation_config.to_dict()})
    (HERE / "runner.py.snapshot").write_bytes(Path(__file__).read_bytes())
    canvas_size = config["padding"]["canvas_size_wh"]
    results = {"map_version": manifest["map_version"], "model": model_id,
               "coordinate_system": "image_pixels_top_left", "model_output_coordinates": "normalized_1000",
               "predictions": [], "errors": []}
    attempts, stopped = [], False
    with (HERE / "attempts.jsonl").open("x", encoding="utf-8") as stream:
        for row in tasks:
            requested = {**row, "width": canvas_size[0], "height": canvas_size[1]}
            a = {"event_id": row["event_id"], "task": json.loads(task_prompt(requested)),
                 "original_task": row, "instruction": SYSTEM + instruction,
                 "coordinate_mode": "normalized_1000", "image_sha256": manifest["image_sha256"],
                 "max_output_tokens": 4096, "created_at": stamp()}
            print("Starting " + row["event_id"], flush=True)
            started = time.monotonic()
            try:
                a.update(infer(local, png, requested, instruction, 4096, False,
                               generation_kwargs=SETTINGS, seed=0))
                prep = a["usage"]["image_preprocessing"]
                assert prep["scale_xy"] == [1.0, 1.0]
                assert prep["canvas_rgb_sha256"] == config["padding"]["canvas_rgb_sha256"]
                a["final_answer"] = final_answer(a["raw"], False)
                prediction = parse_normalized(a["final_answer"], row, canvas_size)
                a.update(prediction=prediction, status="abstained" if prediction["geometry"] is None else "valid")
                results["predictions"].append(prediction)
            except Exception as exc:
                error = {"event_id": row["event_id"], "error_type": type(exc).__name__, "error": str(exc)}
                a.update(status="error", **error)
                results["errors"].append(error)
                stopped = "raw" not in a or isinstance(exc, AssertionError)
            a["elapsed_seconds"] = time.monotonic() - started
            stream.write(json.dumps(a, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            attempts.append(a)
            save(HERE / "predictions.json", results)
            save(HERE / "progress.json", {"attempted": len(attempts), "total": 10, "last": row["event_id"]})
            print(f"{row['event_id']}: {a['status']}, {a['elapsed_seconds']:.1f}s, tokens={a.get('usage', {}).get('output_tokens')}", flush=True)
            gc.collect()
            if local[0].device.type == "mps":
                torch.mps.empty_cache()
            if stopped:
                break
    save(HERE / "completed.json", {"completed_all_tasks": len(attempts) == 10,
         "stopped_on_backend_error": stopped, "attempted": len(attempts), "finished_at": stamp()})
    if stopped:
        raise SystemExit("Backend error; partial results preserved")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    prepare() if args.command == "prepare" else run(args.execute)
