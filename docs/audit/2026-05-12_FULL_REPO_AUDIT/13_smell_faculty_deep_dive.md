# Batch 7 — src/smell_faculty.py deep-dive + M-RUN57 verification

**Date:** 2026-05-12
**File:** src/smell_faculty.py (271 lines)
**Cross-ref:** src/parallel_scorer.py (177 lines)

## 🚨 M-RUN57 CONFIRMED AND WORSE THAN BATCH 6 STATED

In Batch 6 I claimed the smell faculty receives empty `signals` dict so most checks no-op. After reading both files line-by-line, the smell faculty has TWO independent failure modes that compound, and 5 of 7 smells are effectively dead in production.

### Root cause #1: parallel_scorer drops `sig`
parallel_scorer._score_one (lines 38-160) computes `sig = latest_signals(d)` at line 41. This dict contains rsi/vol_ratio/atr/close/gap. But the function's return at lines 155-160 does NOT include `sig`. So when main.py does `sig = p.get("signals") or {}`, the result is `{}` 100% of the time.

### Root cause #2: Smells use FLAT keys but production data is NESTED
The smells have fallbacks to `pick.get(...)` and `pick["scores"].get(...)`. But two key smells (smell_tight_stop, smell_stale_price) use `pick.get("entry")` — production has it at `pick["plan"]["entry"]`. Tests construct flat dicts so tests pass; production picks are nested so production fails.

### Per-smell verdict in production

| Smell | Reads | Verdict |
|---|---|---|
| smell_earnings_imminent | pick["days_to_earnings"] | ✅ WORKS |
| smell_extreme_rsi | rsi (3 fallbacks, all empty) | 🚨 DEAD |
| smell_volume_spike | vol_ratio | 🟡 PROBABLY DEAD |
| smell_gap_up | gap_pct (never populated anywhere) | 🚨 DEAD |
| smell_low_liquidity | avg_volume (never populated) | 🚨 DEAD |
| smell_tight_stop | pick["entry"] but production has pick["plan"]["entry"] | 🚨 DEAD wrong-nesting |
| smell_stale_price | pick["entry"] same problem | 🚨 DEAD wrong-nesting |

5 of 7 smells DEAD. 1 probably dead. Only smell_earnings_imminent fires. The May 11 stale_price smell ("Catches wrong-ticker disasters, would have caught XXYYZZ123") cannot fire because it can't read entry.

## Line-by-line findings

### Lines 1-22: Module docstring + dataclass
- ✅ SF-1: Excellent docstring (lines 1-17). Use as template.
- ⚠️ SF-2 (line 15): Docstring says "(pick, signals)" but signals unused for 5/7 smells in production
- ✅ SF-3 (lines 23-28): Smell dataclass clean. blocking=False default is correct.

### Lines 35-56: smell_earnings_imminent
- ✅ SF-4: Clean three-tier ladder. Defensive int coercion.
- 🟡 SF-5 (line 38): if d2e == "" but not 0 — works but confusing
- ⚠️ SF-6 (line 44): if d < 0: return None — combined with main.py:858-870 may be dead

### Lines 59-76: smell_extreme_rsi — DEAD
- 🚨 SF-7 (line 62): Triple-fallback chain looks defensive but none are populated. Gives FALSE impression of safety.
- 🟡 SF-8 (lines 69, 73): Magic thresholds 85/75
- ⚠️ SF-9 (line 60): Docstring describes < 20 check that isn't implemented

### Lines 79-92: smell_volume_spike — PROBABLY DEAD
- 🟡 SF-10: vol_ratio passed around but never written to scores
- 🟡 SF-11: Magic threshold 4.0, only one tier (other smells have ladders)

### Lines 95-111: smell_gap_up — DEAD
- 🚨 SF-12: gap_pct never populated by any code path. main.py passes hardcoded 0.

