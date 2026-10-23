# Event Grounding Benchmark — Question & Annotation Guidelines (v0.1, 2026-10-19)

中英对照。英文版用于论文和 benchmark 文档；中文版是给自己审核时快速对照用的。**带 ⚠ 的条目是需要导师确认的参数，不是已经定下的标准。**

---

## 1. Task / 任务

**EN.** Given (a) a historical map image, (b) a passage from a historical source describing a battle, and (c) a question about one specific step of that event, the model outputs the spatial footprint of the asked step on the map as a point, line, or polygon in image pixels, or `null` if the asked location is not on the map.

The benchmark targets **event details** (where a unit stood, landed, attacked, crossed, retreated to), not the full extent of a battle and not its temporal dynamics.

**中文。** 输入：历史地图 + 一段描述战役的史料原文 + 针对事件中**某一步**的问题。输出：该步骤在地图上的点、线或面（像素坐标）；不在图内就输出 `null`。只定位事件细节，不定位整场战役的范围，也不还原动态过程。

## 2. Input text rules / 输入文本规则

| # | Rule (EN) | 规则（中文） |
|---|---|---|
| T1 | The passage must be a **verbatim source paragraph** (or a faithful translation of one), with author, title, year and page/URL. | 必须是**史料原文**或忠实翻译，并注明作者、书名、年份、页码或 URL。 |
| T2 | No AI paraphrase, no map captions, no legend text, and no description written by looking at the map. | 不用 AI 改写，不用图注、图例，也不用"看着地图写出来"的描述。 |
| T3 | Trimming is allowed (an ellipsis marks a cut), but no added words. Keep spatial relations that are in the original (east bank, behind the village). | 可以删节（用省略号标注），但不能加字。原文里本来就有的空间关系（东岸、村后）要保留。 |
| T4 | Record the source type: primary (dispatch, report, memoir) or secondary (later history). | 记录来源类型：一手（战报、报告、回忆录）或二手（后世战史）。 |

## 3. Question rules / 问题规则

| # | Rule (EN) | 规则（中文） |
|---|---|---|
| Q1 | Ask about **who did what**, and identify the step by actor, action and time (e.g. *"Where did the first six hundred French soldiers land?"*). | 用"谁、做了什么、什么时候"来指定步骤，例如"最先渡河的六百名法军在哪里登陆？" |
| Q2 | **Never refer to the map**: no legend letters (A, a.a, k.k), "labelled", "shown", "plate", "mapped", colours, symbols, or numbered works. | **不能提到地图本身**：图例字母（A、a.a、k.k）、"labelled"、"shown"、"plate"、"mapped"、颜色、符号、编号工事都不行。 |
| Q3 | **Do not name the answer place** when the passage names it; the model must get it from the text. Names needed only to identify the event (the battle, a unit) are fine. | 如果原文里有答案的地名，**问题里就不要再写出来**，要让模型从文本中得出。用来识别事件的名字（战役名、部队名）可以保留。 |
| Q4 | **No disambiguation hints** that do the model's reasoning for it: "not the whole ridge", "rather than the town bridge", "distinct from …", "not the opposite bank". | **不要替模型排除干扰项**："not the whole ridge"、"rather than the town bridge"、"distinct from …"、"not the opposite bank" 这类都删掉。 |
| Q5 | Do not reveal the geometry type or shape ("mark the road segment", "the island"), except the generic "Mark the location". The output schema already allows any type. | 不透露几何类型或形状（"mark the road segment"、"the island"），统一用"Mark the location"这类说法。输出格式本身允许任何类型。 |
| Q6 | One question = one target. If the passage mentions several candidate places, the question must be answerable by **reading** which one fits. | 一题只问一个目标。原文提到多个地点时，必须靠**读懂文本**才能判断是哪一个。 |

### Self-checks before accepting / 接受前的自检
1. **Text-ablation test.** Delete the passage. If the question plus the map is still enough to answer, rewrite the question or drop the item.
   **删文本测试。** 把原文删掉，只看问题和地图还能答出来，就要重写或剔除。
