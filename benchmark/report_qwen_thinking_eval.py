"""Offline, provisional diagnostics for the frozen Zurich thinking experiment."""
from __future__ import annotations

import base64
from collections import Counter
import importlib.util
import io
import itertools
import json
import math
from pathlib import Path
import statistics

from PIL import Image, ImageDraw, ImageFont
from compare_grounding_methods import cell, costs, diagnose
from run_atlas_vlm import SYSTEM, digest, parse_geometry, read_package
from run_qwen_thinking_eval import final_answer, ROOT, RUNS, SOURCE, save

HERE = RUNS / "zurich10_qwen_thinking_20261013"
GPT = RUNS / "zurich10_gpt6_astra_20261007"
METHODS = {"qwen_instruct": HERE / "instruct", "qwen_thinking": HERE / "thinking", "gpt6_astra": GPT}
NAMES = {"qwen_instruct": "Qwen3-VL-8B Instruct", "qwen_thinking": "Qwen3-VL-8B Thinking", "gpt6_astra": "GPT-6 Astra (历史)"}
COLORS = {"qwen_instruct": "#087849", "qwen_thinking": "#a54a96", "gpt6_astra": "#066ed4"}
EXCLUDED = {"Z0009", "Z0010"}


def load(path):
    return json.loads(path.read_text())


