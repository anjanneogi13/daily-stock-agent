# Audit — `src/data_fetcher.py`
**LOC:** 231 | **Wired in:** ✅ Yes — universe-wide OHLCV fetch (the "senses") | **Tests:** thin  
**Suggestion-only context:** Upstream of every gate. If this fails, NOTHING gets picked.

## Findings

### F9-1 — L128 silently drops `len(df) <= 50`
- **Code:** `if not df.empty and len(df) > 50: results[t] = df`
- **Behavior:** Silently drops any ticker with ≤ 50 days of OHLCV history.
- **Risk:** Recent IPOs, post-halt resumes, or any ticker with sparse history → vanishes from universe with no log entry. Could explain "agent never picks new IPO winners."
- **Verdict:** 🔴 **LOOSEN**
- **Fix:** Lower to `> 20` (enough for short-term technicals). Log dropped tickers with reason.

### F9-2 — L120-132 `fetch_universe_data` only 2 providers
- **Code:** `_fetch_yfinance_ohlcv` → `_fetch_stooq_fallback_ohlcv`. No finnhub fallback.
- **Risk:** When yfinance is rate-limited (frequent) AND stooq is slow (frequent for non-US tickers), entire run gets sparse data → readiness gate fails (F4-1).
- **Verdict:** 🔴 **LOOSEN** (PR-A5)
- **Fix:** Add finnhub OHLCV as 3rd provider. Same pattern as PR-A's sanity gate.

### F9-3 — L42 `timeout=20` per yfinance call
- **Behavior:** 20 seconds per ticker. With max_workers=5 and a 500-ticker universe, worst case = 500/5 × 20s = 33 min.
- **Risk:** When yfinance is being slow (all of last week), this can blow past the 09:20 ET cutoff.
- **Verdict:** ✅ **KEEP** the timeout, but **bump max_workers to 10** to halve worst-case latency.

### F9-4 — L120-132 No per-ticker visibility
- **Behavior:** Reports `Fetched N/M tickers` but doesn't say which failed or why (yfinance vs stooq).
- **Verdict:** 🔴 **LOOSEN** (PR-A3 diagnostics)
- **Fix:** Emit per-provider success/fail counts to Telegram diagnostic when fetch ratio < 50%.

## Summary
- LOOSEN: 2 (F9-1, F9-2 + observability F9-4)
- KEEP: 2 (F9-3 timeout)
- LOC delta: ~40 lines (mostly the finnhub provider integration)

## Why this matters
This is the FOUNDATION. Every gate downstream depends on the data this returns. If F9-1 silently drops 20 promising IPOs every morning, no amount of fixing downstream will recover them. **Fix this in PR-A5 immediately after PR-A2.**
