# Batch 19 — src/risk_manager.py (126 lines) + src/exit_manager.py (63 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** risk_manager.py (126 lines, fully read), exit_manager.py (63 lines, fully read)
**Phase:** B (scoring + data layer) — files 15 and 16 of ~18

**NOTE:** atr_trade_plan.py does NOT exist as a separate file. The `atr_trade_plan` function lives in risk_manager.py (lines 66-125). exit_manager.py is its direct downstream collaborator (called from risk_manager line 98). Substituted accordingly.

## TOP HEADLINE FINDINGS

1. RM-X1: risk_manager.py has TWO PARALLEL TRADE-PLAN FUNCTIONS that produce DIFFERENT shapes:
   - `trade_plan` (lines 43-62) — uses sig dict, config dict, returns 7 fields
   - `atr_trade_plan` (lines 66-125) — uses positional args, returns 17 fields including scale-out tiers
   **Both produce entry/sl/tp/qty/risk_reward.** Theme T8 architectural duplication. Per Batch 8 PS-X3, parallel_scorer reads `risk.account_size` AND `risk.capital` (dual-source) — likely because trade_plan uses `risk_cfg["account_size"]` while atr_trade_plan uses `capital` positional arg.
2. RM-X2: REGIME_RISK_MULT (lines 14-20) — 5-state map for sizing. **But "transition" gets 0.8x default, while regime.py (Batch 15) returns "transition" when DATA BLACKOUT happens.** Per Batch 15 RG-20, total data failure → "transition" → 0.8x sizing. **System sizes at 80% on completely blind data.** Should arguably be 0x or skip.
3. RM-7 (line 31): `REGIME_RISK_MULT.get(regime, REGIME_RISK_MULT["unknown"])` — defaults to "unknown" which is 0.7x. **regime.py never produces "unknown" anymore (per BUG-3 fix Batch 15 RG-1)** but here we still have an "unknown" entry. Dead path? Or defensive belt-and-suspenders?
4. RM-13 (line 53): `(tp - entry) / (entry - sl) if entry > sl else 0` — risk_reward computation. **Returns 0 when entry <= sl.** A pick where stop is at-or-above entry produces RR=0, which downstream gates (PRG-43 risk_reward >= min_risk_reward, MDG-15 risk_reward must be positive) reject. **Fail-CLOSED chain.** ✅
5. RM-X3: `position_size` returns `int(risk_dollars // risk_per_share)` (line 41). **Floor division means small positions can be 0 shares.** A $10k account, 1% risk = $100 risk. A $10 risk-per-share → 10 shares. A $150 risk-per-share (high-vol stock) → 0 shares. **No min-1-share floor** in this function (`atr_trade_plan` line 94 has `max(1, ...)`). Two functions, two minimums.
6. EM-X1: exit_manager is CLEAN — 63 lines, single function, 17-field output, no I/O, no side effects. **One of the cleanest single-purpose modules in the audit.**
7. EM-9 (line 48-51): `if qty < 3: qty_t1=0, qty_t2=qty, qty_t3=0` — single-exit fallback for tiny positions. **But pick_logger (Batch 11 PL-39) writes tier_status="none" initially** and the trailing-stop module (Phase 2B.2) needs all three tiers. **A position < 3 shares may break the trailing-stop assumption** (qty_t3=0 means no trail tier exists). Need to verify Phase 2B.2 handles qty_t3==0.

## src/risk_manager.py — LINE BY LINE

### Lines 1-2: Module docstring + imports
- RM-1 SMELL: 1-line docstring "Position sizing + trade plan." — minimal.
- RM-2 GOOD (line 2): typing.Optional imported. Used.

