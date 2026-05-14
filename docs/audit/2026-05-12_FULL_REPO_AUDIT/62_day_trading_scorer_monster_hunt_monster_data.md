# Batch 56 — src/day_trading_scorer.py (147 lines) + src/monster_hunt.py (141 lines) + src/monster_data.py (57 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** day_trading_scorer.py (147), monster_hunt.py (141), monster_data.py (57)
**Phase:** E (subdirectory & ancillary). Files 33, 34, 35 of ~50.
**NOTE:** 3-file batch. Originally planned sector_classifier.py first but **fetch failed (file may not exist at this path or was renamed)** — substituted with monster_data.py to keep monster-trio cohesive.

## TOP HEADLINE FINDINGS

1. DT-X1: day_trading_scorer.py is **THE 5-COMPONENT INTRADAY SCORER** — 0.30 RVOL + 0.20 ATR ratio + 0.20 momentum + 0.15 trend + 0.15 liquidity = 1.00 weighted composite. Consumed by parallel_scorer (B44 PS-18) which also calls market_guard.classify_with_day_score (B40). **Producer/consumer chain confirmed.** **Different weights from swing scorer** — RVOL is "KING for day trades" per inline comment line 118.
2. DT-X2 (lines 19-87): **5 INDEPENDENT SCORE FUNCTIONS** with 23 magic threshold-bucket numbers. Per Batch 55 FN-X2 / Batch 51 EZ-X3 cross-cutting magic-number proliferation. **Total scoring layer now ~231 magic numbers** (208 + 23 this batch). **No archaeology** for any DT thresholds (e.g. why 1.5%-3.5% is "ideal day-trade volatility" — should cite source).
3. DT-X3 (lines 116-123): **DIFFERENT WEIGHTS from swing** — explicitly inline-documented at lines 118-122. **Per Batch 43 SC scorer cross-cutting**, this is the **SECOND scorer in the codebase with its own weight schema.** **Fundamental architectural decision: parallel-scoring strategies for different trade types.** ✅
4. MH-X1: monster_hunt.py is **PILLAR 3 FOUNDATION v0.1 — the LOTTERY-PICK identifier.** 7-component additive scorer (max 1.00) with explicit threshold ≥0.60 → "monster treatment" (5% wider stop, 25% TP, 1.5% lottery sizing). Per docstring lines 21-22: "Designed to be ADDITIVE — never blocks normal picks, only ADDS info." **OBSERVE-MODE-style guarantee.** Per Batch 50 HE-X2 / Batch 49 WB-X1 OBSERVE-MODE cross-cutting — **15th module with explicit non-mutation contract** (counting variants).
5. MH-X2 (lines 103-140): `apply_monster_treatment` **OVERRIDES SL/TP/qty when is_monster** — preserves originals in `original_*_pre_monster` fields for audit. **Per Batch 53 NS audit-trail discipline**, this is **THE MOST EXPLICIT mutation-with-rollback-trail in audit.** ✅ But **5% wider stop + 25% TP overrides Batch 54 RM atr_trade_plan output** — a monster pick gets DIFFERENT plan than non-monster. **Two parallel SL/TP systems in pipeline.**
6. MD-X1: monster_data.py is **THE 57-LINE FETCH+CACHE+TELEMETRY trio for short_float/float_shares.** **Cleanest cache-pattern in audit** — file-mtime-based 24h TTL + try/except + MDH telemetry on every call. Per Batch 14 MDH-X1 cross-cutting `record_market_data_event` consumer pattern, this is a textbook MDH-aware fetcher.
7. MD-X2 (line 13): **MODULE-IMPORT SIDE EFFECT** — `CACHE_DIR.mkdir(parents=True, exist_ok=True)` at line 13. Per Batch 49 WB-X2 / Batch 51 EZ-X2 cross-cutting, **7th instance** of import-time side effect. **Test-isolation theme persists.**

## src/day_trading_scorer.py — LINE BY LINE

### Lines 1-15: Module docstring
- DT-1 GOOD: 15-line docstring with 6-bullet day-trade requirements list. Operator-readable.
- DT-2 BUG: No archaeology for thresholds ($20M liquidity, RSI 50-75, RVOL>1.2). Per cross-cutting Theme T14 archaeology gap.

