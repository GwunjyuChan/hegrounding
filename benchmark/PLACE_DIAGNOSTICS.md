# 地名定位诊断：第一阶段

本阶段对应 9 月 17 日会议的坐标链路检查、直接地名定位和标注可信度。
先隔离文字识别与坐标输出，不将其等同于历史事件定位。

## 当前入口

- 事件标注仍在 http://127.0.0.1:8767/atlas.html ，数据未迁移。
- 独立地名诊断在 http://127.0.0.1:8769/atlas.html ，P001–P008 共八条。
- 新数据：`diagnostics/zurich_labels_20260921/`。
- 原始坐标对照：`runs/coordinate_ablation_v2/`；格式归一化后的离线派生：`runs/coordinate_ablation_parsed/`。
- `runs/coordinate_ablation/` 是日志序列化中断记录，不用于分析。

新数据复用了地图集界面，页面中的“事件”在这个独立入口实际表示地名诊断题。
八个目标为 ZURICH、Altstetten、Albisrieden、Wollishofen、Kilchberg、Rüschlikon、Thalweil、Horgen。
这些是待人工确认的候选，不自动宣布为高置信度样本；也不计入历史事件样本数量。
输入是既有 1816 年底图，未加入人工标记、模型预测或作战部署符号。

## 你需要标什么

1. 点击 P001–P008，切换“事件标注”；可关闭左侧参考地图以扩大画布。
2. 用“区域”工具，围住目标地名的完整文字，包括变音符号，不框聚落、河岸或整片城区。
3. 尽量贴近文字外接矩形，留相同的小幅边距，不根据模型输出扩大框。
4. 要素类型选“其他”，证据填写实际读出的文字、同名歧义或识读困难。
5. 选择人工标注置信度并保存。确实无法识读时选“有歧义”或“无法定位”，不要强行通过。

本诊断要求模型返回**地名文字中心点**，离线检查该点是否落入人工文字框。
置信度为 null 表示尚未审核；1–5 依次表示非常不确定、不确定、尚可、较有把握、非常有把握。
旧事件标注缺少 confidence 时也视为未审核，不回填 5，不改写历史记录。
当前字段表示对整条人工标注的总体把握，证据中可另记“文本目标不确定”或“地图对应不确定”。
置信度和人工框只用于离线评分，不进入模型输入。

模型结果暂不导入此标注页，以减少锚定偏差。先冻结人工标签，再打开模型结果做审核。

## 坐标诊断设计

两组使用相同地图、地名、问题、模型、设备、图像预处理、greedy 解码和输出上限。
每个地名交替运行顺序；唯一任务差异是坐标约定：

| 组 | 输出约定 | 转回底图 |
|---|---|---|
| pixels | 原图像素 | 不变 |
| normalized_1000 | 每轴 0–1000 相对坐标 | x/1000 × 宽，y/1000 × 高 |

归一化换算依据 [Qwen3-VL 官方 grounding 示例](https://github.com/QwenLM/Qwen3-VL/blob/main/cookbooks/2d_grounding.ipynb)。
模型有时输出单点 `[x,y]` 而非 `[[x,y]]`；诊断解析器明确记录 `format_normalization` 并包装成单点列表。
原始格式失败与转换后几何有效性分别报告。这项结构转换不等于空间正确，也不修改任何数值。
按该约定 1000 位于图像最外边界；本项目点几何要求 x < width、y < height，落在最外边界的点记为越界，
不偷偷截断、不自动尝试另一套坐标。不将旧的像素提示实验事后解释成归一化坐标。
旧事件 pipeline 的提示词、解析方式和存量结果不变，只新增预处理尺寸日志。

每次调用记录：原图尺寸、处理后尺寸、patch/merge 大小、视觉 token 数、图片 hash、完整 prompt、原始回复和成本。
原始日志即使坐标解析失败也保留。输出有效率不是定位命中率。

本轮首次完整运行仍使用严格格式校验；随后通过 `reparse` 读取冻结的原始回复，生成单独派生结果：

```bash
.venv/bin/python benchmark/place_diagnostics.py reparse \
  --source benchmark/diagnostics/zurich_labels_20260921/runs/coordinate_ablation_v2 \
  --output benchmark/diagnostics/zurich_labels_20260921/runs/coordinate_ablation_parsed
```

该操作不调用模型，也不覆盖原始日志。已经生成的目录不能再次覆盖。

## 命令

项目根目录运行。准备新诊断集时输出目录必须不存在：

```bash
.venv/bin/python benchmark/place_diagnostics.py prepare \
  --output benchmark/diagnostics/new_label_set
```

默认使用当前指定的 1816 年底图和八个候选。更换地图时必须复核 TARGETS，不自动跨图迁移标签。
只检查输入，不加载模型：

```bash
.venv/bin/python benchmark/place_diagnostics.py run \
  --dataset benchmark/diagnostics/zurich_labels_20260921 \
  --output benchmark/diagnostics/zurich_labels_20260921/runs/new_run
```

末尾加 `--execute` 才调用本地缓存 Qwen。默认八题、两组，每次最多 1024 输出 token；
可用 `--limit 2` 小测。无需 API key。输出目录不可覆盖，没有断点续跑。

人工框完成后，单独评分，不再次调用模型：

```bash
.venv/bin/python benchmark/place_diagnostics.py score \
  --workspace benchmark/diagnostics/zurich_labels_20260921/workspace \
  --run benchmark/diagnostics/zurich_labels_20260921/runs/coordinate_ablation_parsed \
  --output benchmark/diagnostics/zurich_labels_20260921/score_review1.json
```

只评分 accepted、有 1–5 人工置信度且为 polygon 的文字框；分别汇总全部已审核与 confidence=5 子集。
错误输出和拒答在有 GT 的对应题中计为未命中，不从分母删掉。没有合格 GT 时 hit_rate 为 null，而不是 0%。
评分保存人工答案快照并检查底图版本/hash，防止跨图混算。

重启独立页面：

```bash
bash benchmark/run_annotation_gui.sh --port 8769 \
  --data-root benchmark/diagnostics/zurich_labels_20260921/workspace
```

## 初步几何规则

- 本地名诊断：人工标文字框（polygon），模型预测文字中心（point）。
- 事件点：问题确实指向可辨识的桥端、建筑或其他小范围位置，另设预先约定的像素容差。
- 事件线：问题问一段路、河道或路径；不能拿任意道路点作为线真值。
- 事件面：问题问林地、高地、城区片区或宽泛营地，标合理范围。
- 几何由问题的空间对象决定，不单凭“战争/交通/工业”类型决定。
- 本周复核 Z0009（道路/点）和 Z0010（城区/撤退道路），暂不混入高置信度主评分。

## 尚待完成

- [ ] 人工确认八个文字框与置信度，冻结可靠样本。
- [ ] 对同一批目标做全图/原分辨率裁剪图对照；目标不要总在裁剪中心。
- [ ] 引入同地点 Siegfried / 现代地图；独立标 GT，控制范围和文字大小。
- [ ] 审核旧文本问答，区分理解错误、识读错误、坐标错误和 GT 不确定。
- [ ] 汇总会议用配对结果和错误类型，再决定预处理或模型方向。

这些八题共享一张底图，只能支持小规模诊断，不能声称跨地图泛化。
