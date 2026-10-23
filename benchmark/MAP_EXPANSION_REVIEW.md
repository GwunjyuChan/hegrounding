# 国家覆盖扩充：逐图与事件审核

更新：2026-09-24。

本轮新增 **22 张参考图、88 条待审核候选**；连同原有 4 图、22 条，共 **26 图、110 条**。原有数据及人工标注未改。

**尚未完成“所有国家至少两图”的要求。** 当前 13 国达到候选数量门槛，其余范围与缺口见 [国家覆盖审核](COUNTRY_COVERAGE.md)。暂按现代国界、欧洲战场、1792–1815 年整理，用户尚未确认口径。

新增 88 条中，**24 条来自外部文字材料，64 条是地图图注或部署符号的人工转述**。后者只是选题与定位候选，不是已找到独立战报的正式推理样本。所有条目均未新增 gold，亦未调用模型。

## 审核门槛

- 图像先于事件筛选；均来自 [Maps 目录](https://www.napoleon-series.org/military-information/maps/)，不使用现代游戏截图。
- 未确认的出版年代不写成战争年份。图上有部署、箭头和答案性标记，全部只作为参考地图。
- 每张至少四条目前仅为候选配额。只有日期、实体、地物、证据、几何都经人工审核后，才算正式事件。
- 不把英文转述当逐字原文；不把地图生成的句子称为独立史料。
- 在现有 Atlas 中另建干净输入图。当前新增图不会自动产生底图、标注或实验结果。
- Marengo 两图共享 `marengo_1800`；布萨科两图共享 `bussaco_1810`。同一战役图版不能拆到训练集和测试集两边。
- 主页标记只代表战場概略位置，不是事件真值坐标。

## 优先审核

先看布萨科雷尼耶图、阿尔武埃拉、奥尔泰兹、图卢兹、别列津纳河的文字材料；再补齐其余图的独立文本。
弗利辛恩的外部文本比较宽泛，只能支持区域；小字的四臂村、海尔斯贝格等图需要额外清晰度审核。
Kulm 的目录写 29 日，但原图明确写 **30 August 1813, 1 p.m.**；本批使用原图时间。
Bergen-op-Zoom 图把佯攻列为 Henry，Bamford 修订文章指出应为 Ottley，已保留冲突，不能据旧图直接定案。

## 瑞士 · 第一次苏黎世战役

- 图组：`zurich_first_1799`；战役分组：`zurich_first_1799`；日期：1799.06.04。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/miscellaneous/zurich1.jpg)；本地：`maps/napoleon_maps/zurich_first_1799.jpg`，1302 × 1302。
- 来源说明：Planscizze der Schlacht bei Zurich vom 4ten Juni 1799; German-language historical plan. Exact printing date unverified.
- 审核备注：Map-derived deployment candidates, not independent narrative evidence. Follow the arrows and named terrain, not the orientation of text. The historical scan has low-contrast areas; reject ambiguous endpoints. All refer to 4 June, not the September battle.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0017 | Bey's lakeside approach | line | 地图推导，需补独立文字 |
| MF0018 | Petrasch's approach from Witikon | line | 地图推导，需补独立文字 |
| MF0019 | Hotze's approach through Duebendorf | line | 地图推导，需补独立文字 |
| MF0020 | Northern approach from Seebach | line | 地图推导，需补独立文字 |

### MF0017

**Text:** Bey's column approached the French defenses from the southeastern lakeside, passing through the Riesbach sector rather than the northern heights.

**Question:** Mark the Riesbach approach sector assigned to Bey's column.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/miscellaneous/zurich1.jpg)；Map attack arrow labelled Colonne Graf B. Bey beside Riesbach.

### MF0018

**Text:** Petrasch's column approached from Witikon toward the eastern defenses above the city; this was separate from Bey's lower lakeside approach.

**Question:** Mark the approach from Witikon toward the eastern defenses.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/miscellaneous/zurich1.jpg)；Map arrow II, Colonne FML Petrasch, Witikon to the city-facing slope.

### MF0019

**Text:** Hotze's column advanced from the Duebendorf side toward the defenses east of Zurich, approaching through the Stettbach sector.

**Question:** Mark Hotze's Stettbach approach sector.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/miscellaneous/zurich1.jpg)；Map arrow IV, Colonne Hotze, Duebendorf and Stettbach.

### MF0020

**Text:** The northern column approached via Seebach toward the French obstacles near Affoltern, away from the lakeside attacks.

**Question:** Mark the Seebach-Affoltern approach shown for the northern column.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/miscellaneous/zurich1.jpg)；Map arrow V, Colonne FML Reuss, between Seebach and Affoltern.

## 意大利 · Marengo · 上午部署

- 图组：`marengo_morning_1800`；战役分组：`marengo_1800`；日期：1800.06.14 · 08–10时。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1800/marengo1.jpg)；本地：`maps/napoleon_maps/marengo_morning_1800.jpg`，1741 × 1217。
- 来源说明：Bataille de Marengo, Ire Planche. Printed caption explicitly describes 8-10 a.m.; exact edition unverified.
- 审核备注：Caption-derived, not independent narrative. Same battle and related plate family as MF0005-MF0008: keep in the same split. Verify Buzana spelling and the extent of 'in front'; do not infer a compass direction from that phrase.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0021 | Hadik's river-anchored wing | line | 地图推导，需补独立文字 |
| MF0022 | Elsnitz north of Castel-Ceriolo | polygon | 地图推导，需补独立文字 |
| MF0023 | Victor's defense at Marengo | polygon | 地图推导，需补独立文字 |
| MF0024 | Guard reserve near Buzana | polygon | 地图推导，需补独立文字 |

### MF0021

**Text:** After emerging from the Bormida bridge, the Austrian army deployed in two lines. Hadik's right rested on the river.

**Question:** Mark the Austrian right-wing deployment anchored on the Bormida.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1800/marengo1.jpg)；Plate I, first paragraph: deployment after crossing the Bormida; Hadik on the right.

### MF0022

**Text:** While Ott's infantry used the main road, Elsnitz's cavalry moved in column north of Castel-Ceriolo.

**Question:** Mark the cavalry sector north of Castel-Ceriolo.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1800/marengo1.jpg)；Plate I, second paragraph: cavalry under Elsnitz north of Castel-Ceriolo.

### MF0023

**Text:** Victor's Chambarlhac and Gardanne divisions held the right side of the Marengo stream and strongly occupied the village.

**Question:** Mark the village defense held by Victor's divisions.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1800/marengo1.jpg)；Plate I, paragraph beginning Les deux divisions Francaises; Marengo village.

### MF0024

**Text:** Bonaparte's Guard remained in reserve in front of the Buzana farm while the front-line divisions defended Marengo.