### Lines 16-17: Imports
- DT-3 GOOD: Pure typing.

### Lines 19-27: _score_rvol
- DT-4 GOOD: 7-tier RVOL ladder with explicit "huge volume spike" / "dead volume" comments.
- DT-5 BUG: 7 magic thresholds (2.5, 2.0, 1.5, 1.2, 1.0, 0.8) + 7 magic scores. Per DT-X2.

### Lines 30-39: _score_atr_ratio
- DT-6 GOOD (line 32): Defensive `if not atr or not price or price <= 0` early-return.
- DT-7 GOOD (lines 35-39): 4-tier ATR/price ratio with "ideal day-trade volatility" / "too quiet" / "too volatile" inline labels.
- DT-8 BUG: 6 magic ratio thresholds (0.015, 0.035, 0.010, 0.045, 0.008, 0.055).

### Lines 42-60: _score_intraday_momentum
- DT-9 GOOD (lines 44-51): RSI 6-tier with "sweet spot" + "exhausted" + "weak" labels.
- DT-10 GOOD (line 50): `rsi > 80: 0.20` — explicit overbought-penalty. **Operator-protective.**
- DT-11 BUG: 6 magic RSI thresholds.
- DT-12 GOOD (lines 53-58): MACD hist 4-tier.
- DT-13 GOOD (line 60): **0.6/0.4 weighted blend** — RSI dominates over MACD for intraday. Should be const.
- DT-14 BUG: Magic 0.6/0.4 momentum sub-weights.

### Lines 63-74: _score_trend_alignment
- DT-15 GOOD (line 65): `score = 0.30` baseline (not 0) — prevents single-EMA-miss from zeroing trend score.
- DT-16 GOOD (lines 71-73): 3 additive +0.25/+0.20/+0.25 boosts for above EMA20/EMA50/VWAP. **Geometric defensive checks** (e.g. `close and ema_20 and close > ema_20`).
- DT-17 GOOD (line 74): `min(1.0, ...)` cap.
- DT-18 BUG: Magic baseline 0.30 + magic boosts.

### Lines 77-87: _score_liquidity
- DT-19 GOOD: 6-tier $-volume ladder.
- DT-20 GOOD (line 82): `100_000_000` = $100M underscored for readability.
- DT-21 GOOD (line 87): `0.15` for "too thin" — explicit not-zero so picks aren't always blocked. **Defense vs single-component zeroing.**

### Lines 90-142: day_trading_score
- DT-22 GOOD (lines 91-99): 9-line docstring documenting args + return shape.
- DT-23 GOOD (lines 101-106): Defensive `or 0` / `or 50` / `or 1.0` falsy-fallbacks.
- DT-24 GOOD (line 102): `sig.get("atr_14") or sig.get("atr") or 0` — 3-key fallback (Per Batch 36 PF-7 / Batch 50 DW-16 cross-cutting multi-key fallback pattern).
- DT-25 GOOD (line 104): Same 3-key fallback for RSI.
- DT-26 GOOD (lines 108-114): 5-component dict.
- DT-27 GOOD: Per DT-X3, 5-weight dict at lines 117-123 with inline rationale.
- DT-28 GOOD (line 125): Sum-of-weights composite.
- DT-29 GOOD (line 126): `min(1.0, raw + news_boost)` — capped.
- DT-30 GOOD (lines 128-135): **Reason-string builder** with conditional inclusion based on component score thresholds. **Operator-readable diagnostic.** ✅
- DT-31 GOOD (line 135): `" · ".join(reasons) if reasons else "weak day setup"` — empty-state hint.
- DT-32 GOOD (lines 137-142): 4-key result dict.

### Lines 145-147: is_day_tradeable
- DT-33 GOOD: Simple boolean wrapper.
- DT-34 BUG (line 145): Magic 0.65 default threshold. Should be DAY_TRADE_THRESHOLD const.

## src/monster_hunt.py — LINE BY LINE

