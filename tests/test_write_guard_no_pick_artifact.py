import json
from pathlib import Path

from scripts.validate_daily_no_pick import validate_no_pick_report
from scripts.write_guard_no_pick_artifact import (
    build_guard_no_pick_artifact,
    write_guard_no_pick_artifact,
)


def test_build_guard_market_closed_no_pick_artifact_validates():
    payload = build_guard_no_pick_artifact(
        date_str="2026-05-09",
        cause="NO_PICK_MARKET_CLOSED",
    )

    assert payload["decision"] == "official_no_pick"
    assert payload["primary_no_pick_cause"] == "NO_PICK_MARKET_CLOSED"
    assert payload["pipeline"]["final_pick_count"] == 0
    assert payload["paper_trading_enabled"] is False
    assert payload["live_trading_enabled"] is False
    assert payload["decision_id"]
    assert payload["artifact_id"] == "daily_picks_no_pick_report:2026-05-09:NO_PICK_MARKET_CLOSED"
    assert validate_no_pick_report(payload) == []


def test_build_guard_missed_window_no_pick_artifact_validates():
    payload = build_guard_no_pick_artifact(
        date_str="2026-05-09",
        cause="NO_PICK_WINDOW_MISSED",
    )

    assert payload["decision"] == "official_no_pick"
    assert payload["primary_no_pick_cause"] == "NO_PICK_WINDOW_MISSED"
    assert payload["market_session_status"] == "official_window_missed"
    assert payload["pipeline"]["final_pick_count"] == 0
    assert validate_no_pick_report(payload) == []


def test_write_guard_no_pick_artifact_writes_json_and_markdown(tmp_path):
    result = write_guard_no_pick_artifact(
        date_str="2026-05-09",
        cause="NO_PICK_WINDOW_MISSED",
        data_dir=tmp_path,
    )

    json_path = Path(result["json_path"])
    markdown_path = Path(result["markdown_path"])

    assert json_path.exists()
    assert markdown_path.exists()

    payload = json.loads(json_path.read_text())
    assert payload["primary_no_pick_cause"] == "NO_PICK_WINDOW_MISSED"
    assert validate_no_pick_report(payload) == []
    assert "Official No-Pick Guard Decision" in markdown_path.read_text()