**Question:** Mark the reserve area in front of the Buzana farm.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1800/marengo1.jpg)；Plate I, paragraph La Garde de Bonaparte est en reserve, en avant de la ferme de la Buzana.

## 葡萄牙 · 布萨科 · 雷尼耶进攻

- 图组：`bussaco_reynier_1810`；战役分组：`bussaco_1810`；日期：1810.09.27。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/peninsula/busaco2.jpg)；本地：`maps/napoleon_maps/bussaco_reynier_1810.jpg`，1166 × 1200。
- 实际显示 [同图版高清扫描](https://www.gutenberg.org/files/55231/55231-h/images/reynier-g.jpg)；原目录图另存 `maps/napoleon_maps/bussaco_reynier_1810_maps_original.jpg`。已目视核对地名、地形及部署，未使用AI重绘。
- 来源说明：Reynier's Attack at Bussaco; plate signed B. V. Darbishire, Oxford 1907. Distinct sector plate, not a crop of Ney's attack.
- 审核备注：Same battle and source family as Ney's map: both share split_group bussaco_1810. Uses the same plate's Gutenberg higher-resolution scan, visually compared with Maps original. Text and map from Oman are not independent. Distinguish sequential attacks and use broad terrain sectors where necessary.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0025 | Pass above Santo Antonio | polygon | 外部文字，待核对 |
| MF0026 | Merle's crest objective | polygon | 外部文字，待核对 |
| MF0027 | Foy's rocky summit | polygon | 外部文字，待核对 |
| MF0028 | Leith's covered approach | line | 外部文字，待核对 |

### MF0025

**Text:** Reynier aimed at the low saddle where the road from Santo Antonio de Cantaro crossed the ridge. Heudelet's leading regiment advanced along this road.

**Question:** Mark the ridge crossing targeted by Heudelet's road attack.

**依据：** [来源](https://www.gutenberg.org/files/55231/55231-h/55231-h.htm#Page_370)；Oman III, pp. 369-371; Reynier's objective and the road attack.

### MF0026

**Text:** Merle's troops climbed diagonally across the front of the 88th toward the unoccupied crest between that regiment and the defenders above the pass.

**Question:** Mark the crest gap targeted by Merle, not his downhill starting area.

**依据：** [来源](https://www.gutenberg.org/files/55231/55231-h/55231-h.htm#Page_371)；Oman III, pp. 371-372; gap between the 88th and the pass defenders.

### MF0027

**Text:** After Merle was repulsed, Foy led the 17th Light uphill toward the first low summit on the French right of the pass.

**Question:** Mark the summit targeted by Foy's subsequent attack.

**依据：** [来源](https://www.gutenberg.org/files/55231/55231-h/55231-h.htm#Page_374)；Oman III, pp. 374-376; Foy's attack and the rocky eminence.

### MF0028

**Text:** Leith shifted his division behind the ridge along a communication road hidden from the French, approaching the pass before reinforcing Picton.

**Question:** Mark the rear communication-road segment used near the pass.

**依据：** [来源](https://www.gutenberg.org/files/55231/55231-h/55231-h.htm#Page_375)；Oman III, p. 375; movement on the road behind the plateau.

## 西班牙 · 阿尔武埃拉 · 初始部署

- 图组：`albuera_1811`；战役分组：`albuera_1811`；日期：1811.05.16。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/peninsula/albuera1.jpg)；本地：`maps/napoleon_maps/albuera_1811.jpg`，783 × 1192。
- 来源说明：Albuera, May 16 1811, 1st Position. Colored deployment plan; exact edition unverified.
- 审核备注：Edited dispatch dated 18 May about the battle on 16 May. Initial deployments must not be confused with later rotated lines; the map includes more than one position. Source testimony still requires cross-checking.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0029 | Stewart's initial sector | polygon | 外部文字，待核对 |
| MF0030 | Hamilton's initial left | polygon | 外部文字，待核对 |
| MF0031 | Blake's original right | polygon | 外部文字，待核对 |
| MF0032 | Alten's village defense | polygon | 外部文字，待核对 |

### MF0029

**Text:** Initially Stewart's division stood between the Valverde and Badajoz roads, with Blake to one side and Hamilton to the other.

**Question:** Mark Stewart's initial deployment sector between the two roads.

**依据：** [来源](https://www.napoleon-series.org/military-info/battles/1811/Albuera/Archives/c_Beresforddispatch.html)；Beresford dispatch, initial disposition paragraph beginning General Blake's corps.

### MF0030

**Text:** Before the flank attack developed, Hamilton's division continued the Allied line beyond the Badajoz road on the left.

**Question:** Mark Hamilton's initial deployment sector beyond the Badajoz road.

**依据：** [来源](https://www.napoleon-series.org/military-info/battles/1811/Albuera/Archives/c_Beresforddispatch.html)；Beresford dispatch, initial disposition; Hamilton closed the left.

### MF0031

**Text:** Blake's troops began in two lines on the Allied right, their left touching the Valverde road beside Stewart.

**Question:** Mark Blake's original deployment sector, before the change of front.

**依据：** [来源](https://www.napoleon-series.org/military-info/battles/1811/Albuera/Archives/c_Beresforddispatch.html)；Beresford dispatch, initial disposition and later order to change front.

### MF0032

**Text:** As the main French attack developed elsewhere, Alten's German light infantry defended the village and its bridge against continued attacks.

**Question:** Mark the village-and-bridge defense assigned to Alten.

**依据：** [来源](https://www.napoleon-series.org/military-info/battles/1811/Albuera/Archives/c_Beresforddispatch.html)；Beresford dispatch, paragraph beginning Though the enemy's principal attack.

## 法国 · 奥尔泰兹战役

- 图组：`orthez_1814`；战役分组：`orthez_1814`；日期：1814.02.27。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/peninsula/orthez.jpg)；本地：`maps/napoleon_maps/orthez_1814.jpg`，1007 × 643。
- 来源说明：Orthez, February 27 1814; colored relief and deployment plan. Exact edition unverified.
- 审核备注：French web transcription of Wellington's dispatch. The map shows first and second positions together; initial reserve and later attacks are distinct. Hill's ford is a sector, not an assumed precise pixel.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0033 | Cole's captured village | polygon | 外部文字，待核对 |
| MF0034 | Hill's crossing | polygon | 外部文字，待核对 |
| MF0035 | French initial left | polygon | 外部文字，待核对 |
| MF0036 | Light Division reserve | polygon | 外部文字，待核对 |

### MF0033

**Text:** Beresford's attack with Cole's division captured Saint-Boes, but narrow ground impeded deployment against the heights beyond.

**Question:** Mark the village captured before the attack stalled on the heights.

**依据：** [来源](https://www.orthez-1814.org/ordres-9.htm)；Wellington dispatch, Beresford emporta le village de Saint-Boes.

### MF0034

**Text:** While other troops attacked the heights, Hill forced a ford upstream of Orthez and moved against the French left.

**Question:** Mark Hill's river-crossing sector upstream of the town, not the town bridge.

**依据：** [来源](https://www.orthez-1814.org/ordres-9.htm)；Wellington dispatch, Hill avait force le passage du gue au-dessus d'Orthez.

### MF0035

**Text:** At dawn the French left occupied the heights above Orthez and the town, opposing Hill's passage of the river.

**Question:** Mark the French left-wing sector facing Hill at the beginning of the battle.

**依据：** [来源](https://www.orthez-1814.org/ordres-9.htm)；Wellington dispatch, dawn position of the French left.

### MF0036

**Text:** Alten's Light Division initially maintained communication between the two attacks and stood in reserve behind them.

**Question:** Mark the initial Light Division reserve between the Allied attacks.

**依据：** [来源](https://www.orthez-1814.org/ordres-9.htm)；Wellington dispatch, Alten gardait la communication et s'etablit en reserve.

## 法国 · 图卢兹战役

- 图组：`toulouse_1814`；战役分组：`toulouse_1814`；日期：1814.04.10。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/peninsula/toulouse.jpg)；本地：`maps/napoleon_maps/toulouse_1814.jpg`，765 × 1136。
- 来源说明：Toulouse, April 10 1814, plate No.16; colored operational plan. Exact edition unverified.
- 审核备注：Modern English translation of Soult's report, not independently verified fact. The report was written 11 April about 10 April. Reference map summarizes several phases; annotate only the requested phase.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0037 | Lapujade defense | polygon | 外部文字，待核对 |
| MF0038 | Contested Augustins fort | polygon | 外部文字，待核对 |
| MF0039 | Minimes defended bridge | polygon | 外部文字，待核对 |
| MF0040 | Reille's fallback perimeter | line | 外部文字，待核对 |

### MF0037

**Text:** As Allied columns advanced, Saint-Pol's brigade defended the small plateau of Lapujade before withdrawing in order.

**Question:** Mark the brigade's defensive plateau before its withdrawal.

**依据：** [来源](https://www.napoleon-series.org/wp-content/uploads/2025/08/Journal-of-the-Sieges-Part-16.pdf)；Soult letter No. 120, 11 April 1814; PDF pp. 12-13, Lapujade paragraph.

### MF0038

**Text:** After Allied troops established themselves on the plateau, the fort of Mas des Augustins changed hands repeatedly.

**Question:** Mark the contested fort, not the whole Calvinet ridge.

**依据：** [来源](https://www.napoleon-series.org/wp-content/uploads/2025/08/Journal-of-the-Sieges-Part-16.pdf)；Soult letter No. 120, PDF p. 13; Mas des Augustins taken and retaken.

### MF0039

**Text:** French forces defended the fortified canal crossing at the Minimes on the Montauban road against an Allied attack.

**Question:** Mark the Minimes crossing and its immediate defensive works.

**依据：** [来源](https://www.napoleon-series.org/wp-content/uploads/2025/08/Journal-of-the-Sieges-Part-16.pdf)；Soult letter No. 120, PDF p. 13; fortified bridges and Minimes.

### MF0040

**Text:** After troops were removed from Saint-Cyprien, Reille abandoned the first line and restricted his defense to the suburb's walls.

**Question:** Mark the defensive perimeter retained after Reille's withdrawal.

**依据：** [来源](https://www.napoleon-series.org/wp-content/uploads/2025/08/Journal-of-the-Sieges-Part-16.pdf)；Soult letter No. 120, PDF p. 14; withdrawal to suburb walls.

## 德国 · 耶拿战役

- 图组：`jena_1806`；战役分组：`jena_1806`；日期：1806.10.14。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1806/jena.jpg)；本地：`maps/napoleon_maps/jena_1806.jpg`，1288 × 1387。
- 来源说明：Schlacht bei Jena am 14ten October 1806; German Renvoi describes successive deployments. Exact edition unverified.
- 审核备注：Map-caption paraphrases only. The lettered legend supplies the temporal distinctions, not an independent report. Several phases overlap; k.k and b.b must not be merged.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0041 | Grawert's night position | polygon | 地图推导，需补独立文字 |
| MF0042 | Ney's arrival at Vierzehnheiligen | polygon | 地图推导，需补独立文字 |
| MF0043 | Prussian light troops at Isserstedt | polygon | 地图推导，需补独立文字 |
| MF0044 | Tauentzien's later line | line | 地图推导，需补独立文字 |

### MF0041

**Text:** Before the morning fighting, Grawert's division spent the night near Klein Romstedt rather than on the forward heights above Jena.

**Question:** Mark Grawert's overnight deployment near Klein Romstedt.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1806/jena.jpg)；German Renvoi a.a and e.e; Grawert's overnight position.

### MF0042

**Text:** Ney's advance guard reached Vierzehnheiligen while the French attack expanded away from the heights above Jena.

**Question:** Mark the village sector reached by Ney's advance guard.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1806/jena.jpg)；German Renvoi f.f; Ney's advance guard at Vierzehnheiligen.

### MF0043

**Text:** Prussian fusiliers and jaegers occupied Isserstedt while other formations fought closer to Vierzehnheiligen.

**Question:** Mark the Isserstedt position of the Prussian light troops.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1806/jena.jpg)；German Renvoi m.m; Prussian fusiliers and jaegers at Isserstedt.

### MF0044

**Text:** Following the earlier forward deployment, Tauentzien's detachment formed a line rather than remaining in its original advance-guard position.

**Question:** Mark Tauentzien's later line labelled k.k, not the earlier b.b position.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1806/jena.jpg)；German Renvoi b.b and k.k; initial advance guard versus later line.

## 德国 · 奥尔施泰特战役

- 图组：`auerstadt_1806`；战役分组：`auerstadt_1806`；日期：1806.10.14。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1806/auerstadt1.jpg)；本地：`maps/napoleon_maps/auerstadt_1806.jpg`，1558 × 1507。
- 来源说明：Plan der Schlacht von Auerstaedt am 14ten October 1806; German lettered deployment plan. Exact edition unverified.
- 审核备注：Provisional map-caption reading. Fine letter keys are small: verify at original resolution before acceptance. Do not assign unit boundaries from nearby place-name centroids; no independent narrative yet.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0045 | Prussian cavalry deployment | polygon | 地图推导，需补独立文字 |
| MF0046 | Schmettau's first position | polygon | 地图推导，需补独立文字 |
| MF0047 | Morand's arrival sector | polygon | 地图推导，需补独立文字 |
| MF0048 | Prussian reserve position | polygon | 地图推导，需补独立文字 |

### MF0045

**Text:** Prussian cavalry deployed on the open ground between Poppel and Hassenhausen, forward of the wider Prussian positions.

**Question:** Mark the cavalry deployment identified by the map's a.a key.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1806/auerstadt1.jpg)；Renvoi a.a, Standpunkt der preussischen Kavallerie; marks west of Hassenhausen.

### MF0046

**Text:** Schmettau's division first formed to the west of Hassenhausen before the later combined Prussian attack.

**Question:** Mark Schmettau's first deployment, not the later attacking line.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1806/auerstadt1.jpg)；Renvoi b.b, Erste Aufstellung der Division Schmettau, contrasted with e.e.

### MF0047

**Text:** Morand's division arrived from the French side of the field south of Hassenhausen, distinct from the northern cavalry sector.

**Question:** Mark the arrival sector indicated for Morand's division.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1806/auerstadt1.jpg)；Renvoi i.i, Ankunft der Division Morand; approach south of Hassenhausen.

### MF0048

**Text:** The Prussian reserve remained farther back near Rehehausen while the forward formations were engaged around Hassenhausen.

**Question:** Mark the reserve deployment near Rehehausen.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1806/auerstadt1.jpg)；Renvoi m.m, reserve deployment symbols near Rehehausen; personal name in key requires review.

## 奥地利 · 埃伯斯贝格 · 上午部署

- 图组：`ebersberg_1809`；战役分组：`ebersberg_1809`；日期：1809.05.03 · 09时。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1809/ebersberg.jpg)；本地：`maps/napoleon_maps/ebersberg_1809.jpg`，1581 × 1930。
- 来源说明：Champ de bataille d'Ebersberg, Carte No.7, situation 3 May about 9 a.m.; historical French-language plan. Exact edition unverified.
- 审核备注：Deployment-only candidates taken from the 9 a.m. map. Do not insert later bridge-storming events into this snapshot. Ebersberg is the historical spelling of Ebelsberg; country uses present-day Austria.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0049 | Radetzky west of the Traun | polygon | 地图推导，需补独立文字 |
| MF0050 | Troops beside the bridge exit | polygon | 地图推导，需补独立文字 |
| MF0051 | Hoffmeister near Scharlinz | polygon | 地图推导，需补独立文字 |
| MF0052 | Weissenwolf south of town | polygon | 地图推导，需补独立文字 |

### MF0049

**Text:** At the mapped morning stage, Radetzky's troops stood near Klein-Muenchen on the approach side of the Traun, away from the main body at Ebersberg.

**Question:** Mark Radetzky's Klein-Muenchen deployment sector.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1809/ebersberg.jpg)；Carte No.7, Radetzky and Gradiska labels southwest of Klein-Muenchen.

### MF0050

**Text:** The Ebersberg-side approach to the Traun bridge was covered by troops positioned around the exit and toward Ufer.

**Question:** Mark the defensive sector at the Ebersberg-side bridge exit.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1809/ebersberg.jpg)；Carte No.7, bridge exit and Vol. Vienne symbols toward Ufer.

### MF0051

**Text:** Hoffmeister's formation stood near Scharlinz, behind the forward Klein-Muenchen sector and on the road approach toward the crossing.

**Question:** Mark Hoffmeister's Scharlinz sector.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1809/ebersberg.jpg)；Carte No.7, Hoffmeister at Scharlinz.

### MF0052

**Text:** Weissenwolf's formation occupied the ground south of Ebersberg, toward the road descending to Fichsdorf.

**Question:** Mark the Weissenwolf deployment south of the town.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1809/ebersberg.jpg)；Carte No.7, Weissenwolf south of Ebersberg.

## 奥地利 · 瓦格拉姆 · 战后夜间部署

- 图组：`wagram_night_1809`；战役分组：`wagram_night_1809`；日期：1809.07.06–07 · 夜间。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1809/wagram.jpg)；本地：`maps/napoleon_maps/wagram_night_1809.jpg`，1740 × 1664。
- 来源说明：Le champ de bataille de Wagram, Carte No.10; night of 6-7 July per map and Maps index. Exact edition unverified.
- 审核备注：Night deployment baseline, not daytime battle actions. Verify partially cropped place names and unit spellings. No independent report has yet been paired with these four map-derived statements.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0053 | Guard near Raschdorf | polygon | 地图推导，需补独立文字 |
| MF0054 | Oudin near Deutsch-Wagram | polygon | 地图推导，需补独立文字 |
| MF0055 | Boudet near Jedlerdorf | polygon | 地图推导，需补独立文字 |
| MF0056 | Friant near Althof | polygon | 地图推导，需补独立文字 |

### MF0053

**Text:** In the mapped night deployment the Guard stood on the wooded ground north of Raschdorf, separate from the formations near Deutsch-Wagram.

**Question:** Mark the Guard sector north of Raschdorf.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1809/wagram.jpg)；Carte No.10, Garde label north of Raschdorf.

### MF0054

**Text:** Oudin's division was posted by Deutsch-Wagram along the Russbach sector, rather than with the Guard near Raschdorf.

**Question:** Mark Oudin's Deutsch-Wagram deployment.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1809/wagram.jpg)；Carte No.10, Oudin label at Deutsch Wagram.

### MF0055

**Text:** Boudet's formation lay near Jedlerdorf, on the western part of the French deployment north of the Danube.

**Question:** Mark Boudet's Jedlerdorf sector.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1809/wagram.jpg)；Carte No.10, Boudet beside Jedlerdorf.

### MF0056

**Text:** Friant's formation lay near Althof, below the Markgrafneusiedl sector in the mapped night situation.

**Question:** Mark Friant's Althof deployment sector.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1809/wagram.jpg)；Carte No.10, Friant label beside Althof in the upper-right sector.

## 比利时 · 滑铁卢 · 开战部署

- 图组：`waterloo_1815`；战役分组：`waterloo_1815`；日期：1815.06.18 · 11:15。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1815/waterloo1.jpg)；本地：`maps/napoleon_maps/waterloo_1815.jpg`，1449 × 880。
- 来源说明：Waterloo June 18 1815, Situation at 11.15 a.m.; colored relief and deployment plan. Exact edition unverified.
- 审核备注：Map-derived initial deployment only, not an independent Waterloo narrative. The map also contains a later 1.30 P.M. notation; it is not used in these candidates.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0057 | Guard reserve at Rossomme | polygon | 地图推导，需补独立文字 |
| MF0058 | Byng above Hougoumont | polygon | 地图推导，需补独立文字 |
| MF0059 | D'Erlon's first line | line | 地图推导，需补独立文字 |
| MF0060 | Kempt north of La Haye Sainte | polygon | 地图推导，需补独立文字 |

### MF0057

**Text:** Before the main attacks, the Imperial Guard formed a reserve near Rossomme behind the French front line.

**Question:** Mark the Guard reserve near Rossomme.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1815/waterloo1.jpg)；Map Imperial Guard symbols beside Rossomme, 11:15 a.m. snapshot.

### MF0058

**Text:** Byng's brigade stood on the slope behind Hougoumont, distinct from the troops inside the enclosed farm and wood.

**Question:** Mark Byng's deployment behind Hougoumont, not the farm itself.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1815/waterloo1.jpg)；Byng label and red deployment northwest of the Hougoumont enclosure.

### MF0059

**Text:** D'Erlon's infantry divisions formed the French first line east of the main road near La Belle Alliance.

**Question:** Mark the first infantry line east of La Belle Alliance.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1815/waterloo1.jpg)；D'Erlon first-line divisional symbols from La Belle Alliance toward Durutte.

### MF0060

**Text:** Kempt's brigade occupied the Allied ridge north of La Haye Sainte near the main road, behind the forward farm position.

**Question:** Mark Kempt's ridge position rather than the farm garrison.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1815/waterloo1.jpg)；Kempt label immediately north of La Haye Sainte, beside the highway.

## 比利时 · 四臂村 · 东侧部署

- 图组：`quatre_bras_east_1815`；战役分组：`quatre_bras_east_1815`；日期：1815.06.16 · 14–14:15。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1815/quatre6.jpg)；本地：`maps/napoleon_maps/quatre_bras_east_1815.jpg`，588 × 766。
- 来源说明：Maps entry: 2nd Netherlands Division east of Quatre Bras, 2-2:15 p.m. Map is a historical colored deployment detail; exact edition unverified.
- 审核备注：Only the east-side detail is provided. Do not infer locations outside its cropped extent. Map-derived candidates require independent battle prose; distinguish successive battery positions. Small unit labels need manual review.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0061 | Dutch light troops by the wood | polygon | 地图推导，需补独立文字 |
| MF0062 | Bijleveld's forward battery | polygon | 地图推导，需补独立文字 |
| MF0063 | French columns at Gemioncourt | polygon | 地图推导，需补独立文字 |
| MF0064 | French advance on Piraumont | polygon | 地图推导，需补独立文字 |

### MF0061

**Text:** The Netherlands light infantry held positions near Bois de la Hutte, east of the crossroads sector, facing the approaching French columns.

**Question:** Mark the light-infantry sector around Bois de la Hutte.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1815/quatre6.jpg)；Blue Ch.27 company symbols around Bois de la Hutte.

