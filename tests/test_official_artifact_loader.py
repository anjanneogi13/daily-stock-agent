import json

from src.official_artifact_loader import (
    enrich_pick_row_with_artifact,
    enrich_pick_rows_with_artifacts,
    official_pick_artifacts_for_date,
)


def artifact(ticker="AAPL"):
    return {
        "artifact": "premarket_official_pick",
        "date": "2026-05-09",
        "decision": "official_pick",
        "ticker": ticker,
        "company": "Apple Inc.",
        "contract_version": "premarket_decision_contract_v1",
        "strategy_lane": "premarket_official_daily_pick",
        "score": 0.82,
        "entry": 100.0,
        "stop_loss": 95.0,
        "take_profit": 110.0,
        "risk_reward": 2.0,
        "quantity": 10,
        "risk_dollars": 50.0,
        "selection_reason": "AAPL selected.",
        "invalidation_conditions": ["Do not enter if fresh quote is unavailable."],
        "risk_flags": ["PREMARKET_HALF_SIZE"],
        "score_components": {"composite": 0.82},
    }


def test_official_pick_artifacts_for_date_loads_by_ticker(tmp_path):
    path = tmp_path / "premarket_official_pick_2026-05-09_AAPL.json"
    path.write_text(json.dumps(artifact()), encoding="utf-8")

    result = official_pick_artifacts_for_date("2026-05-09", tmp_path)

    assert result["AAPL"]["ticker"] == "AAPL"
    assert result["AAPL"]["_artifact_path"] == str(path)


def test_enrich_pick_row_with_artifact_preserves_csv_shape():
    row = {"ticker": "AAPL", "entry": "99", "qty": "5"}

    enriched = enrich_pick_row_with_artifact(row, artifact())

    assert enriched["official_artifact_present"] is True
    assert enriched["entry"] == 100.0
    assert enriched["qty"] == 10
    assert enriched["official_selection_reason"] == "AAPL selected."
    assert enriched["official_risk_flags"] == ["PREMARKET_HALF_SIZE"]


def test_enrich_pick_rows_with_artifacts_marks_missing_artifact(tmp_path):
    rows = [{"ticker": "MSFT", "entry": "50"}]

    enriched = enrich_pick_rows_with_artifacts(rows, "2026-05-09", tmp_path)

    assert enriched[0]["official_artifact_present"] is False
    assert enriched[0]["entry"] == "50"
