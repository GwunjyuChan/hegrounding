"""Predeclared local ablations separating text, vision, and coordinate conventions."""
from __future__ import annotations

import argparse
import gc
import io
import json
import math
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "benchmark"))

from PIL import Image, ImageDraw, ImageFont
from atlas_store import AtlasStore
from run_atlas_vlm import SYSTEM, digest, image_preprocessing_metadata, load_local_qwen, pad_image_without_resampling, parse_geometry, read_package, stamp
from run_qwen_thinking_eval import CACHE, MODELS, SOURCE, GenerationProgress, final_answer, generation_settings, save

NAMES = ["Altstetten", "ZURICH", "Regensdorf"]
EVENTS = ["Z0003", "Z0004"]
BUDGET = 4096
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
TILES = {"TL": [0, 0, 800, 896], "TR": [800, 0, 1568, 896],
         "BL": [0, 896, 800, 1760], "BR": [800, 896, 1568, 1760]}


def coordinates(mode):
    base = "The origin is top left; x increases rightward and y downward. "
    if mode == "pixels":
        return base + "Use image pixel coordinates: 0 <= x < width, 0 <= y < height."
    if mode == "normalized_1000":
        return base + ("Use relative coordinates from 0 to 1000 on each axis, NOT pixel coordinates. "
                       "The right image edge is x=1000 and the bottom edge is y=1000.")
    raise ValueError("Unknown coordinate mode")


def label_prompt(mode):
    return ("Locate the center of each requested printed place-name label in the supplied image. "
            "Locate the printed text itself, not a settlement symbol, geographic center or event. "
            "Case and diacritics may differ; do not substitute a different or qualified name. "
            "Use null if the complete requested label cannot be identified in this image. "
            "Return JSON only: {\"labels\":[{\"name\":\"requested name\",\"point\":[x,y]}]}. "
            "Include exactly one entry per requested name; point may be null. " + coordinates(mode))


def build_calls():
    _, _, rows, instruction = read_package(SOURCE)
    rows = {r["event_id"]: r for r in rows}
    calls = []
    for eid in EVENTS:
        calls.append({"id": f"text_{eid}", "kind": "text", "seed": 0, "image": None,
                      "mode": None, "event_id": eid,
                      "system": SYSTEM + "Answer the question using only the passage. Return JSON only with event_id and place, where place is the place name or null if unsupported. Do not give coordinates.",
                      "user": {"event_id": eid, "passage": rows[eid]["text"], "question": rows[eid]["question"]}})
    for image_name, seeds in (("synthetic", [0]), ("full", [0, 1])):
        for seed in seeds:
            modes = ("pixels", "normalized_1000") if seed == 0 else ("normalized_1000", "pixels")
            for mode in modes:
                calls.append({"id": f"labels_{image_name}_{mode}_s{seed}", "kind": "labels", "seed": seed,
                              "image": f"{image_name}.png", "mode": mode, "system": label_prompt(mode),
                              "user": {"width": 1568, "height": 1760, "names": NAMES}})
    for tile, (x0, y0, x1, y1) in TILES.items():
        calls.append({"id": f"labels_tile_{tile}", "kind": "labels", "seed": 0,
                      "image": f"tile_{tile}.png", "mode": "normalized_1000", "system": label_prompt("normalized_1000"),
                      "user": {"width": x1-x0, "height": y1-y0, "names": NAMES}})
    original_coordinates = "Use original image pixels, origin at top left, x rightward, y downward."
    assert instruction.count(original_coordinates) == 1
    for eid in EVENTS:
        for mode in ("pixels", "normalized_1000"):
            calls.append({"id": f"event_{eid}_{mode}", "kind": "event", "seed": 0,
                          "image": "full.png", "mode": mode, "event_id": eid,
                          "system": SYSTEM + instruction.replace(original_coordinates, coordinates(mode)),
                          "user": {"event_id": eid, "width": 1568, "height": 1760,
                                   "passage": rows[eid]["text"], "question": rows[eid]["question"]}})
    assert len(calls) == 16 and len({c["id"] for c in calls}) == 16
    return calls


