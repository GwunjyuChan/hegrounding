"""One row per map image and per text source, for the thesis bibliography. Rebuild after adding items."""
import csv, json
from collections import OrderedDict

rows = [json.loads(l) for l in open("benchmark/map_first_candidates.jsonl")]
rows += [json.loads(l) for l in open("benchmark/sources/pilot_zurich2_2026-10-20.jsonl")]

maps, texts = OrderedDict(), OrderedDict()
for r in rows:
    m = maps.setdefault(r["image"], {"kind": "map", "key": r["image"], "battle_id": r["battle_id"], "events": [],
        "citation": r.get("map_provenance", ""), "url": r.get("map_url", ""), "sha256": r.get("map_asset_sha256", ""),
        "rights": "", "status": r.get("map_kind", "")})
    m["events"].append(r["event_id"])
    if r.get("text_kind") == "verbatim_source_passage" or r.get("source_citation"):
        key = r.get("source_citation") or r.get("article_url")
        status = "translated: " + r["translation_review"] if r.get("translation_by") else "verbatim"
    else:
        key, status = "NO SOURCE: map-derived / AI paraphrase", "needs replacement text"
    t = texts.setdefault(key, {"kind": "text", "key": key, "battle_id": r["battle_id"], "events": [], "citation": key,
        "url": r.get("article_url", "") if not key.startswith("NO SOURCE") else "", "sha256": r.get("source_raw_sha256", ""),
        "rights": r.get("source_rights", ""), "status": status})
    t["events"].append(r["event_id"])
    if t["battle_id"] != r["battle_id"] and r["battle_id"] not in t["battle_id"]:
        t["battle_id"] += ";" + r["battle_id"]

out = "benchmark/sources/SOURCE_REGISTER.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, ["kind", "battle_id", "events", "citation", "url", "sha256", "rights", "status"])
    w.writeheader()
    for d in list(maps.values()) + list(texts.values()):
        d = dict(d); d.pop("key"); d["events"] = " ".join(d["events"]); w.writerow(d)
print(out, len(maps), "maps", len(texts), "text sources")
