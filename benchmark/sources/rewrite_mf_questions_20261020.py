"""Rewrite MF questions that break QUESTION_GUIDELINES v0.1 (Lukaka, 2026-10-20: non-compliant questions are replaced).

Only items whose model input is already a verbatim source passage, or the English translation of one
(MF0101-MF0104, Chambray 1823; translation still pending review), are rewritten here. Items whose text is still
map-derived or an AI paraphrase need a new source passage first and are left alone.
Only target_question changes; the old question is kept in target_question_previous. Geometry (decisions.json)
is not touched. Idempotent.
"""
import csv, json, pathlib

DATA = pathlib.Path("benchmark/map_first_candidates.jsonl")
SCREENING = pathlib.Path("benchmark/annotations/screening_110_2026-10-19.csv")
NEW = {
    "MF0009": "Where were the 43rd and 52nd lying while the French columns climbed the hillside? Mark the location.",
    "MF0010": "From where did Loison's two brigades start their advance? Mark the location.",
    "MF0011": "Where were the Portuguese skirmishers whose flanking fire made Marchand's leading brigade swerve to its left? Mark the location.",
    "MF0012": "Where did the battalion of the 19th Portuguese regiment make its charge? Mark the location.",
    "MF0025": "Which point did Reynier choose as the objective of his attack? Mark the location.",
    "MF0026": "Towards which point did Merle's three regiments direct their advance? Mark the location.",
    "MF0027": "What did Foy choose as his objective? Mark the location.",
    "MF0028": "Along what did the 5th Division make its general move to the left? Mark the location.",
    "MF0029": "Where was Stewart's division drawn up in the morning disposition? Mark the location.",
    "MF0030": "Where was Hamilton's division drawn up in the morning disposition? Mark the location.",
    "MF0031": "Where was Blake's corps drawn up in the morning disposition? Mark the location.",
    "MF0032": "Which part of the original front did Alten and the light infantry brigade of the German legion defend? Mark the location.",
    "MF0033": "What did Beresford carry with the 4th division after an obstinate resistance? Mark the location.",
    "MF0034": "Where did Hill force the passage of the Gave? Mark the location.",
    "MF0035": "Where was the enemy's left when the 6th and Light divisions crossed in the morning? Mark the location.",
    "MF0036": "Where was the Light division kept in reserve? Mark the location.",
    "MF0065": "By what route did part of Houston's and Rottenburg's brigades advance on Flushing? Mark the location.",
    "MF0067": "Where did the advanced guard drive the enemy? Mark the location.",
    "MF0068": "Where were the working parties employed on 8 August? Mark the location.",
    "MF0101": "Which point did Oudinot choose for the passage of the Berezina? Mark the location.",
    "MF0102": "Where was the first point above Borisow where the river could be crossed? Mark the location.",
    "MF0103": "Where was Napoleon in person on the evening of the 25th? Mark the location.",
    "MF0104": "Where did the artillery of the 2nd Corps deploy to blast anything that came forward? Mark the location.",
}
# The source has no location for this item (the 'north of Flushing' detail came from modern commentary).
NO_LOCATION_IN_TEXT = {"MF0066"}
TEXT_KINDS_FROM_SOURCE = {"verbatim_source_passage", "assistant_translation_of_verbatim_source_paragraph"}

def main():
    rows = [json.loads(l) for l in DATA.read_text().splitlines() if l.strip()]
    by_id = {r["event_id"]: r for r in rows}
    for eid, q in NEW.items():
        r = by_id[eid]
        if r.get("text_kind") not in TEXT_KINDS_FROM_SOURCE:
            raise SystemExit(f"{eid}: model input is not a verbatim source passage; not rewriting")
        r.setdefault("target_question_previous", r["target_question"])
        r["target_question"] = q
        r["question_revision"] = "2026-10-20 rewritten to QUESTION_GUIDELINES v0.1 (no hints, no map reference, no geometry hint)"
    DATA.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(DATA, len(NEW), "questions rewritten")

    with SCREENING.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f); fields = reader.fieldnames; srows = list(reader)
    for s in srows:
        eid = s["event_id"]
        if eid in NEW:
            if s["建议"] != "已按规范重写":
                s["问题说明"] = f"原题：{s['原问题']}"
            s["建议"] = "已按规范重写"
            s["原问题"] = NEW[eid]
            s["建议改写的问题"] = ""
        elif eid in NO_LOCATION_IN_TEXT:
            s["建议"] = "建议剔除"
            s["问题说明"] = "原文没有给出位置（“镇北”来自现代注释），按规范无法出题"
    with SCREENING.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(srows)
    print(SCREENING, "updated")
    for eid in NEW:
        print(eid, "|", by_id[eid]["target_question_previous"], "=>", NEW[eid])

if __name__ == "__main__":
    main()
