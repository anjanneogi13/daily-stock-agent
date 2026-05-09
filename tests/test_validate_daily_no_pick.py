import json
from pathlib import Path

from scripts.validate_daily_no_pick import load_no_pick_report, validate_no_pick_report
from src.premarket_decision_contract import (
    CONTRACT_VERSION,
    DECISION_OFFICIAL_NO_PICK,
    SCORING_VERSION,
    STRATEGY_LANE,
    STRATEGY_VERSION,
)


def valid_no_pick_payload():
    return {
        "artifact": "daily_picks_no_pick_report",
        "date": "2026-05-09",
        "timestamp_utc": "2026-05-09T12:45:00Z",
        "decision": DECISION_OFFICIAL_NO_PICK,
        "strategy_lane": STRATEGY_LANE,
        "contract_version": CONTRACT_VERSION,
        "strategy_version": STRATEGY_VERSION,
        "scoring_version": SCORING_VERSION,
        "config_version": "config.yaml",
        "selection_time_et": "2026-05-09T08:45:00-04:00",
        "workflow_run_id": "123",
        "commit_sha": "abc123",
        "mode": "monitoring_only",
        "official_premarket_pick": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "ready_for_paper_trading": False,
        "reason": "No official picks generated.",
        "primary_no_pick_cause": "NO_PICK_NO_SCORED_CANDIDATES",
        "secondary_causes": [],
        "human_readable_summary": "No candidates survived scoring.",
        "data_readiness_status": "ready_no_qualified_candidates",
        "provider_status": "healthy",
        "market_session_status": "premarket",
        "pipeline": {"final_pick_count": 0, "scored_count": 0},
        "diagnostics": {},
        "candidate_diagnostics": {},
        "market_data_health": {},
        "watch_only_available": False,
        "next_action": "Use watch-only fallback only; do not fabricate official picks.",
    }


def test_valid_no_pick_report_passes_validation():
    assert validate_no_pick_report(valid_no_pick_payload()) == []


def test_no_pick_report_requires_zero_final_picks():
    payload = valid_no_pick_payload()
    payload["pipeline"]["final_pick_count"] = 1

    errors = validate_no_pick_report(payload)

    assert "pipeline.final_pick_count must be 0 for official no-pick, got 1" in errors


def test_no_pick_report_rejects_live_trading_enabled():
    payload = valid_no_pick_payload()
    payload["live_trading_enabled"] = True

    errors = validate_no_pick_report(payload)

    assert "live_trading_enabled must be false" in errors


def test_load_no_pick_report_from_data_dir(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    path = data_dir / "daily_picks_no_pick_report_2026-05-09.json"
    path.write_text(json.dumps(valid_no_pick_payload()), encoding="utf-8")

    payload, loaded_path = load_no_pick_report("2026-05-09", data_dir=data_dir)

    assert loaded_path == path
    assert payload["decision"] == DECISION_OFFICIAL_NO_PICK


def test_load_no_pick_report_missing_returns_empty_payload(tmp_path):
    payload, path = load_no_pick_report("2026-05-09", data_dir=tmp_path)

    assert payload == {}
    assert path == tmp_path / "daily_picks_no_pick_report_2026-05-09.json"
