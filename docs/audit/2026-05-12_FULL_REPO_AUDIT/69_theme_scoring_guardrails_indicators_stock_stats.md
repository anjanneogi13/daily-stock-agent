# Batch 63 — src/theme_scoring_guardrails.py (95 lines) + src/indicators.py (307 lines) + src/stock_stats.py (321 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** theme_scoring_guardrails.py (95), indicators.py (307), stock_stats.py (321)
**Phase:** F (extended coverage). Files 4, 5, 6 of ~38.
**NOTE:** Trio closes the SCORING/PROBABILITY producer side: theme guardrail (sister of B62 SS-X1), indicators (the 30+ TA producer consumed by scorer B62 SC-X1), stock_stats (Layer 1 base rates consumed by probability_engine B62 PR-X1).

## TOP HEADLINE FINDINGS

1. TG-X1: theme_scoring_guardrails.py is **THE SISTER GUARDRAIL of scoring_safety** (B62 SS-X1). Per docstring lines 1-7: explicitly disables theme-aware production scoring. **5 future-fields list + 7 prerequisites tuple + 6 safety flags dict + frozen dataclass + assert function + explainer.** Per Batch 62 SS-X2 cross-cutting composite-guardrail pattern, TG is the OTHER half. **Together: 2-guardrail safety net** preventing legacy SEMI/AI boost AND theme-aware scoring from accidentally activating.
2. TG-X2 (lines 23-31): **REQUIRED_PREREQUISITES = 7-item tuple** (historical_validation, forward_observation, train_test_discipline, overfitting_review, clear_tests, founder_approval, readiness_gate_preserved). **First audited explicit-prerequisite gate.** Per Batch 60 PSt-X3 OBSERVE→ENFORCE / Batch 50 HE-X2 OBSERVE-MODE cross-cutting — **most-formal observe-mode contract in audit** (states what must happen before flip).
3. IN-X1: indicators.py is **THE FULL TA INDICATOR SUITE** (307 lines). 11+ indicator producers (sma/ema/rsi/macd/bollinger/atr/stochastic/obv/parabolic_sar/vwap/adx/candlestick/fibonacci/support_resistance) + composite `add_indicators` + `latest_signals`. Consumed by scorer (B62 SC-X1) `_enhanced_indicator_score`. **Per Batch 62 SC-X1 cross-cutting**, this CLOSES the scoring producer side end-to-end (indicators → scorer → composite → parallel_scorer → ...).
4. IN-X2 (lines 197-236, 239-306): **2-PHASE INDICATOR PIPELINE** — `add_indicators(df)` decorates DataFrame with ~25 indicator columns, then `latest_signals(df)` extracts last-row dict + computes 8 derived flags (above_psar, stoch_oversold, di_bullish, etc.). **Per Batch 36 PF cross-cutting indicator pipeline** — first audit at the SOURCE. Schema-stable design: schema-stable downstream consumers.
5. IN-X3 (lines 122-152): **`candlestick_patterns`** — 6 patterns (bullish_engulfing / bearish_engulfing / hammer / shooting_star / doji / morning_star / evening_star) with **derived bullish_signal + bearish_signal aggregates**. **Per Batch 30-33 patterns/* cross-cutting**, this is **OUTSIDE the patterns/ subdir** — second pattern-detection layer parallel to formal detector classes. **Architectural duplication: candlestick patterns LIVE HERE not in patterns/.**
6. SS3-X1: stock_stats.py is **PILLAR 1 / LAYER 1 — THE PROBABILITY-ENGINE BASE-RATE PRODUCER** (321 lines). 5 statistical computers (returns / volatility / atr / drawdowns / bounce_rates) → JSON profile per ticker → consumed by probability_engine (B62 PR-Layer1). **Per Batch 62 PR-X1 cross-cutting**, CLOSES probability engine producer side end-to-end. **First audited "EMPIRICAL REPLACES ARBITRARY" module** — per docstring lines 11-12.
7. SS3-X2 (lines 239-298): **2 EMPIRICAL DECISION HELPERS** — `empirical_sl_pct(target_p_noise=0.30)` returns the percentile of daily moves where P(noise) ≈ target; `empirical_tp_pct(days=5, target_p_reach=0.50)` returns N-day forward return at quantile 1-target. **Per Batch 62 PR-X2 / Batch 53 NS-X2 / Batch 58 WP-X2 cross-cutting fully-documented gold standard** — joins as **8th module** with full inline mathematical archaeology + concrete example use cases.

## src/theme_scoring_guardrails.py — LINE BY LINE

### Lines 1-7: Module docstring
- TG-1 GOOD: 7-line docstring with **Priority 8 explicit non-enablement clause.**
- TG-2 GOOD: "future work must make an explicit, reviewed change before theme intelligence can affect official scores" — **operator-binding contract.**

### Lines 9-12: Imports
- TG-3 GOOD: `from __future__ import annotations` + dataclass + Any.

### Lines 15-21: FUTURE_THEME_SCORING_FIELDS
- TG-4 GOOD: 5-tuple of forward-declared fields. **Documents the un-built feature surface.**

### Lines 23-31: REQUIRED_PREREQUISITES
- TG-5 GOOD: Per TG-X2, 7-item formal prerequisite list.
- TG-6 GOOD (line 30): "founder_approval" — explicit human gate (not just tests).

### Lines 33-40: THEME_SCORING_SAFETY_FLAGS
- TG-7 GOOD: 6-key flag dict, all defaulting False.
- TG-8 GOOD (lines 37-39): paper_trading + live_trading + buy_instructions also gated. **Defense-in-depth** beyond just scoring.

### Lines 43-54: ThemeScoringStatus dataclass
- TG-9 GOOD: **`@dataclass(frozen=True)`** — IMMUTABLE. **First audited frozen dataclass.** Per Batch 58 WP-10 / Batch 59 CL-23 / Batch 62 PR-14/PR-17 cross-cutting dataclass usage — **5th audited dataclass + first frozen.** ✅ Best practice for status records.
- TG-10 GOOD (line 53-54): References REQUIRED_PREREQUISITES + FUTURE_THEME_SCORING_FIELDS as default values — single source of truth.

### Lines 57-59: theme_scoring_status
- TG-11 GOOD: 1-line wrapper returning `asdict()`.

### Lines 62-84: assert_theme_scoring_disabled
- TG-12 GOOD (lines 63-67): 5-line docstring explaining gate purpose + scope.
- TG-13 GOOD (lines 68-71): Defensive type checks with explicit RuntimeError.
- TG-14 GOOD (lines 73-78): **4-key enabled-keys set** (multiple aliases checked).
- TG-15 GOOD (lines 79-84): **Accumulate violations + sorted error message.** Per Batch 62 SS-14 cross-cutting same composite-error pattern.

### Lines 87-94: explain_theme_scoring_guardrail
- TG-16 GOOD: Human-readable single-paragraph explanation for docs/reports. Operator-friendly.
- TG-17 GOOD (lines 91-93): Explicitly names ALL 7 prerequisites in prose.

## src/indicators.py — LINE BY LINE

### Lines 1-3: Module docstring + imports
- IN-1 GOOD: 1-line docstring.
- IN-2 BUG: Undersells — 11+ indicators + composite + latest_signals deserve full mention.
- IN-3 GOOD: pandas + numpy.

### Lines 10-15: sma / ema
- IN-4 GOOD: 1-line each. Pure pandas.

### Lines 18-23: rsi
- IN-5 GOOD (line 22): `loss.replace(0, np.nan)` — div-by-zero guard. Per cross-cutting defensive pattern.

### Lines 26-32: macd
- IN-6 GOOD: Standard 12/26/9 defaults.

### Lines 35-38: bollinger
- IN-7 GOOD: 20-period / 2σ defaults. Returns 3-tuple.

### Lines 41-48: atr
- IN-8 GOOD: True Range max-of-3 implementation.
- IN-9 GOOD (lines 43-47): pd.concat with `.max(axis=1)` — clean idiomatic.

### Lines 55-60: stochastic
- IN-10 GOOD (line 58): `(high_max - low_min).replace(0, np.nan)` — div-by-zero guard.

### Lines 63-65: obv
- IN-11 GOOD (line 64): `np.sign(...).fillna(0)` — defensive None handling.

### Lines 68-91: parabolic_sar
- IN-12 GOOD (lines 68-69): 4-arg signature with standard 0.02/0.20 acceleration.
- IN-13 GOOD (lines 71-91): Manual loop implementation — per Batch 50 HE-X3 dependency-minimization (no TA-Lib dep) ✅.
- IN-14 GOOD (line 80, 86): `low[max(i-2, 0)]` — boundary defensive.

### Lines 94-99: vwap
- IN-15 GOOD: Rolling VWAP with div-by-zero guard.

### Lines 102-119: adx
- IN-16 GOOD: 3-line docstring with ">25 = strong trend" semantic.
- IN-17 GOOD (lines 110-113): up_move / down_move with explicit conditions.
- IN-18 GOOD (line 117): div-by-zero guard.

### Lines 122-152: candlestick_patterns
- IN-19 GOOD (line 123-124): Length guard.
- IN-20 GOOD (lines 125-131): Last/prev/prev2 row extraction with defensive 1e-9 floors.
- IN-21 GOOD (lines 133-148): 6-pattern dict comprehension.
- IN-22 BUG: Magic 2× (hammer/shooting_star wick threshold), 0.1 (doji body ratio), 0.3 (star body ratio). No archaeology.
- IN-23 GOOD (lines 150-151): **Aggregated bullish/bearish signals** for downstream consumption. ✅
- IN-24 BUG: Per IN-X3 head finding, candlestick patterns DUPLICATE the patterns/ subdirectory pattern-detection architecture.

### Lines 155-168: fibonacci_levels
- IN-25 GOOD: 7-tuple of fib retracement levels (0/23.6/38.2/50/61.8/78.6/100).
- IN-26 GOOD (line 156): 60-day lookback default.

### Lines 171-190: support_resistance
- IN-27 GOOD (lines 175-179): Window-based local high/low detection.
- IN-28 GOOD (lines 181-184): Closest above/below filtering with fallback to overall high/low.
- IN-29 GOOD (lines 188-189): Distance % computation rounded to 2 decimals.
- IN-30 BUG (line 171): Magic `lookback=60`, `window=5`. Per cross-cutting magic-number theme.

### Lines 197-236: add_indicators
- IN-31 GOOD (line 198-199): Empty-df early return.
- IN-32 GOOD (line 200): `.copy()` — no caller mutation. ✅
- IN-33 GOOD (lines 203-234): Decorate with **22 indicator columns** in single function.
- IN-34 GOOD (lines 223-226): try/except around parabolic_sar (numerically tricky).
- IN-35 BUG (line 225): bare except → np.nan. Per Theme T1 — should be scoped (KeyError, ValueError, IndexError).
- IN-36 GOOD (line 234): vol_ratio computed inline.

### Lines 239-306: latest_signals
- IN-37 GOOD (lines 240-241): Empty-df early return.
- IN-38 GOOD (lines 245-247): **`_f` helper** for NaN-safe float coercion. Per Batch 47 / Batch 51 cross-cutting NaN defense.
- IN-39 GOOD (lines 249-264): **22-key default-None scaffold** — schema-stable. Per Batch 51 EZ-23 / Batch 57 FH-15 cross-cutting same pattern.
- IN-40 GOOD (lines 251): `prev_close` defensive default to current close on length<2.
- IN-41 GOOD (lines 267-271): bb_position computation with div-by-zero default 0.5.
- IN-42 GOOD (lines 273-282): 5 derived boolean flags (above_psar, stoch_oversold, stoch_overbought, obv_rising, strong_trend, di_bullish) — operator-readable semantic flags.
- IN-43 GOOD (lines 285-290): VWAP position with above_vwap + distance_pct.
- IN-44 GOOD (lines 293-297): try/except around candlestick — wraps with `cdl_*` prefix.
- IN-45 BUG (line 296): bare except pass. Theme T1.
- IN-46 GOOD (lines 300-304): try/except around fibonacci + support_resistance.
- IN-47 BUG (line 303): bare except pass.
- IN-48 GOOD (lines 295): `cdl_*` prefix avoids namespace collision in returned dict.

## src/stock_stats.py — LINE BY LINE

### Lines 1-17: Module docstring
- SS3-1 GOOD: **17-line docstring** with Pillar 1 + Layer 1 + 5 statistic types + "EMPIRICAL REPLACES ARBITRARY" mission + 3 doc references.

### Lines 18-32: Imports
- SS3-2 GOOD: Defensive `try: import yfinance` with YF_OK flag. Per Batch 51 cross-cutting **import-failure-tolerance pattern.** ✅
- SS3-3 GOOD (lines 28-32): YF_OK feature-flag exported globally.

### Lines 34-39: Configuration
- SS3-4 GOOD: 5 named constants with operator-readable comments.
- SS3-5 GOOD (line 36): `365 * 2` — readable expression vs magic 730.
- SS3-6 GOOD (lines 37-39): RETURN_WINDOWS / VOL_WINDOWS / PERCENTILES — explicit ranges. ✅

### Lines 44-61: _fetch_history
- SS3-7 GOOD (line 46-47): YF_OK guard.
- SS3-8 GOOD (lines 51-55): yfinance fetch with auto_adjust=False.
- SS3-9 GOOD (line 56): `len(df) < 60` — empirically-meaningful minimum.
- SS3-10 GOOD (line 58): `df.rename(columns=str.lower)` — schema normalization.
- SS3-11 BUG (line 60): bare except → None. Theme T1. Should track failure type for MDH telemetry (per Batch 14 MDH-X1 cross-cutting).

### Lines 64-89: _compute_returns
- SS3-12 GOOD (lines 65-68): Docstring with example output structure.
- SS3-13 GOOD (lines 75-76): Forward return computation + NaN filter.
- SS3-14 GOOD (line 77): n<30 skip — minimum statistical significance.
- SS3-15 GOOD (lines 79-87): 9-stat dict per window (n + mean + std + skew + kurtosis + 7 percentiles).
- SS3-16 GOOD (line 87): All percentiles computed in single loop.

### Lines 92-111: _compute_volatility
- SS3-17 GOOD: Daily returns base.
- SS3-18 GOOD (line 109): **Annualized via ×√252.** Standard finance convention. ✅

### Lines 114-132: _compute_atr
- SS3-19 GOOD (lines 117-122): True Range computation with `np.roll` + boundary fix.
- SS3-20 GOOD (lines 123): 3 windows (14/30/60).
- SS3-21 GOOD (lines 128-131): atr_abs + atr_pct dual output.

### Lines 135-151: _compute_drawdowns
- SS3-22 GOOD (lines 140-141): cummax-based drawdown.
- SS3-23 GOOD (line 142): "ignore flat periods" filter (drop -1% threshold).
- SS3-24 GOOD (lines 145-151): 5-key drawdown summary.

### Lines 154-186: _compute_bounce_rates
- SS3-25 GOOD (lines 155-158): **3-line docstring with concrete trader-friendly example** ("If NVDA drops 3%, P(recovery in 5 days) = ?"). Operator-readable. ✅
- SS3-26 GOOD (line 164): 4 drop levels (1/2/3/5%).
- SS3-27 GOOD (lines 169-180): 5d + 10d recovery windows with prior-peak comparison.
- SS3-28 BUG (line 174): `prior_peak = closes[max(0, d-5):d].max()` — uses past 5d high. **5d arbitrary** but reasonable as "recent peak."
- SS3-29 GOOD (lines 181-185): Per-drop bounce rate dict.

### Lines 191-215: compute_stock_stats
- SS3-30 GOOD (line 192-194): 3-line docstring.
- SS3-31 GOOD (lines 196-198): None on fetch failure.
- SS3-32 GOOD (lines 202-214): **11-key complete profile dict** with metadata (computed_at + data_start + data_end + n_days + current_price) + 5 stat-categories.
- SS3-33 BUG (line 204): NAIVE `datetime.now().strftime(...)`. Per Batch 49 LG-X4 cross-cutting (acceptable for human-readable display).

### Lines 218-223: save_stats
- SS3-34 GOOD (line 220): mkdir parents.
- SS3-35 BUG: **NO ATOMIC WRITE.** Per cross-cutting. Adds 32nd unsafe writer. Tally: 5/32/37 = ~86% UNSAFE.
- SS3-36 GOOD (line 222): indent=2 — git-friendly.

### Lines 226-234: load_stats
- SS3-37 GOOD: Missing-file None.
- SS3-38 BUG (line 233): bare except → None. Theme T1.

### Lines 239-269: empirical_sl_pct
- SS3-39 GOOD (lines 240-247): **8-line docstring with concrete example** for NVDA. Per SS3-25 same gold standard.
- SS3-40 GOOD (lines 248-250): Defensive `not stats or "returns" not in stats` chained check.
- SS3-41 GOOD (lines 253-260): Closest-percentile interpolation — finds nearest available bucket.
- SS3-42 GOOD (lines 266-268): "Only meaningful if downside" check — returns None if positive percentile (no SL achievable).

### Lines 272-298: empirical_tp_pct
- SS3-43 GOOD (lines 273-281): **9-line docstring with mathematical derivation** ("P(return >= X) = target → X = quantile(1 - target)"). **Per Batch 58 WP-X2 / Batch 62 PR-X2 fully-documented gold standard.** ✅
- SS3-44 GOOD (lines 282-284): Same defensive chained checks.
- SS3-45 GOOD (lines 287-291): Quantile inversion with closest-available percentile.
- SS3-46 GOOD (lines 295-297): Positive-only TP filter.

### Lines 303-321: __main__ (CLI)
- SS3-47 GOOD: Standard argv[1] ticker default to NVDA.
- SS3-48 GOOD (lines 307-310): Failure exit with operator-friendly error.
- SS3-49 GOOD (lines 311-321): Operator-readable output with concrete SL/TP from empirical helpers. **15th __main__ smoke test in audit.**

## CONSOLIDATED CROSS-CUTTING FINDINGS

### TG-X1 + B62 SS-X1 + B62 SS-X2 cross-cutting CONFIRMED 2-guardrail composite safety
**`assert_scoring_safety` (B62 SS-16) calls BOTH guardrails:**
1. `assert_legacy_sector_boosts_disabled` — caps semi/AI multipliers
2. `assert_theme_scoring_disabled` (this batch TG-X1) — blocks theme-aware scoring activation

**2-guardrail single-call composite assertion.** ✅ Per Batch 60 PSt-X2 single-file composite cross-cutting — same architectural pattern. **Safety-layer audit COMPLETE.**

### IN-X3 cross-cutting NEW: candlestick pattern DUPLICATION
**indicators.py contains candlestick_patterns** (6 patterns + aggregates) **OUTSIDE the patterns/ subdirectory architecture** (B59 PI-X1 16-detector registry). **Architectural inconsistency:**
- Formal patterns (HHHL, BullFlag, CupHandle, etc.) → `src/patterns/*` with PatternDetector base class
- Candlestick patterns (engulfing, hammer, doji, star) → `src/indicators.py` inline dict

**Should consolidate.** Either move candlesticks to patterns/ subdir OR document architectural decision (likely: candlesticks are bar-level, patterns are formation-level). Catalog as Theme T22 (architectural-layer drift).

### IN-X1 + B62 SC + B59 cross-cutting CONFIRMED scoring producer chain end-to-end
**Full SCORING PRODUCER chain:**
1. data_fetcher (B42) → OHLCV df
2. **indicators.add_indicators (this batch IN-X1) → 22-column decorated df + latest_signals 30+ key dict**
3. fundamentals (B55) → fund_score 0-1
4. scorer.composite_score (B62 SC-X1) → composite + 11 ind_* sub-scores
5. parallel_scorer (B44) → trade_type dispatch
6. day_trading_scorer (B56) / monster_hunt (B56) → swing/day/monster branches

**6-module SCORING producer chain. NOW FULLY AUDITED end-to-end.** ✅

### SS3-X1 + B62 PR-X1 cross-cutting CONFIRMED probability engine producer chain
**Full PROBABILITY ENGINE chain:**
1. yfinance (third-party) → 2y OHLCV
2. **stock_stats.compute_stock_stats (this batch SS3-X1) → 5-stat profile per ticker**
3. **stock_stats.empirical_sl_pct + empirical_tp_pct (this batch SS3-X2) → base rates**
4. probability_engine.compute_probabilistic_decision (B62 PR-X1) → 6-layer decision
5. (consumer): pick_evaluator / risk_manager (downstream)

**5-module PROBABILITY ENGINE chain. NOW FULLY AUDITED end-to-end.** ✅

### TG-9 + cross-cutting frozen dataclass FIRST INSTANCE
**5 audited dataclasses now:**
- weight_proposer Proposal (B58)
- calibration BucketStat (B59)
- probability_engine SignalState + ProbabilisticDecision (B62)
- **theme_scoring_guardrails ThemeScoringStatus (this batch TG-9) — FIRST FROZEN.**

**Catalog as Theme T22 BEST PRACTICE:** status records should be frozen.

### Cross-cutting: bare-except this batch
- theme_scoring_guardrails: 0 ✅
- indicators: 3 (IN-35 parabolic_sar defense, IN-45 candlestick defense, IN-47 fibonacci/SR defense)
- stock_stats: 2 (SS3-11 yfinance fetch, SS3-38 load_stats parse)

**5 bare-excepts in 3 files.** All graceful-degradation defensive. Below Phase E moderate density.

### Cross-cutting: TZ-aware modules: 11 (no addition; SS3-33 NAIVE).

### Cross-cutting: ATOMIC WRITE
- theme_scoring_guardrails: read-only.
- indicators: pure-compute.
- stock_stats: SS3-35 unsafe writer (32nd).

**1 new unsafe writer.** Tally: 5/32/37 = ~86% UNSAFE.

### Cross-cutting: relative-path constants — 0 new (SS3 STATS_DIR uses default arg pattern, not module const).

### Cross-cutting: bug-archaeology: 14 modules.

### Cross-cutting: __main__ smoke test: 15 modules (stock_stats SS3-49 adds).

### Cross-cutting: dataclass usage: 5 (theme_scoring_guardrails TG-9 first frozen).

### Cross-cutting: yfinance import-tolerance pattern (SS3-2 + B?) — 2-instance.

## SUMMARY (Batch 63)

| Severity | theme_scoring_guardrails | indicators | stock_stats | Cross-cutting | Total |
|---|---:|---:|---:|---:|---:|
| Show-stopper | 0 | 5 | 4 | 4 | 13 |
| Data/safety | 0 | 1 | 1 | 0 | 2 |
| Code smell | 0 | 1 | 0 | 0 | 1 |
| Good code | 17 | 38 | 41 | 0 | 96 |
| Total findings | 17 | 45 | 46 | 4 | 112 |

## TOP 10 CRITICAL FIXES from Batch 63

1. **IN-X3 / Theme T22 (HIGH):** Resolve candlestick-vs-formal-pattern architectural duplication. Either move candlestick_patterns to `src/patterns/candlestick.py` OR document the architectural decision in patterns/__init__.py docstring. (15 min decide / 30 min refactor)
2. **SS3-35 (MEDIUM):** Add atomic write to stock_stats.save_stats. (3 min — bundle with prior)
3. SS3-11: Replace stock_stats bare except with scoped (RuntimeError, ValueError, KeyError, ConnectionError) + MDH telemetry call. Per Batch 14 MDH-X1 cross-cutting. (10 min)
4. IN-35 + IN-45 + IN-47: Scope 3 indicators bare-excepts to specific exception types. (5 min)
5. IN-22 + IN-30: Lift candlestick magic 2×/0.1/0.3 + lookback/window magic to module constants with archaeology. (10 min)
6. IN-2: Expand indicators module docstring — list all 11+ indicators + composite + latest_signals. (5 min)
7. SS3-33: Convert SS3 timestamp to TZ-aware UTC for cross-region operator clarity. (3 min)
8. TG-9 / Theme T22 cross-cutting: Apply `@dataclass(frozen=True)` to other status records (e.g. AT scoring_safety_status returns plain dict — could be frozen dataclass). (5 min)
9. SS3-X2: Memoize empirical_sl_pct + empirical_tp_pct results to avoid repeated load_stats reads. (10 min)
10. IN-X3 + IN-24: Add docs/INDICATORS_VS_PATTERNS_ARCHITECTURE.md explaining bar-level (indicators.py) vs formation-level (patterns/) split. (15 min — only if architectural decision is "keep both").

## NEW THEMES UPDATED

- **Theme T1 (bare except):** **5 in 3 files** (3 indicators + 2 stock_stats). All graceful. Phase F starts moderate.
- **Theme T2 (schema drift):** TG-9 frozen vs SS unfrozen status records (mild).
- **Theme T6 (atomic writes):** SS3-35 adds 32nd unsafe writer. Tally: 5/32/37 = ~86% UNSAFE.
- **Theme T8 (DRY):** IN-24 candlestick patterns duplicate patterns/ architecture.
- **Theme T11 (fail-open by accident):** N/A this batch (all fall-back returns are intentional).
- **Theme T13 (silent-default-fills):** IN-39 22-key schema-stable scaffold (defensive). SS3-32 11-key profile dict (defensive).
- **Theme T14 (gold-standard patterns):** theme_scoring_guardrails TG-1 7-line docstring + TG-2 operator-binding contract + TG-X2 7-prerequisite formal gate + TG-9 first frozen dataclass + TG-15 sorted accumulated-violations error + TG-17 prose explanation lists all prerequisites. indicators IN-X1 22-column decorate + IN-X2 2-phase pipeline + IN-32 .copy() no-mutation + IN-38 NaN-safe _f helper + IN-39 22-key schema-stable scaffold + IN-42 5 operator-readable derived flags + IN-48 cdl_* namespace prefix. stock_stats SS3-1 17-line docstring + SS3-X1 5-stat per ticker + SS3-X2 2 empirical-decision helpers + SS3-2 yfinance import-tolerance + SS3-25 trader-friendly concrete example + SS3-43 mathematical derivation in docstring + SS3-49 operator-readable __main__ output.
- **NEW Theme T22 (architectural-layer drift):** indicators.candlestick_patterns vs patterns/* subdir DUPLICATION. Catalog as architectural inconsistency.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A | 8/8 COMPLETE | (none) | 8/8 |
| Phase B | 18/18 COMPLETE | (none) | 18/18 |
| Phase C | 12/12 COMPLETE | (none) | 12/12 |
| Phase D | 30/~30 COMPLETE | (none) | 30/~30 |
| Phase E | 50/50 COMPLETE | (none) | 50/50 |
| Phase F | 6/~38 done | theme_scoring_guardrails, indicators, stock_stats | 6/~38 |
| Total true line-by-line | | **+3 files** | **139 of ~382 (~36.4%)** |
| Remaining | | | **~243 files** |

**MILESTONE: SCORING-LAYER + PROBABILITY-ENGINE PRODUCER chains COMPLETE end-to-end. SAFETY guardrail layer COMPLETE. 36.4% audit progress.**

## NEXT BATCH

Batch 64 (doc #70): Continue Phase F. 3 NEW files from inventory:
- **`src/llm_agent.py` (~9KB)** — Claude/Gemini fallback for sentiment + classification (paired with B39 MN-X1 / B53 NS-X1).
- **`src/news_classifier.py` (~5KB)** — referenced by B62 PR-Layer 3 (news posteriors).
- **`src/pick_evaluator.py` (~19KB / 18964B)** — LARGEST single file in repo. Outcome attribution consumer of pick_logger (B11) — closes signal_journal/learning loop.

End of Batch 63. Phase F in progress (6/38). **36.4% audit milestone. Scoring + Probability producer chains COMPLETE.**