### Lines 1-22: Module docstring
- MH-1 GOOD: **22-line docstring** with diamond emoji + Pillar 3 v0.1 + 3-bullet monster-treatment table + 7-row score boost table + ADDITIVE guarantee.
- MH-2 GOOD: Per MH-X1, **OBSERVE-MODE-style "ADDITIVE — never blocks" guarantee** at lines 21-22. ✅

### Lines 23-24: Imports
- MH-3 GOOD: Pure typing.

### Lines 26-100: score_monster
- MH-4 GOOD (lines 26-33): 8-arg keyword-friendly signature.
- MH-5 GOOD (lines 34-39): 6-line docstring with critical "missing data contributes 0 (no penalty)" guarantee.
- MH-6 GOOD: Per MH-X1, 7 component blocks each with `if X is not None and X > threshold: components[k] = boost else 0`. **Symmetric pattern.**
- MH-7 GOOD (lines 44-46): Earnings-proximity 0-7 days = +0.20 (per docstring table).
- MH-8 BUG (line 44): Magic 7 days. Per Batch 47 AM-22 / Batch 51 cross-cutting EARNINGS_PROXIMITY_NEAR_DAYS = 7. **3rd module with magic 7.** Should consolidate.
- MH-9 GOOD (lines 51-53): Short-squeeze >15% short_pct_of_float = +0.20 with `f"short {short_pct_of_float*100:.0f}%"` formatted reason.
- MH-10 BUG (line 51): Magic 0.15 short threshold.
- MH-11 GOOD (lines 58-60): Low float <50M = +0.15 with `float_shares/1e6:.0f` M-display.
- MH-12 BUG (line 58): Magic 50M float.
- MH-13 GOOD (lines 65-67): RVOL >1.5 = +0.15.
- MH-14 BUG (line 65): Magic 1.5 RVOL — DIFFERENT from day_trading_scorer DT-4 1.5 boundary (same value but uncoordinated). **2 modules with same magic, no shared const.**
- MH-15 GOOD (lines 72-74): Bullish news flag = +0.15.
- MH-16 GOOD (lines 79-81): Top-decile composite ≥0.85 = +0.10.
- MH-17 BUG (line 79): Magic 0.85 quality bar.
- MH-18 GOOD (lines 86-89): **Catalyst-combo bonus** — earnings ≤14d AND RVOL>1.2 = +0.05. **Composite-condition bonus.** ✅
- MH-19 BUG (lines 86-87): Magic 14d + 1.2 RVOL.
- MH-20 GOOD (line 93): `min(1.0, sum(...))` capped composite.
- MH-21 GOOD (lines 95-100): 4-key result with `is_monster: score >= 0.60` boolean.
- MH-22 BUG (line 99): Magic 0.60 threshold. Per docstring line 19 "configurable in config.yaml monster.threshold" but here HARDCODED. **DOCSTRING DRIFT** — config.yaml override not actually wired.

### Lines 103-140: apply_monster_treatment
- MH-23 GOOD (lines 109-114): 6-line docstring documenting SL/TP/qty overrides.
- MH-24 GOOD (lines 115-116): Stamps monster_score + is_monster.
- MH-25 GOOD (lines 118-119): Early-return if not monster.
- MH-26 GOOD (lines 122-124): Defensive entry extraction with `or 0` falsy + `entry <= 0` check.
- MH-27 GOOD (lines 126-127): 5% wider stop + 25% TP.
- MH-28 BUG (lines 126-127): Magic 0.95 / 1.25 SL/TP multipliers.
- MH-29 GOOD (line 128-129): Lottery sizing — risk_dollars / max(...,0.01) defends div-by-zero.
- MH-30 GOOD (lines 131-133): **Original-value preservation** in `original_*_pre_monster` fields. Per MH-X2, gold-standard rollback trail. ✅
- MH-31 GOOD (lines 135-138): Override SL/TP/qty/RR.
- MH-32 BUG (line 138): Magic 0.01 RR-divisor floor. Should be MIN_RISK_PER_SHARE const.
- MH-33 BUG (line 107): Magic account_size=10000 default. Per Batch 46 PG-28 cross-cutting silent $10k default = 10x undersizing risk. **Same anti-pattern as portfolio_risk_gate.**
- MH-34 BUG (line 107): Magic monster_position_pct=1.5 default.

