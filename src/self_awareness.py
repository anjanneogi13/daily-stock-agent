"""T45 / Pillar 5: Self-Awareness — rolling 30d confidence intervals.

Computes statistically honest 'how confident am I in my recent edge?'
metrics. Used by:
  - weekly_review (footer)
  - monthly_xray (calibration cadence)

Win-rate CI: Wilson score interval (better than normal-approx for small n).
Mean-R CI: standard error of the mean (assumes ~normal R distribution).

Pure stdlib — no scipy/numpy.
"""
from __future__ import annotations
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from src.signal_journal import load_closed


# ─────────── Wilson score interval ───────────
def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson CI for a binomial proportion. Returns (lo, hi)."""
    if n <= 0:
        return (0.0, 0.0)
    p = wins / n
    denom = 1 + z*z/n
    centre = (p + z*z/(2*n)) / denom
    half = (z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def mean_r_ci(rs: List[float], z: float = 1.96) -> tuple[float, float, float]:
    """95% CI on mean R-multiple. Returns (mean, lo, hi)."""
    n = len(rs)
    if n == 0:
        return (0.0, 0.0, 0.0)
    mean = sum(rs) / n
    if n < 2:
        return (mean, mean, mean)
    var = sum((x - mean)**2 for x in rs) / (n - 1)
    se  = math.sqrt(var / n)
    return (mean, mean - z*se, mean + z*se)


# ─────────── filtering ───────────
def _within_days(rec: Dict, days: int, today: Optional[datetime] = None) -> bool:
    today = today or datetime.now()
    cutoff = today - timedelta(days=days)
    for key in ("evaluated_on", "pick_date"):
        v = rec.get(key)
        if not v: continue
        try:
            dt = datetime.fromisoformat(str(v).split("T")[0])
            return dt >= cutoff
        except Exception:
            continue
    return False


# ─────────── public API ───────────
def rolling_window(days: int = 30,
                   today: Optional[datetime] = None) -> Dict:
    """Return rolling stats over the last `days` days w/ 95% CIs.

    Output:
      {
        days: 30, n: 18, wins: 7,
        win_rate: 0.389,   wr_ci_lo: 0.20, wr_ci_hi: 0.61,
        mean_r:   -0.12,   r_ci_lo: -0.55, r_ci_hi: 0.31,
        verdict: "INCONCLUSIVE" | "EDGE_CONFIRMED" | "EDGE_BROKEN",
      }
    """
    closed = [c for c in (load_closed() or [])
              if _within_days(c, days, today)]
    n = len(closed)
    wins = sum(1 for c in closed if c.get("outcome") == "win")
    rs = []
    for c in closed:
        try: rs.append(float(c.get("r_multiple") or 0))
        except (TypeError, ValueError): pass

    wr = wins / n if n else 0.0
    wr_lo, wr_hi = wilson_ci(wins, n)
    mean, r_lo, r_hi = mean_r_ci(rs)

    # Verdict: needs both n>=20 AND CI doesn't straddle 0/0.5
    verdict = "INCONCLUSIVE"
    if n >= 20:
        if r_lo > 0 and wr_lo > 0.45:
            verdict = "EDGE_CONFIRMED"
        elif r_hi < 0 or wr_hi < 0.35:
            verdict = "EDGE_BROKEN"

    return {
        "days":     days,
        "n":        n,
        "wins":     wins,
        "win_rate": round(wr, 3),
        "wr_ci_lo": round(wr_lo, 3),
        "wr_ci_hi": round(wr_hi, 3),
        "mean_r":   round(mean, 3),
        "r_ci_lo":  round(r_lo, 3),
        "r_ci_hi":  round(r_hi, 3),
        "verdict":  verdict,
    }


def format_footer(stats: Dict) -> str:
    """Telegram-ready 2-line footer for weekly review."""
    if stats["n"] == 0:
        return ""
    emoji = {"EDGE_CONFIRMED":"🟢","EDGE_BROKEN":"🔴",
             "INCONCLUSIVE":"🟡"}.get(stats["verdict"], "⚪")
    return (
        f"• {emoji} 30d edge: {stats['verdict']} "
        f"(n={stats['n']}, WR {stats['win_rate']:.0%} "
        f"[{stats['wr_ci_lo']:.0%}-{stats['wr_ci_hi']:.0%}])\n"
        f"• 📊 30d mean R: {stats['mean_r']:+.2f} "
        f"[{stats['r_ci_lo']:+.2f}, {stats['r_ci_hi']:+.2f}] (95% CI)"
    )


def monthly_calibration() -> Dict:
    """Run rolling stats at 30/60/90d windows for monthly X-ray.
    Compare windows to detect 'edge improving / decaying'."""
    w30 = rolling_window(30)
    w60 = rolling_window(60)
    w90 = rolling_window(90)
    trend = "stable"
    if w30["mean_r"] > w90["mean_r"] + 0.20:
        trend = "improving"
    elif w30["mean_r"] < w90["mean_r"] - 0.20:
        trend = "decaying"
    return {
        "30d": w30, "60d": w60, "90d": w90,
        "trend": trend,
    }
