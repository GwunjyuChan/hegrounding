"""Make each recovered source passage the model input (event_text) of its map-first candidate.

English sources are used verbatim; French sources keep the original in source_text and use the
English translation as event_text. The replaced AI paraphrase is kept in event_text_ai_paraphrase.
Running it twice changes nothing.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "benchmark/map_first_candidates.jsonl"
ORIGINALS = ROOT / "benchmark/sources/original_texts_2026-10-19.json"


def apply(rows, originals):
    changed = []
    for row in rows:
        o = originals.get(row["event_id"])
        if not o or not o.get("extracted"):
            continue
        english = o["original_text"] if o["language"] == "en" else o.get("english_translation")
        if not english:
            raise ValueError(f"No English input text for {row['event_id']}")
        row.setdefault("event_text_ai_paraphrase", row["event_text"])
        row.setdefault("previous_article_url", row.get("article_url"))
        row.update(
            event_text=english, source_text=o["original_text"], input_language="en", source_language=o["language"],
            text_kind="verbatim_source_passage" if o["language"] == "en" else "assistant_translation_of_verbatim_source_paragraph",
            source_citation=", ".join(filter(None, [o.get("source"), o.get("location")])),
            article_url=o.get("url") or row.get("article_url"), source_rights=o.get("rights"),
        )
        if o["language"] != "en":
            row.update(translation_by=o.get("translation_by"), translation_review="pending")
        changed.append(row["event_id"])
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    rows = [json.loads(line) for line in CANDIDATES.read_text(encoding="utf-8").splitlines() if line.strip()]
    originals = {o["event_id"]: o for o in json.loads(ORIGINALS.read_text(encoding="utf-8"))}
    unknown = set(originals) - {r["event_id"] for r in rows}
    if unknown:
        raise ValueError(f"Original texts for unknown events: {sorted(unknown)}")
    changed = apply(rows, originals)
    if not args.dry_run:
        CANDIDATES.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps({"updated": changed, "count": len(changed), "dry_run": args.dry_run}, ensure_ascii=False))


if __name__ == "__main__":
    main()
