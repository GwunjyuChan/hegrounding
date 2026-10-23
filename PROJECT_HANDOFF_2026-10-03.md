# HE-Grounding 项目进度与 Agent 交接

整理日期：2026-10-03。项目根目录：`/Users/ericchen/thesis/hegrounding`。

**2026-10-07 后续更新：** 已用 Qwen3-VL 在保持冻结底图原始像素的条件下重跑苏黎世十题，见文末第 14 节。

**同日后续更新：** 用户随后要求清理无关文件，已完成一轮保守清理，范围与新测试结果见文末第 13 节。正文中“本次仅整理交接”指最初的文档整理，不包含这次后续清理。

本文依据当前本地代码、数据、项目文档及本任务的实施记录整理。**本次仅整理交接，没有重新运行模型、重新检查生产服务器或修改标注。** 线上状态最后验证于 2026-09-29；下一位 agent 操作前应重新核对。

## 1. 给下一位 Agent 的快速说明

这是历史事件在历史地图上的视觉定位硕士论文项目，不是普通地名经纬度查询网站。

- 当前研究主线：历史段落 + 指定实体、事件与时刻的问题 + 地图，输出地图上的点、线或区域。
- 已有可用的网页标注平台，部署在 <https://experiment.chanlukaka.com/>。
- 当前本地活动候选为 **26 张参考图、110 条事件**；不是 110 条已验收真值，也不是完成的正式 benchmark。
- 苏黎世十事件已跑过直接定位、纯文本地点问答、Qwen 两阶段和作战参考图诊断；另有八地名定位实验。
- 当前研究瓶颈是可靠真值、文字识读与视觉定位，不能只继续换模型或扩大候选数量。
- 最新完成的产品修改：统一任务内底图编辑、独立地名实验、登录页面、中英切换，**默认英文**。
- 上一次用户问如何修改登录账号密码；已解释服务器修改方法并建议账号设置页面，**尚未授权或实现账号设置页面，也没有改密码**。
- 本地与服务器研究数据不自动同步。**绝不能用本地旧数据覆盖服务器上的新标注。**

建议先读本文，再按用户的新请求定位文件，不需要重做旧 HLS 流程或重新搭建整个网站。

## 2. 研究目标与范围

### 核心任务

例：“部队驻扎在河东岸，交战后退到村南树林，炮兵留在桥边。”问题指定“撤退后的步兵位置”。模型需要区分实体、动作、时间和地理关系，再定位到地图。当前输出可以是静态几何，**不要求重建完整行军轨迹**。

文本地点问答是辅助诊断/两阶段中间结果，不替代最终地图定位任务。地名文字中心定位也是隔离视觉能力的对照实验，不等同于历史事件定位。

### 方向演变

