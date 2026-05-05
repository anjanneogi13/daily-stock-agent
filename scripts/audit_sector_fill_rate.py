"""Audit sector benchmark fill-rate.

Bug #8/#10 (2026-05-05)

Sector-relative learning depends on:
  - sector_etf and sector_close at pick time
  - sector_close_at_exit, sector_return_pct, sector_alpha_pct after close

This audit measures post-floor coverage before additional backfill/refactor work.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PICKS_LOG = ROOT / "data" / "picks_log.csv"
DATA_QUALITY_FLOOR = "2026-05-02"
DEFAULT_WARNING_THRESHOLD = 0.80

CLOSED_STATUSES = {
    "tp_hit",
    "sl_hit",
    "expired",
    "day_close",
}

ENTRY_FIELDS = (
    "sector_etf",
    "sector_close",
)

EXIT_FIELDS = (
    "sector_close_at_exit",
    "sector_return_pct",
    "sector_alpha_pct",
)


def has_value(value) -> bool:
    """Return True when a CSV value is meaningfully populated.

    Accepts numeric zero and text values like XLK. Rejects blank/None/nan-ish
    placeholders.
    """
    if value is None:
        return False
    text = str(value).strip()
    if not text:
        return False
    return text.lower() not in {"none", "nan", "null"}


def _rate(filled: int, total: int):
    return round(filled / total, 4) if total else None


def _is_closed(row: dict) -> bool:
    return (row.get("evaluation_status") or "").strip().lower() in CLOSED_STATUSES


def _ticker(row: dict) -> str:
    return (row.get("ticker") or "").strip()


def load_rows(path: Path = PICKS_LOG) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _field_stats(rows: list[dict], fields: tuple[str, ...], denominator: int) -> dict:
    out = {}
    for field in fields:
        filled = sum(1 for r in rows if has_value(r.get(field)))
        out[field] = {
            "denominator": denominator,
            "filled": filled,
            "missing": max(denominator - filled, 0),
            "fill_rate": _rate(filled, denominator),
        }
    return out


def audit_rows(
    rows: list[dict],
    floor: str = DATA_QUALITY_FLOOR,
    warning_threshold: float = DEFAULT_WARNING_THRESHOLD,
) -> dict:
    post_floor = [
        r for r in rows
        if (r.get("pick_date") or "") >= floor
    ]
    closed_post_floor = [r for r in post_floor if _is_closed(r)]

    fields = {}
    fields.update(_field_stats(post_floor, ENTRY_FIELDS, len(post_floor)))
    fields.update(_field_stats(closed_post_floor, EXIT_FIELDS, len(closed_post_floor)))

    missing_entry_tickers = sorted({
        _ticker(r)
        for r in post_floor
        if _ticker(r) and any(not has_value(r.get(field)) for field in ENTRY_FIELDS)
    })

    missing_exit_tickers = sorted({
        _ticker(r)
        for r in closed_post_floor
        if _ticker(r) and any(not has_value(r.get(field)) for field in EXIT_FIELDS)
    })

    warning_fields = [
        field
        for field, stats in fields.items()
        if stats["denominator"] > 0
        and stats["fill_rate"] is not None
        and stats["fill_rate"] < warning_threshold
    ]

    return {
        "floor": floor,
        "warning_threshold": warning_threshold,
        "total_rows": len(rows),
        "post_floor_rows": len(post_floor),
        "closed_post_floor_rows": len(closed_post_floor),
        "fields": fields,
        "warning": bool(warning_fields),
        "warning_fields": warning_fields,
        "missing_entry_tickers": missing_entry_tickers,
        "missing_exit_tickers": missing_exit_tickers,
    }


def format_report(result: dict) -> str:
    lines = []
    lines.append("═" * 72)
    lines.append("🏭 SECTOR BENCHMARK FILL-RATE AUDIT")
    lines.append(f"   Data floor: {result['floor']}")
    lines.append("═" * 72)
    lines.append("")
    lines.append(f"Rows total:             {result['total_rows']}")
    lines.append(f"Rows post-floor:        {result['post_floor_rows']}")
    lines.append(f"Closed rows post-floor: {result['closed_post_floor_rows']}")
    lines.append(f"Warning threshold:      {result['warning_threshold']:.0%}")
    lines.append("")

    lines.append("Entry fields:")
    for field in ENTRY_FIELDS:
        stats = result["fields"][field]
        rate = stats["fill_rate"]
        rate_text = "n/a" if rate is None else f"{rate:.1%}"
        lines.append(
            f"  - {field:20s} filled={stats['filled']}/{stats['denominator']} "
            f"missing={stats['missing']} fill_rate={rate_text}"
        )

    lines.append("")
    lines.append("Exit fields, closed rows only:")
    for field in EXIT_FIELDS:
        stats = result["fields"][field]
        rate = stats["fill_rate"]
        rate_text = "n/a" if rate is None else f"{rate:.1%}"
        lines.append(
            f"  - {field:20s} filled={stats['filled']}/{stats['denominator']} "
            f"missing={stats['missing']} fill_rate={rate_text}"
        )

    lines.append("")
    if result["warning"]:
        lines.append(
            "Status: 🟡 WARNING — sector benchmark coverage below threshold "
            f"for {', '.join(result['warning_fields'])}"
        )
    else:
        lines.append("Status: ✅ OK")

    if result["missing_entry_tickers"]:
        sample = ", ".join(result["missing_entry_tickers"][:20])
        suffix = "" if len(result["missing_entry_tickers"]) <= 20 else f" ... +{len(result['missing_entry_tickers']) - 20} more"
        lines.append("")
        lines.append(f"Missing entry tickers: {sample}{suffix}")

    if result["missing_exit_tickers"]:
        sample = ", ".join(result["missing_exit_tickers"][:20])
        suffix = "" if len(result["missing_exit_tickers"]) <= 20 else f" ... +{len(result['missing_exit_tickers']) - 20} more"
        lines.append("")
        lines.append(f"Missing exit tickers:  {sample}{suffix}")

    lines.append("")
    lines.append("Next if warning persists: verify pick-time sector ETF/close wiring and closed-row backfill.")
    lines.append("═" * 72)
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--floor", default=DATA_QUALITY_FLOOR, help="Minimum pick_date to include")
    parser.add_argument(
        "--warning-threshold",
        type=float,
        default=DEFAULT_WARNING_THRESHOLD,
        help="Fill-rate threshold below which the audit warns",
    )
    args = parser.parse_args(argv)

    result = audit_rows(
        load_rows(),
        floor=args.floor,
        warning_threshold=args.warning_threshold,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
