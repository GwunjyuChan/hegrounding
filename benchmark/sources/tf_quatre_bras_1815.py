"""Quatre-Bras, 16 June 1815, about 2 p.m.: text-first item from Siborne (1844), vol. I, ch. VI, on
maps/napoleon_maps/quatre_bras_east_1815.jpg. MF0064 keeps its ID and geometry; text and question replaced.
MF0061 and MF0062 are not covered: Siborne does not describe the light companies or Bijleveld's battery at the
detail this map shows (candidate source: De Bas & T'Serclaes de Wommersom, La campagne de 1815 aux Pays-Bas, 1908)."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import write, map_record, SIBORNE_V1, SIBORNE_DROP

IMAGE = "maps/napoleon_maps/quatre_bras_east_1815.jpg"
M = map_record(IMAGE)
SPEC = dict(
    battle_id="quatre_bras_east_1815", created="2026-10-21", image=IMAGE, img_w=M["img_w"], img_h=M["img_h"],
    map_url=M["map_url"], map_provenance=M["map_provenance"],
    sources=dict(siborne=dict(SIBORNE_V1, citation=SIBORNE_V1["citation"] + ", ch. VI")),
    passages=dict(gemioncourt=dict(source="siborne", pages="pp. 101-102",
        start="The Dutch-Belgian troops gradually retired as", end="advanced towards the village of Piermont.",
        drop=SIBORNE_DROP + [r"^32473$"], fixes=[("16a of which Ney", "which Ney"), ("QuatreBras", "Quatre-Bras")])),
    items=[
     dict(event_id="MF0064", replaces="MF0064", passage="gemioncourt",
          question="Towards which village did a portion of Bachelu's infantry division advance on the right? Mark the location.",
          question_zh="Bachelu 步兵师的一部分在右翼向哪个村子推进？", answer_zh="Piermont（地图拼作 Piraumont）",
          text_evidence="a portion of Bachelu’s infantry-division on the right advanced towards the village of Piermont",
          map_evidence="Piraumont village east of the Charleroi road, at the head of the Bachelu arrows.",
          geometry={"type": "polygon", "coordinates": [[230, 434], [251, 430], [276, 438], [298, 445], [305, 459],
                                                       [283, 472], [259, 464], [236, 451]]},
          geometry_source="kept_from_MF0064", tag="place_lookup", confidence_draft=4, time="1815-06-16, about 2 p.m."),
     dict(event_id="MF0120", passage="gemioncourt",
          question="Which post did the 5th battalion of Dutch militia hold against several attacks? Mark the location.",
          question_zh="荷兰民兵第 5 营守住、挡住多次进攻的是哪个据点？", answer_zh="Gemioncourt 农庄（Charleroi 大道旁）",
          text_evidence="The 5th battalion of Dutch militia which occupied this post, successfully withstood several attacks",
          map_evidence="Gemioncourt farm at the left edge beside the Charleroi road, with the B.M.5 company next to it.",
          geometry={"type": "point", "coordinates": [48, 331]}, tag="map_reasoning", confidence_draft=3,
          time="1815-06-16, about 2 p.m."),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/quatre_bras_east_1815_2026-10-21.jsonl")
