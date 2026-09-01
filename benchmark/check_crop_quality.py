#!/usr/bin/env python3
"""Flag blank or low-coverage map crops in a benchmark JSONL file."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageStat


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def crop_stats(path: Path) -> dict:
    img = Image.open(path).convert("RGB")
    pixels = list(img.getdata())
    total = len(pixels)
    white = sum(1 for r, g, b in pixels if r > 245 and g > 245 and b > 245) / total
    near_white = sum(1 for r, g, b in pixels if r > 235 and g > 235 and b > 235) / total
    stdev = sum(ImageStat.Stat(img).stddev) / 3
    return {
        "white_ratio": round(white, 4),
        "near_white_ratio": round(near_white, 4),
        "stdev": round(stdev, 2),
    }


def status_for(stats: dict) -> str:
    if stats["white_ratio"] >= 0.98 or stats["stdev"] <= 1.0:
        return "blank"
    if stats["white_ratio"] >= 0.90 or stats["near_white_ratio"] >= 0.90:
        return "mostly_blank"
    if stats["white_ratio"] >= 0.60 or stats["near_white_ratio"] >= 0.70:
        return "suspicious"
    return "ok"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=Path("benchmark/place_benchmark_mixed_200_local.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("benchmark/crop_quality_mixed_200_local.csv"))
    args = parser.parse_args()

    rows = []
    for rec in load_jsonl(args.benchmark):
        image = Path(rec["image"])
        if not image.exists():
            stats = {"white_ratio": "", "near_white_ratio": "", "stdev": ""}
            status = "missing"
        else:
            stats = crop_stats(image)
            status = status_for(stats)
        rows.append({
            "event_id": rec["event_id"],
            "place": rec["place"],
            "event_type": rec.get("event_type", ""),
            "image": rec["image"],
            "crop_status": status,
            **stats,
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    counts = {}
    for row in rows:
        counts[row["crop_status"]] = counts.get(row["crop_status"], 0) + 1
    print(f"Wrote {len(rows)} rows -> {args.output}")
    print("crop_status:", counts)
    for row in rows:
        if row["crop_status"] != "ok":
            print(
                f"{row['crop_status']:13s} {row['event_id']} {row['place'][:30]:30s} "
                f"white={row['white_ratio']} near_white={row['near_white_ratio']} stdev={row['stdev']}"
            )


if __name__ == "__main__":
    main()
