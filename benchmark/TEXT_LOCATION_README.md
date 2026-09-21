# 文本地点问答评估

用途：检查模型是否能从事件正文中回答指定主体、动作和时间的地点，再由人工审核。
输入只有英文正文、事件问题和事件 ID；不发送地图、像素尺寸、参考图、人工答案、要素提示或审核备注。
本地后端仍使用 Qwen3-VL-8B-Instruct，但本轮只启用文本输入，不调用视觉输入。

## 本轮结果

[苏黎世十条人工审核表](atlas/runs/zurich10_text_20260916_170435/REVIEW.md)。
两模型使用前一轮冻结输入包中的同一组十条正文和问题，各自独立处理每个事件。
问题文字保持原样；统一指令说明将其中的画图要求改为地点文字描述。
所有答案保留英文原始输出，不由助手翻译或改写后冒充模型答案。

Z0003 不受底图范围限制，可根据正文回答。Z0010 也按原问题回答，不将旧人工道路几何当文字答案。
正确率须待人工审核后计算；结构化返回成功、引用确实存在于原文，都不等于答案正确。

## 审核内容

- 主体是否正确：例如 Bontemps 旅与 Oudinot 主力不能混淆。
- 时间是否正确：出发前、渡河后、撤退后不能混淆。
- 地点及关系是否准确：不能只因地名相同就判对，也不能擅自添加东/西、左/右岸。
- 粒度是否合理：正文只支持城后高地时，不要求编造具体山名或精确营地。
- 证据是否支持答案：逐字引用只是可检查性保障，引用了正确原句也可能答错目标。

在 REVIEW.md 每个模型答案下填写人工判定和备注，或填写同目录的 human_review.jsonl。
这两个文件不是自动双向同步的表单；请选一种作为权威审核记录，避免互相矛盾。
建议判定：正确、部分正确、错误、合理拒答、不合理拒答、无法判定。
不修改 answers.json 或 attempts.jsonl，它们是模型原始输出及审计记录。

## 再次执行

在项目根目录运行；不加 `--execute` 时仅验证输入，不读取 key 或加载模型：

```bash
.venv/bin/python benchmark/run_text_location_eval.py \
  --input benchmark/atlas/runs/zurich10_20260916_162847/input.zip \
  --output-dir benchmark/atlas/runs/my_text_run/gpt5 \
  --model gpt-5 --limit 10 --execute

.venv/bin/python benchmark/run_text_location_eval.py \
  --input benchmark/atlas/runs/zurich10_20260916_162847/input.zip \
  --output-dir benchmark/atlas/runs/my_text_run/qwen3vl8b \
  --model Qwen/Qwen3-VL-8B-Instruct --backend qwen-local --limit 10 --execute
```

GPT-5 使用 `.env` 中的 OPENAI_API_KEY 和 Responses API；本地 Qwen 不读取 key、不联网。
默认最多 4096 输出 token；GPT-5 包含推理 token。本轮不自动重试，不通过改答案修复失败。
必须使用尚不存在的输出目录，避免覆盖旧实验。每个模型目录包含：

- `prompt.txt`：冻结后的统一指令，源码为 `run_text_location_eval.py` 的 INSTRUCTION。
- `tasks.jsonl`：实际文本任务，仅包含 event_id、passage、question。
- `manifest.json`：输入哈希、参数、模型及本地运行配置。
- `answers.json`：结构化地点、证据和不确定性；全部有待人工判断。
- `attempts.jsonl`：完整提示词、原始回复、使用量、耗时和错误；API 不完整响应原因也保留。

离线合并两模型结果，生成审核文件（已存在时拒绝覆盖）：

```bash
PYTHONPATH=benchmark .venv/bin/python -c 'from pathlib import Path; from run_text_location_eval import write_review; p=Path("benchmark/atlas/runs/my_text_run"); write_review([p/"gpt5", p/"qwen3vl8b"], p)'
```

## 实验解释

本轮同时改变输入模态和输出任务，不是严格的“只移除图片”消融实验。
它能帮助定位文本理解与地图定位两个环节的问题，但文字答对不能直接证明模型具备视觉地理定位能力。
不把这些文字答案写进地图人工真值或地图模型图层；先前的像素评估与标注均不受影响。
