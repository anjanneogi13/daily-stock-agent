"""Skip stocks that already gapped too much premarket (chasing) or gapped down on bad news."""
import yfinance as yf

def gap_check(ticker: str, max_gap_up: float = 0.03,
              max_gap_down: float = -0.05) -> tuple:
    """
    Returns (is_safe: bool, gap_pct: float, reason: str).
    Run during premarket / open. Uses yesterday close vs current price.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        prev_close = info.get("previousClose") or info.get("previous_close")
        last = info.get("lastPrice") or info.get("last_price") or info.get("regularMarketPrice")
        if not (prev_close and last):
            return True, 0.0, "no premarket data — allow"
        gap = (last - prev_close) / prev_close
        if gap > max_gap_up:
            return False, gap, f"gapped up {gap*100:.1f}% (chasing risk)"
        if gap < max_gap_down:
            return False, gap, f"gapped down {gap*100:.1f}% (bad news risk)"
        return True, gap, f"gap {gap*100:.1f}% OK"
    except Exception as e:
        return True, 0.0, f"gap check failed ({type(e).__name__}) — allowing"
