"""Parallel candidate scoring — all tickers, no shortcuts."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from .indicators import add_indicators, latest_signals
from .fundamentals import score_fundamentals, passes_filters
from .news_sentiment import fetch_news, score_sentiment
from .scorer import composite_score
from .risk_manager import trade_plan
from .data_fetcher import fetch_info


def _score_one(tk, df, cfg):
    try:
        d = add_indicators(df)
        sig = latest_signals(d)
        if not sig.get("close"):
            return None
        info = fetch_info(tk)
        if not passes_filters(info, cfg):
            return None
        fund = score_fundamentals(info)
        news = fetch_news(tk, limit=5)
        sent = score_sentiment(news)
        scores = composite_score(sig, fund, sent, cfg["weights"],
                                 ticker=tk, sector_cfg=cfg.get("sector", {}))
        if scores["composite"] < cfg["output"]["min_score"]:
            return None
        plan = trade_plan(sig, cfg)
        return {
            "ticker": tk, "scores": scores, "plan": plan, "news": news,
            "info_short": {"name": info.get("shortName", tk),
                           "sector": info.get("sector", "N/A")},
        }
    except Exception as e:
        print(f"[score] {tk}: {type(e).__name__}: {str(e)[:80]}")
        return None


def score_all(data: dict, cfg: dict, max_workers: int = 10) -> list:
    """Score every ticker in parallel — no candidates dropped."""
    candidates = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_score_one, tk, df, cfg): tk for tk, df in data.items()}
        for fut in as_completed(futs):
            r = fut.result()
            if r:
                candidates.append(r)
    candidates.sort(key=lambda x: x["scores"]["composite"], reverse=True)
    return candidates
