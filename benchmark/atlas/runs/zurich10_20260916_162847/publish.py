"""Append this run's validated predictions to the active local atlas via its API."""
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
BASE = "http://127.0.0.1:8767"
MID = "074f543caf035b8f"
assert not (HERE / "published.json").exists(), "Already published; avoid duplicate imports"
published = {}
for key in ("gpt5", "qwen3vl8b"):
    payload = json.loads((HERE / key / "predictions.json").read_text())
    if not payload["predictions"]:
        continue
    with urlopen(BASE + "/api/atlas") as response:
        catalog = json.load(response)
    request = Request(BASE + f"/api/atlas/{MID}/predictions", data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json", "X-CSRF-Token": catalog["csrf"],
                               "Origin": BASE}, method="POST")
    with urlopen(request) as response:
        result = json.load(response)
    published[key] = {"model": payload["model"], "map_version": payload["map_version"],
                      "events": [p["event_id"] for p in payload["predictions"]]}
    print(key, published[key])
(HERE / "published.json").write_text(json.dumps(published, indent=2) + "\n")
