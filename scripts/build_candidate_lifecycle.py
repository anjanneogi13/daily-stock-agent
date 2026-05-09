#!/usr/bin/env python3
"""Candidate Lifecycle Ledger v0 — observe-only.

Reconstructs where candidates/theme leaders appeared or disappeared using
existing daily artifacts. This does not alter scoring or create picks.

Outputs:
- data/candidate_lifecycle_YYYY-MM-DD.json
- data/candidate_lifecycle_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIR = Path("data")

SAFETY = {
    "observe_only": True,
    "production_scoring_effect": False,
    "official_score_boost_enabled": False,
    "paper_trading_enabled": False,
    "live_trading_enabled": False,
    "buy_instructions_enabled": False,
}

STATE_PRIORITY = {
    "selected_official": 100,
    "hard_blocked": 90,
    "filtered": 80,
    "watch_only": 70,
    "diagnostics_unavailable": 40,
    "missing_from_universe": 30,
    "data_fetch_failed": 20,
    "unknown": 0,
}


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        return {"_parse_error": str(exc), "_path": str(path)}


def load_jsonl(path: Path) -> tuple[list[dict], int]:
    rows: list[dict] = []
    bad = 0
    if not path.exists():
        return rows, bad
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                rows.append(obj)
        except Exception:
            bad += 1
    return rows, bad


def _ticker(value: Any) -> str:
    return str(value or "").strip().upper()


def _date_prefix(value: Any) -> str:
    return str(value or "")[:10]


def _read_picks_for_date(path: Path, date_str: str) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    try:
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                if _date_prefix(row.get("pick_date")) == date_str:
                    row = dict(row)
                    row["ticker"] = _ticker(row.get("ticker"))
                    rows.append(row)
    except Exception:
        return []
    return [r for r in rows if r.get("ticker")]


def _candidate_detail(row: dict, *, default_source: str = "") -> dict:
    cand = row.get("candidate") if isinstance(row.get("candidate"), dict) else row
    scores = cand.get("scores") if isinstance(cand.get("scores"), dict) else {}
    ticker = _ticker(cand.get("ticker") or row.get("ticker"))
    return {
        "ticker": ticker,
        "company": cand.get("company") or cand.get("company_name") or row.get("company") or "",
        "tag": cand.get("tag") or cand.get("sector_tag") or scores.get("sector_tag") or "",
        "score": cand.get("score") or scores.get("composite") or row.get("score") or "",
        "reason": row.get("reason") or row.get("block_reason") or row.get("rejection_reason") or "",
        "source": row.get("source") or default_source,
    }


def _rejection_groups(path: Path) -> dict[str, list[dict]]:
    raw = load_json(path, {})
    diag = raw.get("diagnostics", raw) if isinstance(raw, dict) else {}
    if not isinstance(diag, dict):
        diag = {}

    groups = {
        "selected_picks": [],
        "hard_blocked_candidates": [],
        "rejected_candidates": [],
        "pre_hard_block_candidates": [],
    }
    for key in groups:
        rows = diag.get(key) or []
        if isinstance(rows, list):
            groups[key] = [
                _candidate_detail(r, default_source=f"candidate_rejections:{key}")
                for r in rows
                if isinstance(r, dict) and _candidate_detail(r).get("ticker")
            ]
    return groups


def _watch_rows(data_dir: Path, date_str: str) -> tuple[list[dict], dict[str, int]]:
    sources = {
        "late_daily_watch_only": data_dir / f"late_daily_ideas_{date_str}.jsonl",
        "opening_range_watch_only": data_dir / f"opening_range_observations_{date_str}.jsonl",
        "intraday_momentum_watch_only": data_dir / f"intraday_momentum_observations_{date_str}.jsonl",
    }
    rows: list[dict] = []
    bad_counts: dict[str, int] = {}
    for source, path in sources.items():
        loaded, bad = load_jsonl(path)
        bad_counts[source] = bad
        for row in loaded:
            ticker = _ticker(row.get("ticker"))
            if not ticker:
                continue
            detail = _candidate_detail(row, default_source=source)
            detail["source"] = source
            detail["reason"] = (
                row.get("reason")
                or row.get("watch_only_reason")
                or row.get("headline")
                or detail.get("reason")
                or ""
            )
            detail["quality_status"] = row.get("opening_range_quality_status") or row.get("quality_status") or ""
            rows.append(detail)
    return rows, bad_counts


def _theme_leaders(data_dir: Path, date_str: str, max_themes: int, max_leaders: int) -> tuple[dict[str, list[str]], dict]:
    bridge_path = data_dir / f"theme_pick_bridge_{date_str}.json"
    discovery_path = data_dir / f"theme_discovery_{date_str}.json"

    bridge = load_json(bridge_path, {})
    if isinstance(bridge, dict) and bridge.get("themes"):
        themes = {}
        for theme in bridge.get("themes", [])[:max_themes]:
            name = str(theme.get("theme") or "")
            leaders = [_ticker(t) for t in theme.get("leaders", [])[:max_leaders] if _ticker(t)]
            if name and leaders:
                themes[name] = leaders
        return themes, {
            "source": str(bridge_path),
            "source_type": "theme_pick_bridge",
            "available": True,
        }

    discovery = load_json(discovery_path, {})
    if isinstance(discovery, dict) and discovery.get("themes"):
        themes = {}
        for theme in discovery.get("themes", [])[:max_themes]:
            name = str(theme.get("theme") or "")
            leaders = [_ticker(t) for t in theme.get("tickers", [])[:max_leaders] if _ticker(t)]
            if name and leaders:
                themes[name] = leaders
        return themes, {
            "source": str(discovery_path),
            "source_type": "theme_discovery",
            "available": True,
        }

    return {}, {
        "source": "",
        "source_type": "none",
        "available": False,
    }


def _add_event(ledger: dict, ticker: str, *, state: str, source: str, detail: dict | None = None) -> None:
    if not ticker:
        return
    row = ledger.setdefault(ticker, {
        "ticker": ticker,
        "company": "",
        "tag": "",
        "lifecycle_state": "unknown",
        "evidence_sources": [],
        "events": [],
        "themes": [],
        "reason": "",
    })

    detail = detail or {}
    if detail.get("company") and not row["company"]:
        row["company"] = detail.get("company", "")
    if detail.get("tag") and not row["tag"]:
        row["tag"] = detail.get("tag", "")
    if detail.get("reason") and not row["reason"]:
        row["reason"] = detail.get("reason", "")

    event = {
        "state": state,
        "source": source,
        "reason": detail.get("reason", ""),
        "score": detail.get("score", ""),
        "quality_status": detail.get("quality_status", ""),
    }
    row["events"].append(event)
    if source and source not in row["evidence_sources"]:
        row["evidence_sources"].append(source)

    if STATE_PRIORITY.get(state, 0) >= STATE_PRIORITY.get(row["lifecycle_state"], 0):
        row["lifecycle_state"] = state


def _finalize_reason(row: dict, readiness: dict) -> str:
    state = row.get("lifecycle_state")
    classification = readiness.get("no_pick_classification", "")
    existing = row.get("reason") or ""

    if state == "diagnostics_unavailable":
        base = existing or "candidate/theme leader could not be traced because diagnostics are unavailable"
        return f"{base} ({classification})" if classification else base
    if state == "data_fetch_failed":
        base = existing or "candidate trace affected by data/provider readiness failure"
        return f"{base} ({classification})" if classification else base

    if existing:
        return existing

    if state == "selected_official":
        return "selected as official pick"
    if state == "hard_blocked":
        return "candidate was hard-blocked"
    if state == "filtered":
        return "candidate was filtered or rejected"
    if state == "watch_only":
        return "candidate appeared in watch-only lane"
    if state == "missing_from_universe":
        return "candidate/theme leader was not found in official, rejection, or watch-only artifacts"
    return "candidate lifecycle is unknown from available artifacts"


def build_candidate_lifecycle(
    *,
    date_str: str,
    data_dir: Path = DATA_DIR,
    max_themes: int = 12,
    max_leaders_per_theme: int = 25,
) -> dict:
    readiness_path = data_dir / f"data_readiness_{date_str}.json"
    rejection_path = data_dir / f"daily_picks_candidate_rejections_{date_str}.json"
    picks_log_path = data_dir / "picks_log.csv"

    readiness = load_json(readiness_path, {})
    if not isinstance(readiness, dict):
        readiness = {}

    official_rows = _read_picks_for_date(picks_log_path, date_str)
    rejection_groups = _rejection_groups(rejection_path)
    watch_rows, watch_bad_counts = _watch_rows(data_dir, date_str)
    theme_map, theme_source = _theme_leaders(data_dir, date_str, max_themes, max_leaders_per_theme)

    ledger: dict[str, dict] = {}

    for row in official_rows:
        _add_event(ledger, _ticker(row.get("ticker")), state="selected_official", source="picks_log", detail={
            "company": row.get("company") or "",
            "tag": row.get("tag") or row.get("sector_tag") or "",
            "reason": row.get("evaluation_status") or "",
        })

    for row in rejection_groups["selected_picks"]:
        _add_event(ledger, row["ticker"], state="selected_official", source="candidate_rejections:selected_picks", detail=row)

    for row in rejection_groups["hard_blocked_candidates"]:
        _add_event(ledger, row["ticker"], state="hard_blocked", source="candidate_rejections:hard_blocked_candidates", detail=row)

    for key in ["rejected_candidates", "pre_hard_block_candidates"]:
        for row in rejection_groups[key]:
            _add_event(ledger, row["ticker"], state="filtered", source=f"candidate_rejections:{key}", detail=row)

    for row in watch_rows:
        _add_event(ledger, row["ticker"], state="watch_only", source=row.get("source") or "watch_only", detail=row)

    diagnostics_available = bool(
        readiness.get("input_status", {}).get("candidate_diagnostics_available")
        or readiness.get("candidate_diagnostics", {}).get("available")
    )
    no_pick_classification = readiness.get("no_pick_classification", "")
    pipeline_incomplete = no_pick_classification in {"pipeline_incomplete", "diagnostics_missing"}
    data_provider_failure = no_pick_classification == "data_provider_failure"

    for theme, leaders in theme_map.items():
        for ticker in leaders:
            row = ledger.setdefault(ticker, {
                "ticker": ticker,
                "company": "",
                "tag": "",
                "lifecycle_state": "unknown",
                "evidence_sources": [],
                "events": [],
                "themes": [],
                "reason": "",
            })
            if theme not in row["themes"]:
                row["themes"].append(theme)

            if not row["events"]:
                if pipeline_incomplete or not diagnostics_available:
                    state = "diagnostics_unavailable"
                elif data_provider_failure:
                    state = "data_fetch_failed"
                else:
                    state = "missing_from_universe"
                _add_event(
                    ledger,
                    ticker,
                    state=state,
                    source=theme_source.get("source_type", "theme_leaders"),
                    detail={"reason": f"theme leader from {theme}; no matching daily candidate artifact"},
                )

    lifecycle_rows = []
    for ticker, row in sorted(ledger.items()):
        row["themes"] = sorted(row.get("themes") or [])
        row["evidence_sources"] = sorted(row.get("evidence_sources") or [])
        row["reason"] = _finalize_reason(row, readiness)
        lifecycle_rows.append(row)

    state_counts = Counter(row["lifecycle_state"] for row in lifecycle_rows)

    return {
        "artifact": "candidate_lifecycle",
        "date": date_str,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **SAFETY,
        "readiness_context": {
            "data_readiness_available": readiness_path.exists(),
            "official_pick_readiness_status": readiness.get("official_pick_readiness_status", ""),
            "no_pick_classification": readiness.get("no_pick_classification", ""),
            "readiness_warnings": readiness.get("readiness_warnings", []),
        },
        "input_status": {
            "picks_log_available": picks_log_path.exists(),
            "official_pick_count": len(official_rows),
            "candidate_rejection_artifact_available": rejection_path.exists(),
            "candidate_diagnostics_available": diagnostics_available,
            "watch_only_row_count": len(watch_rows),
            "watch_only_parse_errors": watch_bad_counts,
            "theme_leader_source_available": theme_source.get("available", False),
            "theme_leader_source": theme_source,
            "theme_count": len(theme_map),
        },
        "summary": {
            "candidate_count": len(lifecycle_rows),
            "state_counts": dict(sorted(state_counts.items())),
            "theme_leader_count": len({ticker for leaders in theme_map.values() for ticker in leaders}),
        },
        "themes": [
            {"theme": theme, "leaders": leaders}
            for theme, leaders in theme_map.items()
        ],
        "candidates": lifecycle_rows,
        "source_files": {
            "data_readiness": str(readiness_path),
            "picks_log": str(picks_log_path),
            "candidate_rejections": str(rejection_path),
            "theme_pick_bridge": str(data_dir / f"theme_pick_bridge_{date_str}.json"),
            "theme_discovery": str(data_dir / f"theme_discovery_{date_str}.json"),
            "late_daily_ideas": str(data_dir / f"late_daily_ideas_{date_str}.jsonl"),
            "opening_range_observations": str(data_dir / f"opening_range_observations_{date_str}.jsonl"),
            "intraday_momentum_observations": str(data_dir / f"intraday_momentum_observations_{date_str}.jsonl"),
        },
        "safety_flags": [
            "observe_only",
            "not_official_scoring",
            "no_production_scoring_effect",
            "not_paper_trade",
            "not_live_trade",
            "no_buy_instructions",
        ],
    }


def candidate_lifecycle_json_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"candidate_lifecycle_{date_str}.json"


def candidate_lifecycle_markdown_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"candidate_lifecycle_{date_str}.md"


def format_markdown(report: dict) -> str:
    lines = [
        "# Candidate Lifecycle Ledger",
        "",
        "Observe-only reconstruction. This report does not alter scoring or create picks.",
        "",
        f"- Date: **{report['date']}**",
        f"- Candidate count: **{report['summary']['candidate_count']}**",
        f"- Readiness status: **{report['readiness_context']['official_pick_readiness_status']}**",
        f"- No-pick classification: **{report['readiness_context']['no_pick_classification']}**",
        "",
        "## State Counts",
    ]

    if report["summary"]["state_counts"]:
        for state, count in report["summary"]["state_counts"].items():
            lines.append(f"- {state}: **{count}**")
    else:
        lines.append("- No candidates reconstructed from available artifacts.")

    lines.extend(["", "## Input Status"])
    for key, value in report["input_status"].items():
        lines.append(f"- {key}: **{value}**")

    lines.extend(["", "## Theme Leader Coverage"])
    if report["themes"]:
        for theme in report["themes"][:12]:
            lines.append(f"- **{theme['theme']}**: `{', '.join(theme['leaders'][:20])}`")
    else:
        lines.append("- No theme leaders available for this date.")

    lines.extend(["", "## Candidate Lifecycle"])
    if report["candidates"]:
        for row in report["candidates"][:80]:
            themes = ", ".join(row.get("themes") or []) or "none"
            sources = ", ".join(row.get("evidence_sources") or []) or "none"
            lines.extend([
                f"- **{row['ticker']}** — `{row['lifecycle_state']}`",
                f"  - Themes: `{themes}`",
                f"  - Sources: `{sources}`",
                f"  - Reason: {row.get('reason') or 'n/a'}",
            ])
    else:
        lines.append("- No candidate lifecycle rows available.")

    lines.extend([
        "",
        "## Safety",
        "- Observe-only lifecycle ledger.",
        "- Does not alter official scoring.",
        "- Does not create picks.",
        "- Does not enable paper or live trading.",
        "- No buy instructions.",
    ])
    return "\n".join(lines)


def write_outputs(report: dict, *, data_dir: Path = DATA_DIR) -> tuple[Path, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = candidate_lifecycle_json_path(report["date"], data_dir=data_dir)
    md_path = candidate_lifecycle_markdown_path(report["date"], data_dir=data_dir)

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_markdown(report) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--max-themes", type=int, default=12)
    parser.add_argument("--max-leaders-per-theme", type=int, default=25)
    args = parser.parse_args(argv)

    report = build_candidate_lifecycle(
        date_str=args.date,
        data_dir=Path(args.data_dir),
        max_themes=args.max_themes,
        max_leaders_per_theme=args.max_leaders_per_theme,
    )
    json_path, md_path = write_outputs(report, data_dir=Path(args.data_dir))

    print(f"[candidate-lifecycle] wrote {json_path}")
    print(f"[candidate-lifecycle] markdown {md_path}")
    print(f"[candidate-lifecycle] candidates {report['summary']['candidate_count']}")
    print(f"[candidate-lifecycle] states {report['summary']['state_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