### Lines 5-20: REGIME_RISK_MULT
- RM-3 GOOD (lines 8-13): Multi-line comment documenting each regime's intent. Operator-friendly.
- RM-4 GOOD (lines 14-20): Named constant dict. **Externalized policy.**
- RM-5 BUG: 5 magic floats (1.0/0.8/0.6/0.4/0.7). Could be config. But arguably "policy" not "config" per Batch 16 NS-8 reasoning.
- RM-6 BUG: REGIME_RISK_MULT has "unknown" at 0.7x but regime.py BUG-3 fix removed "unknown" outputs (Batch 15 RG-1). **Dead key OR defensive fallback.** If regime ever returns "skip_all" (as recommended by my Batch 15 fix #5), this dict has no entry → falls through line 31 to "unknown" → 0.7x sizing. **Fail-LIVE on misconfig.** Should validate.

### Lines 23-31: regime_risk_multiplier
- RM-7 GOOD: Defensive function. None/missing → "unknown" defensive default (0.7x).
- RM-8 GOOD (lines 26-27): Docstring documents the safety stance.

### Lines 35-41: position_size
- RM-9 BUG (line 35): No keyword-only args. Positional. Bug-prone if caller arg-orders wrong.
- RM-10 GOOD (line 39-40): Defensive risk_per_share <= 0 → return 0. Catches stop_loss >= entry case.
- RM-11 BUG (line 41): `int(risk_dollars // risk_per_share)` — floor division then int. Returns 0 for sub-1-share. **No min-1-share floor.** Compare to atr_trade_plan line 94 (`max(1, int(...))`). **Inconsistent minimums.**
- RM-12 BUG: Function takes risk_pct (e.g., 1.0 for 1%) and divides by 100 internally (line 37). **What if caller passes 0.01 thinking it's already decimal?** Risk = account * 0.01 / 100 = account * 0.0001 = 100x too small. No range guard. Per Batch 18 FH-X3 same risk pattern.

### Lines 43-62: trade_plan (THE LEGACY FUNCTION)
- RM-13 BUG (line 44): `risk_cfg = config["risk"]` — KeyError if "risk" missing. No defensive default. Compare to portfolio_risk_gate PRG-29 which uses `cfg.get("risk", {})`.
- RM-14 GOOD (line 47): `if not (entry and atr): return {}` — defensive empty return on missing data.
- RM-15 BUG (line 47): `entry and atr` — falsy-trap. If ATR is exactly 0 (rare but possible for very low-vol stock), returns empty dict. Edge case but undocumented.
- RM-16 BUG (line 49): `risk_cfg["stop_loss_atr_mult"]` — KeyError if missing. No defensive default. Same pattern.
- RM-17 BUG (line 50): Same for `take_profit_atr_mult`.
- RM-18 BUG (line 51-52): position_size with `risk_cfg["account_size"]` — KeyError. Per RM-X1 also: this uses `account_size` while atr_trade_plan uses `capital` arg. **Same data, two names.** Theme T2.
- RM-19 GOOD (line 53): RR computation with else-0 protection.
- RM-20 BUG (line 53): `if entry > sl else 0` — should also check `tp > entry` for completeness. Currently if tp == entry, RR = 0 / (entry - sl) = 0. ✅ but undocumented.
- RM-21 GOOD (lines 54-62): Returns 7-field dict. Consistent with parallel_scorer expectations.
- RM-22 SMELL: trade_plan vs atr_trade_plan — TWO functions, TWO output schemas. Caller must know which to use. **Architectural duplication.**

### Lines 66-125: atr_trade_plan (THE PRODUCTION FUNCTION)
- RM-23 GOOD (lines 66-70): Default args for all parameters. Self-defending.
- RM-24 BUG (line 67-68): `risk_pct: float = 0.01` — DECIMAL (1%). But trade_plan/position_size uses PERCENT (1.0 for 1%). **TWO RISK_PCT CONVENTIONS in same file.** RM-12 risk repeats here. Caller must know which is which.
- RM-25 GOOD (lines 75-77): Excellent comment archaeology — documents PR #67 day-trade tightening reasoning.
- RM-26 GOOD (lines 78-79): Day-trade override with explicit values. Day = (0.6, 1.0) ATR.
- RM-27 BUG (lines 81-82): `if not atr or atr <= 0: atr = price * 0.02` — **silent ATR fallback to 2% of price.** Per Batch 13 IND-X3, vol_ratio bug can produce inf, but ATR fallback here is OK. **However, no logging of the fallback.** A pick with missing ATR silently uses 2%. Audit-trail blind spot.
- RM-28 GOOD (lines 84-85): SL/TP math. Round to 2 decimals.
- RM-29 GOOD (lines 86-89): Defensive risk_per_share check with 0-qty fallback. Returns dict with required fields, just qty=0.
- RM-30 BUG (line 88-89): Returned dict has only 6 fields, missing the 11 fields the success path returns (stop_method, tiers, max_hold_minutes, regime, regime_risk_mult). **Asymmetric return shape.** Downstream code expecting all 17 fields will get None/KeyError.
- RM-31 GOOD (lines 91-93): Regime-aware sizing. risk_capital = capital * risk_pct * regime_mult.
- RM-32 GOOD (line 94): `max(1, int(risk_capital / risk_per_share))` — min-1-share floor. Compare to position_size RM-11 which has NO floor. **Inconsistent.**
- RM-33 BUG (line 94): Min-1-share floor means **risk per trade can EXCEED configured risk_pct**. For a $10k account at 1% risk = $100 budget, a high-vol stock at $50 with $5 risk-per-share = 20 shares = $100 risk. ✅. But if risk-per-share = $150 (very high vol): risk_capital ($100) / 150 = 0.67 → floor → max(1, 0) = 1 share = $150 risk. **150% over budget.** Silent over-risk.
- RM-34 GOOD (line 98): Inline import of compute_exit_tiers — defensive lazy load. Avoids circular imports.
- RM-35 BUG (line 98): Inline import inside function. Recomputes import every call. **Per-call import overhead.** Minor but anti-pattern.
- RM-36 GOOD (line 102): max_hold_min = 240 for day trades. Named magic 4 hours. Comment explains.
- RM-37 BUG (line 102): swing trades have None max_hold (no time stop). Implicit "hold forever". Multi-month positions not gracefully handled. Should have a swing max_hold (e.g., 90 days).
- RM-38 GOOD (lines 104-125): Returns 17-field dict. Rich audit trail.
- RM-39 GOOD (line 124): regime_risk_mult surfaced — operator can see the multiplier applied.
- RM-40 BUG (line 110): `"atr": round(atr, 2)` — but if atr was fallback to price*0.02 (per RM-27), this rounds the fallback. **Doesn't surface that ATR was synthetic.** Should add `"atr_was_fallback": bool` field.
- RM-41 BUG: NO `risk_dollars` field in atr_trade_plan output (compare to trade_plan line 59). **Schema fragmentation between sibling functions.** portfolio_risk_gate (Batch 9 PRG-66) computes risk_dollars itself — works but duplicate logic.

## src/exit_manager.py — LINE BY LINE

### Lines 1-7: Module docstring
- EM-1 GOOD: Documents Phase 2B.1 origin. Lists 3 tiers with their multipliers.
- EM-2 GOOD: Notes TP3 trail handled by future "trailing_stop module" — cross-reference.

### Lines 11-26: compute_exit_tiers signature + docstring
- EM-3 GOOD: Type-hinted, default trade_type="swing".
- EM-4 GOOD: Docstring documents return shape with all 7 fields.

### Lines 29-33: Trade-type ATR multipliers
- EM-5 GOOD: 4 magic numbers (0.75, 1.5, 1.5, 2.5) but coherent — day uses tighter, swing uses wider. **Tied to atr_trade_plan multipliers (0.6, 1.0 day; 2.0, 2.5 swing).** RM and EM should be cross-checked.
- EM-6 BUG: TP1 multipliers (EM 0.75 day, 1.5 swing) vs SL multipliers (RM 0.6 day, 2.0 swing). **For SWING: SL=2.0×ATR, TP1=1.5×ATR.** TP1 is INSIDE the SL distance. **Risk:reward at TP1 is ~0.75 — sub-1.0 RR at first target.** Intentional (lock partial profit early) but reduces overall expectancy if TP1 fires often.
- EM-7 GOOD: comment "swing (default)" — clear.

### Lines 35-36: ATR fallback
- EM-8 BUG: SAME `atr = entry * 0.02` fallback as RM-27. **Duplicate logic in two files.** Theme T8.

### Lines 38-39: TP price math
- EM-9 GOOD: Round to 2 decimals.

### Lines 42-51: quantity tier split
- EM-10 GOOD (line 42): `qty = max(1, int(qty))` — defensive minimum 1.
- EM-11 BUG (lines 43-45): Integer division by 3. For qty=10: 3+3+4. For qty=100: 33+33+34. ✅
- EM-12 BUG (lines 48-51): qty<3 fallback puts ALL in tier 2. **qty_t1=0 and qty_t3=0.** Per EM-X1 finding, downstream trailing_stop expects qty_t3 > 0. **Single-share or 2-share positions may break trail logic.**
- EM-13 SMELL: Dead branches at qty=1 and qty=2. For qty=1: tier_t2 gets 1, others 0. For qty=2: same. **Both could just exit at TP2 directly with no tiering.** Edge cases handled but not optimally.

### Lines 53-62: return dict
- EM-14 GOOD: 7 fields, surfaces tp_mults for audit.
- EM-15 BUG: NO total_qty in return. Caller must add qty_t1+qty_t2+qty_t3 to verify integrity. Could surface.
- EM-16 GOOD (line 56): `tp3_mode: "trail"` — string constant naming the TP3 strategy. Documented.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### RM-X1: Two trade-plan functions produce different schemas
- trade_plan (legacy): 7 fields, uses config["risk"]["account_size"]
- atr_trade_plan (production): 17 fields, uses capital arg
- Both produce entry/sl/tp/qty/risk_reward
- portfolio_risk_gate PRG-14 reads BOTH plan["entry"] AND candidate["entry"] (dual-source) — partly because of this duality
- pick_logger (Batch 11 PL-37) defaults risk_reward to 2.0 if missing — masks which function produced
**Recommend: deprecate trade_plan, use atr_trade_plan everywhere. Single schema.**

### RM-X2: Risk-pct convention mismatch
- position_size: risk_pct as PERCENT (1.0 for 1%), divides by 100 internally
- atr_trade_plan: risk_pct as DECIMAL (0.01 for 1%), no division
- **Two functions, same arg name, two conventions, no type-distinct.** Caller error 100x off undetected.

### RM-X3: Min-share floor inconsistency creates over-risk
- position_size: floor division → 0 shares possible (under-fill)
- atr_trade_plan: max(1, ...) → forces 1 share (over-risk on high-vol)
- **Per RM-33: atr_trade_plan can silently exceed risk_pct by 50%+ for high-vol stocks.**
**Single fix: agree on min_share = 0 with explicit min_position_dollars check.**

### RM-X4: ATR fallback duplicated + silent
- RM-27: atr_trade_plan falls back to price*0.02 silently
- EM-8: exit_manager same fallback
- **Two files, identical fallback. No logging in either.** A pick with missing ATR is silently planned with 2% synthetic vol — sizing/stops based on synthetic data.
**Recommend: emit warning when fallback fires, surface "atr_was_fallback" flag.**

### EM-X1: Tier-split breaks for qty < 3
EM-12: qty=1 or 2 → qty_t3=0 → trailing_stop module (Phase 2B.2) may have edge case. **Cross-check Phase 2B.2 logic in next batches.**

### Cross-cutting: Module-level magic numbers
This batch alone:
- 5 regime risk multipliers (RM-3 to RM-5)
- 4 ATR multipliers in atr_trade_plan (0.6, 1.0, 2.0, 2.5)
- 4 ATR multipliers in exit_manager (0.75, 1.5, 1.5, 2.5)
- 1 max_hold_min (240)
- 2 ATR fallback ratios (0.02 in two places)
**16 magic numbers in 189 lines.** Sizing/exit policy fully hardcoded.

### Cross-cutting: Functions with side effects on import (status)
None this batch. risk_manager and exit_manager are PURE COMPUTATION — no module-import side effects. ✅ Compare to bootstrap_wisdom, pick_logger, data_fetcher, finnhub_data which all do import-time work.

## SUMMARY (Batch 19)

| Severity | risk_manager | exit_manager | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 11 | 4 | 4 | 19 |
| Data/safety | 8 | 3 | 0 | 11 |
| Code smell | 5 | 3 | 0 | 8 |
| Good code | 16 | 8 | 1 | 25 |
| Total findings | 40 | 18 | 5 | 63 |

## TOP 10 CRITICAL FIXES from Batch 19

1. RM-X3 / RM-33: Add explicit min_position_dollars guard in atr_trade_plan to prevent silent over-risk on high-vol stocks. (15 min, biggest safety gap)
2. RM-X1 / RM-22: Deprecate `trade_plan` (legacy). Make atr_trade_plan canonical. Update callers. (30 min)
3. RM-X2 / RM-24: Standardize risk_pct convention (decimal everywhere OR percent everywhere). Type-distinct via separate args names. (15 min)
4. RM-27 / EM-8: Surface ATR-fallback flag (`atr_was_fallback: bool`) in returned dict. Log when fallback fires. (10 min)
5. RM-X2 vs Batch 15 RG-20: Add "skip_all" or "no_data" key to REGIME_RISK_MULT (with multiplier 0.0) for total-blackout case. (5 min)
6. RM-30: Make atr_trade_plan return SAME schema in qty=0 path as in success path. (10 min)
7. RM-37: Add max_hold_days for swing trades (e.g., 90 days). (5 min)
8. EM-12 / EM-X1: Verify trailing_stop module handles qty_t3=0 case. May need to fold tier 3 into tier 2 for qty<3. (30 min)
9. RM-13/16/17/18: Use `risk_cfg.get(K, default)` instead of `risk_cfg[K]` to avoid KeyError on missing config. (10 min)
10. RM-40: Surface synthetic ATR via `atr_was_fallback` field. (5 min, included in #4)

## NEW THEMES UPDATED

- Theme T1 (bare except): None this batch. risk_manager + exit_manager have ZERO bare excepts. ✅ Notable.
- Theme T2 (schema drift): RM-X1 (trade_plan vs atr_trade_plan output shapes), RM-X2 (risk_pct convention), RM-30 (asymmetric return on qty=0).
- Theme T8 (DRY): RM-22, EM-8 (ATR fallback duplicated).
- Theme T11 (fail-open by accident): RM-X3 silent over-risk, RM-27 silent ATR fallback.
- Theme T13 (silent-default-fills): RM-27 (ATR=2%), RM-7 (regime "unknown" default 0.7x).
- Theme T14 (gold-standard patterns): exit_manager IS gold-standard pure computation (no I/O, no side effects, single function, type-hinted, documented).
- Theme T15 (false-positive blocking): N/A this batch.
- Theme T16 (dead-code safety nets): RM-6 — REGIME_RISK_MULT["unknown"] may be dead key.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 16/~18 done | risk_manager, exit_manager | 16/~18 |
| Total true line-by-line | | +2 files | 39 of 382 |
| Remaining | | | 343 files |

## NEXT BATCH

Batch 20: src/trailing_stop.py + src/adaptive_tp.py — Phase 2B.2 trailing stops + Phase 2B.3 adaptive TPs. These are the dynamic-exit modules that consume exit_manager tiers and update pick_logger fields (current_sl, peak_price, tp_raises, etc.).

End of Batch 19. Phase B in progress (16/18).
