#!/usr/bin/env python3
"""Theme Signal Validation Harness (System Reliability Repair Plan Priority 17).

Validates whether observe-only theme-discovery signals have predictive value
before any theme-aware scoring is ever considered.

Validation questions answered (with explicit sample counts):

- Does `confirmed_leadership` outperform the all-theme baseline?
- Does `crowded_momentum` reverse (negative forward evidence)?
- Does `distribution_warning` avoid losses?
- Does theme breadth relate to next-artifact theme-score change?
- Does theme score relate to forward pick-log returns?

Method (observe-only, deterministic, no network calls):

1. Load every retained `data/theme_discovery_YYYY-MM-DD.json` artifact.
2. Split artifact dates chronologically into train/test sets (first ~70% of
   dates train, remainder test). The split is always reported explicitly.
3. Join forward evidence per (date, theme):
   - theme-score / lifecycle change from the next retained artifact,
   - forward closed non-watch-only pick-log returns for the theme's tickers
     within the forward horizon.
4. Bucket by lifecycle state and answer each validation question with one of:
   `supported`, `not_supported`, or `insufficient_sample`.
5. Missing data is reported, not guessed.

Safety:

- observe-only; no production scoring effect,
- no paper trading, no live trading, no buy instructions,
- an explicit overfitting warning is always included,
- theme-aware official scoring remains disabled per ADR-002.

Outputs:

- data/theme_signal_validation_YYYY-MM-DD.json
- data/theme_signal_validation_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from datetime import date as date_cls
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.performance_source_separation import is_watch_only_row

DATA_DIR = Path("data")

CLOSED_STATUSES = {"tp_hit", "sl_hit", "expired", "closed", "day_close"}

# Honest-evidence thresholds: below these, report insufficient_sample instead
# of drawing a conclusion.
MIN_ARTIFACT_DATES = 3
MIN_BUCKET_OBSERVATIONS = 5

FORWARD_RETURN_HORIZON_DAYS = 5

OVERFITTING_WARNING = (
    "Overfitting warning: this harness evaluates a small, single-strategy, "
    "single-market sample. Apparent effects may be regime luck, survivorship, "
    "or multiple-comparison artifacts. No theme signal may influence official "
    "scoring until the effect is stable out-of-sample across regimes and is "
    "explicitly approved (see ADR-002)."
)

SAFETY_FLAGS = [
    "observe_only",
    "not_official_scoring",
    "not_paper_trade",
    "not_live_trade",
    "no_buy_instructions",
    "train_test_separated",
]

THEME_DISCOVERY_PATTERN = re.compile(r"theme_discovery_(\d{4}-\d{2}-\d{2})\.json$")


def _parse_date(value: str) -> date_cls | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def load_theme_discovery_artifacts(data_dir: Path = DATA_DIR) -> list[dict]:
    """Load retained theme discovery artifacts sorted by date ascending."""
    artifacts = []
    for path in sorted(data_dir.glob("theme_discovery_*.json")):
        match = THEME_DISCOVERY_PATTERN.search(path.name)
        if not match:
            continue
        artifact_date = _parse_date(match.group(1))
        if artifact_date is None:
            continue
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        themes = payload.get("themes")
        if not isinstance(themes, list):
            continue
        artifacts.append({
            "date": artifact_date,
            "date_str": match.group(1),
            "path": str(path),
            "themes": themes,
        })
    artifacts.sort(key=lambda a: a["date"])
    return artifacts


def load_closed_pick_rows(picks_log_path: Path = DATA_DIR / "picks_log.csv") -> list[dict]:
    """Load closed, non-watch-only pick rows with usable returns."""
    if not picks_log_path.exists():
        return []
    rows: list[dict] = []
    try:
        with picks_log_path.open() as f:
            for row in csv.DictReader(f):
                if is_watch_only_row(row):
                    continue
                status = (row.get("evaluation_status") or "").strip().lower()
                if status not in CLOSED_STATUSES:
                    continue
                pick_date = _parse_date((row.get("pick_date") or "").strip())
                ticker = (row.get("ticker") or "").strip().upper()
                try:
                    return_pct = float(row.get("actual_return_pct"))
                except (TypeError, ValueError):
                    continue
                if pick_date is None or not ticker:
                    continue
                rows.append({
                    "pick_date": pick_date,
                    "ticker": ticker,
                    "return_pct": return_pct,
                })
    except OSError:
        return []
    return rows


def chronological_train_test_split(dates: list[date_cls]) -> tuple[list[str], list[str]]:
    """Split sorted unique dates chronologically: ~70% train, remainder test.

    With fewer than 2 dates there is nothing to separate; both lists reflect
    that honestly (test set may be empty).
    """
    unique_sorted = sorted(set(dates))
    if not unique_sorted:
        return [], []
    if len(unique_sorted) == 1:
        return [unique_sorted[0].isoformat()], []
    cut = max(1, math.ceil(len(unique_sorted) * 0.7))
    if cut >= len(unique_sorted):
        cut = len(unique_sorted) - 1
    train = [d.isoformat() for d in unique_sorted[:cut]]
    test = [d.isoformat() for d in unique_sorted[cut:]]
    return train, test


def _theme_key(theme: dict) -> str:
    return str(theme.get("theme_id") or theme.get("theme") or "").strip().lower()


def build_observations(
    artifacts: list[dict],
    closed_rows: list[dict],
    *,
    horizon_days: int = FORWARD_RETURN_HORIZON_DAYS,
) -> list[dict]:
    """Build per (date, theme) observations joined with forward evidence."""
    observations: list[dict] = []
    for index, artifact in enumerate(artifacts):
        next_artifact = artifacts[index + 1] if index + 1 < len(artifacts) else None
        next_by_key = {}
        if next_artifact:
            next_by_key = { _theme_key(t): t for t in next_artifact["themes"] if isinstance(t, dict) }

        for theme in artifact["themes"]:
            if not isinstance(theme, dict):
                continue
            key = _theme_key(theme)
            if not key:
                continue
            tickers = {str(t).strip().upper() for t in (theme.get("tickers") or []) if str(t).strip()}
            horizon_end = artifact["date"] + timedelta(days=horizon_days)
            forward_returns = [
                row["return_pct"]
                for row in closed_rows
                if row["ticker"] in tickers and artifact["date"] < row["pick_date"] <= horizon_end
            ]

            next_theme = next_by_key.get(key)
            score_change = None
            next_lifecycle_state = None
            if next_theme is not None:
                try:
                    score_change = float(next_theme.get("theme_score")) - float(theme.get("theme_score"))
                except (TypeError, ValueError):
                    score_change = None
                next_lifecycle_state = next_theme.get("lifecycle_state")

            observations.append({
                "date": artifact["date_str"],
                "theme_id": key,
                "lifecycle_state": str(theme.get("lifecycle_state") or "unknown"),
                "theme_score": theme.get("theme_score"),
                "breadth": theme.get("breadth"),
                "ticker_count": len(tickers),
                "forward_pick_returns": forward_returns,
                "forward_pick_return_count": len(forward_returns),
                "avg_forward_pick_return_pct": (
                    round(sum(forward_returns) / len(forward_returns), 4) if forward_returns else None
                ),
                "next_artifact_date": next_artifact["date_str"] if next_artifact else None,
                "next_theme_score_change": round(score_change, 4) if score_change is not None else None,
                "next_lifecycle_state": next_lifecycle_state,
            })
    return observations


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


def _correlation(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x <= 0 or var_y <= 0:
        return None
    return round(cov / math.sqrt(var_x * var_y), 4)


def _bucket_stats(observations: list[dict], lifecycle_state: str) -> dict:
    bucket = [o for o in observations if o["lifecycle_state"] == lifecycle_state]
    forward_returns = [r for o in bucket for r in o["forward_pick_returns"]]
    score_changes = [
        o["next_theme_score_change"] for o in bucket if o["next_theme_score_change"] is not None
    ]
    return {
        "lifecycle_state": lifecycle_state,
        "theme_observations": len(bucket),
        "forward_pick_return_count": len(forward_returns),
        "avg_forward_pick_return_pct": _mean(forward_returns),
        "forward_pick_win_rate": (
            round(sum(1 for r in forward_returns if r > 0) / len(forward_returns), 4)
            if forward_returns
            else None
        ),
        "next_score_change_count": len(score_changes),
        "avg_next_theme_score_change": _mean(score_changes),
    }


def _question_verdict(
    *,
    sample_count: int,
    condition_met: bool | None,
    min_sample: int = MIN_BUCKET_OBSERVATIONS,
) -> str:
    if sample_count < min_sample or condition_met is None:
        return "insufficient_sample"
    return "supported" if condition_met else "not_supported"


def _answer_questions(observations: list[dict], split_label: str) -> dict:
    all_forward = [r for o in observations for r in o["forward_pick_returns"]]
    baseline = _mean(all_forward)

    confirmed = _bucket_stats(observations, "confirmed_leadership")
    crowded = _bucket_stats(observations, "crowded_momentum")
    warning = _bucket_stats(observations, "distribution_warning")

    breadth_pairs = [
        (float(o["breadth"]), float(o["next_theme_score_change"]))
        for o in observations
        if o.get("breadth") is not None and o.get("next_theme_score_change") is not None
    ]
    breadth_corr = _correlation([p[0] for p in breadth_pairs], [p[1] for p in breadth_pairs])

    score_pairs = [
        (float(o["theme_score"]), float(o["avg_forward_pick_return_pct"]))
        for o in observations
        if o.get("theme_score") is not None and o.get("avg_forward_pick_return_pct") is not None
    ]
    score_corr = _correlation([p[0] for p in score_pairs], [p[1] for p in score_pairs])

    def _outperforms(bucket: dict) -> bool | None:
        if bucket["avg_forward_pick_return_pct"] is None or baseline is None:
            return None
        return bucket["avg_forward_pick_return_pct"] > baseline

    def _reverses(bucket: dict) -> bool | None:
        if bucket["avg_forward_pick_return_pct"] is not None:
            return bucket["avg_forward_pick_return_pct"] < 0
        if bucket["avg_next_theme_score_change"] is not None:
            return bucket["avg_next_theme_score_change"] < 0
        return None

    def _avoids_losses(bucket: dict) -> bool | None:
        if bucket["avg_forward_pick_return_pct"] is None:
            return None
        return bucket["avg_forward_pick_return_pct"] >= 0

    return {
        "split": split_label,
        "theme_observation_count": len(observations),
        "all_theme_baseline_avg_forward_return_pct": baseline,
        "questions": {
            "confirmed_leadership_outperforms": {
                "verdict": _question_verdict(
                    sample_count=confirmed["forward_pick_return_count"],
                    condition_met=_outperforms(confirmed),
                ),
                "bucket": confirmed,
            },
            "crowded_momentum_reverses": {
                "verdict": _question_verdict(
                    sample_count=max(
                        crowded["forward_pick_return_count"], crowded["next_score_change_count"]
                    ),
                    condition_met=_reverses(crowded),
                ),
                "bucket": crowded,
            },
            "distribution_warning_avoids_losses": {
                "verdict": _question_verdict(
                    sample_count=warning["forward_pick_return_count"],
                    condition_met=_avoids_losses(warning),
                ),
                "bucket": warning,
            },
            "breadth_predicts_next_score_change": {
                "verdict": _question_verdict(
                    sample_count=len(breadth_pairs),
                    condition_met=(breadth_corr is not None and breadth_corr > 0)
                    if breadth_corr is not None
                    else None,
                ),
                "pair_count": len(breadth_pairs),
                "correlation": breadth_corr,
            },
            "theme_score_correlates_with_forward_returns": {
                "verdict": _question_verdict(
                    sample_count=len(score_pairs),
                    condition_met=(score_corr is not None and score_corr > 0)
                    if score_corr is not None
                    else None,
                ),
                "pair_count": len(score_pairs),
                "correlation": score_corr,
            },
        },
    }


def build_theme_signal_validation(
    *,
    date_str: str,
    data_dir: Path = DATA_DIR,
    picks_log_path: Path | None = None,
    horizon_days: int = FORWARD_RETURN_HORIZON_DAYS,
) -> dict:
    """Build the observe-only theme signal validation payload."""
    artifacts = load_theme_discovery_artifacts(data_dir)
    closed_rows = load_closed_pick_rows(picks_log_path or (data_dir / "picks_log.csv"))

    artifact_dates = [a["date"] for a in artifacts]
    train_dates, test_dates = chronological_train_test_split(artifact_dates)

    observations = build_observations(artifacts, closed_rows, horizon_days=horizon_days)
    train_obs = [o for o in observations if o["date"] in set(train_dates)]
    test_obs = [o for o in observations if o["date"] in set(test_dates)]

    enough_dates = len(set(artifact_dates)) >= MIN_ARTIFACT_DATES
    status = "evaluated" if enough_dates else "insufficient_artifact_history"

    payload = {
        "artifact": "theme_signal_validation",
        "date": date_str,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "method": {
            "version": "v0_observe_only_train_test",
            "description": (
                "Joins retained theme-discovery artifacts with forward closed "
                "non-watch-only pick-log returns and next-artifact theme-score "
                "changes. Dates are split chronologically into train/test. "
                "Buckets below minimum sample sizes are reported as "
                "insufficient_sample, never guessed."
            ),
            "min_artifact_dates": MIN_ARTIFACT_DATES,
            "min_bucket_observations": MIN_BUCKET_OBSERVATIONS,
            "forward_return_horizon_days": horizon_days,
        },
        "input_status": {
            "theme_discovery_artifacts": len(artifacts),
            "theme_discovery_dates": [a["date_str"] for a in artifacts],
            "closed_non_watch_only_pick_rows": len(closed_rows),
        },
        "validation_status": status,
        "train_test_separation": {
            "split_method": "chronological_70_30_by_artifact_date",
            "train_dates": train_dates,
            "test_dates": test_dates,
            "train_observation_count": len(train_obs),
            "test_observation_count": len(test_obs),
        },
        "train_results": _answer_questions(train_obs, "train"),
        "test_results": _answer_questions(test_obs, "test"),
        "overfitting_warning": OVERFITTING_WARNING,
        "safety_flags": SAFETY_FLAGS,
        "observe_only": True,
        "production_scoring_effect": False,
        "official_score_boost_enabled": False,
        "theme_aware_scoring_enabled": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "buy_instructions_enabled": False,
    }
    return payload


def _verdict_line(name: str, entry: dict) -> str:
    verdict = entry.get("verdict", "insufficient_sample")
    extra = ""
    if "correlation" in entry:
        extra = f" (corr={entry.get('correlation')}, pairs={entry.get('pair_count')})"
    elif "bucket" in entry:
        bucket = entry["bucket"]
        extra = (
            f" (obs={bucket['theme_observations']}, fwd_returns="
            f"{bucket['forward_pick_return_count']}, avg={bucket['avg_forward_pick_return_pct']})"
        )
    return f"- {name}: **{verdict}**{extra}"


def format_markdown(payload: dict) -> str:
    lines = [
        "# Theme Signal Validation (observe-only)",
        "",
        "Monitoring-only theme-signal validation evidence. Not buy instructions.",
        "Theme-aware official scoring remains disabled (ADR-002).",
        "",
        f"- Date: **{payload['date']}**",
        f"- Validation status: **{payload['validation_status']}**",
        f"- Theme-discovery artifacts: **{payload['input_status']['theme_discovery_artifacts']}**"
        f" ({', '.join(payload['input_status']['theme_discovery_dates']) or 'none'})",
        f"- Closed non-watch-only pick rows: **{payload['input_status']['closed_non_watch_only_pick_rows']}**",
        "",
        "## Train/test separation",
        "",
        f"- Split: `{payload['train_test_separation']['split_method']}`",
        f"- Train dates: {', '.join(payload['train_test_separation']['train_dates']) or 'none'}",
        f"- Test dates: {', '.join(payload['train_test_separation']['test_dates']) or 'none'}",
        "",
    ]
    for split_key, title in (("train_results", "Train results"), ("test_results", "Test results")):
        results = payload[split_key]
        lines.append(f"## {title}")
        lines.append("")
        lines.append(
            f"- Theme observations: {results['theme_observation_count']} | "
            f"baseline avg forward return: {results['all_theme_baseline_avg_forward_return_pct']}"
        )
        for name, entry in results["questions"].items():
            lines.append(_verdict_line(name, entry))
        lines.append("")
    lines.extend([
        "## Overfitting warning",
        "",
        payload["overfitting_warning"],
        "",
        "## Safety",
        "",
        "- Observe-only: **true**",
        "- Production scoring effect: **false**",
        "- Theme-aware scoring enabled: **false**",
        "- Paper trading enabled: **false**",
        "- Live trading enabled: **false**",
        "",
    ])
    return "\n".join(lines)


def write_theme_signal_validation(
    payload: dict,
    *,
    data_dir: Path = DATA_DIR,
) -> dict:
    data_dir.mkdir(parents=True, exist_ok=True)
    date_str = payload["date"]
    json_path = data_dir / f"theme_signal_validation_{date_str}.json"
    md_path = data_dir / f"theme_signal_validation_{date_str}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_markdown(payload), encoding="utf-8")
    return {"json_path": str(json_path), "markdown_path": str(md_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        help="Report date (YYYY-MM-DD); defaults to today UTC",
    )
    parser.add_argument("--data-dir", default="data")
    parser.add_argument(
        "--horizon-days",
        type=int,
        default=FORWARD_RETURN_HORIZON_DAYS,
        help="Forward pick-return join horizon in calendar days",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Print the JSON payload without writing artifacts",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    payload = build_theme_signal_validation(
        date_str=args.date,
        data_dir=data_dir,
        horizon_days=args.horizon_days,
    )

    if args.no_write:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    result = write_theme_signal_validation(payload, data_dir=data_dir)
    print("✅ Wrote observe-only theme signal validation artifacts")
    print(f"- validation_status: {payload['validation_status']}")
    print(f"- json_path: {result['json_path']}")
    print(f"- markdown_path: {result['markdown_path']}")
    print("- production_scoring_effect: false")
    print("- paper_trading_enabled: false")
    print("- live_trading_enabled: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
