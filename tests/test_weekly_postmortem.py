"""T42: weekly_review formally exposes a post-mortem section."""
from src.weekly_review import build_report, format_telegram


def test_weekly_includes_postmortem_header():
    text = format_telegram(build_report())
    assert "Weekly Post-Mortem" in text
    # Must appear before recommended actions, after metrics block
    pm_idx  = text.index("Weekly Post-Mortem")
    rec_idx = text.index("Recommended action")
    assert pm_idx < rec_idx


def test_postmortem_section_has_what_worked_and_failed():
    text = format_telegram(build_report())
    pm_idx = text.index("Weekly Post-Mortem")
    after = text[pm_idx:]
    assert "What worked" in after
