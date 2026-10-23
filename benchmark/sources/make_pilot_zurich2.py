"""Second Battle of Zurich pilot (2026-10-20): text-first items on maps/zurich_pilot/zurich2.jpg.

Passages are rebuilt from fixed line ranges of the archive.org OCR files (so nothing is retyped by hand):
lines are joined, end-of-line hyphens removed, whitespace collapsed, then only the OCR fixes listed per
source are applied. Footnotes, running heads and page numbers fall outside the line ranges.
Geometry is an assistant draft for human review.
"""
import hashlib, json, pathlib, re, sys

RAW = "benchmark/sources/raw/"
IMAGE = "maps/zurich_pilot/zurich2.jpg"
SOURCES = {
    "thiers": dict(
        file=RAW + "zurich2_thiers_shoberl_historyfrenchre05shobgoog_djvu.txt",
        archive_id="historyfrenchre05shobgoog",
        citation="Adolphe Thiers, The History of the French Revolution, trans. Frederick Shoberl, vol. IV "
                 "(New York: D. Appleton & Company, 1866)",
        source_kind="secondary_history (published English translation of Thiers, Histoire de la Revolution francaise)",
        fixes=[("Mortier,* with", "Mortier, with"), ("consisting often thousand", "consisting of ten thousand"),
               ("atr tempted", "attempted"), ("demonstration 3 on", "demonstrations on"),
               ("(September 25^.", "(September 25)."), ("extrarordinary", "extraordinary"),
               ("scFeral", "several"), ("ensbarked", "embarked"), ("Lorges* division", "Lorges' division"),
               ("if be should", "if he should"), ("Oudinot,* chief", "Oudinot, chief"),
               ("part x>f the", "part of the"), ("part x&gt;f the", "part of the"),
               ("Korsakofs main", "Korsakof's main"), ("afibrds", "affords"), (" ;", ";")]),
    "alison": dict(
        file=RAW + "zurich2_alison_historyeuropefr26alisgoog_djvu.txt",
        archive_id="historyeuropefr26alisgoog",
        citation="Archibald Alison, History of Europe from the Commencement of the French Revolution, vol. IV "
                 "(Edinburgh and London: William Blackwood and Sons, 1847), ch. XXVIII, para. 43",
        source_kind="secondary_history",
        fixes=[("43. Having", "Having"), ("real',", "rear,"), ("firom", "from"), ("from hia left", "from his left"), ("dow^ to", "down to"),
               ("riyer", "river"), ("it» and", "it, and"), ("men/ in", "men, in"), ("fifbeen", "fifteen"),
               (" ;", ";")]),
}
PASSAGES = {  # source, [(first_line, last_line), ...], pages
    "plan":    ("thiers", [(27741, 27752)], "p. 401"),
    "cross":   ("thiers", [(27754, 27758), (27787, 27807)], "pp. 401-402"),
    "mortier": ("thiers", [(27809, 27820)], "p. 402"),
    "oudinot": ("thiers", [(27822, 27828)], "p. 402"),
    "alison":  ("alison", [(37712, 37732), (37748, 37780)], "pp. 277-278"),
}
ITEMS = [
 dict(event_id="Z0011", passage="plan",
      question="Where was the division of ten thousand men, which comprised four thousand grenadiers and a reserve of cavalry, to be placed? Mark the location.",
      question_zh="那个一万人、含四千掷弹兵和一支骑兵预备队的师，计划部署在哪里？", answer_zh="Altstetten（Klein 师）",
      text_evidence="Klein, with his division, consisting of ten thousand men, was to be placed at Altstetten",
      map_evidence="Altstetten village, west of Zurich between the city and Kloster Fahr.",
      geometry={"type": "point", "coordinates": [1447, 1155]}, tag="place_lookup", confidence_draft=4,
      time="1799-09-25, before the attack"),
 dict(event_id="Z0012", passage="cross",
      question="Where did the three Russian battalions that Gazan surrounded make their defence? Mark the location.",
      question_zh="被 Gazan 包围的三个俄军营在哪里防守？", answer_zh="Kloster Fahr 高地上的树林",
      text_evidence="he marched upon the three Russian battalions guarding Kloster Fahr. These had posted themselves in a wood",
      map_evidence="Russian position on the right bank at Kl. Fahr, opposite the crossing below Dietikon.",
      geometry={"type": "point", "coordinates": [1225, 1012]}, tag="map_reasoning", confidence_draft=3,
      time="1799-09-25, early morning"),
 dict(event_id="Z0013", passage="cross",
      question="Where was Bontemps' brigade placed? Mark the location.",
      question_zh="Bontemps 旅被部署在哪里？", answer_zh="Regensdorf（原文 OCR 作 Regensdof，地图作 Regenstorf）",
      text_evidence="Bontemps' brigade was placed at Regensdof, to make head against Durasof",
      map_evidence="Regenstorf village north of the crossing, at the end of a French advance arrow.",
      geometry={"type": "point", "coordinates": [1355, 877]}, tag="place_lookup", confidence_draft=4,
      time="1799-09-25, morning, after the bridge"),
 dict(event_id="Z0014", passage="mortier",
      question="By which place did Mortier advance upon Zurich before he was obliged to fall back? Mark the location.",
      question_zh="Mortier 在被迫后退之前，经由哪里向苏黎世推进？", answer_zh="Wollishofen（原文作 Wallishofen）",
      text_evidence="Mortier had advanced upon Zurich by Wallishofen",
      map_evidence="Wollishofen on the west shore of the lake, south of Zurich.",
      geometry={"type": "point", "coordinates": [1665, 1425]}, tag="place_lookup", confidence_draft=4,
      time="1799-09-25, morning"),
 dict(event_id="Z0015", passage="oudinot",
      question="Where was the little camp that Oudinot took as he ascended the Limmat? Mark the location.",
      question_zh="Oudinot 沿利马特河上行时攻占的小营地在哪里？", answer_zh="Höngg（原文作 Hong）",
      text_evidence="He had taken the little camp placed at Hong",
      map_evidence="Höngg on the right bank of the Limmat, north-west of Zurich.",
      geometry={"type": "point", "coordinates": [1500, 1058]}, tag="place_lookup", confidence_draft=4,
      time="1799-09-25, day"),
 dict(event_id="Z0016", passage="alison",
      question="Where were the twelve pontoons and thirty-seven barks collected on the evening of 24 September? Mark the location.",
      question_zh="9 月 24 日晚，十二个浮舟和三十七条船集中在哪里？", answer_zh="Dietikon",
      text_evidence="twelve pontoons and thirty-seven barks at Dietikon, on the evening of the 24th September",
      map_evidence="Dietikon village on the left bank of the Limmat, by the French crossing.",
      geometry={"type": "point", "coordinates": [1085, 1050]}, tag="place_lookup", confidence_draft=4,
      time="1799-09-24, evening"),
]

