"""Friedland pilot (2026-10-20): text-first items from Petre 1901, drafted on maps/napoleon_maps/friedland_1807.jpg.

Passages are verbatim from the archive.org OCR (napoleonscampaig00petruoft), with only OCR errors corrected
(listed per item) and footnote markers removed. Geometry is an assistant draft for human review.
"""
import json, hashlib, pathlib

RAW = "benchmark/sources/raw/petre_campaign_in_poland_1901_napoleonscampaig00petruoft_djvu.txt"
BOOK = ("F. Loraine Petre, Napoleon's Campaign in Poland 1806-7: A Military History of Napoleon's First War "
        "with Russia (London: Sampson Low, Marston & Co., 1901)")
ARCHIVE = "https://archive.org/details/napoleonscampaig00petruoft"
IMAGE = "maps/napoleon_maps/friedland_1807.jpg"

P_GROUCHY = ("Whilst these cavalry combats were in progress, Grouchy had observed that the Russians, who were now "
  "rapidly crossing the river, were advancing in force on Heinrichsdorf by the road to Koenigsberg. From that village "
  "they would be in a position to gain the French rear through the Georgenau wood. Sending Nansouty forward from the "
  "Domnau road, Grouchy followed towards Heinrichsdorf, direct from Posthenen. Nansouty, passing through the Georgenau "
  "wood, drove out of it, through Heinrichsdorf, the advanced troops of the Russians, until he was stopped by infantry "
  "and artillery. Ordering Nansouty to form front towards the enemy at the village, Grouchy himself charged their guns "
  "as they entered it; whilst Nansouty, aided by Albert's dragoons, now sent up by Lannes, attacked in front. Disordered "
  "by a successful onslaught, the French were, in turn, charged by Russian cavalry, who, however, only succeeded in "
  "facilitating the withdrawal of most of their own guns before they were beaten off. Grouchy then drew up his men on "
  "either side of Heinrichsdorf at its eastern entrance.")
P_DEPLOY = ("As his troops arrived, the Russian commander drew them up on the plain between Sortlack and the Damerau wood. "
  "On the northern half of this space, between Damerau and the Millstream, the 8th, 7th, 6th, and 3rd divisions, under "
  "Gortchakow, stood, whilst the smaller southern portion, from the Millstream to Sortlack, was occupied by the 1st and "
  "2nd divisions, the advanced guard, and part of the cavalry under Kologribow. The greater part of the cavalry was in "
  "the northern portion, under Uwarow and Gallitzin.")
P_SORTLACK = ("The greater part of the cossacks were about the Damerau wood. In the Sortlack wood were about 3000 picked "
  "jagers, who had been driven back into it, and were fighting there. In support of them, at Sortlack, stood two "
  "battalions, five squadrons, and four guns.")
P_NAPOLEON = ("During the last four miles of the route from Domnau to Friedland, the general slope of the country is "
  "downwards towards the Alle, on the left bank of which stands the little town of Friedland. Two miles before it is "
  "reached, a slight elevation, in rear of Posthenen, affords a clear and uninterrupted view over the whole battlefield, "
  "and down to Friedland, lying directly to the spectator's front. [...] Meanwhile, officer after officer had been "
  "despatched to inform Napoleon of the position of affairs. [...] He reached the field about noon, and, from the "
  "height in rear of Posthenen, scanned the battlefield.")
P_NEY = ("At 5 o'clock, the comparative silence was broken by three salvoes of 20 guns, the signal for the advance. The "
  "echo of the last had not died away before, from the whole line of French artillery, there burst forth a furious fire. "
  "At the same moment, Ney's corps, already collected in the clearings of the nearer portion of the Sortlack wood, "
  "dashed forward with loud cheers, driving the jagers slowly back. By 6 o'clock the wood was cleared, and Ney's "
  "columns began to debouch on the farther side. The supporting Russian troops, at Sortlack, were powerless to stop "
  "their movement, but a battery on the farther bank of the Alle caused them some annoyance.")

