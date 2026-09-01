#!/usr/bin/env python3
"""
Geocode place-level benchmark events with candidate retention and QA labels.

Unlike maps/geocode.py, this script records the top swisstopo candidates and
marks low-confidence matches as ambiguous instead of silently accepting the first
hit. This is meant for the clean core benchmark, where wrong gold is worse than
small sample size.

Output:
  maps/place_geocodes.jsonl
"""

from __future__ import annotations

import argparse
import html
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_EVENTS = Path("extraction/place_events.jsonl")
DEFAULT_OUTPUT = Path("maps/place_geocodes.jsonl")
API_URL = "https://api3.geo.admin.ch/rest/services/api/SearchServer"

CANTON_HINTS = {
    "ag": ["ag", "aargau", "aargauer"],
    "ar": ["ar", "appenzell ausserrhoden"],
    "ai": ["ai", "appenzell innerrhoden"],
    "be": ["be", "bern", "berner"],
    "bl": ["bl", "baselland", "basel land"],
    "bs": ["bs", "basel"],
    "fr": ["fr", "freiburg", "fribourg"],
    "ge": ["ge", "genf", "genfer", "geneve", "geneva"],
    "gl": ["gl", "glarus"],
    "gr": ["gr", "graubunden", "graubuenden", "bundner", "buendner"],
    "ju": ["ju", "jura"],
    "lu": ["lu", "luzern"],
    "ne": ["ne", "neuenburg", "neuchatel"],
    "sg": ["sg", "st gallen", "sankt gallen"],
    "so": ["so", "solothurn"],
    "sz": ["sz", "schwyz"],
    "tg": ["tg", "thurgau"],
    "ti": ["ti", "tessin", "ticino"],
    "vd": ["vd", "waadt", "vaud", "lausanne"],
    "vs": ["vs", "wallis", "valais"],
    "zh": ["zh", "zurich", "zuerich", "zürich"],
}