### MF0062

**Text:** Bijleveld's forward battery position lay near Gemioncourt; the map also records a later battery position farther back toward the crossroads.

**Question:** Mark the forward battery position near Gemioncourt, not the later position.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1815/quatre6.jpg)；Btt. Bijleveld 1ere pos. versus Btt. Bijleveld 2me posit.

### MF0063

**Text:** French attack columns approached the Gemioncourt farm sector while the Netherlands positions extended toward the wood to its east.

**Question:** Mark the Gemioncourt sector approached by the French columns.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1815/quatre6.jpg)；Red column arrows and Dom. Bachelu labels around Gemioncourt.

### MF0064

**Text:** A separate French advance extended toward Piraumont to the east, away from the main Gemioncourt approach.

**Question:** Mark the Piraumont objective of this eastern advance.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1815/quatre6.jpg)；Red advance arrows toward Piraumont on the right of the map.

## 荷兰 · 弗利辛恩围城

- 图组：`flushing_1809`；战役分组：`flushing_1809`；日期：1809.08。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/walcheren/flushing.gif)；本地：`maps/napoleon_maps/flushing_1809.gif`，1155 × 622。
- 来源说明：Attack of Flushing, between the 3rd and 15th of August 1809, as printed in the plan. Exact edition unverified.
- 审核备注：The map covers 3-15 August; 1 August approach events use unchanged terrain, not a matching dated deployment. Text rarely fixes exact positions; broad sectors only, mark unlocatable if unsupported. The 8 August entry does not identify an individual battery or work.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0065 | Approach on the Middelburg road | line | 外部文字，待核对 |
| MF0066 | Skirmish north of the town | polygon | 外部文字，待核对 |
| MF0067 | Defenders forced back to the walls | line | 外部文字，待核对 |
| MF0068 | Working parties before the fortress | polygon | 外部文字，待核对 |

