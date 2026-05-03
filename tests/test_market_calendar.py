"""T51: US Market Calendar — weekends, holidays, half-days, renewal."""
from datetime import date, datetime
import pytest
from src import market_calendar as mc


# ─── Weekend detection ─────────────────────────────────────────
def test_saturday_is_weekend():
    assert mc.is_weekend(date(2026, 5, 2))   # Saturday
    assert mc.is_weekend("2026-05-02")
    assert mc.is_weekend(datetime(2026, 5, 2, 10, 0))


def test_sunday_is_weekend():
    assert mc.is_weekend(date(2026, 5, 3))   # Sunday


def test_monday_is_not_weekend():
    assert not mc.is_weekend(date(2026, 5, 4))  # Monday


def test_friday_is_not_weekend():
    assert not mc.is_weekend(date(2026, 5, 1))  # Friday


# ─── Holiday detection ─────────────────────────────────────────
def test_new_years_2026_is_holiday():
    assert mc.is_holiday("2026-01-01")


def test_memorial_day_2026_is_holiday():
    assert mc.is_holiday("2026-05-25")


def test_july_3_2026_is_holiday_when_jul_4_saturday():
    # Jul 4 2026 = Saturday → market observes Fri Jul 3
    assert mc.is_holiday("2026-07-03")


def test_christmas_2026_is_holiday():
    assert mc.is_holiday("2026-12-25")


def test_random_weekday_is_not_holiday():
    assert not mc.is_holiday("2026-05-06")  # Wed
    assert not mc.is_holiday("2026-08-12")  # Wed


# ─── Trading day = NOT weekend AND NOT holiday ─────────────────
def test_trading_day_normal_weekday():
    assert mc.is_trading_day("2026-05-06")  # Wed


def test_not_trading_day_on_weekend():
    assert not mc.is_trading_day("2026-05-02")  # Sat


def test_not_trading_day_on_holiday():
    assert not mc.is_trading_day("2026-05-25")  # Memorial Day Mon
    assert not mc.is_trading_day("2026-12-25")  # Christmas Fri


# ─── Half-days ─────────────────────────────────────────────────
def test_black_friday_2026_is_early_close():
    assert mc.is_early_close("2026-11-27")


def test_christmas_eve_2026_is_early_close():
    assert mc.is_early_close("2026-12-24")


def test_normal_day_not_early_close():
    assert not mc.is_early_close("2026-05-06")


# ─── reason_market_closed ──────────────────────────────────────
def test_reason_weekend():
    assert mc.reason_market_closed("2026-05-02") == "weekend"


def test_reason_holiday():
    assert mc.reason_market_closed("2026-05-25") == "holiday"


def test_reason_open():
    assert mc.reason_market_closed("2026-05-06") is None


# ─── Next/previous trading day navigation ──────────────────────
def test_next_trading_day_skips_weekend():
    # Friday May 1, 2026 → next trading = Monday May 4
    assert mc.next_trading_day("2026-05-01") == date(2026, 5, 4)


def test_next_trading_day_skips_holiday():
    # Friday May 22 → Mon May 25 = Memorial Day → next = Tue May 26
    assert mc.next_trading_day("2026-05-22") == date(2026, 5, 26)


def test_next_trading_day_skips_weekend_AND_holiday():
    # Wed Dec 23 2026 → Thu Dec 24 (early close) IS trading
    assert mc.next_trading_day("2026-12-23") == date(2026, 12, 24)
    # Thu Dec 24 → Fri Dec 25 (holiday) → Sat → Sun → Mon Dec 28
    assert mc.next_trading_day("2026-12-24") == date(2026, 12, 28)


def test_previous_trading_day():
    assert mc.previous_trading_day("2026-05-04") == date(2026, 5, 1)
    assert mc.previous_trading_day("2026-05-26") == date(2026, 5, 22)


# ─── Annual renewal awareness ──────────────────────────────────
def test_cached_years_includes_2026_2027_2028():
    years = mc.cached_years()
    assert 2026 in years
    assert 2027 in years
    assert 2028 in years


def test_years_remaining_today():
    # As of 2026-05-03, max year cached = 2028, so 2 years remaining
    rem = mc.years_remaining("2026-05-03")
    assert rem == 2


def test_needs_renewal_false_when_plenty():
    assert not mc.needs_renewal(threshold_years=1, today="2026-05-03")


def test_needs_renewal_true_when_close_to_limit():
    # In late 2028, only 0 full years remain
    assert mc.needs_renewal(threshold_years=1, today="2028-06-01")


def test_renewal_message_only_when_needed():
    assert mc.renewal_message("2026-05-03") is None
    msg = mc.renewal_message("2028-06-01")
    assert msg is not None
    assert "2030" in msg or "2028" in msg


# ─── market_status_today snapshot ──────────────────────────────
def test_status_normal_trading_day():
    s = mc.market_status_today("2026-05-06")
    assert s["is_trading_day"] is True
    assert s["closed_reason"] is None


def test_status_weekend():
    s = mc.market_status_today("2026-05-02")
    assert s["is_trading_day"] is False
    assert s["is_weekend"] is True
    assert s["closed_reason"] == "weekend"


def test_status_holiday():
    s = mc.market_status_today("2026-05-25")
    assert s["is_trading_day"] is False
    assert s["is_holiday"] is True
    assert s["closed_reason"] == "holiday"
    assert s["next_open"] == "2026-05-26"


# ─── Cross-year boundaries ─────────────────────────────────────
def test_navigates_across_year_boundary():
    # Dec 31 2026 (Thu) → Jan 1 2027 (Fri, holiday) → Mon Jan 4 2027
    assert mc.next_trading_day("2026-12-31") == date(2027, 1, 4)


def test_holidays_present_for_all_three_years():
    # Sanity: at least 9 holidays per year (NYSE has 9-10 typically)
    for yr in (2026, 2027, 2028):
        ys = [d for d in mc.US_MARKET_HOLIDAYS if d.startswith(str(yr))]
        assert len(ys) >= 8, f"year {yr} has only {len(ys)} holidays"



# ─── T51b — Escalating renewal urgency ─────────────────────────
def test_renewal_urgency_none_when_fresh():
    assert mc.renewal_urgency("2026-05-03") == "none"


def test_renewal_urgency_soft_when_18mo_or_less():
    # ~16 months from May 2027 to Dec 2028
    assert mc.renewal_urgency("2027-08-01") in ("soft", "urgent")


def test_renewal_urgency_urgent_when_under_6mo():
    # Aug 2028 → Dec 2028 = ~4 months
    assert mc.renewal_urgency("2028-08-01") == "urgent"


def test_renewal_urgency_critical_when_under_2mo():
    # Nov 2028 → Dec 2028 = ~1 month
    assert mc.renewal_urgency("2028-11-15") == "critical"


def test_renewal_message_includes_icon_for_each_tier():
    # critical
    msg = mc.renewal_message("2028-11-15")
    assert msg is not None and "🚨" in msg
    # urgent
    msg = mc.renewal_message("2028-08-01")
    assert msg is not None and "⚠️" in msg
