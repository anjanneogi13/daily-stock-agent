"""T49 / Pillar 3 Layer 6: pattern signal → probability engine.

Reads pattern_stats.json + recent matches and returns a per-ticker
multiplier that the probability engine can apply to its base score.

Multiplier = 1.0 (neutral) by default.
  - If a high-confidence pattern fires AND its (pattern, regime) bucket
    has historical edge (n≥20, mean_r > +0.2), multiply by up to 1.15
  - If a high-confidence pattern fires AND historical edge is negative
    (mean_r < -0.2), multiply by down to 0.85
  - Patterns disabled by hypothesis-engine return 1.0 (no effect)
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from src.pattern_engine import scan_ticker, load_recent
from src import pattern_stats as _ps


MIN_SAMPLE_FOR_EDGE = 20
EDGE_R_THRESHOLD    = 0.20
MAX_BOOST           = 0.15   # ±15% multiplier max
DISABLED_KEY        = "_disabled"


def _get_edge(stats: Dict, pattern: str, regime: str) -> Optional[float]:
    """Returns mean_r for (pattern, regime) if n ≥ MIN_SAMPLE, else None."""
    pat = stats.get(pattern, {})
    bucket = pat.get(regime) or pat.get("unknown")
    if not bucket: return None
    if bucket.get("n", 0) < MIN_SAMPLE_FOR_EDGE:
        return None
    return float(bucket.get("mean_r", 0))


def _is_disabled(stats: Dict, pattern: str) -> bool:
    return bool(stats.get(DISABLED_KEY, {}).get(pattern, False))


def pattern_multiplier(ticker: str,
                       regime: Optional[str] = None,
                       df=None,
                       stats: Optional[Dict] = None) -> Tuple[float, List[Dict]]:
    """Return (multiplier, list_of_firing_matches) for a ticker.

    multiplier ∈ [1 - MAX_BOOST, 1 + MAX_BOOST], clamped at 1.0
    if no qualifying patterns fire.
    """
    if stats is None:
        stats = _ps.load()
    matches = scan_ticker(ticker, df=df, regime=regime)
    if not matches:
        return (1.0, [])

    total_signal = 0.0
    qualifying = []
    for m in matches:
        pat = m["pattern"]
        if _is_disabled(stats, pat):
            continue
        edge = _get_edge(stats, pat, regime or "unknown")
        if edge is None:
            continue   # no statistical track record → no effect
        # weighted by detector confidence
        contribution = edge * float(m.get("confidence", 0.5))
        total_signal += contribution
        qualifying.append({**m, "edge": edge, "contribution": round(contribution, 3)})

    if not qualifying:
        return (1.0, matches)

    # squash signal to [-MAX_BOOST, +MAX_BOOST]
    # edge of +0.5 with 0.8 conf = +0.4 raw → scale by 0.3 → +0.12 mult
    raw = total_signal * 0.3
    mult = 1.0 + max(-MAX_BOOST, min(MAX_BOOST, raw))
    return (round(mult, 4), qualifying)


def disable_pattern(pattern: str, stats: Optional[Dict] = None) -> Dict:
    """Mark a pattern as disabled — future scans skip its multiplier effect."""
    s = stats or _ps.load()
    s.setdefault(DISABLED_KEY, {})[pattern] = True
    _ps.save(s)
    return s


def enable_pattern(pattern: str, stats: Optional[Dict] = None) -> Dict:
    s = stats or _ps.load()
    s.setdefault(DISABLED_KEY, {}).pop(pattern, None)
    _ps.save(s)
    return s


def auto_enable_disable(stats: Optional[Dict] = None,
                        kill_threshold_r: float = -0.30,
                        min_n: int = 30) -> Dict:
    """T49 Pillar 4 hook: scan stats and disable patterns with proven
    negative edge (any regime: mean_r < kill_threshold AND n ≥ min_n).

    Returns {disabled: [...], reactivated: [...]}.
    """
    s = stats or _ps.load()
    disabled_now = []
    reactivated  = []
    pre_disabled = set(s.get(DISABLED_KEY, {}).keys())
    s.setdefault(DISABLED_KEY, {})
    for pat, regimes in s.items():
        if pat == DISABLED_KEY: continue
        if not isinstance(regimes, dict): continue
        bad = any(b.get("n",0) >= min_n and b.get("mean_r",0) <= kill_threshold_r
                  for b in regimes.values() if isinstance(b, dict))
        if bad:
            if pat not in pre_disabled:
                s[DISABLED_KEY][pat] = True
                disabled_now.append(pat)
        else:
            if pat in pre_disabled:
                s[DISABLED_KEY].pop(pat, None)
                reactivated.append(pat)
    _ps.save(s)
    # learning journal hook
    try:
        from src import learning_journal as _lj
        for pat in disabled_now:
            _lj.log("pattern_disabled", pattern=pat, reason="negative_edge")
        for pat in reactivated:
            _lj.log("pattern_enabled", pattern=pat, reason="edge_recovered")
    except Exception:
        pass
    return {"disabled": disabled_now, "reactivated": reactivated}
