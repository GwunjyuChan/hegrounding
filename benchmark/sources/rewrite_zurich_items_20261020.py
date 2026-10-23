"""Rewrite Z0001-Z0010 to the question spec (Lukaka, 2026-10-20: non-compliant questions are replaced).

- event_text / source_text become the published English translation (Thiers, trans. Shoberl, Appleton 1866),
  rebuilt from OCR line ranges with make_pilot_zurich2.build_passage, so the model sees exactly what the reviewer sees.
- The French Thiers paragraph and the old assistant translation and question are kept under *_previous / *_french keys.
- target_question is rewritten without disambiguation hints, map references or geometry hints.
- Geometry lives in decisions.json and is not touched. Idempotent: re-running gives the same file.
"""
import csv, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import make_pilot_zurich2 as mp  # noqa: E402

mp.SOURCES["thiers"]["fixes"] += [
    ("(September 26^,", "(September 26),"), ("determmed", "determined"), ("Korsakof s retreat", "Korsakof's retreat"),
    ("baggage » and", "baggage, and"), ("4)bliged", "obliged"), ("J»ut hors", "put hors"), ("OSS of thirteen", "loss of thirteen"),
]
mp.PASSAGES["korsakof"] = ("thiers", [(27872, 27904)], "p. 403")

DATA = pathlib.Path("benchmark/zurich_pilot_10.jsonl")
SCREENING = pathlib.Path("benchmark/annotations/screening_110_2026-10-19.csv")
NEW = {
    "Z0001": ("cross", "Where did the six hundred men who first embarked land? Mark the location."),
    "Z0002": ("cross", "Where did the three Russian battalions that Gazan surrounded make their defence? Mark the location."),
    "Z0003": ("cross", "Where was Bontemps' brigade placed? Mark the location."),
    "Z0004": ("mortier", "Where was Klein's division when Massena despatched it? Mark the location."),
    "Z0005": ("oudinot", "After taking the little camp, what position did Oudinot take next? Mark the location."),
    "Z0006": ("cross", "Where were the troops drawn up in silence before the six hundred men embarked? Mark the location."),
    "Z0007": ("mortier", "By which place did Mortier advance upon Zurich before he was obliged to fall back? Mark the location."),
    "Z0008": ("oudinot", "Where was the little camp that Oudinot took as he ascended the Limmat? Mark the location."),
    "Z0009": ("oudinot", "What did Oudinot possess himself of that was the only way by which the Russians could retreat? Mark the location."),
    "Z0010": ("korsakof", "Into which part of Zurich did Korsakof move his troops once he had become aware of his position? Mark the location."),
}
SRC = mp.SOURCES["thiers"]

def main():
    rows = [json.loads(l) for l in DATA.read_text().splitlines() if l.strip()]
    built = {}
    for r in rows:
        key, question = NEW[r["event_id"]]
        if key not in built:
            built[key] = mp.build_passage(*mp.PASSAGES[key][:2])
        text, fixes = built[key]
        _, ranges, pages = mp.PASSAGES[key]
        if r.get("text_kind") != "verbatim_source_passage":  # first run only: keep what is being replaced
            r["event_text_previous_assistant_translation"] = r["event_text"]
            r["source_text_french"] = r["source_text"]
            r["target_question_previous"] = r["target_question"]
            r["article_url_french"] = r["article_url"]
        r.update({
            "event_text": text, "source_text": text, "target_question": question,
            "text_kind": "verbatim_source_passage", "input_language": "en", "source_language": "en",
            "translation_review": "not_applicable_published_translation",
            "source_title": "The History of the French Revolution, vol. IV (trans. Frederick Shoberl)",
            "source_author": "Adolphe Thiers; trans. Frederick Shoberl", "source_publication_year": 1866,
            "source_citation": f"{SRC['citation']}, {pages}",
            "article_url": f"https://archive.org/details/{SRC['archive_id']}", "source_archive_id": SRC["archive_id"],
            "source_local": SRC["file"], "source_raw_lines": ", ".join(f"{a}-{b}" for a, b in ranges),
            "ocr_corrections": fixes, "source_rights": "public_domain",
            "question_revision": "2026-10-20 rewritten to QUESTION_GUIDELINES v0.1 (no hints, no map reference)",
        })
    DATA.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(DATA, len(rows), "rows rewritten")

    # screening notes shown on the review page: mark the Zurich rows as rewritten
    with SCREENING.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f); fields = reader.fieldnames; srows = list(reader)
    for s in srows:
        if s["event_id"] in NEW:
            if s["建议"] != "已按规范重写":
                s["问题说明"] = f"原题：{s['原问题']}"
            s["建议"] = "已按规范重写"
            s["原问题"] = next(r["target_question"] for r in rows if r["event_id"] == s["event_id"])
            s["建议改写的问题"] = ""
            s["原文为AI改写"] = "否（Shoberl 1866 英译本原文）"
    with SCREENING.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(srows)
    print(SCREENING, "Zurich rows updated")
    for key, (t, fx) in built.items():
        print(f"\n== {key} fixes={fx}\n{t}")
    for r in rows:
        print(r["event_id"], "|", r["target_question"])

if __name__ == "__main__":
    main()
