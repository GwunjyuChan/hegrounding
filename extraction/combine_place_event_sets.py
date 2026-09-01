#!/usr/bin/env python3
"""Combine extracted place-event JSONL files and renumber event ids."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--id-prefix", default="M")
    parser.add_argument("--target", type=int, default=0, help="Optional maximum number of combined rows.")
    args = parser.parse_args()

    combined: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    stats = Counter()

    for path in args.inputs:
        source_name = path.stem
        for row in load_jsonl(path):
            key = (
                (row.get("place") or "").strip().lower(),
                (row.get("event_text") or "").strip().lower(),
                str(row.get("year") or row.get("time") or ""),
            )
            if key in seen:
                stats["duplicates"] += 1
                continue
            seen.add(key)

            rec = dict(row)
            rec["source_event_id"] = row.get("event_id", "")
            rec["source_file"] = source_name
            rec["event_id"] = f"{args.id_prefix}{len(combined) + 1:04d}"
            combined.append(rec)
            stats[f"source_{source_name}"] += 1
            if args.target and len(combined) >= args.target:
                break
        if args.target and len(combined) >= args.target:
            break

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        for rec in combined:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(combined)} events -> {args.output}")
    print("stats:", dict(stats))
    print("event_type:", dict(Counter(row.get("event_type", "") for row in combined)))


if __name__ == "__main__":
    main()
