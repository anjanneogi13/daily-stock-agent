"""Bug #17A (2026-05-05): persist smell faculty verdicts to picks_log.csv.

Problem:
  main.py runs smell_faculty in OBSERVE mode and attaches warning details to
  p["smell_warnings"], but those details are not written to picks_log.csv.
  check_enforcement_readiness therefore reports smell_verdicts_not_persisted.

Contract:
  - pick_logger.FIELDS contains smell persistence columns.
  - main.py serializes p["smell_warnings"] into picks_for_log.
  - pick_logger.log_picks writes those smell fields.
"""
from pathlib import Path

from src.pick_logger import FIELDS


MAIN = Path("main.py")
LOGGER = Path("src/pick_logger.py")

SMELL_FIELDS = {
    "smell_codes",
    "smell_severities",
    "smell_messages",
}


def test_pick_logger_fields_include_smell_columns():
    missing = sorted(SMELL_FIELDS - set(FIELDS))
    assert missing == [], f"Missing smell persistence fields from pick_logger.FIELDS: {missing}"


def test_main_serializes_smell_warnings_for_log():
    src = MAIN.read_text()
    assert "smell_codes" in src
    assert "smell_severities" in src
    assert "smell_messages" in src
    assert "smell_warnings" in src


def test_pick_logger_writes_smell_columns():
    src = LOGGER.read_text()
    assert '"smell_codes": p.get("smell_codes", "")' in src
    assert '"smell_severities": p.get("smell_severities", "")' in src
    assert '"smell_messages": p.get("smell_messages", "")' in src
