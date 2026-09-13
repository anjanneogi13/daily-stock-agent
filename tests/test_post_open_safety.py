"""Lane 2 safety invariants: watch-only lane must never touch official Lane 1 state.

Blueprint rule: watch-only lanes must never mutate data/picks_log.csv,
data/signal_journal.jsonl, data/learning_journal.jsonl, or official pick
artifacts, and must never emit buy-instruction wording.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.run_post_open_watch_only import run_post_open_watch_only
from src.post_open_contract import has_forbidden_action_wording

ET = ZoneInfo("America/New_York")
NOW_OPEN = datetime(2026, 9, 14, 11, 0, tzinfo=ET)
DATE = "2026-09-14"

OFFICIAL_LANE1_FILES = (
    "picks_log.csv",
    "signal_journal.jsonl",
    "learning_journal.jsonl",
    f"daily_picks_{DATE}.json",
    f"daily_picks_no_pick_report_{DATE}.json",
)


def _seed_official_state(data_dir: Path) -> dict[str, str]:
    data_dir.mkdir(parents=True, exist_ok=True)
    contents = {
        "picks_log.csv": "pick_date,ticker,evaluation_status,watch_only\n2026-09-14,ABCD,pending,\n",
        "signal_journal.jsonl": json.dumps({"date": DATE, "ticker": "ABCD"}) + "\n",
        "learning_journal.jsonl": json.dumps({"date": DATE, "lesson": "seed"}) + "\n",
        f"daily_picks_{DATE}.json": json.dumps({"date": DATE, "picks": [{"ticker": "ABCD"}]}),
        f"daily_picks_no_pick_report_{DATE}.json": json.dumps({"date": DATE, "decision": "no_pick"}),
    }
    for name, content in contents.items():
        (data_dir / name).write_text(content)
    return contents


def _seed_signals(data_dir: Path) -> None:
    (data_dir / "news_signals.json").write_text(json.dumps({
        "NVDA": {
            "ticker": "NVDA",
            "sentiment": "bullish",
            "tradeable_score": 0.8,
            "score_delta": 0.1,
            "headline": "NVDA reports strong quarter",
            "added_at": (NOW_OPEN - timedelta(hours=1)).astimezone(timezone.utc).isoformat(),
            "expires": (NOW_OPEN + timedelta(hours=6)).astimezone(timezone.utc).isoformat(),
            "current_price": 100.0,
        }
    }))


def test_lane2_never_mutates_official_lane1_state(tmp_path):
    before = _seed_official_state(tmp_path)
    _seed_signals(tmp_path)

    result = run_post_open_watch_only(
        date_str=DATE, now=NOW_OPEN, data_dir=tmp_path, trading_day_checker=lambda d: True
    )
    assert result["decision"] == "watch_only_opportunities"

    for name, original in before.items():
        assert (tmp_path / name).read_text() == original, f"Lane 2 mutated official file {name}"


def test_lane2_outputs_have_safety_flags_and_no_buy_wording(tmp_path):
    _seed_signals(tmp_path)
    run_post_open_watch_only(
        date_str=DATE, now=NOW_OPEN, data_dir=tmp_path, trading_day_checker=lambda d: True
    )

    payload = json.loads((tmp_path / f"post_open_watchlist_{DATE}.json").read_text())
    assert payload["watch_only"] is True
    assert payload["paper_trading_enabled"] is False
    assert payload["live_trading_enabled"] is False
    assert payload["official_pick_stats_impact"] == "none"
    for row in payload["opportunities"]:
        assert row["watch_only"] is True
        assert row["official_premarket_pick"] is False
        assert not has_forbidden_action_wording(row["reason_against"])

    md = (tmp_path / f"post_open_opportunity_report_{DATE}.md").read_text()
    for line in md.splitlines():
        lowered = line.strip().lower()
        assert not lowered.startswith("buy "), f"buy-instruction wording in markdown: {line}"
        assert not lowered.startswith("sell "), f"sell-instruction wording in markdown: {line}"


def test_forbidden_wording_detector():
    assert has_forbidden_action_wording("buy NVDA at the open")
    assert has_forbidden_action_wording("enter now before the squeeze")
    assert has_forbidden_action_wording("execute the trade immediately")
    assert not has_forbidden_action_wording("buyback program announced")
    assert not has_forbidden_action_wording("evidence is news-only; institutional buying unconfirmed")
