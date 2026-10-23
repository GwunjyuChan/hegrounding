"""Quatre-Bras, 16 June 1815, before and about 2 p.m.: text-first items from Siborne (1844), vol. I, ch. VI, pp. 100-101,
on maps/napoleon_maps/quatre_bras_east_1815.jpg. MF0061-MF0063 keep their IDs; text, question and geometry replaced.
Siborne does not name the Bois de la Hutte light companies or Bijleveld, so the items follow his wording: the wood of
Delhutte held by skirmishers (MF0061), the horse-artillery guns on the high road (MF0062), and the advance of Bachelu's
and Foy's infantry divisions under Piré's cavalry screen (MF0063)."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import write, map_record, SIBORNE_V1, SIBORNE_DROP

IMAGE = "maps/napoleon_maps/quatre_bras_east_1815.jpg"
M = map_record(IMAGE)
T = "1815-06-16"
SPEC = dict(
    battle_id="quatre_bras_east_1815", created="2026-10-21", image=IMAGE, img_w=M["img_w"], img_h=M["img_h"],
    map_url=M["map_url"], map_provenance=M["map_provenance"],
    sources=dict(siborne=dict(SIBORNE_V1, citation=SIBORNE_V1["citation"] + ", ch. VI")),
    passages=dict(dispositions=dict(source="siborne", pages="pp. 100-101",
        start="In the mean time, the Prince of Orange made", end="whilst that of Jerome followed as a reserve.",
        drop=SIBORNE_DROP + [r"^FRANCE AND BELGIUM IN"],
        fixes=[("Niyelles", "Nivelles"), ("@Er-— lon’s", "d’Erlon’s"), ("hoping — that", "hoping that"),
               ("hasten its eee march", "hasten its march"), ("resolyed", "resolved")])),
    items=[
     dict(event_id="MF0061", replaces="MF0061", passage="dispositions",
          question="Which wood was occupied by skirmishers while the Prince of Orange made his dispositions? Mark the area.",
          question_zh="奥兰治亲王部署兵力时，哪片树林由散兵占据？请标出该区域。", answer_zh="Delhutte 树林（Bois de Delhutte）",
          text_evidence="the wood of Delhutte was occupied by skirmishers",
          map_evidence="Unlabelled woodland (tree-circle symbols) in the south-east of the sheet, south-east of Lairalle farm "
                       "and Piraumont; French skirmish groups lie along its northern edge.",
          geometry={"type": "polygon", "coordinates": [[270, 565], [310, 550], [360, 553], [420, 566], [460, 588],
                                                       [492, 622], [512, 680], [530, 765], [222, 765], [226, 690],
                                                       [252, 640]]},
          geometry_source="assistant_redraw (old MF0061 marked the Ch.27 light companies near Etang Materne)",
          tag="place_lookup", confidence_draft=2, time=T + ", before 2 p.m."),
     dict(event_id="MF0062", replaces="MF0062", passage="dispositions",
          question="Where did the Prince of Orange place two guns and a howitzer of Perponcher's divisional horse-artillery? Mark the location.",
          question_zh="奥兰治亲王把 Perponcher 师属骑炮兵的两门炮和一门榴弹炮放在哪里？请标出位置。",
          answer_zh="中央前方的大道（Charleroi 大道）上，Gemioncourt 以南（地图上的 Bijleveld 第一阵位）",
          text_evidence="Upon the high road, in advance of his centre, and in front of Frasne, he placed two guns and a howitzer of Perponcher’s divisional horse-artillery",
          map_evidence="Battery symbols astride the Charleroi high road south of Gemioncourt, labelled B. Bijleveld 1re posit.",
          geometry={"type": "polygon", "coordinates": [[0, 436], [22, 430], [28, 412], [56, 409], [62, 432],
                                                       [30, 444], [18, 460], [0, 460]]},
          geometry_source="assistant_redraw (old MF0062 marked only the guns east of the road at Bijleveld's 1st position)",
          tag="place_lookup", confidence_draft=3, time=T + ", before 2 p.m."),
     dict(event_id="MF0063", replaces="MF0063", passage="dispositions",
          question="Where did the infantry divisions of Bachelu and Foy advance under cover of Piré's light cavalry? Mark the area.",
          question_zh="在 Piré 轻骑兵掩护下，Bachelu 和 Foy 的步兵师向哪里推进？请标出该区域。",
          answer_zh="Charleroi 大道以东、Gemioncourt 与 Piraumont 以南的法军纵队推进区",
          text_evidence="Piré’s light cavalry, constituting a strong line of skirmishers with well-disposed supports, covered the advance of the infantry-divisions of Bachelu and Foy",
          map_evidence="French columns (Brig. Jamin (Foy), Brig. Husson, Brig. Campi, Dion Bachelu) running north-east from the "
                       "Charleroi road towards Piraumont, with Dion Piré beside them.",
          geometry={"type": "polygon", "coordinates": [[60, 684], [128, 470], [156, 466], [162, 490], [192, 444],
                                                       [218, 434], [252, 472], [205, 560], [152, 666], [92, 676]]},
          geometry_source="assistant_redraw (old MF0063 had no geometry; it named the Gemioncourt farm sector)",
          tag="place_lookup", confidence_draft=3, time=T + ", about 2 p.m."),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/quatre_bras_b_2026-10-21.jsonl")
