import json
from pathlib import Path

from scripts.check_daily_artifact_completeness import (
    build_artifact_completeness_report,
    format_markdown,
    write_outputs,
)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def checks_by_key(report: dict) -> dict:
    return {row["key"]: row for row in report["checks"]}


def test_artifact_completeness_marks_missing_critical_files(tmp_path):
    date = "2026-05-09"
    write_json(tmp_path / f"data_readiness_{date}.json", {"official_pick_count": 0})
    write_json(tmp_path / f"candidate_lifecycle_{date}.json", {"artifact": "candidate_lifecycle"})
    write_json(tmp_path / f"theme_discovery_{date}.json", {"artifact": "theme_discovery"})
    write_json(tmp_path / f"theme_pick_bridge_{date}.json", {"artifact": "theme_pick_bridge"})

    report = build_artifact_completeness_report(date_str=date, data_dir=tmp_path)
    checks = checks_by_key(report)

    assert report["completeness_status"] == "missing_critical_artifacts"
    assert checks["daily_run_status"]["severity"] == "critical"
    assert checks["no_pick_report"]["severity"] == "critical"
    assert checks["candidate_rejections"]["severity"] == "critical"
    assert checks["data_readiness"]["severity"] == "ok"
    assert checks["candidate_lifecycle"]["severity"] == "ok"
    assert "daily_run_status" in report["summary"]["missing_critical"]
    assert "candidate_rejections" in report["summary"]["missing_critical"]


def test_artifact_completeness_treats_no_pick_report_as_conditional(tmp_path):
    date = "2026-05-09"
    write_json(tmp_path / f"data_readiness_{date}.json", {"official_pick_count": 1})
    write_jsonl(tmp_path / f"daily_picks_run_status_{date}.jsonl", [{"status": "completed"}])
    write_json(tmp_path / f"daily_picks_candidate_rejections_{date}.json", {"diagnostics": {}})
    write_json(tmp_path / f"candidate_lifecycle_{date}.json", {"artifact": "candidate_lifecycle"})

    report = build_artifact_completeness_report(date_str=date, data_dir=tmp_path)
    checks = checks_by_key(report)

    assert checks["no_pick_report"]["required"] is False
    assert checks["no_pick_report"]["severity"] == "warning"


def test_artifact_completeness_reports_present_empty_jsonl_as_warning(tmp_path):
    date = "2026-05-09"
    write_json(tmp_path / f"data_readiness_{date}.json", {"official_pick_count": 0})
    write_jsonl(tmp_path / f"daily_picks_run_status_{date}.jsonl", [])
    write_json(tmp_path / f"daily_picks_no_pick_report_{date}.json", {"artifact": "no_pick"})
    write_json(tmp_path / f"daily_picks_candidate_rejections_{date}.json", {"diagnostics": {}})
    write_json(tmp_path / f"candidate_lifecycle_{date}.json", {"artifact": "candidate_lifecycle"})

    report = build_artifact_completeness_report(date_str=date, data_dir=tmp_path)
    checks = checks_by_key(report)

    assert checks["daily_run_status"]["status"] == "present_empty"
    assert checks["daily_run_status"]["severity"] == "warning"


def test_artifact_completeness_complete_when_required_artifacts_present(tmp_path):
    date = "2026-05-09"
    write_json(tmp_path / f"data_readiness_{date}.json", {"official_pick_count": 0})
    write_jsonl(tmp_path / f"daily_picks_run_status_{date}.jsonl", [{"status": "completed"}])
    write_json(tmp_path / f"daily_picks_no_pick_report_{date}.json", {"artifact": "no_pick"})
    write_json(tmp_path / f"daily_picks_candidate_rejections_{date}.json", {"diagnostics": {}})
    write_json(tmp_path / f"candidate_lifecycle_{date}.json", {"artifact": "candidate_lifecycle"})
    write_json(tmp_path / f"theme_discovery_{date}.json", {"artifact": "theme_discovery"})
    write_json(tmp_path / f"theme_pick_bridge_{date}.json", {"artifact": "theme_pick_bridge"})
    write_jsonl(tmp_path / f"late_daily_ideas_{date}.jsonl", [{"ticker": "A"}])
    write_jsonl(tmp_path / f"opening_range_observations_{date}.jsonl", [{"ticker": "B"}])
    write_jsonl(tmp_path / f"intraday_momentum_observations_{date}.jsonl", [{"ticker": "C"}])

    report = build_artifact_completeness_report(date_str=date, data_dir=tmp_path)

    assert report["completeness_status"] == "complete"
    assert report["summary"]["missing_critical_count"] == 0
    assert report["summary"]["warning_count"] == 0


def test_artifact_completeness_writes_outputs(tmp_path):
    date = "2026-05-09"
    write_json(tmp_path / f"data_readiness_{date}.json", {"official_pick_count": 0})
    report = build_artifact_completeness_report(date_str=date, data_dir=tmp_path)
    json_path, md_path = write_outputs(report, data_dir=tmp_path)

    assert json_path.name == "artifact_completeness_2026-05-09.json"
    assert md_path.name == "artifact_completeness_2026-05-09.md"

    saved = json.loads(json_path.read_text())
    assert saved["observe_only"] is True
    assert saved["production_scoring_effect"] is False

    md = md_path.read_text()
    assert "Daily Artifact Completeness Report" in md
    assert "Missing Critical Artifacts" in md
    assert "Does not alter official scoring" in md


def test_format_markdown_lists_artifact_matrix(tmp_path):
    date = "2026-05-09"
    write_json(tmp_path / f"data_readiness_{date}.json", {"official_pick_count": 0})
    report = build_artifact_completeness_report(date_str=date, data_dir=tmp_path)
    md = format_markdown(report)

    assert "Artifact Matrix" in md
    assert "daily_run_status" in md
    assert "candidate_rejections" in md
