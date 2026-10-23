"""Marengo, 14 June 1800, 8-10 a.m.: text-first items from Sargent (1897), pp. 163-164, on
maps/napoleon_maps/marengo_morning_1800.jpg. MF0023 keeps its ID; its geometry is redrawn because Sargent places
Victor in front of the village along the Fontanone, not only in the village. MF0021 (Haddick's right on the
Bormida) is not covered: Sargent does not describe the Austrian deployment at that detail."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import RAW, write, map_record

IMAGE = "maps/napoleon_maps/marengo_morning_1800.jpg"
M = map_record(IMAGE)
SPEC = dict(
    battle_id="marengo_morning_1800", created="2026-10-21", image=IMAGE, img_w=M["img_w"], img_h=M["img_h"],
    map_url=M["map_url"], map_provenance=M["map_provenance"],
    sources=dict(sargent=dict(
        file=RAW + "sargent1897_marengo_cu31924024325346_djvu.txt", archive_id="cu31924024325346",
        citation="Herbert H. Sargent, The Campaign of Marengo, with Comments (Chicago: A. C. McClurg and Company, 1897), "
                 "ch. VIII 'Marengo'",
        source_kind="secondary_history", rights_basis="published 1897; author d. 1921")),
    passages=dict(morning=dict(source="sargent", pages="pp. 163-164",
        start="At daybreak on the morning of the 14th of", end="flank on that side.",
        drop=[r"THE CAMPAIGN OF MARENGO\.$", r"^MARENGO\. \d"], fixes=[])),
    items=[
     dict(event_id="MF0023", replaces="MF0023", passage="morning",
          question="Where had Victor taken up a position while the Austrians were deploying? Mark the area.",
          question_zh="奥军展开时，Victor 在哪里占据了阵地？", answer_zh="Marengo 村前、沿泥泞的 Fontanone 小溪",
          text_evidence="Victor at Marengo had taken up a position in front of the village along the muddy stream of Fontanone",
          map_evidence="Chambarlhac and Gardanne lines west and south-west of Marengo village, along the stream.",
          geometry={"type": "polygon", "coordinates": [[1150, 715], [1265, 690], [1330, 700], [1340, 735], [1290, 775], [1150, 770]]},
          geometry_source="assistant_redraw (old MF0023 polygon covered only the village)", tag="map_reasoning",
          confidence_draft=2, time="1800-06-14, about 8 a.m."),
     dict(event_id="MF0123", passage="morning",
          question="On which village did Melas direct Ott's division in order to take the French in flank? Mark the location.",
          question_zh="Melas 让 Ott 师指向哪个村子，以便从侧翼打法军？", answer_zh="Castel-ceriolo",
          text_evidence="having detached Ott's division, directed it on Castel-ceriolo, in order to take the French in",
          map_evidence="Castel-ceriolo village north-east of Marengo.",
          geometry={"type": "polygon", "coordinates": [[1470, 380], [1530, 375], [1545, 410], [1535, 455], [1490, 460], [1465, 420]]},
          tag="place_lookup", confidence_draft=3, time="1800-06-14, morning"),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/marengo_morning_1800_2026-10-21.jsonl")
