"""Lenient reply repair for the Qwen no-none ablation (2026-11-28).

Uses the project-wide unified lenient parser, code/make_lenient_final260.py (same rule for every model,
Lukaka "方案一", 2026-11-28), so this ablation is scored exactly like the main lenient table:
a reply the strict parser reads is left as is; otherwise make_lenient_final260.lenient() is tried
(L1 missing type, L2 other coordinate layout, L3 truncated reply). {"type": "none"} stays 0.
"""
import importlib.util
import json
import os
from pathlib import Path

PKG = Path(__file__).resolve().parents[3] / "benchmark/exports/eval_v2_20261119"
_cwd = os.getcwd()
os.chdir(PKG)  # the module loads code/convert_predictions.py by a path relative to the package
try:
    _spec = importlib.util.spec_from_file_location("make_lenient_final260", PKG / "code/make_lenient_final260.py")
    ml = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ml)
finally:
    os.chdir(_cwd)

LENIENT_RULE = "unified lenient parser code/make_lenient_final260.py (2026-11-28; L1 missing type, L2 coordinate layout, L3 truncated)"


def lenient_raw(raw, w, h):
    """Return (raw, note): raw unchanged with note None, or the canonical JSON the unified parser read."""
    if ml.strict_ok(raw, w, h):
        return raw, None
    res = ml.lenient(raw, w, h)
    if not res:
        return raw, None
    obj, note = res
    return json.dumps(obj), note
