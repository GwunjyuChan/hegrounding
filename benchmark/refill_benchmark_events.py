#!/usr/bin/env python3
"""Reject bad benchmark events and refill from candidate pools."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_quality_rejects(path: Path, statuses: set[str]) -> dict[str, dict]:
    rejects = {}
    if not path.exists():
        return rejects
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("crop_status") in statuses:
                rejects[row["event_id"]] = row
    return rejects


def event_key(row: dict) -> tuple[str, str, str]:
    return (
        (row.get("place") or "").strip().lower(),
        (row.get("event_text") or "").strip().lower(),
        str(row.get("year") or row.get("time") or ""),
    )


def next_id(existing: list[dict], prefix: str) -> int:
    max_seen = 0
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    for row in existing:
        match = pattern.match(row.get("event_id", ""))
        if match:
            max_seen = max(max_seen, int(match.group(1)))
    return max_seen + 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-events", type=Path, default=Path("extraction/place_events_mixed_200_local.jsonl"))
    parser.add_argument("--quality-csv", type=Path, default=Path("benchmark/crop_quality_mixed_200_local.csv"))
    parser.add_argument("--candidate-events", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reject-output", type=Path, default=Path("benchmark/rejected_events_clean_v1.csv"))
    parser.add_argument("--target-war", type=int, default=100)
    parser.add_argument("--target-transport", type=int, default=50)
    parser.add_argument("--target-industrial", type=int, default=50)
    parser.add_argument("--reject-statuses", default="blank,mostly_blank")
    parser.add_argument("--reject-ids", nargs="*", default=[])
    parser.add_argument("--reject-places", nargs="*", default=[])
    parser.add_argument(
        "--prefer-source-event-ids",
        nargs="*",
        default=[],
        help="Candidate source event ids to try first, e.g. L0110 L0116.",
    )
    parser.add_argument("--id-prefix", default="M")
    args = parser.parse_args()

    reject_statuses = {s.strip() for s in args.reject_statuses.split(",") if s.strip()}
    quality_rejects = load_quality_rejects(args.quality_csv, reject_statuses)
    for eid in args.reject_ids:
        quality_rejects.setdefault(eid, {"event_id": eid, "crop_status": "manual_reject"})
    base = load_jsonl(args.base_events)
    rejected_places = {
        row["place"]
        for row in base
        if row["event_id"] in quality_rejects
    }
    rejected_places.update(args.reject_places)

    kept = []
    rejected_rows = []
    seen = set()
    for row in base:
        if row["event_id"] in quality_rejects:
            q = quality_rejects[row["event_id"]]
            rejected_rows.append({
                "event_id": row["event_id"],
                "place": row["place"],
                "event_type": row.get("event_type", ""),
                "reason": q.get("crop_status", "quality_reject"),
                "image": q.get("image", row.get("image", "")),
                "event_text": row.get("event_text", ""),
            })
            continue
        kept.append(row)
        seen.add(event_key(row))

    targets = {
        "war_conflict": args.target_war,
        "transport": args.target_transport,
        "industrial": args.target_industrial,
    }
    counts = Counter(row.get("event_type", "") for row in kept)
    next_num = next_id(base, args.id_prefix)

    candidates = []
    for path in args.candidate_events:
        candidates.extend(load_jsonl(path))
    preferred = {eid: idx for idx, eid in enumerate(args.prefer_source_event_ids)}
    candidates.sort(key=lambda row: (preferred.get(row.get("event_id", ""), len(preferred)), row.get("event_id", "")))

    added = []
    for cand in candidates:
        event_type = cand.get("event_type", "")
        if counts[event_type] >= targets.get(event_type, 0):
            continue
        if cand.get("place") in rejected_places:
            continue
        key = event_key(cand)
        if key in seen:
            continue
        rec = dict(cand)
        rec["source_event_id"] = cand.get("event_id", "")
        rec["source_file"] = "refill_candidate"
        rec["event_id"] = f"{args.id_prefix}{next_num:04d}"
        next_num += 1
        kept.append(rec)
        added.append(rec)
        seen.add(key)
        counts[event_type] += 1

    missing = {k: targets[k] - counts.get(k, 0) for k in targets if counts.get(k, 0) < targets[k]}
    if missing:
        raise SystemExit(f"Could not refill target counts; missing {missing}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        for row in kept:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    args.reject_output.parent.mkdir(parents=True, exist_ok=True)
    with args.reject_output.open("w", encoding="utf-8-sig", newline="") as fh:
        fieldnames = ["event_id", "place", "event_type", "reason", "image", "event_text"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rejected_rows)

    print(f"Wrote {len(kept)} events -> {args.output}")
    print(f"Wrote {len(rejected_rows)} rejects -> {args.reject_output}")
    print("kept event_type:", dict(Counter(row.get("event_type", "") for row in kept)))
    print("rejected:", [(row["event_id"], row["place"], row["reason"]) for row in rejected_rows])
    print("added:", [(row["event_id"], row["place"], row.get("year"), row.get("event_text", "")[:90]) for row in added])


if __name__ == "__main__":
    main()
