#!/usr/bin/env python3
"""Audit candidate coverage, without treating draft events as accepted gold."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def coverage(records, battles, scope):
    by_battle = {b["id"]: b for b in battles}
    maps = {}
    for row in records:
        battle = by_battle[row["battle_id"]]
        country = row.get("country") or battle["country"]
        # Different downloads of identical image bytes do not add map coverage.
        key = (country, row.get("map_asset_sha256") or row["image"])
        group = maps.setdefault(key, {"image": row["image"], "events": set(),
                                     "battle_ids": set(), "external_text": 0})
        if row["event_id"] not in group["events"]:
            group["external_text"] += row.get("evidence_tier") == "external_text"
        group["events"].add(row["event_id"])
        group["battle_ids"].add(row["battle_id"])
    countries = defaultdict(list)
    for (country, _), group in maps.items():
        countries[country].append({**group, "event_count": len(group["events"]),
                                  "events": sorted(group["events"]),
                                  "battle_ids": sorted(group["battle_ids"])})
    rows = []
    targets = {c["name"]: c for c in scope["countries"]}
    for country in sorted(set(targets) | set(countries)):
        groups = countries[country]
        eligible = sum(m["event_count"] >= scope["min_events_per_map"] for m in groups)
        rows.append({"country": country, "maps": groups, "map_count": len(groups),
                     "event_count": sum(m["event_count"] for m in groups),
                     "qualifying_maps": eligible,
                     "candidate_quota_met": eligible >= scope["min_maps_per_country"],
                     "scope_note": targets.get(country, {}).get("note", "范围外新增国家，需审核")})
    return {"scope_confirmed": scope["confirmed"], "country_basis": scope["country_basis"],
            "complete": scope["confirmed"] and all(r["candidate_quota_met"] for r in rows),
            "countries": rows, "map_count": len(maps),
            "event_count": sum(r["event_count"] for r in rows),
            "countries_with_candidate_quota": sum(r["candidate_quota_met"] for r in rows),
            "min_maps_per_country": scope["min_maps_per_country"],
            "min_events_per_map": scope["min_events_per_map"]}


def markdown(report):
    lines = ["# 国家覆盖审核", "", "更新：2026-09-24。由 `benchmark/country_coverage.py` 生成。", "",
             "## 口径与限制", "",
             "暂按今天的国家边界、欧洲陆地战场、1792–1815 年统计，保留法国革命战争样本。用户尚未确认此口径。",
             "本清单是工作范围草案，不是经过穷尽考证的全部交战国名录；国家参战不等于本土有战斗。",
             "北欧、地中海和早期战事的纳入边界仍须确认；不将英美战争、殖民战事或同期独立战争自动并入。",
             "", "**统计的是有文本候选的参考地图，不是已标注、已核实、可评测的底图。**",
             "同一图像的重复下载不计两张；不同图版可以计数，但同一战役仍须共享训练/测试分组。",
             "图注/部署符号转述与独立文本必须分层，不能因为达到四条就声称有四条独立史料支持。", "",
             f"当前：{report['map_count']} 张参考图、{report['event_count']} 条事件；"
             f"{report['countries_with_candidate_quota']} 个国家满足候选数量门槛。全范围完成：否。", "",
             "| 国家 | 参考图 | 候选事件 | 每图≥4条的图数 | 候选配额 | 范围/缺口说明 |",
             "|---|---:|---:|---:|---|---|"]
    for row in report["countries"]:
        status = "数量达标，待审核" if row["candidate_quota_met"] else "缺图或缺事件"
        lines.append(f"| {row['country']} | {row['map_count']} | {row['event_count']} | "
                     f"{row['qualifying_maps']} | {status} | {row['scope_note']} |")
    lines += ["", "## 已接入地图", "", "| 国家 | 图版/战场 ID | 候选数 | 文件 |", "|---|---|---:|---|"]
    for row in report["countries"]:
        for group in row["maps"]:
            lines.append(f"| {row['country']} | {', '.join(group['battle_ids'])} | "
                         f"{group['event_count']} | `{group['image']}` |")
    lines += ["", "## 接下来", "",
              "1. 确认国家边界与年代口径，再核定未覆盖国家是否属于论文范围。",
              "2. 对新增 88 条逐条审核，特别是 64 条地图推导样本；补独立叙事，不将其直接列为正式推理测试。",
              "3. 补足每个缺口国家两张可辨识、具有事件依据的图；不以裁切、翻色或仅有地形的地图凑数。",
              "4. 每张参考图另配干净模型输入底图，完成至少四条可接受事件的人工几何标注。",
              "5. 区分候选配额、通过审核配额和最终可评测配额。当前脚本只检查第一项。", "",
              "资料与逐事件问题：[扩充审核清单](MAP_EXPANSION_REVIEW.md)。",
              "地图目录：[The Napoleon Series Maps](https://www.napoleon-series.org/military-information/maps/)。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    from annotation_server import BATTLES, DATASETS
    records = []
    for source, _ in DATASETS:
        records.extend(json.loads(line) for line in (ROOT / source).read_text(encoding="utf-8").splitlines() if line.strip())
    scope = json.loads((ROOT / "benchmark/country_scope.json").read_text(encoding="utf-8"))
    report = coverage(records, BATTLES, scope)
    content = json.dumps(report, ensure_ascii=False, indent=2) if args.json else markdown(report)
    if args.output:
        args.output.write_text(content + ("\n" if args.json else ""), encoding="utf-8")
    else:
        print(content)
    return 1 if args.require_complete and not report["complete"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
