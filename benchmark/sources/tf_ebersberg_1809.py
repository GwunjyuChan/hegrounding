"""Ebersberg (Ebelsberg), 3 May 1809: text-first items from Pelet, tome II (1824), on maps/napoleon_maps/ebersberg_1809.jpg.
The French original is cut from the OCR by anchors with the OCR fixes listed; the model reads Claude's English translation
(review pending). MF0049-0052 keep their IDs; their questions and geometry are replaced (the old map-derived questions
named Austrian brigades that Pelet does not mention). MF0129 is an abstention item: Enns lies off this map."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import write, map_record
from pelet_common import PELET_T2, PELET_DROP

IMAGE = "maps/napoleon_maps/ebersberg_1809.jpg"
M = map_record(IMAGE)
T = "1809-05-03"
TR_ARRIVAL = "Marulaz's light cavalry, which had returned to the 4th corps the day before, pushed the enemy's troops back to near the Traun. We seized the first woods near the river in spite of a lively fusillade. Masséna followed close behind at the head of Claparède's division, which was still under his orders. Soon we were stopped by a very heavy fire; it came from Klein-München and from the houses at the fork of the two roads to Linz and to Wels, in front of the Traun bridge. Hiller had lodged several battalions there, as if he were ready to debouch on this bank. He no doubt hoped in this way to prevent any attempt to cross the lower Traun and, by disputing these houses, to gain the time needed to put the position of Ebersberg in a good state of defence. Arriving on the rise in front of Scharlinz, we saw the enemy army, with forces estimated at 35 or 40,000 men, occupying a most imposing line of heights. To reach them one had to cross the torrential bed of the Traun, six hundred toises wide, cut by several small channels running between sandbanks and small wooded islands; the only way across was a narrow causeway forming a long defile, and a wooden bridge two hundred toises long over the main stream, which is fast and deep at the right bank. All of this was commanded by the artillery of the heights, enfiladed by musketry from the houses, and closed off entirely by the gate of Ebersberg. Beyond it the hills rose steeply, and the village showed itself on their slope like an amphitheatre. The castle, crowning a detached and completely isolated knoll, presenting a great square mass, a sort of fortress, seemed to us to have been put in a state of defence; it commanded and enfiladed the bridge at about a hundred toises. Information carefully gathered assured us that the Traun was not fordable in the neighbourhood, especially in this season of melting snow. Towards the east, the heights border the right bank of the Traun directly for a distance of a thousand toises, and end at the Delta, very extensive and wooded, through which the river flows into the Danube a long league away. Towards the west, the hills draw away from the Traun and follow the left bank of the Gotschalin brook: at a thousand toises' distance, already six hundred toises from the Traun, they continue, drawing further away in the same direction. Their foot is washed by the Krems-Munster. This brook loses itself in the river a little above Ebersberg; for a long league it flows through a small wooded plain cut by channels along the Traun, between the right bank and the Wels road. We could see these heights of Ebersberg, especially the parts nearest the bridge, covered with batteries and strong masses of infantry. We thought we could make out workers digging entrenchments or raising batteries. Further off stood a second row of hills planted with firs, overtopping the first and doubling their strength. The road crossed both in a double ramp, forming a long defile. The castle and the village were full of skirmishers and infantry. We examined this position in all its details; it would have been unassailable for anyone but Frenchmen."
TR_LEGRAND = "In the morning Marshal Bessières had been seen appearing on the Wels road, which runs along the left bank of the Traun, with General Piré's light cavalry brigade. This force was of little use at that moment; infantry was needed to force this position. As soon as Legrand's division had arrived by the Linz road, Masséna had sent across the 26th light infantry regiment and the 18th of the line. General Legrand advanced at their head. As he was debouching from the bridge in close column, a general ran up to him and hastened to give him directions. Legrand, always as cool as he was intrepid in the midst of danger, replied: I am not asking you for advice, but for room for the head of my column. He pushed forward with the brave General Ledru. The first Austrian battalions could not stand against the 26th and the 18th; they abandoned the lower part of the village."
TR_EVENING = "Napoleon, hearing the cannonade of Ebersberg, had sent off in all haste, as soon as he reached Wels, his aide-de-camp General Durosnel with about a thousand horse. This detachment, preceding the Emperor, arrived unhindered by the road along the right bank of the Traun, which forms one continuous defile. General Durosnel at once came into line with our two divisions. The enemy, vigorously attacked, was broken and put to retreat. Hard pressed, he defended himself stubbornly above the last defile and delayed our progress, but at the cost of greatly increasing his losses. Marshal Bessières put himself at the head of Durosnel's cavalry. That of the 4th corps and of Piré's brigade filed through the flames of Ebersberg. Bessières pursued Hiller, who withdrew during the night to Enns, had the bridge burned completely, and set off towards Amstetten."
SPEC = dict(
    battle_id="ebersberg_1809", created="2026-10-21", image=IMAGE, img_w=M["img_w"], img_h=M["img_h"],
    map_url=M["map_url"], map_provenance=M["map_provenance"],
    sources=dict(pelet=PELET_T2),
    passages=dict(
        arrival=dict(source="pelet", pages="pp. 202-205", lang="fr", drop=PELET_DROP,
            start="La cavalerie légère de Marulaz", end="Français.", translation=TR_ARRIVAL,
            fixes=[("4* corps", "4e corps"), ("de la ïraun.", "de la Traun."), ("suivait deprès", "suivait de près"),
                   ("Rlein-Miinchen", "Klein-München"), ("deiix routes", "deux routes"),
                   ("Arri-vés sur le rideau'qui", "Arrivés sur le rideau qui"), ("4o,ooo", "40,000"),
                   ("oia avait", "on avait"), ("rapide et. profond", "rapide et profond"), ("collines,- sur", "collines, sur"),
                   ("rais en état", "mis en état"), ("haute'urs", "hauteurs"), ("de la Traim,", "de la Traun,"),
                   ("suiventla", "suivent la"), ("le diemin de Wels", "le chemin de Wels"), ("de' batteries", "de batteries"),
                   ("sunnontant", "surmontant"), ("exmninâines", "examinâmes")]),
        legrand=dict(source="pelet", pages="pp. 210-211", lang="fr", drop=PELET_DROP,
            start="Dans la matinée, on avait vu paraître", end="partie basse du village.", translation=TR_LEGRAND,
            fixes=[("majéchal", "maréchal"), ("la brigade . de", "la brigade de"), ("il fiillait", "il fallait"),
                   ("Le^and", "Legrand"), ("Lîntz", "Lintz"), ("avait Eût passer le a6^ régiment", "avait fait passer le 26e régiment"),
                   ("le l'S* de ligne, lie général", "le 18e de ligne. Le général"), ("du'pont", "du pont"),
                   ("court àlui", "court à lui"), ("demai^ pas", "demande pas"), ("autnchiens", "autrichiens"),
                   ("le aô\" et le 18''", "le 26e et le 18e")]),
        evening=dict(source="pelet", pages="pp. 213-214", lang="fr", drop=PELET_DROP,
            start="Napoléon entendant la canonnade", end="vers Amstet", translation=TR_EVENING,
            fixes=[("à 'Wels", "à Wels"), ("forme wx défilé", "forme un défilé"), ("be«ucoup", "beaucoup"),
                   ("d» la cavaleiîe", "de la cavalerie"), ("4* corps", "4e corps"), ("poursuivitHiller", "poursuivit Hiller"),
                   ("se re-> tira", "se retira"), ("à Ënns", "à Enns"), ("vers Amstet", "vers Amstetten.")]),
    ),
    items=[
     dict(event_id="MF0049", replaces="MF0049", passage="arrival",
          question="From where did the very heavy fire that stopped Masséna's advance come? Mark the area.",
          question_zh="挡住 Masséna 前进的猛烈火力来自哪里？", answer_zh="Klein-München 村，以及 Traun 桥前 Linz、Wels 两条路岔口的房屋",
          text_evidence="it came from Klein-München and from the houses at the fork of the two roads to Linz and to Wels, in front of the Traun bridge",
          source_evidence="il partait de Klein-München et des maisons qui sont à l'embranchement des deux routes de Lintz et de Wels",
          map_evidence="Klein-München village on the Wels road and the Mühler houses where the Linz road joins it, at the head of the causeway.",
          geometry={"type": "polygon", "coordinates": [[585, 985], [720, 988], [800, 1000], [860, 995], [875, 1045], [800, 1052], [700, 1040], [585, 1030]]},
          geometry_source="assistant_redraw (old MF0049 marked Radetzky's sector south of Klein-München)", tag="place_lookup", confidence_draft=3, time=T + ", morning"),
     dict(event_id="MF0050", replaces="MF0050", passage="arrival",
          question="What was the only way across the bed of the Traun to the heights? Mark it.",
          question_zh="要穿过 Traun 河床到对岸高地，唯一的通路是什么？", answer_zh="一条狭窄的堤道，接一座约两百 toise 长的木桥",
          text_evidence="the only way across was a narrow causeway forming a long defile, and a wooden bridge two hundred toises long over the main stream",
          source_evidence="pour unique chemin, on avait une chaussée étroite formant un long défilé, et un pont en bois de deux cents toises de longueur",
          map_evidence="Road from the Mühler fork south-east across the Traun bed; the hatched bridge reaches Ebersberg.",
          geometry={"type": "line", "coordinates": [[828, 1035], [845, 1072], [900, 1140], [945, 1195]]},
          geometry_source="assistant_redraw (old MF0050 marked the bridge exit in the town)", tag="route_or_line", confidence_draft=3, time=T + ", morning"),
     dict(event_id="MF0051", replaces="MF0051", passage="legrand",
          question="By which road had Legrand's division arrived? Mark the road.",
          question_zh="Legrand 师是沿哪条路到达的？", answer_zh="Linz 大道",
          text_evidence="As soon as Legrand's division had arrived by the Linz road",
          source_evidence="Aussitôt que la division Legrand était arrivée par la route de Lintz",
          map_evidence="Grande Route from the north-west corner (towards Linz) south-east past Klein Strasser and Hans to the fork at the causeway.",
          geometry={"type": "line", "coordinates": [[338, 140], [380, 205], [430, 255], [470, 295], [500, 330], [525, 380], [548, 440], [590, 505], [630, 570], [680, 660], [720, 740], [760, 820], [790, 880], [825, 940], [842, 990], [845, 1035]]},
          geometry_source="assistant_redraw (old MF0051 marked Hoffmeister's sector near Scharlinz)", tag="route_or_line", confidence_draft=2, time=T + ", midday"),
     dict(event_id="MF0052", replaces="MF0052", passage="evening",
          question="By which road did General Durosnel's detachment arrive from Wels? Mark the road.",
          question_zh="Durosnel 将军的骑兵分队从 Wels 沿哪条路赶到？", answer_zh="Traun 河右岸的道路（经 Fischdorf、Strassenhof 到 Ebersberg）",
          text_evidence="arrived unhindered by the road along the right bank of the Traun",
          source_evidence="arriva librement par la route de la rive droite de la Traun",
          map_evidence="Road on the right (south-east) bank from Fischdorf north-east past Strassenhof and Spitmar into Ebersberg.",
          geometry={"type": "line", "coordinates": [[555, 1715], [620, 1660], [690, 1590], [760, 1520], [830, 1470], [880, 1440], [940, 1400], [985, 1350], [1000, 1300]]},
          geometry_source="assistant_redraw (old MF0052 marked Weissenwolf's sector south of the town)", tag="route_or_line", confidence_draft=2, time=T + ", afternoon"),
     dict(event_id="MF0127", passage="arrival",
          question="Which building commanded and enfiladed the bridge at about a hundred toises? Mark its location.",
          question_zh="哪座建筑在约一百 toise 外俯瞰并纵射这座桥？", answer_zh="城堡，位于一座孤立的小丘上",
          text_evidence="The castle, crowning a detached and completely isolated knoll",
          source_evidence="Le château, couronnant un mamelon détaché et entièrement isolé",
          map_evidence="Isolated hachured knoll with a building just east of the bridge end, above the village.",
          geometry={"type": "polygon", "coordinates": [[975, 1185], [1000, 1180], [1020, 1190], [1022, 1215], [1005, 1225], [982, 1215]]},
          tag="place_lookup", confidence_draft=3, time=T + ", morning"),
     dict(event_id="MF0128", passage="legrand",
          question="On which road was Marshal Bessières seen in the morning with General Piré's light cavalry brigade? Mark the road.",
          question_zh="上午 Bessières 元帅带着 Piré 将军的轻骑兵旅出现在哪条路上？", answer_zh="沿 Traun 河左岸的 Wels 大道",
          text_evidence="Marshal Bessières had been seen appearing on the Wels road, which runs along the left bank of the Traun",
          source_evidence="on avait vu paraître sur la route de Wels, qui longe la rive gauche de la Traun",
          map_evidence="Grande Route de Wels à Enns from the west edge (A.G. Piré) east through Klein-München to the fork.",
          geometry={"type": "line", "coordinates": [[40, 1160], [110, 1138], [175, 1113], [250, 1100], [310, 1095], [370, 1100], [420, 1085], [460, 1058], [500, 1012], [600, 1006], [700, 1006], [790, 1012], [840, 1035]]},
          tag="route_or_line", confidence_draft=3, time=T + ", morning"),
     dict(event_id="MF0129", passage="evening",
          question="Where did Hiller withdraw to during the night? Mark the location.",
          question_zh="Hiller 夜里退到了哪里？", answer_zh="Enns（城不在这张图上，图上只在路名里出现 Enns）",
          text_evidence="Bessières pursued Hiller, who withdrew during the night to Enns",
          source_evidence="qui se retira pendant la nuit à Enns",
          map_evidence="Enns town is east of the map edge; only the road label 'Route de Wels à Enns' names it.",
          geometry=None, status="outside_map", tag="place_lookup", confidence_draft=4, time=T + ", night"),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/ebersberg_1809_2026-10-21.jsonl")
