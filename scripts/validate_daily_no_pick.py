#!/usr/bin/env python3
"""Validate a first-class official no-pick artifact for Daily Picks.

This is used by the daily-picks workflow to distinguish:

- valid official no-pick decision: success
- zero picks with missing/invalid diagnostics: failure

It does not generate picks, enable paper trading, enable live trading, or send alerts.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.premarket_decision_contract import validate_official_no_pick


ET = ZoneInfo("America/New_York")


def default_et_date() -> str:
    return datetime.now(ET).strftime("%Y-%m-%d")


def no_pick_report_path(date_str: str, data_dir: Path = Path("data")) -> Path:
    return data_dir / f"daily_picks_no_pick_report_{date_str}.json"


def load_no_pick_report(date_str: str, data_dir: Path = Path("data")) -> tuple[dict, Path]:
    path = no_pick_report_path(date_str, data_dir=data_dir)
    if not path.exists():
        return {}, path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_parse_error": str(exc)}, path
    return payload if isinstance(payload, dict) else {"_type_error": "payload is not an object"}, path


def validate_no_pick_report(payload: dict) -> list[str]:
    errors = validate_official_no_pick(payload)

    pipeline = payload.get("pipeline") if isinstance(payload.get("pipeline"), dict) else {}
    final_pick_count = int(pipeline.get("final_pick_count") or 0)
    if final_pick_count != 0:
        errors.append(f"pipeline.final_pick_count must be 0 for official no-pick, got {final_pick_count}")

    if payload.get("paper_trading_enabled") is not False:
        errors.append("paper_trading_enabled must be false")

    if payload.get("live_trading_enabled") is not False:
        errors.append("live_trading_enabled must be false")

    if payload.get("decision") != "official_no_pick":
        errors.append("decision must be official_no_pick")

    return list(dict.fromkeys(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=default_et_date())
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args(argv)

    payload, path = load_no_pick_report(args.date, data_dir=Path(args.data_dir))
    if not payload:
        print(f"[no-pick-validate] missing {path}")
        return 1

    if payload.get("_parse_error"):
        print(f"[no-pick-validate] parse error in {path}: {payload['_parse_error']}")
        return 1

    if payload.get("_type_error"):
        print(f"[no-pick-validate] type error in {path}: {payload['_type_error']}")
        return 1

    errors = validate_no_pick_report(payload)
    if errors:
        print(f"[no-pick-validate] invalid {path}")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"[no-pick-validate] valid official no-pick artifact: {path}")
    print(f"[no-pick-validate] cause={payload.get('primary_no_pick_cause')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
