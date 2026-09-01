#!/usr/bin/env python3
"""
Re-fetch Siegfried map crops at 2.5 km × 2.5 km, centred on the gold label.

Reads the existing benchmark JSONL (for event metadata) and the gold-coords
JSONL (for lat/lon), then fetches new images and writes a ready-to-use
benchmark JSONL at the new scale.

Usage:
    python3 maps/refetch_crops_2_5km.py
    python3 maps/refetch_crops_2_5km.py --crop-km 2.5 --sample 20 --seed 42
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
import urllib.parse
import urllib.request
from pathlib import Path


WMS_URL = "https://wms.geo.admin.ch/"
WMS_LAYER = "ch.swisstopo.hiks-siegfried"
IMG_SIZE = 1024


def km_to_deg(km: float, lat: float) -> tuple[float, float]:
    dlat = km / 111.32
    dlon = km / (111.32 * math.cos(math.radians(lat)))
    return dlat, dlon


def metres_per_px(bbox: list[float], img_w: int, img_h: int) -> float:
    south, west, north, east = bbox
    lat_c = (south + north) / 2
    dy_m = (north - south) * 111320
    dx_m = (east - west) * 111320 * math.cos(math.radians(lat_c))
    return (dy_m / img_h + dx_m / img_w) / 2


def fetch_image(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": "hegrounding-thesis/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        return data if data[:2] == b"\xff\xd8" else None
    except Exception as exc:
        print(f"    WMS error: {exc}")
        return None


def build_wms_url(south: float, west: float, north: float, east: float) -> str:
    params = {
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap",
        "LAYERS": WMS_LAYER, "STYLES": "", "CRS": "EPSG:4326",
        "BBOX": f"{south},{west},{north},{east}",
        "WIDTH": str(IMG_SIZE), "HEIGHT": str(IMG_SIZE),
        "FORMAT": "image/jpeg",
    }
    return WMS_URL + "?" + urllib.parse.urlencode(params)


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path,
                        default=Path("benchmark/place_benchmark_mixed_200_clean_v3.jsonl"))
    parser.add_argument("--gold-coords", type=Path,
                        default=Path("maps/place_gold_coords_mixed_200_clean_v3.jsonl"))
    parser.add_argument("--crop-km", type=float, default=2.5)
    parser.add_argument("--crops-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--max-offset-frac", type=float, default=0.25,
                        help="Max random offset as fraction of crop half-extent (default 0.25 → ±312m on 2.5km crop)")
    parser.add_argument("--sample", type=int, default=None,
                        help="Randomly sample N items for a quick test")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sleep", type=float, default=0.8)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    tag = f"{args.crop_km:.1f}km".replace(".", "_")
    if args.crops_dir is None:
        args.crops_dir = Path(f"maps/place_crops_{tag}")
    if args.output is None:
        args.output = Path(f"benchmark/place_benchmark_{tag}.jsonl")

    args.crops_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    benchmark = {r["event_id"]: r for r in load_jsonl(args.benchmark)}
    gold_coords = {r["event_id"]: r for r in load_jsonl(args.gold_coords)}

    rng = random.Random(args.seed)
    items = sorted(benchmark.keys())
    if args.sample:
        items = sorted(rng.sample(items, min(args.sample, len(items))))
    print(f"Processing {len(items)} items at {args.crop_km} km crop, offset±{args.max_offset_frac} …")

    done: set[str] = set()
    existing: dict[str, dict] = {}
    if not args.no_resume and args.output.exists():
        for r in load_jsonl(args.output):
            done.add(r["event_id"])
            existing[r["event_id"]] = r
        print(f"Resuming: {len(done)} already done")

    half_km = args.crop_km / 2
    fetched = skipped = failed = 0

    with args.output.open("w", encoding="utf-8") as fh:
        for eid in items:
            if eid in done:
                fh.write(json.dumps(existing[eid], ensure_ascii=False) + "\n")
                skipped += 1
                continue

            ev = benchmark[eid]
            gc = gold_coords.get(eid)
            if gc is None:
                print(f"SKIP {eid}: no gold coords")
                skipped += 1
                continue

            lat, lon = float(gc["lat"]), float(gc["lon"])
            dlat, dlon = km_to_deg(half_km, lat)

            # Random offset: shift the crop centre away from the gold label
            shift_lat = rng.uniform(-args.max_offset_frac, args.max_offset_frac)
            shift_lon = rng.uniform(-args.max_offset_frac, args.max_offset_frac)
            center_lat = lat - shift_lat * dlat * 2
            center_lon = lon - shift_lon * dlon * 2

            south, north = center_lat - dlat, center_lat + dlat
            west, east = center_lon - dlon, center_lon + dlon

            frac_x = (lon - west) / (east - west)
            frac_y = (north - lat) / (north - south)
            gold_px = [round(frac_x * IMG_SIZE), round(frac_y * IMG_SIZE)]
            bbox = [south, west, north, east]
            m_per_px = round(metres_per_px(bbox, IMG_SIZE, IMG_SIZE), 2)

            url = build_wms_url(south, west, north, east)
            data = fetch_image(url)
            crop_path = args.crops_dir / f"{eid}.jpg"

            if data:
                crop_path.write_bytes(data)
                fetched += 1
                print(f"OK   {eid} {ev['place']!r:30s} gold_px={gold_px}  {m_per_px:.2f} m/px")
            else:
                failed += 1
                print(f"FAIL {eid} {ev['place']!r}")

            rec = {
                **{k: ev[k] for k in [
                    "event_id", "task_level", "event_text", "place", "place_type",
                    "event_type", "interest_score", "time", "year", "tier",
                    "article_url", "geocode_label", "geocode_detail",
                    "geocode_qa_status", "manual_status", "manual_notes",
                ]},
                "image": str(crop_path),
                "bbox": bbox,
                "img_w": IMG_SIZE,
                "img_h": IMG_SIZE,
                "gold_px": gold_px,
                "crop_km": args.crop_km,
                "m_per_px": m_per_px,
                "wms_ok": data is not None,
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            time.sleep(args.sleep)

    print(f"\nDone: {fetched} fetched, {skipped} skipped/resumed, {failed} failed")
    print(f"Crops:     {args.crops_dir}")
    print(f"Benchmark: {args.output}")


if __name__ == "__main__":
    main()
