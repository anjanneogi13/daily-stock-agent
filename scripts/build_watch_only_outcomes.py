#!/usr/bin/env python3
"""Build watch-only outcome attribution artifacts.

Monitoring-only evidence builder. This script evaluates late daily watch-only
ideas and opening-range watch-only observations without mutating official pick
performance, learning journals, paper-trade ledgers, or live-trading state.

Outputs:
- data/watch_only_outcomes_YYYY-MM-DD.jsonl
- data/watch_only_outcome_report_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from statistics import mean
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.backtest_opening_range_observations import (
    evaluate_observation_outcome,
    load_bars_for_observation,
)

DATA_DIR = Path("data")


def today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _safe_float(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def _as_dt(value):
    if isinstance(value, datetime):
        return value
    if value in (None, ""):
        return None
    try:
        text = str(value)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except Exception:
        return None


def load_jsonl(path: Path) -> tuple[list[dict], int]:
    rows: list[dict] = []
    invalid = 0
    if not path.exists():
        return rows, invalid
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
            else:
                invalid += 1
        except Exception:
            invalid += 1
    return rows, invalid


def _base_outcome(row: dict, *, source: str, observation_type: str) -> dict:
    return {
        "artifact": "watch_only_outcome",
        "mode": "monitoring_only",
        "watch_only": True,
        "official_premarket_pick": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "official_pick_stats_mutated": False,
        "ticker": str(row.get("ticker") or "UNKNOWN").upper(),
        "source": source,
        "observation_type": observation_type,
    }


def evaluate_late_daily_idea(row: dict) -> dict:
    """Evaluate a late watch-only idea from retained same-day range only.

    Late idea artifacts currently retain day high/low but not a full intraday
    bar sequence. Therefore this can determine whether TP/SL were inside the
    observed range, but cannot honestly determine which hit first when both did.
    """
    out = _base_outcome(row, source=str(row.get("source") or "late_daily_ideas"), observation_type="late_daily_watch_only")
    first_ts = row.get("generated_at_et") or row.get("date")

    entry = _safe_float(row.get("watch_buy_price") or row.get("current_price"))
    stop_loss = _safe_float(row.get("watch_stop_loss"))
    take_profit = _safe_float(row.get("watch_take_profit"))
    day_high = _safe_float(row.get("day_high"))
    day_low = _safe_float(row.get("day_low"))

    out.update({
        "first_observed_timestamp": first_ts,
        "reference_price": entry,
        "entry_observation_price": entry,
        "stop_loss_observation_level": stop_loss,
        "take_profit_observation_level": take_profit,
        "data_sufficiency_status": "range_only_no_intraday_sequence",
        "safety_flags": [
            "watch_only_evidence",
            "not_official_performance",
            "not_paper_trade",
            "range_only_no_intraday_sequence",
        ],
    })

    if entry is None or entry <= 0 or stop_loss is None or take_profit is None:
        out.update({
            "evaluated": False,
            "status": "missing_observation_levels",
            "max_favorable_excursion_pct": None,
            "max_adverse_excursion_pct": None,
            "tp_hit": False,
            "sl_hit": False,
            "which_hit_first": "unknown",
            "end_of_window_return_pct": None,
        })
        return out

    mfe = round((day_high - entry) / entry * 100, 4) if day_high is not None else None
    mae = round((day_low - entry) / entry * 100, 4) if day_low is not None else None
    tp_hit = bool(day_high is not None and day_high >= take_profit)
    sl_hit = bool(day_low is not None and day_low <= stop_loss)

    if tp_hit and sl_hit:
        which = "unknown_same_day_range_only"
        status = "tp_and_sl_inside_range_order_unknown"
    elif tp_hit:
        which = "tp"
        status = "tp_hit_range_only"
    elif sl_hit:
        which = "sl"
        status = "sl_hit_range_only"
    else:
        which = "neither"
        status = "no_level_hit_range_only"

    out.update({
        "evaluated": True,
        "status": status,
        "max_favorable_excursion_pct": mfe,
        "max_adverse_excursion_pct": mae,
        "tp_hit": tp_hit,
        "sl_hit": sl_hit,
        "which_hit_first": which,
        "end_of_window_return_pct": None,
        "end_of_window_note": "unavailable_for_late_range_only_artifact",
    })
    return out


def _time_of_day_bucket(ts: datetime | None) -> str:
    if not ts:
        return "unknown"
    try:
        local = ts.astimezone(ZoneInfo("America/New_York"))
    except Exception:
        local = ts

    minutes = local.hour * 60 + local.minute
    if minutes < 9 * 60 + 30:
        return "pre_open"
    if minutes < 10 * 60:
        return "opening_30m"
    if minutes < 11 * 60:
        return "morning_followthrough"
    if minutes < 12 * 60:
        return "late_morning"
    if minutes < 14 * 60:
        return "midday"
    if minutes < 16 * 60:
        return "afternoon"
    return "after_hours"


def evaluate_opening_range_quality(
    row: dict,
    *,
    forward_bars: list[dict],
    entry: float | None,
    stop_loss: float | None,
    take_profit: float | None,
    which_hit_first: str,
    max_hold_minutes: int,
) -> dict:
    """Evaluate watch-only opening-range breakout quality.

    This is not official performance and not paper trading. It explains whether
    the retained bar sequence is sufficient to judge breakout follow-through.
    """
    obs_ts = _as_dt(row.get("ts"))
    flags: list[str] = ["watch_only_opening_range_quality"]
    time_bucket = _time_of_day_bucket(obs_ts)

    base = {
        "opening_range_quality_status": "unknown",
        "opening_range_quality_score": None,
        "opening_range_quality_flags": flags,
        "sustained_breakout": None,
        "false_breakout": None,
        "breakout_retest_status": "unknown",
        "overextended_at_observation": None,
        "volume_confirmation_status": "unknown",
        "volume_confirmation_ratio": None,
        "relative_strength_status": "not_available_no_benchmark_series",
        "time_of_day_bucket": time_bucket,
        "quality_window_minutes": max_hold_minutes,
    }

    if not forward_bars:
        flags.append("no_forward_bars_after_observation")
        base.update({
            "opening_range_quality_status": "data_insufficient_no_forward_bars",
            "breakout_retest_status": "not_evaluable_no_forward_bars",
            "volume_confirmation_status": "not_evaluable_no_forward_bars",
        })
        return base

    or_high = _safe_float(row.get("opening_range_high"))
    or_low = _safe_float(row.get("opening_range_low"))
    or_width_pct = _safe_float(row.get("opening_range_width_pct"))
    breakout_pct = _safe_float(row.get("breakout_pct"))
    or_volume = _safe_float(row.get("opening_range_volume"))

    highs = [_safe_float(b.get("high")) for b in forward_bars]
    lows = [_safe_float(b.get("low")) for b in forward_bars]
    closes = [_safe_float(b.get("close")) for b in forward_bars]
    vols = [_safe_float(b.get("volume")) for b in forward_bars]
    highs = [x for x in highs if x is not None]
    lows = [x for x in lows if x is not None]
    closes = [x for x in closes if x is not None]
    vols = [x for x in vols if x is not None]

    overextended = False
    if breakout_pct is not None:
        overextended = breakout_pct >= 2.0
        if or_width_pct is not None and or_width_pct > 0:
            overextended = overextended or breakout_pct >= or_width_pct
    if overextended:
        flags.append("overextended_at_observation")

    retest_status = "not_available"
    false_breakout = False
    sustained_breakout = False

    if lows and or_high is not None:
        if min(lows) <= or_high:
            retest_status = "retested_or_high_or_failed_inside_range"
            false_breakout = True
            flags.append("retested_or_high_or_failed_inside_range")
        else:
            retest_status = "held_above_opening_range_high"
            sustained_breakout = True

    if which_hit_first == "tp":
        sustained_breakout = True
        false_breakout = False
        flags.append("tp_hit_before_stop")
    elif which_hit_first == "sl":
        false_breakout = True
        sustained_breakout = False
        flags.append("stop_hit_before_target")

    if closes and or_high is not None and closes[-1] > or_high and which_hit_first not in {"tp", "sl"}:
        sustained_breakout = True
        flags.append("end_of_window_above_opening_range_high")

    volume_ratio = None
    volume_status = "not_available"
    if vols and or_volume and or_volume > 0:
        # Opening range is normally six 5-minute bars; use average OR bar volume
        # as a simple v1 confirmation baseline.
        avg_or_bar_volume = or_volume / 6.0
        if avg_or_bar_volume > 0:
            volume_ratio = round(vols[0] / avg_or_bar_volume, 4)
            if volume_ratio >= 1.2:
                volume_status = "confirmed"
                flags.append("volume_confirmed")
            elif volume_ratio < 0.8:
                volume_status = "weak"
                flags.append("volume_weak")
            else:
                volume_status = "neutral"

    score = 50
    if sustained_breakout:
        score += 20
    if false_breakout:
        score -= 25
    if which_hit_first == "tp":
        score += 20
    elif which_hit_first == "sl":
        score -= 20
    if volume_status == "confirmed":
        score += 5
    elif volume_status == "weak":
        score -= 5
    if overextended:
        score -= 10
    score = max(0, min(100, score))

    if which_hit_first == "tp":
        quality_status = "sustained_breakout_tp_hit"
    elif which_hit_first == "sl":
        quality_status = "false_breakout_stop_hit"
    elif false_breakout:
        quality_status = "failed_retest_or_range_reentry"
    elif sustained_breakout:
        quality_status = "sustained_breakout_no_target_yet"
    else:
        quality_status = "inconclusive_forward_bars"

    base.update({
        "opening_range_quality_status": quality_status,
        "opening_range_quality_score": score,
        "opening_range_quality_flags": list(dict.fromkeys(flags)),
        "sustained_breakout": sustained_breakout,
        "false_breakout": false_breakout,
        "breakout_retest_status": retest_status,
        "overextended_at_observation": overextended,
        "volume_confirmation_status": volume_status,
        "volume_confirmation_ratio": volume_ratio,
    })
    return base


def evaluate_opening_range_observation(row: dict, *, data_dir: Path, max_hold_minutes: int = 240) -> dict:
    out = _base_outcome(row, source=str(row.get("source") or "opening_range_observations"), observation_type="opening_range_watch_only")
    bars_dir = data_dir / "opening_range_bars"
    bars, bar_path, invalid_bar_lines = load_bars_for_observation(row, bars_dir=bars_dir)
    raw = evaluate_observation_outcome(row, bars, max_hold_minutes=max_hold_minutes)

    entry = _safe_float(raw.get("entry") or row.get("entry_observe") or row.get("price"))
    stop_loss = _safe_float(raw.get("stop_loss") or row.get("stop_loss_observe"))
    take_profit = _safe_float(raw.get("take_profit") or row.get("take_profit_observe"))
    return_pct = _safe_float(raw.get("return_pct"))
    r_multiple = _safe_float(raw.get("r_multiple"))

    obs_ts = _as_dt(row.get("ts"))
    deadline = obs_ts + timedelta(minutes=max_hold_minutes) if obs_ts else None
    forward_bars = []
    for bar in bars:
        bar_ts = _as_dt(bar.get("ts"))
        if obs_ts and deadline and bar_ts and obs_ts < bar_ts <= deadline:
            forward_bars.append(bar)

    highs = [_safe_float(b.get("high")) for b in forward_bars]
    lows = [_safe_float(b.get("low")) for b in forward_bars]
    highs = [x for x in highs if x is not None]
    lows = [x for x in lows if x is not None]

    mfe = round((max(highs) - entry) / entry * 100, 4) if entry and highs else None
    mae = round((min(lows) - entry) / entry * 100, 4) if entry and lows else None

    status = raw.get("status")
    tp_hit = status == "tp_hit"
    sl_hit = status == "sl_hit"
    if tp_hit:
        which = "tp"
    elif sl_hit:
        which = "sl"
    elif raw.get("evaluated"):
        which = "neither"
    else:
        which = "unknown"

    quality = evaluate_opening_range_quality(
        row,
        forward_bars=forward_bars,
        entry=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
        which_hit_first=which,
        max_hold_minutes=max_hold_minutes,
    )

    out.update({
        "first_observed_timestamp": row.get("ts"),
        "reference_price": entry,
        "entry_observation_price": entry,
        "stop_loss_observation_level": stop_loss,
        "take_profit_observation_level": take_profit,
        "evaluated": bool(raw.get("evaluated")),
        "status": status,
        "max_favorable_excursion_pct": mfe,
        "max_adverse_excursion_pct": mae,
        "tp_hit": tp_hit,
        "sl_hit": sl_hit,
        "which_hit_first": which,
        "end_of_window_return_pct": return_pct,
        "r_multiple": r_multiple,
        "exit_timestamp": raw.get("exit_ts"),
        "exit_price": raw.get("exit_price"),
        "data_sufficiency_status": (
            "bar_sequence_available_no_forward_bars_after_observation"
            if bars and not forward_bars and status == "missing_bar_data"
            else "bar_sequence_available"
            if bars
            else "missing_bar_sequence"
        ),
        "bar_file": str(bar_path) if bar_path else "",
        "invalid_bar_lines": invalid_bar_lines,
        **quality,
        "safety_flags": [
            "watch_only_evidence",
            "not_official_performance",
            "not_paper_trade",
            "opening_range_bar_sequence",
        ],
    })
    return out


def build_outcomes(date_str: str, *, data_dir: Path = DATA_DIR, max_hold_minutes: int = 240) -> tuple[list[dict], dict]:
    late_path = data_dir / f"late_daily_ideas_{date_str}.jsonl"
    opening_path = data_dir / f"opening_range_observations_{date_str}.jsonl"

    late_rows, late_invalid = load_jsonl(late_path)
    opening_rows, opening_invalid = load_jsonl(opening_path)

    outcomes: list[dict] = []

    for row in late_rows:
        if row.get("watch_only") is True:
            outcomes.append(evaluate_late_daily_idea(row))

    for row in opening_rows:
        if row.get("watch_only") is True:
            outcomes.append(evaluate_opening_range_observation(row, data_dir=data_dir, max_hold_minutes=max_hold_minutes))

    status_counts = Counter(o.get("status", "unknown") for o in outcomes)
    evaluated = [o for o in outcomes if o.get("evaluated") is True]
    return_values = [_safe_float(o.get("end_of_window_return_pct")) for o in evaluated]
    return_values = [x for x in return_values if x is not None]

    summary = {
        "artifact": "watch_only_outcome_report",
        "date": date_str,
        "mode": "monitoring_only",
        "watch_only": True,
        "official_premarket_pick": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "official_pick_stats_mutated": False,
        "inputs": {
            "late_daily_ideas": str(late_path),
            "opening_range_observations": str(opening_path),
            "opening_range_bars_dir": str(data_dir / "opening_range_bars" / date_str),
        },
        "input_exists": {
            "late_daily_ideas": late_path.exists(),
            "opening_range_observations": opening_path.exists(),
            "opening_range_bars_dir": (data_dir / "opening_range_bars" / date_str).exists(),
        },
        "invalid_input_lines": {
            "late_daily_ideas": late_invalid,
            "opening_range_observations": opening_invalid,
        },
        "n_outcomes": len(outcomes),
        "n_evaluated": len(evaluated),
        "status_counts": dict(sorted(status_counts.items())),
        "avg_end_of_window_return_pct": round(mean(return_values), 4) if return_values else None,
        "outcome_files": {
            "jsonl": str(data_dir / f"watch_only_outcomes_{date_str}.jsonl"),
            "markdown": str(data_dir / f"watch_only_outcome_report_{date_str}.md"),
        },
        "safety_notes": [
            "Watch-only evidence only.",
            "Official pick statistics were not mutated.",
            "Paper trading remains disabled.",
            "Live trading remains disabled.",
        ],
    }
    return outcomes, summary


def format_markdown(summary: dict, outcomes: Iterable[dict]) -> str:
    outcomes = list(outcomes)

    def _display(value):
        return "n/a" if value is None else value

    lines = [
        "# Watch-Only Outcome Report",
        "",
        "Monitoring-only evidence. Not official picks. Not buy instructions. Not paper trading.",
        "",
        f"- Date: **{summary['date']}**",
        f"- Outcomes: **{summary['n_outcomes']}**",
        f"- Evaluated: **{summary['n_evaluated']}**",
        f"- Average end-of-window return: **{summary['avg_end_of_window_return_pct'] if summary['avg_end_of_window_return_pct'] is not None else 'n/a'}**",
        "- Official pick stats mutated: **false**",
        "- Paper trading enabled: **false**",
        "- Live trading enabled: **false**",
        "",
        "## Status Counts",
    ]

    for status, n in summary["status_counts"].items():
        lines.append(f"- {status}: **{n}**")
    if not summary["status_counts"]:
        lines.append("- None")

    lines.extend(["", "## Outcomes"])
    for o in outcomes:
        lines.append(
            f"- {o.get('ticker')} ({o.get('observation_type')}): "
            f"status=**{o.get('status')}**, "
            f"tp_hit=**{str(o.get('tp_hit')).lower()}**, "
            f"sl_hit=**{str(o.get('sl_hit')).lower()}**, "
            f"which_hit_first=**{o.get('which_hit_first')}**, "
            f"mfe=**{_display(o.get('max_favorable_excursion_pct'))}**, "
            f"mae=**{_display(o.get('max_adverse_excursion_pct'))}**, "
            f"end_return=**{_display(o.get('end_of_window_return_pct'))}**, "
            f"data=**{o.get('data_sufficiency_status')}**"
        )
        if o.get("observation_type") == "opening_range_watch_only":
            lines.append(
                f"  - OR quality=**{o.get('opening_range_quality_status')}**, "
                f"quality_score=**{_display(o.get('opening_range_quality_score'))}**, "
                f"sustained=**{str(o.get('sustained_breakout')).lower() if o.get('sustained_breakout') is not None else 'n/a'}**, "
                f"false_breakout=**{str(o.get('false_breakout')).lower() if o.get('false_breakout') is not None else 'n/a'}**, "
                f"volume=**{o.get('volume_confirmation_status')}**, "
                f"time=**{o.get('time_of_day_bucket')}**, "
                f"flags=**{', '.join(o.get('opening_range_quality_flags') or []) or 'none'}**"
            )
    if not outcomes:
        lines.append("- None")

    lines.extend([
        "",
        "## Safety",
        "",
        "- This artifact is watch-only evidence.",
        "- It must not be mixed with official pick performance.",
        "- It did not write `data/picks_log.csv`.",
        "- It did not write `data/signal_journal.jsonl`.",
        "- It did not write `data/learning_journal.jsonl`.",
        "- It did not create paper trades.",
        "- It did not enable live trading.",
        "",
    ])
    return "\n".join(lines)


def write_outputs(date_str: str, outcomes: list[dict], summary: dict, *, data_dir: Path = DATA_DIR) -> tuple[Path, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = data_dir / f"watch_only_outcomes_{date_str}.jsonl"
    md_path = data_dir / f"watch_only_outcome_report_{date_str}.md"

    jsonl_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in outcomes),
        encoding="utf-8",
    )
    md_path.write_text(format_markdown(summary, outcomes) + "\n", encoding="utf-8")
    return jsonl_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build watch-only outcome artifacts.")
    parser.add_argument("--date", default=today_utc())
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--max-hold-minutes", type=int, default=240)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir)
    outcomes, summary = build_outcomes(args.date, data_dir=data_dir, max_hold_minutes=args.max_hold_minutes)

    if args.no_write:
        print(json.dumps({"summary": summary, "outcomes": outcomes}, indent=2, sort_keys=True))
        return 0

    jsonl_path, md_path = write_outputs(args.date, outcomes, summary, data_dir=data_dir)
    print(f"[watch-only-outcomes] wrote {jsonl_path}")
    print(f"[watch-only-outcomes] wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