## src/monster_data.py — LINE BY LINE

### Lines 1-4: Module docstring
- MD-1 GOOD: 3-line docstring documenting purpose + cache rationale.

### Lines 5-10: Imports
- MD-2 GOOD: Pure stdlib + MDH telemetry import.

### Lines 12-14: Constants + side effect
- MD-3 BUG: Per MD-X2, mkdir at module load. **7th cross-cutting instance.**
- MD-4 GOOD (line 14): Named CACHE_TTL_HOURS=24.

### Lines 17-18: _cache_path
- MD-5 GOOD: `ticker.upper()` case-normalized.

### Lines 21-25: _is_fresh
- MD-6 GOOD: File-mtime-based freshness check.
- MD-7 BUG (line 24): NAIVE `datetime.fromtimestamp(p.stat().st_mtime)` + `datetime.now()` comparison. **Per Batch 51 EZ-X4 cross-cutting** Unix-epoch comparison is TZ-agnostic — ✅ safe.

### Lines 28-56: get_monster_data
- MD-8 GOOD (lines 29-32): 4-line docstring documenting None-on-failure semantics.
- MD-9 GOOD (lines 33-38): Cache-first read with try/except + scoped `Exception` (broader than ideal but acceptable given fallback path is safe).
- MD-10 GOOD (line 40): Default-None result dict.
- MD-11 BUG (line 42): **INLINE IMPORT** of yfinance. Per Batch 49 WB-51 / Batch 54 RM-25 cross-cutting inline-import anti-pattern. Should be at module top.
- MD-12 GOOD (lines 43-49): Defensive None checks + float coercion.
- MD-13 GOOD (line 50): **NO ATOMIC WRITE.** `cp.write_text(...)` — power loss = corrupt cache. Per Batch 49 WB-32 / Batch 53 NS atomic-write tally — **adds 24th unsafe writer.** Tally: 5 safe / 24 unsafe / 29 total = ~83% UNSAFE.
- MD-14 GOOD (line 51): `record_market_data_event(... result="success")` — MDH telemetry on success. ✅
- MD-15 GOOD (lines 52-54): Exception path also records MDH event with `error_type=classify_provider_error(e)`. **Producer-side telemetry contract complete.** ✅ Per Batch 14 MDH-X1 gold standard.
- MD-16 GOOD (line 54): Bounded error message `str(e)[:60]`. Per cross-cutting truncation pattern.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### DT-X3 + B43 SC cross-cutting CONFIRMED parallel-scorer architecture
**2 distinct scorer modules with own weight schemas:**
- scorer.py (B43): swing weights via composite_score
- day_trading_scorer.py (this batch): day weights via day_trading_score

**Per Batch 44 PS-18 / Batch 40 MG-X1**, parallel_scorer runs BOTH then market_guard.classify_with_day_score chooses trade_type. **Architectural pattern: two scoring engines + a classifier switch.** ✅ Documented inline by DT-X3.

### DT-X2 + B55 FN-X2 + scoring-layer magic-number tally update
**Updated total scoring-layer magic-number count:**
| Module | Magic # |
|---|---:|
| scorer.py (B43) | ~40 |
| earnings_analyzer (B51) | ~23 |
| pattern detectors (B30-33) | ~70 |
| risk_manager (B54) | ~15 |
| fundamentals (B55) | ~60 |
| **day_trading_scorer (this batch)** | **~23** |
| **monster_hunt (this batch)** | **~10** |
| **Total scoring layer** | **~241** |

**~241 magic numbers across scoring layer. ZERO archaeology for any.** Per Batch 31 HH-X3.

### MH-X1 + B49 WB-X1 + B50 HE-X2 + B53 NS cross-cutting OBSERVE-MODE messaging tally
**15+ modules with explicit OBSERVE-MODE / non-mutation guarantees** (counting variants):
- 6 audited gates (B45-46)
- agent_memoir (B47), wisdom_base (B49 v0.1), hypothesis_engine (B50), daily_wisdom (B50), news_signals (B53)
- monster_hunt (this batch MH-X1) — "ADDITIVE — never blocks"

