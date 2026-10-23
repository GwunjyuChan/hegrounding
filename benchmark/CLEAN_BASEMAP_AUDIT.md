# 26张参考地图的干净历史底图检索

检索日期：2026-09-24。对象：当前26张参考图、110条候选事件。

## 结论与边界

**有可用方向，也找到了一批具体历史图件，但尚未为26张图全部准备好可标注的底图。** 本文件是来源与适配性初筛，不是验收清单。没有修改事件、人工标注、底图版本或实验结果，也没有把候选自动接入模型。

“干净”指没有事件答案性覆盖物，不是没有地名。应保留河流、道路、村镇、地形、城墙等定位信息；排除部队名称与阵列、攻防箭头、战役阶段编号、战役专用图例，以及明显指向答案的后世纪念标记。军事机构测绘的地形图不等于作战部署图。

历史地图也不一定描绘已存在的地物：城市规划图可能画的是拟建道路；工程图可能画的是计划工事。图上有形状不代表战役当时已存在。

本次核验深度不同，明确分为：

- **已有**：项目已有该历史底图来源；当前裁切是否覆盖新增事件仍需检查。
- **具体图件**：已定位到馆藏或数字化图件，尚未逐事件验收。只有特别注明的项目做了视觉初筛。
- **系列候选**：已确认地图系列和检索入口，尚未核定战区对应图幅、像素与完整覆盖。
- **暂缓**：年代、比例尺、范围或获取问题明显，目前不能推荐为正式底图。

“未找到”仅表示本轮未找到合格资料，不表示该图不存在。表内风险和优先级是结合本项目事件要求的判断，而不是来源机构的适用性认证。

## 逐图对应

同一历史地形图可以为不同参考图提供裁切，不需要为了参考图数量强行找不同出版物。参考图、输入图和事件之间的关系必须保留；共享同一底图或战役的样本不能随意拆分到训练集和测试集。

