"""Frozen ten-question API run. No gold is loaded during inference."""
import argparse
import base64
import json
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
from run_atlas_vlm import SYSTEM, digest, load_env_file, parse_geometry, read_package, stamp, task_prompt

MODEL = "gpt-6-astra"
SOURCE = HERE.parent / "zurich10_20260916_162847/input.zip"


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    manifest, png, tasks, instruction = read_package(SOURCE)
    assert [t["event_id"] for t in tasks] == [f"Z{i:04d}" for i in range(1, 11)]
    assert manifest["image_sha256"] == "fc5f835f11cd6f7cafefc7183b57d10c0911372149a1c2077f662a6d70570aec"
    print(f"{MODEL}: {len(tasks)} tasks, original {tasks[0]['width']}x{tasks[0]['height']} PNG", flush=True)
    if not args.execute:
        print("Dry run. No API calls.")
        return
    output = HERE / "predictions.json"
    audit = HERE / "predictions.attempts.jsonl"
    if output.exists() or audit.exists():
        raise SystemExit("Existing results: refusing to repeat paid calls or overwrite history")
    from openai import OpenAI
    load_env_file(ROOT / ".env")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url="https://api.openai.com/v1",
                    timeout=120, max_retries=0)
    (HERE / "input.zip").write_bytes(SOURCE.read_bytes())
    (HERE / "map.png").write_bytes(png)
    (HERE / "prompt.txt").write_text(instruction)
    save(HERE / "manifest.json", {
        "created_at": stamp(), "model": MODEL, "api": "responses", "base_url": str(client.base_url),
        "input_sha256": digest(SOURCE.read_bytes()), "map": manifest,
        "event_ids": [t["event_id"] for t in tasks], "max_output_tokens": 4096,
        "reasoning_effort": "provider default (not explicitly set)",
        "image_detail": "provider default (not explicitly set)",
        "image_policy": "Original PNG bytes, no client resize; provider preprocessing unverified",
        "timeout_seconds": 120, "max_retries": 0, "store": False,
        "spatial_exclusions_declared_before_run": ["Z0009", "Z0010"],
        "outside_map_diagnostic": ["Z0003"], "runner_sha256": digest(Path(__file__).read_bytes()),
    })
    result = {"map_version": manifest["map_version"], "model": MODEL, "predictions": [], "errors": []}
    data_url = "data:image/png;base64," + base64.b64encode(png).decode()
    stopped = False
    with audit.open("x") as stream:
        for row in tasks:
            attempt = {"event_id": row["event_id"], "map_version": manifest["map_version"],
                       "image_sha256": manifest["image_sha256"], "model": MODEL,
                       "api": "responses", "created_at": stamp(), "max_output_tokens": 4096,
                       "instruction": SYSTEM + instruction, "task": row}
            started = time.monotonic()
            try:
                response = client.responses.create(
                    model=MODEL, store=False, instructions=SYSTEM + instruction,
                    input=[{"role": "user", "content": [
                        {"type": "input_text", "text": task_prompt(row)},
                        {"type": "input_image", "image_url": data_url}]}], max_output_tokens=4096)
                attempt.update(raw=response.output_text, usage=response.usage.model_dump() if response.usage else None,
                               response_id=response.id, response_model=response.model, response_status=response.status,
                               incomplete_details=response.incomplete_details.model_dump() if response.incomplete_details else None,
                               response_reasoning=response.reasoning.model_dump() if response.reasoning else None)
                prediction = parse_geometry(response.output_text, row)
                result["predictions"].append(prediction)
                attempt["status"] = "abstained" if prediction["geometry"] is None else "valid"
            except Exception as exc:
                attempt.update(status="error", error_type=type(exc).__name__)
                status = getattr(exc, "status_code", None)
                body = getattr(exc, "body", None)
                details = body.get("error", body) if isinstance(body, dict) else {}
                code = details.get("code") if isinstance(details, dict) else None
                attempt.update(http_status=status, api_error_code=code)
                result["errors"].append({"event_id": row["event_id"], "error_type": type(exc).__name__,
                                         "http_status": status, "api_error_code": code})
                # Stop on endpoint/auth/rate failures, preserving any completed paid calls.
                stopped = status is not None or type(exc).__name__ in {"APIConnectionError", "APITimeoutError"}
            attempt["elapsed_seconds"] = time.monotonic() - started
            stream.write(json.dumps(attempt, ensure_ascii=False) + "\n")
            stream.flush()
            save(output, result)
            print(f"{row['event_id']}: {attempt['status']} ({attempt['elapsed_seconds']:.1f}s)"
                  + (f" {attempt.get('error_type')} {attempt.get('api_error_code')}" if attempt['status'] == 'error' else ''), flush=True)
            if stopped:
                break
    attempted = {p["event_id"] for p in result["predictions"] + result["errors"]}
    save(HERE / "completed.json", {"finished_at": stamp(), "completed_all_tasks": len(attempted) == len(tasks),
                                   "stopped_on_api_error": stopped, "unattempted": [r["event_id"] for r in tasks if r["event_id"] not in attempted]})
    print(f"Saved {output}", flush=True)


if __name__ == "__main__":
    main()
