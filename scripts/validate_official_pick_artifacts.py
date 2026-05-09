#!/usr/bin/env python3
"""Validate official premarket pick artifacts for a Daily Picks run.

This script is used by the daily-picks workflow after main.py completes.

Rules:
- If picks were logged for the ET date, there must be matching valid official
  pick artifacts.
- Every official pick artifact must satisfy the premarket decision contract.
- The daily summary artifact must exist and agree with the number of valid
  official pick artifacts.
- This script does not generate picks, trade, or send alerts.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.premarket_decision_contract import validate_official_pick


ET = ZoneInfo("America/New_York")


def default_et_date() -> str:
    return datetime.now(ET).strftime("%Y-%m-%d")


def _load_json(path: Path) -> tuple[dict, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {}, f"{path}: parse error: {exc}"
    if not isinstance(payload, dict):
        return {}, f"{path}: payload is not an object"
    return payload, None


def _count_csv_rows_for_date(csv_path: Path, date_str: str) -> int:
    if not csv_path.exists():
        return 0
    count = 0
    try:
        with csv_path.open(encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{date_str},"):
                    count += 1
    except Exception:
        return 0
    return count


def official_pick_artifact_paths(date_str: str, data_dir: Path) -> list[Path]:
    return sorted(data_dir.glob(f"premarket_official_pick_{date_str}_*.json"))


def official_pick_summary_path(date_str: str, data_dir: Path) -> Path:
    return data_dir / f"premarket_official_pick_summary_{date_str}.json"


def validate_artifacts(date_str: str, data_dir: Path, csv_path: Path, expected_count: int | None = None) -> list[str]:
    errors: list[str] = []

    csv_count = _count_csv_rows_for_date(csv_path, date_str)
    required_count = expected_count if expected_count is not None else csv_count

    if required_count <= 0:
        return [
            f"expected_count for {date_str} is {required_count}; use validate_daily_no_pick.py for no-pick days"
        ]

    paths = official_pick_artifact_paths(date_str, data_dir)
    if not paths:
        errors.append(f"no official pick artifacts found for {date_str}")
    if len(paths) < required_count:
        errors.append(f"only {len(paths)} official pick artifact(s) found for {required_count} logged pick(s)")
    if len(paths) > required_count:
        errors.append(f"{len(paths)} official pick artifact(s) found for {required_count} logged pick(s)")

    seen_tickers: set[str] = set()
    for path in paths:
        payload, err = _load_json(path)
        if err:
            errors.append(err)
            continue

        artifact_errors = validate_official_pick(payload)
        errors.extend(f"{path.name}: {message}" for message in artifact_errors)

        if payload.get("date") != date_str:
            errors.append(f"{path.name}: date {payload.get('date')!r} does not match {date_str!r}")

        ticker = str(payload.get("ticker") or "").strip().upper()
        if ticker in seen_tickers:
            errors.append(f"{path.name}: duplicate ticker artifact for {ticker}")
        if ticker:
            seen_tickers.add(ticker)

    summary_path = official_pick_summary_path(date_str, data_dir)
    if not summary_path.exists():
        errors.append(f"missing official pick summary artifact: {summary_path}")
    else:
        summary, err = _load_json(summary_path)
        if err:
            errors.append(err)
        else:
            official_count = summary.get("official_pick_count")
            requested_count = summary.get("requested_pick_count")
            if official_count != len(paths):
                errors.append(
                    f"{summary_path.name}: official_pick_count={official_count!r} "
                    f"does not match artifact count {len(paths)}"
                )
            if requested_count != required_count:
                errors.append(
                    f"{summary_path.name}: requested_pick_count={requested_count!r} "
                    f"does not match expected count {required_count}"
                )
            validation_errors = summary.get("validation_errors")
            if validation_errors not in ({}, None):
                errors.append(f"{summary_path.name}: validation_errors is not empty")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=default_et_date(), help="ET date to validate, YYYY-MM-DD")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--csv-path", default="data/picks_log.csv")
    parser.add_argument("--expected-count", type=int, default=None)
    args = parser.parse_args()

    errors = validate_artifacts(
        args.date,
        data_dir=Path(args.data_dir),
        csv_path=Path(args.csv_path),
        expected_count=args.expected_count,
    )

    if errors:
        print("❌ Official pick artifact validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    paths = official_pick_artifact_paths(args.date, Path(args.data_dir))
    print(f"✅ Valid official pick artifacts for {args.date}: {len(paths)}")
    for path in paths:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
