import csv
import json
import subprocess
import sys
from pathlib import Path


def write_csv(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "pick_date",
                "ticker",
                "company",
                "trade_type",
                "score",
                "entry",
                "stop_loss",
                "take_profit",
                "risk_reward",
                "qty",
                "regime",
                "cape",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "pick_date": "2026-05-09",
            "ticker": "AAPL",
            "company": "Apple Inc.",
            "trade_type": "swing",
            "score": "0.7",
            "entry": "99",
            "stop_loss": "94",
            "take_profit": "109",
            "risk_reward": "2",
            "qty": "5",
            "regime": "bullish",
            "cape": "30",
        })


def write_artifact(data_dir: Path):
    payload = {
        "artifact": "premarket_official_pick",
        "date": "2026-05-09",
        "decision": "official_pick",
        "ticker": "AAPL",
        "company": "Apple Inc.",
        "contract_version": "premarket_decision_contract_v1",
        "strategy_lane": "premarket_official_daily_pick",
        "score": 0.82,
        "entry": 100,
        "stop_loss": 95,
        "take_profit": 112,
        "risk_reward": 2.4,
        "quantity": 10,
        "risk_dollars": 50,
        "selection_reason": "AAPL selected from official artifact.",
        "invalidation_conditions": ["Do not enter if fresh quote is unavailable."],
        "risk_flags": ["PREMARKET_SAFE"],
        "score_components": {"composite": 0.82},
    }
    (data_dir / "premarket_official_pick_2026-05-09_AAPL.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    summary = {
        "artifact": "premarket_official_pick_summary",
        "date": "2026-05-09",
        "contract_version": "premarket_decision_contract_v1",
        "official_pick_count": 1,
    }
    (data_dir / "premarket_official_pick_summary_2026-05-09.json").write_text(
        json.dumps(summary),
        encoding="utf-8",
    )


def test_format_picks_email_uses_official_artifact(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_csv(tmp_path / "data/picks_log.csv")
    write_artifact(tmp_path / "data")

    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/format_picks_email.py")],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "Official artifacts: `1`" in result.stdout
    assert "✅ artifact" in result.stdout
    assert "AAPL selected from official artifact." in result.stdout


def test_send_layman_daily_uses_official_artifact(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PICK_DATE", "2026-05-09")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_GROUP_CHAT_ID", raising=False)
    write_csv(tmp_path / "data/picks_log.csv")
    write_artifact(tmp_path / "data")

    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/send_layman_daily.py")],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "validated official decision artifacts" in result.stdout
    assert "Official reason:* AAPL selected from official artifact." in result.stdout
    assert "Official risk flags:* PREMARKET_SAFE" in result.stdout
