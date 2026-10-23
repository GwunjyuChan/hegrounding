"""Submit all saved place annotations on one active map to the local GUI server."""
import argparse
import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request(base, path, body=None, csrf=None):
    headers = {"Origin": base}
    if body is not None:
        headers.update({"Content-Type": "application/json", "X-CSRF-Token": csrf})
    req = Request(base + path, data=None if body is None else json.dumps(body).encode(), headers=headers)
    try:
        with urlopen(req, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        raise ValueError(json.load(exc).get("error", str(exc))) from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8769)
    parser.add_argument("--map-id", help="Required when the service has multiple maps")
    parser.add_argument("--coordinate-mode", choices=("normalized_1000", "pixels"), default="normalized_1000")
    parser.add_argument("--execute", action="store_true", help="Run inference; otherwise preview the saved selection")
    args = parser.parse_args(argv)
    base = f"http://127.0.0.1:{args.port}"
    catalog = request(base, "/api/atlas")
    maps = catalog["maps"]
    mid = args.map_id or (maps[0]["id"] if len(maps) == 1 else None)
    if not mid or not any(m["id"] == mid for m in maps):
        raise ValueError("请选择 --map-id：" + ", ".join(m["id"] for m in maps))
    detail = request(base, f"/api/atlas/{mid}/places")
    selected = [t for t in detail["tasks"] if t["gold"] is not None]
    if not detail["map"] or not selected:
        raise ValueError("当前底图没有已保存人工标注的地名，请先在界面标注并保存。")
    print(f"Map: {mid} | version: {detail['map']['version']} | {len(selected)} saved places", flush=True)
    print(", ".join(t["place_name"] for t in selected), flush=True)
    if not args.execute:
        print("Preview only. Add --execute to run the entire batch.")
        return 0
    state = request(base, f"/api/atlas/{mid}/place-predict", {
        "batch": True, "map_version": detail["map"]["version"], "coordinate_mode": args.coordinate_mode}, catalog["csrf"])
    print(f"Batch: {state['job_id']} | frozen targets: {len(state['task_ids'])}", flush=True)
    previous = None
    while state["status"] == "running":
        progress = state.get("progress", {"done": 0, "total": len(state["task_ids"])})
        if progress != previous:
            print(f"Progress: {progress['done']}/{progress['total']}", flush=True)
            previous = progress
        time.sleep(2)
        state = request(base, f"/api/atlas/{mid}/place-jobs/{state['job_id']}")
    if state["status"] != "completed":
        raise ValueError(state.get("error", state["status"]))
    print(json.dumps(state["counts"], ensure_ascii=False), flush=True)
    print(f"Results: {base}/place-lab.html?map={mid}", flush=True)
    return int(state["counts"]["error"] > 0)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, URLError) as exc:
        raise SystemExit(str(exc)) from None
    except KeyboardInterrupt:
        raise SystemExit("Stopped waiting. The server continues the batch; results remain visible in the UI.") from None
