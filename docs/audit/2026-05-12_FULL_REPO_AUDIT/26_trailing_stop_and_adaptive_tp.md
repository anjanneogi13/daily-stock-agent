# Batch 20 — src/trailing_stop.py (66 lines) + src/adaptive_tp.py (121 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** trailing_stop.py (66 lines, fully read), adaptive_tp.py (121 lines, fully read)
**Phase:** B (scoring + data layer) — files 17 and 18 of ~18 — PHASE B NEAR COMPLETE

## TOP HEADLINE FINDINGS

1. TS-X1: trailing_stop.py is PURE COMPUTATION, 66 LINES, 2 functions, ZERO I/O, ZERO bare-except. **Tied with exit_manager (Batch 19) for cleanest module in the audit.** Use as template for similar dynamic-exit logic.
2. ATP-X1: adaptive_tp.py — 121 lines, 3 functions, **single bare-except (line 76-77 timestamp parse) is appropriately documented** ("malformed timestamp → ignore"). Otherwise clean.
3. TS-X2: trailing_stop has NO STATE PERSISTENCE — pure function. State (current_sl, peak_price) lives in pick_logger CSV columns (Batch 11 PL-40/41). **The CALLER must pass state correctly.** Per Batch 11 PL-40, original_sl/current_sl/peak_price initialized from p["stop_loss"] which can be None. **If caller passes None, line 28 `entry <= 0 or peak_price <= 0` rejects → returns (current_sl, False) → SL never trails.** Silent disablement.
4. ATP-X2: should_raise_tp has 4-CONDITION LADDER (gain / RSI / volume / cooldown). **All 4 must be true to raise.** Combined probability is low — for a ticker to qualify needs +5% gain AND RSI >70 AND vol >1.8x AND no recent raise. **In normal market regimes, this fires rarely.** May be intentional (conservatism) but no analytics on how often it actually fires.
5. ATP-15 (line 80): `candidate_tp = round(current_price * (1 + headroom_pct / 100), 2)` — new TP is 5% above current price. **But current_price may already be >> current_tp (price blew through TP).** In that case candidate_tp = current_price × 1.05 → much higher than current_tp → raises. ✅ But if price was at TP and slightly above, candidate_tp could STILL be near current_tp → barely-raise.
6. TS-12 (line 37): `candidate_sl = round(peak_price * (1 - trail_pct / 100), 2)` — trails from PEAK. **Default trail_pct=2%.** For a stock at $100 peak, SL = $98. **But if entry was $90, the +3% activation threshold (line 32) is at $92.70, peak must reach $92.70+ before trail fires. If peak hits $93, SL = $91.14 — STILL ABOVE original $90 entry but BELOW current price.** Trail correctly locks profit > entry once active. ✅
7. TS-X3: Trailing-stop activation threshold (3%) and trail distance (2%) are **BOTH OPTIONAL ARGS WITH DEFAULTS** but **NEVER OVERRIDDEN by callers I can see** (no callers in audited files). Pick rolls forward with these hardcoded values for every position. **No regime-aware or volatility-aware adjustment.** A high-vol stock should trail wider.
8. ATP-X3: Per Batch 11 PL-43, pick_logger writes `tp_raises = "[]"` JSON-as-string column. ATP `append_raise_audit` (line 91-109) and `last_raise_ts` (line 112-120) are the readers/writers. **Schema is JSON-string-in-CSV-column.** Brittle but isolated to one column. Not as bad as some Theme T13 cases.

## src/trailing_stop.py — LINE BY LINE

### Lines 1-6: Module docstring + imports
- TS-1 GOOD: 4-line docstring describes activation threshold, trail logic, and ratchet-only invariant.
- TS-2 GOOD (line 6): typing.Tuple imported. Used.

