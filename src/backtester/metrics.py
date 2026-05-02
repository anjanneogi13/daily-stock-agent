"""Aggregate metrics across simulated picks."""
from __future__ import annotations
import math
from typing import List, Dict
from collections import defaultdict


def compute_metrics(picks: List[Dict]) -> Dict:
    """Compute Sharpe/Sortino/MaxDD/etc on a list of simulated picks.

    Each pick must have: r_multiple, return_pct, exit_status
    """
    if not picks:
        return {"n_picks": 0, "warning": "no picks to analyze"}

    rs = [p["r_multiple"] for p in picks if p.get("r_multiple") is not None]
    rets = [p["return_pct"] for p in picks if p.get("return_pct") is not None]

    n = len(rs)
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r < 0]

    win_rate = len(wins) / n if n else 0
    avg_r = sum(rs) / n if n else 0
    total_return = sum(rets)

    # Sharpe (using R-multiples as returns, annualized assuming ~250 trading days)
    if n > 1:
        mean_r = sum(rs) / n
        var_r = sum((r - mean_r) ** 2 for r in rs) / (n - 1)
        std_r = math.sqrt(var_r) if var_r > 0 else 0
        sharpe = (mean_r / std_r) * math.sqrt(250) if std_r > 0 else 0
    else:
        sharpe = 0

    # Sortino (downside deviation only)
    if losses:
        downside_var = sum(r ** 2 for r in losses) / len(losses)
        downside_std = math.sqrt(downside_var)
        sortino = (avg_r / downside_std) * math.sqrt(250) if downside_std > 0 else 0
    else:
        sortino = float("inf") if avg_r > 0 else 0

    # Max drawdown (cumulative R)
    cum, peak, max_dd = 0, 0, 0
    for r in rs:
        cum += r
        peak = max(peak, cum)
        dd = peak - cum
        max_dd = max(max_dd, dd)

    # Profit factor
    gross_win = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 0
    profit_factor = gross_win / gross_loss if gross_loss > 0 else float("inf")

    # Exit status breakdown
    exits = defaultdict(int)
    for p in picks:
        exits[p.get("exit_status", "unknown")] += 1

    return {
        "n_picks": n,
        "win_rate_pct": round(win_rate * 100, 2),
        "avg_r": round(avg_r, 3),
        "total_return_pct": round(total_return, 2),
        "sharpe_annualized": round(sharpe, 2),
        "sortino_annualized": round(sortino, 2) if sortino != float("inf") else "inf",
        "max_drawdown_R": round(max_dd, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "inf",
        "wins": len(wins),
        "losses": len(losses),
        "exit_breakdown": dict(exits),
        "statistical_warning": "⚠ N<30, results not significant" if n < 30 else None,
    }


def breakdown_by(picks: List[Dict], key: str) -> Dict[str, Dict]:
    """Group picks by a key and compute metrics per group."""
    groups = defaultdict(list)
    for p in picks:
        groups[str(p.get(key, "unknown"))].append(p)
    return {g: compute_metrics(plist) for g, plist in groups.items()}
