"""Add smell persistence columns to data/picks_log.csv.

Bug #17A/#17B follow-up:
  Code now persists smell verdicts for future picks, but existing picks_log.csv
  may not have the smell_codes/smell_severities/smell_messages header columns.
  Without those columns, check_enforcement_readiness reports
  smell_verdicts_not_persisted forever.

This migration only adds schema columns. It does not fabricate historical smell
verdicts; existing rows get blank smell fields.

Usage:
    python scripts/backfill_smell_columns.py
    python scripts/backfill_smell_columns.py --apply
"""
from __future__ import annotations

import argparse
import csv
import os
import tempfile
from pathlib import Path


PICKS_LOG = Path("data/picks_log.csv")
SMELL_FIELDS = ["smell_codes", "smell_severities", "smell_messages"]


def migrate(path: Path = PICKS_LOG, apply: bool = False) -> int:
    if not path.exists():
        print(f"[backfill_smell_columns] {path} not found — nothing to do.")
        return 0

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    missing = [field for field in SMELL_FIELDS if field not in fieldnames]
    print(
        f"[backfill_smell_columns] missing_fields={missing} "
        f"rows={len(rows)}"
    )

    if not missing:
        print("[backfill_smell_columns] Nothing to do. Exit.")
        return 0

    new_fieldnames = fieldnames + missing
    for row in rows:
        for field in missing:
            row.setdefault(field, "")

    if not apply:
        print(
            f"\n[backfill_smell_columns] DRY RUN — would add {len(missing)} column(s). "
            "Re-run with --apply to write."
        )
        return len(missing)

    tmp_fd, tmp_path = tempfile.mkstemp(
        prefix="picks_log.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(tmp_fd, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=new_fieldnames,
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    print(
        f"\n[backfill_smell_columns] ✅ APPLIED — added {len(missing)} column(s) "
        f"to {path}"
    )
    return len(missing)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes to data/picks_log.csv")
    args = parser.parse_args(argv)

    migrate(apply=args.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
