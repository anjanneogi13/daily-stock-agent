"""Bug #17B (2026-05-05): smell enforcement readiness must use persisted fields.

After Bug #17A, picks_log can persist smell_codes/smell_severities/smell_messages.
check_enforcement_readiness.py should consume those fields instead of always
returning smell_verdicts_not_persisted.
"""

from scripts.check_enforcement_readiness import check_smell_enforce


def closed_row(smell_codes="", status="sl_hit", r_multiple="-1.0"):
    return {
        "pick_date": "2026-05-04",
        "evaluation_status": status,
        "smell_codes": smell_codes,
        "smell_severities": "CRITICAL" if smell_codes else "",
        "smell_messages": "test smell" if smell_codes else "",
        "r_multiple": r_multiple,
    }


def test_smell_readiness_reports_schema_blocker_when_field_missing():
    rows = [{"evaluation_status": "sl_hit", "r_multiple": "-1.0"}]

    result = check_smell_enforce(rows)

    assert result["ready"] is False
    assert result["n_observed"] == 0
    assert "smell_verdicts_not_persisted" in result["blockers"]


def test_smell_readiness_counts_persisted_smell_rows():
    rows = [closed_row("tight_stop") for _ in range(3)]

    result = check_smell_enforce(rows)

    assert result["ready"] is False
    assert result["n_observed"] == 3
    assert "smell_verdicts_not_persisted" not in result["blockers"]
    assert any("n=3 < 30" in b for b in result["blockers"])


def test_smell_readiness_ready_when_enough_smells_and_low_false_positive_rate():
    # 30 smell-tagged closed rows, all bad outcomes => FP rate 0%.
    rows = [closed_row("tight_stop", status="sl_hit", r_multiple="-1.0") for _ in range(30)]

    result = check_smell_enforce(rows)

    assert result["ready"] is True
    assert result["n_observed"] == 30
    assert result["smell_false_positive_rate"] == 0.0
    assert result["blockers"] == []


def test_smell_readiness_blocks_when_false_positive_rate_too_high():
    # 24 bad + 6 good = 20% FP. Threshold is strict: must be < 20%.
    rows = [closed_row("tight_stop", status="sl_hit", r_multiple="-1.0") for _ in range(24)]
    rows += [closed_row("tight_stop", status="tp_hit", r_multiple="1.5") for _ in range(6)]

    result = check_smell_enforce(rows)

    assert result["ready"] is False
    assert result["n_observed"] == 30
    assert result["smell_false_positive_rate"] == 0.2
    assert any("false-positive rate" in b for b in result["blockers"])
