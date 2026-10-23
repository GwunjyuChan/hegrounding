# 苏黎世十题：Qwen3-VL 普通版、Thinking 与 GPT-6 对照

实验日期：2026-10-13（Europe/Zurich）。Qwen 两组为本轮非量化 FP16 实跑；GPT-6 为 2026-10-07/08 历史结果，本轮没有调用付费 API。

**本报告使用仍有争议的旧人工标签，只能解释为诊断结果，不是正式准确率或模型排名。**

[逐题高清交互对比](comparison.html) · [原定实验协议](../PROTOCOL.md) · [结构化结果](diagnostics.json)

## 摘要

- Thinking 主实验：0 条有效几何、0 条合法拒答、10 条输出失败。8192-token 补充测试：0/10 条可解析最终答案（包含拒答）。
- 没有最终坐标时，无法计算 Thinking 的空间误差；不能把 N/A 写成 0% 定位准确率，也不能声称普通版在空间推理能力上胜过 Thinking。
- Instruct 与 GPT-6 共同可评的 3 个点题，平均偏差分别为 323.1 px 和 28.9 px。这只是对暂定人工点的偏差，不是经过仲裁的真实定位误差。
- 这轮首先暴露了受限预算、greedy 解码下的任务完成问题。下一步优先验证推荐采样设置和坐标遵循能力，不宜直接扩大实验规模或据此做模型排名。

## 1. 实验条件

- 两套官方 8B 权重，均以 float16 在同一 Mac 的 MPS 上运行，一次加载一个模型；不使用 4-bit 权重。BF16 存储权重加载成 FP16，并非 FP32。
- 沿用冻结的十个问题、英文原文和提示词。原图 1538×1754，仅右/下补白至 1568×1760，do_resize=False；各题实际输入尺寸及像素哈希均已校验。
- 主实验均为 4096 输出 token 上限。Qwen 两组 greedy 解码；Thinking 的思考 token 也占用此预算，只有结束思考后的最终 JSON 参与评分。
- GPT-6 使用同一原 PNG 与任务，4096 上限、默认推理参数；其内部图像处理与计算量不受我们控制，因此不是严格等算力比较。
- 不提供人工标注、不搜索、不修正坐标、不按回答质量挑选重跑。Z0009/Z0010 沿用实验前排除规则；Z0003 单列图外拒答。

## 2. 主实验输出与开销

| 模型 | 有效几何 | 合法拒答 | 格式/输出失败 | 达到 token 上限 | 总推理秒数 | 输出 tokens |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3-VL-8B Instruct | 9/10 | 0 | 1 | 1 | 482.8 | 4519 |
| Qwen3-VL-8B Thinking | 0/10 | 0 | 10 | 10 | 3501.3 | 40960 |
| GPT-6 Astra (历史) | 8/10 | 1 | 1 | 0 | 108.0 | 2286 |

耗时不含下载和模型加载；本机与云端耗时仅作工作流开销记录，不能用于比较硬件效率。合法几何不等于正确位置。

失败分类：Qwen3-VL-8B Instruct：JSONDecodeError 1 条；Qwen3-VL-8B Thinking：IncompleteThinking 10 条；GPT-6 Astra (历史)：ValueError 1 条。
IncompleteThinking 表示输出未出现完整思考结束标记，没有可评分的最终答案；不能用其草稿位置计算误差。

## 3. 对暂定人工标签的空间诊断

| 模型 | 可评点数/5 | 点误差均值 px | 点误差中位数 px | 区域命中/可评点数 | 图外题 Z0003 |
|---|---:|---:|---:|---:|---:|
| Qwen3-VL-8B Instruct | 5/5 | 418.9 | 346.1 | 0/2 | 错误定位 |
| Qwen3-VL-8B Thinking | 0/5 | N/A | N/A | N/A (0/2 可评) | 无最终答案 |
| GPT-6 Astra (历史) | 3/5 | 28.9 | 20.9 | 2/2 | 正确拒答 |

