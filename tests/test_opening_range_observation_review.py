import json
import subprocess
from pathlib import Path

from scripts.review_opening_range_observations import (
    format_report,
    load_observations,
    summarize_observations,
)


def write_jsonl(path: Path, rows: list[dict], invalid: bool = False):
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
        if invalid:
            f.write("{not-json}\n")


def obs(**kw):
    base = {
        "ts": "2026-05-06T14:00:00+00:00",
        "ticker": "NET",
        "scanner": "opening_range",
        "mode": "monitoring_only",
        "watch_only": True,
        "candidate": True,
        "price": 101.6,
        "score": 80,
        "breakout_pct": 0.6,
        "volume_ratio": 3.2,
        "reason": "opening-range breakout",
    }
    base.update(kw)
    return base


def test_load_observations_reads_jsonl_and_counts_invalid_lines(tmp_path):
    path = tmp_path / "opening_range_observations_2026-05-06.jsonl"
    write_jsonl(path, [obs(), obs(ticker="AAPL")], invalid=True)

    rows, invalid = load_observations([path])

    assert len(rows) == 2
    assert invalid == 1
    assert rows[0]["_source_file"] == str(path)


def test_summarize_observations_reports_safety_and_metrics():
    rows = [
        obs(ticker="NET", breakout_pct=0.6, volume_ratio=3.2, score=80),
        obs(ticker="AAPL", breakout_pct=1.0, volume_ratio=2.0, score=75),
    ]

    summary = summarize_observations(rows)

    assert summary["n_observations"] == 2
    assert summary["watch_only_count"] == 2
    assert summary["monitoring_only_count"] == 2
    assert summary["opening_range_scanner_count"] == 2
    assert summary["non_compliant_count"] == 0
    assert summary["tickers"] == {"AAPL": 1, "NET": 1}
    assert summary["by_date"] == {"2026-05-06": 2}
    assert summary["avg_breakout_pct"] == 0.8
    assert summary["avg_volume_ratio"] == 2.6
    assert summary["paper_trading_enabled"] is False
    assert summary["ready_for_paper_trading"] is False


def test_summarize_flags_non_compliant_rows():
    rows = [
        obs(),
        obs(ticker="BAD", watch_only=False, mode="paper", scanner="opening_range"),
    ]

    summary = summarize_observations(rows)

    assert summary["non_compliant_count"] == 1
    assert summary["non_compliant_examples"][0]["ticker"] == "BAD"


def test_format_report_mentions_monitoring_only_and_paper_disabled():
    summary = summarize_observations([obs()])

    report = format_report(summary)

    assert "OPENING-RANGE OBSERVATION REVIEW" in report
    assert "Monitoring-only" in report
    assert "Paper trading: DISABLED" in report
    assert "not buy instructions" in report.lower()


def test_cli_json_outputs_summary(tmp_path):
    path = tmp_path / "opening_range_observations_2026-05-06.jsonl"
    write_jsonl(path, [obs(ticker="NET")])

    out = subprocess.check_output(
        [
            "python",
            "scripts/review_opening_range_observations.py",
            "--pattern",
            str(tmp_path / "opening_range_observations_*.jsonl"),
            "--json",
        ],
        text=True,
    )

    data = json.loads(out)
    assert data["n_observations"] == 1
    assert data["tickers"] == {"NET": 1}
    assert data["paper_trading_enabled"] is False


def test_cli_human_report_handles_no_files(tmp_path):
    out = subprocess.check_output(
        [
            "python",
            "scripts/review_opening_range_observations.py",
            "--pattern",
            str(tmp_path / "missing_*.jsonl"),
        ],
        text=True,
    )

    assert "Observations:       0" in out
    assert "Paper trading: DISABLED" in out
