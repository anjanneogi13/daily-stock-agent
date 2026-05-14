"""PR-A: provider failure must NOT block daily suggestions.
None price -> HALF_SIZE + provider_unverified, NOT WATCH_ONLY.
"""
from src.premarket_sanity_gate import (
    ACTION_HALF_SIZE,
    ACTION_SAFE,
    ACTION_SKIP_TODAY,
    ACTION_WATCH_ONLY,
    apply_premarket_sanity_decisions,
    evaluate_premarket_sanity,
)


def pick():
    return {
        "ticker": "AAPL",
        "plan": {
            "entry": 100.0,
            "stop_loss": 95.0,
            "take_profit": 110.0,
            "quantity": 20,
        },
    }


def test_safe_candidate_is_actionable():
    result = evaluate_premarket_sanity(
        pick(), current_price=100.5,
        market_snapshot={"global_action": "normal"},
    )
    assert result["action"] == ACTION_SAFE
    assert result["actionable"] is True
    assert result["size_multiplier"] == 1.0
    assert result["provider_unverified"] is False


def test_PR_A_missing_price_becomes_half_size_not_watch_only():
    """Regression: provider failure must not deny the user a daily suggestion."""
    result = evaluate_premarket_sanity(
        pick(), current_price=None,
        market_snapshot={"global_action": "normal"},
    )
    assert result["action"] == ACTION_HALF_SIZE
    assert result["actionable"] is True
    assert result["size_multiplier"] == 0.5
    assert result["provider_unverified"] is True


def test_missing_price_with_market_skip_all_still_skips():
    result = evaluate_premarket_sanity(
        pick(), current_price=None,
        market_snapshot={"global_action": "skip_all"},
    )
    assert result["action"] == ACTION_SKIP_TODAY
    assert result["actionable"] is False
    assert result["provider_unverified"] is True


def test_missing_entry_is_watch_only():
    bad = pick(); bad["plan"]["entry"] = None
    result = evaluate_premarket_sanity(
        bad, current_price=100.5,
        market_snapshot={"global_action": "normal"},
    )
    assert result["action"] == ACTION_WATCH_ONLY
    assert result["actionable"] is False


def test_missing_stop_is_watch_only():
    bad = pick(); bad["plan"]["stop_loss"] = None
    result = evaluate_premarket_sanity(
        bad, current_price=100.5,
        market_snapshot={"global_action": "normal"},
    )
    assert result["action"] == ACTION_WATCH_ONLY
    assert result["actionable"] is False


def test_price_at_stop_is_skip_today():
    result = evaluate_premarket_sanity(
        pick(), current_price=94.5,
        market_snapshot={"global_action": "normal"},
    )
    assert result["action"] == ACTION_SKIP_TODAY
    assert result["actionable"] is False


def test_large_gap_up_is_half_size():
    result = evaluate_premarket_sanity(
        pick(), current_price=104.0,
        market_snapshot={"global_action": "normal"},
    )
    assert result["action"] == ACTION_HALF_SIZE
    assert result["actionable"] is True
    assert result["size_multiplier"] == 0.5


def test_market_skip_all_with_price_blocks_candidate():
    result = evaluate_premarket_sanity(
        pick(), current_price=100.5,
        market_snapshot={"global_action": "skip_all"},
    )
    assert result["action"] == ACTION_SKIP_TODAY
    assert result["actionable"] is False
    assert result["reason"] == "broad market risk"


def test_PR_A_apply_gate_keeps_provider_unverified_in_official():
    """Both candidates must end up in 'official' — MSFT with HALF_SIZE."""
    candidates = [pick(), {**pick(), "ticker": "MSFT"}]
    official, blocked = apply_premarket_sanity_decisions(
        candidates,
        current_prices={"AAPL": 100.5, "MSFT": None},
        market_snapshot={"global_action": "normal"},
    )
    assert {p["ticker"] for p in official} == {"AAPL", "MSFT"}
    assert blocked == []
    msft = next(p for p in official if p["ticker"] == "MSFT")
    assert msft["premarket_action"] == ACTION_HALF_SIZE
    assert msft["premarket_sanity"]["provider_unverified"] is True


def test_half_size_reduces_quantity_before_official_logging():
    candidate = pick()
    official, blocked = apply_premarket_sanity_decisions(
        [candidate],
        current_prices={"AAPL": 104.0},
        market_snapshot={"global_action": "normal"},
    )
    assert blocked == []
    assert len(official) == 1
    assert official[0]["premarket_action"] == ACTION_HALF_SIZE
    assert official[0]["plan"]["quantity"] == 10
    assert official[0]["plan"]["premarket_size_multiplier"] == 0.5
