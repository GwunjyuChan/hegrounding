"""First Battle of Zurich, 4 June 1799: text-first items from Archduke Charles, Geschichte des Feldzuges von 1799,
Theil 1 (Wien 1819), pp. 368-370, on maps/napoleon_maps/zurich_first_1799.jpg. The German original is cut from the
BSB OCR by anchors with the OCR fixes listed; the model reads Claude's English translation (review pending).
MF0018-0020 keep their IDs and geometry. MF0017 keeps its ID; its line is redrawn to end at Hirslanden, which the
text names as the second column's objective (the old line ran on to Riesbach)."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import RAW, write, map_record

IMAGE = "maps/napoleon_maps/zurich_first_1799.jpg"
M = map_record(IMAGE)
T = "1799-06-04, the Austrian attack"
FIXES = [
    ("General J Neck gingmit der ersten Colomne", "General Jellachich ging mit der ersten Colonne"),
    ("Esca- drons", "Escadrons"),
    ("neuerdings. und zum drittenmal an die: Mäuern von 22 Zürich", "neuerdings und zum drittenmal an die Mauern von Zürich"),
    ("J eachich nahm", "Jellachich nahm"), ("Riedsbach ,,wo", "Riesbach, wo"), ("GeneralBey", "General Bey"),
    ("herabfal‚len", "herabfallen"), ("stärk besetzt", "stark besetzt"), ("; a die Österreicher", "; die Österreicher"),
    ("Colonne zurück. |", "Colonne zurück."), ("'von Lothringen", "von Lothringen"),
    ("zum ‚Angriff des Zürich -Bergs bestimmt ;'und", "zum Angriff des Zürich-Bergs bestimmt; und"),
    ("führen, a ungangbar", "führen, als ungangbar"),
    ("Gokhausen \"auf den Attysperger - und. Topelhof", "Gokhausen auf den Attysperger- und Topelhof"),
    ("In‚ fanterie", "Infanterie"), ("Öster“reicher", "Österreicher"), ("dem Erreich", "dem Bereich"),
    ("siein Brand", "sie in Brand"), ("da- , her", "daher"), ("Dübendorfübersetzen", "Dübendorf übersetzen"),
    ("Stepbäch", "Stettbach"), ("nahm: es", "nahm es"), ("‚seiner", "seiner"),
    ("Strasse: von Dübendorfnach‘Schwamendingen", "Strasse von Dübendorf nach Schwamendingen"),
    ("Angriff. gegen Schwamendingen fort...", "Angriff gegen Schwamendingen fort."),
    ("bei ‚der Brücke", "bei der Brücke"), ("die-Fortschritte", "die Fortschritte"), ("am: Fuss", "am Fuss"),
    ("auf den | Zürich-Berg", "auf den Zürich-Berg"), ("fruchtlos blieben. Ip", "fruchtlos blieben."),
    ("2a Escadrons", "2[?] Escadrons"), ("beständ", "bestand"), ("Cen'irums", "Centrums"), ("Ähre Richtung", "ihre Richtung"),
    (". Waldung,,", "Waldung,"), ("Schwamendirgen", "Schwamendingen"), ("bogen-förmige", "bogenförmige"),
    ("kümlang", "Rümlang"),
]
TR = "General Jellachich advanced rapidly with the first column of the left wing (5 battalions, 3 squadrons) along the lake road, threw the enemy out of his entrenchments back into Zurich, and occupied the suburbs. The French drew reserves to them and drove the Austrians back; these came up to the walls of Zurich again, for the third time, but could not hold on there. Jellachich therefore took post on the heights of Riesbach, where the French attacked him several times without success until nightfall. The second column under General Bey (4 battalions, 3 squadrons) advanced at the same time from Wittikon on Hirslanden; made itself master of this place and of the entrenchments close by; and tried to follow up its advantage on the slope of the heights that fall away towards Hottingen and Flunteren: but the slopes and ravines beyond were strongly held. Towards midday the enemy advanced here too; the Austrians fell back level with the first column. No more successful was the third column under the Prince of Lothringen (4 battalions, 4 squadrons), which came up from Dübendorf by way of Fällanden and Pfaffhausen, in touch with the second. It was intended for the attack on the Zürich-Berg, and had taken the route named because the footpaths leading from Dübendorf straight towards the hills had been found impassable. The column did push forward, partly through the woods, partly by Göhrins and Gokhausen, as far as the Attysperger and Topel farms: but the further attack on the flank of the enemy position broke down at the abatis, as well as under the murderous fire of the French infantry and its guns, against which the Austrians could set only two cannon dragged up with difficulty. At 2 o'clock in the afternoon Prince Lothringen withdrew out of range of the enemy's fire. The fourth column under the command of Lieutenant Field Marshal Hotze (7 battalions, 12 squadrons) was to cross the Glatt by the bridge between Wallisellen and Schwamendingen: but the enemy had set it on fire, and prevented its repair by the heavy fire of a battery placed at Schwamendingen. The column therefore had to march off to the left, leaving two battalions at the bridge, and cross behind the third at Dübendorf. Hotze advanced on Stettbach; took it after a stubborn resistance; left the greater part of his cavalry on the road from Dübendorf to Schwamendingen, and continued his attack against Schwamendingen. When the two battalions posted at the bridge of Wallisellen saw the progress of the column at the foot of the hill, they threw themselves into the water and broke into Schwamendingen. The French did not withstand such resolution, and withdrew behind their abatis onto the Zürich-Berg, against which, however, all attempts to break through from Schwamendingen remained fruitless because of the thick wood and the steep fall of the hill. The fifth column (10 battalions, 2? squadrons; the second digit is illegible in the scan) consisted of part of the centre under Prince Reuss. It took its direction by Glattbruck on Seebach; made itself master of this place, of the wood in front of it, and then of the village of Orlicken; linked up on its left with the fourth column at Schwamendingen, and took up a curved position with its right wing on Rümlang. The remaining part of the centre (8 battalions, 16 squadrons) was brought forward as a reserve to the place at Opfiken that Prince Reuss had left."
SPEC = dict(
    battle_id="zurich_first_1799", created="2026-10-21", image=IMAGE, img_w=M["img_w"], img_h=M["img_h"],
    map_url=M["map_url"], map_provenance=M["map_provenance"],
    sources=dict(charles=dict(
        file=RAW + "charles1819_1799_t1_10618682bsb_djvu.txt", archive_id="10618682bsb",
        citation="[Erzherzog Carl von Österreich], Geschichte des Feldzuges von 1799 in Deutschland und in der Schweiz, "
                 "Erster Theil (Wien: Anton Strauss, 1819), 'Erste Schlacht bei Zürich am 4. Juni'",
        source_kind="primary_narrative by the Austrian commander-in-chief (published memoir-history)",
        rights_basis="published 1819; author d. 1847")),
    passages=dict(attack=dict(source="charles", pages="pp. 368-370", lang="de",
        start="General J Neck gingmit", end="bei Opfiken vorgezogen.",
        drop=[r"^Aa$", r"^-$", r"^un 370 on w$", r"^rn A$", r"^Be Ei = Ri en\. be:$", r"^een Z71 mm$"],
        fixes=FIXES,
        translation=TR)),
    items=[
     dict(event_id="MF0017", replaces="MF0017", passage="attack",
          question="From which place, and on which place, did the second column under General Bey advance? Mark the route.",
          question_zh="Bey 将军的第二纵队从哪里出发、向哪里推进？", answer_zh="从 Wittikon 向 Hirslanden",
          text_evidence="advanced at the same time from Wittikon on Hirslanden",
          source_evidence="rückte gleichzeitig von Wittikon auf Hirslanden",
          map_evidence="II. Colonne (Graf Bey) dashed line from Wytikon west to Hirslanden.",
          geometry={"type": "line", "coordinates": [[900, 935], [850, 945], [800, 950], [752, 957], [735, 925], [715, 887]]},
          geometry_source="assistant_redraw (old MF0017 line ran on to Riesbach)", tag="route_or_line", confidence_draft=3, time=T),
     dict(event_id="MF0018", replaces="MF0018", passage="attack",
          question="By which route did the third column under the Prince of Lothringen come up? Mark the route.",
          question_zh="Lothringen 亲王的第三纵队走哪条路线前来？", answer_zh="从 Dübendorf 经 Fällanden、Pfaffhausen，再向 Zürich-Berg",
          text_evidence="which came up from Dübendorf by way of Fällanden and Pfaffhausen",
          source_evidence="von Dübendorf über Fällanden und Pfaffhausen",
          map_evidence="III. Colonne (Prinz Lothringen) dashed line from Fällanden past Pfaffhausen towards the Zürichberg.",
          geometry={"type": "line", "coordinates": [[1181, 842], [1147, 858], [1100, 875], [1063, 886], [1027, 866], [981, 835],
                                                    [938, 806], [871, 799], [822, 783], [787, 757]]},
          geometry_source="kept_from_MF0018", tag="route_or_line", confidence_draft=3, time=T),
     dict(event_id="MF0019", replaces="MF0019", passage="attack",
          question="After crossing behind the third column at Dübendorf, along which route did Hotze attack? Mark the route.",
          question_zh="Hotze 在 Dübendorf 跟在第三纵队后面渡河后，沿哪条路线进攻？", answer_zh="先打 Stettbach，再向 Schwamendingen",
          text_evidence="Hotze advanced on Stettbach; took it after a stubborn resistance",
          source_evidence="Hotze rückte auf Stettbach vor",
          map_evidence="IV. Colonne (Hotze) dashed line from Dübendorf through Stettbach towards Schwamendingen.",
          geometry={"type": "line", "coordinates": [[1050, 532], [1016, 555], [988, 573], [930, 582], [869, 597], [839, 575], [806, 538], [754, 506]]},
          geometry_source="kept_from_MF0019", tag="route_or_line", confidence_draft=3, time=T),
     dict(event_id="MF0020", replaces="MF0020", passage="attack",
          question="Which way did the fifth column under Prince Reuss take? Mark the route.",
          question_zh="Reuss 亲王的第五纵队走的是哪条路？", answer_zh="经 Glattbruck 指向 Seebach",
          text_evidence="It took its direction by Glattbruck on Seebach",
          source_evidence="Diese nahm ihre Richtung über Glattbruck auf Seebach",
          map_evidence="V. Colonne (Fürst Reuss) dashed line from Glattbrugg to Seebach.",
          geometry={"type": "line", "coordinates": [[669, 228], [640, 268], [613, 299], [594, 318], [554, 329]]},
          geometry_source="kept_from_MF0020", tag="route_or_line", confidence_draft=4, time=T),
     dict(event_id="MF0125", passage="attack",
          question="Where did Jellachich take post after his column could not hold on at the walls of Zurich? Mark the area.",
          question_zh="Jellachich 的纵队在苏黎世城墙下站不住后，他在哪里扎下阵地？", answer_zh="Riesbach 高地",
          text_evidence="Jellachich therefore took post on the heights of Riesbach",
          source_evidence="Jellachich nahm daher Posten auf den Höhen von Riesbach",
          map_evidence="Riesbach, on the lake shore south-east of the city, where the I. Colonne line ends.",
          geometry={"type": "polygon", "coordinates": [[595, 900], [650, 895], [675, 925], [670, 965], [625, 975], [595, 945]]},
          tag="place_lookup", confidence_draft=3, time=T),
     dict(event_id="MF0126", passage="attack",
          question="Where was the remaining part of the Austrian centre brought forward as a reserve? Mark the location.",
          question_zh="奥军中路剩下的部分作为预备队前移到了哪里？", answer_zh="Opfiken（Reuss 亲王离开的位置）",
          text_evidence="was brought forward as a reserve to the place at Opfiken that Prince Reuss had left",
          source_evidence="als Reserve auf den vom Fürsten Reuss verlassenen Platz bei Opfiken vorgezogen",
          map_evidence="Reserve symbol beside Opfikon, east of Glattbrugg.",
          geometry={"type": "point", "coordinates": [797, 240]}, tag="place_lookup", confidence_draft=4, time=T),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/zurich_first_1799_2026-10-21.jsonl")
