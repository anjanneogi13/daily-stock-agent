#!/usr/bin/env python3
"""Validate Lane 2 post-open watch-only artifacts for a date.

Roadmap source: docs/planning/MULTI_LANE_IMPLEMENTATION_ROADMAP.md, Phase 3.

Checks, for the given date:

- exactly one Lane 2 decision artifact exists (watchlist XOR no-opportunity),
- the artifact validates against src/post_open_contract.py,
- watch-only + safety flags are intact,
- the Markdown report exists when the watchlist artifact exists.

Exit code 0 = valid, 1 = invalid/missing.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.post_open_artifacts import (
    no_opportunity_path,
    report_path,
    run_status_path,
    watchlist_path,
)
from src.post_open_contract import (
    validate_post_open_no_opportunity,
    validate_post_open_watchlist,
)


def validate_post_open_artifacts_for_date(date_str: str, data_dir: Path = Path("data")) -> dict:
    """Validate the Lane 2 decision artifacts for one date."""
    wl_path = watchlist_path(date_str, data_dir)
    md_path = report_path(date_str, data_dir)
    no_opp_path = no_opportunity_path(date_str, data_dir)
    ledger_path = run_status_path(date_str, data_dir)

    errors: list[str] = []
    decision = None

    wl_exists = wl_path.exists()
    no_opp_exists = no_opp_path.exists()

    if wl_exists and no_opp_exists:
        errors.append(
            "both watchlist and no-opportunity artifacts exist — exactly one Lane 2 "
            "decision is allowed per date"
        )
    elif not wl_exists and not no_opp_exists:
        errors.append("no Lane 2 decision artifact exists for this date")

    if wl_exists:
        decision = "watch_only_opportunities"
        try:
            payload = json.loads(wl_path.read_text())
            errors.extend(validate_post_open_watchlist(payload))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"watchlist artifact unreadable: {exc}")
        if not md_path.exists():
            errors.append("watchlist Markdown report is missing")

    if no_opp_exists:
        decision = "no_opportunity"
        try:
            payload = json.loads(no_opp_path.read_text())
            errors.extend(validate_post_open_no_opportunity(payload))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"no-opportunity artifact unreadable: {exc}")

    return {
        "date": date_str,
        "decision": decision,
        "watchlist_exists": wl_exists,
        "no_opportunity_exists": no_opp_exists,
        "run_status_ledger_exists": ledger_path.exists(),
        "valid": not errors,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date",
        default=datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d"),
        help="ET date, YYYY-MM-DD",
    )
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()

    result = validate_post_open_artifacts_for_date(args.date, Path(args.data_dir))
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["valid"]:
        print("✅ Lane 2 post-open artifacts are valid")
        return 0
    print("❌ Lane 2 post-open artifacts are invalid or missing")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