def prepare():
    inputs = HERE / "inputs"
    if inputs.exists():
        raise ValueError("Inputs already prepared; do not overwrite the frozen plan")
    manifest, png, _, _ = read_package(SOURCE)
    image = Image.open(io.BytesIO(png)).convert("RGB")
    assert image.size == (1538, 1754)
    padded, padding = pad_image_without_resampling(image, 32)
    assert padded.size == (1568, 1760)
    inputs.mkdir()
    (inputs / "input.zip").write_bytes(SOURCE.read_bytes())
    padded.save(inputs / "full.png")
    for tile, box in TILES.items():
        padded.crop(box).save(inputs / f"tile_{tile}.png")
    synthetic = Image.new("RGB", padded.size, "white")
    draw = ImageDraw.Draw(synthetic)
    font = ImageFont.truetype(FONT, 40)
    label_boxes = {}
    for name, center in zip(NAMES, ((240, 320), (1110, 720), (650, 1490))):
        draw.text(center, name, font=font, anchor="mm", fill="black")
        label_boxes[name] = list(draw.textbbox(center, name, font=font, anchor="mm"))
    synthetic.save(inputs / "synthetic.png")
    review = HERE / "reference"
    review.mkdir()
    image.crop((700, 150, 1220, 470)).save(review / "label_inspection.png")
    save(review / "synthetic_boxes.json", {"source": "known rendering bounds, not model predictions", "boxes": label_boxes})
    save(inputs / "plan.json", {"created_at": stamp(), "source": str(SOURCE), "source_sha256": digest(SOURCE.read_bytes()),
                                "source_map": manifest, "native_pixel_check": padding, "tiles": TILES,
                                "model": MODELS["thinking"], "generation_kwargs": generation_settings("thinking", "hf-thinking-vl", BUDGET),
                                "calls": build_calls(), "image_hashes": {p.name: digest(p.read_bytes()) for p in sorted(inputs.glob("*.png"))}})
    print("Prepared 16 calls; reference labels are separate and never loaded by inference")


def parse_json(text):
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object")
    return result


def convert_point(point, width, height, mode):
    if point is None:
        return None
    if not isinstance(point, list) or len(point) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) for v in point):
        raise ValueError("Expected a finite numeric [x,y] point")
    if mode == "normalized_1000":
        if any(not 0 <= v <= 1000 for v in point):
            raise ValueError("Relative point outside [0,1000]")
        point = [point[0] / 1000 * width, point[1] / 1000 * height]
    elif mode != "pixels":
        raise ValueError("Unknown coordinate mode")
    AtlasStore.geometry({"type": "point", "coordinates": [point]}, width, height)
    return point


def parse_answer(text, call):
    answer = parse_json(text)
    if call["kind"] == "text":
        if answer.get("event_id") != call["event_id"] or "place" not in answer:
            raise ValueError("Wrong event or missing place")
        if answer["place"] is not None and not isinstance(answer["place"], str):
            raise ValueError("Place must be a string or null")
        return answer
    width, height = call["user"]["width"], call["user"]["height"]
    if call["kind"] == "labels":
        labels = answer.get("labels")
        if not isinstance(labels, list) or len(labels) != len(NAMES):
            raise ValueError("Expected all requested labels")
        if sorted(r.get("name", "") for r in labels) != sorted(NAMES):
            raise ValueError("Missing, duplicate or unexpected names")
        return {"labels": [{"name": r["name"], "point": convert_point(r["point"], width, height, call["mode"])} for r in labels]}
    row = {"event_id": call["event_id"], "width": width, "height": height}
    if call["mode"] == "pixels":
        return parse_geometry(json.dumps(answer), row)
    result = parse_geometry(json.dumps(answer), {**row, "width": 1001, "height": 1001})
    if result["geometry"]:
        points = [convert_point(p, width, height, call["mode"]) for p in result["geometry"]["coordinates"]]
        result["geometry"] = AtlasStore.geometry({**result["geometry"], "coordinates": points}, width, height)
    return result


def infer(local, call, image_path, settings):
    import torch

    model, processor, _ = local
    content = [{"type": "text", "text": json.dumps(call["user"], ensure_ascii=False)}]
    image = Image.open(image_path).convert("RGB") if image_path else None
    if image:
        assert list(image.size) == [call["user"]["width"], call["user"]["height"]]
        content.append({"type": "image", "image": image})
    messages = [{"role": "system", "content": call["system"]}, {"role": "user", "content": content}]
    template = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    assert template.rstrip().endswith("<think>")
    kwargs = {"images": [image], "do_resize": False} if image else {}
    inputs = processor(text=[template], padding=True, return_tensors="pt", **kwargs)
    vision_count = int((inputs["input_ids"] == model.config.image_token_id).sum())
    preprocessing = None
    if image:
        preprocessing = image_preprocessing_metadata(processor, image.size, inputs["image_grid_thw"].tolist())
        assert preprocessing["processed_size_wh"] == list(image.size)
        assert preprocessing["scale_xy"] == [1.0, 1.0]
        assert vision_count == preprocessing["visual_tokens"] > 0
        pixels = inputs["pixel_values"]
        assert bool(torch.isfinite(pixels).all())
        preprocessing.update(image_rgb_sha256=digest(image.tobytes()), pixel_values_shape=list(pixels.shape),
                             tensor_min=float(pixels.min()), tensor_max=float(pixels.max()))
    else:
        assert vision_count == 0 and "pixel_values" not in inputs
    inputs = inputs.to(model.device)
    count = inputs["input_ids"].shape[1]
    torch.manual_seed(call["seed"])
    with torch.inference_mode():
        output = model.generate(**inputs, **settings, streamer=GenerationProgress())
    tokens = output[0, count:].tolist()
    end_id = processor.tokenizer.convert_tokens_to_ids("</think>")
    thinking_count = tokens.index(end_id) + 1 if end_id in tokens else len(tokens)
    eos_ids = model.generation_config.eos_token_id
    eos_ids = [eos_ids] if isinstance(eos_ids, int) else eos_ids or []
    return {"raw": processor.decode(tokens, skip_special_tokens=True).strip(),
            "raw_with_special_tokens": processor.decode(tokens, skip_special_tokens=False), "generated_token_ids": tokens,
            "rendered_prompt_sha256": digest(template.encode()), "chat_template_sha256": digest(processor.chat_template.encode()),
            "usage": {"input_tokens": count, "output_tokens": len(tokens), "thinking_tokens": thinking_count,
                      "answer_tokens": len(tokens)-thinking_count, "thinking_completed": end_id in tokens,
                      "reached_token_limit": len(tokens) >= settings["max_new_tokens"],
                      "stop_reason": "eos" if tokens and tokens[-1] in eos_ids else "token_limit" if len(tokens) >= settings["max_new_tokens"] else "other",
                      "image_tokens": vision_count, "image_preprocessing": preprocessing}}


