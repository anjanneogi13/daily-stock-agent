"""Tests for risk_metrics."""
import csv
import math
from pathlib import Path
import pytest
from src import risk_metrics as rm


@pytest.fixture
def tmp_log(tmp_path, monkeypatch):
    log = tmp_path / "picks_log.csv"
    monkeypatch.setattr(rm, "PICKS_LOG", log)
    return log


def _write(log: Path, rows: list[dict]):
    with log.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _pick(**o):
    base = {
        "ticker": "X", "pick_date": "2026-04-01", "evaluated_on": "2026-04-05",
        "evaluation_status": "tp_hit",
        "actual_return_pct": "1.0", "r_multiple": "1.0",
    }
    base.update(o)
    return base


def test_no_log_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(rm, "PICKS_LOG", tmp_path / "missing.csv")
    out = rm.compute_risk_metrics()
    assert out["n"] == 0


def test_pending_excluded(tmp_log):
    _write(tmp_log, [_pick(evaluation_status="pending", actual_return_pct="")])
    assert rm.compute_risk_metrics()["n"] == 0


def test_sharpe_basic():
    # Constant non-zero returns → sd=0 → None
    assert rm._sharpe([1.0, 1.0, 1.0]) is None
    # Mean=0, varying → 0
    assert rm._sharpe([-1.0, 1.0]) == 0.0
    # Positive mean
    s = rm._sharpe([1.0, 2.0, 3.0])
    assert s is not None and s > 0


def test_sortino_only_penalizes_downside():
    # Only negative excess matters in denominator
    s = rm._sortino([2.0, 2.0, -1.0])
    # mean=1.0, downside=[0,0,-1], dd=sqrt(1/3)
    assert abs(s - (1.0 / math.sqrt(1 / 3))) < 1e-6


def test_max_drawdown_simple():
    # +10%, -20%, +5% → equity: 1.0, 1.10, 0.88, 0.924
    # peak=1.10, trough=0.88 → dd = (0.88-1.10)/1.10 = -20%
    dd, idx = rm._max_drawdown([10.0, -20.0, 5.0])
    assert dd == -20.0
    assert idx == 2


def test_max_drawdown_no_loss():
    dd, idx = rm._max_drawdown([1.0, 2.0, 3.0])
    assert dd == 0.0


def test_compute_metrics_full(tmp_log):
    _write(tmp_log, [
        _pick(evaluated_on="2026-04-01", actual_return_pct="2.0", r_multiple="1.5"),
        _pick(evaluated_on="2026-04-02", actual_return_pct="-3.0", r_multiple="-1.0"),
        _pick(evaluated_on="2026-04-03", actual_return_pct="1.0", r_multiple="0.5"),
    ])
    m = rm.compute_risk_metrics()
    assert m["n"] == 3
    assert m["sample_warning"] is True
    assert m["mean_return_pct"] == 0.0
    assert m["sharpe_per_trade"] is not None
    assert m["sortino_per_trade"] is not None
    assert m["max_drawdown_pct"] < 0  # there was a loss


def test_chronological_order(tmp_log):
    """DD should reflect actual time-order, not file order."""
    _write(tmp_log, [
        _pick(evaluated_on="2026-04-03", actual_return_pct="-5.0", r_multiple="-1.0"),
        _pick(evaluated_on="2026-04-01", actual_return_pct="10.0", r_multiple="2.0"),
        _pick(evaluated_on="2026-04-02", actual_return_pct="2.0", r_multiple="1.0"),
    ])
    m = rm.compute_risk_metrics()
    # Time order: +10, +2, -5 → peak=1.122, trough=1.066 → dd ~ -5%
    assert m["max_drawdown_pct"] < 0
    assert m["max_drawdown_pct"] >= -5.1


def test_format_text_no_data():
    out = rm.format_risk_text({"n": 0})
    assert "no closed picks" in out


def test_format_text_renders_metrics():
    m = {
        "n": 9, "sample_warning": True,
        "sharpe_per_trade": -0.4, "sharpe_annualized": -2.83,
        "sortino_per_trade": -0.5, "sortino_annualized": -3.5,
        "sharpe_per_trade_R": -0.6,
        "max_drawdown_pct": -10.5, "calmar_annualized": -3.2,
        "mean_return_pct": -2.1,
    }
    out = rm.format_risk_text(m)
    assert "RISK-ADJUSTED" in out
    assert "small sample" in out
    assert "-2.83" in out
    assert "-10.5" in out


def test_constant_returns_sharpe_none(tmp_log):
    _write(tmp_log, [
        _pick(evaluated_on=f"2026-04-0{i}", actual_return_pct="1.0", r_multiple="1.0")
        for i in range(1, 4)
    ])
    m = rm.compute_risk_metrics()
    # sd=0 → sharpe undefined
    assert m["sharpe_per_trade"] is None
