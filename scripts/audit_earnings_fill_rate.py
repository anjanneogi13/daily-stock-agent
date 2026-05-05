"""Audit days_to_earnings fill-rate.

Bug #11 (2026-05-05)

Earnings proximity is important for risk filtering and scoring, but historical
picks showed sparse days_to_earnings coverage. This audit measures the problem
before changing scoring behavior.

Usage:
  python scripts/audit_earnings_fill_rate.py
  python scripts/audit_earnings_fill_rate.py --json
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PICKS_LOG = ROOT / "data" / "picks_log.csv"
DATA_QUALITY_FLOOR = "2026-05-02"
DEFAULT_WARNING_THRESHOLD = 0.80


def has_days_to_earnings(row: dict) -> bool:
    """Return True when days_to_earnings is present and numeric.

    0 is valid because earnings can be today. Blank/None/"None"/invalid values
    are treated as missing.
    """
    value = row.get("days_to_earnings")
    if value in (None, "", "None"):
        return False
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _norm_trade_type(row: dict) -> str:
    value = (row.get("trade_type") or "").strip().lower()
    return value or "unknown"


def _rate(filled: int, total: int):
    return round(filled / total, 4) if total else None


def load_rows(path: Path = PICKS_LOG) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def audit_rows(
    rows: list[dict],
    floor: str = DATA_QUALITY_FLOOR,
    warning_threshold: float = DEFAULT_WARNING_THRESHOLD,
) -> dict:
    post_floor = [
        r for r in rows
        if (r.get("pick_date") or "") >= floor
    ]

    filled = [r for r in post_floor if has_days_to_earnings(r)]
    missing = [r for r in post_floor if not has_days_to_earnings(r)]
    fill_rate = _rate(len(filled), len(post_floor))

    grouped = defaultdict(lambda: {"rows": 0, "filled": 0, "missing": 0})
    for r in post_floor:
        key = _norm_trade_type(r)
        grouped[key]["rows"] += 1
        if has_days_to_earnings(r):
            grouped[key]["filled"] += 1
        else:
            grouped[key]["missing"] += 1

    by_trade_type = {}
    for key in sorted(grouped):
        item = grouped[key]
        by_trade_type[key] = {
            **item,
            "fill_rate": _rate(item["filled"], item["rows"]),
        }

    missing_tickers = sorted({
        (r.get("ticker") or "").strip()
        for r in missing
        if (r.get("ticker") or "").strip()
    })

    warning = fill_rate is not None and fill_rate < warning_threshold

    return {
        "floor": floor,
        "warning_threshold": warning_threshold,
        "total_rows": len(rows),
        "post_floor_rows": len(post_floor),
        "filled_rows": len(filled),
        "missing_rows": len(missing),
        "fill_rate": fill_rate,
        "warning": warning,
        "missing_tickers": missing_tickers,
        "by_trade_type": by_trade_type,
    }


def format_report(result: dict) -> str:
    fill_rate = result["fill_rate"]
    fill_text = "n/a" if fill_rate is None else f"{fill_rate:.1%}"

    lines = []
    lines.append("═" * 72)
    lines.append("📅 EARNINGS FILL-RATE AUDIT")
    lines.append(f"   Data floor: {result['floor']}")
    lines.append("═" * 72)
    lines.append("")
    lines.append(f"Rows total:        {result['total_rows']}")
    lines.append(f"Rows post-floor:   {result['post_floor_rows']}")
    lines.append(f"Filled rows:       {result['filled_rows']}")
    lines.append(f"Missing rows:      {result['missing_rows']}")
    lines.append(f"Fill rate:         {fill_text}")
    lines.append(f"Warning threshold: {result['warning_threshold']:.0%}")

    if result["warning"]:
        lines.append("Status:            🟡 WARNING — earnings coverage below threshold")
    else:
        lines.append("Status:            ✅ OK")

    lines.append("")
    lines.append("By trade type:")
    for trade_type, item in result["by_trade_type"].items():
        rate = item["fill_rate"]
        rate_text = "n/a" if rate is None else f"{rate:.1%}"
        lines.append(
            f"  - {trade_type:8s} rows={item['rows']} "
            f"filled={item['filled']} missing={item['missing']} "
            f"fill_rate={rate_text}"
        )

    if result["missing_tickers"]:
        sample = ", ".join(result["missing_tickers"][:20])
        suffix = "" if len(result["missing_tickers"]) <= 20 else f" ... +{len(result['missing_tickers']) - 20} more"
        lines.append("")
        lines.append(f"Missing tickers: {sample}{suffix}")

    lines.append("")
    lines.append("Next if warning persists: add provider error logging, retry, or fallback calendar source.")
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
