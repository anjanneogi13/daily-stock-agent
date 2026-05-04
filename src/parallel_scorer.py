"""Parallel candidate scoring — all tickers, no shortcuts.

PR #67: Now also computes day_trading_score for each candidate.
classify_with_day_score makes the final DAY/SWING decision.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from .indicators import add_indicators, latest_signals
from .fundamentals import score_fundamentals, passes_filters
from .news_sentiment import fetch_news, score_sentiment
from .scorer import composite_score
from .watchlist_manager import watchlist_score_boost
from .risk_manager import trade_plan, atr_trade_plan
from .data_fetcher import fetch_info
from .day_trading_scorer import day_trading_score
from .market_guard import classify_with_day_score
from .monster_hunt import score_monster
from .monster_data import get_monster_data
from .wisdom_consultant import consult_before_pick as _wisdom_consult
from .signal_journal import build_signals as _build_signals
from .earnings import days_to_earnings as _d2e


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

        # Phase 2A: News watchlist boost
        wl_boost = watchlist_score_boost(tk)
        if wl_boost != 0:
            scores["watchlist_boost"] = round(wl_boost, 3)
            scores["composite"] = max(0.0, min(1.0, scores["composite"] + wl_boost))
            scores["composite"] = round(scores["composite"], 4)

        # 🧠 Pillar 3 Layer 6 — pattern multiplier (T50, additive, defensive)
        # Wires the 16 chart pattern detectors into scoring. Multiplier in
        # [0.85, 1.15] based on (pattern × regime) historical edge. Failure-safe.
        try:
            from .pattern_layer import pattern_multiplier as _pmul
            # M1: cache regime once per run via cfg["_regime"]
            _regime_now = cfg.get("_regime") or _resolve_regime(cfg)
            _pmul_val, _pmatches = _pmul(tk, regime=_regime_now, df=d)
            scores["pattern_multiplier"] = _pmul_val
            if _pmatches:
                scores["pattern_matches"] = ",".join(m.get("pattern","") for m in _pmatches)[:200]
            if _pmul_val != 1.0:
                scores["composite"] = max(0.0, min(1.0, round(scores["composite"] * _pmul_val, 4)))
        except Exception:
            scores["pattern_multiplier"] = 1.0

        if scores["composite"] < cfg["output"]["min_score"]:
            return None

        # PR #67: Day trading score (separate from swing composite)
        # News boost flows in here too (same watchlist signal)
        news_boost_for_day = max(0, wl_boost)  # only positive news helps day trades
        day_eval = day_trading_score(sig, news_boost=news_boost_for_day)
        scores["day_score"] = day_eval["day_score"]
        scores["day_reason"] = day_eval["day_reason"]
        scores["day_components"] = day_eval["day_components"]

        # Determine trade type (day vs swing)
        ttype = classify_with_day_score(scores, day_eval["day_score"], sig=sig)
        scores["trade_type"] = ttype  # surface for downstream

        # ATR-based stops (tighter for day trades)
        atr = sig.get("atr_14") or sig.get("atr") or sig.get("ATR") or 0
        price = sig.get("close", 0)
        capital = cfg.get("risk", {}).get("capital", 10000) or \
                  cfg.get("risk", {}).get("account_size", 10000)
        # E3b: pass regime so atr_trade_plan can size position defensively
        # in chop/bear (bull=1.0x, transition=0.8x, chop=0.6x, bear=0.4x)
        # M1: reuse the same regime cached above
        _regime_for_size = cfg.get("_regime") or _resolve_regime(cfg)
        if atr and atr > 0 and price > 0:
            plan = atr_trade_plan(price, atr, capital, trade_type=ttype,
                                  regime=_regime_for_size)
        else:
            plan = trade_plan(sig, cfg)
            plan["trade_type"] = ttype
            plan["regime"] = _regime_for_size

        # 💎 Monster Hunt scoring (additive, never blocks)
        try:
            mdata = get_monster_data(tk) if cfg.get("monster", {}).get("fetch_short_float", True) else {}
            d2e_val = _d2e(tk)
            d2e_norm = d2e_val if d2e_val is not None and d2e_val < 999 else None
            mres = score_monster(
                composite=scores["composite"],
                days_to_earnings=d2e_norm,
                short_pct_of_float=mdata.get("short_pct_of_float"),
                float_shares=mdata.get("float_shares"),
                vol_ratio=sig.get("vol_ratio"),
                has_bullish_news=(wl_boost > 0),
            )
            scores["monster_score"] = mres["monster_score"]
            scores["monster_reasons"] = mres["monster_reasons"]
            scores["is_monster"] = mres["is_monster"]
        except Exception as _me:
            scores["monster_score"] = 0.0
            scores["is_monster"] = False
            scores["monster_reasons"] = []

        # 🧠 Pillar 2: Consult wisdom base (warnings, boosts, kill check)
        try:
            _signals = _build_signals({
                "ticker": tk,
                "scores": scores,
                "regime": cfg.get("_regime", "unknown"),
                "trade_type": ttype,
                "days_to_earnings": None,  # filled later by main.py
                "vol_ratio": sig.get("vol_ratio"),
                "tag": scores.get("sector_tag"),
            })
            _wis = _wisdom_consult(tk, _signals)
            scores["wisdom_warnings"] = _wis["warnings"]
            scores["wisdom_boosts"]   = _wis["boosts"]
            scores["wisdom_kill"]     = bool(_wis.get("kill"))
            scores["wisdom_score_adj"] = _wis.get("score_adj", 0.0)
            # Tiny score tilt (capped ±0.05 in observe-mode)
            scores["composite"] = max(0.0, min(1.0,
                scores["composite"] + _wis.get("score_adj", 0.0)))
            scores["composite"] = round(scores["composite"], 4)
        except Exception as _wse:
            scores["wisdom_warnings"] = []
            scores["wisdom_boosts"]   = []
            scores["wisdom_kill"]     = False
            scores["wisdom_score_adj"] = 0.0

        return {
            "ticker": tk, "scores": scores, "plan": plan, "news": news,
            "info_short": {"name": info.get("shortName", tk),
                           "sector": info.get("sector", "N/A")},
            "trade_type": ttype,
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