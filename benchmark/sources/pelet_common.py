"""Pelet, Mémoires sur la guerre de 1809 (French): shared source records and OCR drop rules for the text-first specs."""
from textfirst_lib import RAW

PELET_T2 = dict(
    file=RAW + "pelet1809_t2_mmoiressurlague04pelegoog_djvu.txt", archive_id="mmoiressurlague04pelegoog",
    citation="Jean-Jacques-Germain Pelet, Mémoires sur la guerre de 1809, en Allemagne, tome second (Paris: Roret, 1824)",
    source_kind="primary_narrative (memoir-history by Masséna's aide-de-camp, an eyewitness)",
    rights_basis="published 1824; author d. 1858")
PELET_T4 = dict(
    file=RAW + "pelet1809_t4_mmoiressurlague02pelegoog_djvu.txt", archive_id="mmoiressurlague02pelegoog",
    citation="Jean-Jacques-Germain Pelet, Mémoires sur la guerre de 1809, en Allemagne, tome quatrième (Paris: Roret, 1826)",
    source_kind="primary_narrative (memoir-history by Masséna's aide-de-camp, an eyewitness)",
    rights_basis="published 1826; author d. 1858")
# Google scan footers ("c,qi,it!dt, Google", "n,gN..(JNGOO»^IC", ...) and bracketed page numbers ("( 2o4)", "(i36)").
PELET_DROP = [r"[GC][oO0][oO0]", r"^\(\s*.{1,8}\)\s*$"]
