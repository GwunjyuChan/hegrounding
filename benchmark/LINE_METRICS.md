# 线（line）预测的评估方法备选

整理日期：2026-10-19。用途：备选清单，后续视情况加入 `benchmark/eval_geometry.py`。
**当前已实现：** 方法 4（加宽后算 IoU），见 `eval_geometry.py`。

符号：G 为真值折线，P 为预测折线，d(x, L) 为点 x 到折线 L 的最短距离。建议所有距离都按图像对角线归一化（d / √(W² + H²)），这样不同地图之间可以比较。

---

## 1. 端点距离（Endpoint distance）

- **定义：** 两条线对应端点的平均距离，取两种端点配对中较小的一种，处理方向相反的情况：
  `min( (|g₀−p₀| + |g₁−p₁|)/2 , (|g₀−p₁| + |g₁−p₀|)/2 )`
- **出处：** 线框 / 线段检测的 structural AP（sAP）。L-CNN, Zhou et al., *End-to-End Wireframe Parsing*, ICCV 2019。
- **优点：** 简单、直观，适合直线段（一段战线、一段城墙）。
- **缺点：** 完全不看中间走向，两条弯法不同的路端点重合也会得高分；对多段折线没有意义。
- **适用：** 只作直线段的辅助诊断。

## 2. 曲线距离

### 2a. Chamfer 距离（推荐作辅助指标）
- **定义：** 在 G、P 上等距采样，`CD = ½·mean_{x∈G} d(x,P) + ½·mean_{y∈P} d(y,G)`
- **出处：** 高精地图矢量化，用 Chamfer 距离阈值（0.5 / 1.0 / 1.5 m）计算 AP。VectorMapNet（Liu et al., ICML 2023）、MapTR（Liao et al., ICLR 2023）。
- **优点：** 反映整体形状，对单个离群点不敏感，可以按阈值换算成命中率。
- **缺点：** 不考虑方向和点的先后顺序。

### 2b. Hausdorff 距离
- **定义：** `HD = max( max_{x∈G} d(x,P), max_{y∈P} d(y,G) )`；变体 Modified Hausdorff 取平均（Dubuisson & Jain, 1994）。
- **优点：** 能反映最坏偏差。
- **缺点：** 对局部偏离和预测线多画出来的一小段都很敏感。

### 2c. Fréchet 距离（离散版）
- **定义：** 沿两条线同向前进时，所需"牵绳"的最短长度（Eiter & Mannila, 1994，离散 Fréchet）。
- **出处：** 轨迹相似度、地图匹配。
- **优点：** 考虑方向和顺序，适合**行军路线**。
- **缺点：** 必须规定方向；真值没有方向的线（城墙、河岸）不适用。

## 3. 缓冲带覆盖率（道路提取领域）

- **定义：** 在真值和预测周围各加宽度 ρ 的缓冲带：
  - **Completeness（≈ recall）：** G 落在 P 缓冲带内的长度 / G 的总长
  - **Correctness（≈ precision）：** P 落在 G 缓冲带内的长度 / P 的总长
  - **Quality：** 匹配长度 / (G 总长 + P 未匹配长度)
- **出处：** Wiedemann et al., *Empirical Evaluation of Automatically Extracted Road Axes*, 1998；relaxed precision/recall 见 Mnih & Hinton, ECCV 2010。
- **优点：** 能区分"线画短了"（completeness 低）和"线画偏了 / 画多了"（correctness 低），方便做错误分析。
- **缺点：** 两个数需要合成 F1 才能作为单一指标；结果依赖 ρ。

## 4. 加宽后算 IoU（当前主指标，已实现）

- **定义：** G 和 P 各按半宽 r 加宽成区域，再算 IoU。当前参数 r = 图像对角线的 1% ⚠（待导师确认）。
- **出处：** 车道线检测 CULane（Pan et al., *Spatial As Deep*, AAAI 2018）把车道线画成 30 px 宽，IoU > 0.5 算命中。
- **优点：** 和面、点用同一种指标（点画成圆、线加缓冲、面直接用），回应了"不同类型用不同指标不公平"的顾虑。
- **缺点：** 结果依赖 r；线很短时，IoU 对平移误差非常敏感。

## 5. 其他（目前不建议）

- **APLS**（Van Etten et al., SpaceNet 2018）：评估路网拓扑，我们的数据是单条线，用不上。
- **角度差 + 垂直距离**：适合直线段的检测任务，表达能力不如 Chamfer。

---

## 建议组合

| 角色 | 指标 |
|---|---|
| 主指标（与面、点统一） | 加宽 IoU，hit@0.5 / hit@0.75 |
| 辅助（形状误差） | 归一化 Chamfer 距离（中位数） |
| 错误分析 | Completeness / Correctness |
| 视情况 | Fréchet（路线样本多且方向重要时）；端点距离（只作直线段的诊断） |

**需要提前确定的参数（跑模型前冻结）：** 缓冲半宽 r、Chamfer 的采样间隔、命中阈值。
