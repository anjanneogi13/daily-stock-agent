"""Bug #9: closed tracked picks should have SPY-relative alpha fields filled."""

import csv


CLOSED_STATUSES = {"tp_hit", "sl_hit", "expired", "day_close"}
SPY_ALPHA_FIELDS = ["spy_close_at_exit", "spy_return_pct", "alpha_pct"]


def _has_value(value) -> bool:
    return value is not None and str(value).strip() and str(value).strip().lower() not in {
        "none",
        "nan",
        "null",
    }


def test_closed_tracked_picks_have_spy_alpha_fields():
    with open("data/picks_log.csv", newline="") as f:
        rows = list(csv.DictReader(f))

    closed = [
        row for row in rows
        if (row.get("evaluation_status") or "").strip() in CLOSED_STATUSES
    ]

    offenders = []
    for row in closed:
        missing = [field for field in SPY_ALPHA_FIELDS if not _has_value(row.get(field))]
        if missing:
            offenders.append((row.get("pick_date"), row.get("ticker"), missing))

    assert offenders == []


def test_post_floor_closed_tracked_picks_have_spy_alpha_fields():
    with open("data/picks_log.csv", newline="") as f:
        rows = list(csv.DictReader(f))

    closed = [
        row for row in rows
        if (row.get("pick_date") or "") >= "2026-05-02"
        and (row.get("evaluation_status") or "").strip() in CLOSED_STATUSES
    ]

    offenders = []
    for row in closed:
        missing = [field for field in SPY_ALPHA_FIELDS if not _has_value(row.get(field))]
        if missing:
            offenders.append((row.get("pick_date"), row.get("ticker"), missing))

    assert offenders == []
