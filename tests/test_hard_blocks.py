"""Coverage for src.hard_blocks gate logic.

These tests avoid network calls and avoid writing repo data by monkeypatching
sector/news dependencies and using tmp_path/cwd where apply_hard_blocks logs.
"""

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from src import hard_blocks as hb


def test_get_min_sl_pct_uses_price_tiers_and_safe_default():
    assert hb.get_min_sl_pct(150) == 1.5
    assert hb.get_min_sl_pct(50) == 2.0
    assert hb.get_min_sl_pct(20) == 2.5
    assert hb.get_min_sl_pct(4.99) == 3.0
    assert hb.get_min_sl_pct("bad") == 3.0
    assert hb.get_min_sl_pct(None) == 3.0


def test_block_penny_blocks_under_five_and_missing_entry_fail_closed():
    assert hb._block_penny({"ticker": "PENNY", "entry": 4.99}) == (
        False,
        "penny stock ($4.99 < $5.0)",
    )

    ok, reason = hb._block_penny({"ticker": "BROKEN"})
    assert ok is False
    assert "missing entry price" in reason


def test_block_penny_accepts_plan_entry_over_five():
    assert hb._block_penny({"ticker": "OK", "plan": {"entry": 5.00}}) == (True, "")


def test_block_sl_buffer_blocks_too_tight_by_tier():
    ok, reason = hb._block_sl_buffer(
        {"ticker": "MEGA", "plan": {"entry": 100.0, "stop_loss": 99.0}}
    )

    assert ok is False
    assert "SL too tight" in reason
    assert "1.0% < 1.5%" in reason


def test_block_sl_buffer_accepts_wide_enough_stop():
    assert hb._block_sl_buffer(
        {"ticker": "MEGA", "plan": {"entry": 100.0, "stop_loss": 98.0}}
    ) == (True, "")


def test_block_sl_buffer_missing_stop_loss_fail_closed_when_entry_present():
    ok, reason = hb._block_sl_buffer({"ticker": "BROKEN", "entry": 25.0})

    assert ok is False
    assert "missing stop_loss" in reason


def test_get_recent_pick_dates_reads_most_recent_per_ticker(tmp_path, monkeypatch):
    picks_log = tmp_path / "picks_log.csv"
    picks_log.write_text(
        "pick_date,ticker\n"
        "2026-05-01,AAPL\n"
        "2026-05-03,AAPL\n"
        "2026-05-02,MSFT\n"
    )
    monkeypatch.setattr(hb, "PICKS_LOG_PATH", picks_log)

    assert hb._get_recent_pick_dates() == {
        "AAPL": "2026-05-03",
        "MSFT": "2026-05-02",
    }


def test_block_recent_pick_blocks_within_cooldown():
    today = datetime.now().strftime("%Y-%m-%d")

    ok, reason = hb._block_recent_pick({"ticker": "AAPL"}, {"AAPL": today})

    assert ok is False
    assert "recent pick" in reason
    assert f"cooldown {hb.COOLDOWN_DAYS}d" in reason


def test_block_weak_sector_blocks_matching_sector_and_primary_tag():
    ok, reason = hb._block_weak_sector(
        {"ticker": "TECH", "info_short": {"sector": "Technology"}},
        {"Technology": -2.5},
    )
    assert ok is False
    assert "sector 'Technology' down -2.5%" in reason

    ok, reason = hb._block_weak_sector(
        {"ticker": "SEMI", "tag": "SEMI / AI"},
        {"SEMI": -3.0},
    )
    assert ok is False
    assert "tag 'SEMI' ETF down -3.0%" in reason


def test_block_catastrophic_news_blocks_when_news_signal_says_so(monkeypatch):
    import src.news_signals as news_signals

    monkeypatch.setattr(
        news_signals,
        "is_hard_blocked",
        lambda ticker: (True, "bankruptcy filing"),
    )

    ok, reason = hb._block_catastrophic_news({"ticker": "BAD"})

    assert ok is False
    assert reason == "catastrophic news (bankruptcy filing)"


def test_apply_hard_blocks_prioritizes_first_block_and_logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(hb, "get_weak_sectors", lambda: {"Technology": -4.0})
    monkeypatch.setattr(hb, "_get_recent_pick_dates", lambda: {})

    # Avoid depending on src.news_signals internals.
    monkeypatch.setattr(hb, "_block_catastrophic_news", lambda pick: (True, ""))

    picks = [
        {"ticker": "PENNY", "entry": 1.23, "stop_loss": 1.0},
        {"ticker": "OK", "entry": 100.0, "stop_loss": 97.0},
        {
            "ticker": "TECH",
            "entry": 100.0,
            "stop_loss": 97.0,
            "info_short": {"sector": "Technology"},
        },
    ]

    passed, blocked = hb.apply_hard_blocks(picks, check_sectors=True)

    assert [p["ticker"] for p in passed] == ["OK"]
    assert blocked == [
        {
            "ticker": "PENNY",
            "reason": "penny stock ($1.23 < $5.0)",
            "block_type": "penny_stock",
        },
        {
            "ticker": "TECH",
            "reason": "sector 'Technology' down -4.0% premarket",
            "block_type": "weak_sector",
        },
    ]

    log_path = Path("data/hard_blocks_log.json")
    assert log_path.exists()
    assert '"blocked_count": 2' in log_path.read_text()


def test_apply_hard_blocks_can_disable_sector_check(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(hb, "get_weak_sectors", lambda: pytest.fail("should not fetch sectors"))
    monkeypatch.setattr(hb, "_get_recent_pick_dates", lambda: {})
    monkeypatch.setattr(hb, "_block_catastrophic_news", lambda pick: (True, ""))

    picks = [
        {
            "ticker": "TECH",
            "entry": 100.0,
            "stop_loss": 97.0,
            "info_short": {"sector": "Technology"},
        }
    ]

    passed, blocked = hb.apply_hard_blocks(picks, check_sectors=False)

    assert [p["ticker"] for p in passed] == ["TECH"]
    assert blocked == []
