# Maps 优先选图与史料清单

更新：2026-09-24。当前 100 条 Maps 候选，加上未修改的苏黎世 10 条，共 110 条、26 张参考图。
其中本轮新增 22 图、88 条：24 条来自外部文字，64 条为地图推导候选，不是已验证真值。
当前 13 国达到两图、每图四条的候选门槛，但尚未覆盖所有国家；也未为新增图准备干净模型输入图。
新增图文、日期冲突与逐条问题见 [扩充审核清单](MAP_EXPANSION_REVIEW.md)，缺口见 [国家覆盖审核](COUNTRY_COVERAGE.md)。
下文保留最初三组 Maps 候选的来源说明。

## 本次替换

- 移出活动数据：Borkowo、Sochocin、Wavre 旧三图及 N0001–N0020。
- 旧候选、三图及 N0001 的既有标注原样归档至 `archive/napoleon_candidates_2026-09-24/`。
- 当前使用 MF0005–MF0008（Marengo）、MF0009–MF0012（布萨科）、MF0013–MF0016（圣塞巴斯蒂安），不复用退役事件 ID 或坐标。
- 苏黎世候选、地图集底图版本、人工标注、预测日志及地名实验数据均未迁移或清空。
- Wkra 合图及 MF0001–MF0004 因辨识度问题再次退出活动数据，替换为布萨科。换图前的候选与说明快照、Wkra 图存于 `archive/wkra_replaced_by_bussaco_2026-09-24/`。