def read_attempts(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def summary(rows, attempts):
    points = [r["distance_to_gold_px"] for r in rows.values()
              if r["gold_type"] == "point" and "distance_to_gold_px" in r]
    polygons = [r for r in rows.values() if "point_inside_gold" in r]
    thinking_counts = []
    for attempt in attempts:
        usage = attempt.get("usage") or {}
        thinking_counts.append(usage.get("thinking_tokens", (usage.get("output_tokens_details") or {}).get("reasoning_tokens")))
    return {
        "valid_geometry": sum(r["status"] == "valid" for r in rows.values()),
        "abstained": sum(r["status"] == "abstained" for r in rows.values()),
        "errors": sum(r["status"] == "error" for r in rows.values()),
        "error_types": dict(Counter(r.get("error_type", "unknown") for r in rows.values() if r["status"] == "error")),
        "point_n": len(points), "point_mean_px": statistics.mean(points) if points else None,
        "point_median_px": statistics.median(points) if points else None,
        "point_in_polygon": {"hits": sum(p["point_inside_gold"] for p in polygons), "scorable_n": len(polygons), "eligible_n": 2},
        "outside_map_correct": rows.get("Z0003", {}).get("outside_map_abstention") is True,
        "token_limit_ids": [a["event_id"] for a in attempts if (a.get("usage") or {}).get("reached_token_limit")],
        "thinking_tokens": sum(thinking_counts) if thinking_counts and all(n is not None for n in thinking_counts) else None,
        "cost": costs(attempts),
    }


def paired(rows, methods):
    ids = [eid for eid in next(iter(rows.values()))
           if all(rows[m][eid].get("gold_type") == "point" and "distance_to_gold_px" in rows[m][eid] for m in methods)]
    return {"compared_methods": list(methods), "event_ids": ids, "n": len(ids), "methods": {
        m: {"mean_px": statistics.mean(rows[m][eid]["distance_to_gold_px"] for eid in ids),
            "median_px": statistics.median(rows[m][eid]["distance_to_gold_px"] for eid in ids)}
        for m in methods if ids}}


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def figures(report, tasks, png, gold, out):
    # Reuse the existing original-pixel plotting and offline navigation conventions.
    drawing = load_module(GPT / "build_report_figures.py", "zurich_report_drawing")
    original = Image.open(io.BytesIO(png)).convert("RGB")
    for task in tasks:
        eid = task["event_id"]
        points = list((gold[eid].get("geometry") or {}).get("coordinates", []))
        for method in METHODS:
            points.extend((report["rows"][method][eid].get("geometry") or {}).get("coordinates", []))
        points = points or [[0, 0], list(original.size)]
        x0 = max(0, math.floor(min(p[0] for p in points)) - 90)
        y0 = max(0, math.floor(min(p[1] for p in points)) - 90)
        x1 = min(original.width, math.ceil(max(p[0] for p in points)) + 90)
        y1 = min(original.height, math.ceil(max(p[1] for p in points)) + 90)
        width, height = min(original.width, max(1000, x1 - x0)), min(original.height, max(400, y1 - y0))
        x0 = max(0, min(original.width - width, (x0 + x1 - width) // 2))
        y0 = max(0, min(original.height - height, (y0 + y1 - height) // 2))
        im = Image.new("RGB", (width, height + 150), "white")
        im.paste(original.crop((x0, y0, x0 + width, y0 + height)), (0, 104))
        draw = ImageDraw.Draw(im)
        drawing.text(draw, (16, 10), f"{eid} | Qwen3-VL 8B FP16 vs GPT-6 Astra", 24)
        drawing.text(draw, (16, 45), "Human (provisional)", 17, "#d42846")
        for index, method in enumerate(METHODS):
            name = {"qwen_instruct": "Instruct", "qwen_thinking": "Thinking", "gpt6_astra": "GPT-6 (historical)"}[method]
            if report["rows"][method][eid]["status"] == "error":
                name += ": no answer"
            elif report["rows"][method][eid]["status"] == "abstained":
                name += ": abstain"
            drawing.text(draw, (250 + index * 200, 45), name, 18, COLORS[method])
        drawing.text(draw, (16, 74), f"Native pixels | x={x0}, y={y0} | No coordinate repairs", 17)
        drawing.overlay(draw, gold[eid]["geometry"], (x0, y0), "#d42846", gold=True)
        for method in METHODS:
            drawing.overlay(draw, report["rows"][method][eid]["geometry"], (x0, y0), COLORS[method])
        drawing.text(draw, (16, height + 115), "Cross: provisional human label. Circles/outlines: model. Invalid outputs not drawn.", 17)
        im.save(out / f"{eid}_detail.png")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    point_ids = [eid for eid, a in gold.items() if a["status"] == "accepted" and a["geometry"]["type"] == "point" and eid not in EXCLUDED]
    fig, axes = plt.subplots(1, len(point_ids), figsize=(15, 5), sharey=True, layout="constrained")
    ymax = max([r.get("distance_to_gold_px", 0) for rs in report["rows"].values() for r in rs.values()] + [1]) * 1.16
    for ax, eid in zip(axes, point_ids):
        for x, method in enumerate(METHODS):
            d = report["rows"][method][eid].get("distance_to_gold_px")
            if d is None:
                ax.text(x, 25, "N/A", ha="center", rotation=90, fontsize=10)
            else:
                ax.bar(x, d, color=COLORS[method], width=.6)
                ax.text(x, d + 10, f"{d:.0f}", ha="center", fontsize=10)
        ax.set_title(eid)
        ax.set_xticks(range(3), ["Instruct", "Thinking", "GPT-6"], rotation=45, ha="right")
        ax.set_xlim(-.6, 2.6)
        ax.set_ylim(0, ymax)
        ax.grid(axis="y", alpha=.2)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Distance to provisional human point (px)")
    fig.suptitle("Zurich 10: primary 4096-token runs | N/A is not zero error", fontsize=14)
    fig.savefig(out / "point_errors.png", dpi=160)
    plt.close(fig)


def viewer(report, tasks, png, gold, out):
    template = load_module(GPT / "build_viewer.py", "zurich_existing_viewer").TEMPLATE
    # Correct a legacy select tag without editing the historical report.
    template = template.replace('</option value=', '</option><option value=')
    template = template.replace("qwen_native", "qwen_instruct").replace("gpt5", "qwen_thinking")
    template = template.replace("Qwen3-VL · 原像素", "Qwen3-VL-8B · Instruct").replace("GPT-5", "Qwen3-VL-8B · Thinking")
    template = template.replace("苏黎世 · 三模型对比", "苏黎世 · 4096-token 主实验")
    template = template.replace("#874bb1", COLORS["qwen_thinking"])
    template = template.replace(">Qwen3-VL</option>", ">Qwen3-VL-8B · Instruct</option>")
    template = template.replace("2026-10-07 / 08 · 人工答案待复核", "2026-10-13 · GPT-6 为历史对照 · 人工答案待复核")
    template = template.replace("模型输出区域，人工答案为点；不计入点误差。", "模型与人工几何类型不同；未计入点误差。")
    template = template.replace("function metric(r){", "function metric(r){if(r.error_type==='IncompleteThinking')return '思考被截断 · 无最终答案';")
    template = template.replace("'没有合法的预测几何。'", "r.error_type==='IncompleteThinking'?'已达到输出预算，思考未结束；没有可绘制的最终预测。':'没有合法的预测几何。'")
    data = {"tasks": tasks, "rows": report["rows"], "excluded": sorted(EXCLUDED),
            "gold": gold, "image": "data:image/png;base64," + base64.b64encode(png).decode()}
    icons = (ROOT / "benchmark/gui/vendor/lucide.js").read_text()
    html = template.replace("__LUCIDE__", icons).replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("<", "\\u003c"))
    (out / "comparison.html").write_text(html)


def main():
    manifest, png, tasks, instruction = read_package(SOURCE)
    expected = {t["event_id"]: t for t in tasks}
    gold_path = RUNS / "zurich10_20260916_162847/gold_snapshot.json"
    gold_data = load(gold_path)
    assert gold_data["map"]["image_sha256"] == manifest["image_sha256"]
    gold = {a["event_id"]: a for a in gold_data["annotations"]}
    report = {"metrics_kind": "provisional_pixel_diagnostics_not_benchmark_accuracy", "map": manifest,
              "gold_sha256": digest(gold_path.read_bytes()), "excluded": sorted(EXCLUDED),
              "rows": {}, "summaries": {}, "audit_hashes": {}}
    for method, directory in METHODS.items():
        assert load(directory / "completed.json")["completed_all_tasks"]
        predictions = load(directory / "predictions.json")
        assert predictions["map_version"] == manifest["map_version"]
        attempts = read_attempts(directory / "predictions.attempts.jsonl")
        assert len(attempts) == len(tasks) and {a["event_id"] for a in attempts} == set(expected)
        if method != "gpt6_astra":
            config = load(directory / "manifest.json")
            assert config["do_sample"] is False and config["quantization"] is None
            assert config["input_sha256"] == digest(SOURCE.read_bytes())
        by_id = {p["event_id"]: p for p in predictions["predictions"]}
        errors = {e["event_id"]: e for e in predictions["errors"]}
        assert not set(by_id) & set(errors) and set(by_id) | set(errors) == set(expected)
        for a in attempts:
            eid = a["event_id"]
            assert a["task"] == expected[eid] and a["instruction"] == SYSTEM + instruction
            assert a["image_sha256"] == manifest["image_sha256"] and a["max_output_tokens"] == 4096
            if method != "gpt6_astra":
                prep = a["usage"]["image_preprocessing"]
                assert prep["original_pixels_verified"] and prep["content_scale_xy"] == [1.0, 1.0]
                assert prep["processed_size_wh"] == [1568, 1760]
                assert a["local_config"]["dtype"] == "torch.float16"
            if eid in by_id:
                text = a["raw"] if method == "gpt6_astra" else final_answer(a["raw"], method == "qwen_thinking")
                assert parse_geometry(text, expected[eid]) == by_id[eid]
        rows = {}
        for eid in expected:
            rows[eid] = diagnose(gold[eid], by_id.get(eid), errors.get(eid), eid in EXCLUDED)
            rows[eid]["geometry"] = by_id.get(eid, {}).get("geometry")
        report["rows"][method] = rows
        report["summaries"][method] = summary(rows, attempts)
        report["audit_hashes"][method] = digest((directory / "predictions.attempts.jsonl").read_bytes())
    report["paired_points"] = {
        "+".join(ms): paired(report["rows"], ms)
        for ms in [*itertools.combinations(METHODS, 2), tuple(METHODS)]}
    supplemental = {}
    for mode in ("instruct", "thinking"):
        directory = HERE / (mode + "_8192")
        if not directory.exists():
            assert not report["summaries"]["qwen_" + mode]["token_limit_ids"], "Required supplemental run is missing"
            continue
        assert load(directory / "completed.json")["completed_all_tasks"]
        attempts = read_attempts(directory / "predictions.attempts.jsonl")
        assert {a["event_id"] for a in attempts} == set(report["summaries"]["qwen_" + mode]["token_limit_ids"])
        for a in attempts:
            assert a["max_output_tokens"] == 8192 and a["task"] == expected[a["event_id"]]
            assert a["image_sha256"] == manifest["image_sha256"] and a["instruction"] == SYSTEM + instruction
            assert a["usage"]["image_preprocessing"]["original_pixels_verified"]
            if a.get("prediction") is not None:
                assert parse_geometry(final_answer(a["raw"], mode == "thinking"), a["task"]) == a["prediction"]
        supplemental[mode] = [{"event_id": a["event_id"], "status": a["status"],
                               "prediction": a.get("prediction"), "error_type": a.get("error_type"),
                               "diagnostic": diagnose(gold[a["event_id"]], a.get("prediction"),
                                                      {"error_type": a["error_type"]} if a["status"] == "error" else None,
                                                      a["event_id"] in EXCLUDED),
                               "usage": a["usage"], "elapsed_seconds": a["elapsed_seconds"]} for a in attempts]
    report["supplemental_8192"] = supplemental
    out = HERE / "review"
    out.mkdir(exist_ok=True)
    save(out / "diagnostics.json", report)
    (out / "gold_snapshot.json").write_bytes(gold_path.read_bytes())
    figures(report, tasks, png, gold, out)
    viewer(report, tasks, png, gold, out)
    thinking = report["summaries"]["qwen_thinking"]
    thinking_supplement = supplemental.get("thinking", [])
    supplemental_answers = sum(a["status"] in {"valid", "abstained"} for a in thinking_supplement)
    comparison = report["paired_points"]["qwen_instruct+gpt6_astra"]
    lines = ["# 苏黎世十题：Qwen3-VL 普通版、Thinking 与 GPT-6 对照", "",
             "实验日期：2026-10-13（Europe/Zurich）。Qwen 两组为本轮非量化 FP16 实跑；GPT-6 为 2026-10-07/08 历史结果，本轮没有调用付费 API。", "",
             "**本报告使用仍有争议的旧人工标签，只能解释为诊断结果，不是正式准确率或模型排名。**", "",
             "[逐题高清交互对比](comparison.html) · [原定实验协议](../PROTOCOL.md) · [结构化结果](diagnostics.json)", "",
             "## 摘要", "",
             f"- Thinking 主实验：{thinking['valid_geometry']} 条有效几何、{thinking['abstained']} 条合法拒答、{thinking['errors']} 条输出失败。8192-token 补充测试：{supplemental_answers}/{len(thinking_supplement)} 条可解析最终答案（包含拒答）。",
             "- 没有最终坐标时，无法计算 Thinking 的空间误差；不能把 N/A 写成 0% 定位准确率，也不能声称普通版在空间推理能力上胜过 Thinking。",
             f"- Instruct 与 GPT-6 共同可评的 {comparison['n']} 个点题，平均偏差分别为 {comparison['methods']['qwen_instruct']['mean_px']:.1f} px 和 {comparison['methods']['gpt6_astra']['mean_px']:.1f} px。这只是对暂定人工点的偏差，不是经过仲裁的真实定位误差。",
             "- 这轮首先暴露了受限预算、greedy 解码下的任务完成问题。下一步优先验证推荐采样设置和坐标遵循能力，不宜直接扩大实验规模或据此做模型排名。", "",
             "## 1. 实验条件", "",
             "- 两套官方 8B 权重，均以 float16 在同一 Mac 的 MPS 上运行，一次加载一个模型；不使用 4-bit 权重。BF16 存储权重加载成 FP16，并非 FP32。",
             "- 沿用冻结的十个问题、英文原文和提示词。原图 1538×1754，仅右/下补白至 1568×1760，do_resize=False；各题实际输入尺寸及像素哈希均已校验。",
             "- 主实验均为 4096 输出 token 上限。Qwen 两组 greedy 解码；Thinking 的思考 token 也占用此预算，只有结束思考后的最终 JSON 参与评分。",
             "- GPT-6 使用同一原 PNG 与任务，4096 上限、默认推理参数；其内部图像处理与计算量不受我们控制，因此不是严格等算力比较。",
             "- 不提供人工标注、不搜索、不修正坐标、不按回答质量挑选重跑。Z0009/Z0010 沿用实验前排除规则；Z0003 单列图外拒答。", "",
             "## 2. 主实验输出与开销", "",
             "| 模型 | 有效几何 | 合法拒答 | 格式/输出失败 | 达到 token 上限 | 总推理秒数 | 输出 tokens |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for m, s in report["summaries"].items():
        lines.append(f"| {NAMES[m]} | {s['valid_geometry']}/10 | {s['abstained']} | {s['errors']} | {len(s['token_limit_ids'])} | {s['cost']['seconds']:.1f} | {s['cost']['output_tokens']} |")
    lines += ["", "耗时不含下载和模型加载；本机与云端耗时仅作工作流开销记录，不能用于比较硬件效率。合法几何不等于正确位置。", "",
              "失败分类：" + "；".join(f"{NAMES[m]}：" + (", ".join(f"{k} {v} 条" for k, v in s["error_types"].items()) or "无") for m, s in report["summaries"].items()) + "。",
              "IncompleteThinking 表示输出未出现完整思考结束标记，没有可评分的最终答案；不能用其草稿位置计算误差。", "",
              "## 3. 对暂定人工标签的空间诊断", "",
              "| 模型 | 可评点数/5 | 点误差均值 px | 点误差中位数 px | 区域命中/可评点数 | 图外题 Z0003 |",
              "|---|---:|---:|---:|---:|---:|"]
    number = lambda v: "N/A" if v is None else f"{v:.1f}"
    for m, s in report["summaries"].items():
        poly = s["point_in_polygon"]
        region = f"{poly['hits']}/{poly['scorable_n']}" if poly["scorable_n"] else "N/A (0/2 可评)"
        outside = "正确拒答" if s["outside_map_correct"] else "错误定位" if report["rows"][m]["Z0003"]["status"] == "valid" else "无最终答案"
        lines.append(f"| {NAMES[m]} | {s['point_n']}/5 | {number(s['point_mean_px'])} | {number(s['point_median_px'])} | {region} | {outside} |")
    lines += ["", "各行可评点子集不同，不可直接用均值相除声称提升。区域题共两题，命中分母只计算有效点预测；其他几何不自动取中心。失败、拒答和未评分项不记为零误差。", "",
              "![逐题点误差](point_errors.png)", "", "### 同题配对", ""]
    for p in report["paired_points"].values():
        names = " / ".join(NAMES[m] for m in p["compared_methods"])
        lines.append(f"- {names}，共同有效点 n={p['n']}：{', '.join(p['event_ids']) or '无'}。" + "；".join(f"{NAMES[m]} {v['mean_px']:.1f} px" for m, v in p["methods"].items()))
    lines += ["", "## 4. 逐题结果", "", "| 事件 | Instruct | Thinking | GPT-6 历史 | 原像素图 |", "|---|---|---|---|---|"]
    for eid in expected:
        lines.append(f"| {eid} | " + " | ".join(cell(report["rows"][m][eid]) for m in METHODS) + f" | [查看]({eid}_detail.png) |")
    lines += ["", "图中红色十字/边界为旧人工标签，绿色为 Instruct，紫色为 Thinking，蓝色为 GPT-6。图件保留原像素局部裁切；交互查看器支持原比例查看。", "",
              "## 5. 8192-token 补充实验", "",
              "按运行前规则，仅对主实验达到上限的请求增加预算，两个版本采用相同规则；下表不回填主实验结果。", "",
              "| 模式 | 事件 | 状态 | 输出 tokens | 思考 tokens | 再次达到上限 | 秒数 | 独立空间诊断 |", "|---|---|---|---:|---:|---|---:|---|"]
    for mode, records in supplemental.items():
        for a in records:
            lines.append(f"| {mode} | {a['event_id']} | {a['status']} {a.get('error_type') or ''} | {a['usage']['output_tokens']} | {a['usage']['thinking_tokens']} | {a['usage']['reached_token_limit']} | {a['elapsed_seconds']:.1f} | {cell(a['diagnostic'])} |")
    if not supplemental:
        lines.append("尚无补充实验记录。")
    lines += ["", "补充测试只覆盖各自触及上限的题目，两种模式的补充子集可能不同。上面的对比图与主表仅展示 4096-token 主实验，不混入补充预测。"]
    lines += ["", "## 6. 具体错误与下一步", "",
              "### Z0004：从文本识别地名，不等于能在地图上定位", "",
              "目标是 Klein 出发前所在的 Altstetten。Thinking 的原始输出已提取出该地名，随后反复尝试寻找地图位置，但主实验没有提交最终 JSON。这是对中间输出的定性观察，不把草稿当作成功答案。下图只绘制正式解析成功的坐标；Thinking 没有预测图层。",
              "", "![Z0004 原像素局部对照](Z0004_detail.png)", "",
              "### Z0003：缺少图上证据时的拒答", "",
              "该题文本目标为 Regensdorf，冻结标注将其记为图外。Instruct 仍给出位置；历史 GPT-6 返回合法拒答；Thinking 主实验被截断。三种结果必须分别记录，未完成不等于正确拒答。", "",
              "### Z0009：生成失控不只是格式问题", "",
              "Instruct 在道路问题上持续生成规律递增的坐标。8192-token 输出已延伸到 x 约 29,000，而地图宽度只有 1,538；同时 JSON 尚未闭合。因此，补一个括号或只增加预算不足以让这条输出成为合法路线。本轮不裁剪、不截取前几个点、不修补输出。该题的旧人工真值也不适合道路目标，因此按预先规则不计空间分数。", "",
              "### 建议的下一轮", "",
              "1. 先选少量固定诊断题，验证官方推荐的非 greedy 采样设置，并单独记录解码参数、种子、终止原因和完整输出。它是新的探索性实验，不能覆盖本轮失败记录。",
              "2. 增加明确地名定位检查，核对模型是否真正遵循原图像素坐标，而不是事后按人工答案缩放或移动预测点。",
              "3. 冻结经过人工仲裁的答案和几何粒度，再扩大到不同地图；当前仅三个共同有效点，不宜计算总体提升倍数。", "",
              "配置来源：[Qwen3-VL 官方仓库的推理参数](https://github.com/QwenLM/Qwen3-VL)。官方推荐采样与更长生成预算，本轮为沿用历史控制条件的 greedy 设置；两者不可混称。", "",
              "## 7. 解释边界", "",
              "- Instruct 与 Thinking 是不同训练权重，不是同一模型的纯开关消融；差异不能全部归因于输出了思考过程。",
              "- 本次 greedy、受限预算是受控诊断配置，不等同于作者推荐的采样配置与更长输出预算；截断尤其不能等同于模型不知道答案。",
              "- 旧人工标注存在点/面粒度和主体混淆等问题。本轮不以 GPT-6 或未经审核的 AI 候选替换真值；距离缩短只意味着更接近旧标签。",
              "- 十题共享一张地图和四段文本，缺乏独立战场覆盖；不能从这一轮证明一般模型优劣或论文方法有效性。",
              "- 当前网页底图、人工审核记录和旧实验输出均未修改。", "", "## 8. 审计文件", "",
              "- [Instruct 预测](../instruct/predictions.json) · [原始输出](../instruct/predictions.attempts.jsonl)",
              "- [Thinking 预测](../thinking/predictions.json) · [原始输出](../thinking/predictions.attempts.jsonl)",
              "- [Instruct 8192 补充预测](../instruct_8192/predictions.json) · [原始输出](../instruct_8192/predictions.attempts.jsonl)",
              "- [Thinking 8192 补充预测](../thinking_8192/predictions.json) · [原始输出](../thinking_8192/predictions.attempts.jsonl)",
              "- [GPT-6 历史预测](../../zurich10_gpt6_astra_20261007/predictions.json)",
              "- [冻结旧人工标签](gold_snapshot.json) · [结构化统计与来源哈希](diagnostics.json)", "",
              "模型资料：[Instruct](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct)、[Thinking](https://huggingface.co/Qwen/Qwen3-VL-8B-Thinking)。", ""]
    (out / "RESULTS.md").write_text("\n".join(lines))
    print(json.dumps({"summaries": report["summaries"], "pairs": report["paired_points"]}, indent=2))


if __name__ == "__main__":
    main()
