#!/usr/bin/env python3
"""Theme-to-pick bridge v0 — observe-only.

Compares discovered themes against official picks, rejection diagnostics, and
watch-only lanes. It does not affect production scoring.

Outputs:
- data/theme_pick_bridge_YYYY-MM-DD.json
- data/theme_pick_bridge_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DATA_DIR = Path("data")

SAFETY = {
    "observe_only": True,
    "official_score_boost_enabled": False,
    "production_scoring_effect": False,
    "paper_trading_enabled": False,
    "live_trading_enabled": False,
    "buy_instructions_enabled": False,
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def load_jsonl(path: Path) -> tuple[list[dict], int]:
    rows = []
    invalid = 0
    if not path.exists():
        return rows, invalid
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                rows.append(obj)
        except Exception:
            invalid += 1
    return rows, invalid


def _ticker(value) -> str:
    return str(value or "").strip().upper()


def _date_prefix(value) -> str:
    return str(value or "")[:10]


def _read_picks_log(path: Path, date_str: str) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    try:
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                if _date_prefix(row.get("pick_date")) == date_str:
                    rows.append({
                        **row,
                        "ticker": _ticker(row.get("ticker")),
                        "source": "picks_log",
                    })
    except Exception:
        return []
    return [r for r in rows if r.get("ticker")]


def _extract_candidate_ticker(row: dict) -> str:
    cand = row.get("candidate")
    if isinstance(cand, dict):
        return _ticker(cand.get("ticker"))
    return _ticker(row.get("ticker"))


def _extract_candidate_detail(row: dict) -> dict:
    cand = row.get("candidate") if isinstance(row.get("candidate"), dict) else row
    scores = cand.get("scores") if isinstance(cand.get("scores"), dict) else {}
    return {
        "ticker": _ticker(cand.get("ticker") or row.get("ticker")),
        "company": cand.get("company") or cand.get("company_name") or row.get("company") or "",
        "tag": cand.get("tag") or cand.get("sector_tag") or scores.get("sector_tag") or "",
        "score": cand.get("score") or scores.get("composite"),
        "reason": row.get("reason") or row.get("block_reason") or row.get("rejection_reason") or "",
        "hard_block": row.get("hard_block") or row.get("block") or "",
    }


def _load_rejections(path: Path) -> dict:
    raw = load_json(path, {})
    diag = raw.get("diagnostics", raw) if isinstance(raw, dict) else {}

    out = {
        "pre_hard_block_candidates": [],
        "hard_blocked_candidates": [],
        "rejected_candidates": [],
        "selected_picks": [],
    }
    for key in out:
        rows = diag.get(key) if isinstance(diag, dict) else []
        if isinstance(rows, list):
            out[key] = [_extract_candidate_detail(r) for r in rows if isinstance(r, dict)]
    return out


def _watch_rows_for_date(data_dir: Path, date_str: str) -> tuple[list[dict], dict]:
    sources = {
        "late_daily_watch_only": data_dir / f"late_daily_ideas_{date_str}.jsonl",
        "opening_range_watch_only": data_dir / f"opening_range_observations_{date_str}.jsonl",
        "intraday_momentum_watch_only": data_dir / f"intraday_momentum_observations_{date_str}.jsonl",
    }

    rows = []
    invalid = {}
    for source, path in sources.items():
        loaded, bad = load_jsonl(path)
        invalid[source] = bad
        for row in loaded:
            ticker = _ticker(row.get("ticker"))
            if not ticker:
                continue
            rows.append({
                **row,
                "ticker": ticker,
                "source": source,
            })
    return rows, invalid


def _matches(theme_tickers: set[str], rows: Iterable[dict]) -> list[dict]:
    out = []
    seen = set()
    for row in rows:
        ticker = _ticker(row.get("ticker"))
        if ticker in theme_tickers and ticker not in seen:
            seen.add(ticker)
            out.append(row)
    return out


def _simplify_rows(rows: list[dict], *, limit: int = 20) -> list[dict]:
    out = []
    for row in rows[:limit]:
        out.append({
            "ticker": _ticker(row.get("ticker")),
            "source": row.get("source") or "",
            "company": row.get("company") or row.get("company_name") or "",
            "tag": row.get("tag") or row.get("sector_tag") or "",
            "status": row.get("evaluation_status") or row.get("status") or "",
            "score": row.get("score") or row.get("display_score") or "",
            "reason": row.get("reason") or row.get("watch_only_reason") or "",
        })
    return out


def _gap_reasons(
    *,
    leader_count: int,
    official_count: int,
    rejected_count: int,
    hard_blocked_count: int,
    watch_only_count: int,
    rejection_artifact_exists: bool,
    missing_count: int,
) -> list[str]:
    reasons = []
    if official_count:
        reasons.append("official_pick_included")
    if hard_blocked_count:
        reasons.append("hard_blocked")
    if rejected_count:
        reasons.append("filtered_or_rejected")
    if watch_only_count and not official_count:
        reasons.append("watch_only_only")
    if missing_count:
        reasons.append("missing_from_official_and_watch_only")
    if missing_count and not rejection_artifact_exists:
        reasons.append("no_daily_rejection_artifact_available")
    if missing_count and rejection_artifact_exists and not (rejected_count or hard_blocked_count):
        reasons.append("missing_from_daily_universe_or_no_candidate_evidence")
    if leader_count and not reasons:
        reasons.append("no_bridge_gap_detected")
    return reasons


def build_theme_pick_bridge(
    *,
    date_str: str,
    data_dir: Path = DATA_DIR,
    theme_path: Path | None = None,
    max_themes: int = 12,
    max_leaders_per_theme: int = 25,
) -> dict:
    theme_path = theme_path or data_dir / f"theme_discovery_{date_str}.json"
    theme_report = load_json(theme_path, {})
    themes = theme_report.get("themes", []) if isinstance(theme_report, dict) else []

    official_rows = _read_picks_log(data_dir / "picks_log.csv", date_str)
    official_tickers = {_ticker(r.get("ticker")) for r in official_rows}

    rejection_path = data_dir / f"daily_picks_candidate_rejections_{date_str}.json"
    rejection_artifact_exists = rejection_path.exists()
    rejections = _load_rejections(rejection_path)

    rejected_rows = rejections["rejected_candidates"] + rejections["pre_hard_block_candidates"]
    hard_blocked_rows = rejections["hard_blocked_candidates"]
    selected_rows = rejections["selected_picks"]

    watch_rows, invalid_watch_lines = _watch_rows_for_date(data_dir, date_str)
    watch_tickers = {_ticker(r.get("ticker")) for r in watch_rows}

    bridge_themes = []
    for theme in themes[:max_themes]:
        leaders = [_ticker(t) for t in theme.get("tickers", [])[:max_leaders_per_theme] if _ticker(t)]
        leader_set = set(leaders)

        official_matches = _matches(leader_set, official_rows)
        selected_matches = _matches(leader_set, selected_rows)
        rejected_matches = _matches(leader_set, rejected_rows)
        hard_blocked_matches = _matches(leader_set, hard_blocked_rows)
        watch_only_matches = _matches(leader_set, watch_rows)

        covered = (
            {_ticker(r.get("ticker")) for r in official_matches}
            | {_ticker(r.get("ticker")) for r in selected_matches}
            | {_ticker(r.get("ticker")) for r in rejected_matches}
            | {_ticker(r.get("ticker")) for r in hard_blocked_matches}
            | {_ticker(r.get("ticker")) for r in watch_only_matches}
        )
        missing = [t for t in leaders if t not in covered]

        reasons = _gap_reasons(
            leader_count=len(leaders),
            official_count=len(official_matches) + len(selected_matches),
            rejected_count=len(rejected_matches),
            hard_blocked_count=len(hard_blocked_matches),
            watch_only_count=len(watch_only_matches),
            rejection_artifact_exists=rejection_artifact_exists,
            missing_count=len(missing),
        )

        bridge_themes.append({
            "theme": theme.get("theme"),
            "theme_id": theme.get("theme_id"),
            "lifecycle_state": theme.get("lifecycle_state"),
            "theme_score": theme.get("theme_score"),
            "risk_flags": theme.get("risk_flags", []),
            "market_evidence": theme.get("market_evidence", {}),
            "leader_count": len(leaders),
            "leaders": leaders,
            "official_pick_matches": _simplify_rows(official_matches + selected_matches),
            "official_pick_match_count": len(official_matches) + len(selected_matches),
            "rejected_matches": _simplify_rows(rejected_matches),
            "rejected_match_count": len(rejected_matches),
            "hard_blocked_matches": _simplify_rows(hard_blocked_matches),
            "hard_blocked_match_count": len(hard_blocked_matches),
            "watch_only_matches": _simplify_rows(watch_only_matches),
            "watch_only_match_count": len(watch_only_matches),
            "missing_from_official_and_watch_only": missing,
            "missing_from_official_and_watch_only_count": len(missing),
            "likely_gap_reasons": reasons,
            "coverage_ratio": round((len(leaders) - len(missing)) / len(leaders), 4) if leaders else None,
        })

    reason_counts = Counter(
        reason
        for theme in bridge_themes
        for reason in theme["likely_gap_reasons"]
    )

    return {
        "artifact": "theme_pick_bridge",
        "date": date_str,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **SAFETY,
        "source_files": {
            "theme_discovery": str(theme_path),
            "picks_log": str(data_dir / "picks_log.csv"),
            "daily_picks_candidate_rejections": str(rejection_path),
            "late_daily_ideas": str(data_dir / f"late_daily_ideas_{date_str}.jsonl"),
            "opening_range_observations": str(data_dir / f"opening_range_observations_{date_str}.jsonl"),
            "intraday_momentum_observations": str(data_dir / f"intraday_momentum_observations_{date_str}.jsonl"),
        },
        "input_status": {
            "theme_discovery_exists": theme_path.exists(),
            "theme_count_available": len(themes),
            "picks_log_official_rows_for_date": len(official_rows),
            "daily_rejection_artifact_exists": rejection_artifact_exists,
            "rejected_candidate_count": len(rejected_rows),
            "hard_blocked_candidate_count": len(hard_blocked_rows),
            "watch_only_lane_count": len(watch_rows),
            "invalid_watch_only_lines": invalid_watch_lines,
        },
        "summary": {
            "themes_analyzed": len(bridge_themes),
            "official_pick_tickers": sorted(official_tickers),
            "watch_only_tickers": sorted(watch_tickers),
            "gap_reason_counts": dict(sorted(reason_counts.items())),
        },
        "themes": bridge_themes,
        "safety_flags": [
            "observe_only",
            "not_official_scoring",
            "no_production_scoring_effect",
            "not_paper_trade",
            "not_live_trade",
            "no_buy_instructions",
        ],
    }


def bridge_json_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"theme_pick_bridge_{date_str}.json"


def bridge_markdown_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"theme_pick_bridge_{date_str}.md"


def format_markdown(report: dict) -> str:
    lines = [
        "# Theme-to-Pick Bridge Report",
        "",
        "Observe-only comparison. Not production scoring. Not buy instructions.",
        "",
        f"- Date: **{report['date']}**",
        f"- Themes analyzed: **{report['summary']['themes_analyzed']}**",
        f"- Official score boost enabled: **{str(report['official_score_boost_enabled']).lower()}**",
        f"- Production scoring effect: **{str(report['production_scoring_effect']).lower()}**",
        f"- Paper trading enabled: **{str(report['paper_trading_enabled']).lower()}**",
        f"- Live trading enabled: **{str(report['live_trading_enabled']).lower()}**",
        "",
        "## Input Status",
    ]

    for key, value in report["input_status"].items():
        lines.append(f"- {key}: **{value}**")

    lines.extend(["", "## Gap Reason Counts"])
    if report["summary"]["gap_reason_counts"]:
        for key, value in report["summary"]["gap_reason_counts"].items():
            lines.append(f"- {key}: **{value}**")
    else:
        lines.append("- None")

    lines.extend(["", "## Theme Bridge"])
    if not report["themes"]:
        lines.append("- No themes available to bridge.")
    else:
        for theme in report["themes"]:
            lines.extend([
                (
                    f"- **{theme['theme']}** ({theme['lifecycle_state']}, "
                    f"theme_score={theme['theme_score']}, coverage={theme['coverage_ratio']})"
                ),
                f"  - Leaders: `{', '.join(theme['leaders'][:15])}`",
                (
                    "  - Market evidence: "
                    f"status={theme.get('market_evidence', {}).get('market_evidence_status')}, "
                    f"adjustment={theme.get('market_evidence', {}).get('market_quality_score_adjustment')}, "
                    f"vs_spy={theme.get('market_evidence', {}).get('relative_strength_vs_spy_pct')}"
                ),
                f"  - Risk flags: `{', '.join(theme.get('risk_flags') or []) or 'none'}`",
                f"  - Official matches ({theme['official_pick_match_count']}): `{', '.join(r['ticker'] for r in theme['official_pick_matches']) or 'none'}`",
                f"  - Rejected/filtered matches ({theme['rejected_match_count']}): `{', '.join(r['ticker'] for r in theme['rejected_matches']) or 'none'}`",
                f"  - Hard-blocked matches ({theme['hard_blocked_match_count']}): `{', '.join(r['ticker'] for r in theme['hard_blocked_matches']) or 'none'}`",
                f"  - Watch-only matches ({theme['watch_only_match_count']}): `{', '.join(r['ticker'] for r in theme['watch_only_matches']) or 'none'}`",
                f"  - Missing from official/watch-only: `{', '.join(theme['missing_from_official_and_watch_only'][:20]) or 'none'}`",
                f"  - Likely gap reasons: `{', '.join(theme['likely_gap_reasons'])}`",
            ])

    lines.extend([
        "",
        "## Safety",
        "- Observe-only bridge.",
        "- Does not alter official scoring.",
        "- Does not create picks.",
        "- Does not enable paper or live trading.",
        "- No buy instructions.",
    ])
    return "\n".join(lines)


def write_outputs(report: dict, *, data_dir: Path = DATA_DIR) -> tuple[Path, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)

    json_path = bridge_json_path(report["date"], data_dir=data_dir)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = bridge_markdown_path(report["date"], data_dir=data_dir)
    md_path.write_text(format_markdown(report) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--theme-path", default="")
    parser.add_argument("--max-themes", type=int, default=12)
    args = parser.parse_args(argv)

    theme_path = Path(args.theme_path) if args.theme_path else None
    report = build_theme_pick_bridge(
        date_str=args.date,
        data_dir=Path(args.data_dir),
        theme_path=theme_path,
        max_themes=args.max_themes,
    )
    json_path, md_path = write_outputs(report, data_dir=Path(args.data_dir))

    print(f"[theme-pick-bridge] wrote {json_path}")
    print(f"[theme-pick-bridge] markdown {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
