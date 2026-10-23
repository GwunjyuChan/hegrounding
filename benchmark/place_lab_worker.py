"""Load the local model once; independently predict each allowlisted label."""
import json
from pathlib import Path
import sys
import time

from place_diagnostics import instruction, parse_point
from run_atlas_vlm import call_local_qwen, load_local_qwen, SYSTEM


def predict(local, image, task, payload):
    started = time.monotonic()
    result = {"task_id": task["event_id"], "status": "error"}
    try:
        raw, usage = call_local_qwen(local, image, task, instruction(payload["coordinate_mode"]), payload["max_tokens"])
        result.update(raw=raw, usage=usage)
        prediction = parse_point(raw, task, payload["coordinate_mode"])
        result.update(prediction=prediction, status="valid" if prediction["geometry"] else "abstained")
    except Exception as exc:
        result["error_type"] = type(exc).__name__
    result["elapsed_seconds"] = time.monotonic() - started
    return result


def main(directory):
    payload = json.loads((directory / "input.json").read_text())
    result = {"status": "error", "instruction": SYSTEM + instruction(payload["coordinate_mode"])}
    started = time.monotonic()
    try:
        local = load_local_qwen(payload["model"])
        result["local_config"] = local[2]
        image = (directory / "map.png").read_bytes()
        if "tasks" in payload:
            result["results"] = []
            for task in payload["tasks"]:
                item = predict(local, image, task, payload)
                result["results"].append(item)
                # Preserve each completed response even if a later inference is interrupted.
                with (directory / "responses.jsonl").open("a") as f:
                    f.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n")
                progress = directory / "progress.tmp"
                progress.write_text(json.dumps({"done": len(result["results"]), "total": len(payload["tasks"])}))
                progress.replace(directory / "progress.json")
            result["status"] = "completed"
        else:
            result.update(predict(local, image, payload["task"], payload))
    except Exception as exc:
        result["error_type"] = type(exc).__name__
    result["elapsed_seconds"] = time.monotonic()-started
    (directory / "result.json").write_text(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return int(result["status"] == "error")


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
