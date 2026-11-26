#!/usr/bin/env python3
"""Format-compliance counts for final260_20261126/runs/<model>.raw.jsonl (2026-11-26).
strict-ok: the reply is exactly one JSON object (whitespace allowed); fenced: wrapped in ```json fences only;
extra_text: other text around the JSON; unparseable: convert_predictions could not read it (scored 0)."""
import json, sys, statistics as st
from pathlib import Path
sys.path.insert(0, "code")
import convert_predictions as cp
tasks = {json.loads(l)["event_id"]: json.loads(l) for l in open("final260_20261126/tasks.jsonl")}
for m in sys.argv[1:]:
    rows = [json.loads(l) for l in open(f"final260_20261126/runs/{m}.raw.jsonl")]
    c = {"strict_ok": 0, "fenced": 0, "extra_text": 0, "unparseable": 0, "none": 0}
    for r in rows:
        raw = (r.get("raw") or "").strip()
        t = tasks[r["event_id"]]
        try:
            g = cp.to_geometry(cp.extract_json(raw), t["width"], t["height"])
            if g is None: c["none"] += 1
        except (ValueError, KeyError, TypeError):
            c["unparseable"] += 1; continue
        try:
            json.loads(raw); c["strict_ok"] += 1
        except Exception:
            body = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            try:
                json.loads(body); c["fenced"] += 1
            except Exception:
                c["extra_text"] += 1
    print(m, len(rows), c)