2. **Map-ablation test.** If the passage alone fixes the answer to a modern coordinate without needing the map (e.g. just a town name), the item is fine, but tag it `place_lookup`. Items whose answer depends on map features (a ridge, a ford, a wood) are tagged `map_reasoning`.
   **删地图测试。** 只凭原文就能查到现代坐标（比如只是一个镇名）也可以用，但标为 `place_lookup`。答案要靠地图上的地形或地物（山脊、渡口、树林）才能确定的，标为 `map_reasoning`。
3. **Can I defend it?** If I cannot point to the sentence in the source *and* the feature on the map that justify the geometry, drop it.
   **能不能说清依据？** 指不出原文里的哪句话、地图上的哪个地物支持这个几何，就剔除。

## 4. Geometry rules / 几何规则

| Type | When (EN) | 何时使用 |
|---|---|---|
| point | Small target with no meaningful extent at map scale: bridge, ford, battery, farm, single village used as a position. | 在地图比例下没有明显范围的目标：桥、渡口、炮台、农庄、作为阵地的单个村庄。 |
| line | Linear target: road, route of approach, river bank segment, wall, entrenchment, front line. | 线状目标：道路、进攻路线、河岸段、城墙、壕沟、战线。 |
| polygon | Area with a defensible boundary on the map: heights, wood, village built-up area, camp, deployment area. | 在图上有可辨边界的区域：高地、树林、村庄建成区、营地、部署区域。 |

- Draw along visible map features (contours, road, wood edge, built-up area). AI candidates are drafts only. / 沿图上可见的地物画（等高线、道路、林缘、建成区）。AI 候选只作草稿。
- If the boundary is genuinely unknown, do not draw a huge polygon; mark `ambiguous` and drop it from the scored set. / 边界确实不知道时不要画大多边形，标为 `ambiguous`，不进入评分集。
- Record: `geometry_source` (human / human-edited AI), `confidence 1–5`, `text_evidence` (quoted sentence), `map_evidence`. / 记录 `geometry_source`（人工 / 人工修改的 AI 候选）、置信度 1–5、`text_evidence`（引用原句）、`map_evidence`。
- Only confidence ≥ 4 enters the main test set; confidence 3 goes into a reported "hard" subset. / 置信度 ≥ 4 进入主测试集，置信度 3 单列为"难例"子集一起报告。⚠

## 5. Scoring / 评分（`benchmark/eval_geometry.py`）

All gold and predicted geometries are converted to regions on the image, then scored with **IoU**:

| Geometry | Region |
|---|---|
| polygon | its interior |
| line | buffered with half-width = **1%** of the image diagonal ⚠ |
| point | disc with radius = **2%** of the image diagonal ⚠ |

- Report **hit@IoU≥0.5** and **hit@IoU≥0.75**, plus mean IoU, overall and per gold type. ⚠
- One metric for all types answers the fairness concern from the 15 Oct meeting. A point dropped inside a large gold polygon gets a low IoU, not a hit; point-in-region is reported only as a secondary diagnostic.
- `null` gold + `null` prediction = correct abstention; any other `null` mismatch, invalid JSON, or wrong coordinate format scores IoU 0. Outputs are never repaired.
- Thresholds and buffer sizes must be **frozen before** the main model runs.

**中文要点：** 线加缓冲带、点画成圆，全部用 IoU 统一评分，报告 0.5 / 0.75 两档。点落在大面里只会得到很低的 IoU，不算命中。格式错误一律记 0 分，不帮模型修正输出。参数要在正式跑模型之前冻结。

## 6. Data provenance / 数据来源记录
- `ai_assisted: true/false`, and whether the reviewer accepted the AI candidate as is or edited it (report the % edited).
- Keep ~15–20 items **blind-annotated** (annotated without seeing any AI or model output) and ~20 items **double-annotated** by a second person (supervisor or labmate) to report agreement.
- Items from the same battle/map never cross train/test splits.

**中文：** 记录是否用了 AI 辅助，以及是"直接接受"还是"修改过"（最后报告修改比例）。留 15–20 条盲标（不看任何 AI 或模型输出），再请第二个人（导师或同门）对约 20 条独立标注，用来报告一致性。同一战役或同一张图的样本不能拆到训练集和测试集两边。
