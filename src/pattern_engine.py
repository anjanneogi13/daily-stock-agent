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
