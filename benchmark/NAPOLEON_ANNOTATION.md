# Napoleon Pilot Annotation

当前默认是 Maps 目录选图后的 100 条候选，不是已经验证的 benchmark。
本轮新增 88 条中 64 条来自地图推导，需补独立文字；见 `MAP_EXPANSION_REVIEW.md`。
旧 20 条及三张配图已归档；新资料和审核事项见 [Maps 候选清单](MAP_FIRST_CANDIDATES.md)。

## 启动

在项目根目录运行：

```bash
bash benchmark/run_napoleon_annotation.sh --annotator eric
```

默认跳过已保存记录。复查使用 `--review`；`--start 5` 从原始输入第六条开始。
第二位标注者使用独立文件，例如 `--output benchmark/map_first_annotations_reviewer2.jsonl`。
窗口需要本地图形桌面。依赖为现有环境中的 matplotlib 和 Pillow。

## 标注操作

1. 阅读右侧英文事件与目标问题；鼠标滚轮可以滚动文字。终端也显示事件与来源链接。
2. 选择 point、line 或 polygon。点模式单击替换；线和区域逐点单击，区域自动闭合。
3. 右键撤销最后一个顶点；切换几何类型会清空当前图形。工具栏可缩放、平移；恢复普通模式后才能画点。
4. 选择 accepted、ambiguous、unlocatable 或 rejected。后三种允许不画图，只记录原因。
5. 点击 Save 后，在终端填写证据（必填），按下方词表选择要素类型编号或英文代码，再填写点/线容差（原图像素）。不填写证据则本次不保存。
6. Skip 暂时跳过，Quit 或关闭窗口退出；已保存记录不丢失。

证据说明应包含：定位依据、参照物、空间约束、仍不确定的边界。
线的两端必须有证据支持。区域代表可接受的位置范围，不能仅用一个大框包住所有可能地点。
当前每条支持一个几何对象；不连续的多个候选区域请标 ambiguous，并在依据中说明。
不绘制旧城镇中心，避免标注者被旧 gold 引导。

## 要素类型词表 v1

字段 `geo_feature_type` 描述目标位置的地理对象，不描述军事行动或部队身份。
每条选择一个最符合目标的类型；编号只是输入方式，文件中保存英文代码。

| 编号 | 代码 | 含义及适用范围 |
|---|---|---|
| 1 | `bridge` | 桥梁本体及其端点；桥旁的陆地不自动归为桥梁 |
| 2 | `ford` | 有证据说明是浅滩或涉水渡口的过河位置 |
| 3 | `river_bank` | 河岸及沿岸陆地区域，不是水面 |
| 4 | `river` | 河道、水面或一段河流 |
| 5 | `road` | 道路、小径或指定道路区段 |
| 6 | `junction` | 道路交叉口、岔路口 |
| 7 | `woodland` | 森林、树林内部或林缘 |
| 8 | `high_ground` | 高地、山丘、山脊或山坡 |
| 9 | `open_ground` | 有证据支持的开阔地、田野、草地或平原 |
| 10 | `settlement` | 村庄、城镇及建成区；村南某处不等于村庄本身 |
| 11 | `building` | 单体建筑，如磨坊、教堂或农舍；桥梁使用 `bridge` |
| 12 | `other` | 以上未覆盖，或资料未说明地理对象类型；在证据里解释 |

选择规则：

- 标目标对象，不是参照物。例如在磨坊旁的桥上交战，目标是桥，选 `bridge`，不是 `building`。
- 林中的营地选 `woodland`；沿河岸部署的炮兵选 `river_bank`；村内驻军选 `settlement`。
- “在村南扎营”若没有说明地形，不要猜测为 `open_ground`，可选 `other`；地图留白本身也不证明是平原。
- “渡河”是动作，不必然意味着浅滩；只有文本或地图支持 ford 时才选 `ford`。
- 目标同时位于多个要素上时，选最直接限定目标范围的对象，并在证据中记录其他关系。例如“林地内、靠近河岸的阵地”通常选 `woodland`。
- 仍然无法判断类型时用 `other`。定位有歧义则另外选择 `ambiguous` 状态；已知类型但找不到位置时，仍可选该类型并标 `unlocatable`。
- 要素类型不限制几何形式：`river_bank` 可以标点、线或区域，取决于问题和证据。

