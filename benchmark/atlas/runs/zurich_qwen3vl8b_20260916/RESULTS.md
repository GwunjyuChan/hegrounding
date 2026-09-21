# 苏黎世本地 Qwen3-VL 验证

日期：2026-09-16。性质：与 GPT-5 首轮相同输入的小规模诊断，不是正式模型排名。

## 执行配置

- 模型：`Qwen/Qwen3-VL-8B-Instruct`，不是 Thinking 版，也不是量化版。
- 缓存版本：`0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`。
- 本机 Apple MPS，`torch.float16`；PyTorch 2.14.0、Transformers 5.16.1。
- 全程本地离线推理，不读取 API key，不下载模型，不发送地图和事件到外部服务，无 API 费用。
- greedy 解码，`do_sample=False`，`max_new_tokens=4096`；四条均正常完成，未达到 token 上限。
- 复用 GPT-5 的同一个 input.zip，已验证字节完全一致；使用同一套 system instruction、事件文字、问题、输出 schema 和原图像素坐标要求。
- 底图版本：`3cb177ba1bd166169eaf91eb`，1512 × 895 px；独立保留运行前人工标注快照。
- 视觉处理由各模型后端完成，Qwen 记录的 image_grid_thw 为 `[1, 56, 94]`；不能据相同源图片宣称模型内部视觉表示相同。

现有 runner 已加入 `--backend qwen-local`，与 API 后端共用输入包验证和输出解析。代码回归测试 39 项通过。
初次加载因缓存缺少 README 等非推理文件而停止，尚未执行事件；限定所需文件类型后成功离线加载，没有重复运行成功事件。

## 结果

4 条有效输出，0 次拒答，0 个解析或推理错误，全部输出 point。Z0003 为 outside_map，未运行。
四条推理耗时合计 38.5 秒，不含权重加载、对照图生成等时间。
本地 tokenizer 计数：input 6,955、output 188、total 7,143；不同模型的 token 数不适合作为等价计算量比较。

| 事件 | Qwen 原始点 | Qwen 距离 (px) | GPT-5 距离 (px) | 比较方式 |
| --- | --- | ---: | ---: | --- |
| Z0001 | (578, 720) | 656.6 | 80.8 | 到人工区域的最近距离，均在区域外 |
| Z0002 | (620, 480) | 496.5 | 413.6 | 到人工点的距离，均不满足已保存的 0 px 容差 |
| Z0004 | (528, 250) | 237.8 | 114.1 | 到人工区域的最近距离，均在区域外 |
| Z0005 | (700, 380) | 298.1 | 383.3 | 到人工区域的最近距离，均在区域外 |

这里严格按 prompt 要求，把原始输出解释成原图像素；未作坐标缩放、位置修正或容差放宽。
点是否落入区域只衡量点定位，不是区域 IoU；各行也不构成可直接平均的统一指标。

## 坐标约定疑点

Z0004 输出 `(528, 250)`。若事后假设它使用了 0–1000 的归一化坐标，按 `x * 1512 / 1000, y * 895 / 1000` 换算，会得到 `(798.336, 223.75)`，位于当前 Altstetten 人工区域内。

这只是一个可复查的诊断现象，不证明模型一定使用了该约定，也不证明其他三条能通过同样转换修复。没有将这一换算写入预测文件、地图 GUI 或上表，没有事后宣布该条命中。
下一轮可在独立校准样本上确认并预先固定“像素输出”或“归一化输出 + 确定性转换”的协议，再统一重跑，避免按 gold 挑选有利解释。

## 结论与限制

本地加载、视觉输入、结构化输出、解析、对照图和 GUI 导入均已打通；在本轮原图像素协议下，Qwen 的四个预测均未匹配当前人工标注。
不能由四条同图样本断言模型优劣：仍有坐标约定疑点，且 Z0005 的 Höngg 标注与问题要求的城后高地区别需要复核；Z0001 接收岸和 Z0002 林地/单点定义也需进一步确认。
人工答案不能根据模型预测反向修改，任何修订必须有文本和地图证据。

## 查看结果

已将 Qwen 原始预测追加导入 [地图集](http://127.0.0.1:8767/atlas.html)。刷新页面后显示最新 Qwen 预测；GPT-5 的运行文件和追加历史保留，但当前 GUI 默认显示每个事件的最新预测，不提供多模型切换。
已核对人工标注和底图未改变。

- [原始预测](predictions.json)
- [完整响应与运行配置](predictions.attempts.jsonl)
- [诊断数值](diagnostics.json)
- [Z0001 对照图](Z0001_comparison.png)
- [Z0002 对照图](Z0002_comparison.png)
- [Z0004 对照图](Z0004_comparison.png)
- [Z0005 对照图](Z0005_comparison.png)
- [GPT-5 首轮报告](../zurich_gpt5_20260916_140056/RESULTS.md)

重新生成本地诊断和对照图，不执行模型：

```bash
MPLCONFIGDIR=/tmp/hegrounding-mpl .venv/bin/python \
  benchmark/atlas/runs/zurich_gpt5_20260916_140056/inspect_run.py \
  --run-dir benchmark/atlas/runs/zurich_qwen3vl8b_20260916
```

重新执行本地模型时使用新的输出路径，避免覆盖这次记录：

```bash
MPLCONFIGDIR=/tmp/hegrounding-mpl HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 \
.venv/bin/python benchmark/run_atlas_vlm.py \
  --input benchmark/atlas/runs/zurich_qwen3vl8b_20260916/input.zip \
  --backend qwen-local --model Qwen/Qwen3-VL-8B-Instruct \
  --limit 5 --max-output-tokens 4096 --execute \
  --output benchmark/atlas/runs/qwen_next_run.json
```
