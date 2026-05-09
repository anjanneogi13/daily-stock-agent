import json

from src.official_pick_artifact import (
    build_official_pick_artifact,
    official_pick_artifact_path,
    write_official_pick_artifacts,
)
from src.premarket_decision_contract import (
    DECISION_OFFICIAL_PICK,
    STRATEGY_LANE,
    validate_official_pick,
)


def pick(ticker="AAPL"):
    return {
        "ticker": ticker,
        "trade_type": "swing",
        "scores": {
            "composite": 0.82,
            "day_score": 0.5,
            "sector_tag": "TECH",
            "sector_mult": 1.0,
        },
        "plan": {
            "entry": 100.0,
            "stop_loss": 95.0,
            "take_profit": 112.0,
            "risk_reward": 2.4,
            "quantity": 10,
        },
        "info_short": {"name": "Apple Inc.", "sector": "Technology"},
        "premarket_sanity": {"action": "SAFE", "reason": "normal official premarket entry conditions"},
        "portfolio_risk": {"passed": True},
    }


def test_build_official_pick_artifact_satisfies_contract():
    payload = build_official_pick_artifact(
        pick(),
        date_str="2026-05-09",
        selection_time_et="2026-05-09T08:45:00-04:00",
        workflow_run_id="123",
        commit_sha="abc",
        regime={"regime": "bullish"},
    )

    assert payload["artifact"] == "premarket_official_pick"
    assert payload["decision"] == DECISION_OFFICIAL_PICK
    assert payload["strategy_lane"] == STRATEGY_LANE
    assert payload["ticker"] == "AAPL"
    assert payload["risk_dollars"] == 50.0
    assert payload["paper_trading_enabled"] is False
    assert payload["live_trading_enabled"] is False
    assert validate_official_pick(payload) == []


def test_official_pick_artifact_path_sanitizes_ticker(tmp_path):
    path = official_pick_artifact_path(tmp_path, "2026-05-09", "brk.b")

    assert path.name == "premarket_official_pick_2026-05-09_BRKB.json"


def test_write_official_pick_artifacts_writes_pick_and_summary(tmp_path):
    summary = write_official_pick_artifacts(
        [pick()],
        data_dir=tmp_path,
        pipeline={"final_pick_count": 1},
        candidate_diagnostics={"diagnostics_available": True},
        regime={"regime": "bullish"},
    )

    assert summary["official_pick_count"] == 1
    assert summary["validation_errors"] == {}

    artifact_path = tmp_path / summary["artifacts"][0]["path"].split("/")[-1]
    payload = json.loads(artifact_path.read_text())

    assert payload["ticker"] == "AAPL"
    assert validate_official_pick(payload) == []

    summary_files = list(tmp_path.glob("premarket_official_pick_summary_*.json"))
    assert len(summary_files) == 1


def test_write_official_pick_artifacts_records_validation_errors(tmp_path):
    bad = pick("")
    bad["ticker"] = ""

    summary = write_official_pick_artifacts([bad], data_dir=tmp_path)

    assert summary["official_pick_count"] == 0
    assert "?" in summary["validation_errors"]
