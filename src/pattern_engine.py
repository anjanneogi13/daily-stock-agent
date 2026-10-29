"""T47 / Pillar 3 Phase 1: Pattern Engine — runs all detectors per ticker.

Reads OHLCV via data_fetcher.fetch_ohlcv (or accepts a df directly for
test-friendliness). Writes detected matches to data/patterns.jsonl with
ticker + date + regime snapshot for later outcome attribution.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.patterns import ALL_DETECTORS

PATTERNS_LOG = Path("data/patterns.jsonl")

# Detectors (src/patterns/base.py) index Title-case OHLCV columns, but
# data_fetcher.fetch_ohlcv() lowercases every column. Until 2026-10-29 the
# resulting KeyError was swallowed per-detector, so every nightly scan reported
# 0 matches across 100 tickers and pattern_stats.json stayed empty for the
# engine's whole life. Normalise here so either casing works.
_OHLCV_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


def _detector_frame(df):
    """Return ``df`` with Title-case OHLCV columns (copy only when renaming)."""
    if df is None:
        return None
    cols = list(getattr(df, "columns", []))
    if all(c in cols for c in _OHLCV_COLUMNS):
        return df
    lower_map = {str(c).lower(): c for c in cols}
    rename = {}
    for want in _OHLCV_COLUMNS:
        src = lower_map.get(want.lower())
        if src is not None and src != want:
            rename[src] = want
    if not rename:
        return df
    return df.rename(columns=rename)


def scan_ticker(ticker: str,
                df=None,
                detectors=None,
                regime: Optional[str] = None) -> List[Dict]:
    """Run all detectors against one ticker. Returns list of match dicts."""
    detectors = detectors or ALL_DETECTORS
    if df is None:
        try:
            from src.data_fetcher import fetch_ohlcv
            df = fetch_ohlcv(ticker, period="3mo")
        except Exception:
            return []
    if df is None or len(df) == 0:
        return []
    df = _detector_frame(df)
    out = []
    for det in detectors:
        try:
            m = det.detect(df)
        except Exception:
            m = None
        if m is None:
            continue
        rec = m.to_dict()
        rec["date"]      = datetime.now().date().isoformat()
        rec["ticker"]    = ticker.upper()
        rec["direction"] = det.direction
        rec["regime"]    = regime
        out.append(rec)
    return out


def persist(matches: List[Dict],
            path: Optional[Path] = None) -> int:
    """Append matches to patterns.jsonl. Returns count written."""
    if not matches:
        return 0
    path = path or PATTERNS_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        for m in matches:
            f.write(json.dumps(m) + "\n")
    return len(matches)


def persist_pick_time_matches(picks: List[Dict],
                              pick_date: str,
                              regime: Optional[str] = None,
                              path: Optional[Path] = None) -> int:
    """Persist the patterns that fired on OFFICIAL picks at pick time.

    pattern_stats.build_stats() joins patterns.jsonl with picks_log.csv on
    (ticker, date). The nightly scan only stamps the scan date, so before
    2026-10-29 a pick's own patterns never met its own outcome and the
    pattern layer could not learn. The scorer already stores the fired
    pattern names in scores["pattern_matches"] (comma-joined); replay them
    here with date = pick_date so every official pick feeds the stats.
    """
    recs: List[Dict] = []
    for p in picks or []:
        scores = (p or {}).get("scores") or {}
        names = scores.get("pattern_matches") or ""
        if not isinstance(names, str):
            continue
        ticker = str((p or {}).get("ticker") or "").upper()
        if not ticker:
            continue
        for name in {n.strip() for n in names.split(",") if n.strip()}:
            recs.append({
                "pattern":    name,
                "ticker":     ticker,
                "date":       pick_date,
                "regime":     regime,
                "direction":  None,
                "confidence": None,
                "source":     "pick_time",
                "multiplier": scores.get("pattern_multiplier"),
            })
    return persist(recs, path=path)


def load_recent(days: int = 30,
                path: Optional[Path] = None) -> List[Dict]:
    """Read recent pattern matches, newest-last."""
    path = path or PATTERNS_LOG
    if not path.exists():
        return []
    cutoff = datetime.now().date()
    out = []
    for line in path.read_text().splitlines():
        if not line.strip(): continue
        try:
            r = json.loads(line)
            d = datetime.fromisoformat(r["date"]).date()
            if (cutoff - d).days <= days:
                out.append(r)
        except Exception:
            continue
    return out