### Lines 114-132: smell_low_liquidity — DEAD
- 🚨 SF-13: avg_volume not populated. yfinance returns it but data_fetcher drops it.
- ⚠️ SF-14: Magic thresholds 100k/500k

### Lines 135-148: smell_tight_stop — DEAD WRONG-NESTING
- 🚨 SF-15 (lines 138-139): pick.get("entry") — production has pick["plan"]["entry"]. Tests pass with flat dicts; production fails silently.
- ⚠️ SF-16 (line 145): Only flags POSITIVE small stops. Misses sl > entry (broken pick).

### Lines 154-224: smell_stale_price — DEAD WRONG-NESTING + COSTS NETWORK
- 🚨 SF-17 (line 172): Same flat-key bug. Function bails at line 173. Finnhub HTTP call NEVER fires. Docstring says "0.3-1s per pick"; production overhead is 0s and safety is 0.
- ⚠️ SF-18 (lines 178-186): Stacked try/except, silent on Finnhub failure
- 🟡 SF-19 (line 188): Magic 5% buried in cross_validate_price
- ⚠️ SF-20 (lines 189-208): If Finnhub returns is_valid=False due to OUTAGE, returns CRITICAL+blocking. Finnhub down → all picks blocked (when SMELL_ENFORCE=true).

### Lines 227-235: ALL_SMELLS registry
- ✅ SF-21: Clean registry pattern.
- ⚠️ SF-22 (line 234): Comment "E2c.2 cross-validate" implies stale_price is most important — it's dead.

### Lines 238-252: sniff() orchestrator
- ✅ SF-23 (line 240): sig = sig or {} defensive.
- 🚨 SF-24 (lines 247-249): bare except: continue. Theme T1. Use main.py:1781-1789 LOUD-error template.
- 🟡 SF-25 (line 250): severity_order redefined per call. Should be module constant.
- 🟡 SF-26 (line 251): Unknown severity sorts last (acceptable).

### Lines 255-260: has_blocking_smell()
- ⚠️ SF-27: Doesn't short-circuit. main.py:1127-1135 calls sniff TWICE per pick. ~14 smell evaluations + 2 Finnhub calls per pick.

### Lines 263-270: format_for_telegram()
- ✅ SF-28: Clean.
- 🟡 SF-29 (line 267): Markdown asterisks may need MarkdownV2 escape.

## Cross-cutting findings

### 🚨 SF-X1: parallel_scorer drops `sig` — ONE-LINE FIX RESURRECTS 4-5 SMELLS
Add `"signals": sig` to parallel_scorer.py line 155-160 return dict.

### 🚨 SF-X2: parallel_scorer never adds rsi/gap_pct/avg_volume to scores
Belt-and-suspenders fix.

### 🚨 SF-X3: smell_tight_stop and smell_stale_price use FLAT keys
Two-line fix per smell:
plan = pick.get("plan") or {}
entry = float(plan.get("entry") or pick.get("entry") or 0)

### 🚨 SF-X4: Test coverage gives false confidence
test_smell_faculty.py builds flat pick dicts. Tests pass while smells are dead in production. Need test_smell_faculty_production_shape.py that uses real picks.

### 🟡 SF-X5: 5 smells repeat triple-fallback pattern — extract helper

### ⚠️ SF-X6: parallel_scorer._score_one is 122-line God-function (separate batch)

## Summary

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 9 |
| ⚠️ Data/safety | 6 |
| 🟡 Code smell | 8 |
| ✅ Good code | 5 |
| Total findings | 28 |

## New themes confirmed

- Theme T9 (NEW): Test/production data shape divergence. Tests pass; production silently no-ops.
- Theme T4 update: Safety gates inert by design due to data-shape mismatch.

## Coverage tracker

| Phase | Status | Files done | Total |
|---|---|---:|---:|
| Phase A (safety/gates) | 1/8 done | smell_faculty.py | 8 |
| Total true line-by-line | | 16 files | 382 |
| Remaining | | 366 files | |

End of Batch 7.
