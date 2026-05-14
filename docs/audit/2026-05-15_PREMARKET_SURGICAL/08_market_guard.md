# Audit — `src/market_guard.py`
**LOC:** 116 | **Wired in:** ✅ Yes — `vix_level()`, `spy_trend()`, `sector_strength()` called in main.py | **Tests:** thin  
**Suggestion-only context:** Provides advisory data, NOT direct blocks. Other modules consume it for their own decisions.

## Findings

### F8-1 — L5-11 `vix_level()` — returns 0.0 on failure
- **Behavior:** If yfinance fails, returns 0.0 (looks like calm market!).
- **Risk:** Downstream code that does `if vix_level() > 25: caution` will be FOOLED into thinking calm during outages.
- **Verdict:** 🔴 **LOOSEN**
- **Fix:** Return None on failure. Callers must handle None explicitly (treat as unknown, not as calm).

### F8-2 — L13-26 `spy_trend()` — returns above_50/200dma=True on failure
- **Behavior:** Same fail-open pattern.
- **Risk:** Same — defaults to "bullish" on data outage.
- **Verdict:** ✅ **KEEP** (debatable; less critical than VIX, and bullish-default reduces false negative pessimism).

### F8-3 — L53-103 `classify_trade_type()` — day vs swing
- **Behavior:** Per PR #67 fix, lowered thresholds (momentum 0.65, volume 0.55).
- **Risk:** Reasonable. The fix itself shows this code was previously over-restrictive.
- **Verdict:** ✅ **KEEP**

## Summary
- LOOSEN: 1 (F8-1 — VIX fail mode)
- KEEP: 2 (F8-2, F8-3)
- LOC delta: 3 lines + caller updates (~10 lines total)
