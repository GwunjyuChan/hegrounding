"""Bergen-op-Zoom, night of 8-9 March 1814: text-first items from Jones, Journals of Sieges, 3rd ed. (1846), vol. II,
pp. 289-290 (the plan of attack), on maps/napoleon_maps/bergen_op_zoom_1814.jpg. MF0069, MF0070 and MF0072 keep
their IDs and geometry; MF0071 keeps its ID but its geometry is redrawn, because Jones gives Morrice's objective
(fronts 9-10 beside the lines of Steenbergen), not his starting point on the Breda road."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import RAW, write, map_record

IMAGE = "maps/napoleon_maps/bergen_op_zoom_1814.jpg"
M = map_record(IMAGE)
T = "1814-03-08, plan for the night assault"
SPEC = dict(
    battle_id="bergen_op_zoom_1814", created="2026-10-21", image=IMAGE, img_w=M["img_w"], img_h=M["img_h"],
    map_url=M["map_url"], map_provenance=M["map_provenance"],
    sources=dict(jones=dict(
        file=RAW + "bergen_jones1846_v2_journalsofsieges02jone_djvu.txt", archive_id="journalsofsieges02jone",
        citation="Sir John T. Jones, Journals of Sieges carried on by the Army under the Duke of Wellington, in Spain, "
                 "during the years 1811 to 1814, 3rd ed., ed. Harry D. Jones, vol. II (London: John Weale, 1846), "
                 "ch. VIII 'Surprise of Bergen-op-Zoom, March 1814'",
        source_kind="secondary_history by a Royal Engineers officer (engineer's journal)",
        rights_basis="published 1846; author d. 1843, editor d. 1866")),
    passages=dict(plan=dict(source="jones", pages="pp. 289-290",
        start="The command of the enterprise was intrusted to", end="made simultaneously.",
        drop=[r"^VOL\. II\. T$", r"SURPRISE OF BERGEN-OP-ZOOM\.$", r"^Bergen-op- ' O J$"],
        fixes=[("Attack of ^hich beinp^ immediately", "which being immediately"), ("SteenZoom. bergen", "Steenbergen"),
               ("Steen bergen", "Steenbergen"), ("650 men,'", "650 men,")])),
    items=[
     dict(event_id="MF0069", replaces="MF0069", passage="plan",
          question="By which dyke was the column under Skerret and Gore to advance? Mark the route.",
          question_zh="Skerret 和 Gore 率领的纵队要沿哪条堤推进？", answer_zh="Tholen 堤（Tholen Dyke）",
          text_evidence="was to advance by the Tholen Dyke",
          map_evidence="Tholen Dyke running from the north-west across the marshes to the harbour mouth.",
          geometry={"type": "line", "coordinates": [[168, 197], [226, 232], [283, 268], [343, 304], [409, 347], [425, 392]]},
          geometry_source="kept_from_MF0069", tag="route_or_line", confidence_draft=4, time=T),
     dict(event_id="MF0070", replaces="MF0070", passage="plan",
          question="Round which works was the column of 1000 Guards under Lord Proby to march? Mark the route.",
          question_zh="Proby 勋爵率领的一千名近卫军要绕过哪些工事行进？", answer_zh="设防营地（retrenched camp）的眼镜堡右翼，然后踏冰过 3、4 号正面的壕沟",
          text_evidence="was to march round the right flank of the lunettes of the retrenched camp",
          map_evidence="Route from the south along the west side of the Entrenched Camp up to the rampart.",
          geometry={"type": "line", "coordinates": [[568, 741], [548, 716], [535, 691], [525, 663], [520, 630], [512, 590], [508, 550]]},
          geometry_source="kept_from_MF0070", tag="route_or_line", confidence_draft=3, time=T),
     dict(event_id="MF0071", replaces="MF0071", passage="plan",
          question="Which part of the defences was the column under Lieutenant-Colonel Morrice to escalade? Mark the area.",
          question_zh="Morrice 中校的纵队要攀登哪一段城防？", answer_zh="第 9、10 号正面：紧挨 Steenbergen 防线、有宽阔淹水区掩护的一段",
          text_evidence="which being immediately next to the lines of Steenbergen, and covered by a broad inundation",
          map_evidence="Eastern fronts of the fortress where the Lines of Steenbergen join it, behind the inundation.",
          geometry={"type": "polygon", "coordinates": [[785, 285], [835, 290], [870, 340], [870, 430], [830, 440], [790, 380]]},
          geometry_source="assistant_redraw (old MF0071 polygon marked Morrice's start on the Breda road)",
          tag="map_reasoning", confidence_draft=2, time=T),
     dict(event_id="MF0072", replaces="MF0072", passage="plan",
          question="Where was the false attack under Lieutenant-Colonel Henry directed? Mark the route.",
          question_zh="Henry 中校的佯攻指向哪里？", answer_zh="12 号棱堡，其右面有 Steenbergen 城门",
          text_evidence="was ordered against bastion 12, (in the right face of which is the Steenbergen gate,)",
          map_evidence="Henry's route from the Steenbergen road to the Steenbergen Gate on the north side.",
          geometry={"type": "line", "coordinates": [[573, 260], [580, 286], [587, 308], [603, 323], [630, 330], [643, 340]]},
          geometry_source="kept_from_MF0072", tag="map_reasoning", confidence_draft=4, time=T),
     dict(event_id="MF0124", passage="plan",
          question="By what channel was the column under Skerret and Gore to enter the town? Mark the location.",
          question_zh="Skerret 和 Gore 的纵队要从哪条水道进城？", answer_zh="Zoom 河的河道入口（1 号与 15 号棱堡之间，港口处）",
          text_evidence="enter the town by the channel of the Zoom, between bastions 1 and 15",
          map_evidence="Where the River Zoom channel enters the fortifications on the west side, at the end of the Tholen Dyke.",
          geometry={"type": "point", "coordinates": [412, 398]}, tag="map_reasoning", confidence_draft=3, time=T),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/bergen_op_zoom_1814_2026-10-21.jsonl")
