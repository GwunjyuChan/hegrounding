#!/usr/bin/env python3
"""
fetch_siegfried.py — Fetch Siegfried map crops for each event via swisstopo WMS.

For each event in events_200.jsonl:
  1. Look up geocoded coordinates for event["place"].
  2. Apply a deterministic random offset (so the target is NOT always at centre).
  3. Fetch a 1024×1024 JPEG crop from the swisstopo WMS (ch.swisstopo.hiks-siegfried).
  4. Save crop to maps/crops/{event_id}.jpg.
  5. Append gold-coordinate record to maps/gold_coords.jsonl.

Gold-coordinate format (one JSON object per line):
  {
    "event_id":   "E0001",
    "place":      "Luzern",
    "lat":        47.05082,
    "lon":        8.30838,
    "bbox":       [south, west, north, east],   # WGS84 degrees
    "img_w":      1024,
    "img_h":      1024,
    "gold_px":    [x, y],   # pixel position of the place in the image
    "crop_km":    6.0
  }

Run from project root:
  python3 maps/fetch_siegfried.py

Prerequisites:
  maps/places_geocoded.jsonl   (from geocode.py)
  extraction/events_200.jsonl
"""

import json
import math
import random
import time
import urllib.request
import urllib.parse
from pathlib import Path

# ── configuration ──────────────────────────────────────────────────────────
EVENTS_PATH   = Path("extraction/events_200.jsonl")
GEOCODED_PATH = Path("maps/places_geocoded.jsonl")
CROPS_DIR     = Path("maps/crops")
GOLD_PATH     = Path("maps/gold_coords.jsonl")

IMG_SIZE   = 1024        # pixels (square image)
CROP_KM    = 6.0         # real-world side length of the crop in kilometres
RANDOM_SEED = 42         # for reproducible offsets
# Max random offset as fraction of image size (keeps target well inside the image)
MAX_OFFSET_FRAC = 0.30

WMS_URL   = "https://wms.geo.admin.ch/"
WMS_LAYER = "ch.swisstopo.hiks-siegfried"
SLEEP     = 1.0          # seconds between WMS requests

# ── helpers ────────────────────────────────────────────────────────────────

def km_to_deg(km: float, lat: float) -> tuple[float, float]:
    """Convert km to (Δlat_deg, Δlon_deg) at a given latitude."""
    dlat = km / 111.32
    dlon = km / (111.32 * math.cos(math.radians(lat)))
    return dlat, dlon


def build_wms_url(south: float, west: float, north: float, east: float,
                  width: int = IMG_SIZE, height: int = IMG_SIZE) -> str:
    params = {
        "SERVICE":     "WMS",
        "VERSION":     "1.3.0",
        "REQUEST":     "GetMap",
        "LAYERS":      WMS_LAYER,
        "STYLES":      "",
        "CRS":         "EPSG:4326",
        # WMS 1.3.0 + EPSG:4326 → axis order is lat/lon (south,west,north,east)
        "BBOX":        f"{south},{west},{north},{east}",
        "WIDTH":       str(width),
        "HEIGHT":      str(height),
        "FORMAT":      "image/jpeg",
    }
    return WMS_URL + "?" + urllib.parse.urlencode(params)


def fetch_image(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "hegrounding-thesis/1.0 (research project)"
        })
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        # Basic sanity check: JPEG starts with FF D8
        if data[:2] == b"\xff\xd8":
            return data
        return None
    except Exception as exc:
        print(f"    WMS error: {exc}")
        return None

# ── main ───────────────────────────────────────────────────────────────────

def main() -> None:
    CROPS_DIR.mkdir(parents=True, exist_ok=True)

    events   = [json.loads(l) for l in open(EVENTS_PATH, encoding="utf-8")]
    geocoded = {}
    for line in open(GEOCODED_PATH, encoding="utf-8"):
        r = json.loads(line)
        geocoded[r["place"]] = r

    # Load already-done event IDs
    done: set[str] = set()
    existing_gold: list[dict] = []
    if GOLD_PATH.exists():
        for line in open(GOLD_PATH, encoding="utf-8"):
            rec = json.loads(line)
            done.add(rec["event_id"])
            existing_gold.append(rec)

    rng = random.Random(RANDOM_SEED)

    skipped_no_geo = 0
    fetched = 0
    failed  = 0

    gold_fh = open(GOLD_PATH, "a", encoding="utf-8")

    for ev in events:
        eid   = ev["event_id"]
        place = ev["place"]

        if eid in done:
            # Consume rng draws to keep offsets deterministic for later events
            rng.uniform(-1, 1)
            rng.uniform(-1, 1)
            continue

        geo = geocoded.get(place, {})
        lat, lon = geo.get("lat"), geo.get("lon")

        if lat is None or lon is None:
            skipped_no_geo += 1
            rng.uniform(-1, 1)
            rng.uniform(-1, 1)
            print(f"  SKIP  {eid} {place!r} — no geocode")
            continue

        # Deterministic random offset: shift the crop centre so the target
        # is NOT at the image centre.
        half_km  = CROP_KM / 2
        dlat, dlon = km_to_deg(half_km, lat)

        shift_frac_lat = rng.uniform(-MAX_OFFSET_FRAC, MAX_OFFSET_FRAC)
        shift_frac_lon = rng.uniform(-MAX_OFFSET_FRAC, MAX_OFFSET_FRAC)

        # Centre of the fetched image (shifted away from the place)
        centre_lat = lat - shift_frac_lat * dlat * 2
        centre_lon = lon - shift_frac_lon * dlon * 2

        south = centre_lat - dlat
        north = centre_lat + dlat
        west  = centre_lon - dlon
        east  = centre_lon + dlon

        # Gold pixel: where the place falls within the image
        frac_x = (lon - west)  / (east - west)
        frac_y = (north - lat) / (north - south)    # y=0 at top
        gold_px = [round(frac_x * IMG_SIZE), round(frac_y * IMG_SIZE)]

        url  = build_wms_url(south, west, north, east)
        data = fetch_image(url)

        crop_path = CROPS_DIR / f"{eid}.jpg"
        if data:
            crop_path.write_bytes(data)
            fetched += 1
            print(f"  OK    {eid} {place!r:35s} gold_px={gold_px}")
        else:
            failed += 1
            print(f"  FAIL  {eid} {place!r:35s}")

        rec = {
            "event_id":  eid,
            "place":     place,
            "lat":       lat,
            "lon":       lon,
            "bbox":      [south, west, north, east],
            "img_w":     IMG_SIZE,
            "img_h":     IMG_SIZE,
            "gold_px":   gold_px,
            "crop_km":   CROP_KM,
            "wms_ok":    data is not None,
        }
        gold_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        gold_fh.flush()

        time.sleep(SLEEP)

    gold_fh.close()

    total = len(events)
    print(f"\nDone: {fetched} fetched, {failed} WMS failures, "
          f"{skipped_no_geo} skipped (no geocode), "
          f"{len(done)} already done — out of {total} events")
    print(f"Crops: {CROPS_DIR}")
    print(f"Gold:  {GOLD_PATH}")


if __name__ == "__main__":
    main()
