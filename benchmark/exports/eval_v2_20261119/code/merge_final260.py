#!/usr/bin/env python3
"""Assemble final260_20261126/runs/<model>.raw.jsonl, convert and score (2026-11-26).

Final question set = the 260 items, with the 37 "Mark the area/route/..." questions changed to
"Mark the location." (rerun_markloc_20261126). Per model:
  gpt-6.2-sol, claude-opus-5-5, gemini-4-neon-low, gemma-4-26b-q4:
      223 unchanged items from runs/<model>.raw.jsonl + 37 from rerun_markloc_20261126/runs/
  qwen3.8-27b-4bit: all 260 re-run on the MacBook (final260_20261126/runs + rerun_markloc 37);
      the 2026-11-19 Mac mini run stays in runs/ for the reproducibility comparison.
  gemma-4-26b-q4-lenient: the merged Gemma rows with the same lenient fix as gemma_probe_20261125
      (missing "type": {"box": ...} -> box, {"line": ...} -> line; nothing else).
Each output row gets "source": which file it came from. Then convert_predictions.py and
eval_geometry.py (same gold, same line rules) write <model>.pred.json / .score_polygon.json.

Run from the package folder:  python3 code/merge_final260.py [models...]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

FINAL = Path("final260_20261126")
RERUN = Path("rerun_markloc_20261126")
ids = Path("runs/ids_260.txt").read_text().split()
rerun_ids = set(Path(RERUN / "ids.txt").read_text().split())
assert len(ids) == 260 and len(rerun_ids) == 37 and rerun_ids <= set(ids)


def latest_ok(path):
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("error") is None:
                out[r["event_id"]] = r
    return out


def write(model, rows):
    (FINAL / "runs").mkdir(parents=True, exist_ok=True)
    p = FINAL / "runs" / f"{model}.raw.jsonl"
    p.write_text("".join(json.dumps(rows[e], ensure_ascii=False) + "\n" for e in ids), encoding="utf-8")
    subprocess.run([sys.executable, "code/convert_predictions.py", "--raw", str(p), "--tasks", str(FINAL / "tasks.jsonl"),
                    "--out", str(FINAL / "runs" / f"{model}.pred.json")], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, "code/eval_geometry.py", "--gold", "gold/gold_polygon.jsonl",
                    "--pred", str(FINAL / "runs" / f"{model}.pred.json"), "--line-rules", "line_rules.csv",
                    "--out", str(FINAL / "runs" / f"{model}.score_polygon.json")], check=True, stdout=subprocess.DEVNULL)
    print(model, "written")


def merged(model, base, rerun):
    a, b = latest_ok(base), latest_ok(rerun)
    rows = {}
    for e in ids:
        src, r = (rerun, b.get(e)) if e in rerun_ids else (base, a.get(e))
        assert r is not None, (model, e, "missing")
        rows[e] = dict(r, source=str(src))
    return rows


def lenient(rows):
    out = {}
    for e, r in rows.items():
        r = dict(r)
        m = re.search(r"\{.*\}", r.get("raw") or "", re.S)
        try:
            o = json.loads(m.group(0)) if m else None
        except Exception:
            o = None
        if isinstance(o, dict) and "type" not in o and "box" in o:
            r["raw"], r["lenient_fix"] = json.dumps({"type": "box", "bbox": o["box"]}), "box key"
        elif isinstance(o, dict) and "type" not in o and "line" in o:
            r["raw"], r["lenient_fix"] = json.dumps({"type": "line", "points": o["line"]}), "line key"
        out[e] = r
    return out


SPEC = {
    "gpt-6.2-sol": ("runs/gpt-6.2-sol.raw.jsonl", RERUN / "runs/gpt-6.2-sol.raw.jsonl"),
    "claude-opus-5-5": ("runs/claude-opus-5-5.raw.jsonl", RERUN / "runs/claude-opus-5-5.raw.jsonl"),
    "gemini-4-neon-low": ("runs/gemini-4-neon-low.raw.jsonl", RERUN / "runs/gemini-4-neon-low.raw.jsonl"),
    "gemma-4-26b-q4": ("runs/gemma-4-26b-q4.raw.jsonl", RERUN / "runs/gemma-4-26b-q4.raw.jsonl"),
    "qwen3.8-27b-4bit": (FINAL / "runs/qwen3.8-27b-4bit.part223.raw.jsonl", RERUN / "runs/qwen3.8-27b-4bit.raw.jsonl"),
}
todo = sys.argv[1:] or list(SPEC) + ["gemma-4-26b-q4-lenient"]
for model in todo:
    if model == "gemma-4-26b-q4-lenient":
        write(model, lenient(merged("gemma-4-26b-q4", *SPEC["gemma-4-26b-q4"])))
    else:
        write(model, merged(model, *SPEC[model]))