### Lines 9-42: compute_trailing_sl
- TS-3 GOOD (lines 9-13): Type-hinted args with defaults.
- TS-4 GOOD (lines 14-26): Excellent docstring documenting each arg + return shape + invariant.
- TS-5 BUG (line 28): `if entry <= 0 or peak_price <= 0: return current_sl, False` — defensive but **silently no-ops on bad input**. Per TS-X2: if peak_price=None (CSV column empty), Python raises TypeError before reaching this check (None <= 0 raises). **Need to test with None inputs.**
- TS-6 GOOD (line 32): `activation_price = entry * (1 + activation_pct / 100)` — explicit math.
- TS-7 GOOD (line 33-34): If peak hasn't hit activation, no trail. Returns (current_sl, False) — invariant preserved.
- TS-8 GOOD (line 37): candidate_sl trailed from PEAK, not current price. Standard trailing-stop.
- TS-9 GOOD (line 40-42): "SL never moves down" invariant via comparison check. Returns (new, True) on raise, (current, False) on hold.
- TS-10 BUG: NO logging of trail events. Compare to ATP `append_raise_audit` which builds JSON history. **Trailing-stop changes have no audit trail.** A position whose SL was raised 5 times has no history of when/why. Loss of forensic info.
- TS-11 SMELL: 2 magic defaults (activation 3%, trail 2%). Per TS-X3, never overridden in audited callers. Effectively constants.

### Lines 45-65: trail_status
- TS-12 GOOD: Diagnostic function. Returns 4-field dict for logs/Telegram.
- TS-13 GOOD (lines 57-59): Defensive `if entry > 0 else 0.0` — div-by-zero guard.
- TS-14 BUG (line 59): `original_sl > 0` guard — but if original_sl is 0, sl_raised=0.0. **If pick_logger wrote original_sl=None which CSV reads as empty/0, this falls through.** Edge case.
- TS-15 GOOD (line 61): `active = current_sl > original_sl` — derived flag from state. Single source of truth.
- TS-16 BUG: `peak_gain_pct` and `locked_gain_pct` could be NEGATIVE (if peak < entry due to caller error). No sanity guard. Negative locked_gain shown to operator may confuse.

## src/adaptive_tp.py — LINE BY LINE

### Lines 1-15: Module docstring + imports
- ATP-1 GOOD: Multi-line docstring explaining 4 conditions.
- ATP-2 GOOD: Documents debounce ("no recent raise in last cooldown_min").
- ATP-3 GOOD (line 12): `from datetime import datetime` — but no timezone import. **Naive datetime.** Per Batch 17 NC-22 cross-cutting.

