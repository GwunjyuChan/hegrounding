#!/usr/bin/env python3
"""
Assemble the clean place-level benchmark from events, geocodes, and map crops.

By default only automatically accepted geocodes are included. If you create a
manual review file, pass it with --review-csv and include rows whose
manual_status is "accept".

Review CSV columns:
  event_id,manual_status,notes
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_review(path: Path | None) -> dict[str, dict]:
    if path is None or not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return {row["event_id"]: row for row in csv.DictReader(fh)}


def metres_per_px(bbox: list[float], img_w: int, img_h: int) -> float:
    south, west, north, east = bbox
    lat_c = (south + north) / 2
    dy_m = (north - south) * 111320
    dx_m = (east - west) * 111320 * math.cos(math.radians(lat_c))
    return (dy_m / img_h + dx_m / img_w) / 2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, default=Path("extraction/place_events.jsonl"))
    parser.add_argument("--geocodes", type=Path, default=Path("maps/place_geocodes.jsonl"))
    parser.add_argument("--gold", type=Path, default=Path("maps/place_gold_coords.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("benchmark/place_benchmark.jsonl"))
    parser.add_argument("--review-csv", type=Path, default=None)
    parser.add_argument("--include-needs-review", action="store_true")
    args = parser.parse_args()

    events = {row["event_id"]: row for row in load_jsonl(args.events)}
    geocodes = {row["place"]: row for row in load_jsonl(args.geocodes)}
    gold = {row["event_id"]: row for row in load_jsonl(args.gold)}
    review = load_review(args.review_csv)

    records: list[dict] = []
    skipped = Counter()
    for eid, event in sorted(events.items()):
        g = gold.get(eid)
        if not g or not g.get("wms_ok"):
            skipped["missing_crop"] += 1
            continue

        geo = geocodes.get(event["place"], {})
        qa_status = geo.get("qa_status")
        manual = review.get(eid, {})
        manual_status = (manual.get("manual_status") or "").strip().lower()
        accepted = qa_status == "auto_accept"
        accepted = accepted or (args.include_needs_review and qa_status == "needs_review")
        accepted = accepted or manual_status == "accept"
        if manual_status == "reject":
            accepted = False

        if not accepted:
            skipped[f"geocode_{qa_status or 'missing'}"] += 1
            continue

        m_per_px = metres_per_px(g["bbox"], g["img_w"], g["img_h"])
        records.append({
            "event_id": eid,
            "task_level": "place_name",
            "event_text": event["event_text"],
            "place": event["place"],
            "place_type": event["place_type"],
            "event_type": event.get("event_type", ""),
            "interest_score": event.get("interest_score"),
            "time": event.get("time", ""),
            "year": event.get("year"),
            "tier": event.get("tier"),
            "article_url": event.get("article_url", ""),
            "image": g.get("image", f"maps/place_crops/{eid}.jpg"),
            "bbox": g["bbox"],
            "img_w": g["img_w"],
            "img_h": g["img_h"],
            "gold_px": g["gold_px"],
            "crop_km": g["crop_km"],
            "m_per_px": round(m_per_px, 2),
            "geocode_label": geo.get("label", ""),
            "geocode_detail": geo.get("detail", ""),
            "geocode_qa_status": qa_status,
            "manual_status": manual_status or "unreviewed",
            "manual_notes": manual.get("notes", ""),
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} benchmark records -> {args.output}")
    print("skipped:", dict(skipped))
    print("tier:", dict(Counter(r["tier"] for r in records)))
    print("event_type:", dict(Counter(r["event_type"] for r in records)))


if __name__ == "__main__":
    main()
