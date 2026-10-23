"""Toulouse, 10 April 1814: text-first items from Wellington's dispatch to Earl Bathurst, Toulouse, 12 April 1814, in
Gurwood (ed.), Dispatches, vol. XI (1838), pp. 632-637, on maps/napoleon_maps/toulouse_1814.jpg. Replaces the AI
paraphrases of MF0037-0040 (which followed Belmas via a copyrighted modern translation) with verbatim public-domain
passages. All four keep their IDs; questions are rewritten to what the dispatch states and geometry is redrawn where the
answer changed (MF0039 and MF0040 move to the canal bridge nearest the Garonne and the whole suburb on the left bank).
The OCR marks end-of-line hyphens with the sign "¬", which build_passage does not join; each such word is listed as a fix."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import RAW, write, map_record

IMAGE = "maps/napoleon_maps/toulouse_1814.jpg"
M = map_record(IMAGE)
T = "1814-04-10"
GURWOOD_DROP = [r"^1814\.$", r"^TOULOUSE\.$", r"^FRANCE\.$", r"^\d{3}$", r"^G36$", r"^63 7$"]
SPEC = dict(
    battle_id="toulouse_1814", created="2026-10-21", image=IMAGE, img_w=M["img_w"], img_h=M["img_h"],
    map_url=M["map_url"], map_provenance=M["map_provenance"],
    sources=dict(gurwood=dict(
        file=RAW + "wellington_dispatches_vol11_1838_djvu.txt", archive_id="vol11dispatcheso00well",
        citation="Wellington to Earl Bathurst, Toulouse, 12 April 1814, in J. Gurwood (ed.), The Dispatches of Field "
                 "Marshal the Duke of Wellington, vol. XI (London: John Murray, 1838)",
        source_kind="primary_dispatch (commanding general's official report of the battle)",
        rights_basis="published 1838; Wellington d. 1852, editor Gurwood d. 1845")),
    passages=dict(
        hussars=dict(source="gurwood", pages="pp. 632-633", drop=GURWOOD_DROP,
            start="We immediately moved forward to the neighbourhood of", end="assistance for some time.",
            fixes=[("com¬ mand", "command"), ("pos¬ session", "possession")]),
        heights=dict(source="gurwood", pages="p. 635", drop=GURWOOD_DROP,
            start="In the mean time, Marshal Sir William Beresford, with", end="were in our possession.",
            fixes=[("re¬ formed", "re-formed"), ("6tli", "6th"), ("con¬ tinuing", "continuing")]),
        left=dict(source="gurwood", pages="p. 636", drop=GURWOOD_DROP,
            start="While the operations above detailed were going on, on", end="great merit, was killed.",
            fixes=[("sus¬ tained", "sustained"), ("assist¬ ance", "assistance")]),
    ),
    items=[
     dict(event_id="MF0037", replaces="MF0037", passage="hussars",
          question="Through which village did the 18th hussars drive a superior body of the enemy's cavalry? Mark the location.",
          question_zh="第 18 骠骑兵团把数量占优的敌骑兵赶过了哪个村子？", answer_zh="Croix d'Orade（地图作 Croix Daurade）",
          text_evidence="which they drove through the village of Croix d’Orade",
          map_evidence="Croix Daurade village on the road just west of the Bridge of Croix Daurade over the R. Hers (the dispatch's Ers), north of the battlefield.",
          geometry={"type": "polygon", "coordinates": [[445, 185], [470, 162], [512, 145], [532, 135], [542, 148], [522, 190], [500, 212], [450, 205]]},
          geometry_source="assistant_redraw (old MF0037 marked the Mamelon de la Pujade from a Belmas paraphrase)",
          tag="place_lookup", confidence_draft=3, time="1814-04-08, after the crossing of the Garonne"),
     dict(event_id="MF0038", replaces="MF0038", passage="heights",
          question="In which village had the badness of the roads induced Beresford to leave his artillery? Mark the location.",
          question_zh="由于道路太坏，Beresford 把他的炮兵留在了哪个村子？", answer_zh="Montblanc（地图作 Mont Blanc）",
          text_evidence="The badness of the roads had induced the Marshal to leave his artillery in the village of Montblanc",
          map_evidence="Mont Blanc, a hamlet on the west bank of the R. Hers south of Croix Daurade, at the northern foot of the heights.",
          geometry={"type": "polygon", "coordinates": [[562, 320], [600, 317], [640, 322], [642, 358], [600, 364], [562, 360]]},
          geometry_source="assistant_redraw (old MF0038 marked the work at Mas des Augustins from a Belmas paraphrase)",
          tag="place_lookup", confidence_draft=3, time=T + ", during Beresford's attack"),
     dict(event_id="MF0039", replaces="MF0039", passage="left",
          question="Within which tête de pont did Picton's 3rd division drive the enemy before being repulsed in trying to carry it? Mark the location.",
          question_zh="Picton 的第 3 师把敌人赶进了哪座桥头堡，随后强攻失败？", answer_zh="运河上最靠近 Garonne 河的那座桥（Ponts Jumeaux）的桥头堡",
          text_evidence="drove the enemy within the tete de pont on the bridge of the canal nearest to the Garonne",
          map_evidence="Ponts Jumeaux, where the Languedoc Canal reaches the Garonne north-west of the town, with a French bridgehead work beside the label.",
          geometry={"type": "polygon", "coordinates": [[62, 586], [88, 584], [94, 600], [86, 620], [66, 620], [58, 604]]},
          geometry_source="assistant_redraw (old MF0039 marked the Pont des Minimes from a Belmas paraphrase)",
          tag="place_lookup", confidence_draft=3, time=T),
     dict(event_id="MF0040", replaces="MF0040", passage="left",
          question="Where did Sir Rowland Hill drive the enemy from their exterior works within the ancient wall? Mark the area.",
          question_zh="Rowland Hill 在哪里把敌人从外围工事赶回了旧城墙以内？", answer_zh="Garonne 河左岸的郊区（St. Cyprien）",
          text_evidence="Lieut. General Sir Rowland Hill drove the enemy from their exterior works in the suburb, on the left of the Garonne, within the ancient wall.",
          map_evidence="Suburb of St. Cyprien on the west (left) bank of the Garonne opposite the town, enclosed by its line of works.",
          geometry={"type": "polygon", "coordinates": [[120, 745], [150, 738], [186, 722], [210, 718], [240, 745], [236, 785], [215, 830], [205, 875], [188, 880], [160, 860], [128, 856], [112, 850], [100, 800], [108, 776]]},
          geometry_source="assistant_redraw (old MF0040 marked only the inner wall line of St. Cyprien after Reille's withdrawal)",
          tag="place_lookup", confidence_draft=3, time=T),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/toulouse_b_2026-10-21.jsonl")
