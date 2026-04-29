"""
Performance Tracker — the single source of truth for system performance.
Computes win-rate, R-multiple, Sharpe, max DD, profit factor, expectancy.

Reads: data/picks_log.csv (canonical pick history)
Writes: data/metrics_daily.json (latest snapshot)
        data/metrics_history.jsonl (one line per day, forever)
"""
import csv, json, math
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict

PICKS_LOG = Path("data/picks_log.csv")
METRICS_DAILY = Path("data/metrics_daily.json")
METRICS_HISTORY = Path("data/metrics_history.jsonl")


def _load_evaluated_picks() -> List[Dict]:
    """Load only picks that have been evaluated (closed positions)."""
    if not PICKS_LOG.exists():
        return []
    rows = []
    with PICKS_LOG.open() as f:
        for r in csv.DictReader(f):
            status = r.get("evaluation_status", "")
            if status in ("tp_hit", "sl_hit", "expired", "closed"):
                rows.append(r)
    return rows


def _safe_float(v, default=0.0):
    try:
        return float(v) if v not in ("", None) else default
    except (ValueError, TypeError):
        return default


def _r_multiple(row: Dict) -> float:
    """Compute R-multiple: (exit - entry) / (entry - stop). Negative if loss."""
    entry = _safe_float(row.get("entry"))
    stop = _safe_float(row.get("stop_loss"))
    exit_p = _safe_float(row.get("exit_price"))
    if entry <= 0 or stop <= 0 or exit_p <= 0:
        return 0.0
    risk = entry - stop
    if risk <= 0:
        return 0.0
    return round((exit_p - entry) / risk, 3)


def _return_pct(row: Dict) -> float:
    """Actual return %: prefer logged value, else compute."""
    logged = _safe_float(row.get("actual_return_pct"))
    if logged != 0:
        return logged
    entry = _safe_float(row.get("entry"))
    exit_p = _safe_float(row.get("exit_price"))
    if entry > 0 and exit_p > 0:
        return round((exit_p - entry) / entry * 100, 3)
    return 0.0


def _sharpe(returns: List[float], risk_free_pct: float = 0.0) -> float:
    """Annualized Sharpe ratio (assumes daily returns; *sqrt(252))."""
    if len(returns) < 2:
        return 0.0
    mean_r = sum(returns) / len(returns)
    var = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    daily_excess = mean_r - (risk_free_pct / 252)
    return round((daily_excess / std) * math.sqrt(252), 2)


def _max_drawdown(returns_pct: List[float]) -> float:
    """Max drawdown % from cumulative equity curve."""
    if not returns_pct:
        return 0.0
    equity = [100.0]
    for r in returns_pct:
        equity.append(equity[-1] * (1 + r / 100))
    peak = equity[0]
    max_dd = 0.0
    for v in equity:
        if v > peak:
            peak = v
        dd = (peak - v) / peak * 100
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)


def compute_metrics(picks: List[Dict] = None, label: str = "all") -> Dict:
    """Compute all performance metrics from a list of evaluated picks."""
    picks = picks if picks is not None else _load_evaluated_picks()
    n = len(picks)
    if n == 0:
        return {
            "label": label, "n_trades": 0, "win_rate": 0.0, "avg_r": 0.0,
            "sharpe": 0.0, "max_dd_pct": 0.0, "profit_factor": 0.0,
            "expectancy_r": 0.0, "best_trade_r": 0.0, "worst_trade_r": 0.0,
            "best_ticker": None, "worst_ticker": None,
            "wins": 0, "losses": 0, "total_return_pct": 0.0,
        }

    r_multiples = [(p, _r_multiple(p)) for p in picks]
    returns_pct = [_return_pct(p) for p in picks]

    wins = [r for _, r in r_multiples if r > 0]
    losses = [r for _, r in r_multiples if r < 0]
    win_rate = len(wins) / n if n else 0.0
    avg_r = sum(r for _, r in r_multiples) / n if n else 0.0

    gross_win_pct = sum(r for r in returns_pct if r > 0)
    gross_loss_pct = abs(sum(r for r in returns_pct if r < 0))
    profit_factor = round(gross_win_pct / gross_loss_pct, 2) if gross_loss_pct > 0 else 0.0

    expectancy = (win_rate * (sum(wins)/len(wins) if wins else 0)) + \
                 ((1-win_rate) * (sum(losses)/len(losses) if losses else 0))

    best = max(r_multiples, key=lambda x: x[1]) if r_multiples else (None, 0)
    worst = min(r_multiples, key=lambda x: x[1]) if r_multiples else (None, 0)

    return {
        "label": label,
        "n_trades": n,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate * 100, 1),
        "avg_r": round(avg_r, 2),
        "sharpe": _sharpe(returns_pct),
        "max_dd_pct": _max_drawdown(returns_pct),
        "profit_factor": profit_factor,
        "expectancy_r": round(expectancy, 2),
        "best_trade_r": best[1],
        "worst_trade_r": worst[1],
        "best_ticker": best[0]["ticker"] if best[0] else None,
        "worst_ticker": worst[0]["ticker"] if worst[0] else None,
        "total_return_pct": round(sum(returns_pct), 2),
    }


def compute_segmented_metrics() -> Dict:
    """Compute metrics overall + by trade_type + by recency."""
    all_picks = _load_evaluated_picks()
    today = datetime.now().date()

    # Filter helpers
    def by_date_range(picks, days):
        cutoff = today - timedelta(days=days)
        out = []
        for p in picks:
            try:
                d = datetime.strptime(p.get("evaluated_on", ""), "%Y-%m-%d").date()
                if d >= cutoff:
                    out.append(p)
            except (ValueError, TypeError):
                pass
        return out

    day_picks = [p for p in all_picks if p.get("trade_type") == "day"]
    swing_picks = [p for p in all_picks if p.get("trade_type") == "swing"]

    return {
        "computed_at": datetime.now().isoformat(),
        "overall": compute_metrics(all_picks, "overall"),
        "day_trades": compute_metrics(day_picks, "day_trades"),
        "swing_trades": compute_metrics(swing_picks, "swing_trades"),
        "last_7_days": compute_metrics(by_date_range(all_picks, 7), "last_7_days"),
        "last_30_days": compute_metrics(by_date_range(all_picks, 30), "last_30_days"),
        "last_90_days": compute_metrics(by_date_range(all_picks, 90), "last_90_days"),
    }


def save_metrics():
    """Compute and persist metrics. Append to history. Returns metrics dict."""
    metrics = compute_segmented_metrics()
    METRICS_DAILY.parent.mkdir(parents=True, exist_ok=True)
    METRICS_DAILY.write_text(json.dumps(metrics, indent=2))

    # Append snapshot to history (only the overall + day_trades + swing_trades)
    snapshot = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "overall": metrics["overall"],
        "day": metrics["day_trades"],
        "swing": metrics["swing_trades"],
    }
    with METRICS_HISTORY.open("a") as f:
        f.write(json.dumps(snapshot) + "\n")
    return metrics


if __name__ == "__main__":
    m = save_metrics()
    print(json.dumps(m["overall"], indent=2))
