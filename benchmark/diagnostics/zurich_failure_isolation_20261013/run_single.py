"""Adaptive one-label follow-up; preserves the original partial multi-label run."""
import argparse
import gc
import json
import os
from pathlib import Path
import time

from run import HERE, CACHE, MODELS, BUDGET, build_calls, convert_point, infer, load_local_qwen, parse_answer, parse_json
from run_atlas_vlm import digest, stamp
from run_qwen_thinking_eval import final_answer, generation_settings, save


def calls():
    original = build_calls()
    selected = []
    for image_name in ("synthetic.png", "full.png"):
        for mode in ("normalized_1000", "pixels"):
            c = next(c for c in original if c["image"] == image_name and c["kind"] == "labels" and c["seed"] == 0 and c["mode"] == mode)
            selected.append({**c, "id": "single_" + c["id"], "user": {**c["user"], "names": ["Altstetten"]}})
    for c in original:
        if c["image"] and c["image"].startswith("tile_"):
            selected.append({**c, "id": "single_" + c["id"], "user": {**c["user"], "names": ["Altstetten"]}})
    selected += [{**c, "id": "single_" + c["id"]} for c in original if c["kind"] == "event"]
    assert len(selected) == 12
    return selected


def parse_single(text, call):
    if call["kind"] != "labels":
        return parse_answer(text, call)
    answer = parse_json(text)
    rows = answer.get("labels")
    if not isinstance(rows, list) or len(rows) != 1 or rows[0].get("name") != "Altstetten":
        raise ValueError("Expected exactly one Altstetten label")
    point = convert_point(rows[0]["point"], call["user"]["width"], call["user"]["height"], call["mode"])
    return {"labels": [{"name": "Altstetten", "point": point}]}


def main(execute):
    plan = {"calls": calls(), "settings": generation_settings("thinking", "hf-thinking-vl", BUDGET),
            "runner_sha256": digest(Path(__file__).read_bytes()), "shared_runner_sha256": digest((HERE / "run.py").read_bytes()),
            "reference_sha256_not_sent_to_model": digest((HERE / "reference/labels.json").read_bytes()),
            "adaptation_sha256": digest((HERE / "ADAPTATION.md").read_bytes()),
            "input_plan_sha256": digest((HERE / "inputs/plan.json").read_bytes()),
            "gate": "stop if neither single-target synthetic control has a valid final answer"}
    print(json.dumps({"calls": len(plan["calls"]), "settings": plan["settings"], "gate": plan["gate"]}, indent=2), flush=True)
    if not execute:
        print("Dry run; no model loaded")
        return
    out = HERE / "single"
    out.mkdir()
    save(out / "plan.json", plan)
    (out / "runner.py.snapshot").write_bytes(Path(__file__).read_bytes())
    source_plan = json.loads((HERE / "inputs/plan.json").read_text())
    for name, hash_value in source_plan["image_hashes"].items():
        assert digest((HERE / "inputs" / name).read_bytes()) == hash_value
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import torch
    assert torch.backends.mps.is_available() or torch.cuda.is_available()
    model_id, revision = MODELS["thinking"]
    model_path = CACHE / ("models--" + model_id.replace("/", "--")) / "snapshots" / revision
    local = load_local_qwen(str(model_path))
    assert next(local[0].parameters()).dtype == torch.float16
    local[2].update(model_id=model_id, revision=revision, do_sample=True, actual_generation_kwargs=plan["settings"])
    save(out / "local_config.json", local[2])
    attempts, reason = [], None
    with (out / "attempts.jsonl").open("x", encoding="utf-8") as stream:
        for c in plan["calls"]:
            if len(attempts) == 2 and not any(a["status"] == "valid" for a in attempts):
                reason = "single_target_calibration_completion_gate"
                break
            a = {**c, "created_at": stamp(), "generation_kwargs": plan["settings"]}
            started = time.monotonic()
            print(f"Starting {len(attempts)+1}/12 {c['id']}", flush=True)
            try:
                a.update(infer(local, c, HERE / "inputs" / c["image"], plan["settings"]))
                a["final_answer"] = final_answer(a["raw"], True)
                a["prediction"] = parse_single(a["final_answer"], c)
                a["status"] = "valid"
            except Exception as exc:
                a.update(status="error", error_type=type(exc).__name__, error=str(exc))
                if "raw" not in a:
                    reason = "backend_error"
            a["elapsed_seconds"] = time.monotonic()-started
            stream.write(json.dumps(a, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            attempts.append(a)
            save(out / "progress.json", {"attempted": len(attempts), "total": 12, "last_id": c["id"], "last_status": a["status"]})
            print(f"{c['id']}: {a['status']}, {a['elapsed_seconds']:.1f}s, tokens={a.get('usage', {}).get('output_tokens')}, {a.get('error', '')}", flush=True)
            gc.collect()
            if local[0].device.type == "mps":
                torch.mps.empty_cache()
            if reason:
                break
    save(out / "completed.json", {"completed_all_tasks": len(attempts) == 12, "stop_reason": reason,
                                   "finished_at": stamp(), "attempted": len(attempts),
                                   "unattempted": [c["id"] for c in plan["calls"] if c["id"] not in {a["id"] for a in attempts}]})
    if reason == "backend_error":
        raise SystemExit("Backend failure; inspect audit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    main(parser.parse_args().execute)
