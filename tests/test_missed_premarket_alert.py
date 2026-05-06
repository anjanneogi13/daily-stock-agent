from datetime import datetime
from zoneinfo import ZoneInfo

from scripts.send_missed_premarket_alert import build_message


def test_missed_premarket_alert_is_not_actionable_daily_picks():
    msg = build_message(datetime(2026, 5, 6, 9, 45, tzinfo=ZoneInfo("America/New_York")))

    assert "Premarket window missed" in msg
    assert "09:45 ET" in msg
    assert "Official daily picks were *not sent*" in msg
    assert "No normal premarket buy entries are actionable" in msg
    assert "intraday monitor alerts" in msg
