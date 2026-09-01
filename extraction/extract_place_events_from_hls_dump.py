#!/usr/bin/env python3
"""
Extract place-level benchmark events directly from the local HLS dump.

This replaces the slow Wayback-based exploration path when hls-data-v2.json is
available. It is designed for the first-stage benchmark agreed in the meeting:
the event text keeps the natural place name, and the target is a settlement or
named place on a Siegfried map.

For HLS geo articles, the script attaches the article's own coordinates as
`hls_lat` / `hls_lon`, allowing the downstream geocoder to avoid brittle name
searches.

Run:
  python3 extraction/extract_place_events_from_hls_dump.py --target 100

Output:
  extraction/place_events_local.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path


DEFAULT_INPUT = Path("hls-data-v2.json")
DEFAULT_OUTPUT = Path("extraction/place_events_local.jsonl")

YEAR_MIN = 1800
YEAR_MAX = 1926
TEXT_CHAR_LIMIT = 6500
EVENT_PREFILTER_KEYWORDS = [
    "brand", "feuer", "bahn", "bahnhof", "eisenbahn", "brücke", "bruecke",
    "strasse", "straße", "tunnel", "fabrik", "spinnerei", "kraftwerk",
    "schule", "spital", "kirche", "kloster", "hotel", "gegründet",
    "gegruendet", "eröffnet", "eroeffnet", "gebaut", "krieg", "aufstand",
    "belager", "schlacht", "überschwemm", "ueberschwemm", "lawine",
    "ausgrab", "fund", "inbetrieb",
    "tram", "drahtseilbahn", "zahnradbahn", "seilbahn", "schifffahrt",
    "hafen", "postauto", "verkehr", "weberei", "industrie",
    "industrialisierung", "maschinenfabrik", "uhrenindustrie",
    "textilindustrie", "mühle", "muehle", "sägerei", "saegerei",
    "elektrizitätswerk", "elektrizitaetswerk", "saline", "bergwerk",
    "steinbruch", "ziegelei", "papierfabrik",
]
WAR_KEYWORDS = [
    "krieg", "kriege", "sonderbundskrieg", "stecklikrieg", "schlacht",
    "belager", "aufstand", "truppen", "besetz", "besetzt", "gefecht",
    "armee", "heer", "invasion", "feldzug", "sonderbund", "freischar",
    "napoleon", "franzos", "französ", "österreich", "oesterreich",
    "russ", "soldat", "bourbaki",
]
TRANSPORT_KEYWORDS = [
    "bahn", "bahnhof", "eisenbahn", "bahnlinie", "linie", "strecke",
    "brücke", "bruecke", "strasse", "straße", "passstrasse", "tunnel",
    "tram", "drahtseilbahn", "zahnradbahn", "seilbahn", "schifffahrt",
    "hafen", "postauto", "verkehr",
]
INDUSTRIAL_KEYWORDS = [
    "fabrik", "spinnerei", "weberei", "industrie", "industrialisierung",
    "maschinenfabrik", "uhrenindustrie", "textilindustrie", "mühle",
    "muehle", "sägerei", "saegerei", "kraftwerk", "elektrizitätswerk",
    "elektrizitaetswerk", "saline", "bergwerk", "steinbruch", "ziegelei",
    "papierfabrik", "metall", "produktion",
]

def load_articles(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise TypeError(f"Expected list in {path}, got {type(data).__name__}")
    return [row for row in data if isinstance(row, dict)]


def clean_text(text: str) -> str:
    text = re.sub(r"Autorin/Autor:\s*\n.*?(?=\n)", "", text or "", count=1)
    text = re.sub(r"Übersetzung:\s*\n.*?(?=\n)", "", text, count=1)
    text = re.sub(r"(?<=[.!?])(?=[A-ZÄÖÜ])", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def first_year(value: str) -> int | None:
    match = re.search(r"\b(1[0-9]{3})\b", value or "")
    return int(match.group(1)) if match else None


def parse_geo(row: dict) -> tuple[float | None, float | None]:
    geo = row.get("geo") or {}
    try:
        lat = float(geo.get("lat"))
        lon = float(geo.get("lon"))
    except (TypeError, ValueError):
        return None, None
    if lat == 0.0 and lon == 0.0:
        return None, None
    return lat, lon


def in_bbox(lat: float | None, lon: float | None, args: argparse.Namespace) -> bool:
    if lat is None or lon is None:
        return False
    return args.lat_min <= lat <= args.lat_max and args.lon_min <= lon <= args.lon_max


def split_sentences(text: str) -> list[str]:
    text = clean_text(text)
    # HLS text sometimes omits spaces after punctuation; keep the splitter simple
    # and conservative so generated event_text remains readable.
    parts = re.split(r"(?<=[.!?])\s+|(?<=;)\s+", text)
    return [part.strip() for part in parts if len(part.strip()) >= 40]


def title_target(title: str) -> str:
    title = (title or "").strip()
    title = re.sub(r"\s+(Gemeinde|Amtsbezirk|Bezirk|Herrschaft|Kastlanei|Vogtei|Siedlung|Tal|Berg|Kanton)$", "", title)
    title = re.sub(r"\s+(Gemeinde|Amtsbezirk|Bezirk|Herrschaft|Kastlanei|Vogtei|Siedlung|Tal|Berg|Kanton),?\s*$", "", title)
    title = re.sub(r",\s*$", "", title)
    return title.strip()


def classify_event(sentence: str) -> tuple[str, int]:
    lower = sentence.lower()
    labels = {
        "war_conflict": WAR_KEYWORDS,
        "disaster": ["brand", "feuer", "überschwemm", "ueberschwemm", "lawine", "epidemie"],
        "transport": TRANSPORT_KEYWORDS,
        "industrial": INDUSTRIAL_KEYWORDS,
        "institution": ["schule", "spital", "kirche", "kloster", "hotel", "gegründet", "gegruendet", "eröffnet", "eroeffnet"],
        "archaeology": ["ausgrab", "fund", "nekropole", "römisch", "roemisch"],
    }
    for label, keywords in labels.items():
        if any(keyword in lower for keyword in keywords):
            return label, 2
    return "other", 1


def has_war_signal(sentence: str) -> bool:
    lower = sentence.lower()
    named_conflicts = [
        r"\bstecklikrieg(?:s|es)?\b",
        r"\bsonderbundskrieg(?:s|es)?\b",
        r"\balte[rmn]?\s+zürichkrieg\b",
        r"\bkoalitionskrieg(?:s|e|en|es)?\b",
        r"\breligionskrieg(?:s|e|en|es)?\b",
        r"\bburgunderkrieg(?:s|e|en|es)?\b",
        r"\bschwabenkrieg(?:s|e|en|es)?\b",
        r"\bvillmergerkrieg(?:s|e|en|es)?\b",
        r"\btoggenburgerkrieg(?:s|e|en|es)?\b",
        r"\bappenzellerkrieg(?:s|e|en|es)?\b",
        r"\bmailänderkrieg(?:s|e|en|es)?\b",
        r"\bmailaenderkrieg(?:s|e|en|es)?\b",
        r"\bcarrard-aufständ(?:e|en)?\b",
        r"\bcarrard-aufstand(?:s|es)?\b",
        r"\b\w+krieg(?:s|e|en|es)?\b",
    ]
    action_patterns = [
        r"\bbesetz\w*\b",
        r"\btruppen\b",
        r"\bgrenztruppen\b",
        r"\bschlacht(?:en)?\b",
        r"\bbelager\w*\b",
        r"\baufstand(?:s|es|e|es)?\b",
        r"\bgefecht(?:e|en|s)?\b",
        r"\bfeldzug(?:s|es|e|es)?\b",
        r"\binvasion(?:en)?\b",
        r"\bkapitulation(?:en)?\b",
        r"\binternierung(?:en)?\b",
        r"\bbourbaki\b",
        r"\bmarsch(?:es|e|ieren|ierte|ierten)?\b",
        r"\beinmarsch(?:es)?\b",
        r"\brückzug(?:s|es|e|es)?\b",
        r"\brueckzug(?:s|es|e|es)?\b",
        r"\bplünder\w*\b",
        r"\bpluender\w*\b",
        r"\bkriegsschauplatz\b",
    ]
    if not (
        any(re.search(pattern, lower) for pattern in named_conflicts)
        or any(re.search(pattern, lower) for pattern in action_patterns)
    ):
        return False

    false_contexts = [
        "ausbruch des ersten weltkriegs",
        "ausbruch des ersten weltkrieg",
        "nach dem ersten weltkrieg",
        "nach dem zweiten weltkrieg",
        "seit dem ersten weltkrieg",
        "seit dem zweiten weltkrieg",
        "nach dem sonderbundskrieg",
        "nach dem krieg wanderten",
        "französischsprach",
        "militärstrasse",
        "militaerstrasse",
        "morgartendenkmal",
        "schlachtdenkmal",
        "waffenplatz",
    ]
    if any(false_context in lower for false_context in false_contexts):
        return False
    return True


def has_transport_signal(sentence: str) -> bool:
    lower = sentence.lower()
    patterns = [
        r"\bbahnhof(?:s|e|es)?\b",
        r"\beisenbahn(?:en)?\b",
        r"\bbahnlinie(?:n)?\b",
        r"\bbahnstrecke(?:n)?\b",
        r"\bbahn\b",
        r"\btram(?:s)?\b",
        r"\bstrasse(?:n)?\b",
        r"\bstraße(?:n)?\b",
        r"\bpassstrasse(?:n)?\b",
        r"\bbrück(?:e|en)\b",
        r"\bbrueck(?:e|en)\b",
        r"\btunnel(?:s)?\b",
        r"\bdrahtseilbahn(?:en)?\b",
        r"\bzahnradbahn(?:en)?\b",
        r"\bseilbahn(?:en)?\b",
        r"\bschifffahrt\b",
        r"\bhafen(?:s)?\b",
        r"\bpostauto(?:s)?\b",
        r"\bverkehrs\w*\b",
    ]
    if not any(re.search(pattern, lower) for pattern in patterns):
        return False
    false_contexts = [
        "bahnhofstrasse",
        "eisenbahner",
        "bahnangestellte",
    ]
    return not any(false_context in lower for false_context in false_contexts)


def has_industrial_signal(sentence: str) -> bool:
    lower = sentence.lower()
    patterns = [
        r"\bfabrik(?:en)?\b",
        r"\b\w+fabrik(?:en)?\b",
        r"\bspinnerei(?:en)?\b",
        r"\bweberei(?:en)?\b",
        r"\bmaschinenfabrik(?:en)?\b",
        r"\bpapierfabrik(?:en)?\b",
        r"\bmühl(?:e|en)\b",
        r"\bmuehl(?:e|en)\b",
        r"\bsägerei(?:en)?\b",
        r"\bsaegerei(?:en)?\b",
        r"\bkraftwerk(?:e|en|s)?\b",
        r"\belektrizitätswerk(?:e|en|s)?\b",
        r"\belektrizitaetswerk(?:e|en|s)?\b",
        r"\bsaline(?:n)?\b",
        r"\bbergwerk(?:e|en|s)?\b",
        r"\bsteinbruch(?:s|e|es)?\b",
        r"\bziegelei(?:en)?\b",
    ]
    if not any(re.search(pattern, lower) for pattern in patterns):
        return False
    false_contexts = [
        "mithilfe der spinnerei",
        "mit hilfe der spinnerei",
        "nahe der spinnerei",
        "industriegesellschaft",
        "industriequartier",  # Useful sometimes, but usually too generic for event extraction.
    ]
    return not any(false_context in lower for false_context in false_contexts)


def profile_matches(sentence: str, profile: str) -> bool:
    if profile == "general":
        return True
    if profile == "war":
        return has_war_signal(sentence)
    if profile == "transport":
        return has_transport_signal(sentence)
    if profile == "industrial":
        return has_industrial_signal(sentence)
    return True


def profile_event_type(sentence: str, profile: str, event_type: str) -> str:
    if profile == "war":
        return "war_conflict"
    if profile == "transport":
        return "transport"
    if profile == "industrial":
        return "industrial"
    return event_type


def sentence_year(sentence: str, year_min: int, year_max: int) -> int | None:
    years = [
        int(match)
        for match in re.findall(r"\b(1[0-9]{3}|20[0-9]{2})\b", sentence)
        if year_min <= int(match) <= year_max
    ]
    return min(years) if years else None


def rule_extract(row: dict, profile: str, year_min: int, year_max: int) -> list[dict]:
    if row.get("category") != "geo":
        return []
    title = (row.get("title") or "").strip()
    if not title:
        return []

    events: list[dict] = []
    for sentence in split_sentences(row.get("content_text", "")):
        year = sentence_year(sentence, year_min, year_max)
        if year is None:
            continue
        event_type, interest = classify_event(sentence)
        if not profile_matches(sentence, profile):
            continue
        event_type = profile_event_type(sentence, profile, event_type)
        if not any(keyword in sentence.lower() for keyword in EVENT_PREFILTER_KEYWORDS):
            continue
        event_text = sentence
        # Keep the target place name in the VLM input. If the sentence uses
        # pronouns ("hier", "die Gemeinde"), prefix the title explicitly.
        title_base = title_target(title)
        if title_base and title_base.lower() not in event_text.lower():
            event_text = f"In {title_base}: {event_text}"
        events.append({
            "event_text": event_text,
            "place": title_base or title,
            "place_type": "settlement",
            "time": str(year),
            "event_type": event_type,
            "interest_score": interest,
            "confidence": "high",
        })
        if len(events) >= 3:
            break
    return events


def choose_articles(rows: list[dict], categories: set[str], seed: int, args: argparse.Namespace) -> list[dict]:
    chosen = [row for row in rows if row.get("category") in categories]
    if args.swiss_bbox_only:
        filtered = []
        for row in chosen:
            lat, lon = parse_geo(row)
            if row.get("category") == "geo" and not in_bbox(lat, lon, args):
                continue
            filtered.append(row)
        chosen = filtered
    year_re = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")

    def prefilter_score(row: dict) -> int:
        text = (row.get("content_text") or "").lower()
        score = 0
        if any(args.year_min <= int(match) <= args.year_max for match in year_re.findall(text)):
            score += 100
        general_hits = sum(1 for keyword in EVENT_PREFILTER_KEYWORDS if keyword in text)
        war_hits = sum(1 for keyword in WAR_KEYWORDS if keyword in text)
        transport_hits = sum(1 for keyword in TRANSPORT_KEYWORDS if keyword in text)
        industrial_hits = sum(1 for keyword in INDUSTRIAL_KEYWORDS if keyword in text)
        if args.profile == "war":
            if war_hits == 0:
                return 0
            score += war_hits * 10 + general_hits
        elif args.profile == "transport":
            if transport_hits == 0:
                return 0
            score += transport_hits * 10 + general_hits
        elif args.profile == "industrial":
            if industrial_hits == 0:
                return 0
            score += industrial_hits * 10 + general_hits
        else:
            score += general_hits
        lat, lon = parse_geo(row)
        if row.get("category") == "geo" and lat is not None and lon is not None:
            score += 20
        if row.get("category") == "tem":
            score += 5
        return score

    # Prefer event-dense, localisable geo articles first, then theme articles.
    def priority(row: dict) -> tuple[int, int, str]:
        lat, lon = parse_geo(row)
        has_geo = lat is not None and lon is not None
        return (0 if row.get("category") == "geo" and has_geo else 1, -prefilter_score(row), row.get("id", ""))

    chosen = [row for row in chosen if prefilter_score(row) >= 105]
    chosen.sort(key=priority)
    if args.profile in {"war", "transport", "industrial"}:
        return chosen

    geo = [row for row in chosen if row.get("category") == "geo"]
    other = [row for row in chosen if row.get("category") != "geo"]
    rng = random.Random(seed)
    rng.shuffle(geo)
    rng.shuffle(other)
    return geo + other


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--max-articles", type=int, default=500)
    parser.add_argument("--categories", default="geo,tem")
    parser.add_argument("--min-interest", type=int, default=1)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--profile", choices=["general", "war", "transport", "industrial"], default="general")
    parser.add_argument("--year-min", type=int, default=YEAR_MIN)
    parser.add_argument("--year-max", type=int, default=YEAR_MAX)
    parser.add_argument("--swiss-bbox-only", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--lat-min", type=float, default=45.75)
    parser.add_argument("--lat-max", type=float, default=47.95)
    parser.add_argument("--lon-min", type=float, default=5.70)
    parser.add_argument("--lon-max", type=float, default=10.70)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    categories = {cat.strip() for cat in args.categories.split(",") if cat.strip()}
    articles = choose_articles(load_articles(args.input), categories, args.seed, args)

    out: list[dict] = []
    stats = Counter()
    seen: set[tuple[str, str, str]] = set()

    for row in articles[: args.max_articles]:
        stats["articles_seen"] += 1
        lat, lon = parse_geo(row)
        if args.dry_run:
            print(row.get("id"), row.get("category"), row.get("title"), "geo=", (lat, lon))
            if stats["articles_seen"] >= 10:
                break
            continue

        events = rule_extract(row, args.profile, args.year_min, args.year_max)
        if events:
            stats["articles_with_events"] += 1

        for event in events:
            year = first_year(event.get("time", ""))
            if year is None or year < args.year_min or year > args.year_max:
                continue
            if event.get("confidence") != "high":
                continue
            if int(event.get("interest_score") or 0) < args.min_interest:
                continue

            place = (event.get("place") or "").strip()
            text = (event.get("event_text") or "").strip()
            if not place or not text:
                continue
            if not profile_matches(text, args.profile):
                continue

            key = (place.lower(), text.lower(), str(year))
            if key in seen:
                continue
            seen.add(key)

            rec = {
                "event_id": f"L{len(out) + 1:04d}",
                "event_text": text,
                "place": place,
                "place_type": event.get("place_type", "settlement"),
                "time": event.get("time", ""),
                "year": year,
                "tier": 1 if event.get("place_type") == "settlement" else 2,
                "event_type": event.get("event_type", "other"),
                "interest_score": int(event.get("interest_score") or 0),
                "confidence": "high",
                "article_id": row.get("id", ""),
                "article_title": row.get("title", ""),
                "article_category": row.get("category", ""),
                "article_url": f"https://hls-dhs-dss.ch/de/articles/{row.get('id', '')}/",
                "qa_status": "unreviewed",
            }
            # For geo articles, the title coordinate is a reliable settlement-level
            # target when the extracted place is the article place or a direct alias.
            if row.get("category") == "geo" and lat is not None and lon is not None:
                title_norm = re.sub(r"\s+", " ", row.get("title", "").lower()).strip()
                place_norm = re.sub(r"\s+", " ", place.lower()).strip()
                if title_norm and (title_norm in place_norm or place_norm in title_norm):
                    rec["hls_lat"] = lat
                    rec["hls_lon"] = lon
                    rec["hls_geo_source"] = "article_geo"
            out.append(rec)
            stats["events_kept"] += 1
            if len(out) >= args.target:
                break

        if not args.quiet:
            print(
                f"[{stats['articles_seen']:>4}] {row.get('id')} {row.get('category')} "
                f"{row.get('title')[:35]:35s} extracted={len(events):>2} kept={len(out)}/{args.target}"
            )
        if len(out) >= args.target:
            break

    if args.dry_run:
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        for rec in out:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(out)} events -> {args.output}")
    print("stats:", dict(stats))
    print("event_type:", dict(Counter(rec["event_type"] for rec in out)))
    print("place_type:", dict(Counter(rec["place_type"] for rec in out)))
    print("with_hls_geo:", sum(1 for rec in out if "hls_lat" in rec))


if __name__ == "__main__":
    main()
