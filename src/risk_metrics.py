"""Risk-adjusted performance metrics: Sharpe, Sortino, Max Drawdown, Calmar.

Pure math on closed picks from picks_log.csv. No external API calls.

Conventions:
  - Returns are per-trade % (not annualized) since picks are episodic.
  - Sharpe/Sortino reported as raw (per-trade) AND annualized assuming
    ~252 trading days/year and avg holding period inferred from data.
  - Max drawdown computed on cumulative R-multiple equity curve
    (chronological by pick_date, then evaluated_on).
  - Calmar = annualized return / |max drawdown|.

Designed to be additive — does not modify performance_stats.py.

Usage:
    from src.risk_metrics import compute_risk_metrics, format_risk_text
    m = compute_risk_metrics()
    print(format_risk_text(m))
"""
import csv
import math
from pathlib import Path
from statistics import mean, stdev

PICKS_LOG = Path("data/picks_log.csv")
CLOSED_STATUSES = {"tp_hit", "sl_hit", "expired", "day_close"}
TRADING_DAYS_PER_YEAR = 252


def _load_closed_chrono() -> list[dict]:
    if not PICKS_LOG.exists():
        return []
    with PICKS_LOG.open() as f:
        rows = list(csv.DictReader(f))
    closed = [r for r in rows
              if r.get("evaluation_status") in CLOSED_STATUSES
              and r.get("actual_return_pct") not in (None, "")]
    # Chronological by exit (evaluated_on), fall back to pick_date
    closed.sort(key=lambda r: (r.get("evaluated_on") or r.get("pick_date") or ""))
    return closed


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _sharpe(returns: list[float], rf_per_period: float = 0.0) -> float | None:
    """Sharpe per period (no annualization)."""
    if len(returns) < 2:
        return None
    excess = [r - rf_per_period for r in returns]
    sd = stdev(excess)
    if sd == 0:
        return None
    return mean(excess) / sd


def _sortino(returns: list[float], rf_per_period: float = 0.0) -> float | None:
    """Sortino per period — penalizes downside only."""
    if len(returns) < 2:
        return None
    excess = [r - rf_per_period for r in returns]
    downside = [min(0.0, r) for r in excess]
    # Downside deviation = sqrt(mean(downside^2))
    dd = math.sqrt(sum(d * d for d in downside) / len(downside))
    if dd == 0:
        return None
    return mean(excess) / dd


def _max_drawdown(returns_pct: list[float]) -> tuple[float, int]:
    """Max drawdown (%) on equity curve from sequential % returns.

    Returns (max_dd_pct, trough_index). max_dd_pct is negative.
    """
    if not returns_pct:
        return 0.0, 0
    equity = [1.0]
    for r in returns_pct:
        equity.append(equity[-1] * (1 + r / 100.0))
    peak = equity[0]
    max_dd = 0.0
    trough_idx = 0
    for i, e in enumerate(equity):
        if e > peak:
            peak = e
        dd = (e - peak) / peak * 100.0
        if dd < max_dd:
            max_dd = dd
            trough_idx = i
    return round(max_dd, 2), trough_idx


def compute_risk_metrics() -> dict:
    """Compute Sharpe / Sortino / Max DD / Calmar on closed picks."""
    closed = _load_closed_chrono()
    n = len(closed)
    if n == 0:
        return {"n": 0, "note": "no closed picks"}

    pct_returns = [_f(r.get("actual_return_pct")) for r in closed]
    pct_returns = [x for x in pct_returns if x is not None]
    r_mults = [_f(r.get("r_multiple")) for r in closed]
    r_mults = [x for x in r_mults if x is not None]

    sharpe_pct = _sharpe(pct_returns) if pct_returns else None
    sortino_pct = _sortino(pct_returns) if pct_returns else None
    sharpe_r = _sharpe(r_mults) if r_mults else None
    sortino_r = _sortino(r_mults) if r_mults else None

    max_dd, trough_idx = _max_drawdown(pct_returns)

    # Naive annualization: assume avg trade ≈ 5 trading days (swing default)
    # → trades_per_year ≈ 50. sqrt(50) ≈ 7.07
    annual_factor = math.sqrt(50)
    sharpe_annual = round(sharpe_pct * annual_factor, 2) if sharpe_pct is not None else None
    sortino_annual = round(sortino_pct * annual_factor, 2) if sortino_pct is not None else None

    # Calmar = annualized mean return / |max DD|
    annual_return_pct = mean(pct_returns) * 50 if pct_returns else 0.0
    calmar = (annual_return_pct / abs(max_dd)) if max_dd != 0 else None

    return {
        "n": n,
        "sample_warning": n < 30,
        "mean_return_pct": round(mean(pct_returns), 2) if pct_returns else None,
        "sharpe_per_trade": round(sharpe_pct, 3) if sharpe_pct is not None else None,
        "sortino_per_trade": round(sortino_pct, 3) if sortino_pct is not None else None,
        "sharpe_annualized": sharpe_annual,
        "sortino_annualized": sortino_annual,
        "sharpe_per_trade_R": round(sharpe_r, 3) if sharpe_r is not None else None,
        "sortino_per_trade_R": round(sortino_r, 3) if sortino_r is not None else None,
        "max_drawdown_pct": max_dd,
        "trough_at_trade_index": trough_idx,
        "calmar_annualized": round(calmar, 2) if calmar is not None else None,
        "annual_return_pct_naive": round(annual_return_pct, 2),
    }


def format_risk_text(m: dict) -> str:
    """Plain-text block for dashboard / Telegram / GitHub issue."""
    if m.get("n", 0) == 0:
        return "📐 RISK METRICS: (no closed picks yet)\n"
    lines = ["📐 RISK-ADJUSTED METRICS"]
    if m.get("sample_warning"):
        lines.append(f"   ⚠️  n={m['n']} — small sample, treat as directional only")
    else:
        lines.append(f"   n={m['n']} closed trades")

    def fmt(v, sfx=""):
        return f"{v}{sfx}" if v is not None else "—"

    lines += [
        f"   Sharpe (per-trade):       {fmt(m['sharpe_per_trade'])}",
        f"   Sharpe (annualized ~50t): {fmt(m['sharpe_annualized'])}",
        f"   Sortino (per-trade):      {fmt(m['sortino_per_trade'])}",
        f"   Sortino (annualized):     {fmt(m['sortino_annualized'])}",
        f"   Sharpe-R (per-trade):     {fmt(m['sharpe_per_trade_R'])}",
        f"   Max drawdown:             {fmt(m['max_drawdown_pct'], '%')}",
        f"   Calmar (annualized):      {fmt(m['calmar_annualized'])}",
        f"   Mean return / trade:      {fmt(m['mean_return_pct'], '%')}",
    ]
    return "\n".join(lines) + "\n"
