"""Stock universe selection — semiconductor priority built in."""
import pandas as pd
from typing import List
from .semiconductors import get_semi_tickers

SP500_WIKI = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
NASDAQ100_WIKI = "https://en.wikipedia.org/wiki/Nasdaq-100"

def get_sp500_tickers() -> List[str]:
    try:
        tables = pd.read_html(SP500_WIKI)
        return tables[0]["Symbol"].str.replace(".", "-", regex=False).tolist()
    except Exception as e:
        print(f"[universe] Failed S&P 500: {e}. Fallback.")
        return _fallback_universe()

def get_nasdaq100_tickers() -> List[str]:
    try:
        tables = pd.read_html(NASDAQ100_WIKI)
        for t in tables:
            if "Ticker" in t.columns or "Symbol" in t.columns:
                col = "Ticker" if "Ticker" in t.columns else "Symbol"
                return t[col].tolist()
        return _fallback_universe()
    except Exception as e:
        print(f"[universe] Failed NASDAQ-100: {e}. Fallback.")
        return _fallback_universe()

def _fallback_universe() -> List[str]:
    return ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA",
            "JPM", "V", "JNJ", "WMT", "SPY", "QQQ"]

def get_universe(config: dict) -> List[str]:
    src = config["universe"]["source"]
    if src == "semis_only":
        base = []
    elif src == "sp500":
        base = get_sp500_tickers()
    elif src == "nasdaq100":
        base = get_nasdaq100_tickers()
    elif src == "custom":
        base = list(config["universe"]["custom_tickers"])
    else:
        raise ValueError(f"Unknown universe source: {src}")

    semi_cfg = config["universe"].get("semiconductors", {})
    if semi_cfg.get("always_include", True):
        min_ai = semi_cfg.get("min_ai_weight", 0.0)
        base = list(dict.fromkeys(base + get_semi_tickers(min_ai_weight=min_ai)))

    excluded = {t.upper() for t in config["universe"].get("excluded_tickers", [])}
    base = [t for t in base if t.upper() not in excluded]

    semi_set = set(get_semi_tickers())
    print(f"[universe] {len(base)} tickers ({sum(1 for t in base if t.upper() in semi_set)} semis)")
    return base
