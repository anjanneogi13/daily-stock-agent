# Batch 71 — 17-FILE BATCH — TRUE LINE-BY-LINE — SUBDIRECTORIES (Patterns/Backtester/Providers)

**Date:** 2026-05-12
**Files (17):** patterns/__init__ (42) + patterns/base (46) + patterns/breakouts (88) + patterns/cup_handle (97) + patterns/double (138) + patterns/flags (139) + patterns/head_shoulders (107) + patterns/hhhl (106) + patterns/triangles (133) + patterns/wedges (82) + backtester/__init__ (12) + backtester/engine (231) + backtester/metrics (84) + backtester/outcome_simulator (88) + backtester/pit_data (70) + market_data_providers/__init__ (5) + market_data_providers/stooq_provider (137)
**Phase:** H. **Total LOC audited this batch: ~1,705 lines (17 files — most files in single batch).**

## TOP HEADLINE FINDINGS

1. **PI-X1: patterns/__init__.py** (42 lines) is **THE 16-DETECTOR REGISTRY** for "Pillar 3 Pattern Recognition Engine ALL 15 DETECTORS LIVE (T49 — Phase 3 complete)." **NOTE: docstring says 15 but ALL_DETECTORS list contains 16 instances** (includes both directions for HHHL/breakouts/flags/triangles/double/head_shoulders/wedges + cup_handle alone). **Docstring drift bug.**
2. **PB-X1: patterns/base.py** (46 lines) is **THE PATTERN DETECTOR ABSTRACT BASE**. `@dataclass Match` with **5 fields (pattern/confidence/lookback/trigger/notes)** + `to_dict` + ABC PatternDetector with **3 class attrs (name/min_bars/direction) + abstractmethod `detect()` + `_enough_bars` helper.** **First audited ABC base class.** **11th audited dataclass.** Gold standard contract module.
3. **PBO-X1: patterns/breakouts.py** (88 lines) is **THE 20d DONCHIAN BREAKOUT/BREAKDOWN PAIR**. Bullish + bearish symmetric mirror + **identical confidence formula `min(0.95, 0.55 + 0.05 * gap_pct + 0.05 * (vol_ratio - 1))` clamped ≥0.5** + volume-confirmed notes ("with volume" if >1.2x else "low vol"). **Theme T32 sibling discipline (NEW B69) — 2nd audited mirror pair after ASL/ATP.**
4. **PCH-X1: patterns/cup_handle.py** (97 lines) is **THE WILLIAM O'NEIL CUP-HANDLE DETECTOR**. **7 named constants + 30-bar lookback + thirds split (left/middle/right_pre_handle/handle)** + 5 sequential reject gates (cup depth ∈ [10%, 35%] + rims within 3% + handle range ≤5% + handle pullback ∈ [0%, 8%]) + **conf formula combines all 3 quality metrics.** Bullish-only.
5. **PD-X1: patterns/double.py** (138 lines) is **THE DOUBLE TOP/BOTTOM PAIR + SHARED PIVOT HELPERS**. `_local_peaks` + `_local_troughs` shared helpers (k=3 window) + 30-bar lookback + 2% peak-tolerance + 5% trough-drop + **MIN_PEAK_SEPARATION=5 bars + last peak must be near end (i2 ≥ len-10) — "still active pattern" gate.** **Theme T32 sibling-mirror.**
6. **PF1-X1: patterns/flags.py** (139 lines) is **THE BULL/BEAR FLAG PAIR**. POLE 7 bars + FLAG 7 bars + **`MIN_POLE_PCT=8%` + `MAX_FLAG_PCT=5%` range** + 4-condition gate (pole-strong + flag-tight + flag-not-rallied + position-near-top/bottom) + position_top boost +0.05. Continuation-pattern detector. **Theme T32 sibling.**
7. **PHS-X1: patterns/head_shoulders.py** (107 lines) is **THE H&S + INVERSE-H&S PAIR using shared pivot helpers from double.py**. **for-loop over consecutive triples** + 4 gates per triple (separation + head-prominence + shoulder-tolerance + recency) + 35-bar lookback + 4% shoulder tolerance + 3% head-prominence min. **First audited cross-module helper import (`from .double import _local_peaks, _local_troughs`)** — NEW Theme T35.
8. **PHL-X1: patterns/hhhl.py** (106 lines) is **THE TREND-CONTINUATION PIVOT-PAIR DETECTOR**. HHHL bullish + LHLL bearish + **MAX_PIVOT k=2** + private `_pivot_highs`/`_pivot_lows` (NOT shared with double.py — Theme T8 duplication of similar logic). conf = `0.5 + 0.1 * n + 5 * (gap_h + gap_l)`. **Theme T8 NEW: duplicate pivot-finding logic in 3 modules** (double k=3 + hhhl k=2 + head_shoulders imports double).
9. **PT-X1: patterns/triangles.py** (133 lines) is **THE 3-TRIANGLE PAIR via LEAST-SQUARES TRENDLINE FIT**. Pure-stdlib `_linreg` + `_slope_pct_per_bar` + `_TriangleBase` parent class + 3 children (Ascending/Descending/Symmetric) with **2-threshold-based slope dispatch (FLAT_THRESHOLD=0.15, SLOPE_THRESHOLD=0.20)**. **2nd audited inheritance pattern + 4th audited Pure-stdlib Statistical** (joins SA Wilson + HE binomial + RKM Sharpe).
10. **PW-X1: patterns/wedges.py** (82 lines, smallest in patterns/) is **THE FALLING/RISING WEDGE PAIR**. **Imports `_linreg` + `_slope_pct_per_bar` from triangles.py** (Theme T35 cross-module helper) + `_WedgeBase` parent + **MIN_SLOPE=0.15 + MIN_CONVERGENCE=0.10** thresholds + same shape: both lines slope same direction but converge. Smallest patterns/ module + cleanest inheritance.
11. **BI-X1: backtester/__init__.py** (12 lines) is **THE BRAIN REPLAY ENGINE FACADE.** "v2 Brain Replay Engine — Phase A: price-only, no LLM, no news." **2-symbol public API** (`run_backtest`, `compute_metrics`).
12. **BE-X1: backtester/engine.py** (231 lines, **largest in batch**) is **THE BACKTEST ORCHESTRATION ENGINE v1.1.** 3 explicit v1.1 fixes in docstring: cooldown + gap-down fill + RSI overbought penalty. **`_simple_score` reimplements RSI/SMA/ATR/scoring inline** (Theme T8 duplication of indicators.py + scorer.py logic). **Hard-reject RSI ≥ 75** (was AAPL@82, TSM@72 archaeology). Per-day cooldown tracker `last_picked` dict. CSV+JSON+MD report generation per run.
13. **BM-X1: backtester/metrics.py** (84 lines) is **THE BACKTEST METRICS AGGREGATOR**. Sharpe + Sortino + MaxDD + Profit Factor + n<30 statistical_warning + sortino=inf-when-no-losses-and-positive + breakdown_by helper. **5th Pure-stdlib Statistical module.** Per RKM-X1 sibling — DUPLICATE Sharpe/Sortino/MaxDD logic of risk_metrics.py.
14. **BO-X1: backtester/outcome_simulator.py** (88 lines) is **THE V1.1 GAP-AWARE OUTCOME SIMULATOR**. **4-exit dispatch** (sl_gap / tp_gap / sl_hit / tp_hit / max_hold) + **gap-down at OPEN < SL → exit at OPEN (worse than SL)** + gap-up symmetric + conservative SL-FIRST when both hit same bar. **Realistic fill-modeling gold standard** for backtests.
15. **BP-X1: backtester/pit_data.py** (70 lines) is **THE POINT-IN-TIME ANTI-LEAK GUARD.** **5-line CRITICAL docstring** ("All historical data must be sliced so that on simulated day D, only data with timestamp < D is visible"). 2 functions (slice_pit + get_forward_window) + **`df.index < cutoff` strict-less-than (exclusive cutoff)** + min_history_days enforcement + datetime/string/date type-coerce. **First audited explicit anti-leak module** — gold standard.
16. **MDPI-X1: market_data_providers/__init__.py** (5 lines, **smallest in repo**) is **THE STUB FACADE.** "Initial scope: official daily OHLCV only." **No exports.**
17. **STQ-X1: market_data_providers/stooq_provider.py** (137 lines) is **THE STOOQ DAILY OHLCV FALLBACK**. **4-line scope statement** (no paper/live/stale/intraday) + **conservative symbol-mapping** (returns "" for ":" / "/" / "^" prefixes — "avoids pretending we have provider coverage we do not actually have" — operator-explicit) + **dual HTTP client fallback (curl_cffi → requests → RuntimeError)** + period-to-Stooq-date converter + lowercase OHLCV normalization. **First audited dedicated provider module + first cf_requests usage.**

