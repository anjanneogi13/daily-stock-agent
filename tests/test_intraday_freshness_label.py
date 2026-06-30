"""Task 9b / vision item #3: intraday prices are ~15min delayed, not live.

get_live_quote() returns the last 5-min bar from free yfinance (delayed ~15min)
keyed as "price". The intraday Telegram message presented it next to a fresh
"HH:MM ET" timestamp with NO delay disclaimer, implying real-time data. These
tests lock in (a) a machine-readable freshness marker on the quote dict and
(b) a visible delay disclaimer in the user-facing message.
"""
import scripts.intraday_monitor as im


def _alert(ticker="AAA", price=100.0, entry=99.0, change_pct=1.2):
    return {
        "ticker": ticker, "price": price, "entry": entry,
        "change_pct": change_pct, "flags": [], "news": [],
    }


def test_message_discloses_delayed_data():
    msg = im.build_message([_alert()], [])
    low = msg.lower()
    assert "delayed" in low, f"intraday message must disclose delayed data, got:\n{msg}"
    # Must reference the ~15 minute nature so it isn't mistaken for live.
    assert "15" in msg, "disclaimer should mention the ~15 minute delay"


def test_new_opps_only_message_also_discloses_delay():
    opp = {
        "ticker": "BBB", "price": 50.0, "entry": 49.5, "sl": 48.0, "tp": 53.0,
        "score": 7.5, "watch_only": True, "scanner": "intraday",
        "reason": "momentum",
    }
    msg = im.build_message([], [opp])
    assert "delayed" in msg.lower(), "watch-only intraday message must also disclose delay"


def test_empty_message_unchanged():
    # No alerts + no opps => still empty string (no spurious disclaimer).
    assert im.build_message([], []) == ""


def test_get_live_quote_tags_freshness(monkeypatch):
    """get_live_quote must mark its data as delayed (machine-readable)."""
    import scripts.intraday_scanner as isc

    class _FakeHist:
        def __init__(self, closes, vols=None):
            import pandas as pd
            n = len(closes)
            self._df = pd.DataFrame({
                "Close": closes,
                "Volume": vols if vols is not None else [1000] * n,
            })
        @property
        def empty(self):
            return len(self._df) == 0
        def __getitem__(self, k):
            return self._df[k]
        def __len__(self):
            return len(self._df)

    class _FakeTicker:
        def __init__(self, *a, **k):
            pass
        def history(self, period=None, interval=None, prepost=None):
            # 5m intraday call vs 1d daily call: both return a small frame
            return _FakeHist([100.0, 101.0, 102.0], [1000, 1200, 1500])

    class _FakeYF:
        Ticker = _FakeTicker

    monkeypatch.setattr(isc, "yf", _FakeYF)
    q = isc.get_live_quote("AAA")
    assert q.get("data_freshness") == "delayed_~15min", q
    assert "price" in q  # key preserved for backward compat
