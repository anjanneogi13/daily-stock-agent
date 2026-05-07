import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import scripts.run_news_engine as runner


ET = ZoneInfo("America/New_York")


def test_build_news_engine_run_status_is_monitoring_only():
    row = runner.build_news_engine_run_status(
        event="news_engine_completed",
        result="completed",
        reason="ok",
        items_fetched=3,
        items_classified=2,
        signals_added=1,
        hard_blocks=0,
        watchlist_added=1,
        high_impact_count=1,
        telegram_enabled=False,
        telegram_attempted=0,
        now=datetime(2026, 5, 6, 12, 30, tzinfo=ET),
    )

    assert row["date"] == "2026-05-06"
    assert row["workflow"] == "news-engine"
    assert row["mode"] == "monitoring_only"
    assert row["paper_trading_enabled"] is False
    assert row["live_trading_enabled"] is False
    assert row["official_picks_created"] is False
    assert row["items_fetched"] == 3
    assert row["items_classified"] == 2
    assert row["signals_added"] == 1
    assert row["watchlist_added"] == 1
    assert row["lookback_minutes"] == runner.DEFAULT_NEWS_LOOKBACK_MINUTES


def test_append_news_engine_run_status_writes_jsonl(tmp_path):
    path = tmp_path / "news_engine_run_status_2026-05-06.jsonl"

    out = runner.append_news_engine_run_status(
        event="news_engine_completed",
        result="no_fresh_news",
        reason="No fresh news",
        path=path,
        now=datetime(2026, 5, 6, 7, 30, tzinfo=ET),
    )

    assert out == path
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 1
    assert rows[0]["event"] == "news_engine_completed"
    assert rows[0]["result"] == "no_fresh_news"
    assert rows[0]["watchlist_added"] == 0


def test_news_engine_main_records_no_fresh_news_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runner, "get_watchlist_tickers", lambda: ["AAPL"])
    monkeypatch.setattr(runner, "fetch_all_news", lambda **kwargs: [])

    runner.main()

    paths = list((tmp_path / "data").glob("news_engine_run_status_*.jsonl"))
    assert len(paths) == 1
    rows = [json.loads(line) for line in paths[0].read_text().splitlines()]
    assert [r["event"] for r in rows] == ["news_engine_started", "news_engine_completed"]
    assert rows[-1]["result"] == "no_fresh_news"
    assert rows[-1]["items_fetched"] == 0


def test_news_engine_workflow_commits_run_status_artifact():
    text = Path(".github/workflows/news_engine.yml").read_text()
    assert "data/news_engine_run_status_*.jsonl" in text
    assert "data/watchlist.json" in text
    assert "data/news_signals.json" in text


def test_news_lookback_minutes_defaults_to_120(monkeypatch):
    monkeypatch.delenv("NEWS_LOOKBACK_MINUTES", raising=False)

    assert runner.news_lookback_minutes() == 120


def test_news_lookback_minutes_is_configurable_and_clamped(monkeypatch):
    monkeypatch.setenv("NEWS_LOOKBACK_MINUTES", "180")
    assert runner.news_lookback_minutes() == 180

    monkeypatch.setenv("NEWS_LOOKBACK_MINUTES", "5")
    assert runner.news_lookback_minutes() == runner.MIN_NEWS_LOOKBACK_MINUTES

    monkeypatch.setenv("NEWS_LOOKBACK_MINUTES", "999")
    assert runner.news_lookback_minutes() == runner.MAX_NEWS_LOOKBACK_MINUTES

    monkeypatch.setenv("NEWS_LOOKBACK_MINUTES", "not-a-number")
    assert runner.news_lookback_minutes() == runner.DEFAULT_NEWS_LOOKBACK_MINUTES


def test_news_engine_main_uses_default_lookback(tmp_path, monkeypatch):
    captured = {}

    def fake_fetch_all_news(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NEWS_LOOKBACK_MINUTES", raising=False)
    monkeypatch.setattr(runner, "get_watchlist_tickers", lambda: ["AAPL"])
    monkeypatch.setattr(runner, "fetch_all_news", fake_fetch_all_news)

    runner.main()

    assert captured["watchlist_tickers"] == ["AAPL"]
    assert captured["since_minutes"] == 120

    paths = list((tmp_path / "data").glob("news_engine_run_status_*.jsonl"))
    rows = [json.loads(line) for line in paths[0].read_text().splitlines()]
    assert rows[-1]["lookback_minutes"] == 120