### MF0065

**Text:** On 1 August Houston's and Rottenburg's men advanced toward Flushing by the Middelburg road and established themselves left of Graham.

**Question:** Mark the road approach toward Flushing described for these troops.

**依据：** [来源](https://www.napoleon-series.org/wp-content/uploads/2022/10/A-Walcheren-Journal.pdf)；A Walcheren Journal, PDF p. 11, 1 August entry.

### MF0066

**Text:** On 5 August the 26th Regiment encountered French pickets just north of Flushing, before the later sortie against Graham.

**Question:** Mark the northern outskirts sector of this skirmish.

**依据：** [来源](https://www.napoleon-series.org/wp-content/uploads/2022/10/A-Walcheren-Journal.pdf)；A Walcheren Journal, PDF p. 13, commentary citing Bond on 5 August.

### MF0067

**Text:** During the advance on 1 August, British troops drove the opposing troops back under Flushing's walls after taking forward batteries.

**Question:** Mark the walled perimeter reached by the retreating defenders.

**依据：** [来源](https://www.napoleon-series.org/wp-content/uploads/2022/10/A-Walcheren-Journal.pdf)；A Walcheren Journal, PDF p. 11, 1 August entry.

### MF0068

**Text:** On 8 August British working parties continued work on trenches and batteries outside the fortress while the defenders fired intermittently from its ramparts.

**Question:** Mark the siege-trench sector shown outside the landward defenses.

**依据：** [来源](https://www.napoleon-series.org/wp-content/uploads/2022/10/A-Walcheren-Journal.pdf)；A Walcheren Journal, PDF p. 14, 8 August entry; map used to suggest sector only.

## 荷兰 · 贝亨奥普佐姆攻城

- 图组：`bergen_op_zoom_1814`；战役分组：`bergen_op_zoom_1814`；日期：1814.03.08–09。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/holland/bergen1.jpg)；本地：`maps/napoleon_maps/bergen_op_zoom_1814.jpg`，1019 × 815。
- 来源说明：Bergen-op-Zoom, March 8 1814, colored assault plan. Exact edition unverified.
- 审核备注：Map-derived routes, not independently validated attack outcomes. The map labels the northern feint Henry; Andrew Bamford's revised article assigns its command to Ottley. Preserve this discrepancy. Do not silently change the raster or claim these are primary-report narratives.
- [补充核对材料](https://www.napoleon-series.org/military-info/battles/1814/c_lowcountries1814.pdf)。

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0069 | Carleton's dike approach | line | 地图推导，需补独立文字 |
| MF0070 | Cooke's southern approach | line | 地图推导，需补独立文字 |
| MF0071 | Morrice's eastern starting sector | polygon | 地图推导，需补独立文字 |
| MF0072 | Northern feint sector | polygon | 地图推导，需补独立文字 |

### MF0069

**Text:** Carleton's assault column approached along the northern polder dike across ground exposed to tidal flooding.

**Question:** Mark the dike approach assigned to Carleton's column.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/holland/bergen1.jpg)；Map red Carleton route on the northern Polder dike.

### MF0070

**Text:** Cooke's force approached the southern defenses beside the entrenched camp, on a different route from the northern dike column.

**Question:** Mark the southern approach beside the entrenched camp.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/holland/bergen1.jpg)；Map Cooke route and Entrenched Camp label.

### MF0071

**Text:** Morrice's route began on the Breda side east of the fortress before circling toward the southern approaches.

**Question:** Mark the initial eastern sector of Morrice's approach, not its southern endpoint.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/holland/bergen1.jpg)；Map Morrice starting symbols on the To Breda road.

### MF0072

**Text:** A separate feint approached the defenses at the Steenbergen gate, apart from the assaults at the harbor and southern camp.

**Question:** Mark the Steenbergen-gate feint sector.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/holland/bergen1.jpg)；Map Henry route to Steenbergen Gate; Bamford PDF pp. 13-14 corrects command to Ottley.

## 捷克 · 兹诺伊莫战役

- 图组：`znaim_1809`；战役分组：`znaim_1809`；日期：1809.07.11。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1809/znaim.jpg)；本地：`maps/napoleon_maps/znaim_1809.jpg`，1924 × 1984。
- 来源说明：Historical French-language Znaim battle plan; Maps date 11 July 1809. Exact edition unverified.
- 审核备注：Map-derived snapshot; do not infer successful crossings or captured towns from mere deployment symbols. Modern Znojmo is in Czechia despite the archive's Austria campaign heading.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0073 | Montbrun near Zuckerhandl | polygon | 地图推导，需补独立文字 |
| MF0074 | Claparede's east-side sector | polygon | 地图推导，需补独立文字 |
| MF0075 | Napoleon's reserve on the Brno road | polygon | 地图推导，需补独立文字 |
| MF0076 | Massena south of the Thaya | polygon | 地图推导，需补独立文字 |

### MF0073

**Text:** Montbrun's cavalry occupied the open ground north of Zuckerhandl, east of the town rather than across the Thaya.

**Question:** Mark Montbrun's cavalry sector north of Zuckerhandl.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1809/znaim.jpg)；Map Montbrun cavalry symbols north of Zuckerhandl.

### MF0074

**Text:** Claparede's troops stood on the town's eastern side near Zuckerhandl, separate from Massena's southern approach.

**Question:** Mark Claparede's sector east of Znaim.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1809/znaim.jpg)；Map Claparede symbols east and southeast of Zuckerhandl.

### MF0075

**Text:** Napoleon and the reserve cavalry and Guard artillery were grouped on the main road from Brno, east of Znaim.

**Question:** Mark the reserve sector on the Brno road.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1809/znaim.jpg)；Map Napoleon, Cav. de la garde, Nansouty and Arrighi beside Grande Route de Brunn.

