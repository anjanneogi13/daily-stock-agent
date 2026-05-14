"""E2c.2/3 — stale_price smell + is_valid_market_data tests."""
from unittest.mock import patch
from src.smell_faculty import smell_stale_price, sniff, ALL_SMELLS
from src.data_fetcher import is_valid_market_data


# ── smell_stale_price ───────────────────────────────────────────
def test_smell_returns_none_when_prices_agree():
    pick = {"ticker": "NVDA", "entry": 200.0}
    with patch("src.finnhub_data.fetch_finnhub_quote") as mq:
        mq.return_value = {"current": 200.10, "source": "finnhub"}
        assert smell_stale_price(pick, {}) is None


def test_smell_warns_on_2_5_pct_drift():
    pick = {"ticker": "NVDA", "entry": 200.0}
    with patch("src.finnhub_data.fetch_finnhub_quote") as mq:
        mq.return_value = {"current": 194.0, "source": "finnhub"}  # ~3%
        s = smell_stale_price(pick, {})
    assert s is not None
    assert s.severity == "HIGH"
    assert s.blocking is False


def test_smell_warns_on_5pct_plus_disagreement():
    """PR-A2 F1-1: yf↔finnhub disagreements >5% are NORMAL in premarket
    (finnhub returns last regular close, yfinance has early premarket prints).
    Now warns at HIGH severity instead of blocking."""
    pick = {"ticker": "NVDA", "entry": 200.0}
    with patch("src.finnhub_data.fetch_finnhub_quote") as mq:
        mq.return_value = {"current": 180.0, "source": "finnhub"}  # ~10%
        s = smell_stale_price(pick, {})
    assert s is not None
    assert s.severity == "HIGH"
    assert s.blocking is False


def test_smell_silent_when_no_entry_price():
    """Don't create a smell if entry is missing — let other guards catch."""
    assert smell_stale_price({"ticker": "NVDA", "entry": None}, {}) is None
    assert smell_stale_price({"ticker": "NVDA"}, {}) is None


def test_smell_silent_when_no_ticker():
    assert smell_stale_price({"entry": 100.0}, {}) is None


def test_smell_silent_when_finnhub_down():
    """Graceful: no Finnhub access shouldn't create false-positive smells."""
    pick = {"ticker": "NVDA", "entry": 200.0}
    with patch("src.finnhub_data.fetch_finnhub_quote") as mq:
        mq.return_value = {"current": None, "error": "no_api_key"}
        assert smell_stale_price(pick, {}) is None


def test_stale_price_registered_in_all_smells():
    names = [fn.__name__ for fn in ALL_SMELLS]
    assert "smell_stale_price" in names


def test_sniff_includes_stale_price_warning_but_not_blocker():
    """PR-A2 F1-1: stale_price now surfaces as a warning, not a hard block."""
    pick = {"ticker": "NVDA", "entry": 200.0}
    with patch("src.finnhub_data.fetch_finnhub_quote") as mq:
        mq.return_value = {"current": 180.0, "source": "finnhub"}
        warnings = sniff(pick, {})
    kinds = [w.code for w in warnings]
    assert "stale_price" in kinds, "warning must still surface"
    blockers = [w for w in warnings if w.blocking]
    # No longer a blocker:
    assert not any(w.code == "stale_price" for w in blockers)


# ── is_valid_market_data ────────────────────────────────────────
def test_validator_accepts_valid_info():
    ok, _ = is_valid_market_data({"currentPrice": 198.50, "averageVolume": 1_000_000})
    assert ok


def test_validator_rejects_none_price():
    ok, reason = is_valid_market_data({"currentPrice": None, "averageVolume": 1000})
    assert ok is False
    assert "None" in reason or "delisted" in reason


def test_validator_rejects_zero_price():
    ok, _ = is_valid_market_data({"currentPrice": 0, "averageVolume": 1000})
    assert ok is False


def test_validator_rejects_negative_price():
    ok, _ = is_valid_market_data({"currentPrice": -5, "averageVolume": 1000})
    assert ok is False


def test_validator_rejects_zero_volume():
    ok, reason = is_valid_market_data({"currentPrice": 100, "averageVolume": 0})
    assert ok is False
    assert "untradeable" in reason or "volume" in reason.lower()


def test_validator_rejects_suspicious_high_price():
    ok, _ = is_valid_market_data({"currentPrice": 500_000, "averageVolume": 1000})
    assert ok is False


def test_validator_rejects_non_numeric_price():
    ok, _ = is_valid_market_data({"currentPrice": "not a number", "averageVolume": 1000})
    assert ok is False