def build_passage(src, ranges):
    lines = pathlib.Path(SOURCES[src]["file"]).read_text().split("\n")
    text = "\n".join("\n".join(lines[a - 1:b]) for a, b in ranges)
    text = re.sub(r"-\s*\n\s*", "", text)        # end-of-line hyphenation
    text = re.sub(r"\s+", " ", text).strip()
    applied = []
    for a, b in SOURCES[src]["fixes"]:
        if a in text:
            text = text.replace(a, b); applied.append(f"{a.strip()} -> {b.strip()}")
    return text, applied

def main():
    img_sha = hashlib.sha256(pathlib.Path(IMAGE).read_bytes()).hexdigest()
    built = {k: build_passage(s, r) for k, (s, r, _) in PASSAGES.items()}
    out = []
    for it in ITEMS:
        src_key, ranges, pages = PASSAGES[it["passage"]]
        src = SOURCES[src_key]
        text, fixes = built[it["passage"]]
        if it["text_evidence"] not in text:
            sys.exit(f"{it['event_id']}: text_evidence not in passage")
        out.append({
            "event_id": it["event_id"], "battle_id": "zurich_second_1799", "image": IMAGE, "img_w": 2177, "img_h": 1699,
            "map_asset_sha256": img_sha,
            "map_provenance": "F. Becker (drawn and lithographed, signed 'F. Becker entw. & aut.'), 'Croquis der Schlacht bei Zurich, 25.-26. Sept. 1799'; "
                              "German-language sketch map, positions on the morning of 25 Sept. Edition and source of the scan to be verified.",
            "event_text": text, "source_text": text, "text_kind": "verbatim_source_passage",
            "input_language": "en", "source_language": "en", "source_kind": src["source_kind"],
            "source_citation": f"{src['citation']}, {pages}", "article_url": f"https://archive.org/details/{src['archive_id']}",
            "source_rights": "public_domain", "source_archive_id": src["archive_id"], "source_raw_file": src["file"],
            "source_raw_sha256": hashlib.sha256(pathlib.Path(src["file"]).read_bytes()).hexdigest(),
            "source_raw_lines": ", ".join(f"{a}-{b}" for a, b in ranges), "ocr_corrections": fixes,
            "time": it["time"], "target_question": it["question"], "question_zh": it["question_zh"], "answer_zh": it["answer_zh"],
            "text_evidence": it["text_evidence"], "map_evidence": it["map_evidence"],
            "draft_geometry": it["geometry"], "geometry_source": "assistant_draft", "confidence_draft": it["confidence_draft"],
            "spatial_tags": [it["tag"]], "status": "pending", "curation_status": "draft_needs_human_review",
            "related_existing": "Z0001-Z0010 use the assistant translation of the French Thiers text; this pilot uses Shoberl's published translation",
            "created": "2026-10-20",
        })
    path = "benchmark/sources/pilot_zurich2_2026-10-20.jsonl"
    with open(path, "w") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(path, len(out))
    for k, (t, fx) in built.items():
        print(f"\n== {k} ({len(t)} chars) fixes={fx}\n{t}")

if __name__ == "__main__":
    main()
