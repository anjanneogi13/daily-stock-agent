"""Tests for scripts/validate_post_open_artifacts.py (Lane 2 v0)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.run_post_open_watch_only import run_post_open_watch_only
from scripts.validate_post_open_artifacts import validate_post_open_artifacts_for_date

ET = ZoneInfo("America/New_York")
NOW_OPEN = datetime(2026, 9, 14, 11, 0, tzinfo=ET)
DATE = "2026-09-14"


def _write_fresh_signal(data_dir: Path) -> None:
    from datetime import timedelta, timezone

    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "news_signals.json").write_text(json.dumps({
        "NVDA": {
            "ticker": "NVDA",
            "sentiment": "bullish",
            "tradeable_score": 0.8,
            "score_delta": 0.1,
            "headline": "NVDA reports strong quarter",
            "added_at": (NOW_OPEN - timedelta(hours=1)).astimezone(timezone.utc).isoformat(),
            "expires": (NOW_OPEN + timedelta(hours=6)).astimezone(timezone.utc).isoformat(),
        }
    }))


def test_validator_accepts_watchlist_outcome(tmp_path):
    _write_fresh_signal(tmp_path)
    run_post_open_watch_only(
        date_str=DATE, now=NOW_OPEN, data_dir=tmp_path, trading_day_checker=lambda d: True
    )
    result = validate_post_open_artifacts_for_date(DATE, tmp_path)
    assert result["valid"] is True
    assert result["decision"] == "watch_only_opportunities"
    assert result["run_status_ledger_exists"] is True


def test_validator_accepts_no_opportunity_outcome(tmp_path):
    run_post_open_watch_only(
        date_str=DATE, now=NOW_OPEN, data_dir=tmp_path, trading_day_checker=lambda d: True
    )
    result = validate_post_open_artifacts_for_date(DATE, tmp_path)
    assert result["valid"] is True
    assert result["decision"] == "no_opportunity"


def test_validator_rejects_missing_artifacts(tmp_path):
    result = validate_post_open_artifacts_for_date(DATE, tmp_path)
    assert result["valid"] is False
    assert any("no Lane 2 decision artifact" in e for e in result["errors"])


def test_validator_rejects_double_decision(tmp_path):
    _write_fresh_signal(tmp_path)
    run_post_open_watch_only(
        date_str=DATE, now=NOW_OPEN, data_dir=tmp_path, trading_day_checker=lambda d: True
    )
    # Manually create a conflicting second decision artifact.
    (tmp_path / f"post_open_no_opportunity_{DATE}.json").write_text(json.dumps({"decision": "no_opportunity"}))
    result = validate_post_open_artifacts_for_date(DATE, tmp_path)
    assert result["valid"] is False
    assert any("exactly one Lane 2 decision" in e for e in result["errors"])


def test_validator_rejects_tampered_safety_flags(tmp_path):
    _write_fresh_signal(tmp_path)
    run_post_open_watch_only(
        date_str=DATE, now=NOW_OPEN, data_dir=tmp_path, trading_day_checker=lambda d: True
    )
    path = tmp_path / f"post_open_watchlist_{DATE}.json"
    payload = json.loads(path.read_text())
    payload["paper_trading_enabled"] = True
    path.write_text(json.dumps(payload))

    result = validate_post_open_artifacts_for_date(DATE, tmp_path)
    assert result["valid"] is False
    assert any("paper_trading_enabled" in e for e in result["errors"])


def test_validator_rejects_missing_markdown_report(tmp_path):
    _write_fresh_signal(tmp_path)
    run_post_open_watch_only(
        date_str=DATE, now=NOW_OPEN, data_dir=tmp_path, trading_day_checker=lambda d: True
    )
    (tmp_path / f"post_open_opportunity_report_{DATE}.md").unlink()
    result = validate_post_open_artifacts_for_date(DATE, tmp_path)
    assert result["valid"] is False
    assert any("Markdown report is missing" in e for e in result["errors"])
