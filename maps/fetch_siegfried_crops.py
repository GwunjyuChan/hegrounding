#!/usr/bin/env python3
"""
Fetch Siegfried map crops for a chosen event/geocode file pair.

This is the parameterised version used by the place-level benchmark. It keeps
the older maps/fetch_siegfried.py untouched for the building-level prototype.

Outputs:
  maps/place_crops/{event_id}.jpg
  maps/place_gold_coords.jsonl
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


def km_to_deg(km: float, lat: float) -> tuple[float, float]:
    dlat = km / 111.32
    dlon = km / (111.32 * math.cos(math.radians(lat)))
    return dlat, dlon


def build_wms_url(south: float, west: float, north: float, east: float, size: int) -> str:
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": WMS_LAYER,
        "STYLES": "",
        "CRS": "EPSG:4326",
        "BBOX": f"{south},{west},{north},{east}",
        "WIDTH": str(size),
        "HEIGHT": str(size),
        "FORMAT": "image/jpeg",
    }
    return WMS_URL + "?" + urllib.parse.urlencode(params)


def fetch_image(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": "hegrounding-thesis/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        return data if data[:2] == b"\xff\xd8" else None
    except Exception as exc:
        print(f"    WMS error: {exc}")
        return None


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, default=Path("extraction/place_events.jsonl"))
    parser.add_argument("--geocodes", type=Path, default=Path("maps/place_geocodes.jsonl"))
    parser.add_argument("--crops-dir", type=Path, default=Path("maps/place_crops"))
    parser.add_argument("--gold", type=Path, default=Path("maps/place_gold_coords.jsonl"))
    parser.add_argument("--img-size", type=int, default=1024)
    parser.add_argument("--crop-km", type=float, default=6.0)
    parser.add_argument("--max-offset-frac", type=float, default=0.30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument(
        "--allow-review",
        action="store_true",
        help="Also fetch geocodes marked needs_review; otherwise auto_accept only.",
    )
    args = parser.parse_args()

    events = load_jsonl(args.events)
    geocodes = {row["place"]: row for row in load_jsonl(args.geocodes)}
    args.crops_dir.mkdir(parents=True, exist_ok=True)

    done: set[str] = set()
    if args.gold.exists():
        for row in load_jsonl(args.gold):
            done.add(row["event_id"])

    rng = random.Random(args.seed)
    args.gold.parent.mkdir(parents=True, exist_ok=True)
    fetched = skipped = failed = 0

    with args.gold.open("a", encoding="utf-8") as gold_fh:
        for event in events:
            eid = event["event_id"]
            if eid in done:
                rng.uniform(-1, 1)
                rng.uniform(-1, 1)
                continue

            geo = geocodes.get(event["place"])
            allowed = {"auto_accept"}
            if args.allow_review:
                allowed.add("needs_review")
            if not geo or geo.get("qa_status") not in allowed:
                skipped += 1
                rng.uniform(-1, 1)
                rng.uniform(-1, 1)
                print(f"SKIP {eid} {event['place']!r} geocode={geo and geo.get('qa_status')}")
                continue

            lat, lon = geo.get("lat"), geo.get("lon")
            if lat is None or lon is None:
                skipped += 1
                continue

            half_km = args.crop_km / 2
            dlat, dlon = km_to_deg(half_km, float(lat))
            shift_lat = rng.uniform(-args.max_offset_frac, args.max_offset_frac)
            shift_lon = rng.uniform(-args.max_offset_frac, args.max_offset_frac)
            center_lat = float(lat) - shift_lat * dlat * 2
            center_lon = float(lon) - shift_lon * dlon * 2

            south, north = center_lat - dlat, center_lat + dlat
            west, east = center_lon - dlon, center_lon + dlon
            frac_x = (float(lon) - west) / (east - west)
            frac_y = (north - float(lat)) / (north - south)
            gold_px = [round(frac_x * args.img_size), round(frac_y * args.img_size)]

            url = build_wms_url(south, west, north, east, args.img_size)
            data = fetch_image(url)
            crop_path = args.crops_dir / f"{eid}.jpg"
            if data:
                crop_path.write_bytes(data)
                fetched += 1
                print(f"OK   {eid} {event['place']!r:30s} gold_px={gold_px}")
            else:
                failed += 1
                print(f"FAIL {eid} {event['place']!r}")

            rec = {
                "event_id": eid,
                "place": event["place"],
                "lat": lat,
                "lon": lon,
                "bbox": [south, west, north, east],
                "img_w": args.img_size,
                "img_h": args.img_size,
                "gold_px": gold_px,
                "crop_km": args.crop_km,
                "image": str(crop_path),
                "wms_ok": data is not None,
                "geocode_qa_status": geo.get("qa_status"),
                "geocode_label": geo.get("label", ""),
                "geocode_detail": geo.get("detail", ""),
            }
            gold_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            gold_fh.flush()
            time.sleep(args.sleep)

    print(f"Done: {fetched} fetched, {failed} failed, {skipped} skipped")
    print(f"Crops: {args.crops_dir}")
    print(f"Gold:  {args.gold}")


if __name__ == "__main__":
    main()