### MF0076

**Text:** Massena's formations approached from the south toward the river crossing below Znaim, separate from the troops east of the city.

**Question:** Mark the southern approach sector associated with Massena.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1809/znaim.jpg)；Map Massena label and formations south of the Thaya near the Vienna road.

## 捷克 · 库尔姆 · 次日部署

- 图组：`kulm_1813`；战役分组：`kulm_1813`；日期：1813.08.30 · 13时。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1813/kulm1.jpg)；本地：`maps/napoleon_maps/kulm_1813.jpg`，1697 × 1312。
- 来源说明：German plan explicitly states 30 August 1813, about 1 p.m. The Maps link labels kulm1 as 29 August 5 p.m.; the raster caption takes precedence.
- 审核备注：Date conflict: raster 30 August 13:00 versus index 29 August 17:00. These candidates use the raster caption. Map-derived deployments only; exact edition and independent narrative pending.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0077 | Mouton-Duvernet by Kulm | polygon | 地图推导，需补独立文字 |
| MF0078 | Bianchi near Deutsch-Neudorf | polygon | 地图推导，需补独立文字 |
| MF0079 | Kleist's northern approach | polygon | 地图推导，需补独立文字 |
| MF0080 | Allied cavalry near Taurwitz | polygon | 地图推导，需补独立文字 |

