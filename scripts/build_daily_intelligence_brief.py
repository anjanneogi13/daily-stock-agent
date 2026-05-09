#!/usr/bin/env python3
"""Daily Intelligence Brief v0 — observe-only.

Synthesizes data readiness, artifact completeness, candidate lifecycle,
watch-only evidence, no-pick diagnostics, theme discovery, and theme-pick bridge
into one founder-readable daily operating report.

Outputs:
- data/daily_intelligence_brief_YYYY-MM-DD.json
- data/daily_intelligence_brief_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DATA_DIR = Path("data")

SAFETY = {
    "observe_only": True,
    "production_scoring_effect": False,
    "official_score_boost_enabled": False,
    "paper_trading_enabled": False,
    "live_trading_enabled": False,
    "buy_instructions_enabled": False,
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


def _top_themes(theme_discovery: dict, limit: int = 8) -> list[dict]:
    themes = theme_discovery.get("themes", []) if isinstance(theme_discovery, dict) else []
    out = []
    for theme in themes[:limit]:
        out.append({
            "theme": theme.get("theme"),
            "theme_id": theme.get("theme_id"),
            "lifecycle_state": theme.get("lifecycle_state"),
            "theme_score": theme.get("theme_score"),
            "breadth": theme.get("breadth"),
            "tickers": theme.get("tickers", [])[:15],
            "risk_flags": theme.get("risk_flags", []),
        })
    return out


def _theme_bridge_summary(theme_bridge: dict) -> dict:
    if not isinstance(theme_bridge, dict) or not theme_bridge:
        return {
            "available": False,
            "themes_analyzed": 0,
            "gap_reason_counts": {},
            "top_theme_gaps": [],
        }

    top_gaps = []
    for theme in theme_bridge.get("themes", [])[:8]:
        top_gaps.append({
            "theme": theme.get("theme"),
            "lifecycle_state": theme.get("lifecycle_state"),
            "leaders": theme.get("leaders", [])[:15],
            "official_pick_match_count": theme.get("official_pick_match_count", 0),
            "rejected_match_count": theme.get("rejected_match_count", 0),
            "hard_blocked_match_count": theme.get("hard_blocked_match_count", 0),
            "watch_only_match_count": theme.get("watch_only_match_count", 0),
            "likely_gap_reasons": theme.get("likely_gap_reasons", []),
        })

    return {
        "available": True,
        "themes_analyzed": theme_bridge.get("summary", {}).get("themes_analyzed", len(theme_bridge.get("themes", []))),
        "gap_reason_counts": theme_bridge.get("summary", {}).get("gap_reason_counts", {}),
        "top_theme_gaps": top_gaps,
        "input_status": theme_bridge.get("input_status", {}),
    }


def _candidate_summary(candidate_lifecycle: dict) -> dict:
    if not isinstance(candidate_lifecycle, dict) or not candidate_lifecycle:
        return {
            "available": False,
            "candidate_count": 0,
            "state_counts": {},
            "watch_only_tickers": [],
            "diagnostics_unavailable_count": 0,
            "sample_candidates": [],
        }

    candidates = candidate_lifecycle.get("candidates", [])
    watch_only = [
        c.get("ticker") for c in candidates
        if c.get("lifecycle_state") == "watch_only" and c.get("ticker")
    ]

    return {
        "available": True,
        "candidate_count": candidate_lifecycle.get("summary", {}).get("candidate_count", len(candidates)),
        "state_counts": candidate_lifecycle.get("summary", {}).get("state_counts", {}),
        "watch_only_tickers": watch_only[:20],
        "diagnostics_unavailable_count": candidate_lifecycle.get("summary", {}).get("state_counts", {}).get("diagnostics_unavailable", 0),
        "sample_candidates": [
            {
                "ticker": c.get("ticker"),
                "state": c.get("lifecycle_state"),
                "themes": c.get("themes", []),
                "reason": c.get("reason"),
            }
            for c in candidates[:12]
        ],
    }


def _watch_only_lane_summary(data_dir: Path, date_str: str) -> dict:
    lanes = {
        "late_daily_ideas": data_dir / f"late_daily_ideas_{date_str}.jsonl",
        "opening_range_observations": data_dir / f"opening_range_observations_{date_str}.jsonl",
        "intraday_momentum_observations": data_dir / f"intraday_momentum_observations_{date_str}.jsonl",
    }
    summary = {}
    all_tickers = []
    for lane, path in lanes.items():
        rows, bad = load_jsonl(path)
        tickers = [str(r.get("ticker") or "").upper() for r in rows if r.get("ticker")]
        all_tickers.extend(tickers)

        quality_counts = Counter(
            str(r.get("opening_range_quality_status") or r.get("quality_status") or "unknown")
            for r in rows
        )
        summary[lane] = {
            "exists": path.exists(),
            "row_count": len(rows),
            "parse_errors": bad,
            "tickers": tickers[:20],
            "quality_status_counts": dict(sorted(quality_counts.items())) if rows else {},
            "samples": [
                {
                    "ticker": r.get("ticker"),
                    "reason": r.get("reason") or r.get("watch_only_reason") or r.get("headline") or "",
                    "quality_status": r.get("opening_range_quality_status") or r.get("quality_status") or "",
                }
                for r in rows[:5]
            ],
        }

    return {
        "total_watch_only_rows": sum(v["row_count"] for v in summary.values()),
        "unique_watch_only_tickers": sorted(set(all_tickers)),
        "lanes": summary,
    }


def _no_pick_summary(no_pick_report: dict) -> dict:
    if not isinstance(no_pick_report, dict) or not no_pick_report:
        return {"available": False}

    market = no_pick_report.get("market_data_health", {}) if isinstance(no_pick_report.get("market_data_health"), dict) else {}
    providers = market.get("providers", {}) if isinstance(market, dict) else {}
    run = market.get("run", {}) if isinstance(market, dict) else {}

    provider_summary = {}
    for provider, stats in providers.items():
        if isinstance(stats, dict):
            provider_summary[provider] = {
                "attempts": stats.get("attempts", 0),
                "successes": stats.get("successes", 0),
                "errors": stats.get("errors", 0),
                "rate_limited": stats.get("rate_limited", 0),
                "empty": stats.get("empty", 0),
            }

    return {
        "available": True,
        "mode": no_pick_report.get("mode"),
        "next_action": no_pick_report.get("next_action"),
        "pipeline": no_pick_report.get("pipeline", {}),
        "market_data_run": run,
        "provider_summary": provider_summary,
    }


def _scoring_safety_summary() -> dict:
    try:
        from src.scoring_safety import load_yaml_config, scoring_safety_status

        cfg = load_yaml_config("config.yaml")
        status = scoring_safety_status(cfg)
        return {"available": True, "status": "passed", **status}
    except Exception as exc:
        return {"available": True, "status": "failed", "error": str(exc)}


def classify_daily_operating_status(
    *,
    completeness_status: str,
    no_pick_classification: str,
    official_pick_count: int,
) -> str:
    if completeness_status == "missing_critical_artifacts" or no_pick_classification == "pipeline_incomplete":
        return "incomplete_pipeline"
    if no_pick_classification == "data_provider_failure":
        return "data_failed_or_degraded"
    if official_pick_count > 0:
        return "productive_with_official_picks"
    if no_pick_classification == "strategy_driven_no_qualified_candidates":
        return "productive_no_official_picks"
    if no_pick_classification == "diagnostics_missing":
        return "diagnostics_missing"
    return "mixed_or_uncertain"


def _operating_summary(status: str) -> str:
    if status == "incomplete_pipeline":
        return "Daily operating evidence is incomplete. Do not interpret the day as a strategy-driven no-pick outcome."
    if status == "data_failed_or_degraded":
        return "Daily operating evidence indicates data/provider degradation. Official pick quality cannot be judged normally."
    if status == "productive_with_official_picks":
        return "Daily pipeline produced official picks and has enough evidence for normal review."
    if status == "productive_no_official_picks":
        return "Daily pipeline appears to have run and produced no official picks from qualified candidates."
    if status == "diagnostics_missing":
        return "Daily run evidence exists, but candidate diagnostics are missing."
    return "Daily operating status is mixed or uncertain from available artifacts."


def _monitoring_priorities(
    *,
    operating_status: str,
    completeness: dict,
    readiness: dict,
    candidate_summary: dict,
    top_themes: list[dict],
    bridge_summary: dict,
) -> list[str]:
    priorities: list[str] = []

    missing_critical = completeness.get("summary", {}).get("missing_critical", []) if isinstance(completeness, dict) else []
    if missing_critical:
        priorities.append(
            "Restore missing critical daily artifacts: " + ", ".join(missing_critical)
        )

    readiness_warnings = readiness.get("readiness_warnings", []) if isinstance(readiness, dict) else []
    if readiness_warnings:
        priorities.append(
            "Review data readiness warnings: " + ", ".join(readiness_warnings[:6])
        )

    if operating_status == "data_failed_or_degraded":
        priorities.append("Investigate provider/rate-limit/data-health degradation before judging model quality.")

    if candidate_summary.get("diagnostics_unavailable_count", 0):
        priorities.append(
            f"Trace {candidate_summary['diagnostics_unavailable_count']} diagnostics-unavailable candidates/theme leaders after pipeline diagnostics are restored."
        )

    if candidate_summary.get("watch_only_tickers"):
        priorities.append(
            "Review watch-only candidates for lessons, not official performance: "
            + ", ".join(candidate_summary["watch_only_tickers"][:10])
        )

    if top_themes:
        priorities.append(
            "Observe top discovered themes without score boosts: "
            + ", ".join(str(t.get("theme")) for t in top_themes[:5])
        )

    gap_counts = bridge_summary.get("gap_reason_counts", {}) if isinstance(bridge_summary, dict) else {}
    if gap_counts:
        priorities.append(
            "Review theme-to-pick gaps: "
            + ", ".join(f"{k}={v}" for k, v in list(gap_counts.items())[:5])
        )

    if not priorities:
        priorities.append("Continue observe-only monitoring; no urgent reliability issue was found from available artifacts.")

    return priorities


def build_daily_intelligence_brief(
    *,
    date_str: str,
    data_dir: Path = DATA_DIR,
) -> dict:
    artifact_completeness = load_json(data_dir / f"artifact_completeness_{date_str}.json", {})
    data_readiness = load_json(data_dir / f"data_readiness_{date_str}.json", {})
    candidate_lifecycle = load_json(data_dir / f"candidate_lifecycle_{date_str}.json", {})
    theme_discovery = load_json(data_dir / f"theme_discovery_{date_str}.json", {})
    theme_pick_bridge = load_json(data_dir / f"theme_pick_bridge_{date_str}.json", {})
    no_pick_report = load_json(data_dir / f"daily_picks_no_pick_report_{date_str}.json", {})

    official_pick_count = int(data_readiness.get("official_pick_count", 0) or 0) if isinstance(data_readiness, dict) else 0
    no_pick_classification = data_readiness.get("no_pick_classification", "") if isinstance(data_readiness, dict) else ""
    completeness_status = artifact_completeness.get("completeness_status", "") if isinstance(artifact_completeness, dict) else ""

    operating_status = classify_daily_operating_status(
        completeness_status=completeness_status,
        no_pick_classification=no_pick_classification,
        official_pick_count=official_pick_count,
    )

    top_themes = _top_themes(theme_discovery)
    bridge_summary = _theme_bridge_summary(theme_pick_bridge)
    candidate_summary = _candidate_summary(candidate_lifecycle)
    watch_only_summary = _watch_only_lane_summary(data_dir, date_str)
    no_pick = _no_pick_summary(no_pick_report)

    monitoring_priorities = _monitoring_priorities(
        operating_status=operating_status,
        completeness=artifact_completeness if isinstance(artifact_completeness, dict) else {},
        readiness=data_readiness if isinstance(data_readiness, dict) else {},
        candidate_summary=candidate_summary,
        top_themes=top_themes,
        bridge_summary=bridge_summary,
    )

    return {
        "artifact": "daily_intelligence_brief",
        "date": date_str,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **SAFETY,
        "daily_operating_status": operating_status,
        "daily_operating_summary": _operating_summary(operating_status),
        "official_pick_status": {
            "official_pick_count": official_pick_count,
            "official_pick_tickers": data_readiness.get("official_pick_tickers", []) if isinstance(data_readiness, dict) else [],
            "readiness_status": data_readiness.get("official_pick_readiness_status", "") if isinstance(data_readiness, dict) else "",
            "no_pick_classification": no_pick_classification,
        },
        "artifact_completeness": {
            "available": bool(artifact_completeness),
            "completeness_status": completeness_status,
            "missing_critical": artifact_completeness.get("summary", {}).get("missing_critical", []) if isinstance(artifact_completeness, dict) else [],
            "warnings": artifact_completeness.get("summary", {}).get("warnings", []) if isinstance(artifact_completeness, dict) else [],
        },
        "data_readiness": {
            "available": bool(data_readiness),
            "data_provider_status": data_readiness.get("data_provider_status", "") if isinstance(data_readiness, dict) else "",
            "readiness_warnings": data_readiness.get("readiness_warnings", []) if isinstance(data_readiness, dict) else [],
        },
        "candidate_lifecycle": candidate_summary,
        "watch_only": watch_only_summary,
        "no_pick_report": no_pick,
        "theme_discovery": {
            "available": bool(theme_discovery),
            "theme_count": theme_discovery.get("theme_count", 0) if isinstance(theme_discovery, dict) else 0,
            "top_themes": top_themes,
        },
        "theme_pick_bridge": bridge_summary,
        "tomorrow_observe_only_monitoring_priorities": monitoring_priorities,
        "scoring_safety": _scoring_safety_summary(),
        "source_files": {
            "artifact_completeness": str(data_dir / f"artifact_completeness_{date_str}.json"),
            "data_readiness": str(data_dir / f"data_readiness_{date_str}.json"),
            "candidate_lifecycle": str(data_dir / f"candidate_lifecycle_{date_str}.json"),
            "theme_discovery": str(data_dir / f"theme_discovery_{date_str}.json"),
            "theme_pick_bridge": str(data_dir / f"theme_pick_bridge_{date_str}.json"),
            "no_pick_report": str(data_dir / f"daily_picks_no_pick_report_{date_str}.json"),
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


def daily_intelligence_brief_json_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"daily_intelligence_brief_{date_str}.json"


def daily_intelligence_brief_markdown_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"daily_intelligence_brief_{date_str}.md"


def format_markdown(report: dict) -> str:
    lines = [
        "# Daily Intelligence Brief",
        "",
        "Observe-only founder operating report. This report does not alter scoring or create picks.",
        "",
        f"- Date: **{report['date']}**",
        f"- Daily operating status: **{report['daily_operating_status']}**",
        f"- Summary: {report['daily_operating_summary']}",
        f"- Official pick count: **{report['official_pick_status']['official_pick_count']}**",
        f"- Official tickers: `{', '.join(report['official_pick_status']['official_pick_tickers']) or 'none'}`",
        f"- Readiness status: **{report['official_pick_status']['readiness_status']}**",
        f"- No-pick classification: **{report['official_pick_status']['no_pick_classification']}**",
        "",
        "## Artifact Completeness",
        f"- Status: **{report['artifact_completeness']['completeness_status']}**",
        f"- Missing critical: `{', '.join(report['artifact_completeness']['missing_critical']) or 'none'}`",
        f"- Warnings: `{', '.join(report['artifact_completeness']['warnings']) or 'none'}`",
        "",
        "## Data Readiness",
        f"- Provider/data status: **{report['data_readiness']['data_provider_status']}**",
        f"- Warnings: `{', '.join(report['data_readiness']['readiness_warnings']) or 'none'}`",
        "",
        "## Candidate Lifecycle",
        f"- Candidate count: **{report['candidate_lifecycle']['candidate_count']}**",
        f"- State counts: `{report['candidate_lifecycle']['state_counts']}`",
        f"- Watch-only tickers: `{', '.join(report['candidate_lifecycle']['watch_only_tickers']) or 'none'}`",
        f"- Diagnostics unavailable count: **{report['candidate_lifecycle']['diagnostics_unavailable_count']}**",
        "",
        "## Watch-Only Evidence",
        f"- Total watch-only rows: **{report['watch_only']['total_watch_only_rows']}**",
        f"- Unique watch-only tickers: `{', '.join(report['watch_only']['unique_watch_only_tickers']) or 'none'}`",
    ]

    for lane, info in report["watch_only"]["lanes"].items():
        lines.append(f"- **{lane}**: rows={info['row_count']}, exists={info['exists']}, parse_errors={info['parse_errors']}")

    lines.extend(["", "## No-Pick Diagnostics"])
    if report["no_pick_report"]["available"]:
        lines.append(f"- Mode: **{report['no_pick_report'].get('mode')}**")
        lines.append(f"- Next action: {report['no_pick_report'].get('next_action')}")
        lines.append(f"- Pipeline: `{report['no_pick_report'].get('pipeline', {})}`")
        lines.append(f"- Provider summary: `{report['no_pick_report'].get('provider_summary', {})}`")
    else:
        lines.append("- No no-pick report available.")

    lines.extend(["", "## Discovered Themes"])
    if report["theme_discovery"]["top_themes"]:
        for theme in report["theme_discovery"]["top_themes"]:
            lines.append(
                f"- **{theme['theme']}** — state=`{theme['lifecycle_state']}`, "
                f"score=`{theme['theme_score']}`, breadth=`{theme['breadth']}`, "
                f"tickers=`{', '.join(theme['tickers'][:10])}`"
            )
    else:
        lines.append("- No theme discovery artifact available.")

    lines.extend(["", "## Theme-to-Pick Bridge"])
    if report["theme_pick_bridge"]["available"]:
        lines.append(f"- Themes analyzed: **{report['theme_pick_bridge']['themes_analyzed']}**")
        lines.append(f"- Gap reason counts: `{report['theme_pick_bridge']['gap_reason_counts']}`")
        for theme in report["theme_pick_bridge"]["top_theme_gaps"][:6]:
            lines.append(
                f"- **{theme['theme']}** — official={theme['official_pick_match_count']}, "
                f"rejected={theme['rejected_match_count']}, hard_blocked={theme['hard_blocked_match_count']}, "
                f"watch_only={theme['watch_only_match_count']}, gaps=`{', '.join(theme['likely_gap_reasons'])}`"
            )
    else:
        lines.append("- No theme-to-pick bridge artifact available.")

    lines.extend(["", "## Tomorrow Observe-Only Monitoring Priorities"])
    for item in report["tomorrow_observe_only_monitoring_priorities"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Scoring Safety",
        f"- Safety status: **{report['scoring_safety'].get('status')}**",
        f"- Legacy sector boosts disabled: **{report['scoring_safety'].get('legacy_sector_boosts_disabled')}**",
        f"- Theme-aware official scoring enabled: **{report['scoring_safety'].get('theme_aware_official_scoring_enabled')}**",
        f"- Production scoring effect: **{report['scoring_safety'].get('production_scoring_effect')}**",
        "",
        "## Safety",
        "- Observe-only daily intelligence brief.",
        "- Does not alter official scoring.",
        "- Does not create picks.",
        "- Does not enable paper or live trading.",
        "- No buy instructions.",
    ])

    return "\n".join(lines)


def write_outputs(report: dict, *, data_dir: Path = DATA_DIR) -> tuple[Path, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = daily_intelligence_brief_json_path(report["date"], data_dir=data_dir)
    md_path = daily_intelligence_brief_markdown_path(report["date"], data_dir=data_dir)

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_markdown(report) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    args = parser.parse_args(argv)

    report = build_daily_intelligence_brief(date_str=args.date, data_dir=Path(args.data_dir))
    json_path, md_path = write_outputs(report, data_dir=Path(args.data_dir))

    print(f"[daily-brief] wrote {json_path}")
    print(f"[daily-brief] markdown {md_path}")
    print(f"[daily-brief] status {report['daily_operating_status']}")
    print(f"[daily-brief] priorities {len(report['tomorrow_observe_only_monitoring_priorities'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
