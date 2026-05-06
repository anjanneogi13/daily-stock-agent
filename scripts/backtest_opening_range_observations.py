#!/usr/bin/env python3
"""Read-only opening-range observation outcome join/backtest.

Evidence-building only. This script never creates official picks, paper trades,
orders, or paper-trading readiness.
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.review_opening_range_observations import DEFAULT_PATTERN, load_observations


DEFAULT_BARS_DIR = ROOT / "data" / "opening_range_bars"


def _as_dt(value) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        if isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _to_float(value, default=None):
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def observation_date(row: dict) -> str:
    ts = _as_dt(row.get("ts"))
    if ts is not None:
        return ts.date().isoformat()
    raw = str(row.get("ts") or "")
    return raw[:10] if raw else "unknown"


def candidate_bar_paths(row: dict, bars_dir: Path = DEFAULT_BARS_DIR) -> list[Path]:
    ticker = str(row.get("ticker") or "").upper()
    day = observation_date(row)
    if not ticker or day == "unknown":
        return []
    return [
        bars_dir / day / f"{ticker}.jsonl",
        bars_dir / f"{ticker}_{day}.jsonl",
    ]


def load_jsonl(path: Path) -> tuple[list[dict], int]:
    rows, invalid = [], 0
    if not path.exists():
        return rows, invalid
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                invalid += 1
    return rows, invalid


def load_bars_for_observation(row: dict, bars_dir: Path = DEFAULT_BARS_DIR) -> tuple[list[dict], Path | None, int]:
    for path in candidate_bar_paths(row, bars_dir=bars_dir):
        bars, invalid = load_jsonl(path)
        if bars or path.exists():
            return bars, path, invalid
    return [], None, 0


def evaluate_observation_outcome(row: dict, bars: Iterable[dict], *, max_hold_minutes: int = 240) -> dict:
    ticker = str(row.get("ticker") or "UNKNOWN").upper()
    obs_ts = _as_dt(row.get("ts"))

    entry = _to_float(row.get("entry_observe"), _to_float(row.get("price")))
    stop_loss = _to_float(row.get("stop_loss_observe"))
    take_profit = _to_float(row.get("take_profit_observe"))

    if obs_ts is None:
        return {"ticker": ticker, "status": "missing_observation_ts", "evaluated": False, "r_multiple": None}
    if entry is None or entry <= 0 or stop_loss is None or take_profit is None:
        return {"ticker": ticker, "status": "missing_observation_levels", "evaluated": False, "r_multiple": None}

    risk = entry - stop_loss
    if risk <= 0:
        return {"ticker": ticker, "status": "invalid_risk", "evaluated": False, "r_multiple": None}

    deadline = obs_ts + timedelta(minutes=max_hold_minutes)
    parsed = []
    for bar in bars:
        ts = _as_dt(bar.get("ts"))
        if ts is not None and obs_ts < ts <= deadline:
            parsed.append((ts, bar))
    parsed.sort(key=lambda x: x[0])

    if not parsed:
        return {
            "ticker": ticker,
            "status": "missing_bar_data",
            "evaluated": False,
            "r_multiple": None,
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        }

    last_close = None
    for ts, bar in parsed:
        high = _to_float(bar.get("high"))
        low = _to_float(bar.get("low"))
        close = _to_float(bar.get("close"))
        if close is not None:
            last_close = close

        # Conservative same-bar ambiguity: stop-loss first.
        if low is not None and low <= stop_loss:
            return {
                "ticker": ticker,
                "status": "sl_hit",
                "evaluated": True,
                "exit_ts": ts.isoformat(),
                "exit_price": stop_loss,
                "r_multiple": round((stop_loss - entry) / risk, 4),
                "return_pct": round((stop_loss - entry) / entry * 100, 4),
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
            }

        if high is not None and high >= take_profit:
            return {
                "ticker": ticker,
                "status": "tp_hit",
                "evaluated": True,
                "exit_ts": ts.isoformat(),
                "exit_price": take_profit,
                "r_multiple": round((take_profit - entry) / risk, 4),
                "return_pct": round((take_profit - entry) / entry * 100, 4),
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
            }

    if last_close is None:
        return {"ticker": ticker, "status": "missing_close_data", "evaluated": False, "r_multiple": None}

    return {
        "ticker": ticker,
        "status": "timeout",
        "evaluated": True,
        "exit_ts": parsed[-1][0].isoformat(),
        "exit_price": last_close,
        "r_multiple": round((last_close - entry) / risk, 4),
        "return_pct": round((last_close - entry) / entry * 100, 4),
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
    }


def summarize_outcomes(outcomes: list[dict], invalid_bar_lines: int = 0) -> dict:
    status_counts = Counter(o.get("status", "unknown") for o in outcomes)
    evaluated = [o for o in outcomes if o.get("evaluated") is True]
    r_values = [_to_float(o.get("r_multiple")) for o in evaluated if _to_float(o.get("r_multiple")) is not None]
    wins = [r for r in r_values if r > 0]
    losses = [r for r in r_values if r <= 0]

    return {
        "artifact": "opening_range_observation_backtest",
        "mode": "monitoring_only",
        "paper_trading_enabled": False,
        "ready_for_paper_trading": False,
        "paper_trading_note": "Paper trading remains disabled. This read-only backtest builds evidence only.",
        "n_observations": len(outcomes),
        "n_evaluated": len(evaluated),
        "n_missing_or_invalid": len(outcomes) - len(evaluated),
        "invalid_bar_lines": invalid_bar_lines,
        "status_counts": dict(sorted(status_counts.items())),
        "avg_r_multiple": round(mean(r_values), 4) if r_values else None,
        "win_rate": round(len(wins) / len(r_values), 4) if r_values else None,
        "wins": len(wins),
        "losses_or_flat": len(losses),
        "sample_too_small": len(evaluated) < 30,
        "outcomes": outcomes,
    }


def format_report(summary: dict) -> str:
    lines = [
        "═" * 72,
        "🧪 OPENING-RANGE OBSERVATION BACKTEST",
        "   Read-only. Monitoring-only. Not paper trading.",
        "═" * 72,
        "",
        f"Observations:          {summary['n_observations']}",
        f"Evaluated:             {summary['n_evaluated']}",
        f"Missing/invalid:       {summary['n_missing_or_invalid']}",
        f"Invalid bar lines:     {summary['invalid_bar_lines']}",
        f"Average R:             {summary['avg_r_multiple'] if summary['avg_r_multiple'] is not None else 'n/a'}",
        f"Win rate:              {summary['win_rate'] if summary['win_rate'] is not None else 'n/a'}",
        f"Sample too small:      {summary['sample_too_small']}",
        "",
        "Status counts:",
    ]
    if summary["status_counts"]:
        for status, n in summary["status_counts"].items():
            lines.append(f"  {status}: {n}")
    else:
        lines.append("  none")
    lines += [
        "",
        "Paper trading: DISABLED",
        summary["paper_trading_note"],
        "═" * 72,
    ]
    return "\n".join(lines)


def run(observations_pattern: str = DEFAULT_PATTERN, bars_dir: Path = DEFAULT_BARS_DIR, max_hold_minutes: int = 240):
    obs_paths = [Path(p) for p in sorted(glob.glob(observations_pattern))]
    observations, invalid_obs_lines = load_observations(obs_paths)

    outcomes = []
    invalid_bar_lines = 0
    for row in observations:
        bars, bar_path, invalid = load_bars_for_observation(row, bars_dir=bars_dir)
        invalid_bar_lines += invalid
        outcome = evaluate_observation_outcome(row, bars, max_hold_minutes=max_hold_minutes)
        outcome["observation_ts"] = row.get("ts")
        outcome["bar_file"] = str(bar_path) if bar_path else None
        outcomes.append(outcome)

    summary = summarize_outcomes(outcomes, invalid_bar_lines=invalid_bar_lines + invalid_obs_lines)
    summary["observation_files"] = [str(p) for p in obs_paths]
    summary["bars_dir"] = str(bars_dir)
    return summary, obs_paths


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--observations", default=DEFAULT_PATTERN)
    parser.add_argument("--bars-dir", default=str(DEFAULT_BARS_DIR))
    parser.add_argument("--max-hold-minutes", type=int, default=240)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    summary, _ = run(
        observations_pattern=args.observations,
        bars_dir=Path(args.bars_dir),
        max_hold_minutes=args.max_hold_minutes,
    )

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(format_report(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
