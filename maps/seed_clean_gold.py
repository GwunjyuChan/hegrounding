#!/usr/bin/env python3
"""Seed a clean gold/crop directory from an existing benchmark/gold file."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--source-gold", type=Path, required=True)
    parser.add_argument("--source-crops-dir", type=Path, required=True)
    parser.add_argument("--target-gold", type=Path, required=True)
    parser.add_argument("--target-crops-dir", type=Path, required=True)
    args = parser.parse_args()

    event_ids = {row["event_id"] for row in load_jsonl(args.events)}
    source_gold = {row["event_id"]: row for row in load_jsonl(args.source_gold)}

    args.target_crops_dir.mkdir(parents=True, exist_ok=True)
    args.target_gold.parent.mkdir(parents=True, exist_ok=True)

    seeded = missing = 0
    with args.target_gold.open("w", encoding="utf-8") as out:
        for eid in sorted(event_ids):
            row = source_gold.get(eid)
            if row is None:
                missing += 1
                continue
            src_img = args.source_crops_dir / f"{eid}.jpg"
            dst_img = args.target_crops_dir / f"{eid}.jpg"
            if not src_img.exists():
                missing += 1
                continue
            shutil.copy2(src_img, dst_img)
            rec = dict(row)
            rec["image"] = str(dst_img)
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            seeded += 1

    print(f"Seeded {seeded} existing gold/crops -> {args.target_gold}")
    print(f"Missing/new event ids: {missing}")


if __name__ == "__main__":
    main()
