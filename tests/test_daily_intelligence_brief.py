import json
from pathlib import Path

from scripts.build_daily_intelligence_brief import (
    build_daily_intelligence_brief,
    classify_daily_operating_status,
    format_markdown,
    write_outputs,
)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def test_daily_brief_classifies_incomplete_pipeline(tmp_path):
    date = "2026-05-09"
    write_json(tmp_path / f"artifact_completeness_{date}.json", {
        "completeness_status": "missing_critical_artifacts",
        "summary": {
            "missing_critical": ["daily_run_status", "candidate_rejections"],
            "warnings": ["late_daily_ideas"],
        },
    })
    write_json(tmp_path / f"data_readiness_{date}.json", {
        "official_pick_count": 0,
        "official_pick_tickers": [],
        "official_pick_readiness_status": "not_ready_pipeline_incomplete",
        "no_pick_classification": "pipeline_incomplete",
        "data_provider_status": "no_provider_failure_evidence_in_available_artifacts",
        "readiness_warnings": ["candidate_diagnostics_missing"],
    })
    write_json(tmp_path / f"candidate_lifecycle_{date}.json", {
        "summary": {
            "candidate_count": 2,
            "state_counts": {"diagnostics_unavailable": 2},
        },
        "candidates": [
            {"ticker": "AAPL", "lifecycle_state": "diagnostics_unavailable", "themes": ["ai"], "reason": "missing"},
            {"ticker": "NVDA", "lifecycle_state": "diagnostics_unavailable", "themes": ["ai"], "reason": "missing"},
        ],
    })
    write_json(tmp_path / f"theme_discovery_{date}.json", {
        "theme_count": 1,
        "themes": [
            {"theme": "ai", "theme_id": "ai", "lifecycle_state": "emerging_theme", "theme_score": 100, "breadth": 2, "tickers": ["AAPL", "NVDA"], "risk_flags": []}
        ],
    })
    write_json(tmp_path / f"theme_pick_bridge_{date}.json", {
        "summary": {"themes_analyzed": 1, "gap_reason_counts": {"missing_from_official_and_watch_only": 1}},
        "themes": [
            {"theme": "ai", "lifecycle_state": "emerging_theme", "leaders": ["AAPL", "NVDA"], "official_pick_match_count": 0, "rejected_match_count": 0, "hard_blocked_match_count": 0, "watch_only_match_count": 0, "likely_gap_reasons": ["missing_from_official_and_watch_only"]}
        ],
    })

    report = build_daily_intelligence_brief(date_str=date, data_dir=tmp_path)

    assert report["daily_operating_status"] == "incomplete_pipeline"
    assert report["official_pick_status"]["no_pick_classification"] == "pipeline_incomplete"
    assert report["candidate_lifecycle"]["diagnostics_unavailable_count"] == 2
    assert report["theme_discovery"]["top_themes"][0]["theme"] == "ai"
    assert report["observe_only"] is True
    assert report["production_scoring_effect"] is False
    assert any("Restore missing critical daily artifacts" in p for p in report["tomorrow_observe_only_monitoring_priorities"])