## CRITICAL CROSS-FILE FINDINGS

- **NEW Theme T35 (CROSS-MODULE HELPER IMPORTS WITHIN SUBDIR):** Patterns subdir has 2 cross-module helper imports (PHS-X1 imports `_local_peaks/_local_troughs` from double; PW-X1 imports `_linreg/_slope_pct_per_bar` from triangles). **Acceptable but creates implicit hierarchy** — should consolidate into `patterns/_helpers.py` or `patterns/base.py`.
- **NEW Theme T36 (SHARED-LIBRARY DUPLICATION ACROSS DIRECTORIES):** **3 places now duplicate Sharpe/Sortino/MaxDD logic**:
  - B70 RKM-X1 risk_metrics.py (production)
  - B71 BM-X1 backtester/metrics.py (backtest)
  - **2 distinct implementations + 2 distinct annualization conventions** (RKM uses sqrt(50) "trades/year"; BM uses sqrt(250) "trading days") = **drift risk in math.**
- **THEME T32 SIBLING-MODULE EXPLOSION (was 1 pair B69, now 9 pairs):**
  - B69 ASL ↔ ATP (adaptive SL/TP)
  - **B71: 8 new pattern sibling pairs in single batch:**
    - HHHL ↔ LHLL
    - BreakoutDetector ↔ BreakdownDetector
    - BullFlag ↔ BearFlag
    - DoubleTop ↔ DoubleBottom
    - HeadShoulders ↔ InverseHeadShoulders
    - FallingWedge ↔ RisingWedge
    - AscendingTriangle ↔ DescendingTriangle (with Symmetric as third)
  
  **9 sibling pairs total. Sibling-module discipline is HEAVILY-USED PATTERN — formalize as standard.**
- **NEW Theme T37 (BACKTESTER vs LIVE-SCORER DRIFT):** BE-X1 `_simple_score` is **inline reimplementation of RSI/SMA/ATR + thresholds**. Live system uses `src/indicators.py` + `src/scorer.py`. **Backtest may not faithfully replay live decisions** — the v1.1 RSI≥75 hard-reject + parabolic penalty added INDEPENDENTLY without confirmation that live system also has these. **CRITICAL: backtester must call same scoring code as live OR explicitly document divergence.**
- **PURE-STDLIB STATISTICAL MODULES NOW 5** (Theme T29): SA + HE + RKM + BM + PT triangles. Pattern is consistent: deliberate avoidance of scipy/numpy in core math. **Note BE-X1 uses numpy** — only inside backtester engine, not in stats modules.
- **PROVIDER FALLBACK PATTERN (NEW):** STQ-X1 introduces **dual-HTTP-client fallback (curl_cffi → requests)** with optional-import try/except. **Per Theme T31 yfinance brittleness defense — operator-pragmatic alternative source.** Operator-explicit "conservative symbol mapping" rejecting `:` / `/` / `^` prefixes.

## src/patterns/__init__.py — LINE BY LINE

- PI-1 GOOD (1-4): 4-line docstring with **Pillar 3 reference + T49 Phase 3 complete archaeology.**
- PI-2 BUG (3): "ALL 15 DETECTORS LIVE" but ALL_DETECTORS list contains **16 instances**. Docstring drift. **Theme T2 17th instance.**
- PI-3 GOOD (5-17): 9 import statements with **directional grouping** (HHHL/Breakout/Flag/Triangle/Cup/Double/H&S/Wedge).
- PI-4 GOOD (19-29): ALL_DETECTORS as **module-level instantiated list** — pre-instantiated for hot-path performance. Operator-readable.
- PI-5 GOOD (31-41): __all__ explicit export list.