def run(execute, resume):
    plan_path = HERE / "inputs/plan.json"
    plan = json.loads(plan_path.read_text())
    assert plan["calls"] == build_calls()
    assert plan["generation_kwargs"] == generation_settings("thinking", "hf-thinking-vl", BUDGET)
    for name, hash_value in plan["image_hashes"].items():
        assert digest((HERE / "inputs" / name).read_bytes()) == hash_value
    print(json.dumps({"calls": len(plan["calls"]), "model": plan["model"], "settings": plan["generation_kwargs"]}, indent=2), flush=True)
    if not execute:
        print("Dry run; no model loaded")
        return
    out = HERE / "run"
    if out.exists() and not resume:
        raise ValueError("Run exists; resume only unattempted calls")
    frozen = {"plan_sha256": digest(plan_path.read_bytes()), "runner_sha256": digest(Path(__file__).read_bytes()),
              "reference_loaded_during_inference": False}
    out.mkdir(exist_ok=True)
    if (out / "manifest.json").exists():
        assert json.loads((out / "manifest.json").read_text()) == frozen
    else:
        save(out / "manifest.json", frozen)
        (out / "runner.py.snapshot").write_bytes(Path(__file__).read_bytes())
    audit = out / "attempts.jsonl"
    attempts = [json.loads(line) for line in audit.read_text().splitlines()] if audit.exists() else []
    done = {a["id"] for a in attempts}
    assert len(done) == len(attempts)
    pending = [c for c in plan["calls"] if c["id"] not in done]
    if not pending:
        print("All calls already attempted")
        return
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import torch
    assert torch.backends.mps.is_available() or torch.cuda.is_available(), "GPU required"
    model_id, revision = MODELS["thinking"]
    model_path = CACHE / ("models--" + model_id.replace("/", "--")) / "snapshots" / revision
    local = load_local_qwen(str(model_path))
    assert next(local[0].parameters()).dtype == torch.float16
    local[2].update(model_id=model_id, revision=revision, do_sample=True,
                    actual_generation_kwargs=plan["generation_kwargs"], checkpoint_generation_config=local[0].generation_config.to_dict())
    save(out / "local_config.json", local[2])
    stopped = False
    with audit.open("a", encoding="utf-8") as stream:
        for call in pending:
            print(f"Starting {len(attempts)+1}/16 {call['id']}", flush=True)
            attempt = {**call, "created_at": stamp(), "generation_kwargs": plan["generation_kwargs"]}
            started = time.monotonic()
            try:
                image_path = HERE / "inputs" / call["image"] if call["image"] else None
                attempt.update(infer(local, call, image_path, plan["generation_kwargs"]))
                attempt["final_answer"] = final_answer(attempt["raw"], True)
                attempt["prediction"] = parse_answer(attempt["final_answer"], call)
                attempt["status"] = "valid"
            except Exception as exc:
                attempt.update(status="error", error_type=type(exc).__name__, error=str(exc))
                stopped = "raw" not in attempt
            attempt["elapsed_seconds"] = time.monotonic()-started
            stream.write(json.dumps(attempt, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            attempts.append(attempt)
            save(out / "progress.json", {"attempted": len(attempts), "total": 16, "last_id": call["id"], "last_status": attempt["status"]})
            print(f"{call['id']}: {attempt['status']}, {attempt['elapsed_seconds']:.1f}s, tokens={attempt.get('usage', {}).get('output_tokens')}, {attempt.get('error', '')}", flush=True)
            gc.collect()
            if local[0].device.type == "mps":
                torch.mps.empty_cache()
            if stopped:
                break
    save(out / "completed.json", {"completed_all_tasks": len(attempts) == 16, "stopped_on_backend_error": stopped,
                                   "finished_at": stamp(), "unattempted": [c["id"] for c in plan["calls"] if c["id"] not in {a["id"] for a in attempts}]})
    if stopped:
        raise SystemExit("Backend failure; remaining calls not attempted")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run"))
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    else:
        run(args.execute, args.resume)
