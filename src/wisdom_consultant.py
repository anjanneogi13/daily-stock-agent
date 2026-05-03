"""
Wisdom Consultant — applies wisdom to a candidate before final scoring.

Returns a dict:
  {
    "warnings":   ["AVOID when regime=bear (p=0.04, n=15)", ...],
    "boosts":     ["BOOST regime=bull (p=0.012, n=20)", ...],
    "kill":       {ticker, reason, expires_at}  | None,
    "score_adj":  -0.0  to  +0.05               # tiny tilt, observe-mode
  }

OBSERVE-MODE: score_adj is capped at ±0.05 in v0.1.
Bigger tilts in v0.2 once we trust the patterns.
"""
from typing import Dict, Optional, List
from .wisdom_base import (
    load_active_patterns,
    is_killed,
)


SCORE_ADJ_CAP = 0.05  # max ±0.05 tilt per pick in v0.1


def consult_before_pick(ticker: str,
                         signals: Dict[str, str]) -> Dict:
    """
    Apply wisdom to a candidate. Returns warnings + boosts + score_adj.
    Never returns score_adj > +SCORE_ADJ_CAP or < -SCORE_ADJ_CAP.
    """
    result = {
        "warnings":  [],
        "boosts":    [],
        "kill":      None,
        "score_adj": 0.0,
    }

    # 1. Kill list check
    kill = is_killed(ticker)
    if kill:
        result["kill"] = kill
        result["warnings"].append(
            f"💀 KILL LIST: {ticker} — {kill.get('reason','no reason')} "
            f"(expires {kill.get('expires_at','?')[:10]})"
        )
        # No score adj — kill is informational; main.py / scorer decides whether to drop.

    # 2. Pattern matching
    patterns = load_active_patterns()
    for p in patterns:
        sig_name = p.get("signal")
        bucket   = p.get("bucket")
        if signals.get(sig_name) != bucket:
            continue
        msg = (f"{p.get('effect','?').upper()} {sig_name}={bucket} "
               f"WR={p.get('win_rate',0):.0%} n={p.get('sample_n',0)} "
               f"p={p.get('p_value',0):.3f}")
        if p.get("effect") == "edge":
            result["boosts"].append(msg)
            result["score_adj"] += 0.02
        elif p.get("effect") == "drag":
            result["warnings"].append(msg)
            result["score_adj"] -= 0.02

    # Cap the tilt
    if result["score_adj"] >  SCORE_ADJ_CAP: result["score_adj"] =  SCORE_ADJ_CAP
    if result["score_adj"] < -SCORE_ADJ_CAP: result["score_adj"] = -SCORE_ADJ_CAP
    result["score_adj"] = round(result["score_adj"], 3)

    return result
