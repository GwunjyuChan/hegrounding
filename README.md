# HE-Grounding

当前主线：根据历史事件文本中的空间关系，在法国革命与拿破仑战争时期的地图上标注点、线或区域。
目前保留第二次苏黎世战役 10 条，另有 Maps 目录优先选图的 100 条候选，共 26 张参考图，尚非正式评测集。
13 个国家达到每国两图、每图四条的候选配额；并非所有国家已覆盖。见 [国家覆盖与缺口](benchmark/COUNTRY_COVERAGE.md) 和 [逐图/逐事件审核](benchmark/MAP_EXPANSION_REVIEW.md)。新增 88 条中有 64 条为地图推导，需补独立史料。
旧 Borkowo、Sochocin、Wavre 三图及其 20 条候选已于 2026-09-24 移入本地归档。
随后 Wkra 部署合图因辨识度不足退出活动数据，改用布萨科“内伊进攻”图；当前为苏黎世 10 条、Marengo 4 条、布萨科 4 条、圣塞巴斯蒂安围城 4 条。
新地图、对应叙事/报告/部署说明与待核查问题见 [Maps 选图与史料清单](benchmark/MAP_FIRST_CANDIDATES.md)。

## 进度快照（2026-09-21）

- 地图集工具支持底图版本、人工点/线/区域标注，以及按模型区分预测结果。
- 已完成苏黎世十条样本的 GPT-5 / 本地 Qwen3-VL 直接定位、纯文本地点问答、
  Qwen 两阶段（文本地点答案再定位）实验。
- 已测试将作战参考图直接作为模型输入；参考图缺少独立人工真值，不能量化准确率变化。
- 当前仍是诊断实验：只有一个战区，部分标注目标需复核，不能将有效坐标输出比例作为准确率。

操作和实验记录：

- [地图集与模型评测](benchmark/ATLAS_README.md)
- [纯文本地点问答](benchmark/TEXT_LOCATION_README.md)
- [Qwen 两阶段工作流](benchmark/QWEN_STAGED_README.md)
- [直接与两阶段对比结果](benchmark/atlas/runs/zurich10_qwen_staged_20260917_012804/comparison/RESULTS.md)
- [作战参考图实验](benchmark/atlas/runs/zurich10_reference_20260917_021309/review/RESULTS.md)
- [苏黎世 8 地名批量实验结果图与 JSON（2026-09-23）](benchmark/diagnostics/zurich_labels_20260921/workspace/benchmark/atlas/place_lab/runs/bc5c63c8409d4836b8a16610654670d8/review/RESULTS.md)

下一阶段将检查坐标链路，并对比直接地名定位、全图/裁剪图及不同年代地图的表现。
第一阶段的独立地名诊断、标注规则和运行命令见 [地名诊断说明](benchmark/PLACE_DIAGNOSTICS.md)。
仓库保存当前地图资产、标注与实验记录；密钥、虚拟环境、论文 PDF、会议与个人计划、
`todo/` 和旧 HLS 本地归档不上传。

## 开始标注

新流程使用 [地图集编辑工具](benchmark/ATLAS_README.md)：参考作战图与干净标注底图分开，
支持 PDF 导入、裁切、底图版本、独立人工标注、VLM 输入包与模型预测结果图。
启动后访问 `/atlas.html`。现有欧洲地图入口仍保留。

推荐统一的欧洲地图入口，在项目根目录运行：

```bash
bash benchmark/run_annotation_gui.sh
```

打开 http://127.0.0.1:8765，点击战场即可查看全部 110 条事件，证据和要素类型在页面填写。
旧标注自动读取，支持复查和历史版本。详见 [GUI 说明](benchmark/GUI_README.md)。

旧终端入口仍保留：

```bash
bash benchmark/run_napoleon_annotation.sh --annotator eric
```

复查已有标注时添加 `--review`。默认自动跳过已保存记录。
详细规则见 [标注说明](benchmark/NAPOLEON_ANNOTATION.md)。

苏黎世 10 条候选使用 `benchmark/zurich_pilot_10.jsonl`，启动命令与原文出处见
[苏黎世标注说明](benchmark/ZURICH_ANNOTATION.md)。终端启动命令默认打开 Maps 的 100 条候选。

## 当前目录

```text
benchmark/
  annotation_server.py           本地地图标注服务
  run_annotation_gui.sh          统一欧洲地图入口
  gui/                           浏览器界面与离线地图资源
  annotate_geo.py                 点、线、区域标注工具
  run_napoleon_annotation.sh       当前启动入口
  map_first_candidates.jsonl      100 条 Maps 优先候选
  map_first_annotations.jsonl     参考图人工标注输出（保存后产生）
  MAP_FIRST_CANDIDATES.md          来源、问题、审核顺序
  assemble_geo_benchmark.py        导出最新 accepted 标注
  test_annotation.py              标注工具测试
  NAPOLEON_ANNOTATION.md           操作与数据说明
  vlm_eval.py                     保留的模型调用/旧点定位评测工具
maps/napoleon_maps/                3 张 Maps 目录参考图及布萨科原始小图
archive/                          旧数据处理流程和实验归档
meetings/                         会议记录
proposal/                         论文 proposal
relative_work/                    相关研究
```

## 导出和验证

```bash
.venv/bin/python benchmark/assemble_geo_benchmark.py
.venv/bin/python -m unittest discover -s benchmark -p test_annotation.py
```

导出默认写入 `benchmark/map_first_reviewed.jsonl`。地图集模型输入与评测使用
`run_atlas_vlm.py`；当前已有点距离及点落入区域的诊断，完整线/面指标仍待完善。
保留的 `vlm_eval.py` 必须显式指定 `--benchmark`，不再自动选择旧 HLS 数据；
不要把当前候选直接传入旧点定位评测。

## 旧数据

HLS 原始数据、事件提取、瑞士地图处理、审核表、实验输出及旧 showcase 已移动到
[HLS 归档](archive/hls_processing_2026-09-05_044200/ARCHIVE.md)。
[归档索引](archive/README.md) 列出所有历史版本。文件清单包含原路径、大小和 SHA-256。
归档保留原始内容和相对路径，恢复运行需要按清单恢复相关文件。
归档属于本地文件，当前 Git 配置忽略 archive/。

## 环境

依赖由 `pyproject.toml` 和 `uv.lock` 管理，可用 `uv sync` 安装。
标注需要 matplotlib、Pillow 和本地图形桌面。标注过程不调用付费 API。
