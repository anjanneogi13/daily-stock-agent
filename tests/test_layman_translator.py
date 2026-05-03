"""T52: Layman translator — plain-English conversions."""
import pytest
from src import layman_translator as lt


# ─── Score → words ─────────────────────────────────────────────
def test_score_to_words_excellent():
    assert lt.score_to_words(0.92) == "excellent"

def test_score_to_words_strong():
    assert lt.score_to_words(0.75) == "strong"

def test_score_to_words_decent():
    assert lt.score_to_words(0.60) == "decent"

def test_score_to_words_okay():
    assert lt.score_to_words(0.45) == "okay"

def test_score_to_words_weak():
    assert lt.score_to_words(0.20) == "weak"

def test_score_to_words_none():
    assert lt.score_to_words(None) == "unknown"


# ─── Confidence ─────────────────────────────────────────────────
def test_confidence_label_high():
    assert "very confident" in lt.confidence_label(0.85)

def test_confidence_label_low():
    assert "cautious" in lt.confidence_label(0.30)


# ─── Risk label ─────────────────────────────────────────────────
def test_risk_label_low():
    assert lt.risk_label(0.5) == "very low risk"

def test_risk_label_high():
    assert lt.risk_label(6.0) == "high risk"


# ─── Money / pct ────────────────────────────────────────────────
def test_money_positive():
    assert lt.money(45.20) == "+$45.20"

def test_money_negative():
    assert lt.money(-12.50) == "-$12.50"

def test_money_zero():
    assert lt.money(0) == "$0"

def test_money_handles_string():
    assert lt.money("invalid") == "$0"

def test_pct_positive():
    assert lt.pct(2.4) == "+2.4%"

def test_pct_negative():
    assert lt.pct(-1.1) == "-1.1%"


# ─── R-multiple ─────────────────────────────────────────────────
def test_r_multiple_big_win():
    assert "big win" in lt.r_multiple_words(2.5)

def test_r_multiple_full_loss():
    assert "stop-loss" in lt.r_multiple_words(-1.0)

def test_r_multiple_invalid():
    assert lt.r_multiple_words(None) == "no result yet"


# ─── pick_to_layman — keeps actionable data ─────────────────────
def test_pick_to_layman_includes_all_actionable_data():
    pick = {
        "ticker": "NVDA", "composite_score": 0.78,
        "entry": 100.00, "sl": 97.00, "tp": 106.00,
        "qty": 50, "trade_type": "swing"
    }
    out = lt.pick_to_layman(pick)
    # Must keep PRICES
    assert "$100.00" in out
    assert "$97.00" in out
    assert "$106.00" in out
    # Must keep QUANTITY
    assert "50 shares" in out
    # Must explain HOLDING TIME
    assert "few days" in out or "weeks" in out
    # Must show RISK %
    assert "-3.0%" in out
    # Quality label
    assert "strong" in out


def test_pick_to_layman_day_trade_says_today_only():
    pick = {"ticker":"AAPL","composite_score":0.7,
            "entry":150,"sl":148,"tp":154,"qty":10,"trade_type":"day"}
    out = lt.pick_to_layman(pick)
    assert "TODAY" in out


# ─── outcome_to_layman ──────────────────────────────────────────
def test_outcome_tp_hit():
    o = {"ticker":"NVDA","status":"TP_HIT","pnl_dollar":120}
    assert "✅" in lt.outcome_to_layman(o)
    assert "+$120.00" in lt.outcome_to_layman(o)

def test_outcome_sl_hit():
    o = {"ticker":"AMD","status":"SL_HIT","pnl_dollar":-45}
    out = lt.outcome_to_layman(o)
    assert "❌" in out
    assert "-$45.00" in out

def test_outcome_open():
    assert "still holding" in lt.outcome_to_layman({"ticker":"X","status":"OPEN"})


# ─── verdict_line ───────────────────────────────────────────────
def test_verdict_great_day():
    assert "GREAT" in lt.verdict_line(7, 2, 250)

def test_verdict_tough_day():
    assert "TOUGH" in lt.verdict_line(2, 6, -180)

def test_verdict_no_trades():
    assert "No closed trades" in lt.verdict_line(0, 0)


# ─── beat_market_line ───────────────────────────────────────────
def test_beat_market_when_outperforming():
    out = lt.beat_market_line(2.5, 0.5)
    assert "beat the market" in out

def test_trailed_market():
    out = lt.beat_market_line(-1.0, 1.0)
    assert "trailed market" in out

def test_beat_market_handles_none():
    assert lt.beat_market_line(None, 1.0) == ""