| # | 当前参考图 / battle_id | 干净底图候选 | 状态与主要检查项 |
|---|---|---|---|
| 1 | 第一次苏黎世 `zurich_first_1799` | [Usteri 苏黎世州图，1816][zurich] | 已有来源。另取东侧、东北侧范围，包含 Riesbach、Witikon、Stettbach、Seebach、Affoltern；不能直接复用第二次战役的现有裁切并假定全覆盖。 |
| 2 | 第二次苏黎世 `zurich_second_1799` | [Usteri，1816][zurich] | 已有。继续保留原有版本与标注；晚于1799年17年，河道、道路、聚落逐项核对。 |
| 3 | Marengo 战后 `marengo_1800` | [Alessandria，第55/LV幅，1852/1853等版本][alessandria]；[IGM 第13幅，1831系列][sardinia1831] | 具体馆藏线索，暂缓采用。需要获取实际图幅；较晚，须核验 Bormida、Marengo溪、桥和农庄。不能把1852系列名当所有单幅的出版年份。 |
| 4 | Marengo 上午 `marengo_morning_1800` | 同上 | 同一底图可关联两张参考图；重点覆盖 Castel Ceriolo、Marengo、Buzana。当前没有确认四条目标均可辨认。 |
| 5 | 布萨科内伊 `bussaco_1810` | [葡萄牙 DGT 古地图馆藏][portugal]，寻找 Luso / Buçaco / Mealhada 图幅 | 暂缓。本轮未核定足够精细、年代接近的干净图。不能拿已有作战图改灰度充当干净底图。 |
| 6 | 布萨科雷尼耶 `bussaco_reynier_1810` | 同上 | 暂缓。必须能分辨 Santo Antonio、山口、山脊与背坡道路。全国或省级概览图不够。 |
| 7 | 圣塞巴斯蒂安 `san_sebastian_1813` | [Tofiño / Ballester 港城图，1788，出版1789，约1:4,800][sanseb] | 具体图件，优先。已查看网页缩略图并核对官方描述及下载入口；尚未进行全分辨率逐处泄漏检查。原图南向上，需要统一朝向。 |
| 8 | 阿尔武埃拉 `albuera_1811` | [IGN MTN50第802幅 La Albuera，1938，1:50,000][albuera] | 暂缓，过晚127年。只能作为另一个“后世地形图”条件；不能当1811年前后的历史环境真值。 |
| 9 | 奥尔泰兹 `orthez_1814` | [Cassini 第107幅 Aire–Orthez，1771，1:86,400][orthez] | 具体图件。适合先核对聚落、主路和河流；Saint-Boès、渡口、山坡的细节是否足够仍待查看裁切。 |
| 10 | 图卢兹 `toulouse_1814` | [Grandvoinet / Pommian 城市、郊区及周边图，1808][toulouse-image]；[市档案馆古图入口][toulouse] | 具体图件，优先。图像记录为7799×7247；需核对 Lapujade、Minimes、Saint-Cyprien及Augustins目标工事。战时新建工事可能不存在于1808图。 |
| 11 | 耶拿 `jena_1806` | [Güssefeld 周边地形图，1800，约1:35,000][jena] | 具体图件，已打开馆藏原图查看。所见扫描有明显折损/遮挡；存在其他扫描入口，需检查较好版本及北部战场覆盖，暂不验收。 |
| 12 | 奥尔施泰特 `auerstadt_1806` | [图林根历史地形图下载，1852–1880][thuringia] | 系列候选，较晚。需要 Hassenhausen、Rehehausen 等地的具体图幅。[1911百科中的地形图][auerstadt-late]仅作后备，不能标成1806年测绘。 |
| 13 | 埃伯斯贝格 `ebersberg_1809` | [上奥地利第一次测绘，1775–1777][upper-austria] | 系列候选。覆盖方向为 Linz–Ebelsberg–Traun；需要核验桥位、两岸道路及村庄。完整访问/原始扫描受平台条件限制。 |
| 14 | 瓦格拉姆夜间 `wagram_night_1809` | [下奥地利第一次测绘，1773–1781][lower-austria] | 系列候选。需包含 Deutsch-Wagram、Raschdorf、Jedlerdorf、Althof；多瑙河河道与后世整治差异须核验。不是只截 Wagram 镇。 |
| 15 | 滑铁卢 `waterloo_1815` | [Ferraris，1770–1778][ferraris] | 系列候选，优先裁切。核对 Hougoumont、La Haye Sainte、Rossomme；战前图能避免后世战场纪念设施。仍需确定实际图幅和边缘覆盖。 |
| 16 | 四臂村东侧 `quatre_bras_east_1815` | [Ferraris，1770–1778][ferraris] | 系列候选，优先裁切。必须包含路口、Gemioncourt、Piraumont、Bois de la Hutte，不能只截路口中心。 |
| 17 | 弗利辛恩 `flushing_1809` | [Hattinga，1750，Vlissingen城图扫描][vlissingen] | 具体图件。扫描记录5847×4561；城市图未必覆盖北侧行军、营地及壕沟，需要周边 Walcheren 图补足，不能用城市图宣布四条全可标。 |
| 18 | 贝亨奥普佐姆 `bergen_op_zoom_1814` | [乌得勒支大学馆藏城防图，1755][bergen] | 具体图件。需核验1814城门与城墙变化、城外营地是否在图内；原图字母数字不等于部队，但必须解释。避免换成带1747围城进攻线的图。 |
| 19 | 兹诺伊莫 `znaim_1809` | [摩拉维亚第一次测绘，1764–1768][moravia] | 系列候选。核对 Znaim/Znojmo、Zuckerhandl、Thaya/Dyje和布尔诺道路；城市地籍图只能作为局部补充。 |
| 20 | 库尔姆 `kulm_1813` | [波希米亚第一次测绘，1764–1767][bohemia] | 系列候选。检索 Kulm/Chlumec、Priesten/Přestanov等异名，核对南北进出道路；具体图幅与更新年代待核。 |
| 21 | 普乌图斯克 `pultusk_1806` | [Textor / Sotzmann 新东普鲁士地形图，1806–1808，约1:150,000][new-east-prussia] | 系列候选。目录提供分幅，包括Sect.8等，但未在本轮确定Pułtusk图幅；当前链接的Sect.4是索引/其他地区，不能直接拿它作底图。细节可能不足。 |
| 22 | 海尔斯贝格 `heilsberg_1807` | [Schrötter 东西普鲁士地形图，1796–1802测绘，1802–1812出版，1:150,000][schroetter] | 系列候选。核对 Heilsberg/Lidzbark Warmiński、Reichenberg、Bewernick；战役工事N1–5未必在一般地形图中。 |
| 23 | 埃劳 `eylau_1807` | [Schrötter系列][schroetter]；[第XI幅 Preusch. Eylau扫描线索][eylau-sheet] | 具体分幅线索；必须区分Preußisch Eylau与Deutsch Eylau。600dpi扫描不能增加原图没有的地形细节，未验收。 |
| 24 | 弗里德兰 `friedland_1807` | [Schrötter系列][schroetter] | 系列候选。检索Friedland/Pravdinsk，核对Sortlack、Posthenen、Heinrichsdorf；不能直接假设与埃劳同一幅。 |
| 25 | 波洛茨克 `polotsk_first_1812` | [1778城市计划图，1839年图集刊印][polotsk] | 暂缓。已找到具体图及IIIF入口，但可能是规划而非实测，且城市范围不一定覆盖部署。不能直接用于四条郊外事件。 |
| 26 | 别列津纳河 `berezina_1812` | [Borisov区1847年图线索，6俄里/英寸][borisov] | 暂缓。只取得检索索引信息，直接页面本轮返回404；约1:252,000，对Studenka渡口与小范围桥头定位太粗。尚无合格底图。 |

