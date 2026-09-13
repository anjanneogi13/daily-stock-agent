"""Tests for the Theme Signal Validation Harness (Reliability Plan Priority 17).

Acceptance criteria from docs/planning/SYSTEM_RELIABILITY_REPAIR_PLAN.md:

- Train/test separation is included.
- Overfitting warning is explicit.
- No scoring is enabled.

House rules verified here:

- missing data is reported as insufficient, never guessed,
- watch-only pick rows are excluded from forward-return evidence,
- artifacts carry explicit observe-only safety flags.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts.validate_theme_signals import (
    MIN_ARTIFACT_DATES,
    build_theme_signal_validation,
    chronological_train_test_split,
    load_closed_pick_rows,
    load_theme_discovery_artifacts,
    write_theme_signal_validation,
)


def _write_theme_artifact(data_dir: Path, date_str: str, themes: list[dict]) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / f"theme_discovery_{date_str}.json").write_text(
        json.dumps({"artifact": "theme_discovery", "date": date_str, "themes": themes})
    )


def _write_picks_log(data_dir: Path, rows: list[dict]) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    fieldnames = ["pick_date", "ticker", "evaluation_status", "actual_return_pct", "watch_only"]
    with (data_dir / "picks_log.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _theme(theme_id: str, state: str, score: float, breadth: int, tickers: list[str]) -> dict:
    return {
        "theme_id": theme_id,
        "theme": theme_id,
        "lifecycle_state": state,
        "theme_score": score,
        "breadth": breadth,
        "tickers": tickers,
    }


@pytest.fixture
def populated_data_dir(tmp_path):
    data_dir = tmp_path / "data"
    _write_theme_artifact(data_dir, "2026-05-01", [
        _theme("ai", "confirmed_leadership", 90.0, 20, ["NVDA", "AMD"]),
        _theme("shipping", "crowded_momentum", 70.0, 5, ["ZIM"]),
        _theme("retail", "distribution_warning", 40.0, 4, ["WMT"]),
    ])
    _write_theme_artifact(data_dir, "2026-05-04", [
        _theme("ai", "confirmed_leadership", 95.0, 25, ["NVDA", "AMD"]),
        _theme("shipping", "crowded_momentum", 55.0, 4, ["ZIM"]),
        _theme("retail", "distribution_warning", 35.0, 3, ["WMT"]),
    ])
    _write_theme_artifact(data_dir, "2026-05-06", [
        _theme("ai", "confirmed_leadership", 97.0, 30, ["NVDA", "AMD"]),
        _theme("shipping", "failed_theme", 30.0, 2, ["ZIM"]),
    ])
    _write_theme_artifact(data_dir, "2026-05-08", [
        _theme("ai", "confirmed_leadership", 98.0, 32, ["NVDA", "AMD"]),
    ])
    _write_picks_log(data_dir, [
        {"pick_date": "2026-05-02", "ticker": "NVDA", "evaluation_status": "tp_hit", "actual_return_pct": "4.2", "watch_only": ""},
        {"pick_date": "2026-05-05", "ticker": "AMD", "evaluation_status": "tp_hit", "actual_return_pct": "3.1", "watch_only": ""},
        {"pick_date": "2026-05-05", "ticker": "ZIM", "evaluation_status": "sl_hit", "actual_return_pct": "-2.5", "watch_only": ""},
        # watch-only row must be excluded from forward evidence
        {"pick_date": "2026-05-05", "ticker": "NVDA", "evaluation_status": "tp_hit", "actual_return_pct": "9.9", "watch_only": "True"},
        # pending row must be excluded (not closed)
        {"pick_date": "2026-05-06", "ticker": "WMT", "evaluation_status": "pending", "actual_return_pct": "", "watch_only": ""},
    ])
    return data_dir


def test_loaders_read_artifacts_and_closed_rows(populated_data_dir):
    artifacts = load_theme_discovery_artifacts(populated_data_dir)
    assert [a["date_str"] for a in artifacts] == ["2026-05-01", "2026-05-04", "2026-05-06", "2026-05-08"]

    rows = load_closed_pick_rows(populated_data_dir / "picks_log.csv")
    tickers = sorted(r["ticker"] for r in rows)
    assert tickers == ["AMD", "NVDA", "ZIM"], "watch-only and pending rows must be excluded"


def test_train_test_split_is_chronological():
    from datetime import date

    dates = [date(2026, 5, 8), date(2026, 5, 1), date(2026, 5, 4), date(2026, 5, 6)]
    train, test = chronological_train_test_split(dates)
    assert train == ["2026-05-01", "2026-05-04", "2026-05-06"]
    assert test == ["2026-05-08"]
    assert max(train) < min(test), "train dates must strictly precede test dates"


def test_payload_includes_train_test_separation_and_overfitting_warning(populated_data_dir):
    payload = build_theme_signal_validation(date_str="2026-05-09", data_dir=populated_data_dir)

    sep = payload["train_test_separation"]
    assert sep["train_dates"] and sep["test_dates"]
    assert set(sep["train_dates"]).isdisjoint(set(sep["test_dates"]))
    assert "Overfitting warning" in payload["overfitting_warning"]
    assert payload["validation_status"] == "evaluated"


def test_payload_enables_no_scoring_and_no_trading(populated_data_dir):
    payload = build_theme_signal_validation(date_str="2026-05-09", data_dir=populated_data_dir)

    assert payload["observe_only"] is True
    assert payload["production_scoring_effect"] is False
    assert payload["official_score_boost_enabled"] is False
    assert payload["theme_aware_scoring_enabled"] is False
    assert payload["paper_trading_enabled"] is False
    assert payload["live_trading_enabled"] is False
    assert payload["buy_instructions_enabled"] is False
    assert "observe_only" in payload["safety_flags"]


def test_forward_returns_join_uses_horizon_and_theme_tickers(populated_data_dir):
    payload = build_theme_signal_validation(date_str="2026-05-09", data_dir=populated_data_dir)

    train = payload["train_results"]
    confirmed = train["questions"]["confirmed_leadership_outperforms"]["bucket"]
    # NVDA 2026-05-02 (after 05-01), AMD 2026-05-05 (after 05-01 and 05-04):
    # 3 forward joins in train window; watch-only NVDA 9.9 must NOT appear.
    assert confirmed["forward_pick_return_count"] == 3
    assert confirmed["avg_forward_pick_return_pct"] is not None
    assert confirmed["avg_forward_pick_return_pct"] < 5.0, "watch-only 9.9% row must be excluded"


def test_insufficient_history_is_reported_not_guessed(tmp_path):
    data_dir = tmp_path / "data"
    _write_theme_artifact(data_dir, "2026-05-09", [
        _theme("ai", "confirmed_leadership", 90.0, 20, ["NVDA"]),
    ])

    payload = build_theme_signal_validation(date_str="2026-05-09", data_dir=data_dir)
    assert payload["validation_status"] == "insufficient_artifact_history"
    assert payload["input_status"]["theme_discovery_artifacts"] == 1
    assert payload["input_status"]["theme_discovery_artifacts"] < MIN_ARTIFACT_DATES

    for split in ("train_results", "test_results"):
        for entry in payload[split]["questions"].values():
            assert entry["verdict"] in {"insufficient_sample", "not_supported", "supported"}
    # With one artifact there is no forward evidence at all: every question
    # must be insufficient_sample on the (empty) test split.
    for entry in payload["test_results"]["questions"].values():
        assert entry["verdict"] == "insufficient_sample"


def test_missing_everything_is_safe(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    payload = build_theme_signal_validation(date_str="2026-05-09", data_dir=data_dir)
    assert payload["validation_status"] == "insufficient_artifact_history"
    assert payload["input_status"]["theme_discovery_artifacts"] == 0
    assert payload["input_status"]["closed_non_watch_only_pick_rows"] == 0
    for entry in payload["train_results"]["questions"].values():
        assert entry["verdict"] == "insufficient_sample"


def test_write_artifacts_and_markdown(populated_data_dir):
    payload = build_theme_signal_validation(date_str="2026-05-09", data_dir=populated_data_dir)
    result = write_theme_signal_validation(payload, data_dir=populated_data_dir)

    json_path = Path(result["json_path"])
    md_path = Path(result["markdown_path"])
    assert json_path.exists() and md_path.exists()

    reloaded = json.loads(json_path.read_text())
    assert reloaded["artifact"] == "theme_signal_validation"

    md = md_path.read_text()
    assert "Train/test separation" in md
    assert "Overfitting warning" in md
    assert "Theme-aware scoring enabled: **false**" in md
    assert "Not buy instructions" in md


def test_harness_does_not_mutate_inputs(populated_data_dir):
    before_picks = (populated_data_dir / "picks_log.csv").read_text()
    before_theme = (populated_data_dir / "theme_discovery_2026-05-01.json").read_text()

    payload = build_theme_signal_validation(date_str="2026-05-09", data_dir=populated_data_dir)
    write_theme_signal_validation(payload, data_dir=populated_data_dir)

    assert (populated_data_dir / "picks_log.csv").read_text() == before_picks
    assert (populated_data_dir / "theme_discovery_2026-05-01.json").read_text() == before_theme
    assert not (populated_data_dir / "signal_journal.jsonl").exists()
    assert not (populated_data_dir / "learning_journal.jsonl").exists()
