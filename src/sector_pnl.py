"""T46 / Pillar 6: Per-sector P&L view.

Builds on sector_breakdown but adds dollar-equivalent metrics
(total R as proxy, since we trade R-multiples not real dollars).
"""
from __future__ import annotations
from typing import Dict, List, Optional


def _to_float(v) -> Optional[float]:
    try: return float(v)
    except (TypeError, ValueError): return None


def per_sector_pnl(picks: List[Dict]) -> List[Dict]:
    """Group closed picks by sector tag and aggregate P&L."""
    by_sec: Dict[str, List[Dict]] = {}
    for p in picks or []:
        sec = (p.get("sector") or p.get("tag") or "UNKNOWN").upper().split("/")[0].strip()
        by_sec.setdefault(sec, []).append(p)

    out = []
    for sec, rows in by_sec.items():
        rs = [r for r in (_to_float(p.get("r_multiple")) for p in rows) if r is not None]
        if not rs:
            continue
        wins = sum(1 for r in rs if r > 0)
        total_r = sum(rs)
        mean_r = total_r / len(rs)
        # Verdict
        if total_r >= 1.0:           verdict = "🟢 PROFITABLE"
        elif total_r > -1.0:         verdict = "🟡 FLAT"
        else:                        verdict = "🔴 LOSING"
        out.append({
            "sector":   sec,
            "trades":   len(rs),
            "wins":     wins,
            "win_rate": round(wins / len(rs), 3),
            "total_r":  round(total_r, 3),
            "mean_r":   round(mean_r,  3),
            "verdict":  verdict,
        })
    out.sort(key=lambda r: -r["total_r"])
    return out


def format_table(rows: List[Dict]) -> str:
    if not rows:
        return ""
    lines = [
        "| Sector | Trades | WR | Mean R | Total R | Verdict |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['sector']} | {r['trades']} | {r['win_rate']:.0%} | "
            f"{r['mean_r']:+.2f} | {r['total_r']:+.2f} | {r['verdict']} |"
        )
    return "\n".join(lines)