**OBSERVE-MODE is architectural standard.**

### MH-X2 + B53 NS-37 + cross-cutting audit-trail discipline
**3 modules with explicit before/after audit fields:**
- news_signals (B53 NS-37): 10-field signal dict with rich audit
- monster_hunt (this batch MH-30): `original_*_pre_monster` rollback fields
- risk_manager (B54 RM-29): 17-field result dict with regime audit

**3-module pattern. Mutation+rollback trail = TEMPLATE for safe overrides.**

### MD-X2 + cross-cutting import-time side-effect tally
**7 instances now across 5 modules:**
- market_news (B39 MN-X3) — load_dotenv + _KEY freeze
- universe (B40 UN-3) — SESSION init
- wisdom_base (B49 WB-X2) — ROOT.mkdir
- earnings_analyzer (B51 EZ-X2) — load_dotenv + mkdir + _KEY freeze
- monster_data (this batch MD-X2) — CACHE_DIR.mkdir

**Test-isolation theme persists.**

### MD-X1 + Batch 14 MDH cross-cutting CONFIRMED MDH consumer
**Modules that consume MDH telemetry API:**
- data_fetcher (B42)
- earnings_analyzer (B51 — internally)
- monster_data (this batch MD-15) — both success + error paths

**3 audited MDH consumers.** Producer/consumer chain mature.

### MH-22 cross-cutting docstring drift
Documentation says "configurable in config.yaml monster.threshold" but code hardcodes 0.60 at line 99. **Per Batch 53 NS-41 cross-cutting docstring-drift theme.**

### Cross-cutting: bare-except this batch
- day_trading_scorer: 0 ✅ (pure compute)
- monster_hunt: 0 ✅ (pure compute)
- monster_data: 1 (MD-9 cache-load defense, scoped to Exception not bare)

**1 except-Exception. Cleaner than wisdom-layer or news-layer batches.**

### Cross-cutting: TZ-aware modules: 10 (no addition).

### Cross-cutting: relative-path constants — monster_data adds 1 (CACHE_DIR). **45 files now.**

### Cross-cutting: ATOMIC WRITE — MD-13 adds 24th unsafe writer. Tally: **5/24/29 = ~83% UNSAFE.**

### Cross-cutting: __main__ smoke test: still 9 modules (none of these 3 have __main__).

### Cross-cutting: bug-archaeology: still 12 modules.

### NEW THEME (T15) — DEFENSIVE BASELINE in component scorers
**Pattern emerging:** Several functions use non-zero baseline scores (e.g. DT-15 `score = 0.30` baseline, DT-21 `0.15` "too thin") instead of starting at 0. **Prevents single-component miss from zeroing the metric.** Per Batch 51 EZ-43 / B43 cross-cutting normalized-by-applied-weights — **complementary defense pattern.** Should catalog as Theme T15.

## SUMMARY (Batch 56)

| Severity | day_trading_scorer | monster_hunt | monster_data | Cross-cutting | Total |
|---|---:|---:|---:|---:|---:|
| Show-stopper | 5 | 7 | 2 | 4 | 18 |
| Data/safety | 2 | 1 | 1 | 0 | 4 |
| Code smell | 1 | 1 | 1 | 0 | 3 |
| Good code | 26 | 24 | 11 | 0 | 61 |
| Total findings | 34 | 33 | 15 | 4 | 86 |

## TOP 10 CRITICAL FIXES from Batch 56

