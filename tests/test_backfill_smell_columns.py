"""Bug #17 follow-up: migrate picks_log schema to include smell persistence fields."""

import csv
from pathlib import Path

import scripts.backfill_smell_columns as bsc


def _write_csv(path: Path, rows: list[dict], fields=None):
    fields = fields or ["pick_date", "ticker", "evaluation_status"]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def _read_csv(path: Path):
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def test_migrate_adds_missing_smell_columns(tmp_path):
    path = tmp_path / "picks_log.csv"
    _write_csv(path, [
        {"pick_date": "2026-05-04", "ticker": "A", "evaluation_status": "sl_hit"},
    ])

    changed = bsc.migrate(path=path, apply=True)

    fields, rows = _read_csv(path)
    assert changed == 3
    assert fields[-3:] == bsc.SMELL_FIELDS
    assert rows[0]["smell_codes"] == ""
    assert rows[0]["smell_severities"] == ""
    assert rows[0]["smell_messages"] == ""


def test_migrate_preserves_existing_smell_values(tmp_path):
    path = tmp_path / "picks_log.csv"
    fields = ["pick_date", "ticker", "evaluation_status", "smell_codes", "smell_severities"]
    _write_csv(path, [
        {
            "pick_date": "2026-05-04",
            "ticker": "A",
            "evaluation_status": "sl_hit",
            "smell_codes": "earnings_soon",
            "smell_severities": "MED",
        },
    ], fields=fields)

    changed = bsc.migrate(path=path, apply=True)

    fields_after, rows = _read_csv(path)
    assert changed == 1
    assert fields_after[-1] == "smell_messages"
    assert rows[0]["smell_codes"] == "earnings_soon"
    assert rows[0]["smell_severities"] == "MED"
    assert rows[0]["smell_messages"] == ""


def test_migrate_dry_run_does_not_write(tmp_path):
    path = tmp_path / "picks_log.csv"
    _write_csv(path, [
        {"pick_date": "2026-05-04", "ticker": "A", "evaluation_status": "sl_hit"},
    ])

    changed = bsc.migrate(path=path, apply=False)

    fields, rows = _read_csv(path)
    assert changed == 3
    assert "smell_codes" not in fields
    assert rows[0]["ticker"] == "A"


def test_migrate_idempotent_when_columns_exist(tmp_path):
    path = tmp_path / "picks_log.csv"
    fields = ["pick_date", "ticker", "evaluation_status"] + bsc.SMELL_FIELDS
    _write_csv(path, [
        {
            "pick_date": "2026-05-04",
            "ticker": "A",
            "evaluation_status": "sl_hit",
            "smell_codes": "",
            "smell_severities": "",
            "smell_messages": "",
        },
    ], fields=fields)

    changed = bsc.migrate(path=path, apply=True)

    fields_after, rows = _read_csv(path)
    assert changed == 0
    assert fields_after == fields
    assert rows[0]["ticker"] == "A"
