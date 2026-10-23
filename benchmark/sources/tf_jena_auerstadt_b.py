"""Jena and Auerstadt, 14 Oct 1806: text-first items from Petre (1907), on maps/napoleon_maps/jena_1806.jpg
(MF0041, MF0042, MF0044) and maps/napoleon_maps/auerstadt_1806.jpg (MF0045-MF0048). Replaces the AI paraphrases.
The old questions asked for legend-keyed deployments (a.a, b.b, k.k, m.m ...) that the reviewers found unreadable,
ambiguous or in conflict with the map legend; each item keeps its ID and is rewritten to a place Petre names
explicitly. MF0042 keeps its geometry (Vierzehnheiligen); the others are redrawn. Petre's OCR spells Isserstedt
"Isserstadt"."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import RAW, write, map_record

PETRE = dict(
    file=RAW + "petre1907_prussia_india.history.resource.91968_djvu.txt", archive_id="india.history.resource.91968",
    citation="F. Loraine Petre, Napoleon's Conquest of Prussia, 1806 (London: John Lane, The Bodley Head, 1907)",
    source_kind="secondary_history", rights_basis="published 1907; author d. 1925")
PETRE_DROP = [r"^\d{1,3}\.? Napoleon’s Conquest of Prussia$", r"^The Battle of Jena \d+$",
              r"^The Battle of Auerst.dt \d+$", r"^\d{1,3}$", r"^I$", r"^L$"]

# ---------------------------------------------------------------- Jena
IMAGE_J = "maps/napoleon_maps/jena_1806.jpg"
MJ = map_record(IMAGE_J)
SPEC_J = dict(
    battle_id="jena_1806", created="2026-10-21", image=IMAGE_J, img_w=MJ["img_w"], img_h=MJ["img_h"],
    map_url=MJ["map_url"], map_provenance=MJ["map_provenance"],
    sources=dict(petre=PETRE),
    passages=dict(
        camps=dict(source="petre", pages="p. 124", drop=PETRE_DROP,
            start="Hohenlohe’s main body was encamped facing", end="over the wood of Isserstadt.", fixes=[]),
        tauenzien=dict(source="petre", pages="pp. 129-130", drop=PETRE_DROP,
            start="Napoleon, riding amongst Lannes’ troops,", end="behind Lutzeroda.",
            fixes=[("Tauen‘zien", "Tauenzien"), ("the .wood", "the wood")]),
        centre=dict(source="petre", pages="p. 136", drop=PETRE_DROP,
            start="Once more, soon after eleven, the advance of", end="with them was Napoleon himself.",
            fixes=[("by the goth of", "by the 40th of"), ("the rest ‘of", "the rest of"),
                   ("d’Hautpoult’s cuirassiers'", "d’Hautpoult’s cuirassiers")]),
    ),
    items=[
     dict(event_id="MF0041", replaces="MF0041", passage="camps",
          question="In what space were the Prussians of Hohenlohe's main body encamped? Mark the area.",
          question_zh="Hohenlohe 主力中的普鲁士部队在哪一片地方宿营？",
          answer_zh="Kotschau、Klein Romstadt 和 Capellendorf 三村之间（地图作 Kötschau、Kl. Romstädt、Capellendorf）",
          text_evidence="The Prussians were in the space between Kotschau, Klein Romstadt, and Capellendorf",
          map_evidence="Triangle of open ground between Capellendorf (west), Kl. Romstädt (north-east) and Kötschau (south), "
                       "north-west of Isserstädt.",
          geometry={"type": "polygon", "coordinates": [[252, 468], [270, 462], [482, 486], [492, 502], [350, 612],
                                                        [333, 608], [250, 500]]},
          geometry_source="assistant_redraw (old MF0041 had no geometry: Grawert's night position, legend a.a, "
                          "judged ambiguous)",
          tag="place_lookup", confidence_draft=3, time="1806-10-13, night before the battle"),
     dict(event_id="MF0042", replaces="MF0042", passage="centre",
          question="Which village was again captured by the 40th of Suchet's division with the aid of Ney's voltigeurs? "
                   "Mark the location.",
          question_zh="Suchet 师的第 40 团在 Ney 的轻步兵协助下再次攻占了哪个村子？",
          answer_zh="Vierzehnheiligen（地图作 14 Heiligen）",
          text_evidence="Vierzehnheiligen was again captured by the 40th of Suchet’s division with the aid of Ney’s voltigeurs",
          map_evidence="Village labelled 14 Heiligen between Kl. Romstädt and Krippendorf, east of Isserstädt.",
          geometry={"type": "polygon", "coordinates": [[537, 541], [552, 541], [564, 554], [560, 570], [545, 577],
                                                        [534, 566]]},
          geometry_source="kept_from_MF0042", tag="place_lookup", confidence_draft=4,
          time="1806-10-14, soon after 11 a.m."),
     dict(event_id="MF0044", replaces="MF0044", passage="tauenzien",
          question="During the night, which villages and which line did Tauenzien's light troops occupy? Mark the line.",
          question_zh="夜间 Tauenzien 的轻装部队占据了哪两个村子以及它们之间的哪条线？",
          answer_zh="Closewitz 和 Lutzeroda 两村及其间的连线（地图作 Closwitz、Lützeroda）",
          text_evidence="During the night his light troops had occupied Closewitz, Lutzeroda, and the line between them",
          map_evidence="Line from Lützeroda village to Closwitz village on the plateau north-west of Jena, north of Cospeda.",
          geometry={"type": "line", "coordinates": [[622, 700], [655, 703], [690, 708]]},
          geometry_source="assistant_redraw (old MF0044 had no geometry: Tauenzien's later line k.k, judged unreadable)",
          tag="route_or_line", confidence_draft=3, time="1806-10-13/14, night, to 6 a.m."),
    ])

# ---------------------------------------------------------------- Auerstadt
IMAGE_A = "maps/napoleon_maps/auerstadt_1806.jpg"
MA = map_record(IMAGE_A)
POPPEL = {"type": "polygon", "coordinates": [[756, 402], [776, 395], [794, 405], [793, 424], [774, 431], [757, 421]]}
SPEC_A = dict(
    battle_id="auerstadt_1806", created="2026-10-21", image=IMAGE_A, img_w=MA["img_w"], img_h=MA["img_h"],
    map_url=MA["map_url"], map_provenance=MA["map_provenance"],
    sources=dict(petre=PETRE),
    passages=dict(
        night=dict(source="petre", pages="pp. 149-150", drop=PETRE_DROP,
            start="The main Prussian army had started from", end="up before 2 A.M.",
            fixes=[("Wiirtemberg", "Würtemberg"), ("resulted in,so many", "resulted in so many"),
                   ("French, ‘who", "French, who"), ("lave occupied", "have occupied"), ("the Iim", "the Ilm")]),
        morning=dict(source="petre", pages="pp. 153-154", drop=PETRE_DROP,
            start="Before daybreak on the 14th both forces were", end="the 12th.",
            fixes=[("Blucher.. The", "Blucher. The")]),
        morand=dict(source="petre", pages="p. 161", drop=PETRE_DROP,
            start="The 51st reached the top of the slope leading", end="the Prussians fighting in front of Hassenhausen.",
            fixes=[("above the .Ilm", "above the Ilm")]),
        kalkreuth=dict(source="petre", pages="p. 162", drop=PETRE_DROP,
            start="Gudin now pressed on against the", end="(Puck Holz) between Eckardsberga and Lisdorf.",
            fixes=[(".on their right", "on their right"), ("suffciently", "sufficiently")]),
    ),
    items=[
     dict(event_id="MF0045", replaces="MF0045", passage="morning",
          question="Near which village did Burke stumble in the mist on the whole of the Prussian advance guard of 600 "
                   "cavalry led by Blucher? Mark the location.",
          question_zh="Burke 在雾中于哪个村子附近撞上了 Blucher 率领的普军 600 骑兵前卫？",
          answer_zh="Poppel 附近",
          text_evidence="he suddenly stumbled in the mist, near Poppel, on the whole of the Prussian advance guard of 600 "
                        "cavalry led by Blucher",
          map_evidence="Poppel village on the Liesbach at the bottom of the valley west of Taugwitz (map: Tauchwitz), "
                       "on the road to Eckardsberga.",
          geometry=POPPEL,
          geometry_source="assistant_redraw (old MF0045 had no geometry: cavalry keyed a.a, which the legend gives as "
                          "the bivouac of the Prussian main army)",
          tag="place_lookup", confidence_draft=4, time="1806-10-14, before 8 a.m., in the mist"),
     dict(event_id="MF0046", replaces="MF0046", passage="night",
          question="No farther than which village did the outposts of the leading division (Schmettau's) extend? "
                   "Mark the location.",
          question_zh="普军先头师（Schmettau 师）的前哨最远只到哪个村子？",
          answer_zh="Gernstadt（地图作 Gernstädt）",
          text_evidence="The outposts of the leading division (Schmettau’s) extended no farther than Gernstadt.",
          map_evidence="Village labelled Gernstädt south-west of Poppel, between Lisdorf and Rehhausen.",
          geometry={"type": "polygon", "coordinates": [[653, 520], [688, 508], [706, 530], [700, 572], [668, 580],
                                                        [650, 552]]},
          geometry_source="assistant_redraw (old MF0046 had no geometry: Schmettau's first deployment b.b, judged "
                          "unreadable)",
          tag="place_lookup", confidence_draft=3, time="1806-10-13/14, night"),
     dict(event_id="MF0047", replaces="MF0047", passage="morand",
          question="From which village did a strong Prussian force make yet another desperate attempt to outflank "
                   "Morand's left? Mark the location.",
          question_zh="一支强大的普军从哪个村子出发，再次拼命企图迂回 Morand 的左翼？",
          answer_zh="Sonnendorf",
          text_evidence="Yet another desperate attempt to outflank Morand’s left was made by a strong Prussian force from "
                        "Sonnendorf.",
          map_evidence="Sonnendorf village in the valley south of Rehhausen, above the Ilm.",
          geometry={"type": "polygon", "coordinates": [[860, 634], [893, 620], [914, 655], [908, 684], [880, 688],
                                                        [863, 662]]},
          geometry_source="assistant_redraw (old MF0047 marked an uncertain stretch of Morand's approach, legend i.i, "
                          "south-east of Hassenhausen)",
          tag="place_lookup", confidence_draft=3, time="1806-10-14, after 10 a.m."),
     dict(event_id="MF0048", replaces="MF0048", passage="kalkreuth",
          question="Where did Kalkreuth's left occupy an advanced position when he fell back to the line of heights running "
                   "south-east from Eckardsberga? Mark the area.",
          question_zh="Kalkreuth 退到 Eckardsberga 东南的高地线时，他的左翼在哪里占据了一个前出阵地？",
          answer_zh="Eckardsberga 与 Lisdorf 之间的林木高地 Puck Holz（地图作 Puckholz）",
          text_evidence="his left occupying an advanced position on the wooded height (Puck Holz) between Eckardsberga and "
                        "Lisdorf.",
          map_evidence="Wooded height labelled Puckholz between Eckardsberga and Lisdorf, north of the Eckardsberga road.",
          geometry={"type": "polygon", "coordinates": [[293, 468], [325, 449], [380, 444], [425, 452], [432, 478],
                                                        [402, 500], [340, 502], [298, 490]]},
          geometry_source="assistant_redraw (old MF0048 had no geometry: reserve division m.m near Rehhausen, judged "
                          "unreadable)",
          tag="place_lookup", confidence_draft=3, time="1806-10-14, after 12.30 p.m."),
    ])

if __name__ == "__main__":
    write(SPEC_J, "benchmark/sources/text_first/jena_b_2026-10-21.jsonl")
    write(SPEC_A, "benchmark/sources/text_first/auerstadt_b_2026-10-21.jsonl")
