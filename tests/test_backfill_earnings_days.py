"""Bug #11: backfill missing days_to_earnings without touching known values."""

import csv
from pathlib import Path

import scripts.backfill_earnings_days as be


def _write_csv(path: Path, rows: list[dict]):
    fields = ["pick_date", "ticker", "days_to_earnings", "trade_type"]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def _read_csv(path: Path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def test_backfill_fills_missing_post_floor_row(tmp_path, monkeypatch):
    path = tmp_path / "picks_log.csv"
    _write_csv(path, [
        {"pick_date": "2026-05-04", "ticker": "A", "days_to_earnings": "", "trade_type": "swing"},
        {"pick_date": "2026-05-02", "ticker": "TSM", "days_to_earnings": "75", "trade_type": "swing"},
    ])

    calls = []
    def fake_days_to_earnings(ticker, as_of=None):
        calls.append((ticker, as_of))
        return 23

    monkeypatch.setattr(be, "days_to_earnings", fake_days_to_earnings)

    changed = be.backfill(path=path, apply=True)

    rows = _read_csv(path)
    assert changed == 1
    assert rows[0]["days_to_earnings"] == "23"
    assert rows[1]["days_to_earnings"] == "75"
    assert calls == [("A", "2026-05-04")]


def test_backfill_skips_unknown_earnings(tmp_path, monkeypatch):
    path = tmp_path / "picks_log.csv"
    _write_csv(path, [
        {"pick_date": "2026-05-04", "ticker": "UNKNOWN", "days_to_earnings": "", "trade_type": "swing"},
    ])

    monkeypatch.setattr(be, "days_to_earnings", lambda ticker, as_of=None: be.UNKNOWN_EARNINGS_DAYS)

    changed = be.backfill(path=path, apply=True)

    rows = _read_csv(path)
    assert changed == 0
    assert rows[0]["days_to_earnings"] == ""


def test_backfill_dry_run_does_not_write(tmp_path, monkeypatch):
    path = tmp_path / "picks_log.csv"
    _write_csv(path, [
        {"pick_date": "2026-05-04", "ticker": "A", "days_to_earnings": "", "trade_type": "swing"},
    ])

    monkeypatch.setattr(be, "days_to_earnings", lambda ticker, as_of=None: 23)

    changed = be.backfill(path=path, apply=False)

    rows = _read_csv(path)
    assert changed == 1
    assert rows[0]["days_to_earnings"] == ""
