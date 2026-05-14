# Audit — `src/smell_faculty.py`
**LOC:** 271 | **Wired in:** ✅ Yes — `main.py` calls `sniff()` per candidate before publishing | **Tests:** `tests/test_smell_faculty.py` (~70% coverage)  
**Suggestion-only context:** **VIOLATES CONTRACT** — has 4 `blocking=True` paths.

## Findings

### F1-1 — L189-208 `smell_stale_price` blocks at >5% yf↔finnhub disagreement
- **Code:** `if not v["is_valid"]: ... blocking=True`
- **Behavior:** Hard-blocks pick if yfinance and finnhub disagree on price by >5%.
- **Risk:** During premarket window (08:00-09:30 ET), finnhub returns last *regular session* close, while yfinance may return early premarket print. Disagreements of 5-10% are NORMAL premarket on volatile tickers. This silently kills picks every morning.
- **Verdict:** 🔴 **LOOSEN**
- **Fix:** Downgrade to `blocking=False, severity="HIGH"` during 08:00-09:30 ET. Block only post-open (09:30+).

### F1-2 — L46-49 `smell_earnings_imminent` blocks at d2e ≤ 1
- **Code:** `if d <= 1: return Smell(..., blocking=True)`
- **Behavior:** Hard-blocks any pick with earnings in the next 1 day.
- **Risk:** Reasonable for trades. For a SUGGESTION agent, the user can decide to skip or take a small position.
- **Verdict:** 🔴 **LOOSEN** (suggestion-only)
- **Fix:** `blocking=False`, severity stays CRITICAL. User sees giant warning but suggestion still appears.

### F1-3 — L69-72 `smell_extreme_rsi` blocks at RSI ≥ 85
- **Code:** `if r >= 85: return Smell(..., blocking=True)`
- **Behavior:** Hard-blocks if RSI ≥ 85.
- **Risk:** Strongest momentum names regularly run RSI 85-95 for weeks (NVDA Jan 2024, SMCI Feb 2024, AVGO Dec 2024). This filter systematically removes the best winners.
- **Verdict:** 🔴 **LOOSEN**
- **Fix:** `blocking=False`. Show warning. Optionally raise threshold to 92 if any blocking is desired.

### F1-4 — L125-128 `smell_low_liquidity` blocks at avg_vol < 100k
- **Code:** `if v < 100_000: return Smell(..., blocking=True)`
- **Behavior:** Hard-blocks if avg daily volume < 100k shares.
- **Risk:** Low. User genuinely can't fill these efficiently.
- **Verdict:** ✅ **KEEP**

### F1-5 — L79-92 `smell_volume_spike` (volume ratio ≥ 4x)
- **Behavior:** Warning only, never blocks. Severity HIGH.
- **Verdict:** ✅ **KEEP**

### F1-6 — L95-111 `smell_gap_up` (gap ≥ 5% / ≥ 3%)
- **Behavior:** Warning only, never blocks.
- **Risk:** Already covered by `premarket_sanity_gate` HALF_SIZE logic (PR-A). Redundant but harmless.
- **Verdict:** ✅ **KEEP**

### F1-7 — L135-148 `smell_tight_stop` (SL < 0.8% from entry)
- **Behavior:** Warning only, never blocks.
- **Verdict:** ✅ **KEEP** — already covered by `hard_blocks.SL_MIN_TIERS` (which also blocks; see F2-1).

## Module-level findings
- L227-235: `ALL_SMELLS` registry only adds via append, no remove path. Acceptable.
- L238-252: `sniff()` swallows exceptions per-smell — good, prevents one bad smell from killing the agent.
- L255-260: `has_blocking_smell()` is the call point that turns warnings into blocks. **This function should accept a `suggestion_mode=True` parameter that returns None always.** That single change implements the entire suggestion-only contract.

## Test gaps
- No test for `smell_stale_price` premarket-window behavior (the F1-1 silent-kill scenario).
- No test asserting `has_blocking_smell` integration with `main.py` flow.

## Summary
- LOOSEN: 4 (F1-1, F1-2, F1-3, plus `has_blocking_smell` to honor suggestion mode)
- KEEP: 3 (F1-4, F1-5, F1-6, F1-7)
- LOC delta to apply: ~30 lines (mostly flipping `blocking=True` → `blocking=False` and adding suggestion-mode flag)
