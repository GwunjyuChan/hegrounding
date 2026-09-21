# 第二次苏黎世战役：10 条候选

这是一组独立的可标注性试验，不修改原有 20 条候选或人工标注。
目标为 1799 年 9 月 25 日至翌晨战斗前的行动，文本也包含 26 日战况，属于法国革命战争。
2026-09-16 扩展到 10 条：Z0001–Z0005 原记录逐字保留，Z0006–Z0010 为新增待审核候选。
候选文件不存标准坐标；实际审核状态和几何保存在独立的人工标注文件，不以候选中的 pending 覆盖。

## 地图集入口（当前流程）

打开 <http://127.0.0.1:8767/atlas.html>，选择第二次苏黎世战役，再进入“事件标注”。
新候选与旧候选共用同一参考图、同一张 Usteri 1816 年裁切底图，无须重新导入地图。
先保存当前草稿，再重新打开页面加载 10 条列表。新增事件从 Z0006 开始。
原人工标注在 `benchmark/atlas/gold.jsonl`，GPT-5/Qwen 预测在 `benchmark/atlas/predictions.jsonl`，
此次没有改写这些文件、底图版本或历史实验。新增事件需要先人工审核，才会进入下一份 VLM 输入包。

10 条是候选数，不是 10 条有效样本。当前底图没有覆盖 Regensdorf，已有 Z0003 的 outside_map
判定应保留；Z0006、Z0007、Z0008 也需要检查裁切边缘。不要为了凑数把范围外目标拖进图内。
若要得到 10 条 accepted，需在审核后继续补充候选，或另建更大底图版本并重新核对相应几何。

`zurich_pilot_10.jsonl` 是当前唯一加载的苏黎世候选文件。
`zurich_pilot_5.jsonl` 仅保留为不可变的首批快照及回归检查依据，不会重复加载。

## 旧参考图标注入口

[欧洲地图 GUI](GUI_README.md) 与下方旧终端方式仍可使用，但它们标的是原参考图，
不是地图集的干净底图。两种坐标和输出不能混用；当前实验请使用上面的地图集入口。

在项目根目录运行，复用现有入口并覆盖输入、输出：

```bash
bash benchmark/run_napoleon_annotation.sh \
  --input benchmark/zurich_pilot_10.jsonl \
  --output benchmark/zurich_annotations.jsonl \
  --annotator eric
```

复查时在同一命令末尾加 `--review`；从第三条开始加 `--start 2`。
证据、几何类型和要素词表遵循 [统一标注说明](NAPOLEON_ANNOTATION.md)。
标注界面显示英文译文与问题；法文原文保存在每条记录的 `source_text`，
完整原网页另存于 [原文快照](sources/zurich_thiers_1839.html)。

## 本次问题

| ID | 指定事件和时间 | 候选要素 | 主要检查点 |
|---|---|---|---|
| Z0001 | 最初 600 名法军渡河后、增援前的登陆位置 | river_bank | 接收岸，不是出发岸、村中心或后来架桥的位置 |
| Z0002 | Gazan 增援后攻击时，俄军三个营的防守位置 | woodland | 林地，不是修道院；地图可能无法支持林地边界 |
| Z0003 | 主力渡河后 Bontemps 旅的部署地点 | settlement | 明确地名对照题，区分该旅与 Oudinot 主力 |
| Z0004 | Massena 调动之前 Klein 师的位置 | settlement | 明确地名对照题，区分出发前位置与后续目的地 |
| Z0005 | Oudinot 溯河推进时夺取的城后高地 | high_ground | 高地，不是营地或道路；“后方”不等于北方 |
| Z0006 | 首批渡河之前，法军在 Dietikon 附近集结的出发岸 | river_bank | 与 Z0001 的接收岸不同；不把村中心当上船点，检查裁切边缘 |
| Z0007 | Mortier 初次进军、被迫后撤之前途经的聚落 | settlement | Wollishofen 的聚落级地名对照题，不声称精确交战位置 |
| Z0008 | Oudinot 溯河时夺取的小营地 | other | Hong/Höngg 附近营地，不是 Z0005 高地；营地边界不明可判 ambiguous |
| Z0009 | Oudinot 夺取、通往德国并承担俄军退路的道路 | road | 只标可识别的苏黎世附近路段，不标 Winterthur 城区或臆测截击点 |
| Z0010 | Korsakoff 发现困境后、翌晨战斗前移驻的城区 | settlement | 区分利马特河两侧城区、调动前后及之后出城撤退的阶段 |

