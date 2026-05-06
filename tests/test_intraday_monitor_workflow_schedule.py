from pathlib import Path


WORKFLOW = Path(".github/workflows/intraday_monitor.yml")


def test_intraday_workflow_has_targeted_opening_range_cron():
    text = WORKFLOW.read_text()

    assert "35,45 13-14 * * 1-5" in text
    assert "0,30 13-21 * * 1-5" in text


def test_intraday_workflow_skips_off_target_opening_range_fires():
    text = WORKFLOW.read_text()

    assert "Off-target opening-range fire" in text
    assert '[ "$ET_MIN" = "35" ] || [ "$ET_MIN" = "45" ]' in text
    assert '[ "$ET_HOUR" != "09" ]' in text


def test_intraday_workflow_documents_1000_et_followup():
    text = WORKFLOW.read_text()

    assert "10:00 ET opening-range follow-up" in text
