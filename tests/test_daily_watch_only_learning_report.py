import json
from pathlib import Path

from scripts.daily_watch_only_learning_report import build_summary, format_markdown, write_outputs


def test_watch_only_learning_report_summarizes_artifacts(tmp_path):
    data = tmp_path / "data"
    data.mkdir()

    (data / "late_daily_ideas_2026-05-06.jsonl").write_text(
        json.dumps({
            "ticker": "ONC",
            "idea_type": "late_daily_watch_only",
            "mode": "monitoring_only",
            "watch_only": True,
            "paper_trading_enabled": False,
            "live_trading_enabled": False,
            "watch_buy_price": 315.39,
            "watch_stop_loss": 310.66,
            "watch_take_profit": 324.85,
            "risk_reward": 2.0,
            "score": 100,
            "source": "news_signal",
            "reason": "earnings beat",
        }) + "\n"
    )

    (data / "opening_range_observations_2026-05-06.jsonl").write_text(
        json.dumps({
            "ticker": "NET",
            "scanner": "opening_range",
            "mode": "monitoring_only",
            "watch_only": True,
            "entry_observe": 248.69,
            "stop_loss_observe": 234.76,
            "take_profit_observe": 269.585,
            "score": 82.734,
            "breakout_pct": 2.578,
            "volume_ratio": 2.5954,
        }) + "\n"
    )

    (data / "opening_range_run_status_2026-05-06.jsonl").write_text(
        json.dumps({
            "event": "monitor_completed",
            "result": "alerts_ready",
            "github": {"run_id": "123", "sha": "abc", "workflow": "Intraday Monitor"},
        }) + "\n"
    )

    (data / "intraday_alerts_2026-05-06.json").write_text(
        json.dumps(["NEW|SMCI|7", "OR|NET|2026-05-06T09:30"])
    )

    summary = build_summary("2026-05-06", data_dir=data)

    assert summary["mode"] == "monitoring_only"
    assert summary["watch_only"] is True
    assert summary["official_pick_stats_included"] is False
    assert summary["paper_trading_enabled"] is False
    assert summary["live_trading_enabled"] is False
    assert summary["late_daily_watch_only"]["count"] == 1
    assert summary["opening_range_watch_only"]["count"] == 1
    assert summary["intraday_dedupe_fingerprints"]["momentum_count"] == 1
    assert summary["intraday_dedupe_fingerprints"]["opening_range_count"] == 1
    assert summary["opening_range_run_status"]["latest_github_run_id"] == "123"

    md = format_markdown(summary)
    assert "Watch-Only Learning Report" in md
    assert "Official P&L counted:** no" in md
    assert "ONC" in md
    assert "NET" in md
    assert "NEW|SMCI|7" in md


def test_watch_only_learning_report_writes_outputs(tmp_path):
    data = tmp_path / "data"
    data.mkdir()

    summary = build_summary("2026-05-06", data_dir=data)
    json_path, md_path = write_outputs(summary, data_dir=data)

    assert json_path.exists()
    assert md_path.exists()
    payload = json.loads(json_path.read_text())
    assert payload["date"] == "2026-05-06"
    assert payload["ready_for_paper_trading"] is False
    assert "Paper trading" in md_path.read_text()