ITEMS = [
 dict(event_id="MF0105", passage=P_GROUCHY, pages="pp. 308", raw_lines="15189-15208",
      ocr_fixes=["Eussians->Russians", "Hein-richsdorf->Heinrichsdorf", "Xansouty->Nansouty", "Kussians->Russians", "Eussian->Russian", "it ;->it;"],
      question="After the Russian cavalry had been beaten off, where did Grouchy draw up his men? Mark the location.",
      question_zh="俄军骑兵被击退后，Grouchy 把部队部署在哪里？",
      answer_zh="Heinrichsdorf 村东口两侧", text_evidence="Grouchy then drew up his men on either side of Heinrichsdorf at its eastern entrance.",
      map_evidence="East end of the Heinrichsdorf built-up area, where the road to Friedland leaves the village.",
      geometry={"type":"point","coordinates":[345,335]}, tag="map_reasoning", confidence_draft=4, time="1807-06-14, morning (before 9 a.m.)"),
 dict(event_id="MF0106", passage=P_DEPLOY, pages="p. 309", raw_lines="15247-15255", ocr_fixes=["Eussian->Russian"],
      question="Where did the Russian 8th, 7th, 6th and 3rd divisions stand? Mark the location.",
      question_zh="俄军第 8、7、6、3 师站在哪里？", answer_zh="Damerau 树林与 Millstream 之间的平原（北半部）",
      text_evidence="On the northern half of this space, between Damerau and the Millstream, the 8th, 7th, 6th, and 3rd divisions, under Gortchakow, stood",
      map_evidence="Plain bounded by the Mühlen-Fliess (Millstream) to the south and the Damerau wood to the north-east; Russian lines drawn there.",
      geometry={"type":"polygon","coordinates":[[312,592],[330,500],[385,432],[450,383],[500,333],[515,250],[535,165],[575,180],[590,280],[615,380],[625,470],[620,545],[575,565],[500,575],[420,585]]},
      tag="map_reasoning", confidence_draft=3, time="1807-06-14, about 9 a.m."),
 dict(event_id="MF0107", passage=P_DEPLOY, pages="p. 309", raw_lines="15247-15255", ocr_fixes=["Eussian->Russian"],
      question="Where were the Russian 1st and 2nd divisions and the advanced guard drawn up? Mark the location.",
      question_zh="俄军第 1、2 师和前卫部署在哪里？", answer_zh="Millstream 以南到 Sortlack 之间的较小一块（南半部）",
      text_evidence="the smaller southern portion, from the Millstream to Sortlack, was occupied by the 1st and 2nd divisions, the advanced guard, and part of the cavalry under Kologribow",
      map_evidence="Plain between the Mühlen-Fliess and Sortlack, west of Friedland and the Alle; Russian lines drawn there.",
      geometry={"type":"polygon","coordinates":[[302,600],[470,598],[470,680],[447,760],[440,850],[455,895],[400,905],[335,865],[300,800]]},
      tag="map_reasoning", confidence_draft=3, time="1807-06-14, about 9 a.m."),
 dict(event_id="MF0108", passage=P_SORTLACK, pages="pp. 309-310", raw_lines="15263, 15272-15275", ocr_fixes=[],
      question="Where did the two battalions, five squadrons and four guns supporting the jagers stand? Mark the location.",
      question_zh="支援猎兵的两个营、五个骑兵中队和四门炮在哪里？", answer_zh="Sortlack 村（不是 Sortlack 树林）",
      text_evidence="In support of them, at Sortlack, stood two battalions, five squadrons, and four guns.",
      map_evidence="Sortlack village on the Alle bend, south-east of the Sortlack wood.",
      geometry={"type":"point","coordinates":[465,915]}, tag="map_reasoning", confidence_draft=4, time="1807-06-14, morning"),
 dict(event_id="MF0109", passage=P_NAPOLEON, pages="pp. 304, 311", raw_lines="14963-14970, 15334-15340", ocr_fixes=["footnote markers removed"],
      question="From where did Napoleon scan the battlefield when he reached it about noon? Mark the location.",
      question_zh="拿破仑中午到达战场时，在哪里观察全场？", answer_zh="Posthenen 后方（西侧）的高地",
      text_evidence="He reached the field about noon, and, from the height in rear of Posthenen, scanned the battlefield.",
      map_evidence="Rising ground west of Posthenen, on the French side; the exact rise is not clearly drawn, so the boundary is uncertain.",
      geometry={"type":"point","coordinates":[85,655]}, tag="map_reasoning", confidence_draft=3, time="1807-06-14, about noon"),
 dict(event_id="MF0110", passage=P_NEY, pages="p. 315", raw_lines="15498-15509", ocr_fixes=["footnote markers removed"],
      question="Where was the French corps that dashed forward at the signal for the advance collected? Mark the location.",
      question_zh="听到进攻信号后冲出去的法军军团，此前集结在哪里？", answer_zh="Sortlack 树林靠近一侧的林间空地（Ney 军）",
      text_evidence="Ney's corps, already collected in the clearings of the nearer portion of the Sortlack wood, dashed forward",
      map_evidence="French columns drawn in the northern/eastern part of the Sortlack wood, near the Ney label.",
      geometry={"type":"polygon","coordinates":[[210,815],[310,815],[370,870],[380,950],[360,1060],[290,1060],[300,960],[240,895],[205,850]]},
      tag="map_reasoning", confidence_draft=3, time="1807-06-14, 5 p.m."),
]

