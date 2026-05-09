import json

from src.official_artifact_loader import (
    enrich_pick_row_with_artifact,
    enrich_pick_rows_with_artifacts,
    official_pick_artifacts_for_date,
    validate_official_artifacts_for_rows,
)


def artifact(ticker="AAPL"):
    return {
        "artifact": "premarket_official_pick",
        "date": "2026-05-09",
        "decision": "official_pick",
        "decision_id": f"premarket_official_daily_pick:2026-05-09:{ticker}:local:local",
        "artifact_id": f"premarket_official_pick:2026-05-09:{ticker}",
        "artifact_filename": f"premarket_official_pick_2026-05-09_{ticker}.json",
        "artifact_path": f"data/premarket_official_pick_2026-05-09_{ticker}.json",
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
    assert enriched["official_decision_id"] == "premarket_official_daily_pick:2026-05-09:AAPL:local:local"
    assert enriched["official_artifact_id"] == "premarket_official_pick:2026-05-09:AAPL"
    assert enriched["official_selection_reason"] == "AAPL selected."
    assert enriched["official_risk_flags"] == ["PREMARKET_HALF_SIZE"]


def test_enrich_pick_rows_with_artifacts_marks_missing_artifact(tmp_path):
    rows = [{"ticker": "MSFT", "entry": "50"}]

    enriched = enrich_pick_rows_with_artifacts(rows, "2026-05-09", tmp_path)

    assert enriched[0]["official_artifact_present"] is False
    assert enriched[0]["entry"] == "50"


def test_validate_official_artifacts_for_rows_blocks_missing_artifact(tmp_path):
    rows = [{"ticker": "AAPL"}]

    errors = validate_official_artifacts_for_rows(rows, "2026-05-09", tmp_path)

    assert errors == ["no official pick artifacts found for 2026-05-09"]


def test_validate_official_artifacts_for_rows_passes_valid_artifact(tmp_path):
    path = tmp_path / "premarket_official_pick_2026-05-09_AAPL.json"
    payload = artifact()
    payload.update({
        "strategy_version": "premarket_official_v1",
        "scoring_version": "legacy_composite_v1",
        "config_version": "config.yaml",
        "selection_time_et": "2026-05-09T08:30:00-04:00",
        "workflow_run_id": "local",
        "commit_sha": "local",
        "data_readiness_status": "ready",
        "provider_status": "healthy",
        "market_session_status": "premarket",
        "regime": "bullish",
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    })
    path.write_text(json.dumps(payload), encoding="utf-8")

    errors = validate_official_artifacts_for_rows([{"ticker": "AAPL"}], "2026-05-09", tmp_path)

    assert errors == []