## src/patterns/base.py — LINE BY LINE

- PB-1 GOOD (1-11): 11-line docstring with **detect() contract + OHLCV shape + Match purpose statement.**
- PB-2 GOOD (18-27): @dataclass Match with **5 fields + to_dict method + field(default_factory=dict)** for trigger.
- PB-3 GOOD (20-23): Per-field comment annotations — operator-readable.
- PB-4 GOOD (30-45): PatternDetector ABC with **3 class attrs (name/min_bars/direction) + abstractmethod detect() + _enough_bars helper.**
- PB-5 GOOD (33-35): 3 class-level defaults — child detectors override.
- PB-6 GOOD (41-45): _enough_bars with **try/except → False** defensive.
- PB-7 BUG (44): bare Exception. Theme T1.

## src/patterns/breakouts.py — LINE BY LINE

- PBO-1 GOOD (1-10): 10-line docstring with **breakout vs breakdown definition + confidence-formula explanation.**
- PBO-2 GOOD (17-21): BreakoutDetector with `min_bars=21` (20 + today) + bullish.
- PBO-3 GOOD (22-51): detect with **6 sequential operations.**
- PBO-4 GOOD (28-29): max+last-bar separation via `prior = sub.iloc[:-1]` + `today = sub.iloc[-1]`. Anti-leak.
- PBO-5 GOOD (30-31): Strict `<= band_high` reject.
- PBO-6 GOOD (32): gap_pct = `(close - band_high) / band_high * 100`.
- PBO-7 GOOD (33-36): **Volume confirmation** with avg-vs-today ratio + `if "Volume" in prior` defensive (column may be missing).
- PBO-8 GOOD (37-38): conf formula `min(0.95, 0.55 + 0.05*gap + 0.05*(vol-1))` clamped ≥0.5 — bounded magnitude.
- PBO-9 GOOD (39-51): Match return with **4-key trigger + dual-mode notes** ("with volume" if vol>1.2 else "low vol").
- PBO-10 GOOD (54-87): BreakdownDetector mirror with `min_bars=21` + bearish + same formula symmetric. **Theme T32 sibling.**

## src/patterns/cup_handle.py — LINE BY LINE

- PCH-1 GOOD (1-14): 14-line docstring with **structure overview + heuristic implementation steps + golden-fixture-testable mention.** ✅
- PCH-2 GOOD (25-31): 7 named constants — operator-readable + tunable.
- PCH-3 GOOD (33-96): detect with **5 sequential reject gates + complex conf formula.**
- PCH-4 GOOD (38-46): 4-zone partition (left/middle/right_pre_handle/handle) — clear topology.
- PCH-5 GOOD (47-48): Insufficient right_pre_handle → None defensive.
- PCH-6 GOOD (50-52): 3 reference levels computed.
- PCH-7 GOOD (54-59): Cup-depth gate `[10%, 35%]` with avg-rim base.
- PCH-8 GOOD (56): Div-by-zero guard `if avg_rim == 0`.
- PCH-9 GOOD (61-64): Rims-equal gate (3% tolerance).
- PCH-10 GOOD (66-74): Handle 2-gate (range ≤5% + pullback ∈ [0%, 8%]).
- PCH-11 GOOD (69): Div-by-zero guard `if handle_low`.
- PCH-12 GOOD (76-81): conf combines all 3 quality metrics with weighted formula clamped to [0.5, 0.95].
- PCH-13 GOOD (82-96): 7-key trigger return — operator-debuggable.

## src/patterns/double.py — LINE BY LINE

- PD-1 GOOD (1-9): 9-line docstring with **bearish + mirror discipline statement.**
- PD-2 GOOD (15-21): **`_local_peaks` shared helper** with k=3 window + **strict-uniqueness** (`window.count(values[i]) == 1`) — anti-plateau guard. ✅ Operator-correct.
- PD-3 GOOD (24-30): _local_troughs mirror.
- PD-4 GOOD (33-85): DoubleTopDetector with **4 named constants + 5-stage gate.**
- PD-5 GOOD (43-72): detect with **5 sequential rejects.**
- PD-6 GOOD (49-51): Insufficient peaks → None.
- PD-7 GOOD (52-56): **Take 2 highest peaks then sort chronologically** — operator-correct (avoids order bias).
- PD-8 GOOD (57-58): MIN_PEAK_SEPARATION = 5 — anti-noise.
- PD-9 GOOD (60-61): 2% peak-tolerance gate.
- PD-10 GOOD (62-69): **Trough-between gate** with 5% drop minimum + empty-list defensive.
- PD-11 GOOD (70-72): **"Last peak should be near the end (still active pattern)"** — `i2 < len-10 → reject`. **Recency gate gold standard** for live trading. ✅
- PD-12 GOOD (73): conf formula.
- PD-13 GOOD (74-85): 4-key trigger return + operator-readable notes.
- PD-14 GOOD (88-137): DoubleBottomDetector mirror. **Theme T32 sibling.**

## src/patterns/flags.py — LINE BY LINE

- PF1-1 GOOD (1-12): 12-line docstring with **continuation-pattern philosophy + confidence-scaling explanation.**
- PF1-2 GOOD (18-20): _pct_change with **div-by-zero guard.**
- PF1-3 GOOD (23-32): BullFlagDetector with **4 named constants** (POLE_BARS=7, FLAG_BARS=7, MIN_POLE_PCT=8%, MAX_FLAG_PCT=5%).
- PF1-4 GOOD (33-80): detect with **6-step pipeline.**
- PF1-5 GOOD (36-38): 14-bar window split into pole + flag.
- PF1-6 GOOD (40-44): pole strength gate.
- PF1-7 GOOD (46-50): flag-tight gate.
- PF1-8 GOOD (52-57): **flag-not-rallied gate** — "flag rallied — not a flag, it's a continuation already" comment-archaeology.
- PF1-9 GOOD (59-62): Position-in-flag-half computation.
- PF1-10 GOOD (64-67): conf formula with **near-top boost +0.05** ✅.
- PF1-11 GOOD (69-80): 4-key trigger.
- PF1-12 GOOD (83-138): BearFlagDetector mirror with **bear-asymmetry comment** ("Bear flag: small upward drift in flag is OK and expected"). **Theme T32 sibling.**

