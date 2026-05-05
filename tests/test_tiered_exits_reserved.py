"""Bug #13: tiered exit fields are reserved schema, not active logic."""

import csv
from pathlib import Path


TIER_FIELDS = ["tp1", "tp2", "qty_t1", "qty_t2", "qty_t3", "tier_status"]


def _has_active_value(value) -> bool:
    return value is not None and str(value).strip() and str(value).strip().lower() not in {
        "none",
        "nan",
        "null",
        "[]",
    }


def test_existing_picks_do_not_have_active_tiered_exit_fields():
    with open("data/picks_log.csv", newline="") as f:
        rows = list(csv.DictReader(f))

    active = [
        (row.get("pick_date"), row.get("ticker"), field, row.get(field))
        for row in rows
        for field in TIER_FIELDS
        if _has_active_value(row.get(field))
    ]

    assert active == []


def test_todo_bugs_marks_tiered_exits_as_reserved_schema():
    text = Path("docs/TODO_BUGS.md").read_text()

    assert "Bug #13" in text
    assert "Tiered exits" in text
    assert "FIXED" in text
    assert "reserved schema" in text
    assert "Revisit only if/when scale-out execution is implemented" in text


def test_next_likely_fixes_no_longer_lists_tiered_exit_decision():
    text = Path("docs/TODO_BUGS.md").read_text()
    next_section = text.split("## Next likely fixes", 1)[1]

    assert "Bug #13" not in next_section
    assert "decide tiered TP fate" not in next_section


def test_legacy_telegram_only_displays_tiers_when_populated():
    text = Path("scripts/send_telegram.py").read_text()

    assert "3-tier scale-out display" in text
    assert "if tp1 > 0 and tp2 > 0 and (qt1 + qt2 + qt3) > 0 and entry > 0:" in text