## 优先获取的图

### 圣塞巴斯蒂安

[官方图录][sanseb]与[官方文件详情][sanseb-download]。CNIG界面显示JPG、5.18MB；该产品系列说明为250ppi扫描、未地理配准。目录将地图日期列为1788，出版项为1789，应保留两个字段。

图录描述包含城市、La Concha海滩、道路、桥、植被、城防和水深，不是1813部署图。已见缩略图，未见明显军队阵列；这不是全分辨率无泄漏认证。重点检查Urumea两岸、城墙东侧和围城事件目标。真实城防可以保留，1813临时炮位/壕沟不应预画为答案。

下载产品页给出兼容CC-BY 4.0的署名要求，实际采用时保存当时条款与来源。原图朝南；旋转后重新建立像素坐标和标注版本。

### 图卢兹

[1808原图数字副本][toulouse-image]追溯到市档案馆；[官方古图栏目][toulouse]和[官方Flickr图册][toulouse-album]可交叉查找。保存图名、作者、原始馆藏标识和授权，不只保存Commons链接。

1808距1814较近，但“近”不保证同一环境：尤其Augustins堡等临时工事，若1808图上没有，只能用文字与地形关系建立有证据的区域答案；证据不足则标为不可定位，不能把参考图坐标直接平移。

### 滑铁卢和四臂村

[KBR Ferraris入口][ferraris]确认275幅已数字化；[官方拼幅索引][ferraris-index]用于选择原始图幅。[瓦隆政府地理配准图层][ferraris-service]可辅助确定裁切范围，服务说明也列出覆盖缺口。该服务有地理配准，并不代表历史地形或像素定位没有误差。

建议先定包含全部事件锚点的区域，再获取原始扫描；不要按单条答案所在位置做很紧的裁切。若使用拼接版本，记录拼接来源、投影和变换，不与原幅坐标混用。下载与数据集再分发许可需要另核。

### 奥地利和捷克四图

上/下奥地利、波希米亚、摩拉维亚第一次测绘有合适的地形底图方向，源馆藏为奥地利国家档案馆。**2026-09-24实际查看Arcanum页面时显示完整地图访问需要订阅**，本轮没有购买、没有抓取受限瓦片，也没有完成具体战区的高清视觉验收。

[奥地利国家档案馆地图集说明][austria-archive]可核对馆藏来源。捷克另有[ČÚZK档案地图入口][cuzk]用于核对地籍和其他历史地图，但不能假定所有平台提供相同测绘、相同年代或相同授权。

### 耶拿

馆藏页面确认1800、约1:35,000，提供两个IIIF条目，其中一个是[HisBest_derivate_00011514][jena-iiif]。本轮打开第一幅扫描，能看到地形与聚落，但中部有明显折损/遮挡；应进一步检查其他扫描，而不是修补成虚构地形。

页面标注CC BY-NC-SA 4.0。地图本体年代与数字副本的使用条件须分别记录，不能直接把所有旧图都标为无条件可再分发。

## 不应为了数量直接采用的候选

- **布萨科两图**：DGT是下一步馆藏入口，不代表已经找到对应图幅。检索到的全国图比例尺不足，1853地质示意图也不适合代替战术尺度地形图；1913旅行图偏晚且可能带战场纪念标记，不能仅因为不画军队就通过。
- **Marengo两图**：有1831系列和1852/1853具体馆藏线索，但暂未拿到清晰且足够覆盖的实图。本轮未购买IGM复制件。
- **阿尔武埃拉**：1938国家地形图有明确下载页，但晚127年；作为后世底图消融实验尚可讨论，不能混作近同期底图。
- **波洛茨克**：1778规划图的年代很吸引人，实测/规划属性和郊外覆盖却未过关。
- **别列津纳河**：河段、村落和渡点要精细，县级小比例尺图不够；保留缺口比假称已找到合格底图更可靠。
- **奥尔施泰特**：1911百科地形图描绘1806战区，但实际出版是1911；要核对是否带有任何战役标记，不能照网页标题“1806”当出版年。

## 接入前验收

