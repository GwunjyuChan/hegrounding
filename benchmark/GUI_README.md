# 欧洲地图标注台

## 启动

```bash
bash benchmark/run_annotation_gui.sh
```

打开 http://127.0.0.1:8765。端口被占用时使用 `--port 8767`，不要终止其他服务。
本地服务只监听 127.0.0.1，不需要 OpenAI key，不发送事件、标注或图片到模型服务。
Leaflet、Lucide 和 Natural Earth 边界均保存在本地，正常使用不依赖外部地图瓦片服务。

## 工作流

1. 在欧洲地图上点击 Zürich、Wavre 或 Wkra 河战区。Wkra 包含相邻的 Borkowo 与 Sochocin，
   点击后选择战斗。左侧列表也可以直接进入任一战场。
2. 默认打开第一条未审核事件；没有未审核事件时打开第一条。事件列表可搜索、筛选，
   已标注事件仍可打开修改；上一条、下一条按战场完整事件顺序切换。
3. 历史地图工具栏可选点、线、区域。左键逐个添加顶点，区域保存时闭合；
   右键或撤销按钮撤销编辑，支持重做。平移工具用于拖动地图，滚轮缩放。
4. 右侧填写审核状态、统一要素类型、原图像素容差和证据。区域不使用点/线容差。
   无法定位或剔除允许无几何，但理由仍必填。通过必须有合法几何。
5. 保存或保存并下一条。页面切换会提醒未保存修改；刷新/关闭时也会提示。
6. 从“标注版本”选择旧记录会把它载入为草稿，保存后成为新的追加版本，不删除历史。

法文原文可在苏黎世事件的“原文”标签中查看；原 20 条没有逐字原文，原文标签禁用。
原文网站、资料与审核备注均在右侧。底图质量和箭头提示风险没有因更换 GUI 而消失。

## 数据兼容

| 候选输入 | 自动保存位置 |
|---|---|
| `benchmark/napoleon_pilot_20.jsonl` | `benchmark/napoleon_annotations.jsonl` |
| `benchmark/zurich_pilot_10.jsonl` | `benchmark/zurich_annotations.jsonl` |

用户只需使用一个入口，不需要手动选择输入/输出文件。磁盘上保留两份输出，是为了
兼容已存在的命令行工具和导出命令，不是要求分开标注。
保存沿用 schema_version=2，坐标系为原图左上角像素，不使用浏览器缩放后的坐标。
历史记录从原文件读取，最新版本优先。保存时校验版本指纹；其他 GUI 窗口已保存的新版本
会触发冲突提示，当前窗口必须重新打开事件后再保存，不能静默覆盖。
避免同时使用旧终端工具和 GUI 编辑同一事件；旧工具不参与 GUI 的版本冲突协议。

欧洲导航使用现代国家边界，仅供选取战场。导航点为聚落附近的近似坐标，
不是事件发生点，也不写入标准几何。波兰两个战场在总览中分组显示，不挪动真实地理位置。
配置位于 `annotation_server.py` 的 BATTLES 和 DATASETS。新增战场时必须同时配置数据和导航位置。

## 验证

```bash
MPLCONFIGDIR=/tmp/hegrounding-mpl .venv/bin/python -m unittest discover -s benchmark -p 'test_*.py'
```

服务默认不公开项目目录，只提供 GUI 静态资源、候选允许的图片以及专用 JSON API。
写请求需要同源 CSRF 令牌，客户端不能指定任意保存路径。
`--data-root` 可指定隔离测试副本；不要把测试几何写入真实人工标注。

## 第三方资源

- Leaflet 1.9.4：来自 https://unpkg.com/leaflet@1.9.4/dist/ ，许可证保存在 `gui/vendor/LEAFLET-LICENSE`。
- Lucide 0.468.0：来自 https://unpkg.com/lucide@0.468.0/dist/umd/lucide.min.js ，许可证保存在 `gui/vendor/LUCIDE-LICENSE`。
- Natural Earth 110m 国家边界：来自 https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_admin_0_countries.geojson ，
  公共领域数据，2026-09-08 下载，原始 GeoJSON 保存在 `gui/vendor/countries.geojson`。
- 历史地图仍使用候选记录的原始文件，本次没有替换任何标注底图。
