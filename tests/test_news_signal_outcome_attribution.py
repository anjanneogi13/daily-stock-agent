import json
from datetime import datetime, timezone

import pandas as pd

import scripts.news_signal_outcome_attribution as mod


def test_load_evidence_combines_and_dedupes_sources(tmp_path):
    data = tmp_path / "data"
    data.mkdir()

    (data / "news_signals.json").write_text(json.dumps({
        "NET": {
            "ticker": "NET",
            "score_delta": 0.1,
            "catalyst": "earnings_beat",
            "sentiment": "bullish",
            "tradeable_score": 0.92,
            "action_window": "next_day",
            "headline": "NET beats earnings",
            "added_at": "2026-05-06T12:00:00+00:00",
            "hard_block": False,
        }
    }))

    (data / "watchlist.json").write_text(json.dumps({
        "items": [{
            "ticker": "NET",
            "tradeable_score": 0.92,
            "sentiment": "bullish",
            "category": "earnings_beat",
            "action_window": "next_day",
            "headline": "NET beats earnings",
            "added_at": "2026-05-06T12:00:00+00:00",
        }]
    }))

    (data / "news_log.jsonl").write_text(json.dumps({
        "source": "alpaca",
        "ticker_list": ["NET"],
        "headline": "NET beats earnings",
        "published_at": "2026-05-06T12:00:00+00:00",
        "classification": {
            "sentiment": "bullish",
            "category": "earnings_beat",
            "tradeable_score": 0.92,
            "primary_ticker": "NET",
            "action_window": "next_day",
        },
    }) + "\n")

    evidence = mod.load_evidence(data_dir=data)

    assert evidence
    assert {row["source"] for row in evidence} == {"news_signals", "watchlist", "news_log"}
    assert all(row["ticker"] == "NET" for row in evidence)


def test_evaluate_evidence_item_with_fake_price_history(monkeypatch):
    dates = pd.to_datetime([
        "2026-05-06",
        "2026-05-07",
        "2026-05-08",
        "2026-05-11",
    ])
    hist = pd.DataFrame({"Close": [100.0, 103.0, 101.0, 106.0]}, index=dates)

    monkeypatch.setattr(mod, "_history_for_ticker", lambda ticker, signal_dt, horizon_days: hist)

    row = mod.evaluate_evidence_item({
        "source": "news_signals",
        "ticker": "NET",
        "signal_timestamp": "2026-05-06T12:00:00+00:00",
        "headline": "NET beats earnings",
        "sentiment": "bullish",
        "category": "earnings_beat",
        "tradeable_score": 0.92,
        "score_delta": 0.1,
        "action_window": "next_day",
        "hard_block": False,
    }, horizon_days=3)

    assert row["status"] == "evaluated"
    assert row["start_close"] == 100.0
    assert row["one_d_close"] == 103.0
    assert row["one_d_return_pct"] == 3.0
    assert row["horizon_close"] == 106.0
    assert row["horizon_return_pct"] == 6.0
    assert row["mode"] == "monitoring_only"
    assert row["read_only"] is True
    assert row["official_pick_stats_mutated"] is False
    assert row["paper_trading_enabled"] is False
    assert row["live_trading_enabled"] is False


def test_evaluate_evidence_item_handles_missing_history(monkeypatch):
    monkeypatch.setattr(mod, "_history_for_ticker", lambda ticker, signal_dt, horizon_days: None)

    row = mod.evaluate_evidence_item({
        "source": "news_signals",
        "ticker": "NET",
        "signal_timestamp": "2026-05-06T12:00:00+00:00",
    })

    assert row["status"] == "quote_unavailable"
    assert row["paper_trading_enabled"] is False
    assert row["live_trading_enabled"] is False


def test_write_and_summarize_outcomes(tmp_path):
    outcomes = [
        {
            "ticker": "NET",
            "status": "evaluated",
            "one_d_return_pct": 3.0,
            "horizon_return_pct": 6.0,
        },
        {
            "ticker": "AAPL",
            "status": "missing_future_data",
        },
    ]

    path = mod.write_outcomes(outcomes, date_str="2026-05-06", data_dir=tmp_path)
    assert path.exists()
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 2

    summary = mod.summarize_outcomes(outcomes)
    assert summary["count"] == 2
    assert summary["by_status"] == {"evaluated": 1, "missing_future_data": 1}
    assert summary["avg_one_d_return_pct"] == 3.0
    assert summary["avg_horizon_return_pct"] == 6.0
    assert summary["official_pick_stats_mutated"] is False


def test_main_no_write_does_not_create_output(tmp_path, monkeypatch, capsys):
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setattr(mod, "build_outcomes", lambda **kwargs: [])

    rc = mod.main(["--date", "2026-05-06", "--data-dir", str(data), "--no-write"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["count"] == 0
    assert not list(data.glob("news_signal_outcomes_*.jsonl"))