### MF0077

**Text:** Mouton-Duvernet's division occupied the western side of Kulm, between the town and the wooded hills.

**Question:** Mark the division's deployment west of Kulm.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1813/kulm1.jpg)；Map Div. Mouton-Duvernet label west of Kulm.

### MF0078

**Text:** Bianchi's division stood southwest of Deutsch-Neudorf and east of the main Kulm road sector.

**Question:** Mark Bianchi's deployment southwest of Deutsch-Neudorf.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1813/kulm1.jpg)；Map Div. Bianchi, two filled formations southwest of Deutsch-Neudorf.

### MF0079

**Text:** Prussian formations stood on the northern road beyond Kulm toward Nollendorf, behind the French town-side deployment.

**Question:** Mark the northern road sector occupied by the Prussian formations.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1813/kulm1.jpg)；Map northern Prussian brigade symbols and Nollendorf road.

### MF0080

**Text:** Allied cavalry occupied the plain northwest of Taurwitz, separate from the infantry around Kulm and Deutsch-Neudorf.

**Question:** Mark the cavalry deployment northwest of Taurwitz.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1813/kulm1.jpg)；Map Garde Kav., 1. Kur. Div., 2. Kur. Div. near Taurwitz.

## 波兰 · 普乌图斯克战役

- 图组：`pultusk_1806`；战役分组：`pultusk_1806`；日期：1806.12.26。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1806/pultusk1.jpg)；本地：`maps/napoleon_maps/pultusk_1806.jpg`，2356 × 1728。
- 来源说明：Plan der Schlacht von Pultusk den 26ten December 1806; German lettered historical plan. Exact edition unverified.
- 审核备注：Caption-derived candidates. The map overlays successive positions and has fold joins; verify each letter key. This is not the retired Wkra map and no earlier Wkra coordinates are transferred.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0081 | Russian infantry's initial lines | polygon | 地图推导，需补独立文字 |
| MF0082 | Barclay's advance guard | polygon | 地图推导，需补独立文字 |
| MF0083 | French artillery emplacement | polygon | 地图推导，需补独立文字 |
| MF0084 | Gudin's reinforcement approach | polygon | 地图推导，需补独立文字 |

