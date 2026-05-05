"""Bug #8/#10: picker should populate sector benchmark close robustly."""

from unittest.mock import Mock, patch

import main


def pick(sector="Technology", tag=""):
    return {
        "ticker": "NVDA",
        "info_short": {"sector": sector},
        "scores": {"sector_tag": tag},
    }


class FakeHist:
    def __init__(self, closes):
        self.Close = closes

    def __len__(self):
        return len(self.Close)

    def __getitem__(self, key):
        if key == "Close":
            return self.Close
        raise KeyError(key)


class FakeClose:
    def __init__(self, values):
        self._values = values

    def __len__(self):
        return len(self._values)

    @property
    def iloc(self):
        return self

    def __getitem__(self, idx):
        return self._values[idx]


def fake_hist(*values):
    return FakeHist(FakeClose(list(values)))


def test_sector_benchmark_for_pick_resolves_etf_and_close():
    ticker = Mock()
    ticker.return_value.history.return_value = fake_hist(99.0, 101.5)

    with patch.object(main, "_yf_ticker_for_sector_benchmark", ticker):
        etf, close = main._sector_benchmark_for_pick(pick(sector="Technology"))

    assert etf == "XLK"
    assert close == 101.5
    ticker.assert_called_once_with("XLK")


def test_sector_benchmark_for_pick_falls_back_to_spy_when_sector_close_missing():
    def ticker(symbol):
        m = Mock()
        if symbol == "XLK":
            m.history.return_value = fake_hist()
        elif symbol == "SPY":
            m.history.return_value = fake_hist(500.0)
        else:
            raise AssertionError(symbol)
        return m

    with patch.object(main, "_yf_ticker_for_sector_benchmark", ticker):
        etf, close = main._sector_benchmark_for_pick(pick(sector="Technology"))

    assert etf == "SPY"
    assert close == 500.0


def test_sector_benchmark_for_pick_keeps_resolved_etf_when_close_fetch_succeeds():
    def ticker(symbol):
        m = Mock()
        if symbol == "SOXX":
            m.history.return_value = fake_hist(220.0)
        elif symbol == "SPY":
            raise AssertionError("SPY should not be fetched when sector ETF succeeds")
        else:
            raise AssertionError(symbol)
        return m

    with patch.object(main, "_yf_ticker_for_sector_benchmark", ticker):
        etf, close = main._sector_benchmark_for_pick(pick(sector="Technology", tag="SEMI / AI"))

    assert etf == "SOXX"
    assert close == 220.0
