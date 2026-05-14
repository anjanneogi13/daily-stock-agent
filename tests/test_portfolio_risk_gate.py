"""PR-A: portfolio risk gate is now SAME-DAY DIVERSITY only.
Stale tracking rows in picks_log.csv must NEVER block today's suggestions.
"""
from src.portfolio_risk_gate import (
    apply_portfolio_risk_gate,
    build_portfolio_risk_config,
    evaluate_candidate_portfolio_risk,
)


def cfg(max_new=2, max_per_sector=1, max_per_tag=1):
    return {
        "risk": {
            "account_size": 10000,
            "risk_per_trade_pct": 1.0,
            "max_new_picks_per_day": max_new,
            "max_per_sector": max_per_sector,
            "max_per_tag": max_per_tag,
            "min_risk_reward": 1.0,
        }
    }


def candidate(ticker="AAPL", sector="Technology", tag="TECH", qty=10, rr=2.0,
              composite=0.8):
    return {
        "ticker": ticker,
        "scores": {"composite": composite, "sector_tag": tag},
        "info_short": {"sector": sector},
        "plan": {
            "entry": 100.0,
            "stop_loss": 95.0,
            "take_profit": 110.0,
            "risk_reward": rr,
            "quantity": qty,
        },
    }


def test_build_portfolio_risk_config_reads_defaults_and_config():
    result = build_portfolio_risk_config(cfg())
    assert result["account_size"] == 10000
    assert result["risk_per_trade_pct"] == 1.0
    assert result["max_new_picks_per_day"] == 2
    # Legacy alias must equal the new key for backward compat.
    assert result["max_positions"] == 2
    assert result["max_per_sector"] == 1
    assert result["max_per_tag"] == 1


def test_evaluate_candidate_portfolio_risk_allows_valid_candidate():
    risk_config = build_portfolio_risk_config(cfg())
    ok, reason, detail = evaluate_candidate_portfolio_risk(
        candidate(), risk_config=risk_config, sector_counts={}, tag_counts={},
    )
    assert ok is True
    assert reason == "ok"
    assert detail["risk_profile"]["risk_dollars"] == 50.0
    assert detail["risk_profile"]["risk_pct"] == 0.5


def test_evaluate_candidate_portfolio_risk_blocks_too_much_risk():
    risk_config = build_portfolio_risk_config(cfg())
    ok, reason, _ = evaluate_candidate_portfolio_risk(
        candidate(qty=100), risk_config=risk_config,
        sector_counts={}, tag_counts={},
    )
    assert ok is False
    assert "exceeds limit" in reason


def test_PR_A_stale_pending_rows_no_longer_jam_the_gate():
    """Regression: 9 stale 'pending' tracking rows must NOT block today's picks."""
    stale = [
        {"ticker": f"OLD{i}", "evaluation_status": "pending"} for i in range(100)
    ]
    allowed, blocked, summary = apply_portfolio_risk_gate(
        [candidate("AAPL", sector="Technology", tag="TECH"),
         candidate("JPM",  sector="Financials", tag="BANK")],
        cfg(max_new=5),
        existing_positions=stale,  # ignored by PR-A
    )
    assert {p["ticker"] for p in allowed} == {"AAPL", "JPM"}
    assert blocked == []
    assert summary["allowed_count"] == 2
    # Legacy keys must be present (None) so old report code doesn't crash.
    assert summary["available_slots"] is None
    assert summary["open_position_count"] is None


def test_max_new_picks_per_day_caps_today_only():
    cands = [
        candidate("AAPL", sector="Technology", tag="TECH",      composite=0.9),
        candidate("JPM",  sector="Financials", tag="BANK",      composite=0.8),
        candidate("XOM",  sector="Energy",     tag="OIL",       composite=0.7),
    ]
    allowed, blocked, summary = apply_portfolio_risk_gate(cands, cfg(max_new=2))
    assert [p["ticker"] for p in allowed] == ["AAPL", "JPM"]
    assert [b["ticker"] for b in blocked] == ["XOM"]
    assert blocked[0]["block_type"] == "max_new_picks_per_day"
    assert summary["allowed_count"] == 2
    assert summary["max_new_picks_per_day"] == 2


def test_apply_portfolio_gate_enforces_sector_and_tag_caps_today_only():
    aapl = candidate("AAPL", sector="Technology", tag="TECH", composite=0.9)
    msft = candidate("MSFT", sector="Technology", tag="TECH", composite=0.8)
    allowed, blocked, summary = apply_portfolio_risk_gate(
        [aapl, msft], cfg(max_new=5), existing_positions=[],
    )
    assert [p["ticker"] for p in allowed] == ["AAPL"]
    assert [b["ticker"] for b in blocked] == ["MSFT"]
    assert blocked[0]["rejection_stage"] == "portfolio_risk"
    assert ("daily sector cap" in blocked[0]["reason"]
            or "daily tag cap" in blocked[0]["reason"])
    assert summary["allowed_count"] == 1
    assert summary["today_sector_counts"]["Technology"] == 1


def test_apply_portfolio_gate_allows_diverse_until_max_new():
    aapl = candidate("AAPL", sector="Technology",        tag="TECH", composite=0.9)
    jpm  = candidate("JPM",  sector="Financial Services", tag="BANK", composite=0.8)
    xom  = candidate("XOM",  sector="Energy",            tag="OIL",  composite=0.7)
    allowed, blocked, summary = apply_portfolio_risk_gate(
        [aapl, jpm, xom], cfg(max_new=2),
    )
    assert [p["ticker"] for p in allowed] == ["AAPL", "JPM"]
    assert [p["ticker"] for p in blocked] == ["XOM"]
    assert blocked[0]["block_type"] == "max_new_picks_per_day"
    assert summary["allowed_count"] == 2
