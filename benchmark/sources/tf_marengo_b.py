"""Marengo, 13-15 June 1800: text-first items from Sargent, The Campaign of Marengo (1897), ch. VIII, on two Berthier
plates. Replaces the AI paraphrases of the plate captions (MF0005-0008 on plate IV, MF0021/0022/0024 on plate I) with
verbatim public-domain passages; every item keeps its ID.
Plate IV (maps/napoleon_maps/marengo_plate4.jpg, positions on the morning after the battle):
  MF0005 keeps its Castel-ceriolo geometry; MF0006 (old: unreadable deployment line Marengo-Spinetta) now asks for the
  town of Marengo; MF0007 (old: ambiguous Rivaud bivouac, which Sargent never mentions) is now an abstention item,
  San Giuliano lying east of the map edge; MF0008 (old: ambiguous Dalton line before the bridge-head, from a modern
  translation) now asks for the bridge-head Bonaparte prepared to assault on the 15th.
Plate I (maps/napoleon_maps/marengo_morning_1800.jpg, 8-10 a.m. on the 14th):
  Sargent does not describe Haddick's right, Elsnitz's cavalry column or the Guard before the Buzana farm, so MF0021
  now asks for the bridge-head from which the Austrians issued at daybreak, MF0022 for the place where Lannes formed his
  corps about ten, and MF0024 (Consular Guard on the evening of the 13th, along the Scrivia near Tortona) is an
  abstention item. MF0023 and MF0123 (tf_marengo_morning_1800.py) are not touched; the p. 163-164 passage is reused."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import RAW, write, map_record

SARGENT = dict(
    file=RAW + "sargent1897_marengo_cu31924024325346_djvu.txt", archive_id="cu31924024325346",
    citation="Herbert H. Sargent, The Campaign of Marengo, with Comments (Chicago: A. C. McClurg and Company, 1897), "
             "ch. VIII 'Marengo'",
    source_kind="secondary_history", rights_basis="published 1897; author d. 1921")
DROP = [r"THE CAMPAIGN OF MARENGO\.$", r"^MARENGO\. [\dl]"]
GROUND = dict(source="sargent", pages="p. 163", drop=DROP, fixes=[],
              start="The plain of Marengo lies between", end="render the ground uneven.")

IMAGE4 = "maps/napoleon_maps/marengo_plate4.jpg"
M4 = map_record(IMAGE4)
SPEC_P4 = dict(
    battle_id="marengo_1800", created="2026-10-21", image=IMAGE4, img_w=M4["img_w"], img_h=M4["img_h"],
    map_url=M4["map_url"], map_provenance=M4["map_provenance"],
    sources=dict(sargent=SARGENT),
    passages=dict(
        ground=GROUND,
        after=dict(source="sargent", pages="pp. 171-172", drop=DROP, fixes=[],
            start="Meanwhile General Ott, hearing the firing", end="signed."),
    ),
    items=[
     dict(event_id="MF0005", replaces="MF0005", passage="ground",
          question="Which village lies about two miles north of Marengo? Mark the location.",
          question_zh="Marengo 以北约两英里是哪个村子？", answer_zh="Castel-ceriolo",
          text_evidence="About two miles north of Marengo is the village of Castel-ceriolo.",
          map_evidence="Castel-ceriolo village (buildings along the road) north-east of Marengo, labelled 'Castel-ceriolo'.",
          geometry={"type": "polygon", "coordinates": [[1512, 389], [1542, 395], [1564, 416], [1570, 458], [1539, 478], [1502, 455], [1497, 422]]},
          geometry_source="kept_from_MF0005", tag="place_lookup", confidence_draft=4, time="1800-06-15, morning"),
     dict(event_id="MF0006", replaces="MF0006", passage="ground",
          question="Where is the town of Marengo, from which the battle takes its name? Mark the location.",
          question_zh="战役得名的 Marengo 镇在哪里？", answer_zh="Marengo（Bormida 东岸附近、亚历山德里亚通往曼托瓦的大路上）",
          text_evidence="The town of Marengo, from which this battle takes its name, is situated near the east bank of the Bormida on the great highway leading from Alessandria to Mantua.",
          map_evidence="Marengo: the group of buildings on the road east of the Bormida, labelled 'Marengo'.",
          geometry={"type": "polygon", "coordinates": [[1342, 719], [1381, 721], [1386, 738], [1368, 752], [1344, 746]]},
          geometry_source="assistant_redraw (old MF0006 had no geometry: unreadable deployment line Marengo-Spinetta)",
          tag="place_lookup", confidence_draft=4, time="1800-06-15, morning"),
     dict(event_id="MF0007", replaces="MF0007", passage="ground",
          question="Where does the village of San Giuliano lie? Mark the location.",
          question_zh="San Giuliano 村在哪里？", answer_zh="Marengo 以东约三英里的大路上（不在这张图上）",
          text_evidence="the village of San Giuliano, which lies on the main road about three miles east of Marengo",
          map_evidence="San Giuliano lies east of the map edge; the easternmost places shown (Lodola, Paroli, la Lombarda) are well short of three miles from Marengo.",
          geometry=None, status="outside_map", tag="place_lookup", confidence_draft=3, time="1800-06-15, morning"),
     dict(event_id="MF0008", replaces="MF0008", passage="after",
          question="On the morning after the battle, what did Bonaparte make preparations to assault before crossing the Bormida? Mark the location.",
          question_zh="战役次日早晨，拿破仑在渡过 Bormida 之前准备强攻什么？", answer_zh="Bormida 河上（亚历山德里亚前）的桥头堡",
          text_evidence="On the following morning, Bonaparte made preparations to assault the bridge-head and to cross the Bormida, in order to attack the Austrians in Alessandria.",
          map_evidence="'Tête de Pont' lettering where the Alessandria road crosses the Bormida east of the fortress.",
          geometry={"type": "polygon", "coordinates": [[1036, 500], [1060, 492], [1078, 515], [1078, 545], [1058, 552], [1040, 530]]},
          geometry_source="assistant_redraw (old MF0008 had no geometry: ambiguous 30th demi-brigade line from a modern translation)",
          tag="place_lookup", confidence_draft=3, time="1800-06-15, morning"),
    ])

IMAGE1 = "maps/napoleon_maps/marengo_morning_1800.jpg"
M1 = map_record(IMAGE1)
SPEC_P1 = dict(
    battle_id="marengo_morning_1800", created="2026-10-21", image=IMAGE1, img_w=M1["img_w"], img_h=M1["img_h"],
    map_url=M1["map_url"], map_provenance=M1["map_provenance"],
    sources=dict(sargent=SARGENT),
    passages=dict(
        morning=dict(source="sargent", pages="pp. 163-164", drop=DROP, fixes=[],
            start="The plain of Marengo lies between", end="with a part of his corps."),
        evening13=dict(source="sargent", pages="p. 161", drop=DROP, fixes=[(".evening", "evening")],
            start="Thus it happened that on the", end="morrow."),
    ),
    items=[
     dict(event_id="MF0021", replaces="MF0021", passage="morning",
          question="At daybreak on the 14th, from what work on the right bank did the Austrians issue after crossing the Bormida? Mark the location.",
          question_zh="14 日拂晓，奥军渡过 Bormida 后从右岸的什么工事中出来？", answer_zh="Bormida 两座桥前（右岸）的桥头堡",
          text_evidence="the Austrians began to cross the Bormida and to issue from the bridge-head on the right bank",
          map_evidence="'Tête de Pont' at the Bormida crossing of the Alessandria road, with Austrian columns debouching from it.",
          geometry={"type": "polygon", "coordinates": [[990, 478], [1012, 468], [1026, 488], [1023, 518], [1005, 528], [992, 506]]},
          geometry_source="assistant_redraw (old MF0021 marked Haddick's first line near Pedrabona)",
          tag="place_lookup", confidence_draft=3, time="1800-06-14, daybreak"),
     dict(event_id="MF0022", replaces="MF0022", passage="morning",
          question="Where did Lannes bring his corps into line about ten o'clock? Mark the area.",
          question_zh="大约十点，Lannes 把他的军投入了哪里的战线？", answer_zh="Victor 的右侧",
          text_evidence="About ten o'clock Lannes brought his corps into line on the right of Victor.",
          map_evidence="Lannes's infantry (Watrin) columns labelled 'Lannes' east of Marengo near la Fornace, arriving on the right of Victor's line.",
          geometry={"type": "polygon", "coordinates": [[1430, 690], [1475, 680], [1505, 700], [1500, 745], [1470, 768], [1430, 755]]},
          geometry_source="assistant_redraw (old MF0022 had no geometry: ambiguous Elsnitz cavalry north of Castel-ceriolo)",
          tag="map_reasoning", confidence_draft=2, time="1800-06-14, about 10 a.m."),
     dict(event_id="MF0024", replaces="MF0024", passage="evening13",
          question="Where were the Consular Guard, two regiments of cavalry and Monnier's division on the evening of the 13th of June? Mark the location.",
          question_zh="6 月 13 日晚，执政卫队、两个骑兵团和 Monnier 师在哪里？", answer_zh="Tortona 附近的 Scrivia 河沿岸（不在这张图上）",
          text_evidence="the Consular Guard, two regiments of cavalry, and Monnier's division, which belonged to the corps of Desaix, were along the Scrivia near Tortona.",
          map_evidence="The Scrivia and Tortona lie far east of the map edge; only the 'Route de Tortone' leading there is shown.",
          geometry=None, status="outside_map", tag="place_lookup", confidence_draft=4, time="1800-06-13, evening"),
    ])

if __name__ == "__main__":
    write(SPEC_P4, "benchmark/sources/text_first/marengo_plate4_b_2026-10-21.jsonl")
    write(SPEC_P1, "benchmark/sources/text_first/marengo_morning_b_2026-10-21.jsonl")
