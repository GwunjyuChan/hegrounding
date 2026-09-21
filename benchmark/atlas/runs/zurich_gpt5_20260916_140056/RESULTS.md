# 苏黎世首轮 GPT-5 验证

日期：2026-09-16。性质：小规模流程验证与相对现有人工标注的诊断，不是正式 benchmark 结论。

## 配置与数据隔离

- 模型请求 ID：`gpt-5`；Responses API；每条最多 4096 输出 token；超时 120 秒；不自动重试。
- 使用现有 runner 的默认 reasoning/image detail 设置，没有另外指定；输出 token 包含 reasoning token。
- 底图版本：`3cb177ba1bd166169eaf91eb`，1512 × 895 px。
- 图片 SHA-256：`736c66a93c53e40e575c74cdd2cd1c8cfbf84c88a6e1cfe668bd19a16fa62b80`。
- 发送：干净底图、英文历史段落、事件问题、事件 ID 和像素坐标约定。
- 未发送：人工几何、标注证据、参考作战图、建议要素类型或审核提示。
- `gold_snapshot.json` 单独保存在本地，模型 runner 只读取 `input.zip`。
- Z0003 的状态为 `outside_map`，没有调用模型，不计作模型失败。

## 执行结果

4 次请求，4 条有效几何，0 次拒答，0 个 API/解析错误。4 条预测全部为 point。
prompt 允许 point、line、polygon，因此输出点不是格式错误，但不能据此声称已经验证区域预测能力。

| 事件 | 人工几何 | 模型点 (x, y) | 与保存真值的比较 |
| --- | --- | --- | --- |
| Z0001 | polygon | (460, 105) | 在区域外，到区域最近距离 80.8 px |
| Z0002 | point | (850, 140) | 到人工点 (457, 11) 的距离为 413.6 px；已保存容差为 0 px |
| Z0003 | 无，outside_map | 未运行 | 排除 |
| Z0004 | polygon | (948, 254) | 在区域外，到区域最近距离 114.1 px |
| Z0005 | polygon | (1208, 333) | 在区域外，到区域最近距离 383.3 px |

区域诊断为“预测点是否落入人工多边形”，边界计作区域内；距离是到区域的最短欧氏距离，不是到中心的距离。
点诊断为原图像素欧氏距离，与用户预先保存的容差比较。没有新增事后阈值，也没有使用旧 500 米阈值。

三条区域样本均未落入人工区域；一条点样本未满足已保存容差。不要将两类诊断混合包装为经过验证的正式精度指标。

API 返回 token 使用量：input 5,276；output 10,258，其中 reasoning 10,048；total 15,534。
这里记录 token 数，不将其当作已核实的账单金额。实际费用以 API 账单为准。

## 需要优先检查的地方

1. **Z0004 可优先分析模型定位偏差。** 人工区域位于 Altstetten 聚落符号附近，预测点明显在其东侧。当前输出只有几何，无法确定是识别地名失败、文本理解失败还是坐标估计偏差。
2. **Z0005 应先复核真值。** 问题要求定位区别于小营地和主路的城后高地；人工证据写的是 `Hongg`，人工区域圈在 Höngg 一带。需要重新对照原文、地形和参考图确认，不能把模型与当前标注不一致直接等同于模型错误，也不能据此断言模型正确。
3. **Z0002 的目标是俄军防守位置。** 需核对当前单点是否充分表达防守林地/高地，以及 0 px 容差是否有合理依据；人工点距图顶仅 11 px，检查相关地物是否被裁断。
4. **Z0001 应复核登陆岸而非准备区。** 目前人工证据仅为 `near the village of Dietikon`，不足以单独解释为什么这块区域是最初六百人的接收岸。需要补充渡河方向和参考依据，不应按模型结果调整 gold。

地图年份为 1816，事件年份为 1799；当前只有一张底图上的四条请求，原文翻译和标注均尚需独立复核。这个实验说明输入、推理、解析、预测导入与可视化已打通，不足以推断 GPT-5 的整体历史地图推理能力。

## 查看与复现

4 条预测已追加导入地图集。刷新 <http://127.0.0.1:8767/atlas.html>，进入对应事件并启用模型预测图层即可对照。人工标注和底图与运行前快照一致，没有改动。

- [原始结构化预测](predictions.json)
- [逐次原始响应、prompt 与 token 使用记录](predictions.attempts.jsonl)
- [诊断数值](diagnostics.json)
- [Z0001 对照图](Z0001_comparison.png)
- [Z0002 对照图](Z0002_comparison.png)
- [Z0004 对照图](Z0004_comparison.png)
- [Z0005 对照图](Z0005_comparison.png)

所有图中红色为人工标注，蓝色为模型预测，左侧全图、右侧局部。

重新生成本地诊断与对照图，不调用 API：

```bash
MPLCONFIGDIR=/tmp/hegrounding-mpl .venv/bin/python benchmark/atlas/runs/zurich_gpt5_20260916_140056/inspect_run.py
```

这次模型执行命令如下。输出文件已存在，runner 会拒绝覆盖；如确需重新付费运行，应使用新的输出路径并保留本次记录。

```bash
MPLCONFIGDIR=/tmp/hegrounding-mpl .venv/bin/python benchmark/run_atlas_vlm.py \
  --input benchmark/atlas/runs/zurich_gpt5_20260916_140056/input.zip \
  --model gpt-5 --limit 5 --execute \
  --output benchmark/atlas/runs/zurich_gpt5_20260916_140056/predictions.json
```

`--limit 5` 是上限，输入包实际只包含 4 条 accepted 事件。
