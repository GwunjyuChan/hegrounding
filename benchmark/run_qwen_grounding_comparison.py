"""Compare direct grounding with text-answer-then-map grounding, offline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import time

from atlas_store import digest, stamp
from run_atlas_vlm import (SYSTEM, call_local_qwen, load_local_qwen,
                          parse_geometry, read_package, task_prompt)
from run_text_location_eval import INSTRUCTION, call_local, parse_answer


def text_task(row):
    return {"event_id": row["event_id"], "passage": row["text"], "question": row["question"]}


def grounding_task(row, answer):
    # Only model-generated fields cross stages; no full original passage or gold.
    parsed = parse_answer(json.dumps({k: answer[k] for k in
        ("event_id", "answer_location", "evidence_quotes", "uncertainty")}), text_task(row))
    if parsed["answer_location"] is None:
        raise ValueError("An abstention cannot be sent for map grounding")
    description = {k: parsed[k] for k in ("answer_location", "evidence_quotes", "uncertainty")}
    return {**row, "text": json.dumps(description, ensure_ascii=False)}


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def append_log(path, value):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")
        stream.flush()


def run_comparison(local, image, rows, instruction, manifest, output,
                   model_id, text_tokens=4096, map_tokens=4096):
    results = {key: {"map_version": manifest["map_version"],
                    "model": f"{model_id} [{key.replace('_', '-')}]",
                    "base_model": model_id, "method": key, "predictions": [], "errors": []}
               for key in ("direct", "two_stage")}
    stage1 = {"model": model_id, "answers": [], "errors": []}
    for key in ("direct", "stage1", "two_stage"):
        (output / key).mkdir()
    (output / "stage1" / "prompt.txt").write_text(INSTRUCTION + "\n")
    for key in ("direct", "two_stage"):
        (output / key / "prompt.txt").write_text(SYSTEM + instruction + "\n")

    def map_attempt(method, row):
        attempt = {"event_id": row["event_id"], "method": method, "model": model_id,
                   "created_at": stamp(), "image_sha256": manifest["image_sha256"],
                   "map_version": manifest["map_version"], "max_output_tokens": map_tokens,
                   "instruction": SYSTEM + instruction, "task": json.loads(task_prompt(row)),
                   "local_config": local[2]}
        started = time.monotonic()
        try:
            raw, usage = call_local_qwen(local, image, row, instruction, map_tokens)
            attempt.update(raw=raw, usage=usage)
            prediction = parse_geometry(raw, row)
            results[method]["predictions"].append(prediction)
            attempt["status"] = "abstained" if prediction["geometry"] is None else "valid"
        except Exception as exc:
            error = {"event_id": row["event_id"], "error_type": type(exc).__name__}
            results[method]["errors"].append(error)
            attempt.update(status="error", **error)
        attempt["elapsed_seconds"] = time.monotonic() - started
        append_log(output / method / "attempts.jsonl", attempt)
        print(f"{row['event_id']} {method}: {attempt['status']}", flush=True)

    # Independent prompts per call. Alternate method order to reduce order bias.
    for index, row in enumerate(rows):
        if index % 2 == 0:
            map_attempt("direct", row)
        task = text_task(row)
        attempt = {"event_id": row["event_id"], "method": "stage1", "model": model_id,
                   "task": task, "instruction": INSTRUCTION, "created_at": stamp(),
                   "max_output_tokens": text_tokens, "local_config": local[2]}
        started = time.monotonic()
        answer = None
        try:
            raw, usage, meta = call_local(local, task, text_tokens)
            attempt.update(raw=raw, usage=usage, **meta)
            answer = parse_answer(raw, task)
            answer["quote_not_verbatim"] = [q for q in answer["evidence_quotes"] if q not in task["passage"]]
            stage1["answers"].append(answer)
            attempt["status"] = "abstained" if answer["answer_location"] is None else "answered"
        except Exception as exc:
            error = {"event_id": row["event_id"], "error_type": type(exc).__name__}
            stage1["errors"].append(error)
            attempt.update(status="error", **error)
        attempt["elapsed_seconds"] = time.monotonic() - started
        append_log(output / "stage1" / "attempts.jsonl", attempt)
        print(f"{row['event_id']} stage1: {attempt['status']}", flush=True)
        if answer is None or answer["answer_location"] is None:
            status = "upstream_error" if answer is None else "upstream_abstained"
            if answer is None:
                results["two_stage"]["errors"].append({"event_id": row["event_id"], "error_type": "Stage1Error"})
            else:
                results["two_stage"]["predictions"].append({"event_id": row["event_id"], "geometry": None})
            append_log(output / "two_stage" / "attempts.jsonl", {
                "event_id": row["event_id"], "method": "two_stage", "status": status,
                "map_call_skipped": True, "elapsed_seconds": 0, "usage": None})
        else:
            map_attempt("two_stage", grounding_task(row, answer))
        if index % 2:
            map_attempt("direct", row)
        # Save complete-so-far outputs after every event; raw attempts are append-only.
        for key in results:
            (output / key / "predictions.json").write_text(json.dumps(results[key], ensure_ascii=False, indent=2) + "\n")
        (output / "stage1" / "answers.json").write_text(json.dumps(stage1, ensure_ascii=False, indent=2) + "\n")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Clean, frozen atlas input ZIP")
    parser.add_argument("--output-dir", type=Path, required=True, help="New run directory; never overwrite")
    parser.add_argument("--model", default="Qwen/Qwen3-VL-8B-Instruct")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--text-max-tokens", type=int, default=4096)
    parser.add_argument("--map-max-tokens", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if min(args.limit, args.text_max_tokens, args.map_max_tokens) <= 0:
        parser.error("Limits must be positive")
    manifest, image, rows, instruction = read_package(args.input)
    rows = rows[:args.limit]
    print(f"{len(rows)} events; direct + text-only stage1 + derived-text/map stage2", flush=True)
    if not args.execute:
        print("Dry run: no model loaded, no files written, no API calls")
        return
    args.output_dir.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(args.input, args.output_dir / "input.zip")
    write_json(args.output_dir / "manifest.json", {
        **manifest, "selected_event_ids": [r["event_id"] for r in rows], "model": args.model,
        "input_package_sha256": digest(args.input.read_bytes()), "created_at": stamp(),
        "text_max_tokens": args.text_max_tokens, "map_max_tokens": args.map_max_tokens,
        "seed": args.seed, "do_sample": False, "interleave": "alternate_direct_first",
        "stage2_input": "model_answer+model_quotes+model_uncertainty+original_question+map; no full original passage",
        "gold_access": "none; scoring is a separate offline process", "execution_status": "started"})
    import torch
    torch.manual_seed(args.seed)
    local = load_local_qwen(args.model)
    write_json(args.output_dir / "local_config.json", local[2])
    results = run_comparison(local, image, rows, instruction, manifest, args.output_dir,
                             args.model, args.text_max_tokens, args.map_max_tokens)
    write_json(args.output_dir / "completed.json", {"created_at": stamp(), "events": len(rows),
        "methods": {k: {"parsed": len(v["predictions"]), "errors": len(v["errors"])} for k, v in results.items()}})
    print(json.dumps({k: {"parsed": len(v["predictions"]), "errors": len(v["errors"])} for k, v in results.items()}))
    if any(r["errors"] for r in results.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
