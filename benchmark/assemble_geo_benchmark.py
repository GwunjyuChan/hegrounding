#!/usr/bin/env python3
"""
Assemble the geo benchmark by joining spatial candidate crops with manual annotations.

Reads:
  benchmark/napoleon_pilot_20.jsonl  — candidate events and map images
  benchmark/napoleon_annotations.jsonl — manual pixel geometries and evidence

Writes:
  benchmark/napoleon_reviewed.jsonl — latest accepted records

Geometry can be a point, line or polygon. geo_gold_px is populated for points only.
Legacy HLS candidates are supported using explicit input paths.

Usage:
    uv run python benchmark/assemble_geo_benchmark.py
    uv run python benchmark/assemble_geo_benchmark.py --output benchmark/geo_benchmark_50.jsonl
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path,
                        default=Path("benchmark/napoleon_pilot_20.jsonl"))
    parser.add_argument("--annotations", type=Path,
                        default=Path("benchmark/napoleon_annotations.jsonl"))
    parser.add_argument("--output", type=Path,
                        default=Path("benchmark/napoleon_reviewed.jsonl"))
    args = parser.parse_args()

    candidates = {r["event_id"]: r for r in load_jsonl(args.candidates)}
    # Revisions are append-only; only the latest decision for each ID applies.
    annotations = list({r['event_id']: r for r in load_jsonl(args.annotations)}.values())

    if not annotations:
        print(f"No annotations found in {args.annotations}")
        return

    print(f"Candidates: {len(candidates)}")
    print(f"Annotations: {len(annotations)}")

    records = []
    missing = []
    for ann in annotations:
        if ann.get("status", "accepted") != "accepted":
            continue
        if not ann.get("geometry") and ann.get("geo_gold_px") is None:
            raise ValueError(f"Accepted annotation lacks geometry: {ann['event_id']}")
        eid = ann["event_id"]
        cand = candidates.get(eid)
        if cand is None:
            missing.append(eid)
            continue

        rec = {
            **cand,
            "geo_gold_px": ann.get("geo_gold_px"),
            "geo_feature_type": ann.get("geo_feature_type", "other"),
            "geo_feature_vocab_version": ann.get("geo_feature_vocab_version"),
            "geometry": ann.get("geometry"),
            "tolerance_px": ann.get("tolerance_px"),
            "evidence": ann.get("evidence", ""),
            "annotator": ann.get("annotator", ""),
            "status": "accepted",
            "gold_status": ann.get("gold_status", "human_annotated"),
            "img_w": ann.get("img_w", cand.get("img_w")),
            "img_h": ann.get("img_h", cand.get("img_h")),
        }
        records.append(rec)

    if missing:
        print(f"WARNING: {len(missing)} annotations have no matching candidate: {missing}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(records)} records -> {args.output}")
    if not records:
        return

    # Summary stats
    feature_types = Counter(r["geo_feature_type"] for r in records)
    event_types = Counter(r["event_type"] for r in records)
    spatial_scores = [r.get("spatial_score", 0) for r in records]

    print(f"\nFeature types: {dict(feature_types.most_common())}")
    print(f"Event types:   {dict(event_types.most_common())}")
    print(f"Spatial score: min={min(spatial_scores)} max={max(spatial_scores)} "
          f"mean={sum(spatial_scores)/len(spatial_scores):.1f}")

    # Compute displacement between geo_gold_px and settlement gold_px
    import math
    displacements = []
    for r in records:
        if not r.get("gold_px") or not r.get("geo_gold_px") or not r.get("m_per_px"):
            continue
        gx, gy = r["gold_px"]
        px, py = r["geo_gold_px"]
        m_per_px = r.get("m_per_px", 2.44)
        dist_px = math.sqrt((px - gx) ** 2 + (py - gy) ** 2)
        displacements.append(dist_px * m_per_px)
    if displacements:
        displacements.sort()
        median = displacements[len(displacements) // 2]
        print(f"Geo↔settlement displacement: median={median:.0f} m  "
              f"max={max(displacements):.0f} m")


if __name__ == "__main__":
    main()
