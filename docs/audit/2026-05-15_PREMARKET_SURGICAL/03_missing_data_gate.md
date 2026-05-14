# Audit — `src/missing_data_gate.py`
**LOC:** 163 | **Wired in:** ✅ Yes — runs after portfolio_risk_gate, before official logging | **Tests:** `tests/test_missing_data_gate.py` (good)  
**Suggestion-only context:** Validation only — appropriately strict for "what makes a complete official pick."

## Findings

### F3-1 — L122-125 rejects if `premarket_actionable is False` or `portfolio_risk_passed is False`
- **Code:** `if snap.get("premarket_actionable") is False: errors.append("premarket_actionable is false")`
- **Behavior:** If prior gates marked the candidate as non-actionable, this gate also rejects it.
- **Risk:** With PR-A, `premarket_actionable` is now `True` for HALF_SIZE candidates (provider_unverified). So this works correctly. ✅
- **Verdict:** ✅ **KEEP**

### F3-2 — L96-97 trade_type must be "day" or "swing"
- **Code:** `if trade_type not in {"day", "swing"}: errors.append("trade_type must be day or swing")`
- **Behavior:** Rejects if trade_type is anything else (None, "", "intraday", etc.).
- **Risk:** Strict. Confirmed `market_guard.classify_trade_type` only ever returns these two strings. Safe.
- **Verdict:** ✅ **KEEP**

### F3-3 — L116-119 require stop_loss < entry < take_profit
- **Behavior:** Math sanity.
- **Verdict:** ✅ **KEEP**

### F3-4 — L92-93 rejects if score < 0
- **Code:** `elif score < 0: errors.append("score is negative")`
- **Behavior:** Rejects negative composite scores.
- **Risk:** Composite scores are normalized to [0,1] in scoring layer. Negative score = upstream bug, not over-blocking.
- **Verdict:** ✅ **KEEP**

## What's actually wrong here

### F3-5 — Missing diagnostic on bulk failure
- **Behavior:** If all candidates fail this gate, the orchestrator gets `allowed=[]` with detailed `blocked` list, but it's logged to JSON not Telegram.
- **Verdict:** 🔴 **LOOSEN** (in PR-A3 diagnostics)
- **Fix:** When blocked_count > 0, surface the top 3 missing-field reasons in Telegram diagnostics.

## Summary
- LOOSEN: 1 (F3-5, observability only — NOT validation)
- KEEP: 3 (F3-1, F3-2, F3-3, F3-4)
- This file is **NOT a silent killer.** It's correctly strict.