上表是审核提示，不是答案。Z0009 建议 line，其余建议 polygon，但可依据证据调整。
不得用村中心点替代未知的部署位置。若只能支持聚落级位置，证据中明确其粒度。
四条明确地名锚定题（Z0003、Z0004、Z0007、Z0008）作为对照，另六条为关系题。
营地题虽有明确地名，精确营地仍可能无法定位；题型分类不代表标注已经合格。
Z0006/Z0001 可检查出发岸与接收岸的区分；Z0008/Z0005/Z0009 可检查同段落中营地、
高地和道路三个目标的区分；Z0010 检查时间阶段和相对河岸的理解，不要求恢复完整移动轨迹。

## 地图审查

- [原图](https://www.napoleon-series.org/images/military/maps/miscellaneous/zurich2.jpg)
  来自 [Napoleon Series 地图档案](https://www.napoleon-series.org/military-information/maps/)。
- 本地文件：`maps/zurich_pilot/zurich2.jpg`，原始 JPEG，2177 × 1699；未裁切、增强或重绘。
- 图题为 1799 年 9 月 25–26 日苏黎世战役，印刷比例尺为 1:100,000。
  图例区分 25 日早晨阵位与法军渡河/推进箭头，不是单一时间截面的所有位置。
- 已目视确认 Dietikon、Kl. Fahr、Regensdorf、Altstetten、Höngg、Zürich、
  Limmat 和主要山脊可辨；小林地、登陆点与阵地边界仍有限。
- 图中有部队姓名、阵位和推进箭头，会提示答案。本版只能作为人工候选审核图；
  正式评测必须制定视觉提示控制，并重新确认处理后仍能定位。
- 具体出版年份、地图来源归属和再分发权利尚未确认，不能将其称为 1799 年原始测绘图。
- 图片 SHA-256：`66447450d37d58b900744a6ce90e4f6b60debf806db2b6c543c307985342c8e5`。

## 文本证据与限制

来源为 Adolphe Thiers，*Histoire de la Révolution Française*，第十卷，
第九版（1839），第 XVIII 章的四个段落（快照 `<p>` 索引 347、348、349、351）。
[Project Gutenberg 原文](https://www.gutenberg.org/files/13607/13607-h/13607-h.htm)。

- `source_text` 是完整法文段落，仅合并 HTML 排版空白，没有改写。
- `source_paragraph_index` 是快照中从 0 开始的 HTML `<p>` 索引；
  `source_section` 另给章节和段首，便于人工检索。
- `event_text` 为助手所作完整英文译文，不是历史原文或经人工认可的翻译。
  `translation_review`、`historical_review` 和 `map_text_alignment_review` 均为 pending。
- 这是 1839 年的事后叙述，不是目击者报告。其赞颂性措辞、伤亡数字和人物归属
  都只是该作者的陈述，不代表已经交叉核实。先评估“依据给定材料能否定位”。
- Hong / Höngg、Closter-Fahr / Kl. Fahr、Vintherthur / Winterthur 是审核时需核对的
  拼写对应；不自动加入模型输入，避免额外降低任务难度。
- Z0001–Z0003 与 Z0006 共用段落 347；Z0004/Z0007 共用 348；
  Z0005/Z0008/Z0009 共用 349；Z0010 使用 351。十条共用一张地图，不是十份独立地理样本。
  `split_group=zurich_1799`；以后加入第一次战役或同地区地图时，保守地沿用此组，
  不把共享地理底图和原文段落拆进训练、测试两侧。
- 原文明确位置的题可作为对照；空间约束不足的题应标 ambiguous 或 unlocatable，
  不用扩大容差来凑 accepted。只有独立人工审核才能确定是否合格。
- 正式模型输入应只有选定的地图、正文和问题；不得传入 `place`、要素建议、
  审核提示、来源段首、人工证据或标准几何等辅助字段。

## 旧参考图标注导出

地图集的干净底图流程请使用页面上的“VLM 输入包”和“人工答案”，只导出当前版本的 accepted。
以下命令仅用于旧参考图标注文件，不会读取 `atlas/gold.jsonl`：

标注完成后运行：

```bash
.venv/bin/python benchmark/assemble_geo_benchmark.py \
  --candidates benchmark/zurich_pilot_10.jsonl \
  --annotations benchmark/zurich_annotations.jsonl \
  --output benchmark/zurich_reviewed.jsonl
```

此命令只导出最新 accepted 标注，不等于通过翻译、史实、版权或正式评测验收。
不使用旧的米制点定位脚本评价本组像素区域标注。
