"""Strategy/tag/regime performance breakdown.

Groups closed picks by dimension (trade_type, tag, regime) and computes:
  - n (count)
  - win_rate
  - avg_return_pct
  - avg_r
  - avg_alpha_pct (vs SPY)
  - total_r

Reads data/picks_log.csv. Pure analytics — no API calls.

Usage:
    from src.strategy_breakdown import breakdown_by, print_all_breakdowns
    rows = breakdown_by('trade_type')
    print_all_breakdowns()  # to stdout via rich
"""
import csv
from collections import defaultdict
from pathlib import Path
from typing import Iterable

PICKS_LOG = Path("data/picks_log.csv")
CLOSED_STATUSES = {"tp_hit", "sl_hit", "expired"}


def _load_closed() -> list[dict]:
    if not PICKS_LOG.exists():
        return []
    with PICKS_LOG.open() as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows
            if r.get("evaluation_status") in CLOSED_STATUSES
            and r.get("actual_return_pct") not in (None, "")]


def _to_float(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def breakdown_by(dimension: str, rows: list[dict] | None = None) -> list[dict]:
    """Group closed picks by `dimension` field and compute metrics.

    Returns list of dicts sorted by count desc, then total_r desc:
        [{
            'group': 'swing',
            'n': 5,
            'wins': 1,
            'losses': 4,
            'win_rate': 0.20,
            'avg_return_pct': -3.2,
            'avg_r': -0.6,
            'total_r': -3.0,
            'avg_alpha_pct': -2.1,
        }, ...]
    """
    if rows is None:
        rows = _load_closed()
    if not rows:
        return []

    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        key = (r.get(dimension) or "").strip() or "unknown"
        groups[key].append(r)

    out = []
    for group, items in groups.items():
        returns = [_to_float(r.get("actual_return_pct")) for r in items]
        returns = [x for x in returns if x is not None]
        r_mults = [_to_float(r.get("r_multiple")) for r in items]
        r_mults = [x for x in r_mults if x is not None]
        alphas = [_to_float(r.get("alpha_pct")) for r in items]
        alphas = [x for x in alphas if x is not None]

        wins = sum(1 for r in items if r.get("evaluation_status") == "tp_hit")
        losses = sum(1 for r in items if r.get("evaluation_status") == "sl_hit")
        n = len(items)

        out.append({
            "group": group,
            "n": n,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / n, 3) if n else 0.0,
            "avg_return_pct": round(sum(returns) / len(returns), 2) if returns else None,
            "avg_r": round(sum(r_mults) / len(r_mults), 2) if r_mults else None,
            "total_r": round(sum(r_mults), 2) if r_mults else None,
            "avg_alpha_pct": round(sum(alphas) / len(alphas), 2) if alphas else None,
        })

    out.sort(key=lambda d: (-d["n"], -(d["total_r"] or 0)))
    return out


def format_breakdown_text(dimension: str, rows: list[dict]) -> str:
    """Plain-text table for console / Telegram / GitHub issue body."""
    if not rows:
        return f"=== Breakdown by {dimension} ===\n(no closed picks)\n"
    lines = [f"=== Breakdown by {dimension} ===",
             f"{'group':<15} {'n':>3} {'wins':>4} {'win%':>5} "
             f"{'avgR':>6} {'totR':>6} {'avgRet%':>8} {'avgAlpha%':>10}"]
    for r in rows:
        wr = f"{r['win_rate']*100:.0f}%"
        avg_r = f"{r['avg_r']:.2f}" if r["avg_r"] is not None else "—"
        tot_r = f"{r['total_r']:.2f}" if r["total_r"] is not None else "—"
        avg_ret = f"{r['avg_return_pct']:.2f}" if r["avg_return_pct"] is not None else "—"
        avg_a = f"{r['avg_alpha_pct']:.2f}" if r["avg_alpha_pct"] is not None else "—"
        lines.append(f"{r['group']:<15} {r['n']:>3} {r['wins']:>4} {wr:>5} "
                     f"{avg_r:>6} {tot_r:>6} {avg_ret:>8} {avg_a:>10}")
    return "\n".join(lines) + "\n"


def print_all_breakdowns(dimensions: Iterable[str] = ("trade_type", "tag", "regime")) -> None:
    """Print breakdowns for each dimension to stdout."""
    closed = _load_closed()
    if not closed:
        print("(no closed picks yet — breakdowns unavailable)")
        return
    print(f"\n📊 STRATEGY BREAKDOWN ({len(closed)} closed picks)\n")
    for dim in dimensions:
        rows = breakdown_by(dim, closed)
        print(format_breakdown_text(dim, rows))
