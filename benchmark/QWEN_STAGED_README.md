# Qwen3-VL 两阶段定位工作流

## 两条路线

```text
A 直接定位
  历史段落 + 事件问题 + 干净底图
                  |
             Qwen3-VL
                  |
              点 / 线 / 区域

B 两阶段定位
  历史段落 + 事件问题（不含地图）
                  |
             Qwen3-VL 第一次调用
                  |
       地点答案 + 原文证据 + 不确定性
                  |
  上述输出 + 原事件问题 + 同一张干净底图
                  |
             Qwen3-VL 第二次调用
                  |
              点 / 线 / 区域
```

第一步是可审查的地点答案，不要求模型输出冗长的内部思考过程。
第二步不再给完整历史段落；只保留第一步模型产生的地点、证据和不确定性，以及原问题。
证据是第一步输出的摘录，不是额外从人工答案补入的提示；非逐字引用会标记，但不会事后改写。
各次调用独立，不携带前一轮隐藏状态或其他事件的聊天历史。

两条路线定位时共用同一个 prompt、原图像素规则、图像尺寸、预处理及最大输出 token。
同一个本地缓存权重只加载一次，greedy 解码；记录随机种子、设备、精度、库版本及图片哈希。
执行顺序在事件间交替，减少总是某条路线先执行的顺序影响。
两阶段额外消耗一次文本推理，必须同时比较 token、耗时和错误，不能称为等计算量实验。

## 本轮结果

使用原十条冻结样本，同一张 1538 × 1754 底图；这次重新运行直接路线，不把旧结果假称新实验。
[对比报告与逐条图像](atlas/runs/zurich10_qwen_staged_20260917_012804/comparison/RESULTS.md)。

事先约定的诊断范围：

- 全部十条都推理；Z0003 是图外拒答对照，不纳入像素距离均值。
- Z0009 问道路路段，人工答案只有一点；Z0010 问城区，人工答案/证据为撤退道路。两条先展示，不作主要空间评分。
- 点真值报告欧氏像素距离；面真值遇到点预测时检查点是否在区域内、到区域距离。
- 其他输出几何组合本版只展示，不声称已实现线/面综合指标。
- 配对均值只取两路线都成功返回点的同一批点真值样本，列出实际 ID 和 n；失败/拒答不算零误差。
- 所有有效/无效输出都保留；不裁剪越界坐标，不根据结果改标注或事后选择命中阈值。

当前人工点/线容差为 0，且真值和文本翻译仍需审核。结果仅作流程诊断，不能由一张地图推断普遍提升。

## 执行

项目根目录运行。第一条默认仅检查输入，不加载模型、不读 key、不写输出：

```bash
MPLCONFIGDIR=/tmp/hegrounding-mpl .venv/bin/python benchmark/run_qwen_grounding_comparison.py \
  --input benchmark/atlas/runs/zurich10_20260916_162847/input.zip \
  --output-dir benchmark/atlas/runs/my_qwen_staged
```

正式运行在末尾添加 `--execute`。默认模型 `Qwen/Qwen3-VL-8B-Instruct`，最多十条，
`--text-max-tokens 4096 --map-max-tokens 4096`；小规模验证可设 `--limit 2`。
输出目录必须不存在，防止覆盖。只使用本地缓存权重，无网络、无付费 API、无 `.env` 读取。

推理结束后，独立进行本地评分（不加载模型）：

```bash
MPLCONFIGDIR=/tmp/hegrounding-mpl .venv/bin/python benchmark/compare_grounding_methods.py \
  --run-dir benchmark/atlas/runs/my_qwen_staged \
  --gold benchmark/atlas/runs/zurich10_20260916_162847/gold_snapshot.json \
  --exclude Z0009 --exclude Z0010
```

小规模运行只传入实际包含的排除 ID；`--limit 2` 时不要传 Z0009/Z0010。
其他数据集应在查看预测前确定自己的排除标准。gold 必须与输入底图版本和哈希匹配。
这里使用已冻结、且与当前人工标注一致的快照；后续重标后应重新导出相应版本的人工答案。

模型输出/解析错误不会终止余下事件，但执行结束返回退出码 1，以防被误当成全部成功。
只要存在 `completed.json` 即表示全部选定事件已处理，可以评分；没有该文件不能评分半成品。
中断后不覆盖原目录；另选新目录重新运行，当前没有断点续跑功能。

## 输出和人工检查

```text
my_qwen_staged/
  input.zip                  冻结输入
  manifest.json              输入身份、参数及实验设计（启动记录）
  local_config.json          缓存权重、设备、库版本
  completed.json             完成标记及各路线错误数
  stage1/
    prompt.txt
    answers.json             第一次文本推理结果
    attempts.jsonl           实际输入、原始回复、用量与耗时
  direct/
    prompt.txt
    predictions.json         直接路线几何
    attempts.jsonl
  two_stage/
    prompt.txt
    predictions.json         两阶段最终几何
    attempts.jsonl           可检查实际传入第二步的文字
  comparison/
    gold_snapshot.json       只由离线评分进程保存，不交给模型
    diagnostics.json
    RESULTS.md
    Z0001.png ...             直接与两阶段并排，红色为人工标注
```

第一步解析失败时，第二步记 `upstream_error`，不退回原文直接定位；第一步拒答时记
`upstream_abstained`，最终输出空几何。它们与第二步调用失败、第二步主动拒答分别保存。

两份 `predictions.json` 的模型显示名带 `[direct]` / `[two-stage]`，可分别在地图集里导入。
不会覆盖之前的 Qwen/GPT-5 记录。当前地图集按模型家族着色，两条 Qwen 路线可能都是绿色，
请按完整方法名切换图层；报告对照图固定绿色为直接、紫色为两阶段。

## 代码

- `run_qwen_grounding_comparison.py`：运行与阶段传递，推理进程不接受 gold 参数。
- `run_text_location_eval.py` 的 INSTRUCTION：第一步地点问答规则。
- 输入包 `prompt.txt`：两条路线共用的地图定位规则。
- `compare_grounding_methods.py`：评分、成本汇总与可视化。
- `test_qwen_grounding_comparison.py`、`test_grounding_diagnostics.py`：隔离、失败传播和指标测试。
