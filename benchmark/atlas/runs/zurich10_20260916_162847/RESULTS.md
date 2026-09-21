# 苏黎世十条候选：GPT-5 / Qwen3-VL 验证

本轮是相对人工快照的诊断，不是经过独立验收的 benchmark 精度。

## 配置

- 底图版本：`2ae3fca4eb15dced41f82401`；尺寸 1538 × 1754 px。
- 图片 SHA-256：`fc5f835f11cd6f7cafefc7183b57d10c0911372149a1c2077f662a6d70570aec`。
- 两模型使用同一个 input.zip，含全部十条；与网页默认的 accepted-only 导出不同，另纳入 Z0003 图外拒答对照。
- 模型只收到干净 PNG、英文正文、问题和像素坐标规则；人工答案、审核状态、排除理由及作战图没有发送。
- GPT-5：Responses API，最多 4096 输出 token（含推理），超时 120 秒，不自动重试；调用参数沿用上一轮。
- Qwen/Qwen3-VL-8B-Instruct：本机缓存，Transformers / MPS float16，greedy，最多 4096 新 token。
- 英文翻译及历史定位尚待独立复核；不把同图十条看成十张独立地图。

## 执行结果

有效几何只表示格式、顶点及图像边界校验通过，不表示位置正确。

| 模型 | 请求 | 有效几何 | 拒答 | 调用/解析/几何错误 |
|---|---:|---:|---:|---:|
| gpt-5 | 10 | 9 | 0 | 1 |
| Qwen/Qwen3-VL-8B-Instruct | 10 | 8 | 0 | 2 |

## 逐条诊断

距离单位均为原图像素；不同几何类型不合并成一个准确率。
Z0010 在查看模型结果之前已标记为人工目标不匹配，从空间汇总中排除。

| ID | 人工标注 | GPT-5 | Qwen3-VL |
|---|---|---|---|
| Z0001 | point | 距人工点 924.9 px | 距人工点 358.6 px |
| Z0002 | point | 无效输出/生成失败 | 距人工点 348.3 px |
| Z0003 | outside_map | 图外仍给出坐标 | 无效输出/生成失败 |
| Z0004 | point | 距人工点 182.5 px | 距人工点 279.6 px |
| Z0005 | point | 距人工点 244.9 px | 距人工点 742.9 px |
| Z0006 | point | 距人工点 786.3 px | 距人工点 390.8 px |
| Z0007 | polygon | 区域外 85.5 px | 区域外 425.0 px |
| Z0008 | polygon | 区域外 103.9 px | 区域外 349.5 px |
| Z0009 | point | 几何类型不同，暂不评分 | 无效输出/生成失败 |
| Z0010 | line | 已运行；人工目标不匹配，不评分 | 已运行；人工目标不匹配，不评分 |

## 汇总和限制

- gpt-5：有效点对点 n=4，均值 534.7 px，中位数 515.6 px。失败/拒答不记为零距离。
- gpt-5：点落入人工区域 0/2；这是点对区域诊断，不是区域 IoU。
- Qwen/Qwen3-VL-8B-Instruct：有效点对点 n=5，均值 424.1 px，中位数 358.6 px。失败/拒答不记为零距离。
- Qwen/Qwen3-VL-8B-Instruct：点落入人工区域 0/2；这是点对区域诊断，不是区域 IoU。
- 两模型都有效的共同点样本（Z0001, Z0004, Z0005, Z0006，n=4）：
  gpt-5 平均 534.7 px，中位数 515.6 px。此项仅比较成功返回点的交集，存在成功样本筛选偏差。
  Qwen/Qwen3-VL-8B-Instruct 平均 443.0 px，中位数 374.7 px。此项仅比较成功返回点的交集，存在成功样本筛选偏差。
- 点/线容差全部为 0 px，未设事后阈值，也未使用旧 500 米标准；不报告混合几何总准确率。
- Z0010 问的是 Korsakoff 调动后在利马特河另一侧的城区；当前证据/线条描述 Durasof 的撤退道路，需独立重标。
- Z0009 问道路路段，人工真值却是单点；其点距离仅供排查，不足以验证完整道路定位。
- Z0002 的防守林地与高地、Z0001/Z0006 的接收岸/出发岸仍建议复核；本轮没有替用户改标注。
- 本轮底图、裁切和人工答案不同于五条版本，不能直接把数值变化解释为模型能力变化。

## 错误与使用量

- gpt-5 Z0002：JSONDecodeError；输出预算全部用于推理，未返回可解析答案。
- gpt-5 token：input=10583，output=27696，total=38279。
- Qwen/Qwen3-VL-8B-Instruct Z0003：ValueError；请对照原始响应检查几何有效性/越界，不裁剪或缩放修正。
- Qwen/Qwen3-VL-8B-Instruct Z0009：ValueError；请对照原始响应检查几何有效性/越界，不裁剪或缩放修正。
- Qwen/Qwen3-VL-8B-Instruct token：input=30831，output=892，total=31723。

token 用量不等于账单金额。Qwen 离线推理未调用付费 API。

## 文件

- [冻结输入包](input.zip)、[人工答案快照](gold_snapshot.json)、[运行前审核说明](review_snapshot.json)。
- [GPT-5 预测](gpt5/predictions.json)、[原始响应](gpt5/predictions.attempts.jsonl)。
- [Qwen 预测](qwen3vl8b/predictions.json)、[原始响应](qwen3vl8b/predictions.attempts.jsonl)。
- [逐项诊断 JSON](diagnostics.json)。
- 对照图：左 GPT-5 蓝色，右 Qwen 绿色，红色为保存的人工答案；无效输出不绘制成有效标注。
- [Z0001 对照图](Z0001_comparison.png)
- [Z0002 对照图](Z0002_comparison.png)
- [Z0003 对照图](Z0003_comparison.png)
- [Z0004 对照图](Z0004_comparison.png)
- [Z0005 对照图](Z0005_comparison.png)
- [Z0006 对照图](Z0006_comparison.png)
- [Z0007 对照图](Z0007_comparison.png)
- [Z0008 对照图](Z0008_comparison.png)
- [Z0009 对照图](Z0009_comparison.png)
- [Z0010 对照图](Z0010_comparison.png)

## 离线重算

```bash
MPLCONFIGDIR=/tmp/hegrounding-mpl .venv/bin/python benchmark/atlas/runs/zurich10_20260916_162847/inspect_run.py
```

此命令仅重建诊断报告与对照图，不调用模型，不改人工标注。