def main():
    raw_sha = hashlib.sha256(pathlib.Path(RAW).read_bytes()).hexdigest()
    img_sha = hashlib.sha256(pathlib.Path(IMAGE).read_bytes()).hexdigest()
    out = []
    for it in ITEMS:
        out.append({
            "event_id": it["event_id"], "battle_id": "friedland_1807", "image": IMAGE, "img_w": 783, "img_h": 1138,
            "map_asset_sha256": img_sha,
            "map_url": "https://www.napoleon-series.org/images/military/maps/1807/Friedland1.jpg",
            "map_provenance": "Mikhailovsky-Danilevsky, plan No.21: 2 June Old Style / 14 June 1807 New Style, morning to 5 p.m. Historical Russian-language plan. Exact edition unverified.",
            "event_text": it["passage"], "source_text": it["passage"], "text_kind": "verbatim_source_passage",
            "input_language": "en", "source_language": "en", "source_kind": "secondary_history",
            "source_citation": f"{BOOK}, {it['pages']}", "article_url": ARCHIVE, "source_rights": "public_domain",
            "source_archive_id": "napoleonscampaig00petruoft", "source_raw_file": RAW, "source_raw_sha256": raw_sha,
            "source_raw_lines": it["raw_lines"], "ocr_corrections": it["ocr_fixes"],
            "time": it["time"], "target_question": it["question"], "question_zh": it["question_zh"], "answer_zh": it["answer_zh"],
            "text_evidence": it["text_evidence"], "map_evidence": it["map_evidence"],
            "draft_geometry": it["geometry"], "geometry_source": "assistant_draft", "confidence_draft": it["confidence_draft"],
            "spatial_tags": [it["tag"]], "status": "pending", "curation_status": "draft_needs_human_review",
            "supersedes_candidates": ["MF0093", "MF0094", "MF0095", "MF0096"], "created": "2026-10-20",
        })
    path = "benchmark/sources/pilot_friedland_petre_2026-10-20.jsonl"
    with open(path, "w") as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(path, len(out))
    # every quoted text_evidence must occur verbatim in its passage
    for r in out: assert r["text_evidence"] in r["event_text"], r["event_id"]

if __name__ == "__main__":
    main()