### MF0081

**Text:** Russian infantry initially formed in three lines northwest of Pultusk, with the town and river behind the position.

**Question:** Mark the initial infantry formation identified as A.A.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1806/pultusk1.jpg)；German Renvoi A.A, Russian infantry in three lines.

### MF0082

**Text:** Barclay de Tolly's advance guard occupied the wooded Mosino sector ahead of the main Russian position.

**Question:** Mark the advance-guard sector at Mosino.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1806/pultusk1.jpg)；German Renvoi B.B and B-prime; advance guard of Barclay de Tolly, Mosino.

### MF0083

**Text:** French artillery was emplaced between the advancing French formations and the approaches to Pultusk, indicated separately from cavalry.

**Question:** Mark the French artillery emplacement labelled H.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1806/pultusk1.jpg)；German Renvoi H, emplacement of French artillery; H near Gorki approach.

### MF0084

**Text:** A detachment from Gudin's division arrived from the north to reinforce the French left during the attack on Barclay's sector.

**Question:** Mark the northern arrival sector labelled P.P.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1806/pultusk1.jpg)；German Renvoi P.P, arrival of Gudin's division detachment to reinforce the left.

## 波兰 · 海尔斯贝格 · 前卫战

- 图组：`heilsberg_1807`；战役分组：`heilsberg_1807`；日期：1807.06.10。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1807/Heilsberg.jpg)；本地：`maps/napoleon_maps/heilsberg_1807.jpg`，783 × 1140。
- 来源说明：Mikhailovsky-Danilevsky plan of Heilsberg position and advance-guard action, 29 May Old Style / 10 June 1807 New Style; exact scan edition unverified.
- 审核备注：Cyrillic historical labels and small lettering require manual transcription review; these are broad provisional sectors only. Heilsberg is now Lidzbark Warminski in Poland. Do not mistake the Old Style date for 29 May Gregorian.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0085 | Bagration near Reichenberg | polygon | 地图推导，需补独立文字 |
| MF0086 | Soult and Murat forward sector | polygon | 地图推导，需补独立文字 |
| MF0087 | Platov north of Heilsberg | polygon | 地图推导，需补独立文字 |
| MF0088 | Russian fortified town-side line | line | 地图推导，需补独立文字 |

### MF0085

**Text:** Bagration's formation was positioned near Reichenberg south of Heilsberg, separated from the main fortified town sector.

**Question:** Mark Bagration's Reichenberg deployment sector.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1807/Heilsberg.jpg)；Cyrillic map label for Prince Bagration's position near Reichenberg.

### MF0086

**Text:** Soult and Murat's troops occupied the forward approach west of Heilsberg near Bewernick, facing the Russian defenses.

**Question:** Mark the French forward sector around Bewernick.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1807/Heilsberg.jpg)；Cyrillic Soult and Murat labels, Bewernick approach.

### MF0087

**Text:** Platov's troops stood north of Heilsberg near Grossendorf, apart from Bagration's southern position.

**Question:** Mark Platov's northern sector near Grossendorf.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1807/Heilsberg.jpg)；Cyrillic Platov label north of Grossendorf.

### MF0088

**Text:** The Russian fortified line covered the approaches west and northwest of Heilsberg, linking numbered works outside the town.

**Question:** Mark the defensive line along the numbered works west of Heilsberg.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1807/Heilsberg.jpg)；Map works N.1-N.5 and nearby defensive symbols outside Heilsberg.

## 俄罗斯 · 埃劳战役

- 图组：`eylau_1807`；战役分组：`eylau_1807`；日期：1807.02.08。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1807/Eylau2.jpg)；本地：`maps/napoleon_maps/eylau_1807.jpg`，880 × 1252。
- 来源说明：Mikhailovsky-Danilevsky, plan No.14: 27 January Old Style / 8 February 1807 New Style. Historical Russian-language deployment plan.
- 审核备注：Present-day Bagrationovsk, Kaliningrad region, Russia; historical East Prussia. Cyrillic place-name verification is required. Map title says from morning but explicitly includes Davout's noon arrival: do not treat all symbols as simultaneous.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0089 | Davout's southeastern arrival | polygon | 地图推导，需补独立文字 |
| MF0090 | French Guard south of Eylau | polygon | 地图推导，需补独立文字 |
| MF0091 | Russian position at Serpallen | polygon | 地图推导，需补独立文字 |
| MF0092 | Russian northern line | polygon | 地图推导，需补独立文字 |

### MF0089

**Text:** Davout's corps entered the battlefield from the southeast near Mollwitten, separate from the French troops already at Eylau.

**Question:** Mark the arrival sector near Mollwitten, not the later positions near the town.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1807/Eylau2.jpg)；Cyrillic map label Davout corps arriving at noon; Mollwitten sector.

### MF0090

**Text:** The French Guard was posted south of Eylau behind the forward troops facing the Russian line.

**Question:** Mark the Guard deployment south of Eylau.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1807/Eylau2.jpg)；Cyrillic Guard label and purple formations immediately south of the town.

### MF0091

**Text:** Russian troops held the southeastern sector around Serpallen, facing the approach from the south.

**Question:** Mark the Russian Serpallen sector.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1807/Eylau2.jpg)；Green formations and Cyrillic Serpallen label southeast of Eylau.

### MF0092

**Text:** The Russian line extended toward Schloditten north of Eylau, distinct from the southern troops near Serpallen.

**Question:** Mark the northern Russian deployment near Schloditten.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1807/Eylau2.jpg)；Green northern formations and Cyrillic Schloditten label.

## 俄罗斯 · 弗里德兰 · 白天部署

- 图组：`friedland_1807`；战役分组：`friedland_1807`；日期：1807.06.14 · 白天至17时。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1807/Friedland1.jpg)；本地：`maps/napoleon_maps/friedland_1807.jpg`，783 × 1138。
- 来源说明：Mikhailovsky-Danilevsky, plan No.21: 2 June Old Style / 14 June 1807 New Style, morning to 5 p.m. Historical Russian-language plan.
- 审核备注：Present-day Pravdinsk, Kaliningrad region, Russia; historical East Prussia. Only the morning-to-5-p.m. phase, not Ney's later attack. Cyrillic aliases and bank identity require review; these are map-derived deployments.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0093 | Russian cavalry near Heinrichsdorf | polygon | 地图推导，需补独立文字 |
| MF0094 | French troops in Sortlack wood | polygon | 地图推导，需补独立文字 |
| MF0095 | Russian Guard reserve | polygon | 地图推导，需补独立文字 |
| MF0096 | French center at Posthenen | polygon | 地图推导，需补独立文字 |

