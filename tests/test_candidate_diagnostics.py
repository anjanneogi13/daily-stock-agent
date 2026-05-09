from src.candidate_diagnostics import build_candidate_diagnostics, summarize_candidate


def candidate(ticker="AAPL", score=0.7):
    return {
        "ticker": ticker,
        "scores": {
            "composite": score,
            "trade_type": "swing",
            "sector_tag": "TECH",
            "day_score": 0.4,
        },
        "plan": {
            "entry": 100.0,
            "stop_loss": 95.0,
            "take_profit": 110.0,
            "risk_reward": 2.0,
            "quantity": 10,
        },
        "info_short": {"name": f"{ticker} Inc.", "sector": "Technology"},
        "days_to_earnings": 10,
    }


def test_summarize_candidate_is_compact_and_contains_key_fields():
    summary = summarize_candidate(candidate())

    assert summary["ticker"] == "AAPL"
    assert summary["score"] == 0.7
    assert summary["entry"] == 100.0
    assert summary["risk_reward"] == 2.0
    assert summary["quantity"] == 10


def test_build_candidate_diagnostics_counts_selected_and_rejected():
    aapl = candidate("AAPL")
    msft = candidate("MSFT")
    blocked = [{"ticker": "MSFT", "block_type": "recent_pick", "reason": "cooldown"}]

    diagnostics = build_candidate_diagnostics(
        pipeline={"universe_count": 2, "fetched_count": 2},
        scored_candidates=[aapl, msft],
        filtered_candidates=[aapl, msft],
        capped_candidates=[aapl, msft],
        pre_hard_block_candidates=[aapl, msft],
        hard_blocked_candidates=blocked,
        post_hard_block_candidates=[aapl],
        selected_picks=[aapl],
    )

    assert diagnostics["diagnostics_available"] is True
    assert diagnostics["stage_counts"]["selected_pick_count"] == 1
    assert diagnostics["stage_counts"]["rejected_candidate_count"] == 1
    assert diagnostics["selected_picks"][0]["ticker"] == "AAPL"
    assert diagnostics["hard_blocked_candidates"][0]["ticker"] == "MSFT"
    assert diagnostics["hard_blocked_candidates"][0]["rejection_stage"] == "hard_block"


def test_build_candidate_diagnostics_includes_premarket_sanity_blocks():
    aapl = candidate("AAPL")
    blocked = [{
        "ticker": "AAPL",
        "action": "WATCH_ONLY",
        "reason": "fresh quote unavailable",
        "candidate": aapl,
        "sanity": {"action": "WATCH_ONLY", "actionable": False},
    }]

    diagnostics = build_candidate_diagnostics(
        pipeline={"universe_count": 1, "fetched_count": 1},
        scored_candidates=[aapl],
        filtered_candidates=[aapl],
        capped_candidates=[aapl],
        pre_hard_block_candidates=[aapl],
        post_hard_block_candidates=[aapl],
        pre_premarket_sanity_candidates=[aapl],
        premarket_sanity_blocked_candidates=blocked,
        selected_picks=[],
    )

    assert diagnostics["stage_counts"]["premarket_sanity_blocked_count"] == 1
    assert diagnostics["premarket_sanity_blocked_candidates"][0]["ticker"] == "AAPL"
    assert diagnostics["premarket_sanity_blocked_candidates"][0]["rejection_stage"] == "premarket_sanity"


def test_build_candidate_diagnostics_counts_scored_not_filtered():
    aapl = candidate("AAPL")
    msft = candidate("MSFT")

    diagnostics = build_candidate_diagnostics(
        pipeline={},
        scored_candidates=[aapl, msft],
        filtered_candidates=[aapl],
        capped_candidates=[aapl],
        selected_picks=[aapl],
    )

    assert diagnostics["stage_counts"]["scored_not_filtered_count"] == 1

def test_build_candidate_diagnostics_includes_portfolio_risk_blocks():
    aapl = candidate("AAPL")
    blocked = [{
        "ticker": "AAPL",
        "block_type": "risk_limit",
        "reason": "per-trade risk exceeds limit",
        "candidate": aapl,
        "detail": {"risk_profile": {"risk_pct": 2.0}},
    }]

    diagnostics = build_candidate_diagnostics(
        pipeline={},
        scored_candidates=[aapl],
        filtered_candidates=[aapl],
        capped_candidates=[aapl],
        pre_hard_block_candidates=[aapl],
        post_hard_block_candidates=[aapl],
        pre_premarket_sanity_candidates=[aapl],
        portfolio_risk_blocked_candidates=blocked,
        selected_picks=[],
    )

    assert diagnostics["stage_counts"]["portfolio_risk_blocked_count"] == 1
    assert diagnostics["portfolio_risk_blocked_candidates"][0]["ticker"] == "AAPL"
    assert diagnostics["portfolio_risk_blocked_candidates"][0]["rejection_stage"] == "portfolio_risk"

def test_build_candidate_diagnostics_includes_missing_data_blocks():
    aapl = candidate("AAPL")
    blocked = [{
        "ticker": "AAPL",
        "block_type": "missing_or_malformed_required_data",
        "reason": "entry must be positive",
        "missing_or_invalid_fields": ["entry must be positive"],
        "required_field_snapshot": {"ticker": "AAPL", "entry": None},
        "candidate": aapl,
    }]

    diagnostics = build_candidate_diagnostics(
        pipeline={},
        scored_candidates=[aapl],
        filtered_candidates=[aapl],
        capped_candidates=[aapl],
        pre_hard_block_candidates=[aapl],
        post_hard_block_candidates=[aapl],
        pre_premarket_sanity_candidates=[aapl],
        missing_data_blocked_candidates=blocked,
        selected_picks=[],
    )

    assert diagnostics["stage_counts"]["missing_data_blocked_count"] == 1
    assert diagnostics["missing_data_blocked_candidates"][0]["ticker"] == "AAPL"
    assert diagnostics["missing_data_blocked_candidates"][0]["rejection_stage"] == "missing_data"
