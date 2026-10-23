# 全量事件第一轮 AI 辅助标注报告

日期：2026-10-11。**这是候选标注，不是人工金标准，也不是新一轮模型评测结果。**

## 交付

- [逐事件审核页](review.html)：一次显示一个事件，支持原像素、缩放、候选区域和参考图切换。
- [人工审核工作台](http://127.0.0.1:8771/review.html)：支持点、线、区域编辑，接受/修改后接受/需修改/待补证据/剔除与备注保存。人工几何单独保存在审核日志，不覆盖 AI 候选。需启动本地 `serve_reviews.py`，详见标注规则；直接打开 HTML 文件是只读模式。
- [机器可读记录](annotations.jsonl)：110 条，包含原始题目、文本、来源、坐标、证据和疑点。
- [手工决策源文件](decisions.json)、[版本与哈希](manifest.json)、[标注规则](PROTOCOL.md)。
- [浏览器检查记录](browser_validation.json)：逐事件图像及叠加像素检查、桌面/手机布局。它检查页面功能，不证明历史标注正确。
- [地图总览目录](overviews/)：26 张叠加图，像素尺寸与各自标注底图一致。细节审核以逐事件页面为准。

## 覆盖

活动集合共 **110 条事件、26 张参考地图**：苏黎世第二次战役 10 条，以及 map-first 扩展的 100 条。archive 中停用或重复版本没有再标。

| 本轮状态 | 数量 | 含义 |
| --- | ---: | --- |
| 待确认候选 | 120 | 有可审核几何，但仍不是 gold |
| 有歧义 | 13 | 其中 4 条只给假设几何，其余不强行画图 |
| 图示难辨 | 0 | 需更清晰地图或可读单位标签 |
| 来源冲突 | 0 | 问题或来源转述需先修正 |
| 图幅外 | 6 | 仅指本轮使用的底图版本 |

共 **123 条有几何，16 条为空**。空几何也有完整审核记录；不能把这些条目算作模型错误。所有记录均 pending / not_gold / eligible_for_scoring=false。

## 底图和独立性

苏黎世使用此前实验冻结的 Usteri 裁切 `2ae3fca4eb15dced41f82401`，1538 × 1754。**不是当前 UI 的 1144 × 820 版本。坐标不能直接粘到当前版本上。**该 1816 年地图也不是 1799 年即时测绘，需核对年代差异。

其他 100 条暂在各自原始作战参考图上标注，保留原像素。已有军事符号可以帮助第一轮标注，但它们会泄漏答案；这些结果不能包装成干净底图上的推理能力或定位准确率。

本轮没有读取预测坐标来生成标签，没有调用收费模型，没有修改旧 gold、活动事件文件、地图原件或线上平台。苏黎世已有模型结果出现在之前讨论里，因此不能声称是严格盲标。

多数 map-first 问题由地图图注或符号转述，文本和地图不独立。已逐图目视检查，并对部分外部原文回查；`source_check` 说明检查层级，不等于全体来源已经独立考证。

地理要素沿用项目 v1 词表；军事对象与部署语义保存在 `target_kind`。这是独立候选格式，需人工审核、版本对齐与字段转换后才能导入 atlas，不能直接替换其 gold 文件。

## 优先修复

1. **MF0045、MF0083、MF0095**：原先的图例/来源冲突已于 2026-10-21 随原文替换解决（题目改为 Petre 原文点名的地点），需在审核页复核新题。
4. **苏黎世 Z0002、Z0003**：Fahr 高地/树林受北侧裁切影响；Regensdorf 在本轮底图之外。先扩图或明确排除，不调整标签去迎合模型。
5. **苏黎世 Z0001、Z0005、Z0006、Z0008**：岸段、高地或营地存在定位粒度不足。保留疑点，不能把给定村名直接当作精确事件区域。
6. **MF0102**：Stakhov 有新旧村和河岸对应问题；必须核对地名变体。

上述地图图例冲突可在对应 [Auerstadt 原图](https://www.napoleon-series.org/images/military/maps/1806/auerstadt1.jpg)、[Pultusk 原图](https://www.napoleon-series.org/images/military/maps/1806/pultusk1.jpg)、[Friedland 原图](https://www.napoleon-series.org/images/military/maps/1807/Friedland1.jpg)对照核查。

## 建议审核顺序

先看来源冲突，再看有歧义/图示难辨，最后确认候选几何。不要仅凭多边形看起来合理就接受；应同时核对目标实体、时刻、岸别、地形与地图版本。

人工确认后另存审核版本，注明审核者、时间、修改原因和证据。争议样本应由导师或第二位标注者裁决；受模型输出影响的修订需披露。正式评测之前冻结问题、地图、标签及容差，不能把本轮 79 条候选直接当正式测试集。

## 地图索引

| 战场/图幅 | 事件数 | 候选/歧义/其他 | 逐事件 | 总览 |
| --- | ---: | --- | --- | --- |
| zurich_second_1799 | 10 | 4 / 5 / 1 | [Z0001](review.html#Z0001) | [PNG](overviews/2ae3fca4eb15dced41f82401.png) |
| marengo_1800 | 4 | 3 / 0 / 1 | [MF0005](review.html#MF0005) | [PNG](overviews/marengo_plate4.png) |
| bussaco_1810 | 4 | 2 / 2 / 0 | [MF0009](review.html#MF0009) | [PNG](overviews/bussaco_ney_1907_hires.png) |
| san_sebastian_1813 | 6 | 6 / 0 / 0 | [MF0013](review.html#MF0013) | [PNG](overviews/san_sebastian_1813.png) |
| 第一次苏黎世战役 | 6 | 6 / 0 / 0 | [MF0017](review.html#MF0017) | [PNG](overviews/zurich_first_1799.png) |
| Marengo · 上午部署 | 5 | 4 / 0 / 1 | [MF0021](review.html#MF0021) | [PNG](overviews/marengo_morning_1800.png) |
| 布萨科 · 雷尼耶进攻 | 4 | 3 / 1 / 0 | [MF0025](review.html#MF0025) | [PNG](overviews/bussaco_reynier_1810.png) |
| 阿尔武埃拉 · 初始部署 | 4 | 4 / 0 / 0 | [MF0029](review.html#MF0029) | [PNG](overviews/albuera_1811.png) |
| 奥尔泰兹战役 | 4 | 4 / 0 / 0 | [MF0033](review.html#MF0033) | [PNG](overviews/orthez_1814.png) |
| 图卢兹战役 | 4 | 4 / 0 / 0 | [MF0037](review.html#MF0037) | [PNG](overviews/toulouse_1814.png) |
| 耶拿战役 | 6 | 6 / 0 / 0 | [MF0041](review.html#MF0041) | [PNG](overviews/jena_1806.png) |
| 奥尔施泰特战役 | 4 | 4 / 0 / 0 | [MF0045](review.html#MF0045) | [PNG](overviews/auerstadt_1806.png) |
| 埃伯斯贝格 · 上午部署 | 7 | 6 / 0 / 1 | [MF0049](review.html#MF0049) | [PNG](overviews/ebersberg_1809.png) |
| 瓦格拉姆 · 战后夜间部署 | 9 | 8 / 0 / 1 | [MF0053](review.html#MF0053) | [PNG](overviews/wagram_night_1809.png) |
| 滑铁卢 · 开战部署 | 9 | 9 / 0 / 0 | [MF0057](review.html#MF0057) | [PNG](overviews/waterloo_1815.png) |
| 四臂村 · 东侧部署 | 5 | 5 / 0 / 0 | [MF0061](review.html#MF0061) | [PNG](overviews/quatre_bras_east_1815.png) |
| 弗利辛恩围城 | 4 | 1 / 3 / 0 | [MF0065](review.html#MF0065) | [PNG](overviews/flushing_1809.png) |
| 贝亨奥普佐姆攻城 | 5 | 5 / 0 / 0 | [MF0069](review.html#MF0069) | [PNG](overviews/bergen_op_zoom_1814.png) |
| 兹诺伊莫战役 | 7 | 6 / 0 / 1 | [MF0073](review.html#MF0073) | [PNG](overviews/znaim_1809.png) |
| 库尔姆 · 次日部署 | 4 | 4 / 0 / 0 | [MF0077](review.html#MF0077) | [PNG](overviews/kulm_1813.png) |
| 普乌图斯克战役 | 8 | 8 / 0 / 0 | [MF0081](review.html#MF0081) | [PNG](overviews/pultusk_1806.png) |
| 海尔斯贝格 · 前卫战 | 4 | 4 / 0 / 0 | [MF0085](review.html#MF0085) | [PNG](overviews/heilsberg_1807.png) |
| 埃劳战役 | 4 | 4 / 0 / 0 | [MF0089](review.html#MF0089) | [PNG](overviews/eylau_1807.png) |
| 弗里德兰 · 白天部署 | 4 | 4 / 0 / 0 | [MF0093](review.html#MF0093) | [PNG](overviews/friedland_1807.png) |
| 第一次波洛茨克 · 次日 | 4 | 4 / 0 / 0 | [MF0097](review.html#MF0097) | [PNG](overviews/polotsk_first_1812.png) |
| 别列津纳河渡河 | 4 | 2 / 2 / 0 | [MF0101](review.html#MF0101) | [PNG](overviews/berezina_1812.png) |

## 逐条记录

| 事件 | 状态 | 置信度/5 | 几何 | 候选位置或未定位原因 |
| --- | --- | ---: | --- | --- |
| [Z0001](review.html#Z0001) | 有歧义 | 2 | polygon | Dietikon 对岸、Schönenwerd 河弯北侧的候选登陆岸段 |
| [Z0002](review.html#Z0002) | 有歧义 | 2 | null | Closter-Fahr 高地上的树林 |
| [Z0003](review.html#Z0003) | 图幅外 | 4 | null | Regensdorf |
| [Z0004](review.html#Z0004) | 待确认候选 | 4 | polygon | Altstetten 村庄 |
| [Z0005](review.html#Z0005) | 有歧义 | 2 | null | 苏黎世后方的高地，可能涉及 Zürichberg 一带 |
| [Z0006](review.html#Z0006) | 有歧义 | 2 | polygon | Dietikon 一侧、Schönenwerd 河弯南西岸的候选集结岸段 |
| [Z0007](review.html#Z0007) | 待确认候选 | 4 | polygon | Wollishofen 村庄 |
| [Z0008](review.html#Z0008) | 有歧义 | 2 | null | Hong / Höngg 的小营地 |
| [Z0009](review.html#Z0009) | 待确认候选 | 3 | line | 苏黎世北东出口经 Schwamendingen 方向的道路可见段 |
| [Z0010](review.html#Z0010) | 待确认候选 | 3 | polygon | Limmat 东侧的苏黎世城内部分 |
| [MF0005](review.html#MF0005) | 待确认候选 | 4 | polygon | Castel-ceriolo |
| [MF0006](review.html#MF0006) | 待确认候选 | 4 | polygon | Marengo（Bormida 东岸附近、亚历山德里亚通往曼托瓦的大路上） |
| [MF0007](review.html#MF0007) | 图幅外 | 3 | null | Marengo 以东约三英里的大路上（不在这张图上） |
| [MF0008](review.html#MF0008) | 待确认候选 | 3 | polygon | Bormida 河上（亚历山德里亚前）的桥头堡 |
| [MF0009](review.html#MF0009) | 待确认候选 | 3 | line | Craufurd 阵地前、Sula 上方的凹陷道路段 |
| [MF0010](review.html#MF0010) | 有歧义 | 2 | null | Sula 前方低地的进攻出发区 |
| [MF0011](review.html#MF0011) | 待确认候选 | 3 | polygon | Moura 道路转弯内侧的小松林 |
| [MF0012](review.html#MF0012) | 有歧义 | 2 | polygon | Craufurd 右侧、沟头道路和 Coleman 部队前方的候选反击区 |
| [MF0013](review.html#MF0013) | 待确认候选 | 3 | polygon | St. Bartolomeo 修道院和旁边的小多面堡（城前约 700-800 码） |
| [MF0014](review.html#MF0014) | 待确认候选 | 3 | polygon | Urumea 河对岸的 Chofre 沙丘（远距离炮台） |
| [MF0015](review.html#MF0015) | 待确认候选 | 4 | polygon | Santa Clara 岛 |
| [MF0016](review.html#MF0016) | 待确认候选 | 3 | polygon | 城堡（Monte Orgullo 上）和 St. Teresa 修道院 |
| [MF0017](review.html#MF0017) | 待确认候选 | 3 | line | 从 Wittikon 向 Hirslanden |
| [MF0018](review.html#MF0018) | 待确认候选 | 3 | line | 从 Dübendorf 经 Fällanden、Pfaffhausen，再向 Zürich-Berg |
| [MF0019](review.html#MF0019) | 待确认候选 | 3 | line | 先打 Stettbach，再向 Schwamendingen |
| [MF0020](review.html#MF0020) | 待确认候选 | 4 | line | 经 Glattbruck 指向 Seebach |
| [MF0021](review.html#MF0021) | 待确认候选 | 3 | polygon | Bormida 两座桥前（右岸）的桥头堡 |
| [MF0022](review.html#MF0022) | 待确认候选 | 2 | polygon | Victor 的右侧 |
| [MF0023](review.html#MF0023) | 待确认候选 | 2 | polygon | Marengo 村前、沿泥泞的 Fontanone 小溪 |
| [MF0024](review.html#MF0024) | 图幅外 | 4 | null | Tortona 附近的 Scrivia 河沿岸（不在这张图上） |
| [MF0025](review.html#MF0025) | 待确认候选 | 3 | polygon | Santo Antonio 道路越过山脊的鞍部 |
| [MF0026](review.html#MF0026) | 待确认候选 | 3 | polygon | 88th 与山口守军之间的山脊空隙 |
| [MF0027](review.html#MF0027) | 有歧义 | 2 | null | San Antonio 山口法军右侧的低峰 |
| [MF0028](review.html#MF0028) | 待确认候选 | 3 | line | 山脊背面的交通道路可见段 |
| [MF0029](review.html#MF0029) | 待确认候选 | 3 | polygon | Albuera 西侧两条道路间 Stewart 初始部署区 |
| [MF0030](review.html#MF0030) | 待确认候选 | 3 | polygon | Hamilton 初始左翼，Badajoz 道路以外 |
| [MF0031](review.html#MF0031) | 待确认候选 | 3 | polygon | Valverde 道路南侧 Blake 初始右翼 |
| [MF0032](review.html#MF0032) | 待确认候选 | 3 | polygon | Albuera 村庄至河桥的防御走廊 |
| [MF0033](review.html#MF0033) | 待确认候选 | 4 | polygon | Saint-Boes 村庄 |
| [MF0034](review.html#MF0034) | 待确认候选 | 3 | polygon | Orthez 上游、Souars 附近 Hill 渡河地段 |
| [MF0035](review.html#MF0035) | 待确认候选 | 3 | polygon | Orthez 上方高地的法军左翼初始区域 |
| [MF0036](review.html#MF0036) | 待确认候选 | 4 | polygon | Roman Camp 南侧的初始 Light Division 预备区 |
| [MF0037](review.html#MF0037) | 待确认候选 | 3 | polygon | Croix d'Orade（地图作 Croix Daurade） |
| [MF0038](review.html#MF0038) | 待确认候选 | 3 | polygon | Montblanc（地图作 Mont Blanc） |
| [MF0039](review.html#MF0039) | 待确认候选 | 3 | polygon | 运河上最靠近 Garonne 河的那座桥（Ponts Jumeaux）的桥头堡 |
| [MF0040](review.html#MF0040) | 待确认候选 | 3 | polygon | Garonne 河左岸的郊区（St. Cyprien） |
| [MF0041](review.html#MF0041) | 待确认候选 | 3 | polygon | Kotschau、Klein Romstadt 和 Capellendorf 三村之间（地图作 Kötschau、Kl. Romstädt、Capellendorf） |
| [MF0042](review.html#MF0042) | 待确认候选 | 4 | polygon | Vierzehnheiligen（地图作 14 Heiligen） |
| [MF0043](review.html#MF0043) | 待确认候选 | 4 | polygon | Isserstadt（地图拼作 Isserstädt）一带 |
| [MF0044](review.html#MF0044) | 待确认候选 | 3 | line | Closewitz 和 Lutzeroda 两村及其间的连线（地图作 Closwitz、Lützeroda） |
| [MF0045](review.html#MF0045) | 待确认候选 | 4 | polygon | Poppel 附近 |
| [MF0046](review.html#MF0046) | 待确认候选 | 3 | polygon | Gernstadt（地图作 Gernstädt） |
| [MF0047](review.html#MF0047) | 待确认候选 | 3 | polygon | Sonnendorf |
| [MF0048](review.html#MF0048) | 待确认候选 | 3 | polygon | Eckardsberga 与 Lisdorf 之间的林木高地 Puck Holz（地图作 Puckholz） |
| [MF0049](review.html#MF0049) | 待确认候选 | 3 | polygon | Klein-München 村，以及 Traun 桥前 Linz、Wels 两条路岔口的房屋 |
| [MF0050](review.html#MF0050) | 待确认候选 | 3 | line | 一条狭窄的堤道，接一座约两百 toise 长的木桥 |
| [MF0051](review.html#MF0051) | 待确认候选 | 2 | line | Linz 大道 |
| [MF0052](review.html#MF0052) | 待确认候选 | 2 | line | Traun 河右岸的道路（经 Fischdorf、Strassenhof 到 Ebersberg） |
| [MF0053](review.html#MF0053) | 待确认候选 | 3 | polygon | Aderklaa 与 Raschdorf 之间 |
| [MF0054](review.html#MF0054) | 待确认候选 | 2 | line | 经 Säuring 到 Enzersfeld |
| [MF0055](review.html#MF0055) | 待确认候选 | 3 | polygon | Jedlersdorf |
| [MF0056](review.html#MF0056) | 待确认候选 | 2 | line | 从 Jedlersdorf 起沿 Brünn 大道向北（终点地名扫描不清，可能是图上的 Helbesbrunn） |
| [MF0057](review.html#MF0057) | 待确认候选 | 4 | polygon | Rossomme 农庄稍前方，Charleroi 大道两侧 |
| [MF0058](review.html#MF0058) | 待确认候选 | 4 | polygon | Byng 的第 2 近卫旅：山脊顶上，第 1 旅与 Nivelles 大道之间 |
| [MF0059](review.html#MF0059) | 待确认候选 | 4 | line | 从 La Belle Alliance 向东，到正对 Papelotte 和 La Haye 的山脊端 |
| [MF0060](review.html#MF0060) | 待确认候选 | 4 | polygon | Kempt 旅：Pack 旅右前方、Wavre 路树篱后不远，右翼靠 Charleroi 大道 |
| [MF0061](review.html#MF0061) | 待确认候选 | 2 | polygon | Delhutte 树林（Bois de Delhutte） |
| [MF0062](review.html#MF0062) | 待确认候选 | 3 | polygon | 中央前方的大道（Charleroi 大道）上，Gemioncourt 以南（地图上的 Bijleveld 第一阵位） |
| [MF0063](review.html#MF0063) | 待确认候选 | 3 | polygon | Charleroi 大道以东、Gemioncourt 与 Piraumont 以南的法军纵队推进区 |
| [MF0064](review.html#MF0064) | 待确认候选 | 4 | polygon | Piermont（地图拼作 Piraumont） |
| [MF0065](review.html#MF0065) | 有歧义 | 2 | null | Middelburg 至 Flushing 的接近道路 |
| [MF0066](review.html#MF0066) | 有歧义 | 1 | null | Flushing 北郊法军哨兵接触区 |
| [MF0067](review.html#MF0067) | 待确认候选 | 3 | line | Flushing 朝陆地的堡垒外缘 |
| [MF0068](review.html#MF0068) | 有歧义 | 1 | null | 城外英军围城壕与炮台作业地段 |
| [MF0069](review.html#MF0069) | 待确认候选 | 4 | line | Tholen 堤（Tholen Dyke） |
| [MF0070](review.html#MF0070) | 待确认候选 | 3 | line | 设防营地（retrenched camp）的眼镜堡右翼，然后踏冰过 3、4 号正面的壕沟 |
| [MF0071](review.html#MF0071) | 待确认候选 | 2 | polygon | 第 9、10 号正面：紧挨 Steenbergen 防线、有宽阔淹水区掩护的一段 |
| [MF0072](review.html#MF0072) | 待确认候选 | 4 | line | 12 号棱堡，其右面有 Steenbergen 城门 |
| [MF0073](review.html#MF0073) | 待确认候选 | 4 | polygon | Brenditz |
| [MF0074](review.html#MF0074) | 待确认候选 | 4 | polygon | Klosterbruck（修道院） |
| [MF0075](review.html#MF0075) | 待确认候选 | 2 | polygon | Tesswitz（地图作 Kl. Tesswitz） |
| [MF0076](review.html#MF0076) | 待确认候选 | 3 | polygon | Legrand 师（在 Oblass 以南、维也纳大道两侧） |
| [MF0077](review.html#MF0077) | 待确认候选 | 3 | polygon | Priesten 村 |
| [MF0078](review.html#MF0078) | 待确认候选 | 3 | polygon | Arbesau 村 |
| [MF0079](review.html#MF0079) | 待确认候选 | 3 | line | Nollendorf 大道（从 Kulm 向东北经 Schande 上山） |
| [MF0080](review.html#MF0080) | 待确认候选 | 3 | polygon | Böhmisch Neudörfel 村 |
| [MF0081](review.html#MF0081) | 待确认候选 | 2 | polygon | 大树林与 Mosin 村之间的空地 |
| [MF0082](review.html#MF0082) | 待确认候选 | 3 | polygon | Mosin 高地大树林的西南半部 |
| [MF0083](review.html#MF0083) | 待确认候选 | 2 | polygon | 从 Golymin 大道上（大树林西南、主阵线一侧） |
| [MF0084](review.html#MF0084) | 待确认候选 | 3 | line | 沿 Golymin 大道（从东北方向朝 Mosin 高地而来） |
| [MF0085](review.html#MF0085) | 待确认候选 | 3 | polygon | Reichenberg（Petre 拼作 Reichenburg；图上 Рейхенбергъ） |
| [MF0086](review.html#MF0086) | 待确认候选 | 4 | polygon | Bewernick（图上 Беверникъ） |
| [MF0087](review.html#MF0087) | 待确认候选 | 3 | polygon | Grossendorf（图上 Гроссендорфъ，湖北岸） |
| [MF0088](review.html#MF0088) | 待确认候选 | 3 | line | 从靠河的 1 号多面堡经 2 号到右后方的 3 号多面堡 |
| [MF0089](review.html#MF0089) | 待确认候选 | 3 | polygon | Klein Sausgarten（图上 Саусгартенъ） |
| [MF0090](review.html#MF0090) | 待确认候选 | 3 | polygon | Anklappen（图上误刻作 Ауклапенъ） |
| [MF0091](review.html#MF0091) | 待确认候选 | 3 | polygon | Serpallen（图上 Серпаленъ） |
| [MF0092](review.html#MF0092) | 待确认候选 | 3 | polygon | Schloditten（图上 Шлодитенъ；不是北面的 Шмодитенъ/Schmoditten） |
| [MF0093](review.html#MF0093) | 待确认候选 | 4 | polygon | Heinrichsdorf（图上 Гейнрихсдорфъ） |
| [MF0094](review.html#MF0094) | 待确认候选 | 3 | polygon | Sortlack 树林（图上 Сортлакскій лѣсъ） |
| [MF0095](review.html#MF0095) | 待确认候选 | 2 | polygon | 较小的南部：从 Millstream（磨坊溪）到 Sortlack |
| [MF0096](review.html#MF0096) | 待确认候选 | 4 | polygon | Posthenen（图上 Постененъ） |
| [MF0097](review.html#MF0097) | 待确认候选 | 3 | line | Prismenitz 前方 A 俄军第一线 |
| [MF0098](review.html#MF0098) | 待确认候选 | 3 | polygon | 北部聚落道路以东 Wrede 师 D 队列 |
| [MF0099](review.html#MF0099) | 待确认候选 | 4 | polygon | Dvina 河畔、城西的 Castex 骑兵 K |
| [MF0100](review.html#MF0100) | 待确认候选 | 4 | polygon | Polota 支流东侧 Corbineau 骑兵 M |
| [MF0101](review.html#MF0101) | 待确认候选 | 3 | polygon | Studianka 对岸之间的选定渡河地段 |
| [MF0102](review.html#MF0102) | 有歧义 | 2 | null | Stakhov 佯动区，地名对应尚不唯一 |
| [MF0103](review.html#MF0103) | 待确认候选 | 3 | polygon | Borissow 主城的集结区域 |
| [MF0104](review.html#MF0104) | 有歧义 | 2 | null | Studianka 所在一岸、村上方高地炮位 |
| [MF0124](review.html#MF0124) | 待确认候选 | 3 | polygon | Zoom 河的河道入口（1 号与 15 号棱堡之间，港口处） |
| [MF0121](review.html#MF0121) | 待确认候选 | 3 | polygon | Gr. Romstadt（地图作 Gr. Romstädt） |
| [MF0122](review.html#MF0122) | 待确认候选 | 3 | polygon | Klein Romstadt（地图作 Kl. Romstädt） |
| [MF0123](review.html#MF0123) | 待确认候选 | 3 | polygon | Castel-ceriolo |
| [MF0111](review.html#MF0111) | 待确认候选 | 3 | polygon | 深谷外侧（离镇较远一侧）、Pultusk 西北河岸高地 |
| [MF0112](review.html#MF0112) | 待确认候选 | 3 | line | Golymin 大道，从 Pultusk 到大道进入 Mosin 高地树林处 |
| [MF0113](review.html#MF0113) | 待确认候选 | 3 | polygon | 大树林外、骑跨 Golymin 大道（树林靠 Mosin 一侧） |
| [MF0114](review.html#MF0114) | 待确认候选 | 3 | line | 骑兵线前方的洼地里，一直延伸到森林前的零星树林 |
| [MF0120](review.html#MF0120) | 待确认候选 | 3 | polygon | Gemioncourt 农庄（Charleroi 大道旁） |
| [MF0115](review.html#MF0115) | 待确认候选 | 3 | polygon | Durutte 师：山脊最东端，正对 Papelotte 和 La Haye 农庄 |
| [MF0116](review.html#MF0116) | 待确认候选 | 3 | polygon | Jaquinot 骑兵师：步兵右侧的谷地，前方是 Smohain 村 |
| [MF0117](review.html#MF0117) | 待确认候选 | 4 | polygon | Charleroi 大道旁的大沙坑，面对 La Haye Sainte 后面的小花园 |
| [MF0118](review.html#MF0118) | 待确认候选 | 3 | polygon | Bylandt 旅：山脊外坡，介于高丘和 Genappe 大道之间 |
| [MF0119](review.html#MF0119) | 待确认候选 | 3 | polygon | Pack 旅：山脊内坡，离 Wavre 路约 200 码 |
| [MF0125](review.html#MF0125) | 待确认候选 | 3 | polygon | Riesbach 高地 |
| [MF0126](review.html#MF0126) | 待确认候选 | 4 | polygon | Opfiken（Reuss 亲王离开的位置） |
| [MF0127](review.html#MF0127) | 待确认候选 | 3 | polygon | 城堡，位于一座孤立的小丘上 |
| [MF0128](review.html#MF0128) | 待确认候选 | 3 | line | 沿 Traun 河左岸的 Wels 大道 |
| [MF0129](review.html#MF0129) | 图幅外 | 4 | null | Enns（城不在这张图上，图上只在路名里出现 Enns） |
| [MF0130](review.html#MF0130) | 待确认候选 | 4 | polygon | Leopoldau |
| [MF0131](review.html#MF0131) | 待确认候选 | 2 | line | 经 Gerasdorf 退到 Hagenbrunn 前面 |
| [MF0132](review.html#MF0132) | 待确认候选 | 2 | polygon | Stammersdorf 高地 |
| [MF0133](review.html#MF0133) | 待确认候选 | 2 | polygon | Strebersdorf 一带的丘陵 |
| [MF0134](review.html#MF0134) | 图幅外 | 4 | null | Rohrwald 隘口入口、Korneuburg 平原后方（不在这张图上） |
| [MF0135](review.html#MF0135) | 待确认候选 | 3 | polygon | Schallersdorf 桥（河在这里拐成直角） |
| [MF0136](review.html#MF0136) | 待确认候选 | 3 | polygon | Edelspitz（扫描作 Edbpiz） |
| [MF0137](review.html#MF0137) | 图幅外 | 4 | null | Erdberg（不在这张图上） |
| [MF0138](review.html#MF0138) | 待确认候选 | 2 | polygon | 山下的地峡（迎击从城里出来的守军） |
| [MF0139](review.html#MF0139) | 待确认候选 | 2 | polygon | 地峡上的 St. Bartolomeo 高地 |

## 来源回查

除各地图原图及图例外，本轮回查的外部材料如下。回查不等于独立证实地图边界。

- [Z0001, Z0002, Z0003, Z0004, Z0005, Z0006, Z0007, Z0008, Z0009, Z0010](https://archive.org/details/historyfrenchre05shobgoog)。具体章节保留在每条 `source_record.source_section` 中。
- [MF0009, MF0010, MF0011, MF0025, MF0026, MF0027, MF0028](https://www.gutenberg.org/files/55231/55231-h/55231-h.htm)。具体章节保留在每条 `source_record.source_section` 中。
- [MF0012](https://www.wtj.com/archives/wellington/1810_09d.htm)。具体章节保留在每条 `source_record.source_section` 中。
- [MF0029, MF0030, MF0031, MF0032](https://www.napoleon-series.org/military-info/battles/1811/Albuera/Archives/c_Beresforddispatch.html)。具体章节保留在每条 `source_record.source_section` 中。
- [MF0033, MF0034, MF0035, MF0036](https://archive.org/details/vol11dispatcheso00well)。具体章节保留在每条 `source_record.source_section` 中。
- [MF0065, MF0066, MF0067, MF0068](https://www.napoleon-series.org/wp-content/uploads/2022/10/A-Walcheren-Journal.pdf)。具体章节保留在每条 `source_record.source_section` 中。
- [MF0101, MF0102, MF0103, MF0104](https://archive.org/details/histoiredelexpd00chamgoog)。具体章节保留在每条 `source_record.source_section` 中。

## 验证与复现

生成时校验 110 个 ID 完整且不重复、原图哈希和尺寸、坐标边界、非退化几何及多边形无自交。机器校验不能证明历史定位正确。

```sh
.venv/bin/python benchmark/annotations/assistant_round_20261011/build.py
```

脚本只重建本目录输出。任何坐标或题目修订都需重新生成，并保留人工审核记录。图像与文献的公开再分发许可仍需另行检查。
