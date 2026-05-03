"""T47 / Pillar 3 Phase 1: per-pattern × per-regime stats aggregator.

Joins data/patterns.jsonl (detected) with data/picks_log.csv (outcomes
for picks that match the same ticker+date) to build a stats table:

  {
    "bull_flag": {
      "bull": {"n": 42, "wins": 28, "win_rate": 0.667, "mean_r": +0.45},
      "chop": {"n": 11, "wins": 4,  "win_rate": 0.364, "mean_r": -0.10},
    },
    ...
  }

Writes data/pattern_stats.json. Used by hypothesis-engine + Telegram
to surface 'this pattern has 67% WR in bull regime, n=42'.
"""
from __future__ import annotations
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

PATTERNS_LOG = Path("data/patterns.jsonl")
PICKS_LOG    = Path("data/picks_log.csv")
STATS        = Path("data/pattern_stats.json")


def _to_float(v):
    try: return float(v)
    except (TypeError, ValueError): return None


def _read_jsonl(p: Path) -> List[Dict]:
    if not p.exists(): return []
    out = []
    for line in p.read_text().splitlines():
        if not line.strip(): continue
        try: out.append(json.loads(line))
        except: pass
    return out


def _read_picks(p: Path) -> List[Dict]:
    if not p.exists(): return []
    with p.open() as f:
        return list(csv.DictReader(f))


def build_stats(patterns_path: Optional[Path] = None,
                picks_path: Optional[Path] = None) -> Dict:
    """Aggregate. Joins on (ticker, date)."""
    matches = _read_jsonl(patterns_path or PATTERNS_LOG)
    picks   = _read_picks(picks_path or PICKS_LOG)

    # index picks by (ticker, pick_date) -> list of r_multiples
    by_key = defaultdict(list)
    for p in picks:
        key = (str(p.get("ticker","")).upper(),
               str(p.get("pick_date","")))
        r = _to_float(p.get("r_multiple"))
        if r is not None:
            by_key[key].append(r)

    # accumulate per (pattern, regime)
    bucket = defaultdict(lambda: {"n": 0, "wins": 0, "rs": []})
    for m in matches:
        key = (str(m.get("ticker","")).upper(), str(m.get("date","")))
        rs = by_key.get(key, [])
        if not rs:
            continue
        regime = m.get("regime") or "unknown"
        pat    = m.get("pattern") or "unknown"
        for r in rs:
            b = bucket[(pat, regime)]
            b["n"] += 1
            if r > 0: b["wins"] += 1
            b["rs"].append(r)

    out: Dict[str, Dict[str, Dict]] = {}
    for (pat, regime), b in bucket.items():
        n = b["n"]
        rs = b["rs"]
        out.setdefault(pat, {})[regime] = {
            "n":        n,
            "wins":     b["wins"],
            "win_rate": round(b["wins"]/n, 3) if n else 0.0,
            "mean_r":   round(sum(rs)/n, 3) if n else 0.0,
            "total_r":  round(sum(rs), 3) if rs else 0.0,
        }
    return out


def save(stats: Dict, path: Optional[Path] = None) -> Path:
    path = path or STATS
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(stats, indent=2) + "\n")
    return path


def load(path: Optional[Path] = None) -> Dict:
    path = path or STATS
    if not path.exists():
        return {}
    return json.loads(path.read_text())
