import csv
import json
from pathlib import Path

from scripts.build_candidate_lifecycle import (
    build_candidate_lifecycle,
    format_markdown,
    write_outputs,
)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def write_picks(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row}) or ["pick_date", "ticker"]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def by_ticker(report: dict) -> dict:
    return {row["ticker"]: row for row in report["candidates"]}


def test_candidate_lifecycle_reconstructs_official_rejected_hard_blocked_watch_only(tmp_path):
    date = "2026-05-09"
    write_json(tmp_path / f"data_readiness_{date}.json", {
        "official_pick_readiness_status": "readiness_uncertain",
        "no_pick_classification": "mixed_or_uncertain",
        "input_status": {"candidate_diagnostics_available": True},
        "candidate_diagnostics": {"available": True},
        "readiness_warnings": [],
    })
    write_picks(tmp_path / "picks_log.csv", [
        {"pick_date": date, "ticker": "NVDA", "company": "NVIDIA", "tag": "AI"}
    ])
    write_json(tmp_path / f"daily_picks_candidate_rejections_{date}.json", {
        "diagnostics_available": True,
        "diagnostics": {
            "selected_picks": [{"ticker": "NVDA"}],
            "hard_blocked_candidates": [
                {"candidate": {"ticker": "ARM", "scores": {"sector_tag": "SEMI"}}, "block_reason": "hard risk block"}
            ],
            "rejected_candidates": [
                {"candidate": {"ticker": "MSFT", "scores": {"sector_tag": "AI"}}, "reason": "filtered"}
            ],
            "pre_hard_block_candidates": [],
        },
    })
    write_jsonl(tmp_path / f"late_daily_ideas_{date}.jsonl", [
        {"ticker": "ADBE", "reason": "late AI news"}
    ])
    write_json(tmp_path / f"theme_pick_bridge_{date}.json", {
        "themes": [
            {"theme": "ai", "leaders": ["NVDA", "ARM", "MSFT", "ADBE"]}
        ]
    })

    report = build_candidate_lifecycle(date_str=date, data_dir=tmp_path)
    rows = by_ticker(report)

    assert rows["NVDA"]["lifecycle_state"] == "selected_official"
    assert rows["ARM"]["lifecycle_state"] == "hard_blocked"
    assert rows["MSFT"]["lifecycle_state"] == "filtered"
    assert rows["ADBE"]["lifecycle_state"] == "watch_only"
    assert rows["NVDA"]["themes"] == ["ai"]
    assert report["observe_only"] is True
    assert report["production_scoring_effect"] is False


def test_candidate_lifecycle_marks_theme_leaders_diagnostics_unavailable_when_pipeline_incomplete(tmp_path):
    date = "2026-05-09"
    write_json(tmp_path / f"data_readiness_{date}.json", {
        "official_pick_readiness_status": "not_ready_pipeline_incomplete",
        "no_pick_classification": "pipeline_incomplete",
        "input_status": {"candidate_diagnostics_available": False},
        "candidate_diagnostics": {"available": False},
        "readiness_warnings": ["candidate_diagnostics_missing"],
    })
    write_picks(tmp_path / "picks_log.csv", [])
    write_json(tmp_path / f"theme_pick_bridge_{date}.json", {
        "themes": [
            {"theme": "ai", "leaders": ["AAPL", "NVDA"]}
        ]
    })

    report = build_candidate_lifecycle(date_str=date, data_dir=tmp_path)
    rows = by_ticker(report)

    assert rows["AAPL"]["lifecycle_state"] == "diagnostics_unavailable"
    assert rows["NVDA"]["lifecycle_state"] == "diagnostics_unavailable"
    assert "pipeline_incomplete" in rows["AAPL"]["reason"]


def test_candidate_lifecycle_marks_missing_from_universe_when_diagnostics_available(tmp_path):
    date = "2026-05-09"
    write_json(tmp_path / f"data_readiness_{date}.json", {
        "official_pick_readiness_status": "ready_no_qualified_candidates",
        "no_pick_classification": "strategy_driven_no_qualified_candidates",
        "input_status": {"candidate_diagnostics_available": True},
        "candidate_diagnostics": {"available": True},
        "readiness_warnings": [],
    })
    write_picks(tmp_path / "picks_log.csv", [])
    write_json(tmp_path / f"daily_picks_candidate_rejections_{date}.json", {
        "diagnostics_available": True,
        "diagnostics": {
            "pre_hard_block_candidates": [],
            "hard_blocked_candidates": [],
            "rejected_candidates": [],
            "selected_picks": [],
        },
    })
    write_json(tmp_path / f"theme_pick_bridge_{date}.json", {
        "themes": [
            {"theme": "security", "leaders": ["KTOS"]}
        ]
    })

    report = build_candidate_lifecycle(date_str=date, data_dir=tmp_path)
    rows = by_ticker(report)

    assert rows["KTOS"]["lifecycle_state"] == "missing_from_universe"


def test_candidate_lifecycle_falls_back_to_theme_discovery_when_no_bridge(tmp_path):
    date = "2026-05-09"
    write_json(tmp_path / f"data_readiness_{date}.json", {
        "official_pick_readiness_status": "not_ready_diagnostics_missing",
        "no_pick_classification": "diagnostics_missing",
        "input_status": {"candidate_diagnostics_available": False},
        "candidate_diagnostics": {"available": False},
        "readiness_warnings": [],
    })
    write_picks(tmp_path / "picks_log.csv", [])
    write_json(tmp_path / f"theme_discovery_{date}.json", {
        "themes": [
            {"theme": "semi", "tickers": ["NVDA", "TSM"]}
        ]
    })

    report = build_candidate_lifecycle(date_str=date, data_dir=tmp_path)

    assert report["input_status"]["theme_leader_source"]["source_type"] == "theme_discovery"
    rows = by_ticker(report)
    assert rows["NVDA"]["themes"] == ["semi"]


def test_candidate_lifecycle_writes_outputs(tmp_path):
    date = "2026-05-09"
    write_json(tmp_path / f"data_readiness_{date}.json", {
        "official_pick_readiness_status": "not_ready_pipeline_incomplete",
        "no_pick_classification": "pipeline_incomplete",
        "input_status": {"candidate_diagnostics_available": False},
        "candidate_diagnostics": {"available": False},
        "readiness_warnings": [],
    })
    write_picks(tmp_path / "picks_log.csv", [])
    write_json(tmp_path / f"theme_pick_bridge_{date}.json", {
        "themes": [{"theme": "ai", "leaders": ["AAPL"]}]
    })

    report = build_candidate_lifecycle(date_str=date, data_dir=tmp_path)
    json_path, md_path = write_outputs(report, data_dir=tmp_path)

    assert json_path.name == "candidate_lifecycle_2026-05-09.json"
    assert md_path.name == "candidate_lifecycle_2026-05-09.md"

    saved = json.loads(json_path.read_text())
    assert saved["observe_only"] is True

    md = md_path.read_text()
    assert "Candidate Lifecycle Ledger" in md
    assert "diagnostics_unavailable" in md
    assert "Does not alter official scoring" in md


def test_format_markdown_handles_empty_report(tmp_path):
    date = "2026-05-09"
    write_picks(tmp_path / "picks_log.csv", [])
    report = build_candidate_lifecycle(date_str=date, data_dir=tmp_path)
    md = format_markdown(report)

    assert "Candidate Lifecycle Ledger" in md
    assert "No candidates reconstructed" in md or "No candidate lifecycle rows" in md
