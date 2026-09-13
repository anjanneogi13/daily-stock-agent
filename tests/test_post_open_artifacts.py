"""Lane 2 artifact writer tests: post-open watch-only opportunity lane."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.post_open_artifacts import (
    append_run_status,
    build_no_opportunity_payload,
    build_watchlist_payload,
    format_watchlist_markdown,
    no_opportunity_path,
    run_status_path,
    watchlist_path,
    write_no_opportunity_artifact,
    write_watchlist_artifacts,
)
from src.post_open_contract import IDEA_TYPE


def _opportunity(ticker: str = "NVDA") -> dict:
    return {
        "ticker": ticker,
        "date": "2026-09-14",
        "idea_type": IDEA_TYPE,
        "source": "news_signal",
        "headline": f"{ticker} strong catalyst evidence",
        "sentiment": "bullish",
        "observed_at_et": "2026-09-14T10:05:00-04:00",
        "score": 88.0,
        "risk_flags": ["news_only_no_breadth_confirmation"],
        "reason_against": "evidence is news-only with no breadth confirmation",
        "watch_reference_price": 100.0,
        "watch_stop_loss": 98.5,
        "watch_take_profit": 103.0,
        "watch_only": True,
        "official_premarket_pick": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }


def test_write_watchlist_artifacts_valid(tmp_path):
    payload = build_watchlist_payload(
        date_str="2026-09-14",
        opportunities=[_opportunity()],
        data_readiness={"news_signals_available": True},
    )
    result = write_watchlist_artifacts(payload, data_dir=tmp_path)
    assert result["valid"] is True

    reloaded = json.loads(Path(result["json_path"]).read_text())
    assert reloaded["artifact"] == "post_open_watchlist"
    assert reloaded["watch_only"] is True
    assert reloaded["official_pick_stats_impact"] == "none"
    assert reloaded["paper_trading_enabled"] is False
    assert reloaded["live_trading_enabled"] is False

    md = Path(result["markdown_path"]).read_text()
    assert "NOT official daily picks" in md
    assert "NOT buy instructions" in md
    assert "NVDA" in md


def test_write_watchlist_rejects_invalid_payload(tmp_path):
    payload = build_watchlist_payload(
        date_str="2026-09-14",
        opportunities=[{**_opportunity(), "paper_trading_enabled": True}],
        data_readiness={},
    )
    with pytest.raises(RuntimeError, match="failed validation"):
        write_watchlist_artifacts(payload, data_dir=tmp_path)
    assert not watchlist_path("2026-09-14", tmp_path).exists(), "invalid artifact must not be written"


def test_write_no_opportunity_artifact_valid(tmp_path):
    payload = build_no_opportunity_payload(
        date_str="2026-09-14",
        cause="NO_OPPORTUNITY_NO_FRESH_SIGNALS",
        summary="Only stale signals were available.",
        data_readiness={"news_signals_available": True},
        counts={"stale_or_expired": 4},
    )
    result = write_no_opportunity_artifact(payload, data_dir=tmp_path)
    reloaded = json.loads(Path(result["json_path"]).read_text())
    assert reloaded["decision"] == "no_opportunity"
    assert reloaded["primary_no_opportunity_cause"] == "NO_OPPORTUNITY_NO_FRESH_SIGNALS"
    assert reloaded["watch_only"] is True


def test_write_no_opportunity_rejects_unknown_cause(tmp_path):
    payload = build_no_opportunity_payload(
        date_str="2026-09-14",
        cause="NO_OPPORTUNITY_FAKE",
        summary="bad cause",
        data_readiness={},
    )
    with pytest.raises(RuntimeError, match="failed validation"):
        write_no_opportunity_artifact(payload, data_dir=tmp_path)
    assert not no_opportunity_path("2026-09-14", tmp_path).exists()


def test_append_run_status_ledger(tmp_path):
    append_run_status(date_str="2026-09-14", event="scan_started", data_dir=tmp_path)
    append_run_status(
        date_str="2026-09-14",
        event="completed_no_opportunity",
        data_dir=tmp_path,
        cause="NO_OPPORTUNITY_NO_FRESH_SIGNALS",
    )
    lines = run_status_path("2026-09-14", tmp_path).read_text().strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["event"] == "scan_started"
    assert second["event"] == "completed_no_opportunity"
    for row in (first, second):
        assert row["lane"] == "post_open_watch_only_opportunity"
        assert row["watch_only"] is True
        assert row["paper_trading_enabled"] is False
        assert row["live_trading_enabled"] is False


def test_markdown_reports_missing_levels_honestly():
    row = _opportunity()
    row["watch_reference_price"] = None
    row["watch_stop_loss"] = None
    row["watch_take_profit"] = None
    payload = build_watchlist_payload(
        date_str="2026-09-14",
        opportunities=[row],
        data_readiness={},
    )
    md = format_watchlist_markdown(payload)
    assert "Price levels: unavailable" in md
