#!/usr/bin/env python3
"""
geocode.py — Geocode place names from events_200.jsonl via swisstopo API.

Output: maps/places_geocoded.jsonl
  { place, label, lat, lon, x_lv95, y_lv95, detail, status }

Run from project root:
  python3 maps/geocode.py
"""

import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

EVENTS_PATH = Path("extraction/events_200.jsonl")
OUT_PATH    = Path("maps/places_geocoded.jsonl")
SLEEP       = 0.4   # seconds between requests (be polite to swisstopo)

# swisstopo geocoding — returns WGS84 lat/lon and LV95 (x=easting, y=northing)
API_URL = "https://api3.geo.admin.ch/rest/services/api/SearchServer"


def geocode(place: str) -> dict:
    params = {
        "searchText": place,
        "type":       "locations",
        "lang":       "de",
        "limit":      5,
    }
    url = API_URL + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read())
        results = data.get("results", [])
        if not results:
            return {"place": place, "status": "not_found",
                    "lat": None, "lon": None}
        best = results[0]["attrs"]
        return {
            "place":   place,
            "label":   best.get("label", ""),
            "detail":  best.get("detail", ""),
            "lat":     best.get("lat"),
            "lon":     best.get("lon"),
            "x_lv95":  best.get("x"),      # easting  (LV95 / EPSG:2056)
            "y_lv95":  best.get("y"),      # northing (LV95 / EPSG:2056)
            "status":  "ok",
        }
    except Exception as exc:
        return {"place": place, "status": f"error: {exc}",
                "lat": None, "lon": None}


def main() -> None:
    events  = [json.loads(l) for l in open(EVENTS_PATH, encoding="utf-8")]
    places  = sorted(set(e["place"] for e in events))
    print(f"{len(places)} unique places to geocode")

    # Resume: load already-geocoded results
    existing: dict[str, dict] = {}
    if OUT_PATH.exists():
        for line in open(OUT_PATH, encoding="utf-8"):
            r = json.loads(line)
            existing[r["place"]] = r
        print(f"  Resuming — {len(existing)} already done")

    results = dict(existing)

    for place in places:
        if place in results:
            continue
        rec = geocode(place)
        results[place] = rec
        if rec["status"] == "ok":
            print(f"  OK  {place!r:40s} → {rec['lat']:.5f}, {rec['lon']:.5f}")
        else:
            print(f"  ??  {place!r:40s} → {rec['status']}")
        time.sleep(SLEEP)

    # Write sorted output
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for r in sorted(results.values(), key=lambda x: x["place"]):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    ok  = sum(1 for r in results.values() if r["status"] == "ok")
    bad = len(results) - ok
    print(f"\n{ok}/{len(places)} geocoded successfully, {bad} failed → {OUT_PATH}")
    if bad:
        print("Failed places:")
        for r in results.values():
            if r["status"] != "ok":
                print(f"  {r['place']!r} — {r['status']}")


if __name__ == "__main__":
    main()
