#!/usr/bin/env python3
"""Review opening-range scanner observations.

Monitoring-only analysis tool.

Reads:
  data/opening_range_observations_*.jsonl

Produces:
  - observation counts
  - watch-only / monitoring-only compliance
  - ticker/date summaries
  - average breakout percentage
  - average volume ratio
  - top observations by score

This script never creates trades, paper trades, or official picks.
"""
from __future__ import annotations

import argparse
import glob
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATTERN = str(ROOT / "data" / "opening_range_observations_*.jsonl")


def _to_float(value, default=None):
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _date_from_row(row: dict) -> str:
    ts = row.get("ts") or ""
    if ts:
        try:
            return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            return str(ts)[:10]
    return "unknown"


def discover_paths(pattern: str = DEFAULT_PATTERN) -> list[Path]:
    """Return sorted observation JSONL files for a glob pattern."""
    return [Path(p) for p in sorted(glob.glob(pattern))]


def load_observations(paths: Iterable[Path] | None = None) -> tuple[list[dict], int]:
    """Load observation rows.

    Returns:
      (rows, invalid_line_count)
    """
    if paths is None:
        paths = discover_paths()

    rows: list[dict] = []
    invalid = 0

    for path in paths:
        if not Path(path).exists():
            continue
        with Path(path).open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    row["_source_file"] = str(path)
                    rows.append(row)
                except json.JSONDecodeError:
                    invalid += 1

    return rows, invalid


def summarize_observations(rows: list[dict], invalid_lines: int = 0) -> dict:
    """Summarize opening-range observations.

    This is intentionally read-only and conservative. It does not infer
    readiness for paper trading.
    """
    tickers = Counter((r.get("ticker") or "UNKNOWN").upper() for r in rows)
    by_date = Counter(_date_from_row(r) for r in rows)

    breakout_values = [
        v for v in (_to_float(r.get("breakout_pct")) for r in rows)
        if v is not None
    ]
    volume_ratios = [
        v for v in (_to_float(r.get("volume_ratio")) for r in rows)
        if v is not None
    ]

    watch_only_count = sum(1 for r in rows if r.get("watch_only") is True)
    monitoring_only_count = sum(1 for r in rows if r.get("mode") == "monitoring_only")
    scanner_count = sum(1 for r in rows if r.get("scanner") == "opening_range")

    non_compliant = [
        {
            "ticker": r.get("ticker"),
            "ts": r.get("ts"),
            "watch_only": r.get("watch_only"),
            "mode": r.get("mode"),
            "scanner": r.get("scanner"),
            "source_file": r.get("_source_file"),
        }
        for r in rows
        if not (
            r.get("watch_only") is True
            and r.get("mode") == "monitoring_only"
            and r.get("scanner") == "opening_range"
        )
    ]

    top_by_score = sorted(
        rows,
        key=lambda r: _to_float(r.get("score"), -1) or -1,
        reverse=True,
    )[:10]

    top_rows = [
        {
            "ts": r.get("ts"),
            "ticker": r.get("ticker"),
            "score": _to_float(r.get("score")),
            "price": _to_float(r.get("price")),
            "breakout_pct": _to_float(r.get("breakout_pct")),
            "volume_ratio": _to_float(r.get("volume_ratio")),
            "reason": r.get("reason", ""),
        }
        for r in top_by_score
    ]

    return {
        "artifact": "opening_range_observations",
        "mode": "monitoring_only",
        "paper_trading_enabled": False,
        "paper_trading_note": (
            "Paper trading remains disabled. Opening-range observations are "
            "watch-only evidence, not buy instructions."
        ),
        "n_observations": len(rows),
        "invalid_lines": invalid_lines,
        "watch_only_count": watch_only_count,
        "monitoring_only_count": monitoring_only_count,
        "opening_range_scanner_count": scanner_count,
        "non_compliant_count": len(non_compliant),
        "non_compliant_examples": non_compliant[:10],
        "unique_tickers": len(tickers),
        "tickers": dict(sorted(tickers.items())),
        "by_date": dict(sorted(by_date.items())),
        "avg_breakout_pct": round(mean(breakout_values), 4) if breakout_values else None,
        "avg_volume_ratio": round(mean(volume_ratios), 4) if volume_ratios else None,
        "max_breakout_pct": round(max(breakout_values), 4) if breakout_values else None,
        "max_volume_ratio": round(max(volume_ratios), 4) if volume_ratios else None,
        "top_by_score": top_rows,
        "ready_for_paper_trading": False,
    }


def format_report(summary: dict) -> str:
    """Format summary as a human-readable report."""
    lines = []
    lines.append("═" * 72)
    lines.append("📈 OPENING-RANGE OBSERVATION REVIEW")
    lines.append("   Monitoring-only. Not paper trading. Not buy instructions.")
    lines.append("═" * 72)
    lines.append("")
    lines.append(f"Observations:       {summary['n_observations']}")
    lines.append(f"Unique tickers:      {summary['unique_tickers']}")
    lines.append(f"Invalid JSON lines:  {summary['invalid_lines']}")
    lines.append("")
    lines.append("Safety compliance:")
    lines.append(f"  watch_only=true:        {summary['watch_only_count']}/{summary['n_observations']}")
    lines.append(f"  mode=monitoring_only:   {summary['monitoring_only_count']}/{summary['n_observations']}")
    lines.append(f"  scanner=opening_range:  {summary['opening_range_scanner_count']}/{summary['n_observations']}")
    lines.append(f"  non-compliant rows:     {summary['non_compliant_count']}")
    lines.append("")
    lines.append(f"Average breakout %:  {summary['avg_breakout_pct'] if summary['avg_breakout_pct'] is not None else 'n/a'}")
    lines.append(f"Average volume x:    {summary['avg_volume_ratio'] if summary['avg_volume_ratio'] is not None else 'n/a'}")
    lines.append(f"Max breakout %:      {summary['max_breakout_pct'] if summary['max_breakout_pct'] is not None else 'n/a'}")
    lines.append(f"Max volume x:        {summary['max_volume_ratio'] if summary['max_volume_ratio'] is not None else 'n/a'}")

    if summary["by_date"]:
        lines.append("")
        lines.append("By date:")
        for d, n in summary["by_date"].items():
            lines.append(f"  {d}: {n}")

    if summary["tickers"]:
        lines.append("")
        lines.append("Tickers:")
        for ticker, n in summary["tickers"].items():
            lines.append(f"  {ticker}: {n}")

    if summary["top_by_score"]:
        lines.append("")
        lines.append("Top observations by score:")
        for r in summary["top_by_score"]:
            lines.append(
                f"  {r.get('ticker')} score={r.get('score')} "
                f"breakout={r.get('breakout_pct')}% "
                f"volume={r.get('volume_ratio')}x"
            )

    lines.append("")
    lines.append("Paper trading: DISABLED")
    lines.append(summary["paper_trading_note"])
    lines.append("═" * 72)
    return "\n".join(lines)


def run(pattern: str = DEFAULT_PATTERN) -> tuple[dict, list[Path]]:
    paths = discover_paths(pattern)
    rows, invalid = load_observations(paths)
    return summarize_observations(rows, invalid_lines=invalid), paths


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pattern",
        default=DEFAULT_PATTERN,
        help="Glob pattern for opening-range observation JSONL files",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    summary, paths = run(args.pattern)
    summary["files"] = [str(p) for p in paths]

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(format_report(summary))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
