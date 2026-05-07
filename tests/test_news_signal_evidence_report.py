import csv
import json
from pathlib import Path

from scripts.news_signal_evidence_report import build_report, format_markdown, write_outputs


def test_news_signal_evidence_report_summarizes_artifacts(tmp_path):
    data = tmp_path / "data"
    data.mkdir()

    (data / "news_log.jsonl").write_text(
        json.dumps({
            "source": "alpaca",
            "ticker_list": ["NET"],
            "headline": "NET beats earnings",
            "classification": {
                "sentiment": "bullish",
                "category": "earnings_beat",
                "tradeable_score": 0.92,
                "primary_ticker": "NET",
                "action_window": "next_day",
            },
        }) + "\n"
    )

    (data / "news_signals.json").write_text(json.dumps({
        "NET": {
            "ticker": "NET",
            "score_delta": 0.1,
            "catalyst": "earnings_beat",
            "sentiment": "bullish",
            "tradeable_score": 0.92,
            "action_window": "next_day",
            "headline": "NET beats earnings",
            "hard_block": False,
            "added_at": "2026-05-06T12:00:00+00:00",
            "expires": "2026-05-13T12:00:00+00:00",
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

    (data / "news_engine_run_status_2026-05-06.jsonl").write_text(
        json.dumps({
            "event": "news_engine_completed",
            "result": "completed",
            "items_fetched": 3,
            "items_classified": 2,
            "signals_added": 1,
            "hard_blocks": 0,
            "watchlist_added": 1,
            "lookback_minutes": 120,
            "timestamp_et": "2026-05-06T12:30:00-04:00",
            "github": {"run_id": "123"},
        }) + "\n"
    )

    (data / "late_daily_ideas_2026-05-06.jsonl").write_text(
        json.dumps({
            "ticker": "NET",
            "source": "news_signal",
            "score": 102,
            "tradeable_score": 0.92,
            "score_delta": 0.1,
            "watch_only": True,
            "mode": "monitoring_only",
        }) + "\n"
    )

    with (data / "picks_log.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "pick_date", "ticker", "trade_type", "watch_only",
            "watch_only_reason", "news_action_window", "score",
        ])
        writer.writeheader()
        writer.writerow({
            "pick_date": "2026-05-06",
            "ticker": "NET",
            "trade_type": "swing",
            "watch_only": "False",
            "watch_only_reason": "",
            "news_action_window": "next_day",
            "score": "0.91",
        })

    report = build_report("2026-05-06", data_dir=data)

    assert report["artifact"] == "news_signal_evidence_report"
    assert report["mode"] == "monitoring_only"
    assert report["read_only"] is True
    assert report["official_pick_stats_mutated"] is False
    assert report["paper_trading_enabled"] is False
    assert report["live_trading_enabled"] is False
    assert report["news_log"]["count"] == 1
    assert report["news_log"]["high_tradeable_count"] == 1
    assert report["active_news_signals"]["count"] == 1
    assert report["active_news_signals"]["bullish_count"] == 1
    assert report["watchlist"]["count"] == 1
    assert report["news_engine_run_status"]["totals"]["items_fetched"] == 3
    assert report["news_engine_run_status"]["lookback_minutes_latest"] == 120
    assert report["late_daily_ideas"]["news_or_watchlist_count"] == 1
    assert report["official_picks_news_usage"]["with_news_fields_count"] == 1

    md = format_markdown(report)
    assert "News Signal Evidence Report" in md
    assert "NET" in md
    assert "Read-only" in md
    assert "Next evidence gap" in md


def test_news_signal_evidence_report_writes_outputs(tmp_path):
    data = tmp_path / "data"
    data.mkdir()

    report = build_report("2026-05-06", data_dir=data)
    json_path, md_path = write_outputs(report, data_dir=data)

    assert json_path.exists()
    assert md_path.exists()
    payload = json.loads(json_path.read_text())
    assert payload["date"] == "2026-05-06"
    assert payload["read_only"] is True
    assert "News Signal Evidence Report" in md_path.read_text()
