#!/usr/bin/env python3
"""Build the 2026-11-28 "no none option" ablation package for Qwen3.8-27B.

Items: the 75 of the final 260 where Qwen3.8-27B (final260_20261126 run) answered {"type": "none"}.
Prompt: identical to final260_20261126/tasks.jsonl (grounding-v2-20261119, incl. the 37 re-worded
questions) except that the answer line '- the place is not shown on this map: {"type": "none"}' is
removed (prompt.USER_TEMPLATE_V2_NONONE). System prompt, passage, question and image are unchanged.
Writes rerun_nonone_20261128/tasks.jsonl and ids.txt; images/ is a symlink. Run from the package folder:

    python3 code/make_nonone_rerun.py
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import convert_predictions as cp  # noqa: E402
import prompt  # noqa: E402

FINAL = Path("final260_20261126")
out_dir = Path("rerun_nonone_20261128")
out_dir.mkdir(exist_ok=True)
if not (out_dir / "images").exists():
    os.symlink("../images", out_dir / "images")

none_ids = set()
for line in (FINAL / "runs/qwen3.8-27b-4bit.raw.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(line)
    try:
        if str(cp.extract_json(r["raw"]).get("type", "")).lower() == "none":
            none_ids.add(r["event_id"])
    except ValueError:
        pass
assert len(none_ids) == 75, len(none_ids)

rows = []
for line in (FINAL / "tasks.jsonl").read_text(encoding="utf-8").splitlines():
    t = json.loads(line)
    if t["event_id"] not in none_ids:
        continue
    assert t["prompt_version"] == prompt.PROMPT_VERSION_V2
    assert t["user_prompt"] == prompt.user_prompt_v2(t["model_input_text"], t["question"])
    new = prompt.user_prompt_v2_nonone(t["model_input_text"], t["question"])
    assert t["user_prompt"].count(prompt.NONE_LINE_V2) == 1
    assert t["user_prompt"].replace(prompt.NONE_LINE_V2, "") == new
    rows.append(dict(t, user_prompt=new, prompt_version=prompt.PROMPT_VERSION_V2_NONONE))
assert len(rows) == 75
(out_dir / "tasks.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
(out_dir / "ids.txt").write_text("".join(r["event_id"] + "\n" for r in rows))
print(len(rows), "items written to", out_dir / "tasks.jsonl")
