import csv
import json
from pathlib import Path

from scripts.build_data_readiness_report import (
    build_data_readiness_report,
    classify_no_pick,
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


def test_data_readiness_reports_healthy_official_pick_day(tmp_path):
    date = "2026-05-09"
    write_jsonl(tmp_path / f"daily_picks_run_status_{date}.jsonl", [
        {"date": date, "status": "completed", "official_pick_count": 1}
    ])
    write_picks(tmp_path / "picks_log.csv", [
        {"pick_date": date, "ticker": "NVDA", "company": "NVIDIA", "tag": "AI"}
    ])
    write_json(tmp_path / f"daily_picks_candidate_rejections_{date}.json", {
        "diagnostics_available": True,
        "diagnostics": {
            "pre_hard_block_candidates": [],
            "hard_blocked_candidates": [],
            "rejected_candidates": [],
            "selected_picks": [{"ticker": "NVDA"}],
        },
    })

    report = build_data_readiness_report(date_str=date, data_dir=tmp_path)

    assert report["observe_only"] is True
    assert report["production_scoring_effect"] is False
    assert report["official_pick_count"] == 1
    assert report["official_pick_tickers"] == ["NVDA"]
    assert report["official_pick_readiness_status"] == "official_picks_available"
    assert report["no_pick_classification"] == "strategy_driven_no_qualified_candidates"


def test_data_readiness_classifies_missing_daily_artifacts_as_pipeline_incomplete(tmp_path):
    date = "2026-05-09"
    write_picks(tmp_path / "picks_log.csv", [])
    write_json(tmp_path / f"theme_pick_bridge_{date}.json", {
        "artifact": "theme_pick_bridge",
        "input_status": {
            "daily_rejection_artifact_exists": False,
            "watch_only_lane_count": 0,
            "picks_log_official_rows_for_date": 0,
        },
    })

    report = build_data_readiness_report(date_str=date, data_dir=tmp_path)

    assert report["official_pick_count"] == 0
    assert report["input_status"]["daily_run_status_available"] is False
    assert report["input_status"]["rejection_artifact_available"] is False
    assert report["no_pick_classification"] == "pipeline_incomplete"
    assert report["official_pick_readiness_status"] == "not_ready_pipeline_incomplete"
    assert "daily_run_status_missing" in report["readiness_warnings"]
    assert "candidate_rejection_artifact_missing" in report["readiness_warnings"]
    assert "theme_bridge_reports_missing_daily_inputs" in report["readiness_warnings"]


def test_data_readiness_detects_provider_failure_from_no_forward_bars(tmp_path):
    date = "2026-05-09"
    write_jsonl(tmp_path / f"daily_picks_run_status_{date}.jsonl", [
        {"date": date, "status": "completed", "official_pick_count": 0}
    ])
    write_json(tmp_path / f"daily_picks_candidate_rejections_{date}.json", {
        "diagnostics_available": True,
        "diagnostics": {
            "pre_hard_block_candidates": [],
            "hard_blocked_candidates": [],
        },
    })
    write_jsonl(tmp_path / f"opening_range_observations_{date}.jsonl", [
        {
            "ticker": "TSLA",
            "opening_range_quality_status": "data_insufficient_no_forward_bars",
            "opening_range_volume_status": "not_evaluable_no_forward_bars",
        }
    ])
    write_picks(tmp_path / "picks_log.csv", [])

    report = build_data_readiness_report(date_str=date, data_dir=tmp_path)

    assert report["watch_only_lanes"]["opening_range_observations"]["no_forward_bars_count"] == 1
    assert report["data_provider_status"] == "provider_or_market_data_failure_evidence_detected"
    assert report["no_pick_classification"] == "data_provider_failure"
    assert report["official_pick_readiness_status"] == "not_ready_data_provider_failure"
    assert "opening_range_no_forward_bars_detected" in report["readiness_warnings"]


def test_data_readiness_marks_missing_diagnostics(tmp_path):
    date = "2026-05-09"
    write_jsonl(tmp_path / f"daily_picks_run_status_{date}.jsonl", [
        {"date": date, "status": "completed", "official_pick_count": 0}
    ])
    write_picks(tmp_path / "picks_log.csv", [])

    report = build_data_readiness_report(date_str=date, data_dir=tmp_path)

    assert report["no_pick_classification"] == "diagnostics_missing"
    assert report["official_pick_readiness_status"] == "not_ready_diagnostics_missing"
    assert "candidate_diagnostics_missing" in report["readiness_warnings"]


def test_classify_no_pick_never_invents_strategy_when_pipeline_missing():
    classification = classify_no_pick(
        official_pick_count=0,
        daily_run_status_available=False,
        no_pick_report_available=False,
        rejection_artifact_available=False,
        candidate_diagnostics_available=False,
        provider_failure_evidence=False,
        watch_only_lane_count=0,
        theme_bridge_available=True,
    )

    assert classification == "pipeline_incomplete"


def test_data_readiness_writes_outputs(tmp_path):
    date = "2026-05-09"
    write_jsonl(tmp_path / f"daily_picks_run_status_{date}.jsonl", [
        {"date": date, "status": "completed", "official_pick_count": 0}
    ])
    write_json(tmp_path / f"daily_picks_candidate_rejections_{date}.json", {
        "diagnostics_available": True,
        "diagnostics": {
            "pre_hard_block_candidates": [],
            "hard_blocked_candidates": [],
        },
    })
    write_picks(tmp_path / "picks_log.csv", [])

    report = build_data_readiness_report(date_str=date, data_dir=tmp_path)
    json_path, md_path = write_outputs(report, data_dir=tmp_path)

    assert json_path.name == "data_readiness_2026-05-09.json"
    assert md_path.name == "data_readiness_2026-05-09.md"

    saved = json.loads(json_path.read_text())
    assert saved["observe_only"] is True

    md = md_path.read_text()
    assert "Daily Data Readiness Report" in md
    assert "No-pick classification" in md
    assert "Observe-only readiness report" in md


def test_format_markdown_includes_safety_and_warnings(tmp_path):
    date = "2026-05-09"
    write_picks(tmp_path / "picks_log.csv", [])
    report = build_data_readiness_report(date_str=date, data_dir=tmp_path)
    md = format_markdown(report)

    assert "Daily Data Readiness Report" in md
    assert "Readiness Warnings" in md
    assert "Does not alter official scoring" in md