各行可评点子集不同，不可直接用均值相除声称提升。区域题共两题，命中分母只计算有效点预测；其他几何不自动取中心。失败、拒答和未评分项不记为零误差。

![逐题点误差](point_errors.png)

### 同题配对

- Qwen3-VL-8B Instruct / Qwen3-VL-8B Thinking，共同有效点 n=0：无。
- Qwen3-VL-8B Instruct / GPT-6 Astra (历史)，共同有效点 n=3：Z0002, Z0004, Z0006。Qwen3-VL-8B Instruct 323.1 px；GPT-6 Astra (历史) 28.9 px
- Qwen3-VL-8B Thinking / GPT-6 Astra (历史)，共同有效点 n=0：无。
- Qwen3-VL-8B Instruct / Qwen3-VL-8B Thinking / GPT-6 Astra (历史)，共同有效点 n=0：无。

## 4. 逐题结果

| 事件 | Instruct | Thinking | GPT-6 历史 | 原像素图 |
|---|---|---|---|---|
| Z0001 | 距人工点 383.3 px | IncompleteThinking | ValueError | [查看](Z0001_detail.png) |
| Z0002 | 距人工点 346.1 px | IncompleteThinking | 距人工点 18.2 px | [查看](Z0002_detail.png) |
| Z0003 | 图外仍定位 | IncompleteThinking | 图外拒答 | [查看](Z0003_detail.png) |
| Z0004 | 距人工点 280.6 px | IncompleteThinking | 距人工点 20.9 px | [查看](Z0004_detail.png) |
| Z0005 | 距人工点 742.1 px | IncompleteThinking | 几何不同/无可用真值，未评分 | [查看](Z0005_detail.png) |
| Z0006 | 距人工点 342.5 px | IncompleteThinking | 距人工点 47.5 px | [查看](Z0006_detail.png) |
| Z0007 | 区域外 419.3 px | IncompleteThinking | 区域内 0.0 px | [查看](Z0007_detail.png) |
| Z0008 | 区域外 375.9 px | IncompleteThinking | 区域内 0.0 px | [查看](Z0008_detail.png) |
| Z0009 | JSONDecodeError | IncompleteThinking | 已运行，不评分 | [查看](Z0009_detail.png) |
| Z0010 | 已运行，不评分 | IncompleteThinking | 已运行，不评分 | [查看](Z0010_detail.png) |

图中红色十字/边界为旧人工标签，绿色为 Instruct，紫色为 Thinking，蓝色为 GPT-6。图件保留原像素局部裁切；交互查看器支持原比例查看。

## 5. 8192-token 补充实验

按运行前规则，仅对主实验达到上限的请求增加预算，两个版本采用相同规则；下表不回填主实验结果。

| 模式 | 事件 | 状态 | 输出 tokens | 思考 tokens | 再次达到上限 | 秒数 | 独立空间诊断 |
|---|---|---|---:|---:|---|---:|---|
| instruct | Z0009 | error JSONDecodeError | 8192 | 0 | True | 716.8 | JSONDecodeError |
| thinking | Z0001 | error IncompleteThinking | 8192 | 8192 | True | 703.7 | IncompleteThinking |
| thinking | Z0002 | error IncompleteThinking | 8192 | 8192 | True | 702.9 | IncompleteThinking |
| thinking | Z0003 | error IncompleteThinking | 8192 | 8192 | True | 702.7 | IncompleteThinking |
| thinking | Z0004 | error IncompleteThinking | 8192 | 8192 | True | 699.8 | IncompleteThinking |
| thinking | Z0005 | error IncompleteThinking | 8192 | 8192 | True | 698.5 | IncompleteThinking |
| thinking | Z0006 | error IncompleteThinking | 8192 | 8192 | True | 702.9 | IncompleteThinking |
| thinking | Z0007 | error IncompleteThinking | 8192 | 8192 | True | 700.0 | IncompleteThinking |
| thinking | Z0008 | error IncompleteThinking | 8192 | 8192 | True | 698.6 | IncompleteThinking |
| thinking | Z0009 | error IncompleteThinking | 8192 | 8192 | True | 698.8 | IncompleteThinking |
| thinking | Z0010 | error IncompleteThinking | 8192 | 8192 | True | 706.2 | IncompleteThinking |