所有新增参考图先从 [Napoleon Series Maps 目录](https://www.napoleon-series.org/military-information/maps/) 选图；布萨科使用同一图版的 Gutenberg 较高清扫描，两个来源分别记录。
参考图含部队位置、说明文字和行动线，不能直接充当无答案泄漏的 VLM 输入底图。

## 1. 布萨科 / Bussaco：内伊进攻

- [Maps 目录原图](https://www.napoleon-series.org/images/military/maps/peninsula/busaco1.jpg)，615 × 676，留存于 `maps/napoleon_maps/bussaco_ney_maps_original.jpg`。
- 当前显示 [同图版的较高清扫描](https://www.gutenberg.org/files/55231/55231-h/images/ney-g.jpg)，1141 × 1200，留存于 `maps/napoleon_maps/bussaco_ney_1907_hires.jpg`。并非放大插值或 AI 重画，也不是 1810 年现场地图。
- 图版署名 B. V. Darbishire, Oxford, 1907；见 Charles Oman, *A History of the Peninsular War*, vol. III (1908)，图版 XIII、对页 380。已目视比对 Maps 与 Gutenberg 两版的道路、部队、地名和图例；二者边距不同，不互换像素坐标。
- 地点：葡萄牙布萨科山地；日期：1810-09-27；范围限定在 Ney 进攻的 Sula、Moura、修道院一带。
- 图例以红、绿、黑区分英军、葡军、法军；地名为拉丁字母。核心地名和相邻部署可辨认，但仍非无限精度地形图。
- 本图有答案性的部署符号，只作参考图；还没有新建干净 VLM 底图或人工真值。
- 此图是战斗示意性重建，不是逐分钟快照。初始部署、推进和反击不能当成同一时刻。

对应资料：

1. [Oman 原书数字版，Section XXI, Chapter II](https://www.gutenberg.org/files/55231/55231-h/55231-h.htm#Page_378)，pp. 378–383：Ney 两个师的进攻、Craufurd 的防御、Marchand 的转向。MF0009–MF0011 取自正文，非看图编造叙事；但正文和图仍来自同一书，不能当独立交叉验证。
2. [Wellington 致 Liverpool，1810-09-30](https://www.wtj.com/archives/wellington/1810_09d.htm)：本次已阅读的战报网络转录。MF0012 使用 Coleman 预备旅和第 19 葡萄牙团反击段；只支持较宽的战区位置，非精确坐标。未查验手稿。
3. MF0012 的道路/沟谷细化线索另见 [Oman p. 381](https://www.gutenberg.org/files/55231/55231-h/55231-h.htm#Page_381)；它属于后出的解释，不混入战报原意。
4. Napoleon Series 的 [葡萄牙轻步兵叙事](https://www.napoleon-series.org/military-info/organization/portugal/Infantry/Notes/c_NotesonPortugueseInfantry1stCacadores.html) 可作补充阅读，本轮不据此增加重复定位目标。

| ID | 目标 | 文本依据 | 建议几何 |
|---|---|---|---|
| MF0009 | 43rd、52nd 反击前隐蔽的凹陷道路区段 | Oman pp. 379–380 | 线 |
| MF0010 | Loison 两旅上坡前、Sula 前方的低地出发区域 | Oman p. 379 | 区域 |
| MF0011 | Marchand 先头旅转离道路攻击的小松林 | Oman pp. 382–383 | 区域 |
| MF0012 | 第 19 葡萄牙团在 Craufurd 右侧的反击地段 | Wellington 战报；Oman 作辅助对照 | 区域 |

先核 MF0009 和 MF0011 的道路/树林对应，再处理初始位置与反击区域。不要把图中的推进队形直接当作 MF0010 的起点；不要把观察者画面左侧当作部队行进方向的左侧。证据不足时保留歧义，不画一个过大的范围充当答案。

## 2. Marengo 第四图：战后部署

- [第四图原图](https://www.napoleon-series.org/images/military/maps/1800/marengo4.jpg)
- 本地：`maps/napoleon_maps/marengo_plate4.jpg`，1750 × 1232；保留原图说明与图例供审核。
- 原图标题：Bataille de Marengo, IVme Planche。图题明确是战役次日早晨的部署，按 1800-06-15 记录；网站目录却标成 14 日夜晚。两种时间信息均保留，不默默混用。
- Sources 列有 Berthier 的 *Relation De La Bataille De Marengo*（Paris, 1805），但总书目不等于此扫描件的逐图来源证明，具体版次暂记待核实。
- Marengo、Spinetta、Castel-Ceriolo、Bormida 和 Alessandria 在图内可见。第三图的 San Giuliano 区域覆盖不足，已移到本次归档中的 `maps/research_not_selected/`，没有为了凑数接入德塞到达阶段问题。

对应资料：

1. 第四图左侧法文部署说明：已目视核对。MF0005–MF0007 是图注的英文转述，不是另找的独立战报。尤其村内部队编号为 **70th**，不能误读为 75th。
2. T. E. Crowdy，[Marengo and the Journal of General Jean Boudet](https://www.napoleon-series.org/military-info/battles/1800/Italy/Marengo/MarengoBoudet.pdf)：含 Boudet 日记、Dalton 报告和 Boudet 致 Berthier 的战斗报告译文。这里查阅的是现代文章中的译文，不是军队档案手稿。
3. MF0008 使用 PDF **第 13 页（从 1 计数）** 的 Dalton 报告：写于 16 日，叙述 15 日部署。只能作为独立对照候选；不能未经核对就说它与第四图精确一致。
4. 同 PDF 第 11–12 页日记、第 14–16 页正式报告可用于后续研究 14 日战斗阶段；本轮没有把其中 San Giuliano 的部署硬套到第四图上。

| ID | 目标 | 证据性质 | 建议几何 |
|---|---|---|---|
| MF0005 | Castel-Ceriolo 村内第 70 半旅 | 原图部署说明，非独立对照 | 区域 |
| MF0006 | Marengo 与 Spinetta 之间的部署线 | 原图部署说明，非独立对照 | 线 |
| MF0007 | Rivaud 在 Castel-Ceriolo 后方的宿营区域 | 原图部署说明；后方朝向待核 | 区域 |
| MF0008 | 第 30 半旅靠 Bormida、平行道路的部署线 | 独立报告译文；精确图文对应待核 | 线 |

MF0008 的位置可能与图注 Boudet 部署并不一致，需保留冲突而非强行给出一个真值。

## 3. 圣塞巴斯蒂安围城 / San Sebastian，1813

- [Maps 彩色围城图原图](https://www.napoleon-series.org/images/military/maps/peninsula/sebastian1.jpg)，1260 × 765，未裁切、未放大或重绘；本地为 `maps/napoleon_maps/san_sebastian_1813.jpg`。
- 这是 Maps 目录的第一张 San Sebastian: 1813 图。另一个黑白版本对比后未接入，以免重复或降低辨识度。
- 原图可见 Santa Clara、Chofre Sandhills、San Martin、St. Bartholomew、Monte Orgullo 和 Castle of La Mota，以及炮台、战壕和缺口。英文字标、河岸和城墙较清晰，适合先做可标注性审核。
- 标题的 1813 是所绘事件年份，**不是已经确认的制图或出版年份**；确切作者与版本尚待考证。印刷比例尺不直接转换成像素误差的米数。
- 参考图汇总多个围城阶段，不能把 7 月攻外围工事、8 月攻城和后续城堡抵抗合并为同一时刻。
- 本次仅新增参考图和文本；没有创建干净底图、人工答案或模型预测。

文本来源：

1. Ray Foster，[9th Regiment of Foot](https://www.napoleon-series.org/military-info/organization/Britain/Infantry/WellingtonsRegiments/c_9thFoot.html)，1813 年段、17 July 兵力表前的叙事。MF0013 使用夺取 San Bartolome 后进至 San Martin 的部分；是现代部队史整理，不是当事人原始报告。
2. Gareth Glover，[San Sebastian Then and Now: The Siege of 1813](https://www.napoleon-series.org/military-info/virtual/SanSebastian.pdf)，PDF **第 1 页（从 1 计数）**、The Siege。MF0014–MF0016 分别来自炮击、附加炮台和守军撤退段；是现代战史概述，非独立核验后的真值。

| ID | 目标 | 时间/阶段 | 几何 |
|---|---|---|---|
| MF0013 | 先头部队受阻的 San Martin 郊区 | 7 月 17 日，攻外围工事后 | 区域 |
| MF0014 | 打开东墙缺口的 Chofre 炮兵阵地区域 | 围城炮击阶段；不指定某一炮台号 | 区域 |
| MF0015 | Santa Clara 岛的附加炮台区域 | 具体部署日期在所用段落中未说明 | 区域 |
| MF0016 | 弃城后守军据守的山丘与城堡区域 | 8 月 31 日城墙被攻破后 | 区域 |

MF0013 要区分先前占领的位置与后来受阻的位置；MF0016 要区分城墙缺口与撤退终点。
MF0014、MF0015 更接近带事件背景的地理定位基线，不应全部算作多步事件推理样本。
资料只支持区域时不要给精确点；同一战役四条共同使用 `split_group: san_sebastian_1813`。
图像 SHA-256：`d89640aa190ff782fd9a8047632dd1ba77e00ca0d36a2dbf831436eda93b3dd6`。

## 审核顺序

1. 在主页或地图集查看参考图和每条问题的出处，先判定图上地物、部队、日期与文字能否对应。
2. 优先核 MF0005、MF0006；再核相对方向更模糊的 MF0007 和独立报告 MF0008。
3. 布萨科先核对叙事阶段和相对方向，再决定哪些记录能正式纳入。当前不计入模型准确率。
   圣塞巴斯蒂安可先核 MF0013、MF0016 的事件前后位置，再核两条炮兵位置基线。
4. 为每张通过审核的参考图另配干净标注底图；不要默认部署图本身可作模型输入。
5. 在干净底图上保存人工几何，记录跨图对应依据；参考图上审核的坐标不会自动迁移过去。
6. `split_group` 按战役分组；同图多个问题不能当成多个独立地图样本，图注来源与独立报告须分层报告结果。

## 文件与追溯

- 候选：`benchmark/map_first_candidates.jsonl`。所有英文文本均为简短转述，非逐字引文，具体章节逐条保存。
- 传统参考图标注：`benchmark/map_first_annotations.jsonl`（首次保存后产生）。
- 地图集标注仍写现有 `benchmark/atlas/`，与传统入口的原图像素标注不同。
- 原图 SHA-256：布萨科高清版 `c0017121d9b72e754f0c956811a532447e9580d68757189ce078a6f95e11d6cc`；Maps 小图 `5bcca09bdc366b074d130698ca22c417a244df7fddd95c13ede8403a582e4c9b`；Marengo `3c7a466b716e7b585c1a1ee735929b3493e5d7f821f25821a3b6f8a4d704200b`。
- 网站有自己的使用条款；候选仍标 `needs_release_review`，公开发布图像/译文之前需另核许可，不由可下载推定可任意再分发。