1. 早期使用 HLS 瑞士历史词典，扩展战争、交通和工业事件，做现代位置核验。
2. 因历史事件难以可靠标注，转向法国革命与拿破仑战争的地图和文本。
3. 以 The Napoleon Series 的 [Maps 目录](https://www.napoleon-series.org/military-information/maps/) 为参考图来源，先选可读部署图，再找对应叙事、报告和部署信息。
4. 将“参考作战图”和“不含事件答案的模型输入底图”分开，避免模型直接读取部署标记。
5. 目前并行推进候选资料审核和苏黎世小规模定位失败诊断。

### 会议与论文材料

- `meetings/9.3meeting.whisper`：原始转写。
- `todo/2026-09-03-follow-up.md`：9 月 3 日会议解读与行动清单。核心是可信 benchmark、静态定位、证据和点线面定义，训练不是前置条件。
- `meetings/9.17meeting.whisper`：后续会议转写。
- `plan/weekly_plan_2026-09-17_meeting.md`：重点诊断事件理解、图像尺度、历史地图域差异、视觉 grounding 的错误来源。
- `proposal/proposal_v3_swiss_vlm.md` 和中文快读版：旧阶段 proposal。**不能假定该版本已完整反映当前拿破仑地图任务和线上平台。**
- `relative_work/`：相关研究资料；既有记录包括 FRIEDA、OmniMapBench。文件存在不等于已完成阅读或比较。

会议、计划、proposal、相关论文及整个 `todo/` 被 Git 忽略；新 agent 若只得到远程仓库，可能没有这些本地资料。

## 3. 数据现状

| 对象 | 当前位置 / 状态 |
|---|---|
| 第二次苏黎世十事件 | `benchmark/zurich_pilot_10.jsonl`，Z0001–Z0010，本次读取确认 10 条 |
| Maps 优先扩展候选 | `benchmark/map_first_candidates.jsonl`，本次读取确认 100 条 |
| 覆盖审核 | `benchmark/COUNTRY_COVERAGE.md`、`country_scope.json`、`country_coverage.py` |
| 扩展配置与证据审核 | `benchmark/map_expansion_battles.json`、`MAP_FIRST_CANDIDATES.md`、`MAP_EXPANSION_REVIEW.md` |
| 历史参考图 | `maps/napoleon_maps/`、`maps/zurich_pilot/` |
| 图像来源与版本 | `benchmark/atlas/originals/`、`assets/`、`sources.jsonl`、`maps.jsonl` |
| 本地事件人工记录 | `benchmark/atlas/gold.jsonl`，本次确认 19 条追加历史，**不是 19 个不同事件** |
| 本地事件预测记录 | `benchmark/atlas/predictions.jsonl`，本次确认 42 条追加历史，**不是 42 个不同样本** |
| 实验输出 | `benchmark/atlas/runs/`、`benchmark/diagnostics/` |
| 十条问题/文本便于核对版 | 根目录 `ZURICH_10_QUESTIONS_AND_TEXTS.md` |

### 国家配额不是完成验收

用户期望：在本土发生过相关战斗的国家，每国至少两张地图，每图至少四事件。

目前有 13 国达到**候选数量**门槛：瑞士、法国、西班牙、葡萄牙、意大利、德国、奥地利、比利时、荷兰、捷克、波兰、俄罗斯、白俄罗斯。瑞士 14 条，其余每国 8 条，合计 110 条。

- 暂按现代国界、欧洲陆地战场、1792–1815 年统计；这一范围尚未由用户最终确认。
- 不代表所有相关国家已覆盖，缺口见 `COUNTRY_COVERAGE.md`。
- 扩展批次新增 88 条中，64 条属于地图推导，尚需独立文本支持；不能包装成独立叙事推理题。
- 同一战役或共享底图的样本不能随意拆到训练和测试两侧。

### 已退出活动集的数据

旧 Borkowo、Sochocin、Wavre 三图及 20 条候选已归档；Wkra 合图也因可读性问题退出。不要因 Git 中显示删除就恢复它们。

旧 HLS 提取、地理处理和实验在 `archive/`；该目录本地保留、被 Git 忽略。旧 500 米命中指标不适用于当前未地理配准的历史图像任务。

## 4. 干净历史底图

三层数据必须区分：

1. **参考地图**：原始作战部署图，用于核对史实，可以含军队、箭头和阵位。
2. **标注底图 / 模型输入图**：固定版本的图像，不烘焙人工标注或模型预测。
3. **人工答案**：单独保存的几何、证据、审核状态、置信度和容差，不能进入模型输入。

“不烘焙标注”不等于“原图没有答案泄漏”。用户显式选择参考图作为底图时，图像已有的军事符号仍存在。上传图也需要人工审核，不能自动标为无泄漏。

干净地图来源清单：`benchmark/CLEAN_BASEMAP_AUDIT.md`。目前是逐图检索和适配性初筛，**未为 26 张图全部完成底图获取和验收**。

- 苏黎世已有 Usteri 1816 州图的导入和裁切，源页 <https://www.e-rara.ch/zuz/content/titleinfo/8751704>。它晚于 1799 战役 17 年，不能写成 1799 年地图。
- 圣塞巴斯蒂安：Tofiño / Ballester 1788 测绘、1789 出版的港城图是较好候选；朝南，需核对旋转、范围和具体工事。
- 图卢兹：1808 Grandvoinet / Pommian 城市周边图是近同期候选；1814 临时工事不一定存在于该图。
- 滑铁卢/四臂村：Ferraris 系列是候选方向；仍需核定图幅与目标覆盖。
- 其余图的年代、授权、清晰度、范围等风险见清单，不要把“找到系列入口”写成“已获取可用底图”。

更换、裁切或旋转底图必须建立新版本。**不同底图之间不可按宽高比例自动搬运旧真值。** 不用生成式修补或超分产生的细节当历史证据。

## 5. 平台当前功能与交互约定

### 事件标注

- 主页为欧洲战场入口，选择战役后进入事件工作区。
- 未设置底图时默认预览参考图，用户可确认使用它，或在当前任务中上传/编辑另一张图。
- 已有底图时直接进入事件标注；“编辑底图”属于当前任务，不是和标注并列的另一条导航。
- 支持 PDF/图像导入、裁切、直角旋转、尺寸限制、底图历史恢复。
- 支持点/线/区域、撤销/重做、证据、统一要素词表、1–5 置信度、审核状态、像素容差。
- 支持旧事件重标、版本冲突检查、按模型显示 GPT-5/Qwen 预测、独立导出输入包、人工答案和叠加图。
- 保存追加历史，不覆盖旧版；只取对应事件和底图版本的最新记录。事件预测按模型区分，尚无同模型所有运行批次的完整选择 UI。

### 独立地名实验

- 不依赖欧洲战场或事件，上传自己的地图即可新增地名、标注和查看预测。
- 左上 HE 回到平台首页；线上 `/labels/` 直接打开地名实验。
- 任务是**地名文字中心/文字区域定位**，不是村庄中心或事件位置。
- 用户先标注多个地点，再统一运行一批。界面不提供逐条模型运行按钮。
- 本地一批只加载一次 Qwen，每地名独立请求，不共享聊天历史；不是一次生成全部地名。
- 支持整批历史结果、模型名、人工/模型图层、对比误差、结果 JSON 和对比图。
- 线上无 Qwen 权重，使用“导出预测输入包 → 本地推理 → 导入模型 JSON”。

### 登录与语言

- 已有独立登录页，替代浏览器 Basic Auth 弹窗；单账号，支持退出。
- 中英切换覆盖登录、主页、事件标注和地名实验。
- **默认英文**；明确选过中文则保留中文；使用 `localStorage['he-language']`。
- 切换不刷新编辑器，不重置输入或几何；事件原文、问题、自定义名字、人工证据和模型回答不自动翻译。
- 账号设置/改密页面**未实现**。上次只是提出建议，没有修改实际账号密码。

## 6. 实验结果：可引用到什么程度

**当前都是小规模诊断；合法坐标不等于正确定位，不能报告成正式 benchmark 总准确率。**

| 实验 | 已记录结果 | 重要限制 |
|---|---|---|
| 苏黎世 10 事件直接定位 | GPT-5 有效几何 9/10；Qwen3-VL-8B 8/10 | 只表示格式/边界有效；真值与文本仍待独立复核 |
| Qwen 直接 vs 两阶段 | 有效几何 8/10 vs 9/10；共同成功点样本 n=4，平均误差 432.4 vs 400.5 px | 成功子集有选择偏差；两阶段多一次调用；两路点落入人工区域均为 0/2 |
| Qwen 作战参考图输入 | 有效几何 9/10，对照干净底图 8/10 | 参考图没有独立真值，不能量化准确率变化；覆盖、风格和提示同时改变 |
| 八地名坐标提示消融 | pixels 和 normalized_1000 两组，严格格式各 0/8；显式单点结构转换后各 8/8 有效 | `[x,y]` 包装成 `[[x,y]]` 不改数值；没有合格 GT 时不报告命中率 |
| 9 月 23 日交互八地名实验 | 有效 8/8；按当时各题容差命中 2/8 | 1161×946 裁切图；容差不全相同，部分置信度缺失或较低，仅诊断 |

### 结果索引

- 十事件直接比较：`benchmark/atlas/runs/zurich10_20260916_162847/RESULTS.md`，含 `input.zip`、gold 快照、诊断 JSON、逐题对比图。
- 纯文本地点回答：`benchmark/atlas/runs/zurich10_text_20260916_170435/REVIEW.md`。
- 两阶段比较：`benchmark/atlas/runs/zurich10_qwen_staged_20260917_012804/comparison/RESULTS.md`。
- 参考图输入：`benchmark/atlas/runs/zurich10_reference_20260917_021309/review/RESULTS.md`。
- 坐标诊断：`benchmark/diagnostics/zurich_labels_20260921/RESULTS.md`。原始完整运行 `runs/coordinate_ablation_v2/`，派生解析 `runs/coordinate_ablation_parsed/`；`runs/coordinate_ablation/` 是中断记录。
- 八地名批次：`benchmark/diagnostics/zurich_labels_20260921/workspace/benchmark/atlas/place_lab/runs/bc5c63c8409d4836b8a16610654670d8/review/`，含 `RESULTS.md`、`comparison.png`、`experiment.json`。

### 不可忽略的真值问题

- Z0009 问道路路段，旧人工答案却是点；Z0010 问城区，旧证据/几何对应另一人的撤退道路。两条先前从主要空间评分排除，需独立复核，不能默认已经修好。
- Z0003 的 `outside_map` 与特定裁切绑定；在含 Regensdorf 的参考图上不能继续沿用图外标签。
- Z0001/Z0006 的登陆岸与出发岸，Z0002 的林地/高地对象也需复核。
- 苏黎世事件实验用过 1538×1754 图，交互地名实验用过 1161×946 图，当前活动裁切可能另有版本；只按冻结 manifest/hash 匹配，不依据地图名称合并结果。
- 当前只有点距离、点落入区域等诊断；完整线/面指标尚待完善。不同尺度的像素误差不可直接横比或说成米。

## 7. 关键代码与数据结构

| 文件 | 责任 |
|---|---|
| `benchmark/annotation_server.py` | 标注 HTTP 服务、数据集与战场入口、公共部署模式 |
| `benchmark/atlas_store.py` | 底图来源/版本、事件标注、模型预测、输入包导出；事件定位 prompt 在 `export()` |
| `benchmark/gui/app.js`、`index.html` | 主页与欧洲导航 |
| `benchmark/gui/atlas.js`、`atlas.html`、`atlas.css` | 事件标注和任务内底图编辑 |
| `benchmark/gui/atlas-api.js` | 请求与 CSRF 令牌刷新、有限安全重试 |
| `benchmark/gui/workspace-url.js` | 根路径和 `/labels/` 挂载、工作区导航 |
| `benchmark/place_lab.py` | 地名任务/真值/批次、导出与导入；地名输入 prompt 在 `export_input()` |
| `benchmark/place_lab_worker.py`、`run_place_batch.py` | 本地后台批量推理及提交入口 |
| `benchmark/gui/place-lab.*` | 独立地名实验界面 |
| `benchmark/run_atlas_vlm.py` | ZIP 输入校验、API/本地 Qwen 推理；`load_local_qwen()` 和 `call_local_qwen()` 定义本地后端 |
| `benchmark/run_text_location_eval.py` | 纯文本问答，`INSTRUCTION` 是文本任务 prompt |
| `benchmark/run_qwen_grounding_comparison.py`、`compare_grounding_methods.py` | 两阶段实验与独立离线评分 |
| `benchmark/place_diagnostics.py` | pixels/normalized_1000 对照、重解析、评分；`instruction(mode)` 定义提示 |
| `benchmark/export_place_results.py` | 已有批次离线导出对比图和 JSON，不重跑模型 |
| `benchmark/web_auth.py`、`gui/login.*`、`gui/session-ui.js` | 登录网关、登录页与会话操作 |
| `benchmark/gui/i18n.js`、`i18n.css` | 中英词表、动态绑定与布局补充 |
| `deploy/` | 部署配置、验证、登录说明及历史发布记录 |

地名实验数据在各工作区的 `benchmark/atlas/place_lab/` 下：`maps.jsonl`、`tasks.jsonl`、`gold.jsonl`、`predictions.jsonl`、`runs/<job_id>/`。批次保存冻结输入、干净地图、原始回答、进度和日志。

模型输入只包含任务需要的图像、文本/地名和坐标规则。**不得加入人工几何、证据、置信度或已有预测。** 回看一次实验的实际输入，应优先看该次冻结 ZIP、`prompt.txt` 和原始调用日志，而不是只看今天的代码。

## 8. 本地运行与验证

以下命令在 `/Users/ericchen/thesis/hegrounding` 执行。依赖见 `pyproject.toml`、`uv.lock`，Python 3.12+，已有 `.venv`；PDF 导入依赖 Poppler。

```bash
# 主事件工作区；脚本不传 --port 时默认 8765，这里显式使用 8767。
bash benchmark/run_annotation_gui.sh --port 8767

# 独立地名实验；data-root 与主工作区不同。
bash benchmark/run_annotation_gui.sh --port 8769 \
  --data-root benchmark/diagnostics/zurich_labels_20260921/workspace

# 回归测试，HTTP 测试需要临时本机端口权限。
MPLCONFIGDIR=/tmp/hegrounding-mpl .venv/bin/python -m unittest discover -s benchmark -p 'test_*.py'
node --test benchmark/test_atlas_api.cjs benchmark/test_i18n.cjs

# 本地地名批次预览，不运行模型；实际运行另加 --execute。
.venv/bin/python benchmark/run_place_batch.py
```

线上导出的 ZIP 可先无成本验证：

```bash
.venv/bin/python benchmark/run_atlas_vlm.py --input /absolute/path/input.zip

# 只有明确需要实际运行时才加 --execute；输出使用新的文件路径。
.venv/bin/python benchmark/run_atlas_vlm.py \
  --input /absolute/path/input.zip \
  --backend qwen-local --model Qwen/Qwen3-VL-8B-Instruct \
  --limit 10000 --execute --output /absolute/path/new-predictions.json
```

- `run_atlas_vlm.py` 默认只跑 1 条；`--limit` 必须按任务明确设置。
- 本地 Qwen 只使用已有缓存，不读 API key、不自动下载模型；模型缓存是否仍可用需运行前核对。
- API 模式使用根目录 `.env` 的 `OPENAI_API_KEY`；**不读取或输出密钥来做交接，不假定历史额度错误已解决**。
- ZIP 地名输入当前使用原图像素坐标；`run_place_batch.py` 默认 0–1000 相对坐标。不能混用，按运行 manifest 转换。
- 输出目录/文件不覆盖旧实验。失败保留原始日志；不猜坐标制式、不裁掉越界值、不伪造定位点。
- 不要停掉未知用途的旧服务，或用多个服务同时写同一个数据根目录；UI 测试只用数据副本。

最后完成的验证：2026-09-29 全套 104 项 Python、17 项 JavaScript 测试通过；随后默认英文修改又通过 17 项 JS 测试，线上脚本与本地逐字节一致。**这不是 10 月 3 日重新运行的结果。**

## 9. 线上部署交接

### 访问和进程

- 平台：<https://experiment.chanlukaka.com/>
- 登录：<https://experiment.chanlukaka.com/login.html>
- 事件：<https://experiment.chanlukaka.com/atlas.html>
- 地名：<https://experiment.chanlukaka.com/labels/place-lab.html>
- SSH：`ssh root@66.154.115.22 -p 22`。
- 发布入口：`/opt/hegrounding/current`。最后记录指向 `/opt/hegrounding/releases/20260929T161311Z-i18n`，随后对 `i18n.js` 做了默认英文的原子热更新。
- Python 环境：`/opt/hegrounding/venv`。
- `hegrounding@events`：`127.0.0.1:8877`，数据 `/var/lib/hegrounding/events`。
- `hegrounding@labels`：`127.0.0.1:8879`，数据 `/var/lib/hegrounding/labels`。
- `hegrounding-auth`：`127.0.0.1:8880`。
- Caddy 主配置 `/etc/caddy/Caddyfile`，本站片段 `/etc/caddy/hegrounding.caddy`；服务器还有其他站点，不能整体替换配置。

### 数据保护

- 线上新增标注只写服务器，没有自动回传本地。部署仅更新代码。
- 9 月 29 日最后一次完整发布，停写窗口内校验 183 个数据文件哈希均未改变。
- 当时保存历史：事件 gold 19、事件预测 42；地名 gold 16、地名预测 10。地名活动任务 8 条。
- 当时活动事件底图版本匹配的预测数为 0，不代表历史预测丢失，而是旧记录绑定旧图。
- 最近完整发布备份：`/root/hegrounding-before-i18n-20260929T161311Z`；是当时快照，不是未来新增标注的备份。
- 没有已配置的自动异地备份；下次更新先检查当前数据并备份，不假定还只有 183 文件。

### 认证与密钥

- 单账号，会话 Cookie 为 Secure/HttpOnly/SameSite=Lax，12 小时有效；重启认证服务使已有会话失效。
- 密码只以加盐 scrypt 哈希存于 `/etc/hegrounding-auth.json`，root:hegrounding、0640。
- 运维私有凭据文件：本地 `.deploy/access.txt`、服务器 `/root/hegrounding-access.txt`。**不要打印、复制到交接文档、提交 Git，或把密码写入命令参数。**
- `deploy/verify.py` 用服务器私有凭据验证登录，因此将来改账号时需同步维护验证方式；本地旧凭据不会自动更新。
- 网关保留 Origin、JSON 请求和限速校验；标注服务保留 CSRF、Host/Origin 和版本校验。不要为解决 Unauthorized 错误移除安全检查。
- 线上推理禁用，服务器没有 Qwen 权重或 OpenAI API key。
- 运维说明：`deploy/README.md`、`deploy/LOGIN.md`、`deploy/DEPLOYMENT_STATUS.md`。
- 不要在现有部署上重跑旧初始化安装器；它包含早期 Basic Auth 引导逻辑。

## 10. 建议下一阶段工作

以下是建议，不代表已获用户授权立刻执行全部工作。

1. **冻结可信诊断真值**：先独立复核 5–10 条高置信度地名及必要事件；确认对象、时刻、文字中心/地物位置、点线面和容差，避免看模型结果后反向改 GT。
2. **完成 full/crop 配对实验**：相同目标、模型与提示，裁切保持原始分辨率和足够上下文，目标不要总在正中心；记录坐标变换。当前未有已完成该对照的证据。
3. **完成历史/Siegfried/现代图对照**：同地点尽量匹配范围及可读尺度，各图独立标 GT。当前未有完成该对照的证据。
4. **审核文本地点回答和错误类型**：区分事件理解错误、地图识读错误、坐标指令错误、精度不足、GT 不确定；“文字答案经常正确”仍需要系统人工审核。
5. **补干净底图与独立史料**：优先少量可读、近同期、可追溯地图；审核 64 条地图推导候选，补叙事或分层，不以国家配额取代证据质量。
6. **完善评测设计**：预先固定合理容差/允许区域、线面指标、拒答处理、置信度分层、地图/战役分组划分；不能事后选择最好看的阈值。
7. **修订论文与汇报**：围绕可信数据及失败诊断组织贡献，proposal 需与当前任务对齐，而不是只描述平台开发。
8. **按用户后续需求做账号管理**：若明确要求，再实现验证当前密码的账号设置页、原子凭据更新、会话失效和安全回归；当前只停留在建议。

## 11. Git 与旧文档注意事项

- 本次读取到最新提交为 `20527c0`，2026-09-21，`Snapshot Napoleon atlas annotation and Zurich grounding experiments`。
- 工作树有大量修改、未跟踪文件和有意删除项，包括部署、登录、双语、地名实验及扩展数据。**网站已上线不等于这些改动已提交/推送 Git。**
- 不要 `git reset --hard`、恢复旧候选，或批量删除未跟踪文件。提交前检查新资产、许可证、数据体积和敏感文件；不要直接 `git add .` 后推送。
- `.env*`、`.venv`、`.deploy/`、`archive/`、`meetings/`、`plan/`、`proposal/`、`relative_work/`、`todo/` 等被忽略。
- 根目录 `PROJECT_PROGRESS_2026-09-13.md`、README 的部分段落、`todo/` 的数量和早期诊断入口存在旧阶段信息；优先用本文、当前 JSONL/代码和有日期的实验快照交叉核对。
- `README.md` 中仍可见“当前三张/四张”“22 条”等阶段性叙述，不能覆盖当前 26 图/110 候选统计。

## 12. 建议接手顺序

1. 先确认用户此次具体目标，不默认继续开发账号设置或立即跑付费模型。
2. 查看 `git status --short`，保留全部已有改动。
3. 按任务阅读 `ATLAS_README.md`、`PLACE_LAB.md` 或 `deploy/LOGIN.md`，再看相关实现。
4. 涉及结果比较先匹配冻结输入、底图版本/hash 和 gold 快照；涉及线上操作先核对服务、发布路径与当前数据。
5. 在隔离数据中测试，说明本次实际验证范围；不能把旧测试、旧准确率或旧线上统计说成刚测得的新结果。

可给下一位 agent 的开场提示：

> 请先阅读项目根目录 `PROJECT_HANDOFF_2026-10-03.md`，结合当前代码核对进度。保留工作树改动和所有研究数据；服务器标注与本地不自动同步，不要用本地快照覆盖线上数据。先理解历史事件定位、独立地名诊断和不同底图版本的区别，再执行我接下来提出的具体任务。

## 13. 2026-10-03 无关文件清理

- 删除初始化占位 `main.py`（仅打印 Hello，未被项目引用）。
- 删除与论文实验无关的 `tmp/pdfs/build_cv.py`、两张简历预览 PNG 和 `output/pdf/Guanyu_CV_EN.pdf`。
- 删除不再使用的 `.claude/settings.local.json`、项目代码的四个 `__pycache__` 目录和六个 `.DS_Store`。
- 移除清空后的 `.claude/`、`tmp/`、`output/` 和原本为空的 `eval/` 目录。
- 保留 `.venv`、`.env`、`.deploy`、所有研究数据/结果/历史版本，以及论文、会议、相关研究和交接文档。本轮未修改服务器。
- 特别保留 `vlm_eval.py`（当前推理脚本仍导入 `load_env_file`）和 `zurich_pilot_5.jsonl`（回归测试使用的不可变快照）。
- 旧归档 `archive/` 约 1.1 GB，用户已于 2026-10-03 明确选择先保留；不要删除或移出，后续调整需用户重新授权。
- 清理后实际重新验证：107 项 Python 测试、17 项 JavaScript 测试全部通过；测试使用 `PYTHONDONTWRITEBYTECODE=1`，未调用真实模型。
- 本轮只是清理少量无关文件和缓存，未做大规模空间释放，也未提交 Git。

## 14. 2026-10-07 保持原像素的十题重跑

- 用户要求重新运行第二次苏黎世战役十题，保持底图像素不变。为与旧结果比较，使用 9 月 16 日冻结输入，不是当前网页活动裁切。
- `run_atlas_vlm.py` 新增可选 `--preserve-image-pixels`，仅用于 `qwen-local`；默认行为保持不变。
- 原图 1538×1754，右补白 30、下补白 6 至 1568×1760，`do_resize=False`。原图 RGB 哈希及十次实际处理尺寸均已校验；原点和内容像素不变，没有恢复原扫描已丢失的细节。
- 使用相同 Qwen3-VL-8B 缓存、MPS/float16、greedy、4096 输出预算和原提示词；未调用付费 API。
- 新结果：9/10 有效几何、0 拒答、1 错误；五个共同点样本平均误差 418.9 px（旧 424.1），中位数 346.1 px（旧 358.6）；区域命中仍为 0/2。
- Z0003 在图外目标上仍给坐标，不因有效输出数上升宣称准确率提升。Z0009 生成大量越界道路顶点至 4096 token 截断，JSON 解析失败，耗时约 357.6 秒。总推理约 501.5 秒。
- Z0009/Z0010 继续排除主要空间评分；人工真值未更改，未发布到网页旧/新底图。
- 报告与对比图：`benchmark/atlas/runs/zurich10_native_pixels_20261007/review/RESULTS.md`，同目录有十张逐题图、总览及诊断 JSON；上级包含冻结输入、原图、补白画布、预测和逐次原始日志。
- 完成 110 项 Python 回归测试。此轮只支持“关闭轻微重采样未明显改善这批样本”，不能外推为大图降采样没有影响。

## 15. 2026-10-07/08 GPT-6 Astra 十题比较

- 用户要求调用 GPT-6 比较效果。账号可用模型包含 `gpt-6-astra`，本轮明确使用该 ID，API 返回模型 ID 一致；没有改用 GPT-6.1 或其他系列。
- 使用相同冻结十题、提示词和 1538×1754 原 PNG；Responses API、4096 输出 token、无工具、无重试。reasoning 未显式指定，十次返回元数据均为 medium。客户端未缩放，不能验证服务端图像预处理不缩放。
- 10 次 API 调用均完成，耗时约 108.0 秒；8 条合法几何、1 条拒答、1 条格式错误。Z0001 返回 `[311,100]` 而非 `[[311,100]]`，保留为错误，不补救重跑。Z0005 返回 polygon，而人工答案为 point，未纳入点误差。
- 与保持原像素 Qwen 的 3 个共同有效点（Z0002/Z0004/Z0006）比较，均值 323.1 → 28.9 px，降低 91.1%。与旧 GPT-5 的 2 个共同有效点（Z0004/Z0006）比较，484.4 → 34.2 px，降低 92.9%。不同配对子集不能混为全部十题准确率。
- Z0007/Z0008 两个点落入人工区域，2/2；此前 Qwen/GPT-5 均为 0/2。Z0003 正确返回图外拒答，此前两模型仍给坐标。
- Z0009/Z0010 沿用事前评分排除规则，但均完成推理。单张图、暂定 GT、历史对照、不同内部视觉/推理预算，仍不足以说明一般化性能提升。
- 结果目录：`benchmark/atlas/runs/zurich10_gpt6_astra_20261007/`；`predictions.json`、原始响应与 usage、冻结输入、参数、推理脚本和离线评分脚本都已保存。`review/RESULTS.md`、`diagnostics.json`、十张逐题对比图及总览可供复核。
- 本轮未修改生产推理脚本、网页图层、人工标注或服务器。完成输入/提示/hash/事件覆盖断言及对比图目视核查；未重跑全项目回归测试。实验跨过当地午夜，于 2026-10-08 00:00 完成，目录保留开始日期。
- 2026-10-08：总览拼图过小，新增 `review/comparison.html` 离线高清查看器（由同级上层 `build_viewer.py` 生成）。嵌入原 PNG 和已有诊断数据，逐题切换、三模型同步缩放/拖动、单模型视图、1:1、原像素 PNG 导出；报告首部已有入口。没有重新推理或改变评分，未发布线上。
- 2026-10-08：新增根目录中文详报 `ZURICH_MODEL_COMPARISON_REPORT_2026-10-08.md`，含九张原像素局部图/误差图、十题误差分析、能力边界和下一阶段安排。图件及可重算补充统计位于该实验的 `review/report_figures/`，由 `build_report_figures.py` 生成。特别区分主分数与事后诊断：Z0001 原始数字若仅补数组层级，距 GT 9.1 px，但主评分仍是格式错误；Z0005 人工点在预测面外，距该面 128.0 px，不纳入点均值。十题只涉及四段文本，三个模型共同有效点只有 Z0004/Z0006。未重新调用模型、修改标注或发布线上。
