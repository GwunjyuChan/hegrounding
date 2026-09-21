# Qwen3-VL：直接定位与两阶段定位

## 实验设计

- 直接：原文 + 原问题 + 干净底图 → 几何。
- 两阶段：原文 + 原问题 → 地点答案/证据/不确定性；再将这三项 + 原问题 + 同一底图 → 几何。
- 第二步不含完整原文，不共享第一步对话状态；引用证据来自模型输出，不经人工修正。
- 同一本地模型缓存、greedy 解码、图像预处理、定位 prompt 与定位输出预算；交替安排两种方法先后顺序。
- 两阶段多一次调用，并非等计算量对比。原始像素坐标不做缩放纠正，不自动重试。
- 真值只在离线评分进程读取；推理进程不读取人工几何。
- 底图 `2ae3fca4eb15dced41f82401`；模型 `Qwen/Qwen3-VL-8B-Instruct`；定位上限 4096 token，文本上限 4096 token。

## 返回与成本

| 方法 | 有效几何 | 拒答 | 错误 | 调用数 | 总推理耗时（秒） | 总 token |
|---|---:|---:|---:|---:|---:|---:|
| direct | 8/10 | 0 | 2 | 10 | 182.2 | 31723 |
| two_stage | 9/10 | 0 | 1 | 20 | 234.4 | 36026 |

耗时不含模型加载/报告绘制；两阶段包含第一步。合法几何不代表位置正确。

## 逐条定位诊断

| 事件 | 直接 | 两阶段 |
|---|---|---|
| Z0001 | 距人工点 358.6 px | 距人工点 358.6 px |
| Z0002 | 距人工点 348.3 px | 距人工点 205.0 px |
| Z0003 | ValueError | 图外仍定位 |
| Z0004 | 距人工点 279.6 px | 距人工点 312.2 px |
| Z0005 | 距人工点 742.9 px | 距人工点 726.2 px |
| Z0006 | 距人工点 390.8 px | ValueError |
| Z0007 | 区域外 425.0 px | 区域外 414.4 px |
| Z0008 | 区域外 349.5 px | 区域外 508.6 px |
| Z0009 | ValueError | 已运行，不评分 |
| Z0010 | 已运行，不评分 | 已运行，不评分 |

## 配对比较

共同成功返回点、且人工真值为点的样本：n=4，Z0001, Z0002, Z0004, Z0005。
- direct：平均 432.4 px；中位数 353.5 px。
- two_stage：平均 400.5 px；中位数 335.4 px。
- 两阶段偏差更小 2 条，更大 1 条，相同 1 条。
- direct：预测点落入人工区域 0/2（不是多边形 IoU）。
- two_stage：预测点落入人工区域 0/2（不是多边形 IoU）。

共同成功子集可能有选择偏差，须同时看所有请求的错误/拒答，不能把失败记为零距离。
排除评分事件：Z0009, Z0010。

排除条目应先复核目标和几何粒度；排除不等于模型错误，具体原因见工作流说明。
范围外条目单独检查拒答；第一步拒答传播到最终输出不等于视觉阶段正确识别了图外地点。
不报告混合几何总准确率或事后挑选命中阈值；点和区域诊断分开，其他几何组合仅展示。
同底图的关联事件和暂定真值不足以证明一般性提升；地图和文本翻译也仍需审核。

## 中间地点答案（未经人工修改）

### Z0001

the opposite bank of the Limmat, near the plateau of Closter-Fahr

不确定性：未声明

证据：
- Six hundred men boldly embarked and reached the opposite bank. They immediately attacked and scattered the enemy skirmishers.
- Korsakoff had stationed three battalions with artillery there, on the plateau of Closter-Fahr.
- Our artillery, skilfully directed, soon silenced the Russian guns and protected the successive crossings of our advance guard.

人工审核：待审核

### Z0002

in a wood on the plateau of Closter-Fahr

不确定性：未声明

证据：
- Korsakoff had stationed three battalions with artillery there, on the plateau of Closter-Fahr.
- They had established themselves in a wood and defended it bravely.

人工审核：待审核

### Z0003

Regensdorf

不确定性：未声明

证据：
- Bontemps's brigade was stationed at Regensdorf to face Durasof should he move up from the lower Limmat.

人工审核：待审核

### Z0004

Altstetten

不确定性：未声明

证据：
- Arriving at that moment, Massena set Klein's division, which was at Altstetten, in motion.

人工审核：待审核

### Z0005

the heights behind Zurich

不确定性：未声明

证据：
- Oudinot, with his fifteen thousand men, continued moving upstream along the Limmat. He had captured the small camp at Hong, as well as the heights behind Zurich, and had seized the main road to Vintherthur

人工审核：待审核

### Z0006

on the bank near the village of Dietikon

不确定性：未声明

证据：
- Preparations for the crossing had been made near the village of Dietikon with extraordinary care and secrecy.
- By morning they were afloat, and the troops were silently drawn up on the bank.

人工审核：待审核

### Z0007

Wollishofen

不确定性：未声明

证据：
- Mortier had advanced towards Zurich by way of Wollishofen

人工审核：待审核

### Z0008

Hong

不确定性：未声明

证据：
- He had captured the small camp at Hong, as well as the heights behind Zurich, and had seized the main road to Vintherthur

人工审核：待审核

### Z0009

the main road to Vintherthur, which led into Germany

不确定性：未声明

证据：
- Oudinot, with his fifteen thousand men, continued moving upstream along the Limmat.
- He had captured ... the main road to Vintherthur, which led into Germany and was the only route by which the Russians could retreat.

注意：部分引用不是逐字原文，已原样传递，未人工纠正。

人工审核：待审核

### Z0010

behind the Limmat

不确定性：未声明

证据：
- Korsakoff had finally realized his situation and had moved his troops into the other part of Zurich, behind the Limmat.

人工审核：待审核

## 文件

- [结构化诊断](diagnostics.json)、[人工快照](gold_snapshot.json)。
- [直接预测](../direct/predictions.json)、[两阶段预测](../two_stage/predictions.json)。
- [第一步原始回答](../stage1/answers.json)。各阶段 attempts.jsonl 保存实际输入、原始输出、耗时和用量。
- 两份预测 JSON 使用不同方法标签，可分别导入地图集，不覆盖原 Qwen 或 GPT-5 结果。
- [Z0001 对照图](Z0001.png)
- [Z0002 对照图](Z0002.png)
- [Z0003 对照图](Z0003.png)
- [Z0004 对照图](Z0004.png)
- [Z0005 对照图](Z0005.png)
- [Z0006 对照图](Z0006.png)
- [Z0007 对照图](Z0007.png)
- [Z0008 对照图](Z0008.png)
- [Z0009 对照图](Z0009.png)
- [Z0010 对照图](Z0010.png)
