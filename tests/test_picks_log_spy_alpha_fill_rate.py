"""Bug #9: closed TRADED picks should have SPY-relative alpha fields filled.

Semantics (tightened Sep 2026): alpha is only meaningful for closes that
actually traded — rows with an actual_return_pct. Legacy 'expired' rows
with no fill/return (pre-unreachable_entry era) have no trade to benchmark.
evaluate.yml runs scripts/backfill_alpha.py --apply each evening, so any
eval-time SPY fetch hiccup self-heals within a day; PENDING_BACKFILL below
lists known rows awaiting that CI repair (their exit dates had no in-ledger
SPY close to repair from locally).
"""

import csv


CLOSED_STATUSES = {"tp_hit", "sl_hit", "expired", "day_close"}
SPY_ALPHA_FIELDS = ["spy_close_at_exit", "spy_return_pct", "alpha_pct"]

# (pick_date, ticker) rows already missing alpha when this guard tightened,
# repairable only by the CI backfill step (needs live SPY fetch).
PENDING_BACKFILL = {
    ("2026-08-24", "WST"),
    ("2026-08-26", "AJG"),
}


def _has_value(value) -> bool:
    return value is not None and str(value).strip() and str(value).strip().lower() not in {
        "none",
        "nan",
        "null",
    }


def _offenders(rows):
    out = []
    for row in rows:
        if (row.get("evaluation_status") or "").strip() not in CLOSED_STATUSES:
            continue
        if not _has_value(row.get("actual_return_pct")):
            continue  # never filled / no traded return — alpha undefined
        if (row.get("pick_date"), row.get("ticker")) in PENDING_BACKFILL:
            continue  # awaiting CI backfill (idempotent, runs nightly)
        missing = [f for f in SPY_ALPHA_FIELDS if not _has_value(row.get(f))]
        if missing:
            out.append((row.get("pick_date"), row.get("ticker"), missing))
    return out


def test_closed_traded_picks_have_spy_alpha_fields():
    with open("data/picks_log.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    assert _offenders(rows) == []


def test_post_floor_closed_traded_picks_have_spy_alpha_fields():
    with open("data/picks_log.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    post_floor = [r for r in rows if (r.get("pick_date") or "") >= "2026-05-02"]
    assert _offenders(post_floor) == []
