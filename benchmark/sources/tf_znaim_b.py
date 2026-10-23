"""Znaim, 11 July 1809, morning: text-first item from Pelet, tome IV (1826), p. 266, on maps/napoleon_maps/znaim_1809.jpg.
French original cut from the OCR with the fixes listed; the model reads Claude's English translation (review pending).
MF0076 keeps its ID; the old item (Masséna's formations approaching from the south toward the river crossing) is
narrowed to the division Pelet names: Legrand's, with which Masséna reached the Taja at ten in the morning."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import write, map_record
from pelet_common import PELET_T4, PELET_DROP

IMAGE = "maps/napoleon_maps/znaim_1809.jpg"
M = map_record(IMAGE)
TR_APPROACH = ("Davout, who has already passed Nicolsburg, receives the order to make for Znaim. Masséna is informed of "
    "the general disposition. He will form the pivot of the great wheel that the Emperor is carrying out by the right. "
    "Meanwhile Davout was about a dozen leagues from Znaim; Napoleon, 14; Oudinot, farther still. It was difficult for "
    "these corps to arrive before the 12th. Marmont found himself isolated in the midst of the enemy army. Masséna was "
    "4 leagues away, with two divisions of infantry and two of cavalry, much weakened. There was in the position of the "
    "11th corps and in Masséna's march an audacity that overawed the Archduke. Marmont kept a good countenance on the "
    "morning of the 11th. Masséna set out very early for Znaim. The superb positions of Jetzeldorf, the marshy Pulka "
    "bordered with woods, two excellent commanding heights covered with vineyards, were abandoned. The enemy withdrew "
    "to the banks of the Taja. Masséna arrived there at ten in the morning, with Legrand's division.")
SPEC = dict(
    battle_id="znaim_1809", created="2026-10-21", image=IMAGE, img_w=M["img_w"], img_h=M["img_h"],
    map_url=M["map_url"], map_provenance=M["map_provenance"],
    sources=dict(pelet=PELET_T4),
    passages=dict(
        approach=dict(source="pelet", pages="p. 266", lang="fr", drop=PELET_DROP,
            start="Davout qui a déjà dépassé", end="avec la division Legrand.", translation=TR_APPROACH,
            fixes=[("Nicolsboui^,", "Nicolsbourg,"), ("à i4 ;Oudinot", "à 14; Oudinot"),
                   ("Tl était dilBcile", "Il était difficile"), ("avant le la.", "avant le 12."),
                   ("ta position du 1 1' corps", "la position du 11e corps"), ("fit- bonne", "fit bonne"),
                   ("du II.", "du 11."), ("laBulka", "la Pulka"), ("Ij'ennemi", "L'ennemi")]),
    ),
    items=[
     dict(event_id="MF0076", replaces="MF0076", passage="approach",
          question="With which division did Masséna arrive on the banks of the Taja at ten in the morning? Mark that division.",
          question_zh="上午十点，马塞纳带着哪个师到达 Taja 河岸？请标出该师。", answer_zh="Legrand 师（在 Oblass 以南、维也纳大道两侧）",
          text_evidence="Masséna arrived there at ten in the morning, with Legrand's division.",
          source_evidence="Masséna y arriva à dix heures du matin , avec la division Legrand.",
          map_evidence="Two infantry bars labelled Legrand astride the Vienna road south of Oblass and the Schallersdorf bridge, "
                       "north of the Saint-Sulpice cuirassiers.",
          geometry={"type": "polygon", "coordinates": [[686, 1750], [782, 1712], [786, 1748], [704, 1788], [690, 1772]]},
          geometry_source="assistant_redraw (old MF0076 had no geometry; it named Masséna's southern approach sector)",
          tag="place_lookup", confidence_draft=3, time="1809-07-11, about 10 a.m."),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/znaim_b_2026-10-21.jsonl")
