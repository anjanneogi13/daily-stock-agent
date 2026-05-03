"""
Hypothesis Engine v0.1 — Pillar 1 Layer 4

For each (signal, value) bucket from the signal journal, compute:
  - sample size n
  - wins / losses
  - bucket win-rate vs base-rate win-rate
  - binomial p-value (two-sided test)
  - average R-multiple in this bucket

Surfaces:
  - significant_edges  (bucket beats base rate, p < 0.05, n >= MIN_N)
  - significant_drags  (bucket worse than base rate, p < 0.05)
  - low_sample_buckets (interesting but n < MIN_N — wait & see)

OBSERVE-MODE: Engine ONLY reports. No auto-flipping of weights.
"""
from typing import Dict, List
from collections import defaultdict
from math import comb


MIN_SAMPLE_SIZE = 10
SIGNIFICANCE_THRESHOLD = 0.05


# ═══════════════════════════════════════════════════════════════
# Pure-stdlib binomial CDF (avoids scipy dependency)
# ═══════════════════════════════════════════════════════════════
def _binom_pmf(k: int, n: int, p: float) -> float:
    if n < 0 or k < 0 or k > n: return 0.0
    if p <= 0.0: return 1.0 if k == 0 else 0.0
    if p >= 1.0: return 1.0 if k == n else 0.0
    return comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def _binom_cdf(k: int, n: int, p: float) -> float:
    return sum(_binom_pmf(i, n, p) for i in range(0, k + 1))


def two_sided_p_value(wins: int, n: int, base_rate: float) -> float:
    """Two-sided binomial p-value vs base rate."""
    if n == 0: return 1.0
    if base_rate <= 0 or base_rate >= 1: return 1.0
    expected = n * base_rate
    if wins >= expected:
        # right tail: P(X >= wins)
        right = 1.0 - _binom_cdf(wins - 1, n, base_rate)
        return min(1.0, 2 * right)
    else:
        # left tail: P(X <= wins)
        left = _binom_cdf(wins, n, base_rate)
        return min(1.0, 2 * left)


# ═══════════════════════════════════════════════════════════════
# Main analysis
# ═══════════════════════════════════════════════════════════════
def analyze(closed_rows: List[Dict],
            min_n: int = MIN_SAMPLE_SIZE,
            alpha: float = SIGNIFICANCE_THRESHOLD) -> Dict:
    """
    closed_rows: list of journal rows with outcome ('win' or 'loss').
    Returns dict with edges, drags, low_sample, base_rate, total_n.
    """
    n_total = len(closed_rows)
    if n_total == 0:
        return {
            "total_n": 0, "base_rate": None,
            "edges": [], "drags": [], "low_sample": [],
            "summary": "No closed picks yet — journal empty."
        }

    base_wins = sum(1 for r in closed_rows if r.get("outcome") == "win")
    base_rate = base_wins / n_total

    # Group by (signal_name, bucket_value)
    buckets = defaultdict(list)
    for r in closed_rows:
        for sig_name, bucket_val in (r.get("signals") or {}).items():
            buckets[(sig_name, bucket_val)].append(r)

    edges, drags, low_sample = [], [], []
    for (sig, bucket), rows in buckets.items():
        n = len(rows)
        wins = sum(1 for x in rows if x.get("outcome") == "win")
        win_rate = wins / n if n else 0.0

        r_mults = [x.get("r_multiple") for x in rows
                   if isinstance(x.get("r_multiple"), (int, float))]
        avg_r = round(sum(r_mults) / len(r_mults), 3) if r_mults else None

        record = {
            "signal":    sig,
            "bucket":    bucket,
            "n":         n,
            "wins":      wins,
            "win_rate":  round(win_rate, 3),
            "vs_base":   round(win_rate - base_rate, 3),
            "avg_r":     avg_r,
        }

        if n < min_n:
            low_sample.append(record)
            continue

        p = two_sided_p_value(wins, n, base_rate)
        record["p_value"] = round(p, 4)

        if p < alpha and win_rate > base_rate:
            edges.append(record)
        elif p < alpha and win_rate < base_rate:
            drags.append(record)

    edges.sort(key=lambda x: x["vs_base"], reverse=True)
    drags.sort(key=lambda x: x["vs_base"])
    low_sample.sort(key=lambda x: x["n"], reverse=True)

    return {
        "total_n":    n_total,
        "base_rate":  round(base_rate, 3),
        "base_wins":  base_wins,
        "edges":      edges,
        "drags":      drags,
        "low_sample": low_sample,
        "summary":    (f"{n_total} closed picks, base win-rate {base_rate:.1%}. "
                       f"{len(edges)} edges + {len(drags)} drags found."),
    }


def format_report(result: Dict) -> str:
    """Human-readable text report."""
    lines = []
    lines.append("═" * 70)
    lines.append("🧠 HYPOTHESIS REVIEW — Pillar 1 Layer 4 v0.1 (observe-mode)")
    lines.append("═" * 70)
    lines.append(result["summary"])

    if result["total_n"] == 0:
        return "\n".join(lines)

    if result["edges"]:
        lines.append("")
        lines.append(f"✅ STATISTICALLY SIGNIFICANT EDGES ({len(result['edges'])})")
        lines.append("─" * 70)
        for e in result["edges"]:
            ar = f"avg_R={e['avg_r']:+.2f}" if e['avg_r'] is not None else "avg_R=?"
            lines.append(
                f"  {e['signal']}={e['bucket']:<10} "
                f"n={e['n']:<3} wins={e['wins']:<3} "
                f"WR={e['win_rate']:.0%} (Δ{e['vs_base']:+.0%}) "
                f"p={e['p_value']:.3f} {ar}"
            )

    if result["drags"]:
        lines.append("")
        lines.append(f"❌ STATISTICALLY SIGNIFICANT DRAGS ({len(result['drags'])})")
        lines.append("─" * 70)
        for d in result["drags"]:
            ar = f"avg_R={d['avg_r']:+.2f}" if d['avg_r'] is not None else "avg_R=?"
            lines.append(
                f"  {d['signal']}={d['bucket']:<10} "
                f"n={d['n']:<3} wins={d['wins']:<3} "
                f"WR={d['win_rate']:.0%} (Δ{d['vs_base']:+.0%}) "
                f"p={d['p_value']:.3f} {ar}"
            )

    if result["low_sample"]:
        lines.append("")
        lines.append(f"⏳ LOW SAMPLE — interesting but need more data (top 10)")
        lines.append("─" * 70)
        for ls in result["low_sample"][:10]:
            ar = f"avg_R={ls['avg_r']:+.2f}" if ls['avg_r'] is not None else "avg_R=?"
            lines.append(
                f"  {ls['signal']}={ls['bucket']:<10} "
                f"n={ls['n']:<3} wins={ls['wins']:<3} WR={ls['win_rate']:.0%} {ar}"
            )

    lines.append("")
    lines.append("═" * 70)
    lines.append("OBSERVE-MODE: No weights auto-changed. You decide what to act on.")
    lines.append("═" * 70)
    return "\n".join(lines)
