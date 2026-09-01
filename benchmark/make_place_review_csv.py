#!/usr/bin/env python3
"""
Create a manual review CSV for place-level benchmark QA.

The CSV is intentionally simple so it can be opened in a spreadsheet:
  event_id,place,time,event_type,geocode_qa_status,geocode_label,image,manual_status,notes

Fill manual_status with:
  accept | reject
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, default=Path("extraction/place_events.jsonl"))
    parser.add_argument("--geocodes", type=Path, default=Path("maps/place_geocodes.jsonl"))
    parser.add_argument("--gold", type=Path, default=Path("maps/place_gold_coords.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("benchmark/place_review.csv"))
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="Output encoding. Default utf-8-sig opens correctly in Excel/Numbers.",
    )
    args = parser.parse_args()

    geocodes = {row["place"]: row for row in load_jsonl(args.geocodes)}
    gold = {row["event_id"]: row for row in load_jsonl(args.gold)} if args.gold.exists() else {}
    rows = []
    for event in load_jsonl(args.events):
        geo = geocodes.get(event["place"], {})
        g = gold.get(event["event_id"], {})
        rows.append({
            "event_id": event["event_id"],
            "place": event["place"],
            "time": event.get("time", ""),
            "event_type": event.get("event_type", ""),
            "geocode_qa_status": geo.get("qa_status", ""),
            "geocode_label": geo.get("label", ""),
            "geocode_detail": geo.get("detail", ""),
            "image": g.get("image", f"maps/place_crops/{event['event_id']}.jpg"),
            "event_text": event.get("event_text", ""),
            "manual_status": "",
            "notes": "",
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding=args.encoding, newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} review rows -> {args.output}")


if __name__ == "__main__":
    main()