### MF0093

**Text:** Russian cavalry confronted the French in the Heinrichsdorf sector north of the main infantry struggle near Friedland.

**Question:** Mark the Russian cavalry sector facing Heinrichsdorf.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1807/Friedland1.jpg)；Map cavalry symbols east of Heinrichsdorf and north of Friedland.

### MF0094

**Text:** French troops held positions in the Sortlack woodland south of Posthenen, facing the Russian left beside the river bend.

**Question:** Mark the French woodland sector, not the village of Sortlack.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1807/Friedland1.jpg)；Cyrillic Sortlack wood label and French formations in its western portion.

### MF0095

**Text:** The Russian Guard reserve stood in the rear of the southern infantry deployment, west of the Alle's bend and south of Friedland.

**Question:** Mark the Guard reserve sector behind the southern Russian line.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1807/Friedland1.jpg)；Cyrillic Guard Corps label south of Friedland on the left bank.

### MF0096

**Text:** The French center occupied the Posthenen approach west of Friedland, between the northern cavalry fighting and Sortlack wood.

**Question:** Mark the French center around Posthenen.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1807/Friedland1.jpg)；Cyrillic Lannes and Posthenen labels; central French formations.

## 白俄罗斯 · 第一次波洛茨克 · 次日

- 图组：`polotsk_first_1812`；战役分组：`polotsk_first_1812`；日期：1812.08.18。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1812/Sabron/Sabron2b.jpg)；本地：`maps/napoleon_maps/polotsk_first_1812.jpg`，2048 × 1240。
- 来源说明：Sabron collection in Maps, Polotsk 18 Augustus 1812; Dutch legend. Exact edition unverified.
- 审核备注：Present-day Belarus, not Russia. Dutch letter keys mix unit identity and later dispositions N/O/P. Do not confuse those 5 p.m. positions with initial lines. Independent narrative remains to be paired.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0097 | Russian first line by Prismenitz | line | 地图推导，需补独立文字 |
| MF0098 | Wrede's division east of the road | polygon | 地图推导，需补独立文字 |
| MF0099 | Castex's cavalry by the Dvina | polygon | 地图推导，需补独立文字 |
| MF0100 | Corbineau east of the tributary | polygon | 地图推导，需补独立文字 |

### MF0097

**Text:** The Russian first line faced the French around Prismenitz, ahead of a separate supporting line nearer the woods.

**Question:** Mark the first Russian line labelled A, not the supporting line B.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1812/Sabron/Sabron2b.jpg)；Dutch legend A Voorste Linie der Russen; B second line.

### MF0098

**Text:** Wrede's division stood east of the Saint Petersburg road near the northern stream-side settlements.

**Question:** Mark Wrede's division in the northern French front, identified by D.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1812/Sabron/Sabron2b.jpg)；Dutch legend D Divisie Wrede; D formations near the northern settlement.

### MF0099

**Text:** Castex's cavalry brigade waited west of Polotsk near the Dvina, away from the northern infantry formations.

**Question:** Mark Castex's river-side deployment labelled K.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1812/Sabron/Sabron2b.jpg)；Dutch legend K Cav. Brigade Castex; K near Dvina west of the city.

### MF0100

**Text:** Corbineau's cavalry was positioned east of the tributary beyond the town's northern edge, opposite the infantry on the other side.

**Question:** Mark Corbineau's cavalry sector labelled M.

**依据：** [来源](https://www.napoleon-series.org/images/military/maps/1812/Sabron/Sabron2b.jpg)；Dutch legend M Cav. Brigade Corbineau; M east of Polota tributary.

## 白俄罗斯 · 别列津纳河渡河

- 图组：`berezina_1812`；战役分组：`berezina_1812`；日期：1812.11.24–29。
- [Maps 原图](https://www.napoleon-series.org/images/military/maps/1812/Sabron/Sabron4b.jpg)；本地：`maps/napoleon_maps/berezina_1812.jpg`，1053 × 2048。
- 来源说明：Sabron collection in Maps; Dutch title Kaart voor de Gevechten aan de Berezina. Map index covers 26-29 November; exact edition unverified.
- 审核备注：Modern translation of a historical campaign account, not a verified primary report. Map includes the wider battle phase; 24-25 November diversions are localized by terrain rather than dated unit symbols. Wesselowo and Studianka must remain distinct. Map spelling Stakow/Borissow differs from the prose.

| ID | 目标 | 几何 | 证据层级 |
|---|---|---|---|
| MF0101 | Chosen crossing at Studianka | polygon | 外部文字，待核对 |
| MF0102 | Diversion at Stakhov | polygon | 外部文字，待核对 |
| MF0103 | Concentration at Borisov | polygon | 外部文字，待核对 |
| MF0104 | Artillery above Studianka | polygon | 外部文字，待核对 |

### MF0101

**Text:** Although other crossings were considered, Oudinot selected the ford opposite Studianka and ordered preparations there.

**Question:** Mark the selected crossing opposite Studianka, not Wesselowo.

**依据：** [来源](https://www.napoleon-series.org/military-information/battles-and-campaigns/histoire-de-la-campagne-de-russie/attachment/history-of-the-campaign-of-russia-part-68/)；Part 68, PDF pp. 2-3, reconnaissance and selection of Studianka.

### MF0102

**Text:** While the real bridge preparations continued at Studianka, Oudinot increased demonstrations at Stakhov and other crossings to distract the Russians.

**Question:** Mark the Stakhov demonstration sector rather than the actual bridge site.

**依据：** [来源](https://www.napoleon-series.org/military-information/battles-and-campaigns/histoire-de-la-campagne-de-russie/attachment/history-of-the-campaign-of-russia-part-68/)；Part 68, PDF p. 3, demonstrations at Stakhov, Borisov and Ukholody.

### MF0103

**Text:** To conceal the intended crossing, Napoleon concentrated troops at Borisov while work proceeded farther upstream.

**Question:** Mark the Borisov concentration area used for the diversion.

**依据：** [来源](https://www.napoleon-series.org/military-information/battles-and-campaigns/histoire-de-la-campagne-de-russie/attachment/history-of-the-campaign-of-russia-part-68/)；Part 68, PDF p. 4, concentration on 24-25 November.

### MF0104

**Text:** When bridge building began, French artillery occupied the crest above Studianka to cover troops crossing to the opposite bank.

**Question:** Mark the artillery's hill sector above Studianka, not the opposite bank.

**依据：** [来源](https://www.napoleon-series.org/military-information/battles-and-campaigns/histoire-de-la-campagne-de-russie/attachment/history-of-the-campaign-of-russia-part-68/)；Part 68, PDF p. 6, morning of 26 November and covering artillery.
