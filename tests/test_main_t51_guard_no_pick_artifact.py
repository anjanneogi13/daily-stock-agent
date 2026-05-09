"""Priority 17.1 — main.py T51 market-closed guard must write the official
no-pick guard artifact, not just bare-return.

Regression test for the gap discovered during the 2026-05-09 Lane 1 audit:
the daily-picks workflow YAML correctly invoked
scripts/write_guard_no_pick_artifact.py on closed-market days, but main.py's
own T51 guard early-returned without writing any artifact. Any caller that
bypassed the workflow (manual run, codespace, future tools) silently
violated the Priority 17 contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_write_guard_no_pick_artifact_for_main_writes_valid_artifact(tmp_path, monkeypatch):
    """The helper must write a valid official no-pick artifact for
    NO_PICK_MARKET_CLOSED that passes the canonical validator."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()

    import main
    result = main._write_guard_no_pick_artifact_for_main(
        cause="NO_PICK_MARKET_CLOSED",
        reason="US market closed (Saturday); next trading day 2026-05-11.",
    )
    assert result is True

    json_files = list((tmp_path / "data").glob("daily_picks_no_pick_report_*.json"))
    md_files = list((tmp_path / "data").glob("daily_picks_no_pick_report_*.md"))
    assert json_files, "helper must write the official no-pick JSON artifact"
    assert md_files, "helper must write the official no-pick Markdown artifact"

    payload = json.loads(json_files[0].read_text())
    assert payload["decision"] == "official_no_pick"
    assert payload["primary_no_pick_cause"] == "NO_PICK_MARKET_CLOSED"
    assert payload["paper_trading_enabled"] is False
    assert payload["live_trading_enabled"] is False
    assert payload.get("decision_id"), "decision_id must be set for traceability"

    from scripts.validate_daily_no_pick import validate_no_pick_report
    assert validate_no_pick_report(payload) == [], "guard artifact must pass official validator"


def test_write_guard_no_pick_artifact_for_main_never_raises_on_writer_failure(monkeypatch, tmp_path):
    """Safety contract: the helper must swallow writer failures so the
    calling guard's hard-stop return remains the actual safety stop."""
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
        cause="NO_PICK_MARKET_CLOSED",
        reason="simulated failure path",
    )
    assert result is False


def test_main_t51_guard_invokes_helper(monkeypatch, tmp_path):
    """Wiring regression: the T51 market-closed guard inside main.py's run()
    function must invoke _write_guard_no_pick_artifact_for_main with cause
    NO_PICK_MARKET_CLOSED.

    Without this assertion the wiring can silently rot — the helper exists
    and helper-level tests pass, but the guard fails to call it (the exact
    bug found during the 2026-05-09 Lane 1 audit)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()

    import main

    calls = []

    def _spy(*, cause, reason=""):
        calls.append({"cause": cause, "reason": reason})
        return True

    # Stub config + dotenv so run() does not need a real config.yaml in tmp_path.
    monkeypatch.setattr(main, "load_config", lambda *a, **k: {})
    monkeypatch.setattr(main, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr(main, "_is_td", lambda *a, **k: False)
    monkeypatch.setattr(main, "_why_closed", lambda *a, **k: "weekend")
    monkeypatch.setattr(main, "_next_td", lambda *a, **k: "2026-05-11")
    monkeypatch.setattr(main, "_write_guard_no_pick_artifact_for_main", _spy)

    main.run()

    assert calls, "T51 guard must invoke _write_guard_no_pick_artifact_for_main"
    assert calls[0]["cause"] == "NO_PICK_MARKET_CLOSED"
