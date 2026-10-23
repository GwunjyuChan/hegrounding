"""Kulm, 30 Aug 1813: text-first items from Petre, Napoleon's Last Campaign in Germany (1912), p. 239, on
maps/napoleon_maps/kulm_1813.jpg (German plan, 'Situation am 30. August 1813, gegen 1 Uhr nachmittags').
Replaces the map-derived paraphrases of MF0077-0080. Petre does not place Mouton-Duvernet, Bianchi, the Prussian
brigades or the allied reserve cavalry on the 30th, so all four are rewritten (rule 6a) to places his p. 239 account of
the battle of the 30th does name and the plan shows: Priesten (allied centre), Arbesau (allied right's advance), the
Nollendorf road (Kleist's hoped-for blocking of the retreat) and Boehmisch Neudoerfel (extent of the allied right).
Old geometry was null for all four, so geometry is drawn new. Eggmuehl and the Striesowitz Berg are not lettered on
this plan and Tellnitz cannot be identified on it, so no item depends on them."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import RAW, write, map_record

IMAGE = "maps/napoleon_maps/kulm_1813.jpg"
M = map_record(IMAGE)
T = "1813-08-30, morning (the plan shows about 1 p.m.)"
SPEC = dict(
    battle_id="kulm_1813", created="2026-10-21", image=IMAGE, img_w=M["img_w"], img_h=M["img_h"],
    map_url=M["map_url"], map_provenance=M["map_provenance"],
    sources=dict(petre=dict(
        file=RAW + "petre1912_germany_napoleonslastcam00petr_djvu.txt", archive_id="napoleonslastcam00petr",
        citation="F. Loraine Petre, Napoleon's Last Campaign in Germany, 1813 (London: John Lane, 1912), "
                 "ch. 'From Dresden to Kulm'",
        source_kind="secondary_history (based on Friederich, Danilewski and the author's visit to the field)",
        rights_basis="published 1912; author d. 1925")),
    passages=dict(
        battle30=dict(source="petre", pages="p. 239",
            start="Vandamme took up a position with his right", end="Tellnitz.",
            drop=[r"^FROM DRESDEN TO KULM", r"^\d+ NAPOLEON'S LAST CAMPAIGN"],
            fixes=[("Eggmiihl", "Eggmühl"), ("1 1 A.M.", "11 A.M.")]),
    ),
    items=[
     dict(event_id="MF0077", replaces="MF0077", passage="battle30",
          question="Where was the centre of the allies who faced Vandamme across the Teplitz road? Mark the location.",
          question_zh="隔着 Teplitz 大道与 Vandamme 对峙的联军，中央在哪里？", answer_zh="Priesten 村",
          text_evidence="centre at Priesten",
          map_evidence="Village of Priesten on the Teplitz road south-west of Kulm; its name is partly overprinted by "
                       "the blocks of Div. Helffreich and the II. Korps.",
          geometry={"type": "polygon", "coordinates": [[430, 940], [545, 930], [552, 985], [500, 1012], [425, 1012]]},
          geometry_source="assistant_redraw (old MF0077 had no geometry; asked for Mouton-Duvernet west of Kulm, "
                          "whom Petre does not place on the 30th)",
          tag="place_lookup", confidence_draft=3, time=T),
     dict(event_id="MF0078", replaces="MF0078", passage="battle30",
          question="After the Striesowitz Berg was taken, towards which village did the allies begin to press forward? "
                   "Mark the location.",
          question_zh="攻下 Striesowitz 山后，联军开始向哪个村庄推进？", answer_zh="Arbesau 村",
          text_evidence="the allies began to press forward towards Arbesau",
          map_evidence="Ober-Arbesau and the Arbesau lettering east of Kulm, north-west of the allied reserve cavalry.",
          geometry={"type": "polygon", "coordinates": [[1100, 478], [1250, 468], [1258, 535], [1242, 575], [1110, 580],
                                                       [1090, 540]]},
          geometry_source="assistant_redraw (old MF0078 had no geometry; asked for Bianchi's division, which Petre "
                          "does not place on the 30th)",
          tag="place_lookup", confidence_draft=3, time=T),
     dict(event_id="MF0079", replaces="MF0079", passage="battle30",
          question="By which road was it hoped that Kleist would close Vandamme's line of retreat? Mark the route.",
          question_zh="联军希望 Kleist 切断 Vandamme 沿哪条路的退路？", answer_zh="Nollendorf 大道（从 Kulm 向东北经 Schande 上山）",
          text_evidence="It was hoped that Kleist would close his line of retreat by the Nollendorf road",
          map_evidence="Double-lined chaussee leaving Kulm to the east, bending round Schanda and climbing north-north-"
                       "east to the top edge, where the Prussian 10th-12th brigades stand on it.",
          geometry={"type": "line", "coordinates": [[760, 640], [810, 622], [855, 618], [885, 598], [905, 562],
                                                    [945, 540], [958, 500], [973, 440], [1004, 408], [1058, 377],
                                                    [1111, 338], [1150, 292], [1173, 238], [1181, 146]]},
          geometry_source="assistant_redraw (old MF0079 had no geometry; asked for the Prussian formations on the "
                          "northern road by map position)",
          tag="route_or_line", confidence_draft=3, time=T),
     dict(event_id="MF0080", replaces="MF0080", passage="battle30",
          question="As far as opposite which village did the right of the allies stretch? Mark the location.",
          question_zh="联军右翼一直延伸到哪个村庄的对面？", answer_zh="Böhmisch Neudörfel 村",
          text_evidence="right stretching as far as opposite Bohmisch Neudorfel",
          map_evidence="Village lettered 'Böhm. Neudörfel' at the foot of the wooded hills south-east of Karwitz.",
          geometry={"type": "polygon", "coordinates": [[1035, 1118], [1088, 1118], [1092, 1208], [1040, 1212]]},
          geometry_source="assistant_redraw (old MF0080 had no geometry; asked for allied cavalry north-west of "
                          "'Taurwitz', a map reading Petre does not support)",
          tag="place_lookup", confidence_draft=3, time=T),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/kulm_b_2026-10-21.jsonl")
