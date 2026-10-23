"""Znaim, 11 July 1809: text-first items from Pelet, tome IV (1826), pp. 266-273, on maps/napoleon_maps/znaim_1809.jpg.
French original cut from the OCR with the fixes listed; the model reads Claude's English translation (review pending).
MF0073-0075 keep their IDs; questions and geometry replaced (the old questions named French formations that Pelet does
not place). MF0137 is an abstention item: Erdberg lies off this map."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import write, map_record
from pelet_common import PELET_T4, PELET_DROP

IMAGE = "maps/napoleon_maps/znaim_1809.jpg"
M = map_record(IMAGE)
T = "1809-07-11"
TR_GROUND = "Masséna arrived there at ten in the morning with Legrand's division. Znaim, surrounded by walls, resting on the west on the steep rocks of the Taja and on the east on the slopes of the Lischen, dominates its surroundings. The ground falls away on every side down to the bridge of Schallersdorf, where the river bends at a right angle towards Tesswitz, which lies at the mouth of the Lischen. These waters surround the hill of Znaim and make of it a kind of entrenched position, 1800 toises wide on the south and of equal depth. On the left bank of the Lischen lies the plateau of Tesswitz; beyond a small valley, that of Zuckerhandl; these rounded hills join up towards Brenditz. The second has steeper slopes and forms, towards its southern end, a commanding summit 700 toises from Tesswitz and from Zuckerhandl. On this summit was Marmont's first position and the site of the Emperor's tents. Brenditz was Charles's headquarters; holding from there the knot of spurs, he was still master of the roads to Budwitz and to Brünn. The enemy had lined the wooded banks of the Taja with infantry and barricaded the bridge. He had worked during the night; four epaulements covered his artillery on the rise of Klosterbruck, which was strongly held, as was a magazine."
TR_ATTACK = "The 4th corps was received with a lively fusillade and with the fire of the batteries. This amphitheatre of ground was soon reconnoitred, despite the trees that hid it. Masséna cannonaded the bridge to drive off the workers and the artillery. The first guns and the battalions supporting them fell back a little. But the covered batteries went on firing, and from the wood came a fusillade that stopped everything. This position, well supported by the valley of the Taja, was completely enfiladed by the ground beyond it. Some guns, brought to the left on the bend of the river, took in flank the opposite bank, the bridge and the enemy, who was forced to withdraw. While the bridge was being cleared, the voltigeurs and the light cavalry crossed at various fords; the infantry soon followed in column. The plateaux of Tesswitz and Zuckerhandl could be seen covered with troops. At that moment the cannon could be heard rumbling along the two opposing lines; it stayed stationary for a long time. Soon Legrand attacked and debouched from the bridge with the French brigade; he threw the 26th regiment to the right, which, climbing the rise of Alt-Schallersdorf, seized the magazine and the works. The 18th carried Klosterbruck, which was full of infantry."
TR_AFTERNOON = "At the same moment Saint-Cyr arrived and crossed to the other bank of the Taja to support Legrand. The heights were reoccupied; our line established itself under the walls of Znaim. The battery that was on the left advanced to beyond Edelspitz [the scan reads 'Edbpiz']. It took the enemy's guns and troops in flank; it did so much damage that the Prince of Reuss was about to oppose it with a triple battery. Against the position of Znaim, this is the best means of attack. The progress of the Austrians had not escaped Napoleon. They threatened the centre of the line of fire that had been established from the bend of the Taja to above Gukrowitz. The Emperor then ordered Marmont to debouch from Tesswitz. Marmont, crossing the bridge of the Lischen, climbed the height under a very deadly fire."
TR_EVENING = "However much speed Davout and Oudinot had made, the heads of their columns were, on the 11th at seven in the evening, only at Erdberg, where Gudin's division was arriving. The 3rd corps, which had been heading for the bridge of Wisternitz, was coming back by forced marches. Oudinot's corps, crossing the Taja below Joslowitz, was to be assembled at nine in the evening and to move off an hour before daybreak; its headquarters was also at Erdberg."
SPEC = dict(
    battle_id="znaim_1809", created="2026-10-21", image=IMAGE, img_w=M["img_w"], img_h=M["img_h"],
    map_url=M["map_url"], map_provenance=M["map_provenance"],
    sources=dict(pelet=PELET_T4),
    passages=dict(
        ground=dict(source="pelet", pages="pp. 266-267", lang="fr", drop=PELET_DROP,
            start="Masséna y arriva à dix heures", end="qu'un magasin.", translation=TR_GROUND,
            fixes=[("recoui4>e", "recourbe"), ("Ges eaux", "Ces eaux"), ("la Taja ,,", "la Taja,"), ("KIosterbrudt", "Klosterbruck")]),
        attack=dict(source="pelet", pages="pp. 267-268", lang="fr", drop=PELET_DROP,
            start="Le 4\" corps fut reçu", end="rempli d'in&n", translation=TR_ATTACK,
            fixes=[("Le 4\" corps", "Le 4e corps"), ("fet bientôt", "fut bientôt"), ("Tartillerie", "l'artillerie"),
                   (")es bataillons", "les bataillons"), ("uns fusillade", "une fusillade"), ("se troure", "se trouve"),
                   ("qai fut", "qui fut"), ("deiix lignes", "deux lignes"), ("long -temps", "long-temps"), ("Liegrand", "Legrand"),
                   ("le 36* régiment", "le 26e régiment"), ("AltSchallersdorf", "Alt-Schallersdorf"),
                   ("Le i8* enlève Kiosterbruck rempli d'in&n", "Le 18e enlève Klosterbruck rempli d'infanterie.")]),
        afternoon=dict(source="pelet", pages="pp. 271-272", lang="fr", drop=PELET_DROP,
            start="Dans le même moment, arrivait Saint", end="hauteur sous un feu très-meurtrier.", translation=TR_AFTERNOON,
            fixes=[("SaintCyr", "Saint-Cyr"), ("La battre quiétaità la gauche", "La batterie qui était à la gauche"),
                   ("d'Edbpiz", "d'Edelspitz [OCR : Edbpiz]"), ("l'enaenit", "l'ennemi"), ("prince de Beuss", "prince de Reuss"),
                   ("contre la portion de Znaïm", "contre la position de Znaïm"), ("delaTaja", "de la Taja"),
                   ("Marmontde", "Marmont de")]),
        evening=dict(source="pelet", pages="p. 273", lang="fr", drop=PELET_DROP,
            start="Quelque diligence", end="aussi à Erdberg.", translation=TR_EVENING,
            fixes=[("Oudioot", "Oudinot"), ("le 1 1,", "le 11,"), ("3« corps", "3e corps"), ("d'Oudinot^", "d'Oudinot")]),
    ),
    items=[
     dict(event_id="MF0073", replaces="MF0073", passage="ground",
          question="Where was the Archduke Charles's headquarters? Mark the location.",
          question_zh="卡尔大公的司令部设在哪里？", answer_zh="Brenditz",
          text_evidence="Brenditz was Charles's headquarters",
          source_evidence="Brenditz était le quartier-général de Charles",
          map_evidence="Brenditz village north-west of Znaim on the road to Budwitz.",
          geometry={"type": "polygon", "coordinates": [[230, 610], [270, 612], [300, 640], [305, 690], [280, 705], [245, 690], [228, 650]]},
          geometry_source="assistant_redraw (old MF0073 marked Montbrun's cavalry north of Zuckerhandl)", tag="place_lookup", confidence_draft=4, time=T),
     dict(event_id="MF0074", replaces="MF0074", passage="attack",
          question="Which place, full of infantry, did the 18th regiment carry? Mark the location.",
          question_zh="第 18 团攻下了哪个满是步兵的地方？", answer_zh="Klosterbruck（修道院）",
          text_evidence="The 18th carried Klosterbruck, which was full of infantry.",
          source_evidence="Le 18e enlève Klosterbruck rempli d'infanterie.",
          map_evidence="Kloster Bruck monastery on the Taja south of Znaim.",
          geometry={"type": "point", "coordinates": [548, 1493]},
          geometry_source="assistant_redraw (old MF0074 marked Claparède's sector east of Znaim)", tag="place_lookup", confidence_draft=4, time=T + ", late morning"),
     dict(event_id="MF0075", replaces="MF0075", passage="afternoon",
          question="From which place did the Emperor order Marmont to debouch? Mark the location.",
          question_zh="皇帝命令 Marmont 从哪里出击？", answer_zh="Tesswitz（地图作 Kl. Tesswitz）",
          text_evidence="The Emperor then ordered Marmont to debouch from Tesswitz.",
          source_evidence="L'Empereur ordonna alors à Marmont de déboucher de Tesswitz.",
          map_evidence="Kl. Tesswitz village on the Taja east of Znaim, at the mouth of the side valley.",
          geometry={"type": "point", "coordinates": [875, 1335]},
          geometry_source="assistant_redraw (old MF0075 marked the reserve column on the Brünn road)", tag="place_lookup", confidence_draft=2, time=T + ", afternoon"),
     dict(event_id="MF0135", passage="ground",
          question="Down to which bridge does the ground fall away on every side from Znaim? Mark the bridge.",
          question_zh="Znaim 四周的地势一直向下倾斜到哪座桥？", answer_zh="Schallersdorf 桥（河在这里拐成直角）",
          text_evidence="The ground falls away on every side down to the bridge of Schallersdorf",
          source_evidence="Le terrain descend de tous côtés jusqu'au pont de Schallersdorf",
          map_evidence="Road bridge over the Taja between Alt-Schallersdorf and Oblass.",
          geometry={"type": "point", "coordinates": [680, 1592]}, tag="place_lookup", confidence_draft=3, time=T),
     dict(event_id="MF0136", passage="afternoon",
          question="Beyond which village did the battery on the left advance? Mark the location.",
          question_zh="左翼的炮兵连推进到了哪个村子以外？", answer_zh="Edelspitz（扫描作 Edbpiz）",
          text_evidence="The battery that was on the left advanced to beyond Edelspitz",
          source_evidence="La batterie qui était à la gauche s'avança jusqu'au-delà d'Edelspitz",
          map_evidence="Edelspitz village on the west bank of the Taja south-west of Kloster Bruck.",
          geometry={"type": "point", "coordinates": [515, 1600]}, tag="place_lookup", confidence_draft=3, time=T + ", afternoon"),
     dict(event_id="MF0137", passage="evening",
          question="Where were the heads of Davout's and Oudinot's columns at seven in the evening on the 11th? Mark the location.",
          question_zh="11 日晚七点，Davout 和 Oudinot 的纵队前锋到了哪里？", answer_zh="Erdberg（不在这张图上）",
          text_evidence="were, on the 11th at seven in the evening, only at Erdberg",
          source_evidence="qu'à Erdberg où arrivait la division Gudin",
          map_evidence="Erdberg lies south of the map edge.",
          geometry=None, status="outside_map", tag="place_lookup", confidence_draft=4, time=T + ", 7 p.m."),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/znaim_1809_2026-10-21.jsonl")