1. **出处与授权**：保存馆藏页、原图链接、作者、测绘年、出版年、修订年、获取日期与再分发条件。
2. **范围与辨识度**：对每张参考图的至少四条事件逐个检查锚点是否在图内且能读清。只认出城市名不算可定位。
3. **图像泄漏**：人工逐块检查部队、箭头、日期阶段、阵地编号、围城壕沟及后世纪念标识。不得仅靠OCR阴性判断无泄漏。
4. **历史变化**：核对河道、桥、村落、林缘和道路。后建铁路、公路、新桥不能被当作战役时的约束。
5. **标注证据**：在干净底图上新建gold，旁看参考图核验。不同地图投影、比例、朝向不同，不能复制原图像素点。
6. **不确定性**：给出点/线容差或允许区域。明确到不了某座临时桥的位置，就用有证据的区域或剔除该题，不伪造精确点。
7. **输入隔离**：VLM只收到固定的干净底图、原始文本与目标问题，不收到参考图、人工坐标、人工画布截图或答案性来源备注。
8. **实验分组**：干净底图为主实验；带部署参考图只能作为独立条件对比。共享底图、战役、文本来源的样本按组划分，防止交叉泄漏。

不建议用AI擦除或生成式补画制造“历史底图”：可能改变地形与地名。必要的传统修复也应保留原件、掩膜和修复记录，并单列为另一实验条件。

**没有作战标记只能降低视觉答案泄漏，不能保证模型不受既有历史知识引导。** 建议另设文本-only与地图-only基线；若要判断模型是否真的依赖地理关系，可在明确标为合成对照的样本中改变方向或匿名化实体，并重新审核答案，不能把改写内容冒充史实。

现有64条地图推导候选即使换成干净底图，也仍不自动成为独立史料支持的事件，需继续补文本证据。

## 来源

[zurich]: https://www.e-rara.ch/zuz/content/titleinfo/8751704
[alessandria]: https://www.cittametropolitana.torino.it/cms/risorse/patrimonio-artistico-culturale-storico/dwd/biblioteca-storica/raccolte-particolari/CarteGeograficheArchivio_CatalogoNomiLuogo.pdf
[sardinia1831]: https://igmi.org/carte-antiche/colori_a1/?b_start%3Aint=8900
[portugal]: https://www.dgterritorio.gov.pt/dgt/historia-patrimonio/cartografia-antiga
[sanseb]: https://www.ign.es/web/catalogo-cartoteca/resources/html/000825.html
[sanseb-download]: https://centrodedescargas.cnig.es/CentroDescargas/detalleArchivo?sec=10899663
[albuera]: https://centrodedescargas.cnig.es/CentroDescargas/detalleArchivo?sec=11440
[orthez]: https://www.davidrumsey.com/maps1070028-25732.html
[toulouse]: https://www.archives.toulouse.fr/histoire-de-toulouse/patrimoine-urbain/plans-anciens/plans1772_1847
[toulouse-image]: https://commons.wikimedia.org/wiki/File:Plan_original_de_la_ville,_fauxbourgs_et_environs_de_Toulouse_avec_les_changements_survenus_depuis_1789_jusqu%E2%80%99en_1808.jpg
[toulouse-album]: https://www.flickr.com/photos/archives-toulouse/albums/72157664247082820/
[jena]: https://collections.thulb.uni-jena.de/receive/HisBest_cbu_00026914
[jena-iiif]: https://collections.thulb.uni-jena.de/api/iiif/presentation/v2/HisBest_derivate_00011514/manifest
[thuringia]: https://geoportal.geoportal-th.de/gaialight-th/_apps/dladownload/dl-histkart1.html
[auerstadt-late]: https://etc.usf.edu/maps/pages/3400/3428/3428.htm
[upper-austria]: https://maps.arcanum.com/en/map/firstsurvey-upper-austria/
[lower-austria]: https://maps.arcanum.com/en/map/firstsurvey-lower-austria/
[moravia]: https://maps.arcanum.com/en/map/firstsurvey-moravia/
[bohemia]: https://maps.arcanum.com/en/map/firstsurvey-bohemia/
[austria-archive]: https://archivinformationssystem.at/detail.aspx?ID=6715
[cuzk]: https://ags.cuzk.cz/archiv/
[ferraris]: https://www.kbr.be/en/the-ferraris-map/
[ferraris-index]: https://common.ngi.be/FerrarisKBR/index.jsp?l=fr
[ferraris-service]: https://geoservices.wallonie.be/arcgis/rest/services/CARTES_ANCIENNES/FERRARIS/MapServer/0
[vlissingen]: https://commons.wikimedia.org/wiki/File:Vlissingen_1750_Hattinga.jpg
[bergen]: https://dbc.library.uu.nl/handle/1874/291323
[new-east-prussia]: https://rcin.org.pl/dlibra/publication/33118/edition/31789/?language=pl
[schroetter]: https://rcin.org.pl/dlibra/publication/12308/edition/829?language=pl
[eylau-sheet]: https://igrek.amzp.pl/details.php?id=11809055
[polotsk]: https://imperiia.omeka.fas.harvard.edu/document/3785?collection=71
[borisov]: https://etomesto.com/map-belarus_borisovskiy-uezd-1847/
