# Audit — `src/premarket_readiness_gate.py`
**LOC:** 197 | **Wired in:** ✅ Yes — runs BEFORE scoring (early gate) | **Tests:** `tests/test_premarket_readiness_gate.py`  
**Suggestion-only context:** Cuts the entire run if data is too sparse. Failure mode = `NO_PICK_DATA_READINESS_FAILED` or `NO_PICK_DATA_PROVIDER_DEGRADED`.

## Findings

### F4-1 — L18-19 `DEFAULT_MIN_FETCH_COVERAGE = 0.25` and `DEFAULT_MIN_FETCHED_COUNT = 25`
- **Behavior:** Requires either 25% of universe OR 25 absolute tickers fetched, whichever is smaller.
- **Risk:** With universe of ~500 and 25% threshold = 125. If yfinance is rate-limited and only 80 tickers come back, **the entire run fails-closed** even though 80 candidates is plenty for a top-5 pick.
- **Verdict:** 🔴 **LOOSEN**
- **Fix:** Lower default to `min_fetched_count=15`, `min_fetch_coverage=0.05`. Anything ≥15 is enough to score and pick.

### F4-2 — L161-178 ohlcv-degraded check
- **Code:** `if ohlcv_attempts >= 10 and ohlcv_successes == 0 and (errors+empty) >= attempts: fail`
- **Behavior:** If ALL 10+ attempts fail/empty → fail-closed.
- **Risk:** Reasonable — if 0/10 worked, providers are genuinely down.
- **Verdict:** ✅ **KEEP**

### F4-3 — L116-128 universe_count ≤ 0 → fail
- **Behavior:** Empty universe = no point.
- **Verdict:** ✅ **KEEP**

### F4-4 — L130-142 fetched_count ≤ 0 → fail
- **Behavior:** Zero data = no point.
- **Verdict:** ✅ **KEEP** (but combine with F4-1 fix — even 1 fetched ticker should NOT fail if you only need to pick 5)

### F4-5 — Hardcoded thresholds, no override path
- **Behavior:** Defaults are baked in; caller can pass custom values but `main.py` doesn't.
- **Verdict:** 🔴 **LOOSEN**
- **Fix:** Read from `config.yaml` so user can tune without code changes.

## Summary
- LOOSEN: 3 (F4-1, F4-4 combined, F4-5)
- KEEP: 2 (F4-2, F4-3)
- LOC delta: ~10 lines + 3 lines in `config.yaml`

## Why this matters
On a day when yfinance is slow (every Monday and Friday lately), this gate alone can kill the entire premarket run before scoring even starts — and the Telegram message will say `NO_PICK_DATA_READINESS_FAILED` which sounds like "data is broken" but really means "we were too strict about how much data we needed."
