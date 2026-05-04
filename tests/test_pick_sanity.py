"""Sanity gate tests — these MUST pass forever or no pick ships to user."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.send_layman_daily import _is_pick_sane


def test_blocks_zero_take_profit():
    pick = {"ticker": "X", "entry": 100.0, "stop_loss": 98.0, "take_profit": 0.0}
    sane, why = _is_pick_sane(pick)
    assert not sane, f"should have blocked but said: {why}"
    assert "take_profit" in why or "tp" in why


def test_blocks_zero_entry():
    pick = {"ticker": "X", "entry": 0.0, "stop_loss": 98.0, "take_profit": 110.0}
    assert not _is_pick_sane(pick)[0]


def test_blocks_tp_below_entry():
    pick = {"ticker": "X", "entry": 100.0, "stop_loss": 98.0, "take_profit": 95.0}
    sane, why = _is_pick_sane(pick)
    assert not sane and "tp" in why.lower()


def test_blocks_sl_above_entry():
    pick = {"ticker": "X", "entry": 100.0, "stop_loss": 105.0, "take_profit": 110.0}
    assert not _is_pick_sane(pick)[0]


def test_blocks_low_rr():
    # entry 100, sl 98 (risk 2%), tp 101 (reward 1%) = R/R 0.5
    pick = {"ticker": "X", "entry": 100.0, "stop_loss": 98.0, "take_profit": 101.0}
    sane, why = _is_pick_sane(pick)
    assert not sane and "R/R" in why


def test_passes_good_pick():
    # entry 100, sl 98, tp 106 — risk 2%, reward 6%, R/R 3.0
    pick = {"ticker": "X", "entry": 100.0, "stop_loss": 98.0, "take_profit": 106.0}
    sane, why = _is_pick_sane(pick)
    assert sane, f"good pick rejected: {why}"


def test_field_name_take_profit_works():
    """The bug we just fixed: 'take_profit' must be recognized."""
    pick = {"ticker": "A", "entry": 114.52, "stop_loss": 112.36, "take_profit": 120.0}
    sane, _ = _is_pick_sane(pick)
    assert sane


def test_field_name_tp_works():
    pick = {"ticker": "A", "entry": 114.52, "stop_loss": 112.36, "tp": 120.0}
    sane, _ = _is_pick_sane(pick)
    assert sane


def test_field_name_target_price_works():
    pick = {"ticker": "A", "entry": 114.52, "stop_loss": 112.36, "target_price": 120.0}
    sane, _ = _is_pick_sane(pick)
    assert sane


# ───────────────────────────────────────────────────────────────
# Bug #7 — company name display
# ───────────────────────────────────────────────────────────────
from src.layman_translator import pick_to_layman, _company_suffix


def test_company_suffix_hides_when_equals_ticker():
    """If company == ticker (data fetch fallback), don't render '(A)'."""
    assert _company_suffix({"company": "A"}, "A") == ""


def test_company_suffix_hides_when_empty():
    assert _company_suffix({"company": ""}, "AAPL") == ""
    assert _company_suffix({"company": None}, "AAPL") == ""
    assert _company_suffix({}, "AAPL") == ""


def test_company_suffix_shows_real_name():
    assert _company_suffix({"company": "Apple Inc."}, "AAPL") == " (Apple)"


def test_company_suffix_trims_long_corporate_suffixes():
    assert "Inc." not in _company_suffix({"company": "Agilent Technologies, Inc."}, "A")
    assert "Corp." not in _company_suffix({"company": "Microsoft Corp."}, "MSFT")


def test_pick_to_layman_renders_company_in_header():
    pick = {"ticker": "AAPL", "company": "Apple Inc.",
            "entry": 200, "stop_loss": 195, "take_profit": 215,
            "qty": 10, "trade_type": "swing", "score": 0.85}
    out = pick_to_layman(pick, 1)
    assert "AAPL" in out and "Apple" in out
