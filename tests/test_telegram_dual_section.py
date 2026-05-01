"""Tests for PR #69 — Telegram dual-section format."""
import sys
from pathlib import Path

# Need to load the module without triggering the top-level send code
# by mocking env vars before import
import os
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
os.environ["TELEGRAM_CHAT_ID"] = "test_chat"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the helpers (skip __main__ block)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "send_telegram",
    Path(__file__).resolve().parent.parent / "scripts" / "send_telegram.py"
)
send_telegram = importlib.util.module_from_spec(spec)
spec.loader.exec_module(send_telegram)


# ═══════════════════════════════════════════════════════════════
# Helper: build a fake CSV row
# ═══════════════════════════════════════════════════════════════
def _row(ticker, trade_type="swing", score=0.75, entry=100.0, sl=95.0, tp=110.0,
         qty=10, regime="bullish", cape=38.0, **extra):
    base = {
        "pick_date": "2026-05-04",
        "pick_time": "13:00:00",
        "ticker": ticker,
        "company": ticker,
        "tag": "",
        "trade_type": trade_type,
        "score": str(score),
        "multiplier": "1.0",
        "entry": str(entry),
        "stop_loss": str(sl),
        "take_profit": str(tp),
        "risk_reward": "2.0",
        "qty": str(qty),
        "days_to_earnings": "",
        "regime": regime,
        "spy_close": "500",
        "cape": str(cape),
        "evaluation_status": "pending",
        "evaluated_on": "",
        "exit_price": "",
        "actual_return_pct": "",
        "r_multiple": "",
        "tp1": "", "tp2": "",
        "qty_t1": "", "qty_t2": "", "qty_t3": "",
        "tier_status": "",
    }
    base.update({k: str(v) for k, v in extra.items()})
    return base


# ═══════════════════════════════════════════════════════════════
# Classification tests
# ═══════════════════════════════════════════════════════════════
def test_classify_returns_day_for_day_picks():
    row = _row("NVDA", trade_type="day")
    assert send_telegram._classify_pick(row) == "day"


def test_classify_returns_swing_default():
    row = _row("LLY")  # default swing
    assert send_telegram._classify_pick(row) == "swing"


def test_classify_handles_missing_field():
    row = _row("AAPL")
    del row["trade_type"]
    assert send_telegram._classify_pick(row) == "swing"  # backward compat


def test_classify_handles_uppercase():
    row = _row("MSFT", trade_type="DAY")
    assert send_telegram._classify_pick(row) == "day"


# ═══════════════════════════════════════════════════════════════
# Message building tests
# ═══════════════════════════════════════════════════════════════
def test_build_message_no_picks():
    msg = send_telegram.build_message([], {}, "2026-05-04")
    assert "No picks today" in msg
    assert "2026-05-04" in msg


def test_build_message_only_swing():
    """Only swing picks → no DAY section, just SWING."""
    rows = [
        _row("LLY", trade_type="swing"),
        _row("GOOGL", trade_type="swing"),
    ]
    msg = send_telegram.build_message(rows, {}, "2026-05-04")
    assert "SWING TRADES (2)" in msg
    assert "DAY TRADES" not in msg
    assert "0 day · 2 swing" in msg


def test_build_message_only_day():
    """Only day picks → no SWING section."""
    rows = [
        _row("NVDA", trade_type="day", entry=200, sl=197.6, tp=202),
    ]
    msg = send_telegram.build_message(rows, {}, "2026-05-04")
    assert "DAY TRADES (1)" in msg
    assert "SWING TRADES" not in msg
    assert "Hold ≤4h" in msg
    assert "Close by EOD" in msg


def test_build_message_dual_section():
    """Mix → both sections present, day first."""
    rows = [
        _row("NVDA", trade_type="day", entry=200, sl=197.6, tp=202),
        _row("LLY", trade_type="swing", entry=850, sl=810, tp=890),
        _row("AVGO", trade_type="day", entry=1200, sl=1186, tp=1224),
    ]
    msg = send_telegram.build_message(rows, {}, "2026-05-04")
    # Both sections present
    assert "DAY TRADES (2)" in msg
    assert "SWING TRADES (1)" in msg
    # Day section appears BEFORE swing section
    day_idx = msg.index("DAY TRADES")
    swing_idx = msg.index("SWING TRADES")
    assert day_idx < swing_idx, "DAY section should appear before SWING"


def test_day_pick_shows_tight_stop_pct():
    """Day pick should show 2-decimal stop pct (1.20% not 1.2%)."""
    rows = [_row("NVDA", trade_type="day", entry=200, sl=197.6, tp=202)]
    msg = send_telegram.build_message(rows, {}, "2026-05-04")
    assert "−1.20%" in msg or "-1.20%" in msg


def test_day_pick_shows_max_hold():
    rows = [_row("NVDA", trade_type="day")]
    msg = send_telegram.build_message(rows, {}, "2026-05-04")
    assert "Hold ≤4h" in msg
    assert "force EOD" in msg


def test_swing_pick_no_max_hold():
    rows = [_row("LLY", trade_type="swing")]
    msg = send_telegram.build_message(rows, {}, "2026-05-04")
    assert "Hold ≤4h" not in msg


def test_message_includes_pr_versions():
    rows = [_row("NVDA", trade_type="day")]
    msg = send_telegram.build_message(rows, {}, "2026-05-04")
    assert "PR #66" in msg
    assert "#69" in msg  # part of "PR #66+#67+#68+#69" footer


def test_message_handles_bad_numeric_data():
    """Don't crash on missing/empty entry/sl/tp."""
    rows = [_row("BAD", entry="", sl="", tp="")]
    msg = send_telegram.build_message(rows, {}, "2026-05-04")
    # Should not raise — pick is still rendered, just with 0s
    assert "BAD" in msg


def test_message_truncation_safety():
    """Build huge message — caller truncates at 4000 chars."""
    rows = [_row(f"T{i:03d}", trade_type="swing") for i in range(50)]
    msg = send_telegram.build_message(rows, {}, "2026-05-04")
    # Just verify it builds without error; truncation happens in __main__
    assert len(msg) > 0
    assert "SWING TRADES (50)" in msg


# ═══════════════════════════════════════════════════════════════
# Format helper tests
# ═══════════════════════════════════════════════════════════════
def test_safe_float_handles_empty():
    assert send_telegram._safe_float("") == 0.0
    assert send_telegram._safe_float(None) == 0.0
    assert send_telegram._safe_float("abc") == 0.0
    assert send_telegram._safe_float("12.5") == 12.5


def test_safe_int_handles_empty():
    assert send_telegram._safe_int("") == 0
    assert send_telegram._safe_int(None) == 0
    assert send_telegram._safe_int("10.5") == 10