补充测试只覆盖各自触及上限的题目，两种模式的补充子集可能不同。上面的对比图与主表仅展示 4096-token 主实验，不混入补充预测。

## 6. 具体错误与下一步

### Z0004：从文本识别地名，不等于能在地图上定位

目标是 Klein 出发前所在的 Altstetten。Thinking 的原始输出已提取出该地名，随后反复尝试寻找地图位置，但主实验没有提交最终 JSON。这是对中间输出的定性观察，不把草稿当作成功答案。下图只绘制正式解析成功的坐标；Thinking 没有预测图层。

![Z0004 原像素局部对照](Z0004_detail.png)

### Z0003：缺少图上证据时的拒答

该题文本目标为 Regensdorf，冻结标注将其记为图外。Instruct 仍给出位置；历史 GPT-6 返回合法拒答；Thinking 主实验被截断。三种结果必须分别记录，未完成不等于正确拒答。

### Z0009：生成失控不只是格式问题

Instruct 在道路问题上持续生成规律递增的坐标。8192-token 输出已延伸到 x 约 29,000，而地图宽度只有 1,538；同时 JSON 尚未闭合。因此，补一个括号或只增加预算不足以让这条输出成为合法路线。本轮不裁剪、不截取前几个点、不修补输出。该题的旧人工真值也不适合道路目标，因此按预先规则不计空间分数。

### 建议的下一轮

1. 先选少量固定诊断题，验证官方推荐的非 greedy 采样设置，并单独记录解码参数、种子、终止原因和完整输出。它是新的探索性实验，不能覆盖本轮失败记录。
2. 增加明确地名定位检查，核对模型是否真正遵循原图像素坐标，而不是事后按人工答案缩放或移动预测点。
3. 冻结经过人工仲裁的答案和几何粒度，再扩大到不同地图；当前仅三个共同有效点，不宜计算总体提升倍数。

配置来源：[Qwen3-VL 官方仓库的推理参数](https://github.com/QwenLM/Qwen3-VL)。官方推荐采样与更长生成预算，本轮为沿用历史控制条件的 greedy 设置；两者不可混称。

## 7. 解释边界

- Instruct 与 Thinking 是不同训练权重，不是同一模型的纯开关消融；差异不能全部归因于输出了思考过程。
- 本次 greedy、受限预算是受控诊断配置，不等同于作者推荐的采样配置与更长输出预算；截断尤其不能等同于模型不知道答案。
- 旧人工标注存在点/面粒度和主体混淆等问题。本轮不以 GPT-6 或未经审核的 AI 候选替换真值；距离缩短只意味着更接近旧标签。
- 十题共享一张地图和四段文本，缺乏独立战场覆盖；不能从这一轮证明一般模型优劣或论文方法有效性。
- 当前网页底图、人工审核记录和旧实验输出均未修改。

## 8. 审计文件

- [Instruct 预测](../instruct/predictions.json) · [原始输出](../instruct/predictions.attempts.jsonl)
- [Thinking 预测](../thinking/predictions.json) · [原始输出](../thinking/predictions.attempts.jsonl)
- [Instruct 8192 补充预测](../instruct_8192/predictions.json) · [原始输出](../instruct_8192/predictions.attempts.jsonl)
- [Thinking 8192 补充预测](../thinking_8192/predictions.json) · [原始输出](../thinking_8192/predictions.attempts.jsonl)
- [GPT-6 历史预测](../../zurich10_gpt6_astra_20261007/predictions.json)
- [冻结旧人工标签](gold_snapshot.json) · [结构化统计与来源哈希](diagnostics.json)

模型资料：[Instruct](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct)、[Thinking](https://huggingface.co/Qwen/Qwen3-VL-8B-Thinking)。
