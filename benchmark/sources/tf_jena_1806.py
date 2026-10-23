"""Jena, 14 Oct 1806, morning: text-first items from Petre (1907), p. 132, on maps/napoleon_maps/jena_1806.jpg.
MF0043 keeps its ID and geometry (Isserstedt village); text and question replaced."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import RAW, write, map_record

IMAGE = "maps/napoleon_maps/jena_1806.jpg"
M = map_record(IMAGE)
T = "1806-10-14, about 8.30 a.m."
SPEC = dict(
    battle_id="jena_1806", created="2026-10-21", image=IMAGE, img_w=M["img_w"], img_h=M["img_h"],
    map_url=M["map_url"], map_provenance=M["map_provenance"],
    sources=dict(petre=dict(
        file=RAW + "petre1907_prussia_india.history.resource.91968_djvu.txt", archive_id="india.history.resource.91968",
        citation="F. Loraine Petre, Napoleon's Conquest of Prussia, 1806 (London: John Lane, The Bodley Head, 1907)",
        source_kind="secondary_history", rights_basis="published 1907; author d. 1925")),
    passages=dict(hohenlohe=dict(source="petre", pages="p. 132",
        start="Hohenlohe, meanwhile, had for some time after", end="left rear.",
        drop=[r"^\d+ Napoleon’s Conquest of Prussia$"], fixes=[("Tle was", "He was"), ("the’ Weimar", "the Weimar")])),
    items=[
     dict(event_id="MF0043", replaces="MF0043", passage="hohenlohe",
          question="Where did Dyherrn's brigade form a reserve? Mark the location.",
          question_zh="Dyherrn 旅在哪里组成预备队？", answer_zh="Isserstadt（地图拼作 Isserstädt）一带",
          text_evidence="Dyherrn’s brigade formed a reserve about Isserstadt",
          map_evidence="Isserstädt village west of Vierzehnheiligen, beside the great wood.",
          geometry={"type": "polygon", "coordinates": [[446, 622], [473, 619], [490, 632], [487, 647], [466, 653], [444, 643]]},
          geometry_source="kept_from_MF0043", tag="place_lookup", confidence_draft=4, time=T),
     dict(event_id="MF0121", passage="hohenlohe",
          question="Around which village had Gravert begun to take up a position facing the direction of Tauenzien? Mark the location.",
          question_zh="Gravert 开始移到哪个村子一带、面朝 Tauenzien 方向布阵？", answer_zh="Gr. Romstadt（地图作 Gr. Romstädt）",
          text_evidence="who had begun to move to his left into a position about Gr. Romstadt, facing the direction of Tauenzien",
          map_evidence="Gr. Romstädt village west of Kl. Romstädt, north of Isserstädt.",
          geometry={"type": "point", "coordinates": [386, 495]}, tag="place_lookup", confidence_draft=3, time=T),
     dict(event_id="MF0122", passage="hohenlohe",
          question="Towards which village was Tauenzien ordered to fall back into second line? Mark the location.",
          question_zh="Tauenzien 奉命退向哪个村子、组成第二线？", answer_zh="Klein Romstadt（地图作 Kl. Romstädt）",
          text_evidence="He sent orders to Tauenzien to fall back into second line towards Klein Romstadt",
          map_evidence="Kl. Romstädt village north-west of Vierzehnheiligen.",
          geometry={"type": "point", "coordinates": [480, 498]}, tag="place_lookup", confidence_draft=3, time=T),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/jena_1806_2026-10-21.jsonl")
