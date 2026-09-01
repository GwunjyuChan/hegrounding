#!/usr/bin/env python3
"""
Build a coarse place-level event set for the first HE-grounding benchmark loop.

This script intentionally keeps the target place name in the event text. That
matches the first-stage task discussed in the supervisor meeting: evaluate how
well VLMs can localise named Swiss places on Siegfried map images before moving
to building-level or hidden-name variants.

Default input is the original place-level extraction backup:
  extraction/_v1_backup/events_200.jsonl

Output:
  extraction/place_events.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable


DEFAULT_INPUT = Path("extraction/_v1_backup/events_200.jsonl")
DEFAULT_OUTPUT = Path("extraction/place_events.jsonl")

DEFAULT_KEEP_TYPES = {"settlement", "hamlet_farmstead"}
YEAR_MIN = 1800
YEAR_MAX = 1926

INTEREST_KEYWORDS = {
    "war_conflict": [
        "krieg", "belager", "schlacht", "aufstand", "staatsstreich",
        "truppen", "milit", "kommandant", "besetzt", "invasion",
    ],
    "disaster": [
        "brand", "feuer", "überschwemm", "hochwasser", "lawine",
        "erdbeben", "epidemie", "cholera", "typhus",
    ],
    "infrastructure": [
        "bahn", "bahnhof", "tunnel", "brücke", "strasse", "straße",
        "kanal", "kraftwerk", "linie", "eröffnet", "gebaut",
    ],
    "institution": [
        "gründ", "eröffnet", "schule", "spital", "kloster", "kirche",
        "verein", "fabrik", "hotel", "museum",
    ],
}

LOW_INTEREST_KEYWORDS = [
    "studierte", "lehrer", "pfarrer", "professor", "wirkte", "unterrichtete",
    "mitglied", "sitz in", "wohnte", "geboren", "gestorben",
]


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def first_year(value: str) -> int | None:
    match = re.search(r"\b(1[0-9]{3})\b", value or "")
    return int(match.group(1)) if match else None


def classify_event(text: str) -> tuple[str, int]:
    lower = text.lower()
    hits: list[str] = []
    for label, keywords in INTEREST_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            hits.append(label)

    low_interest = any(keyword in lower for keyword in LOW_INTEREST_KEYWORDS)
    if hits:
        return hits[0], 2 if not low_interest else 1
    return "biographical_or_generic" if low_interest else "other", 0 if low_interest else 1


def place_is_in_text(place: str, text: str) -> bool:
    place_norm = re.sub(r"\s*\([^)]*\)", "", place).strip().lower()
    text_norm = text.lower()
    return bool(place_norm) and place_norm in text_norm


def build_events(args: argparse.Namespace) -> list[dict]:
    rows = load_jsonl(args.input)
    keep_types = {p.strip() for p in args.keep_place_types.split(",") if p.strip()}

    out: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if row.get("confidence") != "high":
            continue
        if row.get("place_type") not in keep_types:
            continue

        year = first_year(row.get("time", ""))
        if year is None or year < args.year_min or year > args.year_max:
            continue

        place = (row.get("place") or "").strip()
        event_text = (row.get("event_text") or "").strip()
        if not place or not event_text:
            continue
        if args.require_place_in_text and not place_is_in_text(place, event_text):
            continue

        key = (place.lower(), event_text.lower())
        if key in seen_keys:
            continue
        seen_keys.add(key)

        event_type, interest_score = classify_event(event_text)
        if interest_score < args.min_interest:
            continue

        rec = {
            "event_id": f"P{len(out) + 1:04d}",
            "event_text": event_text,
            "place": place,
            "place_type": row.get("place_type"),
            "time": row.get("time", ""),
            "year": year,
            "tier": 1 if row.get("place_type") == "settlement" else 2,
            "event_type": event_type,
            "interest_score": interest_score,
            "source_event_id": row.get("event_id", ""),
            "article_id": row.get("article_id", ""),
            "article_type": row.get("article_type", ""),
            "article_url": row.get("article_url", ""),
            "qa_status": "unreviewed",
        }
        out.append(rec)
        if args.target and len(out) >= args.target:
            break

    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--year-min", type=int, default=YEAR_MIN)
    parser.add_argument("--year-max", type=int, default=YEAR_MAX)
    parser.add_argument(
        "--keep-place-types",
        default=",".join(sorted(DEFAULT_KEEP_TYPES)),
        help="Comma-separated place_type values to keep.",
    )
    parser.add_argument("--min-interest", type=int, default=0)
    parser.add_argument(
        "--require-place-in-text",
        action="store_true",
        help="Keep only records where the target place name appears in event_text.",
    )
    args = parser.parse_args()

    events = build_events(args)
    write_jsonl(args.output, events)

    print(f"Wrote {len(events)} place-level events -> {args.output}")
    print("place_type:", dict(Counter(e["place_type"] for e in events)))
    print("event_type:", dict(Counter(e["event_type"] for e in events)))
    print("tier:", dict(Counter(e["tier"] for e in events)))


if __name__ == "__main__":
    main()
