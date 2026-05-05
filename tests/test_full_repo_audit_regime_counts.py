"""full_repo_audit must parse CSV correctly when company names contain commas."""

import csv

from scripts.full_repo_audit import format_regime_counts, recent_regime_counts


def test_recent_regime_counts_handles_quoted_company_commas(tmp_path):
    path = tmp_path / "picks_log.csv"
    fields = ["pick_date", "ticker", "company", "days_to_earnings", "regime"]
    rows = [
        {
            "pick_date": "2026-05-02",
            "ticker": "TSM",
            "company": "TSM",
            "days_to_earnings": "75",
            "regime": "bull",
        },
        {
            "pick_date": "2026-05-04",
            "ticker": "A",
            "company": "Agilent Technologies, Inc.",
            "days_to_earnings": "23",
            "regime": "bull",
        },
    ]

    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    assert recent_regime_counts(path=path, limit=10) == {"bull": 2}


def test_format_regime_counts_matches_uniq_count_style():
    assert format_regime_counts({"bull": 10}) == "    10 bull"


def test_format_regime_counts_empty():
    assert format_regime_counts({}) == "no picks_log rows"
