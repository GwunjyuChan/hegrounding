# 欧洲地图标注台

## 启动

```bash
bash benchmark/run_annotation_gui.sh
```

打开 http://127.0.0.1:8765。端口被占用时使用 `--port 8767`，不要终止其他服务。
本地服务只监听 127.0.0.1，不需要 OpenAI key，不发送事件、标注或图片到模型服务。
Leaflet、Lucide 和 Natural Earth 边界均保存在本地，正常使用不依赖外部地图瓦片服务。

## 工作流

1. 在欧洲地图或战役列表选择战场。当前共 26 张参考地图、110 条候选事件，统一进入 `/atlas.html?map=...`。
2. 未选底图时，先预览参考图。可直接“使用当前参考图并开始标注”，或在当前任务内“编辑底图”，上传替代图、裁切并确认。底图编辑不再与标注任务并列。
3. 已有底图时直接进入事件标注，默认第一条未审核事件；事件列表可筛选，也可回到已标注事件。点、线、区域工具用于绘制，支持撤销、重做；平移工具用于拖动地图，滚轮缩放。
4. 右侧填写审核状态、统一要素类型、最终底图像素容差和证据。区域不使用点/线容差。
   无法定位或剔除允许无几何，但理由仍必填。通过必须有合法几何。
5. 保存人工标注，再用“下一条”切换事件。离开未保存草稿时会提醒。
6. 顶部“编辑底图”可更换地图；取消不切换底图。新版本不复用旧像素标注，恢复旧底图可找回该版本的标注。详情见 [底图工作流](ATLAS_README.md)。

原文、资料链接与审核备注可在事件的“原文与资料”中查看。Maps 的 100 条包含英文转述；新增批次区分外部文字与地图推导，详见 `MAP_EXPANSION_REVIEW.md`。
新增地图的日期冲突与证据来源见 [资料清单](MAP_FIRST_CANDIDATES.md)。它们是参考图，尚非干净模型输入。
原文网站、资料与审核备注均在右侧。底图质量和箭头提示风险没有因更换 GUI 而消失。

## 界面语言

登录页、主页、事件标注和独立地名实验的页首提供 `中文 / English` 切换。
首次访问默认英文；手动选择的语言保存在当前浏览器中，跨页面保留。无需重新加载页面，未保存的输入和几何不会重置。
只翻译界面控件、提示和状态。事件原文、问题、用户地图名称、地名、证据、模型输出及导出数据保持原样。
翻译表与动态文本绑定位于 `gui/i18n.js`，布局补充位于 `gui/i18n.css`。

## 数据兼容

| 候选输入 | 统一工作区保存位置 |
|---|---|
| `benchmark/map_first_candidates.jsonl` | `benchmark/atlas/gold.jsonl` |
| `benchmark/zurich_pilot_10.jsonl` | `benchmark/atlas/gold.jsonl` |

用户只需使用一个入口。新标注绑定所选底图版本，坐标系为最终底图左上角像素，不使用浏览器缩放后的坐标。
旧 `map_first_annotations.jsonl`、`zurich_annotations.jsonl` 保留供旧命令行工具使用，不自动迁移其原图坐标。
主页统计统一采用当前底图版本的标注；旧版本的标注保留在历史中，不计入当前版本进度。
历史记录取对应底图版本的最新记录。保存时校验版本指纹；其他 GUI 窗口已保存的新版本
会触发冲突提示，当前窗口必须重新打开事件后再保存，不能静默覆盖。
避免同时使用旧终端工具和 GUI 编辑同一事件；旧工具不参与 GUI 的版本冲突协议。

欧洲导航使用现代国家边界，仅供选取战场。导航点为聚落附近的近似坐标，
不是事件发生点，也不写入标准几何。布萨科四条候选共用“内伊进攻”参考图。
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
- 当前参考图使用候选记录的文件；2026-09-24 换图未迁移任何旧坐标，苏黎世底图和标注未变。