## src/patterns/head_shoulders.py — LINE BY LINE

- PHS-1 GOOD (1-7): 7-line docstring.
- PHS-2 GOOD (11): **Cross-module import `from .double import _local_peaks, _local_troughs`.** **NEW Theme T35.**
- PHS-3 GOOD (14-22): HeadShouldersDetector with **4 named constants** (LOOKBACK=35, SHOULDER_TOL=4%, HEAD_PROMINENCE=3%, MIN_SEPARATION=4).
- PHS-4 GOOD (24-61): detect with **for-loop over consecutive triples** — robust to noise.
- PHS-5 GOOD (29-31): Insufficient peaks → None.
- PHS-6 GOOD (34-47): Per-triple 5 sequential reject gates.
- PHS-7 GOOD (35): Tuple-unpacking pattern `(il, l), (ih, h), (ir, r)` — pythonic.
- PHS-8 GOOD (36-37): Two separation gates.
- PHS-9 GOOD (39): "Head must be highest" — strict greater-than (no ties).
- PHS-10 GOOD (41-42): Shoulder-tolerance gate (4%).
- PHS-11 GOOD (44-45): Head-prominence gate (3%).
- PHS-12 GOOD (47): "Right shoulder must be near end" — recency gate (8 bars from end).
- PHS-13 GOOD (48-60): conf formula + 4-key trigger return.
- PHS-14 GOOD (61): Loop returns None if no triple matches.
- PHS-15 GOOD (64-106): InverseHeadShouldersDetector mirror with **strict less-than for head-lowest.** **Theme T32 sibling.**

## src/patterns/hhhl.py — LINE BY LINE

- PHL-1 GOOD (1-11): 11-line docstring.
- PHL-2 BUG (18-33): **DUPLICATE of double._local_peaks/_local_troughs but with k=2** instead of k=3. **Theme T8 sibling-pivot duplication** — should consolidate into `patterns/_helpers.py`. **3rd pivot-finder implementation in 3 modules.**
- PHL-3 GOOD (36-71): HHHLDetector with **simple 3-gate detect.**
- PHL-4 GOOD (48-49): Insufficient pivots → None.
- PHL-5 GOOD (51-55): Strict-increasing checks for last 2 pivot-highs + lows.
- PHL-6 GOOD (57-60): conf with **n_pivots scaling + gap% scaling + max(.., 1e-9) div-by-zero guard.**
- PHL-7 GOOD (61-71): 5-key trigger + operator-readable notes.
- PHL-8 GOOD (74-105): LHLLDetector strict mirror. **Theme T32 sibling.**

## src/patterns/triangles.py — LINE BY LINE

- PT-1 GOOD (1-13): 13-line docstring with **3-classification table + confidence-scaling explanation.**
- PT-2 GOOD (19-31): **`_linreg` PURE-STDLIB least-squares** — 11-line implementation with **edge cases (n<2, den==0).** ✅ **5th Pure-stdlib statistical** (Theme T29).
- PT-3 GOOD (34-37): _slope_pct_per_bar with div-by-zero guard.
- PT-4 GOOD (40-58): **`_TriangleBase` parent class** with shared `_fit` method + 2 named slope thresholds. **2nd audited inheritance.**
- PT-5 GOOD (44): FLAT_THRESHOLD=0.15 / SLOPE_THRESHOLD=0.20 — 2-tier dispatch primitives.
- PT-6 GOOD (61-82): AscendingTriangleDetector with **flat-resistance + rising-support gate.**
- PT-7 GOOD (85-106): DescendingTriangleDetector mirror with **flat-support + falling-resistance.**
- PT-8 GOOD (109-132): SymmetricTriangleDetector with **converging gate + roughly-symmetric (slope-magnitude diff ≤ 0.30).**
- PT-9 GOOD (122): conf cap **0.90 (not 0.95)** for symmetric — direction-uncertain pattern. Operator-correct lower confidence.
- PT-10 GOOD (78-79, 102-103, 128-129): All 3 use same 2-key trigger schema (resistance + support slopes).

## src/patterns/wedges.py — LINE BY LINE

- PW-1 GOOD (1-8): 8-line docstring with **same-direction-but-converging philosophy.**
- PW-2 GOOD (12): **Cross-module import from triangles** — Theme T35.
- PW-3 GOOD (15-29): _WedgeBase parent with shared _fit + 2 named constants (MIN_SLOPE=0.15, MIN_CONVERGENCE=0.10).
- PW-4 GOOD (32-55): FallingWedgeDetector with **3-gate AND** (both lines ≤ -MIN_SLOPE + sl > sh + convergence ≥ MIN_CONVERGENCE).
- PW-5 GOOD (43): "lows must fall LESS than highs (sl > sh, both negative)" — operator-readable comment.
- PW-6 GOOD (45): conf cap 0.90.
- PW-7 GOOD (58-81): RisingWedgeDetector mirror. **Theme T32 sibling.**

## src/backtester/__init__.py — LINE BY LINE

- BI-1 GOOD (1-7): 7-line docstring with **v2 + Brain Replay Engine + strict point-in-time discipline + Phase A scope.**
- BI-2 GOOD (8-9): 2-import facade.
- BI-3 GOOD (11): __all__ explicit.

## src/backtester/engine.py — LINE BY LINE (largest in batch — 231 lines)

