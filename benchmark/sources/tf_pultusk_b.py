"""Pultusk, 26 Dec 1806 (second set): text-first items from Petre (1901), pp. 90-91 and 98-99, on
maps/napoleon_maps/pultusk_1806.jpg. Replaces the map-derived paraphrases of MF0081, MF0083, MF0084 (which only named
legend letters A.A, H, P.P) with verbatim passages. All three keep their IDs; their old geometry was null, so geometry
is drawn new. MF0081 is rewritten (rule 6a): the A.A three-line position is already item MF0112 (tf_pultusk_1806.py),
so it now asks for the Polish cavalry between the wood and Mosin from the same p. 90 passage. MF0083 is rewritten: the
map's H is Bagavout's cavalry, not French artillery; it now asks for Bennigsen's powerful battery fired from the
Golymin road (map R, 'Grosse Batterie gegen die rechte Flanke der ins Gehoelz vorgedrungenen Franzosen'). MF0084 asks
for the road by which d'Aultanne's column (map P.P, 'Anmarsch der Division Gudin') approached."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import RAW, write, map_record

IMAGE = "maps/napoleon_maps/pultusk_1806.jpg"
M = map_record(IMAGE)
PETRE = RAW + "petre_campaign_in_poland_1901_napoleonscampaig00petruoft_djvu.txt"
DROP = [r"^THE BATTLES OF PULTUSK", r"^\d+ NAPOLEON'S CAMPAIGN", r"^NAPOLEON'S CAMPAIGN", r"^\* For this account of d'Aultaune"]
SPEC = dict(
    battle_id="pultusk_1806", created="2026-10-21", image=IMAGE, img_w=M["img_w"], img_h=M["img_h"],
    map_url=M["map_url"], map_provenance=M["map_provenance"],
    sources=dict(petre=dict(
        file=PETRE, archive_id="napoleonscampaig00petruoft",
        citation="F. Loraine Petre, Napoleon's Campaign in Poland, 1806-7 (London: Sampson Low, Marston & Co., 1901), "
                 "ch. V(a) 'Pultusk'",
        source_kind="secondary_history (based on Dumas, Wilson, Hoepfner, Davout and Lannes' report)",
        rights_basis="published 1901; author d. 1925; archive.org possible-copyright-status NOT_IN_COPYRIGHT")),
    passages=dict(
        position=dict(
            source="petre", start="The position chosen by Bennigsen", end="and Ostrolenka.", pages="pp. 90-91",
            drop=DROP, fixes=[("Bagavout * thus", "Bagavout thus"), ("Eussian", "Russian"), ("Eozan", "Rozan")]),
        aultanne=dict(
            source="petre", start="At this juncture, Bennigsen was warned", end="in the outer half of the wood.",
            pages="pp. 98-99", drop=DROP,
            fixes=[("Kussian", "Russian"), ("waggons.*", "waggons."), ("battalions.*", "battalions."),
                   ("cue gun", "one gun")]),
    ),
    items=[
     dict(event_id="MF0081", replaces="MF0081", passage="position",
          question="Where, on the Russian right, was the regiment of Polish cavalry posted? Mark the area.",
          question_zh="俄军右翼那个波兰骑兵团驻在哪里？", answer_zh="大树林与 Mosin 村之间的空地",
          text_evidence="In the space between the wood and Mosin was a regiment of Polish cavalry",
          map_evidence="Open ground between the north-east edge of the great wood and the village of Mosino, where the "
                       "cavalry bar B''' stands just south-west of the village.",
          geometry={"type": "polygon", "coordinates": [[2040, 770], [2120, 760], [2170, 790], [2165, 850],
                                                       [2110, 880], [2045, 865]]},
          geometry_source="assistant_redraw (old MF0081 had no geometry; asked for the A.A infantry lines, already MF0112)",
          tag="place_lookup", confidence_draft=2, time="1806-12-26, before the attack"),
     dict(event_id="MF0083", replaces="MF0083", passage="aultanne",
          question="From where did Bennigsen direct the fire of a powerful battery against the French in the outer half "
                   "of the wood? Mark the location.",
          question_zh="Bennigsen 从哪里用一个强大炮兵连轰击树林外半部的法军？", answer_zh="从 Golymin 大道上（大树林西南、主阵线一侧）",
          text_evidence="Bennigsen directed the fire of a powerful battery, from the Golymin road, against the French in the outer half of the wood",
          map_evidence="Battery R, a hatched gun line just west of the Golymin road where the road leaves the great wood "
                       "towards Pultusk.",
          geometry={"type": "polygon", "coordinates": [[1720, 1050], [1742, 1042], [1790, 1090], [1770, 1112]]},
          geometry_source="assistant_redraw (old MF0083 had no geometry; asked for 'French artillery H', which the "
                          "Renvoi gives as Bagavout's cavalry)",
          tag="place_lookup", confidence_draft=2, time="1806-12-26, about 2 p.m."),
     dict(event_id="MF0084", replaces="MF0084", passage="aultanne",
          question="By which road did the strong hostile column of which the cossacks on Bennigsen's right warned him "
                   "approach? Mark the route.",
          question_zh="Bennigsen 右翼的哥萨克报告有一支强大敌军纵队逼近，它是沿哪条路来的？",
          answer_zh="沿 Golymin 大道（从东北方向朝 Mosin 高地而来）",
          text_evidence="the approach, by the Golymin road, of a strong hostile column",
          map_evidence="Road lettered 'n. Strzegoczin u. Golymin' entering at the north-east corner and running "
                       "south-west to Mosino, with the P column marks of Gudin's division beside it.",
          geometry={"type": "line", "coordinates": [[2337, 106], [2300, 187], [2250, 262], [2200, 331], [2162, 400],
                                                    [2140, 440], [2120, 520]]},
          geometry_source="assistant_redraw (old MF0084 had no geometry; asked for the P.P sector by legend letter)",
          tag="route_or_line", confidence_draft=3, time="1806-12-26, towards 2 p.m."),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/pultusk_b_2026-10-21.jsonl")
