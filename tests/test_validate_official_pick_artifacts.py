import json

from scripts.validate_official_pick_artifacts import validate_artifacts
from src.official_pick_artifact import write_official_pick_artifacts


def pick(ticker="AAPL"):
    return {
        "ticker": ticker,
        "trade_type": "swing",
        "scores": {"composite": 0.8, "sector_tag": "TECH"},
        "plan": {
            "entry": 100,
            "stop_loss": 95,
            "take_profit": 110,
            "risk_reward": 2,
            "quantity": 10,
        },
        "info_short": {"name": "Apple Inc.", "sector": "Technology"},
        "premarket_sanity": {"action": "SAFE"},
        "portfolio_risk": {"passed": True},
    }


def write_csv(path, date="2026-05-09", tickers=("AAPL",)):
    path.write_text(
        "pick_date,ticker,score\n"
        + "\n".join(f"{date},{ticker},0.8" for ticker in tickers)
        + "\n",
        encoding="utf-8",
    )


def test_validate_artifacts_accepts_matching_pick_artifacts(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_SHA", "abc")
    csv_path = tmp_path / "picks_log.csv"
    write_csv(csv_path)

    write_official_pick_artifacts([pick()], data_dir=tmp_path)

    # Artifact writer uses today's ET date. Normalize filenames/payloads for deterministic validation.
    generated = list(tmp_path.glob("premarket_official_pick_*_AAPL.json"))[0]
    payload = json.loads(generated.read_text())
    payload["date"] = "2026-05-09"
    target = tmp_path / "premarket_official_pick_2026-05-09_AAPL.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    if generated != target:
        generated.unlink()

    summary = list(tmp_path.glob("premarket_official_pick_summary_*.json"))[0]
    summary_payload = json.loads(summary.read_text())
    target_summary = tmp_path / "premarket_official_pick_summary_2026-05-09.json"
    target_summary.write_text(json.dumps(summary_payload), encoding="utf-8")
    if summary != target_summary:
        summary.unlink()

    assert validate_artifacts("2026-05-09", tmp_path, csv_path) == []


def test_validate_artifacts_fails_when_artifact_missing(tmp_path):
    csv_path = tmp_path / "picks_log.csv"
    write_csv(csv_path)

    errors = validate_artifacts("2026-05-09", tmp_path, csv_path)

    assert any("no official pick artifacts" in error for error in errors)
    assert any("missing official pick summary" in error for error in errors)


def test_validate_artifacts_fails_on_count_mismatch(tmp_path):
    csv_path = tmp_path / "picks_log.csv"
    write_csv(csv_path, tickers=("AAPL", "MSFT"))

    write_official_pick_artifacts([pick()], data_dir=tmp_path)
    generated = list(tmp_path.glob("premarket_official_pick_*_AAPL.json"))[0]
    payload = json.loads(generated.read_text())
    payload["date"] = "2026-05-09"
    target = tmp_path / "premarket_official_pick_2026-05-09_AAPL.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    if generated != target:
        generated.unlink()

    summary = list(tmp_path.glob("premarket_official_pick_summary_*.json"))[0]
    summary_payload = json.loads(summary.read_text())
    target_summary = tmp_path / "premarket_official_pick_summary_2026-05-09.json"
    target_summary.write_text(json.dumps(summary_payload), encoding="utf-8")
    if summary != target_summary:
        summary.unlink()

    errors = validate_artifacts("2026-05-09", tmp_path, csv_path)

    assert any("logged pick" in error for error in errors)
