"""Priority 17.2 — main.py agent-paused and duplicate-already-logged guards
must write formal official no-pick artifacts, not just bare-return.

Completes the follow-up deferred from the 2026-05-09 Lane 1 audit (P17.1):
the T51 market-closed guard was wired, but the auto-pause guard and the
same-day multi-fire guard still early-returned without recording an official
decision. This left days with no official pick artifact and no official
no-pick artifact — the exact Lane 1 failure case.

Safety invariants tested here:

- exactly one official outcome per day: the writer must skip when official
  picks are already logged or when an earlier no-pick decision exists,
- the helper never raises (bare return stays the hard stop),
- paper/live trading flags remain false in every artifact.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest


def _write_picks_log(path: Path, rows: list[dict]) -> None:
    fieldnames = sorted({key for row in rows for key in row}) or ["pick_date", "ticker"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _today_et() -> str:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")


# ─── writer-level: new causes are supported and validate ───────────────────

@pytest.mark.parametrize("cause", ["NO_PICK_AGENT_PAUSED", "NO_PICK_DUPLICATE_ALREADY_LOGGED"])
def test_writer_supports_new_p17_2_causes(tmp_path, cause):
    from scripts.validate_daily_no_pick import validate_no_pick_report
    from scripts.write_guard_no_pick_artifact import write_guard_no_pick_artifact

    result = write_guard_no_pick_artifact(
        date_str="2026-05-11",
        cause=cause,
        data_dir=tmp_path,
    )
    assert result["valid"] is True

    payload = json.loads((tmp_path / "daily_picks_no_pick_report_2026-05-11.json").read_text())
    assert payload["decision"] == "official_no_pick"
    assert payload["primary_no_pick_cause"] == cause
    assert payload["paper_trading_enabled"] is False
    assert payload["live_trading_enabled"] is False
    assert validate_no_pick_report(payload) == []
    assert (tmp_path / "daily_picks_no_pick_report_2026-05-11.md").exists()


@pytest.mark.parametrize("cause", ["NO_PICK_AGENT_PAUSED", "NO_PICK_DUPLICATE_ALREADY_LOGGED"])
def test_contract_allows_new_p17_2_causes(cause):
    from src.premarket_decision_contract import OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES

    assert cause in OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES


# ─── helper skip flags: exactly one official outcome per day ───────────────

def test_helper_skips_when_official_picks_already_logged(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    today = _today_et()
    _write_picks_log(
        tmp_path / "data" / "picks_log.csv",
        [{"pick_date": today, "ticker": "AAPL", "status": "open"}],
    )

    import main

    result = main._write_guard_no_pick_artifact_for_main(
        cause="NO_PICK_DUPLICATE_ALREADY_LOGGED",
        reason="duplicate run",
        skip_if_official_picks_logged=True,
        skip_if_no_pick_artifact_exists=True,
    )
    assert result is False, "must not write a no-pick artifact on a pick day"
    assert not list((tmp_path / "data").glob("daily_picks_no_pick_report_*.json"))


def test_helper_skips_when_no_pick_artifact_already_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    today = _today_et()
    (tmp_path / "data").mkdir()
    existing = tmp_path / "data" / f"daily_picks_no_pick_report_{today}.json"
    existing.write_text(json.dumps({"primary_no_pick_cause": "NO_PICK_WINDOW_MISSED"}))

    import main

    result = main._write_guard_no_pick_artifact_for_main(
        cause="NO_PICK_AGENT_PAUSED",
        reason="paused",
        skip_if_official_picks_logged=True,
        skip_if_no_pick_artifact_exists=True,
    )
    assert result is False, "first official no-pick decision must win"
    payload = json.loads(existing.read_text())
    assert payload["primary_no_pick_cause"] == "NO_PICK_WINDOW_MISSED", "existing artifact must be preserved"


def test_helper_writes_when_only_watch_only_rows_logged(tmp_path, monkeypatch):
    """Watch-only rows are not official picks: the official decision is still
    missing and the duplicate-guard artifact must be written."""
    monkeypatch.chdir(tmp_path)
    today = _today_et()
    _write_picks_log(
        tmp_path / "data" / "picks_log.csv",
        [{"pick_date": today, "ticker": "ZIM", "watch_only": "True", "tag": "late_watch_only"}],
    )

    import main

    result = main._write_guard_no_pick_artifact_for_main(
        cause="NO_PICK_DUPLICATE_ALREADY_LOGGED",
        reason="duplicate run with only watch-only rows",
        skip_if_official_picks_logged=True,
        skip_if_no_pick_artifact_exists=True,
    )
    assert result is True

    files = list((tmp_path / "data").glob("daily_picks_no_pick_report_*.json"))
    assert files, "official no-pick artifact must be written"
    payload = json.loads(files[0].read_text())
    assert payload["primary_no_pick_cause"] == "NO_PICK_DUPLICATE_ALREADY_LOGGED"

    from scripts.validate_daily_no_pick import validate_no_pick_report

    assert validate_no_pick_report(payload) == []


# ─── wiring: guards inside run() must invoke the helper ────────────────────

def _stub_main_pre_guard(monkeypatch, main):
    monkeypatch.setattr(main, "load_config", lambda *a, **k: {"output": {"top_n_picks": 5, "min_score": 0.6}})
    monkeypatch.setattr(main, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr(main, "_is_td", lambda *a, **k: True)


def test_agent_paused_guard_invokes_helper(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()

    import main

    calls = []

    def _spy(cause, reason="", **kwargs):
        calls.append({"cause": cause, "reason": reason, **kwargs})
        return True

    _stub_main_pre_guard(monkeypatch, main)
    monkeypatch.setattr(
        main,
        "_is_paused",
        lambda *a, **k: {"paused": True, "reason": "3 SL in 5d", "until": "2026-05-15", "days_remaining": 3},
    )
    monkeypatch.setattr(main, "_write_guard_no_pick_artifact_for_main", _spy)

    main.run()

    assert calls, "agent-paused guard must invoke _write_guard_no_pick_artifact_for_main"
    assert calls[0]["cause"] == "NO_PICK_AGENT_PAUSED"
    assert calls[0].get("skip_if_official_picks_logged") is True
    assert calls[0].get("skip_if_no_pick_artifact_exists") is True


def test_duplicate_already_logged_guard_invokes_helper(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    from datetime import date

    today_local = date.today().strftime("%Y-%m-%d")
    _write_picks_log(
        tmp_path / "data" / "picks_log.csv",
        [{"pick_date": today_local, "ticker": "AAPL", "status": "open"}],
    )

    import main

    calls = []

    def _spy(cause, reason="", **kwargs):
        calls.append({"cause": cause, "reason": reason, **kwargs})
        return True

    _stub_main_pre_guard(monkeypatch, main)
    monkeypatch.setattr(main, "_is_paused", lambda *a, **k: {"paused": False})
    # Market-guard calls before the duplicate guard must not hit the network.
    monkeypatch.setattr(main, "vix_level", lambda *a, **k: 15.0)
    monkeypatch.setattr(main, "spy_trend", lambda *a, **k: {"above_50dma": True, "above_200dma": True})
    monkeypatch.setattr(main, "sector_strength", lambda *a, **k: {})
    monkeypatch.setattr(main, "_write_guard_no_pick_artifact_for_main", _spy)

    main.run()

    assert calls, "duplicate guard must invoke _write_guard_no_pick_artifact_for_main"
    assert calls[0]["cause"] == "NO_PICK_DUPLICATE_ALREADY_LOGGED"
    assert calls[0].get("skip_if_official_picks_logged") is True
    assert calls[0].get("skip_if_no_pick_artifact_exists") is True


def test_helper_never_raises_on_writer_failure_with_skip_flags(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()

    import main

    def _boom(**kwargs):
        raise RuntimeError("simulated writer failure")

    monkeypatch.setattr(
        "scripts.write_guard_no_pick_artifact.write_guard_no_pick_artifact",
        _boom,
    )
    result = main._write_guard_no_pick_artifact_for_main(
        cause="NO_PICK_AGENT_PAUSED",
        reason="simulated failure path",
        skip_if_official_picks_logged=True,
        skip_if_no_pick_artifact_exists=True,
    )
    assert result is False
