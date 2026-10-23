"""Write the benchmark gold set from a review round and an exported review journal.

Gold = the latest review per event that is accepted, modified_accepted or accepted_no_location and was made
on the current candidate (see eval_geometry.load_review_gold). Each row carries the model input (question and
event text) and the map, so the file alone is enough to run and score a model.

Usage:
    python benchmark/export_review_gold.py ANNOTATIONS REVIEWS OUT.jsonl
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval_geometry as ev  # noqa: E402


def export(annotations, reviews, out):
    cands = {r["event_id"]: r for r in map(json.loads, ev._lines(annotations))}
    latest = {}
    for r in map(json.loads, ev._lines(reviews)):
        latest[r["event_id"]] = r
    gold = ev.load_review_gold(annotations, reviews)
    rows = []
    for eid in sorted(gold):
        cand, rev, src = cands[eid], latest[eid], cands[eid]["source_record"]
        rows.append({"event_id": eid, "geometry": gold[eid]["geometry"],
                     "width": gold[eid]["width"], "height": gold[eid]["height"],
                     "image": cand["annotation_image"]["path"], "image_sha256": cand["annotation_image"]["sha256"],
                     "question": src.get("target_question"), "event_text": src.get("event_text"),
                     "battle_id": src.get("battle_id"), "feature_type": cand.get("feature_type"),
                     "answerable": gold[eid]["geometry"] is not None,
                     "review_decision": rev["decision"], "reviewer": rev.get("reviewer"),
                     "reviewed_at": rev.get("reviewed_at"), "review_notes": rev.get("notes", ""),
                     "candidate_sha256": rev.get("candidate_sha256")})
    Path(out).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    current = {eid: ev.candidate_digest(c) for eid, c in cands.items()}
    state = Counter("not reviewed" if eid not in latest else
                    "stale" if latest[eid].get("candidate_sha256") not in (None, current[eid]) else
                    latest[eid]["decision"] for eid in cands)
    return {"gold": len(rows), "answerable": sum(r["answerable"] for r in rows),
            "abstention": sum(not r["answerable"] for r in rows),
            "maps": len({r["image"] for r in rows}),
            "geometry_types": dict(Counter((r["geometry"] or {}).get("type", "none") for r in rows)),
            "review_state": dict(state)}


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    print(json.dumps(export(*sys.argv[1:]), indent=2, ensure_ascii=False))
