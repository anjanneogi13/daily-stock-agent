"""Bug #6: tracked picks_log should not store ticker as fake company name."""

import csv


def test_tracked_picks_log_does_not_store_ticker_as_company_name():
    with open("data/picks_log.csv", newline="") as f:
        rows = list(csv.DictReader(f))

    offenders = []
    for row in rows:
        ticker = (row.get("ticker") or "").strip()
        company = (row.get("company") or "").strip()
        if ticker and company and ticker.upper() == company.upper():
            offenders.append((row.get("pick_date"), ticker))

    assert offenders == []
