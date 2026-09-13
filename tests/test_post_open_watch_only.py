"""Lane 2 scanner + runner tests: post-open watch-only opportunity lane v0."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from scripts.run_post_open_watch_only import classify_session_window, run_post_open_watch_only
from src.post_open_scanner import (
    scan_post_open_opportunities,
    signal_is_fresh,
)

ET = ZoneInfo("America/New_York")

# 2026-09-14 is a Monday; 11:00 ET is inside the open window.
NOW_OPEN = datetime(2026, 9, 14, 11, 0, tzinfo=ET)
DATE = "2026-09-14"


def _fresh_signal(ticker: str, *, score: float = 0.75, sentiment: str = "bullish", **extra) -> dict:
    return {
        "ticker": ticker,
        "sentiment": sentiment,
        "tradeable_score": score,
        "score_delta": 0.1,
        "headline": f"{ticker} reports strong quarter and raises guidance",
        "added_at": (NOW_OPEN - timedelta(hours=1)).astimezone(timezone.utc).isoformat(),
        "expires": (NOW_OPEN + timedelta(hours=6)).astimezone(timezone.utc).isoformat(),
        **extra,
    }


def _write_inputs(
    data_dir: Path,
    *,
    news_signals: dict | None = None,
    watchlist_items: list | None = None,
    picks_rows: list[dict] | None = None,
    late_ideas: list[dict] | None = None,
) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    if news_signals is not None:
        (data_dir / "news_signals.json").write_text(json.dumps(news_signals))
    if watchlist_items is not None:
        (data_dir / "watchlist.json").write_text(json.dumps({"items": watchlist_items}))
    if picks_rows is not None:
        fieldnames = ["pick_date", "ticker", "evaluation_status", "watch_only"]
        with (data_dir / "picks_log.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(picks_rows)
    if late_ideas is not None:
        with (data_dir / f"late_daily_ideas_{DATE}.jsonl").open("w") as f:
            for row in late_ideas:
                f.write(json.dumps(row) + "\n")


def test_signal_freshness():
    now = datetime(2026, 9, 14, 15, 0, tzinfo=timezone.utc)
    fresh = {"added_at": "2026-09-14T14:00:00+00:00", "expires": "2026-09-15T14:00:00+00:00"}
    stale = {"added_at": "2026-09-10T14:00:00+00:00", "expires": "2026-09-15T14:00:00+00:00"}
    expired = {"added_at": "2026-09-14T14:00:00+00:00", "expires": "2026-09-14T14:30:00+00:00"}
    missing = {}
    assert signal_is_fresh(fresh, now)
    assert not signal_is_fresh(stale, now)
    assert not signal_is_fresh(expired, now)
    assert not signal_is_fresh(missing, now)


def test_scanner_accepts_fresh_bullish_signals(tmp_path):
    _write_inputs(tmp_path, news_signals={"NVDA": _fresh_signal("NVDA")}, watchlist_items=[])
    scan = scan_post_open_opportunities(date_str=DATE, now=NOW_OPEN, data_dir=tmp_path)
    assert scan["counts"]["accepted"] == 1
    row = scan["opportunities"][0]
    assert row["ticker"] == "NVDA"
    assert row["idea_type"] == "post_open_watch_only"
    assert row["watch_only"] is True
    assert row["official_premarket_pick"] is False
    assert row["reason_against"]


def test_scanner_skips_official_picks_and_late_idea_duplicates(tmp_path):
    _write_inputs(
        tmp_path,
        news_signals={
            "NVDA": _fresh_signal("NVDA"),
            "AMD": _fresh_signal("AMD"),
            "TSLA": _fresh_signal("TSLA"),
        },
        picks_rows=[{"pick_date": DATE, "ticker": "NVDA", "evaluation_status": "pending", "watch_only": ""}],
        late_ideas=[{"ticker": "AMD"}],
    )
    scan = scan_post_open_opportunities(date_str=DATE, now=NOW_OPEN, data_dir=tmp_path)
    tickers = [row["ticker"] for row in scan["opportunities"]]
    assert tickers == ["TSLA"]
    assert scan["counts"]["skipped_official_pick_today"] == 1
    assert scan["counts"]["skipped_late_idea_duplicate"] == 1


def test_scanner_rejects_bearish_hard_blocked_and_low_score(tmp_path):
    _write_inputs(tmp_path, news_signals={
        "BEAR": _fresh_signal("BEAR", sentiment="bearish"),
        "BLKD": _fresh_signal("BLKD", hard_block=True),
        "LOWS": _fresh_signal("LOWS", score=0.30),
    })
    scan = scan_post_open_opportunities(date_str=DATE, now=NOW_OPEN, data_dir=tmp_path)
    assert scan["opportunities"] == []
    assert scan["counts"]["rejected_or_below_threshold"] == 3


def test_scanner_caps_corporate_action_scores(tmp_path):
    _write_inputs(tmp_path, news_signals={
        "SPAC": _fresh_signal(
            "SPAC",
            score=0.95,
            headline="SPAC announces business combination with merger sub ahead of deal vote",
        ),
    })
    scan = scan_post_open_opportunities(date_str=DATE, now=NOW_OPEN, data_dir=tmp_path)
    row = scan["opportunities"][0]
    assert row["score"] <= 70.0
    assert "event_structure_uncertain" in row["risk_flags"]
    assert "cap" in row["score_explanation"]


def test_scanner_levels_only_from_payload_price(tmp_path):
    _write_inputs(tmp_path, news_signals={
        "QUOT": _fresh_signal("QUOT", current_price=50.0),
        "NOQT": _fresh_signal("NOQT"),
    })
    scan = scan_post_open_opportunities(date_str=DATE, now=NOW_OPEN, data_dir=tmp_path)
    by_ticker = {row["ticker"]: row for row in scan["opportunities"]}
    assert by_ticker["QUOT"]["watch_reference_price"] == 50.0
    assert by_ticker["QUOT"]["watch_stop_loss"] < 50.0 < by_ticker["QUOT"]["watch_take_profit"]
    assert by_ticker["NOQT"]["watch_reference_price"] is None
    assert scan["data_readiness"]["quote_provider_used"] is False


def test_session_window_classification():
    monday = datetime(2026, 9, 14, 8, 0, tzinfo=ET)
    assert classify_session_window(monday, trading_day=True) == "before_open"
    assert classify_session_window(monday.replace(hour=11), trading_day=True) == "open_window"
    assert classify_session_window(monday.replace(hour=15, minute=16), trading_day=True) == "after_new_opportunity_cutoff"
    assert classify_session_window(monday, trading_day=False) == "market_closed"


def test_runner_writes_watchlist_and_ledger(tmp_path):
    _write_inputs(tmp_path, news_signals={"NVDA": _fresh_signal("NVDA")})
    result = run_post_open_watch_only(
        date_str=DATE,
        now=NOW_OPEN,
        data_dir=tmp_path,
        trading_day_checker=lambda d: True,
    )
    assert result["decision"] == "watch_only_opportunities"
    assert (tmp_path / f"post_open_watchlist_{DATE}.json").exists()
    assert (tmp_path / f"post_open_opportunity_report_{DATE}.md").exists()

    ledger = (tmp_path / f"post_open_run_status_{DATE}.jsonl").read_text().strip().splitlines()
    events = [json.loads(line)["event"] for line in ledger]
    assert events == ["scan_started", "completed_watch_only_opportunities"]


def test_runner_writes_no_opportunity_when_below_threshold(tmp_path):
    _write_inputs(tmp_path, news_signals={"LOWS": _fresh_signal("LOWS", score=0.2)})
    result = run_post_open_watch_only(
        date_str=DATE,
        now=NOW_OPEN,
        data_dir=tmp_path,
        trading_day_checker=lambda d: True,
    )
    assert result["decision"] == "no_opportunity"
    payload = json.loads((tmp_path / f"post_open_no_opportunity_{DATE}.json").read_text())
    assert payload["primary_no_opportunity_cause"] == "NO_OPPORTUNITY_ALL_BELOW_THRESHOLD"


def test_runner_reports_missing_inputs_honestly(tmp_path):
    tmp_path.mkdir(exist_ok=True)
    result = run_post_open_watch_only(
        date_str=DATE,
        now=NOW_OPEN,
        data_dir=tmp_path,
        trading_day_checker=lambda d: True,
    )
    assert result["decision"] == "no_opportunity"
    payload = json.loads((tmp_path / f"post_open_no_opportunity_{DATE}.json").read_text())
    assert payload["primary_no_opportunity_cause"] == "NO_OPPORTUNITY_INPUTS_MISSING"
    assert "not evidence that no opportunities existed" in payload["human_readable_summary"]


def test_runner_skips_outside_session_window(tmp_path):
    _write_inputs(tmp_path, news_signals={"NVDA": _fresh_signal("NVDA")})
    late = datetime(2026, 9, 14, 15, 30, tzinfo=ET)
    result = run_post_open_watch_only(
        date_str=DATE,
        now=late,
        data_dir=tmp_path,
        trading_day_checker=lambda d: True,
    )
    assert result["decision"] == "no_opportunity"
    assert result["session_window"] == "after_new_opportunity_cutoff"
    payload = json.loads((tmp_path / f"post_open_no_opportunity_{DATE}.json").read_text())
    assert payload["primary_no_opportunity_cause"] == "NO_OPPORTUNITY_TOO_LATE_IN_SESSION"
    assert not (tmp_path / f"post_open_watchlist_{DATE}.json").exists()


def test_runner_skips_on_market_closed(tmp_path):
    result = run_post_open_watch_only(
        date_str="2026-09-13",
        now=datetime(2026, 9, 13, 11, 0, tzinfo=ET),  # Sunday
        data_dir=tmp_path,
        trading_day_checker=lambda d: False,
    )
    assert result["decision"] == "no_opportunity"
    payload = json.loads((tmp_path / "post_open_no_opportunity_2026-09-13.json").read_text())
    assert payload["primary_no_opportunity_cause"] == "NO_OPPORTUNITY_MARKET_CLOSED"


def test_runner_no_write_mode_writes_nothing(tmp_path):
    _write_inputs(tmp_path, news_signals={"NVDA": _fresh_signal("NVDA")})
    result = run_post_open_watch_only(
        date_str=DATE,
        now=NOW_OPEN,
        data_dir=tmp_path,
        trading_day_checker=lambda d: True,
        write=False,
    )
    assert result["decision"] == "watch_only_opportunities"
    assert not (tmp_path / f"post_open_watchlist_{DATE}.json").exists()
    assert not (tmp_path / f"post_open_run_status_{DATE}.jsonl").exists()
