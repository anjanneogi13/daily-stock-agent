"""T28: Per-sector P&L breakdown for the weekly review.

Enriches each closed pick with a sector_etf resolved from its tag/sector
fields (using src.sector_benchmark.resolve_sector_etf), then groups by ETF
and computes win-rate, R-multiple, and a verdict emoji.
"""
from typing import Dict, List

from .sector_benchmark import resolve_sector_etf
from .strategy_breakdown import breakdown_by


def _enrich_with_sector_etf(picks: List[Dict]) -> List[Dict]:
    """Add 'sector_etf' to each pick dict (in-place + returned)."""
    for p in picks:
        # Already enriched? skip
        if p.get("sector_etf"):
            continue
        try:
            etf = resolve_sector_etf(
                sector=p.get("sector"),
                tag=p.get("tag"),
            )
        except Exception:
            etf = "SPY"
        p["sector_etf"] = etf or "SPY"
    return picks


def _verdict(win_rate: float, total_r: float) -> str:
    """Map (win_rate, total_r) → emoji + label."""
    if total_r is None:
        return "⚪ N/A"
    if win_rate >= 0.65 and total_r >= 1.5:
        return "🌟 STRONG"
    if win_rate >= 0.50 and total_r > 0:
        return "🟢 OK"
    if total_r >= 0:
        return "🟡 MIXED"
    if total_r >= -2:
        return "🟠 WEAK"
    return "🔴 BLEEDING"


def sector_breakdown(picks: List[Dict]) -> List[Dict]:
    """Return per-sector rows sorted by total_r ascending (worst first).

    Each row: {sector, n, win_rate, avg_r, total_r, verdict}
    """
    if not picks:
        return []
    enriched = _enrich_with_sector_etf(picks)
    rows = breakdown_by("sector_etf", rows=enriched)
    out = []
    for r in rows:
        out.append({
            "sector":   r["group"],
            "n":        r["n"],
            "win_rate": r["win_rate"],
            "avg_r":    r["avg_r"],
            "total_r":  r["total_r"],
            "verdict":  _verdict(r["win_rate"], r["total_r"]),
        })
    # Worst first — bleeding sectors should leap off the page
    out.sort(key=lambda d: (d["total_r"] if d["total_r"] is not None else 0))
    return out


def format_sector_panel(rows: List[Dict]) -> str:
    """Markdown table for the weekly review snapshot."""
    if not rows:
        return ""
    lines = ["", "🏭 *Sector Breakdown*", ""]
    lines.append("| Sector | Trades | Win% | Avg R | Total R | Verdict |")
    lines.append("|--------|--------|------|-------|---------|---------|")
    for r in rows:
        wr = f"{r['win_rate']*100:.0f}%"
        ar = f"{r['avg_r']:+.2f}" if r["avg_r"] is not None else "—"
        tr = f"{r['total_r']:+.2f}" if r["total_r"] is not None else "—"
        lines.append(
            f"| {r['sector']} | {r['n']} | {wr} | {ar} | {tr} | {r['verdict']} |"
        )
    return "\n".join(lines)