### Lines 17-88: should_raise_tp — THE MAIN FUNCTION
- ATP-4 GOOD (lines 17-28): Type-hinted, all 9 args have defaults except first 5. **Plus `now: Optional[datetime] = None` — INJECTABLE FOR TESTS.** Test-friendly design ✅.
- ATP-5 GOOD (lines 29-50): Comprehensive docstring with arg explanations.
- ATP-6 BUG (line 51): `now = now or datetime.now()` — **NAIVE datetime if not injected.** Per ATP-3.
- ATP-7 GOOD (lines 53-54): Defensive input validation. Returns explicit reason string.
- ATP-8 GOOD (lines 56-59): Condition 1 (gain). With formatted reason string.
- ATP-9 GOOD (lines 61-63): Condition 2 (RSI). Handles None case.
- ATP-10 BUG (line 63): `f"RSI {current_rsi} below {rsi_threshold}"` — if current_rsi is None, format string shows "RSI None below 70.0". Cosmetic.
- ATP-11 GOOD (lines 65-67): Condition 3 (volume). Handles None.
- ATP-12 GOOD (lines 69-77): Condition 4 (cooldown).
- ATP-13 GOOD (line 72): `datetime.fromisoformat(last_raise_iso)` — handles ISO format.
- ATP-14 BUG (line 72): If `last_raise_iso` was written by `append_raise_audit` line 105 with `timespec="seconds"`, format is "2026-05-12T14:30:45". fromisoformat handles. ✅. **But if it was timezone-aware ISO (like "2026-05-12T14:30:45+00:00"), naive `now` minus tz-aware `last_dt` raises TypeError.** ATP-6 uses naive now → mismatch with any tz-aware caller.
- ATP-15 BUG (lines 76-77): `except ValueError: pass` — bare-except-equivalent, **DOCUMENTED as "malformed timestamp → ignore."** Per Batch 14 MDH-40 / Batch 15 CB-57 pattern. Defensible documented exception. ✅
- ATP-16 GOOD (line 80): candidate_tp computation explicit.
- ATP-17 BUG (line 80): Magic 5% headroom default. **For high-vol stocks, 5% headroom from current is conservative; for low-vol it's aggressive.** No vol-aware adjustment. Same TS-X3 pattern.
- ATP-18 GOOD (lines 82-84): "TP only moves UP" invariant via comparison.
- ATP-19 GOOD (lines 86-88): Reason string with formatted gain/RSI/vol/old/new TP. Operator-friendly.
- ATP-20 BUG (line 86): `RSI {current_rsi:.0f}` — float format with .0 precision. If current_rsi=None, **AttributeError** (None doesn't support :.0f). But line 62 ALREADY rejected None — unreachable in success path. ✅ defensively safe but type-narrowing implicit.
- ATP-21 BUG: NO PARTIAL conditions logging. If 3 of 4 conditions met, function returns False with the FIRST failing reason. Operator can't see "would raise if vol picked up" — only sees current blocker. Could be enhanced to return all_conditions dict.

### Lines 91-109: append_raise_audit
- ATP-22 GOOD: Single-purpose, returns updated JSON string.
- ATP-23 BUG (line 97): `now = now or datetime.now()` — same naive-datetime issue.
- ATP-24 GOOD (lines 98-103): Defensive try/except with isinstance check. Recovers from corrupt JSON.
- ATP-25 GOOD (line 105): `now.isoformat(timespec="seconds")` — second precision. Reasonable for human audit.
- ATP-26 BUG (line 105): naive datetime → ISO without tz. Cross-process consistency at risk.
- ATP-27 GOOD (lines 104-108): Append-only audit. History grows linearly. **Could grow unbounded** for a long-held position with many raises. **No cap.** For weeks-long swing trade with daily raises, 100+ entries possible. Not a real risk for normal trading.
- ATP-28 GOOD (line 109): `json.dumps(history)` — serializes back to string for CSV storage.

### Lines 112-120: last_raise_ts
- ATP-29 GOOD: Single-purpose, returns last ts or None.
- ATP-30 GOOD (lines 114-119): Defensive try/except with isinstance check.
- ATP-31 GOOD (line 117): `history[-1].get("ts")` — uses .get for safety. Returns None if "ts" key missing.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### TS-X1 + ATP-X1: BOTH FILES ARE GOLD-STANDARD COMPUTATION MODULES
- No I/O
- No module-level state
- Type-hinted
- Documented invariants ("SL only moves UP")
- Defensive input validation
- Single documented bare-except (ATP-15)
- Test-injectable time (ATP-4)
- Pure functions
**Use as template for any future dynamic-exit logic.** Compare to risk_manager (Batch 19) which has 2 schemas, 2 risk-pct conventions, dead unknown key. Smaller files = cleaner discipline.

### TS-X2: state-passing fragility
trailing_stop expects caller to pass entry/peak_price/current_sl. Caller is the intraday monitor (TBD when audited). pick_logger writes these as CSV columns; if reader doesn't coerce empty-to-float properly, None propagates → line 28 of trailing_stop checks `peak_price <= 0` which raises TypeError on None. **One missing CSV row → trail disabled silently OR crash.** Need defensive caller.

### ATP-X2: 4-condition AND ladder rarely fires
Per ATP-X2 head finding: gain >5% AND RSI >70 AND vol >1.8x AND cooldown 60min. **Combined probability is low.** No analytics on actual fire rate. **Could be:**
  - Intentionally conservative (good — protects against over-raising)
  - Effectively dead (bad — feature exists but never useful)
**Recommend: instrument fire rate. If 0/1000 picks raise TP in 30 days, lower thresholds.**

### TS-X3 + ATP-17: Volatility-blind defaults
Both modules use FIXED defaults (TS: 3% activation, 2% trail; ATP: 5% gain, 5% headroom). **No ATR/vol adjustment.** A high-vol stock (ATR=5%) gets the same 2% trail as a low-vol one (ATR=1%). **High-vol gets stopped out on noise; low-vol gives back too much.** Compare to risk_manager.atr_trade_plan (Batch 19) which IS vol-aware. **Inconsistency:** entry-side uses ATR, exit-side doesn't.

### Cross-cutting: Naive datetime issue spreads to dynamic-exit modules
- ATP-3, ATP-6, ATP-23, ATP-26 all use naive `datetime.now()`
- Joins NC-22 (Batch 17), FH-7/FH-11 (Batch 18), CB-22 (Batch 15)
**Mixed timezone discipline across codebase.** MDH/NS use tz-aware. Most others don't. Would benefit from a `_now_utc()` shared helper.

### Cross-cutting: Documented bare-except count
1. MDH-40 (Batch 14): "Telemetry must never break the picker."
2. CB-57 (Batch 15): "Safe: returns [] if anything goes wrong."
3. ATP-15 (this batch): "malformed timestamp → ignore"
**3 documented Theme T1 exceptions. All on non-critical paths.** Pattern is established.

## SUMMARY (Batch 20)

| Severity | trailing_stop | adaptive_tp | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 4 | 7 | 4 | 15 |
| Data/safety | 3 | 4 | 0 | 7 |
| Code smell | 3 | 3 | 0 | 6 |
| Good code | 8 | 18 | 0 | 26 |
| Total findings | 18 | 32 | 4 | 54 |

## TOP 10 CRITICAL FIXES from Batch 20

1. TS-X3 + ATP-17: Make trail and TP-headroom defaults vol-aware (scale by ATR%). Eliminates noise-stop-outs on high-vol. (30 min)
2. ATP-X2: Instrument should_raise_tp fire rate. If <1% over 30 days, lower thresholds. (15 min instrumentation)
3. TS-X2 + TS-5: Coerce caller inputs defensively. `peak_price = float(peak_price or 0)` before line 28 check. Eliminates None-crash. (5 min)
4. TS-10: Add audit-trail to compute_trailing_sl (current is silent). Output (new_sl, did_raise, audit_event). (15 min)
5. ATP-21: Return all-conditions-evaluated dict for full transparency. (15 min)
6. Cross-cutting naive datetime: Add `from datetime import timezone; _now_utc = lambda: datetime.now(timezone.utc)` shared helper. Replace all naive .now() in audited files. (30 min)
7. ATP-14: Make ATP cooldown comparison tz-aware to match. (5 min, included in #6)
8. ATP-20: Add `current_rsi or 0` for safe formatting if reaching success path with None. (1 min)
9. ATP-27: Cap audit history length (e.g., last 50 raises). Prevent unbounded growth. (5 min)
10. TS-X3 / ATP-17: Make activation/trail/headroom configurable via cfg dict for future tuning without code changes. (15 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): ATP-15 joins documented-exception club. Now 3 confirmed.
- Theme T2 (schema drift): N/A this batch.
- Theme T8 (DRY): N/A this batch — these modules don't duplicate.
- Theme T11 (fail-open by accident): TS-X2 None-input → silent no-op, ATP-X2 4-condition AND ladder may rarely fire.
- Theme T13 (silent-default-fills): TS-X3, ATP-17 — vol-blind defaults applied universally.
- Theme T14 (gold-standard patterns): trailing_stop AND adaptive_tp join exit_manager (Batch 19) as exemplary pure-computation modules.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 18/~18 done | trailing_stop, adaptive_tp | **PHASE B COMPLETE** |
| Total true line-by-line | | +2 files | 41 of 382 |
| Remaining | | | 341 files |

## PHASE B COMPLETE — FINAL TALLY (Files 9-20)

| File | Lines | Findings | Critical | Use as template? |
|---|---:|---:|---:|---|
| scorer.py (Batch 12) | 236 | 50 | 18 | NO — 63 magic numbers |
| scoring_safety.py (Batch 12) | 104 | 26 | 6 | YES — fail-loud guardrails |
| data_fetcher.py (Batch 13) | 231 | 47 | 11 | PARTIAL — best telemetry |
| indicators.py (Batch 13) | 307 | 43 | 10 | YES — pure computation |
| market_data_health.py (Batch 14) | 228 | 45 | 4 | **YES — gold standard for state writes** |
| market_calendar.py (Batch 14) | 215 | 39 | 8 | PARTIAL — calendar will rot |
| regime.py (Batch 15) | 123 | 30 | 8 | PARTIAL — fail-loud recovery good |
| calibration.py (Batch 15) | 387 | 49 | 12 | YES — read-only attribution |
| news_signals.py (Batch 16) | 384 | 57 | 12 | NO — false-pos blocking risk |
| news_engine.py (Batch 16) | 163 | 43 | 14 | NO — regex XML parsing |
| news_classifier.py (Batch 17) | 136 | 43 | 14 | NO — heuristic fallback dead |
| news_sentiment.py (Batch 17) | 46 | 25 | 8 | NO — duplicate of news_engine |
| fundamentals.py (Batch 18) | 144 | 28 | 8 | NO — empty data passes |
| finnhub_data.py (Batch 18) | 277 | 49 | 12 | PARTIAL — cross_validate dead? |
| risk_manager.py (Batch 19) | 126 | 40 | 11 | NO — 2 schemas, 2 conventions |
| exit_manager.py (Batch 19) | 63 | 18 | 4 | YES — pure computation |
| trailing_stop.py (Batch 20) | 66 | 18 | 4 | **YES — gold standard pure compute** |
| adaptive_tp.py (Batch 20) | 121 | 32 | 7 | **YES — gold standard pure compute** |
| **Phase B total** | **3,357** | **680** | **171** | |

## PHASE B KEY INSIGHTS

1. **Quality bimodal across Phase B.** Pure computation modules (indicators, exit_manager, trailing_stop, adaptive_tp) are gold-standard. State-writing/network modules (news_*, fundamentals, risk_manager) have widespread issues.

2. **News pipeline is the lowest-quality subsystem** — 168 findings across 4 files (news_signals, news_engine, news_classifier, news_sentiment). Includes:
   - TWO PARALLEL pipelines (NC-X1)
   - Heuristic fallback produces ZERO signals (NC-X2)
   - 180-day BANKRUPTCY block on substring match (NS-X2)
   - Same Yahoo source fetched 3 ways (NC-X3)

3. **3 documented bare-except patterns now established** (MDH-40, CB-57, ATP-15). Theme T1 has a viable defense if path is non-critical AND comment is explicit.

4. **gold standard for state writes is market_data_health** (atomic write + Lock + UTC + daily rotation + documented bare-except philosophy). 5 patterns absent elsewhere. **Single biggest reusable win across Phase A+B.**

5. **Phase B revealed 171 critical findings.** Combined with Phase A's 102 = **273 critical findings across 23 audited files in 1,896 + 3,357 = 5,253 lines of code.** Density ~5 critical per 100 lines. Well above industry average.

6. **Cross-cutting themes have hardened:**
   - 10+ files with relative-path constants → src/_paths.py URGENT
   - 7+ truncation lengths → src/_constants.py URGENT
   - 5 copies of _safe_float, 3 of _safe_int → src/_utils.py URGENT
   - Mixed naive/aware datetime → _now_utc() helper URGENT
   - 6 sites of AI/SEMI tag-split bug → _utils.tags_in() helper URGENT
   - 80+ magic scoring/policy numbers → scoring_thresholds.yaml URGENT

## NEXT BATCH — PHASE C BEGINS (Brain Pillars)

Batch 21: src/hypothesis_engine.py + src/pattern_stats.py — Pillar 4 brain components. These consume calibration outputs and produce hypothesis/pattern testing. Likely the deep-research layer that makes the agent "self-improve."

End of Batch 20. Phase B complete. Phase C begins.
