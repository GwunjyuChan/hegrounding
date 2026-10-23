"""Instruct positive controls for the shared local image-grounding pipeline."""
import argparse
import gc
import json
import os
from pathlib import Path
import time

from PIL import Image
from run import HERE, CACHE, MODELS, load_local_qwen, image_preprocessing_metadata
from run_single import calls, parse_single
from run_atlas_vlm import digest, stamp
from run_qwen_thinking_eval import final_answer, save


def infer(local, call):
    import torch
    model, processor, _ = local
    image = Image.open(HERE / "inputs" / call["image"]).convert("RGB")
    messages = [{"role": "system", "content": call["system"]},
                {"role": "user", "content": [{"type": "text", "text": json.dumps(call["user"], ensure_ascii=False)},
                                              {"type": "image", "image": image}]}]
    template = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    assert not template.rstrip().endswith("<think>")
    inputs = processor(text=[template], images=[image], do_resize=False, padding=True, return_tensors="pt")
    prep = image_preprocessing_metadata(processor, image.size, inputs["image_grid_thw"].tolist())
    image_tokens = int((inputs["input_ids"] == model.config.image_token_id).sum())
    assert prep["processed_size_wh"] == list(image.size) and prep["scale_xy"] == [1.0, 1.0]
    assert image_tokens == prep["visual_tokens"] > 0 and bool(torch.isfinite(inputs["pixel_values"]).all())
    prep.update(image_rgb_sha256=digest(image.tobytes()), pixel_values_shape=list(inputs["pixel_values"].shape))
    inputs = inputs.to(model.device)
    count = inputs["input_ids"].shape[1]
    torch.manual_seed(0)
    with torch.inference_mode():
        result = model.generate(**inputs, do_sample=False, max_new_tokens=4096)
    tokens = result[0, count:].tolist()
    return {"raw": processor.decode(tokens, skip_special_tokens=True).strip(), "generated_token_ids": tokens,
            "raw_with_special_tokens": processor.decode(tokens, skip_special_tokens=False),
            "rendered_prompt_sha256": digest(template.encode()), "chat_template_sha256": digest(processor.chat_template.encode()),
            "usage": {"input_tokens": count, "output_tokens": len(tokens), "image_tokens": image_tokens,
                      "image_preprocessing": prep, "reached_token_limit": len(tokens) >= 4096}}


def main(execute=False):
    selected = [{**c, "id": c["id"].replace("single_", "instruct_", 1)} for c in calls()[:4]]
    print(json.dumps({"model": MODELS["instruct"], "calls": [c["id"] for c in selected], "do_sample": False, "max_new_tokens": 4096}, indent=2), flush=True)
    if not execute:
        print("Dry run; no model loaded")
        return
    completed = json.loads((HERE / "single/completed.json").read_text())
    assert completed["stop_reason"] != "backend_error"
    source_plan = json.loads((HERE / "inputs/plan.json").read_text())
    for name, expected_hash in source_plan["image_hashes"].items():
        assert digest((HERE / "inputs" / name).read_bytes()) == expected_hash
    out = HERE / "instruct_control"
    out.mkdir()
    save(out / "plan.json", {"calls": selected, "model": MODELS["instruct"], "do_sample": False, "max_new_tokens": 4096,
                              "runner_sha256": digest(Path(__file__).read_bytes()), "scope": "positive control, not model ranking"})
    (out / "runner.py.snapshot").write_bytes(Path(__file__).read_bytes())
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import torch
    assert torch.backends.mps.is_available() or torch.cuda.is_available()
    model_id, revision = MODELS["instruct"]
    path = CACHE / ("models--" + model_id.replace("/", "--")) / "snapshots" / revision
    local = load_local_qwen(str(path))
    assert next(local[0].parameters()).dtype == torch.float16
    local[2].update(model_id=model_id, revision=revision, actual_generation_kwargs={"do_sample": False, "max_new_tokens": 4096})
    save(out / "local_config.json", local[2])
    attempts, stopped = [], False
    with (out / "attempts.jsonl").open("x", encoding="utf-8") as stream:
        for c in selected:
            print("Starting " + c["id"], flush=True)
            a = {**c, "created_at": stamp()}
            started = time.monotonic()
            try:
                a.update(infer(local, c))
                a["final_answer"] = final_answer(a["raw"], False)
                a["prediction"] = parse_single(a["final_answer"], c)
                a["status"] = "valid"
            except Exception as exc:
                a.update(status="error", error_type=type(exc).__name__, error=str(exc))
                stopped = "raw" not in a
            a["elapsed_seconds"] = time.monotonic()-started
            stream.write(json.dumps(a, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            attempts.append(a)
            print(f"{c['id']}: {a['status']}, {a['elapsed_seconds']:.1f}s, tokens={a.get('usage', {}).get('output_tokens')}", flush=True)
            gc.collect()
            if local[0].device.type == "mps":
                torch.mps.empty_cache()
            if stopped:
                break
    save(out / "completed.json", {"completed_all_tasks": len(attempts) == 4, "stopped_on_backend_error": stopped, "finished_at": stamp()})
    if stopped:
        raise SystemExit("Backend error")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    main(parser.parse_args().execute)
