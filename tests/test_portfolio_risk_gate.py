from src.portfolio_risk_gate import (
    apply_portfolio_risk_gate,
    build_portfolio_risk_config,
    evaluate_candidate_portfolio_risk,
)


def cfg():
    return {
        "risk": {
            "account_size": 10000,
            "risk_per_trade_pct": 1.0,
            "max_positions": 2,
            "max_per_sector": 1,
            "max_per_tag": 1,
            "min_risk_reward": 1.0,
        }
    }


def candidate(ticker="AAPL", sector="Technology", tag="TECH", qty=10, rr=2.0):
    return {
        "ticker": ticker,
        "scores": {"composite": 0.8, "sector_tag": tag},
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
    assert result["max_positions"] == 2
    assert result["max_per_sector"] == 1
    assert result["max_per_tag"] == 1


def test_evaluate_candidate_portfolio_risk_allows_valid_candidate():
    risk_config = build_portfolio_risk_config(cfg())

    ok, reason, detail = evaluate_candidate_portfolio_risk(
        candidate(),
        risk_config=risk_config,
        sector_counts={},
        tag_counts={},
    )

    assert ok is True
    assert reason == "ok"
    assert detail["risk_profile"]["risk_dollars"] == 50.0
    assert detail["risk_profile"]["risk_pct"] == 0.5


def test_evaluate_candidate_portfolio_risk_blocks_too_much_risk():
    risk_config = build_portfolio_risk_config(cfg())

    ok, reason, _detail = evaluate_candidate_portfolio_risk(
        candidate(qty=100),
        risk_config=risk_config,
        sector_counts={},
        tag_counts={},
    )

    assert ok is False
    assert "exceeds limit" in reason


def test_apply_portfolio_gate_blocks_when_max_positions_reached():
    allowed, blocked, summary = apply_portfolio_risk_gate(
        [candidate("AAPL")],
        cfg(),
        existing_positions=[
            {"ticker": "MSFT", "evaluation_status": "pending"},
            {"ticker": "NVDA", "evaluation_status": "pending"},
        ],
    )

    assert allowed == []
    assert blocked[0]["block_type"] == "max_positions"
    assert summary["available_slots"] == 0


def test_apply_portfolio_gate_enforces_sector_and_tag_caps():
    aapl = candidate("AAPL", sector="Technology", tag="TECH")
    msft = candidate("MSFT", sector="Technology", tag="TECH")

    allowed, blocked, summary = apply_portfolio_risk_gate(
        [aapl, msft],
        cfg(),
        existing_positions=[],
    )

    assert [p["ticker"] for p in allowed] == ["AAPL"]
    assert [p["ticker"] for p in blocked] == ["MSFT"]
    assert blocked[0]["rejection_stage"] == "portfolio_risk"
    assert "sector exposure cap" in blocked[0]["reason"] or "tag exposure cap" in blocked[0]["reason"]
    assert summary["allowed_count"] == 1


def test_apply_portfolio_gate_allows_different_sector_and_tag_until_max_positions():
    aapl = candidate("AAPL", sector="Technology", tag="TECH")
    jpm = candidate("JPM", sector="Financial Services", tag="BANK")
    xom = candidate("XOM", sector="Energy", tag="OIL")

    allowed, blocked, summary = apply_portfolio_risk_gate(
        [aapl, jpm, xom],
        cfg(),
        existing_positions=[],
    )

    assert [p["ticker"] for p in allowed] == ["AAPL", "JPM"]
    assert [p["ticker"] for p in blocked] == ["XOM"]
    assert blocked[0]["block_type"] == "max_positions"
    assert summary["allowed_count"] == 2