- BE-1 GOOD (1-7): 7-line docstring with **3 explicit v1.1 fixes archaeology.**
- BE-2 GOOD (8-18): 8-import statement.
- BE-3 GOOD (21-95): **`_simple_score` v1.1 inline RSI/SMA/ATR/scoring.**
- BE-4 BUG (21): **DUPLICATE of indicators.py + scorer.py logic.** Theme T8. **NEW Theme T37 (backtester-vs-live-scorer drift).**
- BE-5 GOOD (23-24): n<60 None defensive.
- BE-6 GOOD (32-39): RSI(14) computation with `np.where` + `avg_loss > 0` div-by-zero guard.
- BE-7 GOOD (41-43): **HARD REJECT RSI≥75** with archaeology comment ("AAPL@82, TSM@72 problem"). ✅
- BE-8 GOOD (45-46): SMA20 + SMA50 with len-defensive fallback.
- BE-9 GOOD (48-51): ATR(15) computation using **True Range with np.roll for prev_close**.
- BE-10 GOOD (53-78): **5-tier RSI dispatch + 3-tier MA stack + 4-tier momentum** — operator-readable.
- BE-11 GOOD (61): RSI 65-74 = -0.10 penalty (v1.1).
- BE-12 GOOD (74): pct_5d ≥ 8% = -0.10 parabolic penalty (v1.1).
- BE-13 GOOD (78): score clamped [0, 1].
- BE-14 GOOD (80-81): Min-score gate (0.55).
- BE-15 GOOD (83-95): Plan with **entry + 1.5×ATR SL + 3×ATR TP + 7-key return.**
- BE-16 GOOD (98-107): run_backtest signature with **8 named kwargs + cooldown_days=5 v1.1.**
- BE-17 GOOD (109-115): run_id generation + per-run output dir + 3-line config print.
- BE-18 BUG (109): Naive datetime.now() — should be TZ-aware. **6th naive-datetime instance.**
- BE-19 GOOD (117-127): Reference-ticker resolution with SPY-preferred + 2 datetime-coerce.
- BE-20 GOOD (131-132): all_picks list + last_picked dict cooldown tracker.
- BE-21 GOOD (134-175): **Per-day simulation loop with cooldown check + scoring + top-N + outcome simulation.**
- BE-22 GOOD (139-143): Cooldown skip with operator-readable comment.
- BE-23 GOOD (148-150): slice_pit anti-leak guard.
- BE-24 GOOD (152-155): Plan stamping (ticker + pick_date).
- BE-25 GOOD (157-158): Score-sort + top_n_per_day cap.
- BE-26 GOOD (160-172): Per-pick simulate_outcome + last_picked update.
- BE-27 GOOD (174-175): Progress print every 50 days.
- BE-28 GOOD (177-183): CSV write **with `newline=""`.** ✅ Per Theme T11 — **first CSV writer audited that follows newline convention.**
- BE-29 GOOD (185-203): Metrics + breakdown + summary 5-key.
- BE-30 BUG (180, 206, 209): 3 file writes — **NO ATOMIC.** **52nd, 53rd, 54th unsafe writers.**
- BE-31 GOOD (209-222): Markdown report generation with **operator-readable structure** (headline + per-status breakdown).
- BE-32 GOOD (224-228): 4-line operator-readable summary print.

## src/backtester/metrics.py — LINE BY LINE

- BM-1 GOOD (1): 1-line docstring.
- BM-2 BUG (1): Module docstring undersells — has 2 functions + 11-key result.
- BM-3 GOOD (8-75): compute_metrics with **9-stage computation.**
- BM-4 GOOD (13-14): Empty input → 2-key skeleton.
- BM-5 GOOD (16-17): Filtered-list construction with None defensive.
- BM-6 GOOD (28-34): **Sharpe annualized with sqrt(250)** + n>1 guard + std==0 guard.
- BM-7 GOOD (36-42): **Sortino with `float("inf")` when no losses + positive avg_r.** Operator-correct semantically.
- BM-8 GOOD (45-50): Max DD with peak tracking + cumulative R.
- BM-9 GOOD (53-55): Profit factor with **inf when zero gross loss.**
- BM-10 GOOD (57-60): Exit status defaultdict counter.
- BM-11 GOOD (62-75): **11-key schema-stable result + statistical_warning n<30 + sortino/profit_factor "inf" string when float("inf").**
- BM-12 GOOD (78-83): breakdown_by helper with per-group recursion.
- BM-13 BUG: **DUPLICATE of risk_metrics.py logic.** Theme T36 NEW.

## src/backtester/outcome_simulator.py — LINE BY LINE

