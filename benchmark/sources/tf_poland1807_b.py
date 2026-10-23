"""Heilsberg (10 June 1807), Eylau (8 Feb 1807) and Friedland (14 June 1807): text-first items from Petre, Napoleon's
Campaign in Poland 1806-7 (1901), on the three Mikhailovsky-Danilevsky plans (Cyrillic labels):
maps/napoleon_maps/heilsberg_1807.jpg, eylau_1807.jpg, friedland_1807.jpg.
Replaces the AI paraphrases of MF0085-0096 (map-derived, not independent text) with verbatim passages. All twelve keep
their IDs; questions are rewritten to places Petre names and the map labels (in Russian transliteration). MF0090
(French Guard, 'unreadable') and MF0095 (Russian Guard, 'source_conflict') are rewritten to other well-supported
questions on the same map. Passages are cut between Petre's footnotes, or the footnote lines are dropped, so no
footnote text enters the model input."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import RAW, write, map_record

PETRE_FILE = RAW + "petre_campaign_in_poland_1901_napoleonscampaig00petruoft_djvu.txt"
PETRE_CIT = "F. Loraine Petre, Napoleon's Campaign in Poland, 1806-7 (London: Sampson Low, Marston & Co., 1901)"
PETRE_KIND = "secondary_history (based on Dumas, Hoepfner, Wilson, the French Archives Historiques, Kausler)"
PETRE_RIGHTS = "published 1901; author d. 1925; archive.org possible-copyright-status NOT_IN_COPYRIGHT"
HEAD = [r"^THE BATTLE", r"^TEE BATTLE", r"^\d+ NAPOLEON'S CAMPAIGN", r"^NAPOLEON'S CAMPAIGN"]


def petre(chapter):
    return dict(file=PETRE_FILE, archive_id="napoleonscampaig00petruoft", citation=f"{PETRE_CIT}, {chapter}",
                source_kind=PETRE_KIND, rights_basis=PETRE_RIGHTS)


def spec(battle_id, image, **kw):
    M = map_record(image)
    return dict(battle_id=battle_id, created="2026-10-21", image=image, img_w=M["img_w"], img_h=M["img_h"],
                map_url=M["map_url"], map_provenance=M["map_provenance"], **kw)


# ---------------------------------------------------------------- Heilsberg
TH = "1807-06-10"
HEILSBERG = spec("heilsberg_1807", "maps/napoleon_maps/heilsberg_1807.jpg",
    sources=dict(petre=petre("Part V ch. II 'The Battle of Heilsberg, and Operations of the 11th-13th June'")),
    passages=dict(
        works=dict(source="petre", pages="p. 286", drop=HEAD,
            start="On the left bank of the river, where it passes through the",
            end="fortifications on this side of the river.", fixes=[]),
        line=dict(source="petre", pages="p. 287", drop=HEAD,
            start="On the fortified heights on both banks, Bennigsen, on the", end="held Grossendorf.",
            fixes=[("Eussian", "Russian")]),
        orders=dict(source="petre", pages="p. 288", drop=HEAD,
            start="Between 9 and 10 a.m., the", end="columns were.",
            fixes=[("Kussian", "Russian"), ("Keichenburg", "Reichenburg")]),
        advance=dict(source="petre", pages="p. 289", drop=HEAD,
            start="Shortly after leaving Launau, Legrand's division had", end="Lawden, which he had nearly reached.",
            fixes=[("Savary 's", "Savary's")]),
    ),
    items=[
     dict(event_id="MF0085", replaces="MF0085", passage="orders",
          question="From which place was Bagration retiring, on the opposite side of the river, when he was ordered to cross by the pontoon bridges? Mark the location.",
          question_zh="Bagration 接到命令从浮桥过河时，他正在河对岸从哪个地方撤退？", answer_zh="Reichenberg（Petre 拼作 Reichenburg；图上 Рейхенбергъ）",
          text_evidence="Bagration, who was retiring on the opposite side of the river from Reichenburg",
          map_evidence="Village Рейхенбергъ (Reichenberg) south of the Alle, with the label '1. Позиція К. Багратіона' (Bagration's 1st position) beside it.",
          geometry={"type": "polygon", "coordinates": [[406, 818], [428, 805], [452, 795], [462, 806], [466, 836], [490, 858], [482, 870], [460, 862], [440, 852], [410, 838]]},
          geometry_source="assistant_redraw (old MF0085 marked Bagration's troop symbols west of the village)",
          tag="place_lookup", confidence_draft=3, time=TH + ", 9-10 a.m."),
     dict(event_id="MF0086", replaces="MF0086", passage="advance",
          question="Which village did St. Cyr occupy about 3 p.m. under the protection of Soult's 36 guns? Mark the location.",
          question_zh="下午 3 点左右，St. Cyr 在 Soult 的 36 门炮掩护下占领了哪个村子？", answer_zh="Bewernick（图上 Беверникъ）",
          text_evidence="Under the protection of Soult's 36 guns, St. Cyr occupied Bewernick about 3 p.m.",
          map_evidence="Village Беверникъ (Bewernick) on the Guttstadt road north of the Alle, between Launau and Langwiese.",
          geometry={"type": "polygon", "coordinates": [[266, 532], [284, 514], [303, 520], [306, 546], [292, 553], [268, 546]]},
          geometry_source="assistant_redraw (old MF0086 marked the French columns west and south of the village)",
          tag="place_lookup", confidence_draft=4, time=TH + ", about 3 p.m."),
     dict(event_id="MF0087", replaces="MF0087", passage="line",
          question="Which village, beyond the lake, was held by 5 regiments of cossacks? Mark the location.",
          question_zh="湖那边由 5 个哥萨克团据守的是哪个村子？", answer_zh="Grossendorf（图上 Гроссендорфъ，湖北岸）",
          text_evidence="Beyond the lake, 5 regiments of cossacks held Grossendorf.",
          map_evidence="Гроссендорфъ (Grossendorf) at the north shore of the lake north of Heilsberg, with Платовъ (Platov's cossacks) beside it. A second block of houses west of the name is labelled 'Речъ'; the polygon takes the village on the lake shore that Petre describes.",
          geometry={"type": "polygon", "coordinates": [[606, 236], [628, 230], [650, 246], [656, 282], [640, 292], [612, 290], [604, 262]]},
          geometry_source="assistant_redraw (old MF0087 marked Platov's troop symbols east of the village)",
          tag="place_lookup", confidence_draft=3, time=TH),
     dict(event_id="MF0088", replaces="MF0088", passage="works",
          question="Along what line did redoubts No. 1, No. 2 and No. 3 stand on the left bank? Mark the line.",
          question_zh="左岸 1、2、3 号多面堡沿哪条线排列？", answer_zh="从靠河的 1 号多面堡经 2 号到右后方的 3 号多面堡",
          text_evidence="Some 500 paces from the river, on a projecting spur, was redoubt No. 1 ; 900 paces farther in the same line was redoubt No. 2. No. 3 was 1500 paces farther, on the right rear of No. 2.",
          map_evidence="Works labelled N.1, N.2 and N.3 west and north-west of Heilsberg (Гейльсбергъ), N.1 nearest the river.",
          geometry={"type": "line", "coordinates": [[549, 512], [547, 470], [592, 418]]},
          geometry_source="assistant_redraw (old MF0088 was a line from N.1 to beyond N.3, towards N.5)",
          tag="route_or_line", confidence_draft=3, time=TH),
    ])

# ---------------------------------------------------------------- Eylau
TE = "1807-02-08"
EYLAU = spec("eylau_1807", "maps/napoleon_maps/eylau_1807.jpg",
    sources=dict(petre=petre("Part III ch. II 'The Battle of Eylau'")),
    passages=dict(
        night=dict(source="petre", pages="p. 167", drop=HEAD,
            start="Bennigsen's army was thus disposed for the night.", end="munication with Lestocq.",
            fixes=[("Eylau. f The", "Eylau. The")]),
        reserve=dict(source="petre", pages="p. 168", drop=HEAD,
            start="In front of Serpallen was Bagavout, with 2 infantry", end="Kl. Sausgarten.",
            fixes=[("Kamenskoi.*", "Kamenskoi."), ("Gallitzin.f", "Gallitzin."), ("Anklappen.J", "Anklappen.")]),
        davout=dict(source="petre", pages="p. 184", drop=HEAD,
            start="DaYOut, at 2 p.m. on the 7th, had received orders from", end="48th regiment.",
            fixes=[("DaYOut", "Davout"), ("Berthier *", "Berthier"), ("Eriant", "Friant"), ("position.f", "position.")]),
        reconnaissance=dict(source="petre", pages="p. 185", drop=HEAD,
            start="Davout, whilst waiting, caused a reconnaissance to be", end="Serpallen.",
            fixes=[("Eussian", "Russian")]),
    ),
    items=[
     dict(event_id="MF0089", replaces="MF0089", passage="reconnaissance",
          question="In the direction of which village was the rest of Friant's division sent, following Marulaz and the 33rd regiment? Mark the location.",
          question_zh="Friant 师的其余部队跟在 Marulaz 和第 33 团后面，朝哪个村子方向前进？", answer_zh="Klein Sausgarten（图上 Саусгартенъ）",
          text_evidence="followed, in the direction of Klein Sausgarten, by the rest of Friant's division",
          map_evidence="Village Саусгартенъ (Sausgarten) east of Eylau, north of Serpallen.",
          geometry={"type": "polygon", "coordinates": [[696, 706], [718, 696], [745, 700], [752, 722], [740, 738], [712, 738], [698, 724]]},
          geometry_source="assistant_redraw (old MF0089 marked Davout's columns near Mollwitten, which Petre does not name)",
          tag="place_lookup", confidence_draft=3, time=TE + ", 11 a.m.-noon"),
     dict(event_id="MF0090", replaces="MF0090", passage="reserve",
          question="Where were the sixty horse artillery guns? Mark the location.",
          question_zh="那 60 门骑炮在哪里？", answer_zh="Anklappen（图上误刻作 Ауклапенъ）",
          text_evidence="Sixty horse artillery guns were at Anklappen.",
          map_evidence="Hamlet Ауклапенъ (Anklappen, engraved with у for н) north-east of Eylau on the road to Domnau.",
          geometry={"type": "point", "coordinates": [578, 527]},
          geometry_source="assistant_redraw (old MF0090 asked for the French Guard south of Eylau; status was unreadable, no geometry)",
          tag="place_lookup", confidence_draft=3, time=TE + ", night of 7-8 February"),
     dict(event_id="MF0091", replaces="MF0091", passage="davout",
          question="Which village had Bagavout evacuated as Friant approached, so that it was occupied by some companies of the French 48th regiment? Mark the location.",
          question_zh="Friant 逼近时 Bagavout 撤出、随后由法军第 48 团几个连占领的是哪个村子？", answer_zh="Serpallen（图上 Серпаленъ）",
          text_evidence="the heights short of Serpallen, which village Bagavout had evacuated as he approached",
          map_evidence="Village Серпаленъ (Serpallen) south-east of Eylau, with the label Багговутъ (Bagavout) just south-east of it.",
          geometry={"type": "polygon", "coordinates": [[588, 888], [604, 876], [628, 880], [642, 896], [638, 922], [608, 928], [590, 914]]},
          geometry_source="assistant_redraw (old MF0091 marked the Russian troop symbols north-west of the village)",
          tag="place_lookup", confidence_draft=3, time=TE + ", soon after sunrise"),
     dict(event_id="MF0092", replaces="MF0092", passage="night",
          question="On the extreme right of Bennigsen's line, from which village did Markow's 12 cavalry regiments commence? Mark the location.",
          question_zh="Bennigsen 阵线最右端，Markow 的 12 个骑兵团从哪个村子起排开？", answer_zh="Schloditten（图上 Шлодитенъ；不是北面的 Шмодитенъ/Schmoditten）",
          text_evidence="On the extreme right, commencing from Schloditten, Markow commanded 12 cavalry regiments",
          map_evidence="Village Шлодитенъ (Schloditten) north of Eylau on the Koenigsberg road; Шмодитенъ (Schmoditten) lies farther north.",
          geometry={"type": "polygon", "coordinates": [[262, 362], [282, 352], [322, 356], [328, 380], [318, 402], [282, 404], [262, 390]]},
          geometry_source="assistant_redraw (old MF0092 marked Russian troop symbols from the village southwards)",
          tag="place_lookup", confidence_draft=3, time=TE + ", night of 7-8 February"),
    ])

# ---------------------------------------------------------------- Friedland
TF = "1807-06-14"
FRIEDLAND = spec("friedland_1807", "maps/napoleon_maps/friedland_1807.jpg",
    sources=dict(petre=petre("Part V ch. III 'The Battle of Friedland'")),
    passages=dict(
        gallitzin=dict(source="petre", pages="p. 305", drop=HEAD,
            start="It was 6 p.m. on the 13th June when the head of", end="his cavalry at Posthenen.",
            fixes=[("Ptussian", "Prussian")]),
        heinrichsdorf=dict(source="petre", pages="p. 308", drop=HEAD,
            start="Whilst these cavalry combats were in progress,", end="Heinrichsdorf at its eastern entrance.",
            fixes=[("Eussian", "Russian"), ("Kussian", "Russian"), ("Xansouty", "Nansouty")]),
        plain=dict(source="petre", pages="pp. 309-310",
            drop=HEAD + [r"^\* At 9 a\.m\. all the divisions", r"^detached towards Allenburg were sent back",
                         r"^p\. 155\)\.$"],
            start="As his troops arrived, the", end="from Sortlack wood, against the left flank.",
            fixes=[("Eussian", "Russian"), ("artillery.*", "artillery.")]),
    ),
    items=[
     dict(event_id="MF0093", replaces="MF0093", passage="heinrichsdorf",
          question="On which village did Grouchy observe the Russians advancing in force by the road to Koenigsberg? Mark the location.",
          question_zh="Grouchy 发现俄军沿通往柯尼斯堡的道路大举向哪个村子推进？", answer_zh="Heinrichsdorf（图上 Гейнрихсдорфъ）",
          text_evidence="were advancing in force on Heinrichsdorf by the road to Koenigsberg",
          map_evidence="Village Гейнрихсдорфъ (Heinrichsdorf) in the north-west of the plain, on the road from Friedland to Koenigsberg.",
          geometry={"type": "polygon", "coordinates": [[248, 296], [266, 278], [302, 278], [346, 316], [356, 344], [342, 358], [316, 356], [282, 330], [250, 312]]},
          geometry_source="assistant_redraw (old MF0093 marked the Russian cavalry north-east of the village)",
          tag="place_lookup", confidence_draft=4, time=TF + ", early morning"),
     dict(event_id="MF0094", replaces="MF0094", passage="plain",
          question="In which wood were about 3000 picked jagers fighting? Mark the area.",
          question_zh="大约 3000 名精选猎兵在哪片树林里作战？", answer_zh="Sortlack 树林（图上 Сортлакскій лѣсъ）",
          text_evidence="In the Sortlack wood were about 3000 picked jagers",
          map_evidence="The large wood labelled Сортлакскій лѣсъ (Sortlack wood) south-west of Friedland, west of Sortlack village.",
          geometry={"type": "polygon", "coordinates": [[40, 795], [150, 790], [262, 800], [302, 830], [342, 880], [366, 930], [372, 1000], [356, 1055], [40, 1055]]},
          geometry_source="assistant_redraw (old MF0094 marked only French columns in the eastern part of the wood)",
          tag="place_lookup", confidence_draft=3, time=TF + ", about 9 a.m."),
     dict(event_id="MF0095", replaces="MF0095", passage="plain",
          question="Which part of the plain was occupied by the 1st and 2nd divisions, the advanced guard, and part of the cavalry under Kologribow? Mark the area.",
          question_zh="第 1、第 2 师、前卫和 Kologribow 指挥的部分骑兵占据了平原的哪一部分？", answer_zh="较小的南部：从 Millstream（磨坊溪）到 Sortlack",
          text_evidence="the smaller southern portion, from the Millstream to Sortlack, was occupied by the 1st and 2nd divisions, the advanced guard, and part of the cavalry under Kologribow",
          map_evidence="Ground south of the Мюлен Флисъ (Millstream) between the brook, the Alle and Sortlack village, where the Russian lines labelled 'позиція Багратіона' and '1. позиція гвардіи' stand.",
          geometry={"type": "polygon", "coordinates": [[292, 612], [360, 598], [440, 604], [500, 626], [470, 662], [448, 690], [450, 770], [530, 790], [520, 830], [470, 840], [470, 900], [450, 950], [410, 945], [360, 905], [310, 850], [288, 760]]},
          geometry_source="assistant_redraw (old MF0095 asked for the Russian Guard reserve; status was source_conflict, no geometry)",
          tag="place_lookup", confidence_draft=2, time=TF + ", about 9 a.m."),
     dict(event_id="MF0096", replaces="MF0096", passage="gallitzin",
          question="Where did Gallitzin take post with his cavalry after forcing back the French 9th Hussars? Mark the location.",
          question_zh="Gallitzin 把法军第 9 骠骑兵团逼退后，带骑兵驻扎在哪里？", answer_zh="Posthenen（图上 Постененъ）",
          text_evidence="taking post with his cavalry at Posthenen",
          map_evidence="Village Постененъ (Posthenen) west of Friedland on the Eylau road, where the Millstream rises.",
          geometry={"type": "polygon", "coordinates": [[102, 660], [120, 640], [150, 630], [180, 640], [184, 672], [152, 702], [110, 706]]},
          geometry_source="assistant_redraw (old MF0096 marked the French centre around the village)",
          tag="place_lookup", confidence_draft=4, time="1807-06-13, 6 p.m."),
    ])

if __name__ == "__main__":
    write(HEILSBERG, "benchmark/sources/text_first/heilsberg_b_2026-10-21.jsonl")
    write(EYLAU, "benchmark/sources/text_first/eylau_b_2026-10-21.jsonl")
    write(FRIEDLAND, "benchmark/sources/text_first/friedland_b_2026-10-21.jsonl")
