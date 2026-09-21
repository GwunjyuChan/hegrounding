# 苏黎世作战参考图输入实验

## 当前结论

已用原始作战参考图对同样十条事件运行 Qwen3-VL 直接定位。**目前无法计算定位准确率的变化**：
参考图尚无独立人工真值，旧答案在另一张图的像素坐标系上，不能直接使用或按宽高比例缩放迁移。
下表是输出有效性，不是定位正确率。

| 输入 | 请求数 | 有效几何 | 拒答 | 错误 | 推理耗时（秒） |
|---|---:|---:|---:|---:|---:|
| geographic | 10 | 8 | 0 | 2 | 182.2 |
| reference | 10 | 9 | 0 | 1 | 256.0 |

## 控制与限制

- Qwen/Qwen3-VL-8B-Instruct，同一缓存版本、设备与精度、greedy、4096 输出 token 上限；原文、问题、定位 prompt 保持一致。
- baseline 使用刚完成的直接定位运行，不把旧预测伪称为重新调用。只新运行参考图十条，不重跑 GPT-5 或两阶段。
- 原底图为 1538 × 1754；参考图为 2177 × 1699。原始 JPEG 仅无损转换为 PNG，解码后的像素相同，未裁切、增强或重绘。
- 图像改变同时改变了地理覆盖、缩放、绘图风格和军事提示，不能把差异仅归因于部署标记。
- 参考图含部队名称、阵位和箭头，是有答案提示的诊断条件，不是无泄漏测试集。
- Regensdorf 出现在参考图中，Z0003 不能继续沿用旧图的 outside_map 标签。
- 原始部署符号并非每条事件/时刻的真值；特别是首次登陆、后续夺取和撤退不能混为同一时间层。

## 人工审核

### 预测图目视检查（不是正式评分）

参考图预测仍有明显错位。例如 Z0004 的目标是 Altstetten，但预测点落在 Otelfingen 附近；
Z0007 的目标是 Wollishofen，但预测点落在更北面的 Dällikon 附近。
因此，不能把有效几何从 8/10 增至 9/10 解读为定位准确率提升。
上述判断来自地图地名与预测覆盖图的目视核对，不是新增人工真值，也没有据此计算准确率。

独立入口：<http://127.0.0.1:8768/atlas.html>。主站 8767 的底图、人工标注和预测没有更改。
在独立入口先关闭模型预测图层，按问题在参考图上标注；避免用预测点当真值。
该入口的数据保存在本实验 reference_workspace 内，不是原项目人工标注的替代品。
十条初始均为待审核，既不自动接受，也不继承旧图的范围外判定。
完成后应预先定义各图的合理容差/允许区域，在两图都可定位且目标一致的共同事件上比较命中率。
不能直接比较两种比例尺的像素距离均值；Z0009/Z0010 的原人工答案目标/几何问题也仍需复核。

## 输出

- [参考图全部预测概览](reference_predictions.png)
- [原始预测 JSON](../predictions.json)、[逐次原始响应](../predictions.attempts.jsonl)。
- [运行统计](summary.json)、[备用空白真值模板](reference_gold_template.jsonl)。
- 对照图左为原底图预测，右为参考图预测；不是相同地理范围/比例尺的配准图。
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

## 复现

```bash
MPLCONFIGDIR=/tmp/hegrounding-mpl .venv/bin/python benchmark/run_atlas_vlm.py \
  --input benchmark/atlas/runs/zurich10_reference_20260917_021309/input.zip \
  --backend qwen-local --model Qwen/Qwen3-VL-8B-Instruct --limit 10 --execute \
  --output benchmark/atlas/runs/另一个新目录/predictions.json
```

重新打开独立审核服务：

```bash
bash benchmark/run_annotation_gui.sh --port 8768 \
  --data-root benchmark/atlas/runs/zurich10_reference_20260917_021309/reference_workspace
```