def norm(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokens(text: str) -> set[str]:
    return {tok for tok in norm(text).split() if len(tok) > 1}


def query_swisstopo(place: str, lang: str, limit: int) -> list[dict]:
    params = {
        "searchText": place,
        "type": "locations",
        "lang": lang,
        "limit": limit,
    }
    url = API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "hegrounding-thesis/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())
    return [item.get("attrs", {}) for item in data.get("results", [])]


def simplify_candidate(attrs: dict) -> dict:
    return {
        "label": attrs.get("label", ""),
        "detail": attrs.get("detail", ""),
        "lat": attrs.get("lat"),
        "lon": attrs.get("lon"),
        "x_lv95": attrs.get("x"),
        "y_lv95": attrs.get("y"),
        "feature_id": attrs.get("featureId"),
        "origin": attrs.get("origin"),
        "rank": attrs.get("rank"),
    }


def context_hints(place: str, context: str) -> set[str]:
    haystack = norm(f"{place} {context}")
    hints: set[str] = set()

    for match in re.findall(r"\(([A-Z]{2})\)", f"{place} {context}"):
        hints.add(match.lower())

    for canton, words in CANTON_HINTS.items():
        if any(re.search(rf"\b{re.escape(norm(word))}\b", haystack) for word in words):
            hints.add(canton)
    return hints


def candidate_has_hint(cand: dict, hints: set[str]) -> bool:
    if not hints:
        return True
    haystack = tokens(f"{cand.get('label', '')} {cand.get('detail', '')}")
    return any(hint in haystack for hint in hints)


def score_candidate(place: str, cand: dict, hints: set[str]) -> tuple[int, str]:
    place_tokens = tokens(place)
    label_tokens = tokens(cand.get("label", ""))
    detail_tokens = tokens(cand.get("detail", ""))
    haystack = label_tokens | detail_tokens

    if not place_tokens:
        return 0, "empty_place"

    overlap = len(place_tokens & haystack)
    score = overlap * 10

    place_norm = norm(place)
    label_norm = norm(cand.get("label", ""))
    detail_norm = norm(cand.get("detail", ""))
    if place_norm and (place_norm in label_norm or place_norm in detail_norm):
        score += 50
    elif place_tokens <= haystack:
        score += 30

    if hints:
        if candidate_has_hint(cand, hints):
            score += 25
        else:
            score -= 40

    if cand.get("lat") is not None and cand.get("lon") is not None:
        score += 5
    if cand.get("origin") == "gg25":
        score += 5

    reason = f"overlap={overlap}/{len(place_tokens)} hints={','.join(sorted(hints)) or '-'}"
    return score, reason


def choose_candidate(place: str, candidates: list[dict], context: str, place_types: set[str]) -> dict:
    hints = context_hints(place, context)
    if not candidates:
        return {
            "place": place,
            "status": "not_found",
            "qa_status": "reject",
            "lat": None,
            "lon": None,
            "candidates": [],
        }

    simplified = [simplify_candidate(c) for c in candidates]
    scored = []
    for cand in simplified:
        score, reason = score_candidate(place, cand, hints)
        cand["match_score"] = score
        cand["match_reason"] = reason
        scored.append(cand)
    scored.sort(key=lambda c: c["match_score"], reverse=True)
    best = scored[0]
    second = scored[1]["match_score"] if len(scored) > 1 else -1

    label_norm = norm(best.get("label", ""))
    suspicious_for_settlement = (
        "settlement" in place_types
        and any(word in label_norm for word in ["ausfahrt", "haltestelle", "strasse", "strasse"])
    )
    hint_missing = bool(hints) and not candidate_has_hint(best, hints)

    if hint_missing:
        qa_status = "ambiguous"
    elif suspicious_for_settlement:
        qa_status = "needs_review"
    elif best["match_score"] >= 55:
        qa_status = "auto_accept"
    elif best["match_score"] >= 25 and best["match_score"] - second >= 15:
        qa_status = "needs_review"
    else:
        qa_status = "ambiguous"

    return {
        "place": place,
        "status": "ok" if qa_status != "ambiguous" else "ambiguous",
        "qa_status": qa_status,
        "label": best.get("label", ""),
        "detail": best.get("detail", ""),
        "lat": best.get("lat"),
        "lon": best.get("lon"),
        "x_lv95": best.get("x_lv95"),
        "y_lv95": best.get("y_lv95"),
        "match_score": best.get("match_score"),
        "match_reason": best.get("match_reason"),
        "context_hints": sorted(hints),
        "place_types": sorted(place_types),
        "candidates": scored,
    }


def load_events(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def hls_geocode(place: str, events: list[dict]) -> dict | None:
    coords = []
    for event in events:
        if event.get("place") != place:
            continue
        lat, lon = event.get("hls_lat"), event.get("hls_lon")
        if lat is not None and lon is not None:
            coords.append((float(lat), float(lon), event.get("hls_geo_source", "hls_geo")))
    if not coords:
        return None
    lat, lon, source = coords[0]
    return {
        "place": place,
        "status": "ok",
        "qa_status": "auto_accept",
        "label": place,
        "detail": source,
        "lat": lat,
        "lon": lon,
        "x_lv95": None,
        "y_lv95": None,
        "match_score": 100,
        "match_reason": "local_hls_geo",
        "context_hints": [],
        "place_types": sorted({event.get("place_type", "") for event in events if event.get("place") == place}),
        "candidates": [],
    }


def load_existing(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    existing: dict[str, dict] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                row = json.loads(line)
                existing[row["place"]] = row
    return existing


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--lang", default="de")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--sleep", type=float, default=0.4)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    events = load_events(args.events)
    places = sorted({event["place"] for event in events})
    contexts = {
        place: " ".join(event.get("event_text", "") for event in events if event["place"] == place)
        for place in places
    }
    place_types = {
        place: {event.get("place_type", "") for event in events if event["place"] == place}
        for place in places
    }
    existing = {} if args.refresh else load_existing(args.output)
    results = dict(existing)
    print(f"{len(places)} unique places; {len(existing)} already geocoded")

    for place in places:
        if place in results:
            continue
        local = hls_geocode(place, events)
        if local:
            results[place] = local
            print(f"{local['qa_status']:>12s}  {place:35s}  -> local HLS geo")
            continue
        try:
            candidates = query_swisstopo(place, args.lang, args.limit)
            rec = choose_candidate(place, candidates, contexts.get(place, ""), place_types.get(place, set()))
        except Exception as exc:
            rec = {
                "place": place,
                "status": f"error: {exc}",
                "qa_status": "reject",
                "lat": None,
                "lon": None,
                "candidates": [],
            }
        results[place] = rec
        print(f"{rec['qa_status']:>12s}  {place:35s}  -> {rec.get('label', '')}")
        time.sleep(args.sleep)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        for place in places:
            fh.write(json.dumps(results[place], ensure_ascii=False) + "\n")

    counts: dict[str, int] = {}
    for rec in results.values():
        counts[rec["qa_status"]] = counts.get(rec["qa_status"], 0) + 1
    print(f"Wrote {args.output}")
    print("qa_status:", counts)


if __name__ == "__main__":
    main()