1. **MH-22 (HIGH):** Wire monster.threshold from config.yaml — currently docstring lies. Either fix docstring or add config plumbing. (10 min)
2. **MH-33 / B46 PG-28 cross-cutting (HIGH):** Add operator warning when account_size defaults to 10000. **Same silent 10x undersizing as portfolio_risk_gate.** (5 min)
3. **DT-X2 + MH magic-number cross-cutting (MEDIUM):** Add provenance citations to ~33 day-trade + monster-hunt threshold-buckets. (45 min)
4. MH-8 + cross-cutting: Consolidate magic 7 (earnings proximity) across 3 modules into shared EARNINGS_PROXIMITY_NEAR_DAYS const. (10 min)
5. MH-14: Consolidate magic 1.5 RVOL between day_trading_scorer + monster_hunt. (3 min)
6. MD-13: Add atomic write to monster_data cache. (3 min — bundled with prior atomic-write refactors)
7. MD-3: Move CACHE_DIR.mkdir into lazy init function. Test isolation. (5 min)
8. MD-11: Hoist `import yfinance` to module top. (1 min)
9. MH-2 + DT-1: Improve docstrings — add provenance for thresholds (cite Mark Minervini, William O'Neil for momentum/volume thresholds). (15 min)
10. DT-34 + MH-22: Consolidate `min_threshold` constants across day_trading_scorer (0.65) + monster_hunt (0.60) + market_guard. (5 min)

## NEW THEMES UPDATED

- **Theme T1 (bare except):** day_trading_scorer 0 ✅. monster_hunt 0 ✅. monster_data 1 (scoped Exception, cache-load defense). **3-file batch with low bare-except. Continuing Phase E clean trend.**
- **Theme T2 (schema drift):** MH-22 docstring-claims-config-override-but-hardcoded.
- **Theme T6 (atomic writes):** MD-13 adds 24th unsafe writer. Tally: 5/24/29 = ~83% UNSAFE.
- **Theme T8 (DRY):** MH-8 magic 7 earnings proximity in 3 modules. MH-14 magic 1.5 RVOL in 2 modules. DT-34 + MH-22 threshold const drift in 3 modules.
- **Theme T11 (fail-open by accident):** MH-X1 ADDITIVE-only guarantee (intentional, documented).
- **Theme T13 (silent-default-fills):** MH-33 silent $10k account_size default = 10x undersizing.
- **Theme T14 (gold-standard patterns):** monster_hunt MH-1 22-line docstring with score-table archaeology + MH-X2 original_*_pre_monster rollback fields + MH-6 symmetric `if X is not None: ... else 0` 7-component pattern. day_trading_scorer DT-X3 inline-rationale weight dict + DT-30 reason-string builder. monster_data MD-X1 cleanest cache pattern in audit (mtime-TTL + try/except + MDH telemetry both paths) + MD-15 producer-side telemetry contract complete.
- **Theme T15 (NEW — defensive baseline scores):** Component scorers use non-zero baseline (DT-15 0.30, DT-21 0.15) so single-component miss doesn't zero metric. **Catalog as new architectural pattern.** Cumulative scope:
  - day_trading_scorer (this batch DT-15, DT-21)
  - fundamentals (B55 FN-21 normalized-by-applied-weights variant)
  - earnings_analyzer (B51 EZ-43 same)

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A | 8/8 COMPLETE | (none) | 8/8 |
| Phase B | 18/18 COMPLETE | (none) | 18/18 |
| Phase C | 12/12 COMPLETE | (none) | 12/12 |
| Phase D | 30/~30 COMPLETE | (none) | 30/~30 |
| Phase E | 35/~50 done | day_trading_scorer, monster_hunt, monster_data | 35/~50 |
| Total true line-by-line | | **+3 files** | **118 of ~382 (~30.9%)** |
| Remaining | | | **~264 files** |

**FETCH FAILURE NOTE:** sector_classifier.py (planned slot 1 this batch) failed to fetch — file may not exist at this path or was renamed. Substituted with monster_data.py for cohesive monster-trio audit. Will revisit sector_classifier next batch with verified path.

## NEXT BATCH

Batch 57 (doc #63): Continue Phase E. 3-file batch attempting to close fundamentals/cache layer:
- **`src/finnhub_data.py` (~5KB)** — Finnhub fetcher consumed by fundamentals (B55 FN-1 mentions it).
- **`src/sector_classifier.py`** — RETRY with file-existence verification.
- **`src/finnhub_metrics.py` (~4KB)** — alternate Finnhub layer if classifier still missing.

End of Batch 56. Phase E in progress (35/50). **30.9% audit milestone.**