新记录只接受词表代码或编号（例如 `7`、`woodland`），英文大小写不敏感。
新标注直接回车默认 `other`；复查时，若原类型在词表中，回车保留它。
旧的自由文本类型不会批量改写；复查遇到词表外的旧值会提示重新选择。
新保存的标注记录 `geo_feature_vocab_version: 1`，导出时保留版本号。

点/线容差记录原图像素数，目前尚未接入正式评测；不确定时可填 `0`，表示不加额外容差。
证据本身只能支持大致范围时，应选择区域标注或歧义状态，不通过任意放大容差解决。

## 旧数据来源与限制（已归档）

本节仅追溯旧 N 系列；当前 MF 系列以 [新资料清单](MAP_FIRST_CANDIDATES.md) 为准。

| ID | 数量 | 文章及地图 |
|---|---:|---|
| N0001–N0007 | 7 | [Borkowo](https://www.napoleon-series.org/military-info/battles/1806/Borkowo/c_borkowo.html) |
| N0008–N0014 | 7 | [Sochocin](https://www.napoleon-series.org/military-info/battles/1806/Sochocin/c_sochocin.html) |
| N0015–N0020 | 6 | [Wavre](https://www.napoleon-series.org/military-info/battles/hundred/c_chapter6.html) |

事件文字是依据文章写的简短英文转述，不是原文引文，也不是历史一手资料。
每条记录包含 source_section，可回到对应小节核实。转述未获得人工批准。
这批数据有意包含精度不足的候选，用来衡量可标注性；不能为了凑 20 个 accepted 而猜测。
先标前 5 条，讨论规则，再继续其余样本。若大多数无法定位，应寻找更详细的地图。

以下关于旧三图的说明仅供归档追溯，不描述当前默认候选：
已目视检查的旧三张图片均为低分辨率示意地图，不应声称为拿破仑时期原始地图。
Borkowo 650x431，Sochocin 600x393，Wavre 292x358；放大不会增加原始细节。
河流和聚落可辨认，但高地、单个桥端、渡口及营地边界未必能确定。
Wavre 图有 French advance 箭头，可能泄露答案。当前只收录原图，未生成遮挡版。
版权/再发布资格未确认，不能因本地可下载就视为可公开发布。

同一地图上的多个事件不是独立地图样本；Borkowo 和 Sochocin 覆盖重叠区域，
split_group 都是 wkra_1806，未来必须一起分组，不能随机跨训练/测试集。
两条 Limale crossing/guard 等样本共享地理目标，也不能当作独立定位证据。

## 保存与导出

`map_first_annotations.jsonl` 按追加方式保留修改历史，同一 event_id 最后一条为当前版本。
保存原图左上角为原点的像素坐标，x 向右、y 向下；不虚构经纬度或米/像素。
区域坐标不重复首顶点。只有点标注保留兼容字段 geo_gold_px，线/面该字段为 null。

```bash
.venv/bin/python benchmark/assemble_geo_benchmark.py \
  --candidates benchmark/map_first_candidates.jsonl \
  --annotations benchmark/map_first_annotations.jsonl \
  --output benchmark/map_first_reviewed.jsonl
```

导出仅包含最新 accepted 标注。该文件是审核后的数据，不代表已能运行旧 VLM eval：
旧评测依赖米制比例尺和点 gold；此批数据的区域评分、输入图遮挡及目标问题 prompt
尚需接入后才能正式评测。不要直接传给旧 eval，否则可能使用不适用的字段或指标。
