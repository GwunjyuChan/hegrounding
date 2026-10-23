"""Pultusk, 26 Dec 1806: text-first items from Petre (1901), pp. 90-91, on maps/napoleon_maps/pultusk_1806.jpg.
MF0082 keeps its ID and geometry; its map-derived text and question are replaced by the verbatim passage."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import RAW, write

PETRE = RAW + "petre_campaign_in_poland_1901_napoleonscampaig00petruoft_djvu.txt"
SPEC = dict(
    battle_id="pultusk_1806", created="2026-10-21",
    image="maps/napoleon_maps/pultusk_1806.jpg", img_w=2356, img_h=1728,
    map_url="https://www.napoleon-series.org/images/military/maps/1806/pultusk1.jpg",
    map_provenance="'Plan der Schlacht von Pultusk den 26ten December 1806', Pl. I, scale 1:20,000; German-language "
                   "lettered plan with Renvoi. Downloaded from napoleon-series.org (Maps page). Original publication "
                   "unverified (candidate: atlas to E. von Hoepfner, Der Krieg von 1806 und 1807, Berlin 1850-51).",
    sources=dict(petre=dict(
        file=PETRE, archive_id="napoleonscampaig00petruoft",
        citation="F. Loraine Petre, Napoleon's Campaign in Poland, 1806-7 (London: Sampson Low, Marston & Co., 1901), "
                 "ch. V(a) 'Pultusk'",
        source_kind="secondary_history (based on Dumas, Wilson, Hoepfner, Davout and Lannes' report)",
        rights_basis="published 1901; author d. 1925; archive.org possible-copyright-status NOT_IN_COPYRIGHT")),
    passages=dict(position=dict(
        source="petre", start="The position chosen by Bennigsen", end="and Ostrolenka.", pages="pp. 90-91",
        drop=[r"^THE BATTLES OF PULTUSK", r"^\d+ NAPOLEON'S CAMPAIGN", r"^NAPOLEON'S CAMPAIGN"],
        fixes=[("Bagavout * thus", "Bagavout thus"), ("Eussian", "Russian"), ("Eozan", "Rozan")])),
    items=[
     dict(event_id="MF0082", replaces="MF0082", passage="position",
          question="On the Russian right, where was Barclay de Tolly thrown forward with his jager regiments? Mark the area.",
          question_zh="俄军右翼，Barclay de Tolly 带猎兵团前出到了哪里？", answer_zh="Mosin 高地大树林的西南半部",
          text_evidence="Barclay de Tolly was thrown forward into the south-western half of the great wood",
          map_evidence="Barclay's B-series units in the large wood south-west of Mosino, on the Pultusk side of the road.",
          geometry={"type": "polygon", "coordinates": [[1748, 784], [1835, 784], [1944, 828], [1954, 920], [1905, 1004],
                                                       [1802, 1015], [1727, 967], [1738, 870]]},
          geometry_source="kept_from_MF0082", tag="map_reasoning", confidence_draft=3, time="1806-12-26, before the attack"),
     dict(event_id="MF0111", passage="position",
          question="Where did Bagavout stand with his detachment to cover the Narew bridge? Mark the area.",
          question_zh="Bagavout 带分遣队在哪里掩护 Narew 河桥？", answer_zh="深谷外侧（离镇较远一侧）、Pultusk 西北河岸高地",
          text_evidence="Here Bagavout stood, beyond the deep ravine",
          map_evidence="C-series units north-west of the town, west of the ravine that falls to the Narew low ground.",
          geometry={"type": "polygon", "coordinates": [[815, 1190], [1060, 1190], [1080, 1300], [1060, 1415],
                                                       [860, 1400], [815, 1300]]},
          tag="map_reasoning", confidence_draft=3, time="1806-12-26, before the attack"),
     dict(event_id="MF0112", passage="position",
          question="Along what line did Bennigsen draw up his main body in three lines? Mark the line.",
          question_zh="Bennigsen 的主力三线列阵沿哪条线展开？", answer_zh="Golymin 大道，从 Pultusk 到大道进入 Mosin 高地树林处",
          text_evidence="practically coincided with the line of the Golymin road, from Pultusk to the point where it enters the wood on the Mosin heights",
          map_evidence="A-series infantry lines along the road from the town north-east to the edge of the great wood.",
          geometry={"type": "line", "coordinates": [[1300, 1440], [1500, 1345], [1700, 1250], [1880, 1055]]},
          tag="route_or_line", confidence_draft=3, time="1806-12-26, before the attack"),
     dict(event_id="MF0113", passage="position",
          question="Where was the battery that commanded the approach from Golymin? Mark the location.",
          question_zh="控制 Golymin 来路的那个炮兵连在哪里？", answer_zh="大树林外、骑跨 Golymin 大道（树林靠 Mosin 一侧）",
          text_evidence="supported a battery placed outside the wood, astride of the road, commanding the approach from Golymin",
          map_evidence="Gun marks beside the road just north of the wood edge, near the B-II label below Mosino.",
          geometry={"type": "point", "coordinates": [1980, 800]}, tag="map_reasoning", confidence_draft=3,
          time="1806-12-26, before the attack"),
     dict(event_id="MF0114", passage="position",
          question="Where was the long line of cossacks posted? Mark the line.",
          question_zh="那条很长的哥萨克线在哪里？", answer_zh="骑兵线前方的洼地里，一直延伸到森林前的零星树林",
          text_evidence="In the valley, beyond the cavalry and extending into the outlying woods in front of the forest, was a long line of cossacks",
          map_evidence="E-series double-hatched chain across the valley from west of Pultusk to north-west of Mosino.",
          geometry={"type": "line", "coordinates": [[1040, 975], [1250, 912], [1400, 825], [1600, 700], [1800, 560], [1895, 497]]},
          tag="route_or_line", confidence_draft=3, time="1806-12-26, before the attack"),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/pultusk_1806_2026-10-21.jsonl")