- BO-1 GOOD (1): 1-line docstring with v1.1 mention.
- BO-2 GOOD (7-87): simulate_outcome with **5-exit dispatch.**
- BO-3 GOOD (16-25): 2 defensive returns (no_data + invalid_sl) with **6-key schema-stable.**
- BO-4 GOOD (21): risk = abs(entry - stop_loss) — **abs() supports both long and short** (though side defaults to long).
- BO-5 GOOD (27): bars cap at max_hold_days.
- BO-6 GOOD (29-77): **Per-bar walk with 4-exit checks** (sl_gap / tp_gap / sl_hit / tp_hit).
- BO-7 GOOD (35-45): **Long-side gap-down at OPEN ≤ SL → exit at OPEN** with archaeology comment "worse than stop". ✅ Realistic fill.
- BO-8 GOOD (47-56): **Long-side gap-up at OPEN ≥ TP → exit at OPEN** ("better than TP"). Symmetric.
- BO-9 GOOD (58-77): **Conservative SL-FIRST when both hit** (intra-bar — can't tell which actually hit first). ✅ Conservative-bias gold standard.
- BO-10 GOOD (79-87): max_hold default exit with last_close + days_held + r_multiple.
- BO-11 GOOD: **6-key schema-stable across all 5 exit paths.** Theme T13 gold standard.
- BO-12 BUG: side default "long" but code only handles long branch (no short branch). **Drift risk** — function signature suggests short support but it's not implemented. Document as long-only.

## src/backtester/pit_data.py — LINE BY LINE

- BP-1 GOOD (1-5): **5-line CRITICAL docstring** with anti-leak mandate. ✅ Operator-trust gold standard.
- BP-2 GOOD (12-43): slice_pit with **3 type-coerce paths + cutoff < strict-less-than.**
- BP-3 GOOD (24-25): df None/empty → None defensive.
- BP-4 GOOD (27-30): Datetime/string/date coercion to date type.
- BP-5 GOOD (33-35): DatetimeIndex coercion with copy-then-mutate.
- BP-6 GOOD (37-38): **`df.index < cutoff` strict less-than (exclusive)** — anti-leak invariant. ✅
- BP-7 GOOD (40-41): min_history_days enforcement.
- BP-8 GOOD (46-69): get_forward_window with **`>= cutoff` inclusive + n_days head.**
- BP-9 GOOD (50-51): "ONLY place where future data is used" docstring honesty.
- BP-10 GOOD (66-67): Empty forward → None.

## src/market_data_providers/__init__.py — LINE BY LINE (smallest in repo — 5 lines)

- MDPI-1 GOOD (1-4): 4-line docstring with scope statement.

## src/market_data_providers/stooq_provider.py — LINE BY LINE

- STQ-1 GOOD (1-11): 11-line docstring with **4-line scope statement (no paper/live/stale/intraday) + Stooq daily CSV format.**
- STQ-2 GOOD (20-23): **Optional cf_requests import with `# pragma: no cover` annotation.** ✅ **First audited optional-dep import pattern.**
- STQ-3 GOOD (25-28): Optional requests import same pattern.
- STQ-4 GOOD (31-33): 3 named constants + **regex `^[a-z0-9.-]+$` for symbol whitelist.**
- STQ-5 GOOD (36-53): stooq_symbol with **conservative-symbol-mapping operator philosophy** in docstring.
- STQ-6 GOOD (44-50): 5-stage validation (empty / colon / slash / caret / regex).
- STQ-7 GOOD (47): "TSX:AQN not safely mappable... Returning empty symbol prevents noisy parser errors and avoids pretending we have provider coverage that we do not actually have." **Operator-trust gold standard.** ✅
- STQ-8 GOOD (51-53): Dot-suffix passthrough + .us auto-suffix for US tickers.
- STQ-9 GOOD (56-80): _start_date_for_period with **4-suffix dispatch** (d/mo/y/max-ytd) + **+10-day buffer** (+10 days) for safe coverage.
- STQ-10 GOOD (83-94): _http_get with **dual-client cascade** (cf_requests preferred → requests fallback → RuntimeError).
- STQ-11 GOOD (85): cf_requests `impersonate="chrome"` — anti-bot defensive.
- STQ-12 GOOD (97-136): fetch_stooq_ohlcv with **5-stage pipeline.**
- STQ-13 GOOD (99-100): Non-daily interval → empty df.
- STQ-14 GOOD (102-104): No-symbol → empty df.
- STQ-15 GOOD (116-117): "No data" sentinel detection.
- STQ-16 GOOD (123): Lowercase normalization.
- STQ-17 GOOD (124-126): Required-columns subset check → empty df defensive.
- STQ-18 GOOD (128-134): **errors="coerce" + dropna pipeline** — robust to malformed Stooq CSV.
- STQ-19 GOOD (134): volume-fillna(0) — operator-correct (volume can be missing, not NaN-rejected).
- STQ-20 GOOD (136): 5-column return ensures schema-stability across providers.

## CONSOLIDATED CROSS-CUTTING (THIS BATCH)

### NEW Theme T35 (CROSS-MODULE HELPER IMPORTS WITHIN SUBDIR)
- PHS-2: `from .double import _local_peaks, _local_troughs`
- PW-2: `from .triangles import _linreg, _slope_pct_per_bar`

**Pattern:** Subdirectory modules import private helpers from siblings. **Acceptable but creates implicit hierarchy.** Recommend consolidating shared helpers into `patterns/_helpers.py` or moving to `patterns/base.py`.

### NEW Theme T36 (SHARED-LIBRARY DUPLICATION ACROSS DIRECTORIES)
- B70 RKM-X1 + B71 BM-X1 = 2 distinct Sharpe/Sortino/MaxDD implementations
- 2 distinct annualization conventions (sqrt(50) vs sqrt(250)) → drift risk
- Sortino "inf when no losses" handled differently across the 2 impls

**Recommend:** Create `src/_stats.py` with single shared Sharpe/Sortino/MaxDD/Calmar/ProfitFactor. Both modules import.

### NEW Theme T37 (BACKTESTER-vs-LIVE DRIFT)
- BE-X1 `_simple_score` is **inline rewrite of indicators+scorer logic** — divergent from production.
- v1.1 added RSI≥75 + parabolic penalty INDEPENDENTLY without confirmation that live system has same.
- **CRITICAL:** Backtester result accuracy depends on faithfulness to live decision flow. **Currently they can drift silently.**

**Recommend:** Backtester must call same `score_pick()` function as live OR explicitly document divergence in `docs/BACKTESTER_DIVERGENCE.md`.

### Theme T32 (SIBLING-MODULE DISCIPLINE) MASSIVE EXPANSION
**Was 1 pair (B69) → now 9 pairs (8 added in single batch):**
| Pair | Module |
|---|---|
| ASL ↔ ATP | adaptive_sl ↔ adaptive_tp |
| HHHL ↔ LHLL | hhhl |
| Breakout ↔ Breakdown | breakouts |
| BullFlag ↔ BearFlag | flags |
| DoubleTop ↔ DoubleBottom | double |
| HeadShoulders ↔ Inverse | head_shoulders |
| FallingWedge ↔ RisingWedge | wedges |
| Asc/Desc/Sym Triangle | triangles (3-way variation) |

**Sibling discipline is now CORE PATTERN.** Formalize as standard in `docs/SIBLING_MODULE_PATTERN.md`.

### Theme T8 (DRY) UPDATE
- _safe_float / _to_float: still 30 modules (no new duplicates this batch).
- **Pivot-finder duplicates: 3 implementations** (double k=3 + hhhl k=2 + head_shoulders imports double).
- **RSI/SMA/ATR/scoring duplicates:** indicators + scorer + backtester engine = 3 implementations (BE-4 archive note).
- **Sharpe/Sortino duplicates:** RKM + BM = 2 implementations.

### Theme T6 (ATOMIC WRITES) UPDATE
| Module | Status |
|---|---|
| BE-30 picks.csv | ❌ unsafe (52nd) |
| BE-30 metrics.json | ❌ unsafe (53rd) |
| BE-30 report.md | ❌ unsafe (54th) |

**Tally: 9 safe / 54 unsafe / 63 = ~86% UNSAFE.**

### Theme T11 (CSV newline="") FIRST POSITIVE INSTANCE
- BE-28: `with open(csv_path, "w", newline="") as f:` ✅ **First CSV writer audited that follows the newline convention.** All prior CSV writes lack `newline=""` (which can cause Windows double-newlines).

### Theme T13 (SCHEMA-STABLE) UPDATE — heavy this batch too
- All 14 pattern detectors return **schema-stable Match dataclass.** ✅
- BO-X1 6-key schema-stable across 5 exit paths.
- BM-X1 11-key schema-stable across all returns.
- STQ-X1 5-column schema-stable across all paths (empty df is schema-compatible).

### Theme T14 (gold standard) UPDATE — heaviest single batch
- PB-X1 ABC contract + dataclass Match + abstract method + class-attr defaults
- PBO-X1 sibling-mirror discipline + bounded conf magnitude + volume-confirmed notes
- PCH-X1 14-line docstring + golden-fixture-testable + named constants + 5-stage rejects
- PD-X1 strict-uniqueness pivot + chronological re-sort + recency gate ("still active pattern")
- PF1-X1 12-line docstring + flag-not-rallied gate + position-near-top boost
- PHS-X1 for-loop over consecutive triples (robust) + tuple-unpack pattern + recency gate
- PT-X1 _TriangleBase inheritance + Pure-stdlib _linreg + 0.90 conf cap for symmetric (direction-uncertain)
- PW-X1 _WedgeBase inheritance + cross-module helper import (Theme T35)
- BE-X1 hard-reject RSI≥75 archaeology + parabolic penalty + cooldown tracker + slice_pit anti-leak + CSV newline=""
- BO-X1 v1.1 gap-aware fills + conservative SL-FIRST when both hit + 6-key schema-stable across 5 exits
- BP-X1 5-line CRITICAL anti-leak docstring + strict-less-than cutoff + "ONLY place where future data is used" honesty
- STQ-X1 conservative-symbol-mapping + dual-HTTP-client cascade + cf_requests impersonate="chrome" + errors="coerce" pipeline + "avoids pretending we have provider coverage we do not actually have"

### Cross-cutting tally summary (this batch only)
| Metric | Before | This batch | After |
|---|---:|---:|---:|
| _safe_float duplicates | 30 | 0 | **30** |
| Pivot-finder duplicates | 0 | 3 | **3** |
| RSI/SMA/ATR scoring duplicates | 1 | 1 | **2 places** (live + backtester) |
| Sharpe/Sortino duplicates | 1 | 1 | **2 places** (RKM + BM) |
| Bare-except | mod | 1 | continues moderate |
| Inline imports | ~40 | 0 | ~40 |
| Import-time side effects | 19 | 0 | 19 |
| Unsafe writers | 51 | 3 | **54 / 63 = 86% UNSAFE** |
| Atomic writers | 9 | 0 | 9 |
| TZ-aware modules | 21 | 1 (STQ) | **22** |
| Naive datetime usage | catalog | 1 (BE-18) | **catalog ongoing** |
| DATED archaeology | 43 | 5 (T49 Phase 3 + v1.1 fixes ×3 + AAPL@82 archaeology) | **48** |
| Frozen dataclasses | 4 | 0 | 4 |
| Regular dataclasses | 10 | 1 (Match) | **11** |
| ABC base classes | 0 | 1 (PatternDetector) | **1** |
| Inheritance patterns | 1 | 2 (_TriangleBase + _WedgeBase) | **3** |
| OBSERVE-MODE modules | 26 | 0 | 26 |
| __main__ smoke tests | 29 | 0 | 29 |
| Pure-stdlib statistical | 3 | 2 (PT triangles + BM) | **5** |
| **NEW Theme T35 cross-module helpers** | new | 2 instances | **2** |
| **NEW Theme T36 shared-lib duplication** | new | 1 (Sharpe×2) | **1** |
| **NEW Theme T37 backtester-live drift** | new | 1 critical | **1** |
| Theme T32 sibling pairs | 1 | 8 new | **9** |
| Sibling-module pairs total | 1 | 8 | **9** |
| Provider modules | 0 | 1 (Stooq) | **1** |
| CSV writers with newline="" | 0 | 1 (BE-28) | **1 of unknown total** |
| Optional-dep import patterns | 0 | 1 (STQ) | **1** |

## SUMMARY (Batch 71 — 17-FILE)

| File | Show-stop | Data/safety | Code smell | Good code | Findings |
|---|---:|---:|---:|---:|---:|
| patterns/__init__ | 1 | 0 | 0 | 4 | 5 |
| patterns/base | 1 | 0 | 0 | 6 | 7 |
| patterns/breakouts | 0 | 0 | 0 | 10 | 10 |
| patterns/cup_handle | 0 | 0 | 0 | 13 | 13 |
| patterns/double | 0 | 0 | 0 | 14 | 14 |
| patterns/flags | 0 | 0 | 0 | 12 | 12 |
| patterns/head_shoulders | 0 | 0 | 0 | 15 | 15 |
| patterns/hhhl | 1 | 0 | 0 | 7 | 8 |
| patterns/triangles | 0 | 0 | 0 | 10 | 10 |
| patterns/wedges | 0 | 0 | 0 | 7 | 7 |
| backtester/__init__ | 0 | 0 | 0 | 3 | 3 |
| backtester/engine | 5 | 0 | 0 | 27 | 32 |
| backtester/metrics | 2 | 0 | 0 | 11 | 13 |
| backtester/outcome_simulator | 1 | 0 | 0 | 11 | 12 |
| backtester/pit_data | 0 | 0 | 0 | 10 | 10 |
| market_data_providers/__init__ | 0 | 0 | 0 | 1 | 1 |
| market_data_providers/stooq_provider | 0 | 0 | 0 | 20 | 20 |
| **TOTAL** | **11** | **0** | **0** | **181** | **192** |

## TOP 15 CRITICAL FIXES from Batch 71

1. **NEW Theme T37 (CRITICAL — backtester-live drift):** BE-X1 `_simple_score` reimplements indicators + scorer logic. **Replace with direct call to live `score_pick()`** OR **document divergence in `docs/BACKTESTER_DIVERGENCE.md` and add unit tests asserting parity.** **HIGHEST-IMPACT finding this batch** — a backtest that doesn't faithfully replay live decisions can give false confidence. (3 hours)
2. **NEW Theme T36 (HIGH-IMPACT consolidation):** Create `src/_stats.py` with single Sharpe/Sortino/MaxDD/Calmar/ProfitFactor. Migrate RKM-X1 + BM-X1 to import. (1 hour)
3. **NEW Theme T35 (helper consolidation):** Create `src/patterns/_helpers.py` with `_local_peaks`, `_local_troughs`, `_pivot_highs`, `_pivot_lows`, `_linreg`, `_slope_pct_per_bar`. Migrate hhhl + head_shoulders + double + triangles + wedges. (45 min)
4. **PI-2 (docstring drift):** "ALL 15 DETECTORS" → "ALL 16 DETECTORS" (or recount). 17th Theme T2 instance. (1 min)
5. **BE-30 3 unsafe writers:** picks.csv + metrics.json + report.md atomic-rename. **Tally now 86% unsafe** — DS-X1 atomic pattern propagation continues. (15 min)
6. **BE-28 CSV newline="" FIRST POSITIVE:** Audit all other CSV writers across audit (~10+ writers without newline=""). **Bulk add newline="" parameter.** (30 min)
7. **HHHL pivot-finder duplication (Theme T8 NEW):** **3 pivot-finder implementations** (double + hhhl + head_shoulders imports double). Consolidate into _helpers.py per fix #3. (30 min)
8. **BE-18 naive-datetime:** run_id should use TZ-aware UTC. **6th naive-datetime instance.** (1 min)
9. **BO-12 side="long" but only long handled:** Either document long-only OR implement short branch OR remove side parameter. (30 min)
10. **STQ-X1 + DS-X1 promotion:** STQ optional-dep import pattern + dual-HTTP cascade is gold-standard for **all external API providers**. Document in `docs/PROVIDER_INTEGRATION_PATTERN.md`. (30 min)
11. **BP-X1 anti-leak gate:** Verify ALL backtester code paths use slice_pit (no direct df access). **End-to-end test** that backtester cannot see future data. (1 hour test-writing)
12. **PD-11 + PHS-12 recency gate:** "Last peak/right-shoulder must be near end" — verify same recency gate applied to ALL pattern detectors (not just 2). Currently HHHL/Flags/Triangles/Wedges/CupHandle don't have explicit recency gate — possible missed gates. (45 min audit)
13. **PT-9 + PW-6 conf cap 0.90:** Direction-uncertain patterns capped at 0.90 (not 0.95) — verify intent. Symmetric triangle is genuinely direction-uncertain; wedges are directional but reversal-pattern uncertainty might justify the cap. Document in patterns/ROADMAP.md. (10 min)
14. **MDPI-X1 stub facade:** market_data_providers/__init__.py has 0 exports. **Once 2nd provider added** (Polygon/Alpaca/IEX), promote to symbol-registry pattern matching patterns/__init__.py. (placeholder)
15. **Theme T32 sibling-discipline document:** With 9 sibling pairs now catalogued, write `docs/SIBLING_MODULE_PATTERN.md` capturing the 4-condition AND gate template + "only-moves-UP" / "only-moves-DOWN" invariant + symmetric configuration constants. (45 min)

## NEW THEMES UPDATED

- **NEW Theme T35 (cross-module helper imports within subdir):** 2 instances. Acceptable but should consolidate.
- **NEW Theme T36 (shared-library duplication across directories):** Sharpe/Sortino in 2 places — first audited shared-lib duplication.
- **NEW Theme T37 (backtester-vs-live-scorer drift):** **CRITICAL.** Backtest result accuracy depends on faithfulness to live flow. **Highest-impact finding this batch.**
- **Theme T32 (sibling-modules):** 9 pairs total — formalize as standard.
- **Theme T29 (pure-stdlib statistical):** 5 modules total (added PT triangles _linreg + BM compute_metrics).
- **Theme T8 (DRY):** Pivot-finder × 3 + RSI/SMA/ATR × 2 + Sharpe/Sortino × 2 — multiple consolidations needed.
- **Theme T11 (CSV newline=""):** BE-28 first positive — audit all other CSV writers.

## COVERAGE TRACKER

| Phase | Status | Cumulative |
|---|---|---:|
| Phase G | done | 30/~30 |
| Phase H | started | 17/~30 |
| Total true line-by-line | **+17 files (17 successful, 0 failures)** | **238 of ~378 (~63.0%)** |

**🎯 63% AUDIT MILESTONE. Patterns + Backtester + Providers SUBDIRECTORIES FULLY AUDITED. 9 sibling pairs catalogued. Critical Theme T37 backtester-vs-live drift identified.**

## NEXT BATCH (15-FILE)

Batch 72: Continue Phase H. Remaining src/ candidates:
- missing_data_gate, opening_range_scanner, paper_trader, performance_*, official_*, pick_logger, picks_csv, portfolio_risk_gate, position_monitor, quarterly_report, stock_stats, watchlist_manager, wisdom_consultant, wisdom_coverage, yearly_report, monster_*, news_signals, news_sentiment, pattern_engine, pattern_layer, pattern_stats, premarket_decision_contract (B70 done — skip), strategy_breakdown, sector_breakdown, sector_pnl, performance_source_separation, hypothesis_engine, indicators (B63 retry), book_ingest

End of Batch 71. **🎯 63.0% audit milestone. 9 sibling pairs catalogued. NEW Themes T35 (cross-module helpers), T36 (shared-lib duplication), T37 (backtester-live drift CRITICAL). Patterns subdir + Backtester subdir + Providers subdir COMPLETE.**
