"""Summarize frozen label ablation outputs without assigning human ground truth."""
import io
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from compare_grounding_methods import draw_geometry
from run_atlas_vlm import read_package

BASE = Path(__file__).resolve().parent
RUN = BASE / "runs/coordinate_ablation_parsed"
rows = [json.loads(line) for line in (RUN / "attempts.jsonl").read_text().splitlines()]
summary = {"accuracy": None, "reason": "pending independent human label boxes", "modes": {}}
lines = ["# 坐标链路与地名定位初测", "", "## 设计", "",
         "Qwen3-VL-8B；同一张 1816 年苏黎世底图；八个地名文字中心；两种坐标约定。",
         "本轮不含事件推理，也不是此前十条事件的重跑。人工文字框尚未审核，不能计算定位准确率。", "",
         "## 输入尺寸", ""]
metadata = rows[0]["usage"]["image_preprocessing"]
summary["image_preprocessing"] = metadata
lines += [f"- 原图：{metadata['original_size_wh']}；模型处理后：{metadata['processed_size_wh']}（宽、高）。",
          f"- patch size={metadata['patch_size']}，merge size={metadata['merge_size']}，视觉 tokens={metadata['visual_tokens']}。",
          "- 这张图没有被大幅下采样；这不能排除原图文字不清、视觉密度或模型识读能力的影响。", "",
          "## 输出有效性（不是准确率）", "",
          "| 坐标提示 | 调用 | 原解析器有效输出 | 明确结构转换后有效点 | 转换后错误 | 推理秒数 |",
          "|---|---:|---:|---:|---:|---:|"]
for mode, color in (("pixels", "#2479d8"), ("normalized_1000", "#bc3857")):
    group = [r for r in rows if r["mode"] == mode]
    stats = {"calls": len(group), "strict_valid": sum(r["original_status"] == "valid" for r in group),
             "valid_points": sum(r["status"] == "valid" for r in group),
             "errors": sum(r["status"] == "error" for r in group),
             "format_normalizations": sum(bool(r.get("prediction", {}).get("format_normalization")) for r in group),
             "elapsed_seconds": sum(r["elapsed_seconds"] for r in group)}
    summary["modes"][mode] = stats
    lines.append(f"| {mode} | {stats['calls']} | {stats['strict_valid']} | {stats['valid_points']} | {stats['errors']} | {stats['elapsed_seconds']:.1f} |")
    _, png, _, _ = read_package(RUN / f"full_{mode}.zip")
    image = Image.open(io.BytesIO(png)).convert("RGB")
    for attempt in group:
        geometry = attempt.get("prediction", {}).get("geometry")
        if attempt["status"] != "valid" or not geometry:
            continue
        draw_geometry(image, geometry, color)
        x, y = geometry["coordinates"][0]
        ImageDraw.Draw(image).text((x+14, y+8), attempt["event_id"], fill=color)
    image.save(BASE / f"{mode}_predictions.png")
lines += ["", "## 日志与解释", "",
          "- 模型使用了 [x,y]，不是要求的 [[x,y]]。保留 strict-schema 失败，再用可测试的结构转换单独解析。",
          "- 结构转换只给单点增加一层列表，不改数值。只有显式 normalized_1000 组做 x/1000×宽、y/1000×高换算。",
          "- 原像素提示组绝不根据目视效果再乘比例；没有启发式坐标制式猜测。",
          "- 原始调用：runs/coordinate_ablation_v2；离线派生：runs/coordinate_ablation_parsed。派生过程零模型调用。",
          "- 第一轮 coordinate_ablation 因日志序列化中断，不纳入这张表。",
          "- 部分相同地名在两组返回接近的数值，这是坐标指令遵循需要重点复核的信号，并非已验证的因果结论。", "",
          "## 目视观察（不作为人工真值）", "",
          "相对坐标组 P001/ZURICH、P003/Albisrieden 的预测接近对应文字；但 P008/Horgen 仍落在 ZURICH 文字处。",
          "这说明坐标约定值得优先控制，但不能将它当作所有失败的唯一解释。这里不据此给出命中率。", "",
          "## 程序检查", "",
          "- 已知像素经过裁切、0/90/180/270 度旋转及结果图绘制的测试通过。",
          "- 非正方形图归一化、裁剪偏移/缩放还原、边界拒绝、缺少 GT 不计分均有回归测试。",
          "- 此前参考图日志 grid=[1,106,136]，patch=16，对应 2176×1696，原图 2177×1699；同样不是大幅下采样。",
          "- 这些检查尚不能证明模型一定正确读取地图或遵守指定坐标约定。", "",
          "## 下一步", "",
          "先在独立 8769 标注页完成八个人工文字框与置信度，再使用 PLACE_DIAGNOSTICS.md 中的 score 命令。",
          "预测图不自动导入待标注页。最好先完成独立标注，再查看下列结果，避免锚定偏差。", "",
          "- [原像素提示预测图](pixels_predictions.png)",
          "- [相对坐标提示预测图](normalized_1000_predictions.png)",
          "- [官方坐标示例](https://github.com/QwenLM/Qwen3-VL/blob/main/cookbooks/2d_grounding.ipynb)", ""]
(BASE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
(BASE / "RESULTS.md").write_text("\n".join(lines))
print(json.dumps(summary, indent=2))