def test_daily_brief_classifies_data_failed_or_degraded(tmp_path):
    date = "2026-05-08"
    write_json(tmp_path / f"artifact_completeness_{date}.json", {
        "completeness_status": "missing_or_empty_noncritical_artifacts",
        "summary": {"missing_critical": [], "warnings": ["theme_discovery"]},
    })
    write_json(tmp_path / f"data_readiness_{date}.json", {
        "official_pick_count": 0,
        "official_pick_tickers": [],
        "official_pick_readiness_status": "not_ready_data_provider_failure",
        "no_pick_classification": "data_provider_failure",
        "data_provider_status": "provider_or_market_data_failure_evidence_detected",
        "readiness_warnings": ["provider_or_market_data_failure_evidence_detected"],
    })
    write_json(tmp_path / f"candidate_lifecycle_{date}.json", {
        "summary": {"candidate_count": 1, "state_counts": {"watch_only": 1}},
        "candidates": [
            {"ticker": "TSLA", "lifecycle_state": "watch_only", "themes": [], "reason": "opening range"}
        ],
    })
    write_jsonl(tmp_path / f"opening_range_observations_{date}.jsonl", [
        {"ticker": "TSLA", "reason": "opening range", "opening_range_quality_status": "data_insufficient_no_forward_bars"}
    ])
    write_json(tmp_path / f"daily_picks_no_pick_report_{date}.json", {
        "mode": "monitoring_only",
        "next_action": "Use watch-only fallback only; do not fabricate official picks.",
        "pipeline": {"final_pick_count": 0},
        "market_data_health": {
            "providers": {"yfinance": {"attempts": 10, "successes": 2, "errors": 8, "rate_limited": 8}},
            "run": {"universe_count": 10},
        },
    })

    report = build_daily_intelligence_brief(date_str=date, data_dir=tmp_path)

    assert report["daily_operating_status"] == "data_failed_or_degraded"
    assert report["watch_only"]["total_watch_only_rows"] == 1
    assert report["no_pick_report"]["available"] is True
    assert report["no_pick_report"]["provider_summary"]["yfinance"]["rate_limited"] == 8
    assert any("provider" in p.lower() for p in report["tomorrow_observe_only_monitoring_priorities"])


def test_classify_daily_operating_status_priority_order():
    assert classify_daily_operating_status(
        completeness_status="missing_critical_artifacts",
        no_pick_classification="data_provider_failure",
        official_pick_count=0,
    ) == "incomplete_pipeline"

    assert classify_daily_operating_status(
        completeness_status="complete",
        no_pick_classification="data_provider_failure",
        official_pick_count=0,
    ) == "data_failed_or_degraded"

    assert classify_daily_operating_status(
        completeness_status="complete",
        no_pick_classification="mixed_or_uncertain",
        official_pick_count=1,
    ) == "productive_with_official_picks"

    assert classify_daily_operating_status(
        completeness_status="complete",
        no_pick_classification="strategy_driven_no_qualified_candidates",
        official_pick_count=0,
    ) == "productive_no_official_picks"


def test_daily_brief_writes_outputs(tmp_path):
    date = "2026-05-09"
    write_json(tmp_path / f"artifact_completeness_{date}.json", {
        "completeness_status": "missing_critical_artifacts",
        "summary": {"missing_critical": ["daily_run_status"], "warnings": []},
    })
    write_json(tmp_path / f"data_readiness_{date}.json", {
        "official_pick_count": 0,
        "official_pick_tickers": [],
        "official_pick_readiness_status": "not_ready_pipeline_incomplete",
        "no_pick_classification": "pipeline_incomplete",
        "data_provider_status": "",
        "readiness_warnings": [],
    })
    write_json(tmp_path / f"candidate_lifecycle_{date}.json", {
        "summary": {"candidate_count": 0, "state_counts": {}},
        "candidates": [],
    })

    report = build_daily_intelligence_brief(date_str=date, data_dir=tmp_path)
    json_path, md_path = write_outputs(report, data_dir=tmp_path)

    assert json_path.name == "daily_intelligence_brief_2026-05-09.json"
    assert md_path.name == "daily_intelligence_brief_2026-05-09.md"

    saved = json.loads(json_path.read_text())
    assert saved["observe_only"] is True
    assert saved["buy_instructions_enabled"] is False

    md = md_path.read_text()
    assert "Daily Intelligence Brief" in md
    assert "Tomorrow Observe-Only Monitoring Priorities" in md
    assert "No buy instructions" in md


def test_format_markdown_includes_safety_status(tmp_path):
    date = "2026-05-09"
    report = build_daily_intelligence_brief(date_str=date, data_dir=tmp_path)
    md = format_markdown(report)

    assert "Daily Intelligence Brief" in md
    assert "Scoring Safety" in md
    assert "Does not alter official scoring" in md
