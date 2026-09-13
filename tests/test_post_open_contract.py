"""Lane 2 contract tests: post-open watch-only opportunity lane (Phase 3 v0)."""

from __future__ import annotations

import pytest

from src.post_open_contract import (
    DECISION_NO_OPPORTUNITY,
    DECISION_WATCH_ONLY_OPPORTUNITIES,
    IDEA_TYPE,
    STRATEGY_LANE,
    contract_summary,
    has_forbidden_action_wording,
    validate_post_open_decision,
    validate_post_open_no_opportunity,
    validate_post_open_opportunity,
    validate_post_open_watchlist,
)


def _valid_opportunity() -> dict:
    return {
        "ticker": "NVDA",
        "date": "2026-09-14",
        "idea_type": IDEA_TYPE,
        "source": "news_signal",
        "headline": "NVDA announces record data-center revenue",
        "sentiment": "bullish",
        "observed_at_et": "2026-09-14T10:05:00-04:00",
        "score": 88.0,
        "risk_flags": ["news_only_no_breadth_confirmation"],
        "reason_against": "evidence is news-only with no breadth confirmation",
        "watch_reference_price": 100.0,
        "watch_stop_loss": 98.5,
        "watch_take_profit": 103.0,
        "reason": "Observed post-open momentum with fresh catalyst evidence",
        "watch_only": True,
        "official_premarket_pick": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }


def _valid_watchlist() -> dict:
    return {
        "artifact": "post_open_watchlist",
        "date": "2026-09-14",
        "decision": DECISION_WATCH_ONLY_OPPORTUNITIES,
        "strategy_lane": STRATEGY_LANE,
        "contract_version": "post_open_contract_v1",
        "strategy_version": "post_open_watch_only_v0",
        "generated_at_utc": "2026-09-14T14:10:00Z",
        "opportunity_count": 1,
        "opportunities": [_valid_opportunity()],
        "data_readiness": {"news_signals_available": True},
        "watch_only": True,
        "official_pick_stats_impact": "none",
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }


def _valid_no_opportunity() -> dict:
    return {
        "artifact": "post_open_no_opportunity",
        "date": "2026-09-14",
        "decision": DECISION_NO_OPPORTUNITY,
        "strategy_lane": STRATEGY_LANE,
        "contract_version": "post_open_contract_v1",
        "strategy_version": "post_open_watch_only_v0",
        "generated_at_utc": "2026-09-14T14:10:00Z",
        "primary_no_opportunity_cause": "NO_OPPORTUNITY_ALL_BELOW_THRESHOLD",
        "human_readable_summary": "No candidate met the watch-only evidence threshold.",
        "data_readiness": {"news_signals_available": True},
        "watch_only": True,
        "official_pick_stats_impact": "none",
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }


def test_valid_opportunity_passes():
    assert validate_post_open_opportunity(_valid_opportunity()) == []


def test_valid_watchlist_passes():
    assert validate_post_open_watchlist(_valid_watchlist()) == []


def test_valid_no_opportunity_passes():
    assert validate_post_open_no_opportunity(_valid_no_opportunity()) == []


@pytest.mark.parametrize("field", ["watch_only", "official_premarket_pick"])
def test_opportunity_rejects_wrong_lane_flags(field):
    row = _valid_opportunity()
    row[field] = not row[field]
    errors = validate_post_open_opportunity(row)
    assert errors, f"flipping {field} must fail validation"


@pytest.mark.parametrize("field", ["paper_trading_enabled", "live_trading_enabled"])
def test_opportunity_rejects_trading_flags(field):
    row = _valid_opportunity()
    row[field] = True
    errors = validate_post_open_opportunity(row)
    assert any(field in e for e in errors)


def test_opportunity_rejects_wrong_idea_type():
    row = _valid_opportunity()
    row["idea_type"] = "official_pick"
    assert any("idea_type" in e for e in validate_post_open_opportunity(row))


def test_opportunity_rejects_action_wording_in_copy():
    row = _valid_opportunity()
    row["reason"] = "BUY now before the close"
    errors = validate_post_open_opportunity(row)
    assert any("forbidden executable-action wording" in e for e in errors)


def test_opportunity_rejects_non_positive_levels():
    row = _valid_opportunity()
    row["watch_reference_price"] = 0
    assert any("watch_reference_price" in e for e in validate_post_open_opportunity(row))


def test_opportunity_allows_missing_levels():
    row = _valid_opportunity()
    row["watch_reference_price"] = None
    row["watch_stop_loss"] = None
    row["watch_take_profit"] = None
    assert validate_post_open_opportunity(row) == []


def test_watchlist_rejects_count_mismatch():
    payload = _valid_watchlist()
    payload["opportunity_count"] = 7
    assert any("opportunity_count" in e for e in validate_post_open_watchlist(payload))


def test_watchlist_rejects_empty_opportunities():
    payload = _valid_watchlist()
    payload["opportunities"] = []
    payload["opportunity_count"] = 0
    errors = validate_post_open_watchlist(payload)
    assert any("no-opportunity artifact" in e for e in errors)


def test_watchlist_rejects_official_stats_impact():
    payload = _valid_watchlist()
    payload["official_pick_stats_impact"] = "counted"
    assert any("official_pick_stats_impact" in e for e in validate_post_open_watchlist(payload))


def test_no_opportunity_rejects_unknown_cause():
    payload = _valid_no_opportunity()
    payload["primary_no_opportunity_cause"] = "NO_OPPORTUNITY_MADE_UP"
    assert any("unsupported primary_no_opportunity_cause" in e for e in validate_post_open_no_opportunity(payload))


def test_decision_router_handles_both_and_rejects_unknown():
    assert validate_post_open_decision(_valid_watchlist()) == []
    assert validate_post_open_decision(_valid_no_opportunity()) == []
    assert validate_post_open_decision({"decision": "official_pick"}) != []


def test_forbidden_action_wording_detector():
    assert has_forbidden_action_wording("BUY now")
    assert has_forbidden_action_wording("buy NVDA at open")
    assert has_forbidden_action_wording("please execute the trade")
    assert has_forbidden_action_wording("enter a position here")
    assert not has_forbidden_action_wording("watch-only reference level near $100")
    assert not has_forbidden_action_wording("buyback program announced")  # not "^buy " instruction... requires care
    assert not has_forbidden_action_wording("")


def test_contract_summary_is_safe():
    summary = contract_summary()
    assert summary["strategy_lane"] == STRATEGY_LANE
    assert summary["official_pick_stats_impact"] == "none"
    assert summary["paper_trading_enabled"] is False
    assert summary["live_trading_enabled"] is False
