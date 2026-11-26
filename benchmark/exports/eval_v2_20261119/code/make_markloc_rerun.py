#!/usr/bin/env python3
"""Build the 2026-11-26 re-run package for the 37 questions that ended in "Mark the area/route/line/...".

Question rule Q5 allows only the generic "Mark the location."; 37 of the 260 evaluated questions still
named the geometry type. This writes rerun_markloc_20261126/tasks.jsonl with only those items, the
question ending replaced by "Mark the location." and user_prompt re-rendered with the same template
(prompt.user_prompt_v2). Everything else (system prompt, passage, image) is unchanged.
images/ is a symlink to the package images. Run from the package folder:

    python3 code/make_markloc_rerun.py
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prompt  # noqa: E402

PAT = re.compile(r"Mark the (area|route|line|street|road|bridge)\.$")
ids = set(Path("runs/ids_260.txt").read_text().split())
out_dir = Path("rerun_markloc_20261126")
out_dir.mkdir(exist_ok=True)
if not (out_dir / "images").exists():
    os.symlink("../images", out_dir / "images")
rows = []
for line in Path("tasks.jsonl").read_text(encoding="utf-8").splitlines():
    t = json.loads(line)
    if t["event_id"] not in ids or not PAT.search(t["question"]):
        continue
    assert t["user_prompt"] == prompt.user_prompt_v2(t["model_input_text"], t["question"])
    new_q = PAT.sub("Mark the location.", t["question"])
    t2 = dict(t, question=new_q, user_prompt=prompt.user_prompt_v2(t["model_input_text"], new_q),
              question_before_20261126=t["question"])
    assert t2["user_prompt"].replace(new_q, t["question"]) == t["user_prompt"]
    rows.append(t2)
(out_dir / "tasks.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
(out_dir / "ids.txt").write_text("".join(r["event_id"] + "\n" for r in rows))
print(len(rows), "items written to", out_dir / "tasks.jsonl")
