"""Tests for Daily Picks no-pick diagnostics and rejection reporting."""
import json
from pathlib import Path


def test_no_pick_report_function_supports_diagnostics_and_cause_classification():
    text = Path("main.py").read_text()

    assert "def _classify_no_pick_cause(" in text
    assert "primary_no_pick_cause" in text
    assert "secondary_causes" in text
    assert "human_readable_summary" in text
    assert "daily_picks_candidate_rejections_" in text
    assert "hard_blocked_candidates" in text
    assert "_write_daily_picks_no_pick_report(reason, pipeline, diagnostics)" in text


def test_no_pick_cause_classifier_all_finalists_hard_blocked():
    import main

    primary, secondary, summary = main._classify_no_pick_cause(
        {
            "fetched_count": 100,
            "scored_count": 50,
            "filtered_count": 10,
            "pre_hard_block_pick_count": 2,
            "hard_blocked_count": 2,
            "final_pick_count": 0,
        },
        {
            "providers": {
                "yfinance": {
                    "attempts": 100,
                    "errors": 25,
                    "rate_limited": 25,
                }
            },
            "by_stage": {},
        },
        {},
    )

    assert primary == "NO_PICK_ALL_FINALISTS_HARD_BLOCKED"
    assert "YFINANCE_PROVIDER_DEGRADED" in secondary
    assert "hard-blocked" in summary


def test_no_pick_report_writes_candidate_rejection_artifacts(tmp_path, monkeypatch):
    import main

    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        main,
        "_classify_no_pick_cause",
        lambda pipeline, health, diagnostics=None: (
            "NO_PICK_ALL_FINALISTS_HARD_BLOCKED",
            ["YFINANCE_PROVIDER_DEGRADED"],
            "No official picks were generated because all finalists were hard-blocked.",
        ),
    )

    main._write_daily_picks_no_pick_report(
        "test reason",
        {
            "fetched_count": 100,
            "scored_count": 50,
            "filtered_count": 10,
            "pre_hard_block_pick_count": 1,
            "hard_blocked_count": 1,
            "final_pick_count": 0,
        },
        {
            "hard_blocked_candidates": [
                {
                    "ticker": "TEST",
                    "block_type": "recent_pick",
                    "reason": "recent pick",
                    "candidate": {"ticker": "TEST", "score": 0.91},
                }
            ]
        },
    )

    json_files = list(Path("data").glob("daily_picks_candidate_rejections_*.json"))
    md_files = list(Path("data").glob("daily_picks_candidate_rejections_*.md"))

    assert len(json_files) == 1
    assert len(md_files) == 1

    payload = json.loads(json_files[0].read_text())
    assert payload["mode"] == "monitoring_only"
    assert payload["paper_trading_enabled"] is False
    assert payload["live_trading_enabled"] is False
    assert payload["primary_no_pick_cause"] == "NO_PICK_ALL_FINALISTS_HARD_BLOCKED"
    assert payload["diagnostics"]["hard_blocked_candidates"][0]["ticker"] == "TEST"

    md = md_files[0].read_text()
    assert "Daily Picks Candidate Rejection Report" in md
    assert "TEST" in md
    assert "Not official picks" in md
