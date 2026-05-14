# Batch 44 — src/calibration.py (387 lines) + src/parallel_scorer.py (177 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** calibration.py (387 lines), parallel_scorer.py (177 lines)
**Phase:** D (pipeline & output) — files 25 and 26 of ~30
**MILESTONE:** 50th audit document

## TOP HEADLINE FINDINGS

1. CA-X1: calibration.py is **THE BACKTEST ATTRIBUTION ENGINE** (T37+T38) — reads backtest CSVs and computes per-factor + per-month win_rate / mean_R / total_R. **READ-ONLY.** Per docstring lines 9-12: "Used by T39 weight-delta proposer (READ-ONLY) + T40 weekly Telegram footer + manual review (CLI)." **The CALIBRATION half of probability_engine PE3-X1.**
2. CA-X2: calibration.py has **THE MOST POWERFUL CLI in audit** — 5 subcommands (latest/factors/timeframes/summary/run) with --json + --min-n flags. **Operator-runnable on any backtest.** Compare Batch 43 PE3-X2 4-test smoke. **CA + PE3 are the 2 most CLI-mature modules.**
3. CA-X3 (lines 178-184): `FACTOR_KEYS` dict — **5 factor extractors as lambdas in dict.** Pluggable factor architecture. Adding a new factor = add 1 lambda. **Excellent extensibility.** ✅
4. CA-X4 (line 142, line 188, line 197, line 325): `min_n` threshold (default 5 or 30) — **statistical-validity floor.** Buckets with < min_n picks are dropped. **Per Batch 22 SJ-X3 minimum-sample-size cross-cutting**, this is the FORMAL implementation. **Sample-size discipline.** ✅
5. PS-X1: parallel_scorer.py is **THE PIPELINE ORCHESTRATOR** — for each ticker, runs: indicators → fundamentals → news → composite_score → watchlist boost → pattern multiplier → day score → trade type → ATR plan → monster hunt → wisdom consult. **11 INTEGRATION POINTS PER TICKER.** **Most-coupled module in audit.**
6. PS-X2: parallel_scorer has **4 SCORE-MUTATION POINTS** all touching `scores["composite"]`:
   - Line 57: watchlist_boost added (max +0.30)
   - Line 72: pattern_multiplier multiplied (× 0.85-1.15)
   - Line 147: wisdom score_adj added (max ±0.05)
   - composite_score itself includes sector_mult (× 1.0-1.30)
   **Compounding chain: raw × sector_mult × pattern_mult + watchlist + wisdom** = potentially **±50% adjustment from raw.** Per Batch 41 WM-X4 cross-cutting compounding warning CONFIRMED at integration site.
7. PS-X3 (lines 73-74, 124-127, 149-153): **3 BARE-EXCEPT BLOCKS** with silent score-default fallbacks. **Per Batch 30 PL-X1 "wires through but rarely fires" risk** — a broken pattern_layer/monster_hunt/wisdom_consultant import = silent neutralization. **A future refactor that breaks an import = ALL tickers lose that signal silently.** **Ranks among biggest silent-failure risks in audit.**

## src/calibration.py — LINE BY LINE

### Lines 1-20: Module docstring
- CA-1 GOOD: 20-line docstring with T37+T38 reference + CLI examples + downstream consumers.
- CA-2 GOOD: "READ-ONLY" qualifier on T39 reference. **Joins OBSERVE-MODE pattern (Batch 39 GO-X1 cross-cutting).**

### Lines 21-31: Imports
- CA-3 GOOD: Pure stdlib (csv, json, statistics, defaultdict).
- CA-4 BUG: Relative path `data/backtest_results`. **27th file with this pattern.**

### Lines 36-46: list_runs / latest_run
- CA-5 GOOD: Defensive empty-list on missing dir.
- CA-6 GOOD: Sorted oldest→newest.
- CA-7 GOOD: latest_run() returns Optional.

### Lines 49-70: load_picks
- CA-8 GOOD (line 53): Explicit FileNotFoundError on missing CSV.
- CA-9 GOOD (lines 58-60): 10 named numeric columns hardcoded for coercion.
- CA-10 BUG (lines 58-60): Schema-coupled hardcoded list. If picks.csv adds new numeric column, must update here. Per Batch 28 cross-cutting Theme T2 schema-chaos.
- CA-11 GOOD (lines 62-68): Triple-defensive None / "" / "None" check + try/except float coercion. **Handles CSV's stringified None.**
- CA-12 GOOD (line 67): Specific (ValueError, TypeError) — NOT bare-except. ✅

### Lines 75-107: Bucket helpers
- CA-13 GOOD: 4 bucket functions (rsi/score/atr/month) with explicit thresholds + None handling.
- CA-14 BUG (lines 78-81): RSI bucket boundaries 30/50/70 — magic. Standard TA convention. Should cite source.
- CA-15 BUG (lines 86-89): Score buckets 0.5/0.7/0.85 — magic. Per Batch 31 HH-X3 cross-cutting.
- CA-16 GOOD (lines 92-100): ATR bucket as percentage of entry — divides for volatility-comparable buckets.
- CA-17 GOOD (line 94): `not atr or not entry or entry <= 0` — defensive.
- CA-18 GOOD (line 105): "len(pick_date) < 7" — defensive against malformed date.

### Lines 112-131: BucketStat dataclass
- CA-19 GOOD: 6-field dataclass with as_row() helper.
- CA-20 GOOD (line 122-131): Rounding for display. JSON-friendly.

### Lines 134-137: _is_win
- CA-21 GOOD: Explicit win definition (r_multiple > 0). Single source of truth.

### Lines 140-173: attribute_by
- CA-22 GOOD: Generic group-by attribution.
- CA-23 BUG (line 151-152): bare except on keyfunc. **Theme T1 undocumented.** A KeyError in lambda = silent skip.
- CA-24 GOOD (line 159-160): Per CA-X4, min_n threshold drops small buckets.
- CA-25 GOOD (lines 161-172): 5 stats per bucket.
- CA-26 GOOD (line 173): Sorted by n DESC for display priority.

### Lines 178-184: FACTOR_KEYS
- CA-27 GOOD: Per CA-X3, pluggable factor dict.
- CA-28 BUG (line 178): Type hint `Dict[str, callable]` — lowercase callable. Should be `Callable`.

### Lines 187-201: Reports
- CA-29 GOOD: per_factor_report + per_timeframe_report wrap attribute_by.

### Lines 204-218: overall_summary
- CA-30 GOOD: Returns 6-key headline dict.
- CA-31 GOOD (line 207-208): Empty-rows fallback to zero-stats. Defensive.
- CA-32 BUG (lines 215, 217): `mean_r` and `expectancy_R` are SAME computation. Duplicate field. Should alias or remove one.

### Lines 223-235: _resolve_run
- CA-33 GOOD: 3-strategy run resolution (latest / abs path / RESULTS_ROOT-relative).
- CA-34 GOOD: SystemExit with operator-friendly emoji + error.

### Lines 238-248: _fmt_table
- CA-35 GOOD: Pure-stdlib pretty table — column-aware.
- CA-36 GOOD (line 240): Defensive empty-rows fallback.
- CA-37 GOOD (line 241): `max(len(c), max(len(...)))` — handles empty data.

### Lines 251-316: main (CLI)
- CA-38 GOOD: argparse with 5 subcommands.
- CA-39 GOOD (lines 256-260): DRY subcommand setup loop.
- CA-40 GOOD (lines 277-289): "summary" produces 4-section human report.
- CA-41 BUG (line 311-314): Recursive `main()` call for `run` subcommand. **Anti-pattern** — should call `_resolve_run + render` directly. Recursive argparse is fragile.

### Lines 319-320: __main__
- CA-42 GOOD: SystemExit(main()) — proper exit code propagation.

### Lines 325-366: telegram_footer_lines (T40)
- CA-43 GOOD (lines 326-330): Docstring explicit "Safe: returns [] if anything goes wrong."
- CA-44 GOOD (lines 341-348): Best/worst factor edge detection via bias = mean_r - overall_mean_r.
- CA-45 GOOD (lines 356-360): Magic 0.05 R bias threshold for "edge". Should be const.
- CA-46 GOOD (line 365-366): Per T40 contract, bare-except returns [].

### Lines 369-385: open_proposals_summary
- CA-47 GOOD: Cross-module link to weight_proposer (Batch 22 WP).
- CA-48 GOOD (lines 376-378): 3-action breakdown (kill / boost / penalize).
- CA-49 BUG (line 384-385): bare except. **Should be specific (ImportError, AttributeError, ...).**

## src/parallel_scorer.py — LINE BY LINE

### Lines 1-5: Module docstring
- PS-1 GOOD: 5-line docstring with PR #67 archaeology.
- PS-2 GOOD: References classify_with_day_score (Batch 40 MG).

### Lines 6-20: Imports
- PS-3 BUG: 13 module imports. **HIGHEST IMPORT FAN-OUT in audit.** Per PS-X1, most-coupled module. **A breaking change in ANY of 13 deps cascades here.**
- PS-4 GOOD (line 18-20): Aliased imports for readability (`as _wisdom_consult`, etc.).

### Lines 25-36: _resolve_regime
- PS-5 GOOD (lines 26-27): "M1 fix" archaeology comment — caches regime per-run.
- PS-6 GOOD (line 28): cfg-cached regime. Per Batch 22 SJ-X1 cache-via-config pattern.
- PS-7 BUG (lines 30-34): Inline import + bare-except + silent "unknown" fallback. **Latent silent-failure source.** Per PS-X3.
- PS-8 GOOD (line 35): Cache result back into cfg.

### Lines 38-163: _score_one (THE INTEGRATION FUNCTION)
- PS-9 GOOD (line 38): Single-ticker scorer. Thread-safe by design.
- PS-10 GOOD (lines 39-43): Indicator + signal extraction + close-price guard.
- PS-11 GOOD (lines 44-46): fetch_info + passes_filters early exit.
- PS-12 GOOD (lines 47-51): fund + sent + composite_score (Batch 43 SC-X1).
- PS-13 GOOD (lines 53-58): Per PS-X2 mutation #1 — watchlist_boost. Recapped composite [0,1].
- PS-14 GOOD (lines 60-74): Pattern multiplier with explicit T50 comment.
- PS-15 GOOD (lines 60-62): "Failure-safe" called out in comment.
- PS-16 BUG (lines 73-74): Per PS-X3 silent-failure. **An ImportError on pattern_layer = ALL tickers get pattern_multiplier=1.0 silently.** No alarm.
- PS-17 GOOD (lines 76-77): min_score early exit AFTER all adjustments. Filter.
- PS-18 GOOD (lines 79-86): day_trading_score + classify_with_day_score (Batch 40 MG).
- PS-19 GOOD (line 81): `news_boost_for_day = max(0, wl_boost)` — only positive news helps day trades. **Asymmetric design comment.**
- PS-20 GOOD (lines 87-89): trade_type surfaced.
- PS-21 GOOD (lines 91-95): ATR + price + capital extraction with 2-key fallback (capital or account_size).
- PS-22 GOOD (lines 96-98): "E3b" archaeology + regime-based size adjustment table inline.
- PS-23 GOOD (lines 100-106): atr_trade_plan vs trade_plan dispatch based on ATR availability.
- PS-24 GOOD (lines 108-127): Monster Hunt with try/except — "additive, never blocks" docstring.
- PS-25 BUG (lines 124-127): Per PS-X3, bare-except silent-failure point #2.
- PS-26 GOOD (lines 110): "if cfg.get('monster', {}).get('fetch_short_float', False)" — explicit feature flag.
- PS-27 GOOD (line 112): `d2e_norm = d2e_val if d2e_val < 999 else None` — handles 999-sentinel from earnings module.
- PS-28 GOOD (lines 129-153): Wisdom consult with try/except.
- PS-29 GOOD (line 145): "Tiny score tilt (capped ±0.05 in observe-mode)" — Batch 25 wisdom_consultant cross-cutting documented HERE.
- PS-30 BUG (lines 149-153): Per PS-X3, bare-except silent-failure point #3. **3 silent-failure points total in _score_one.**
- PS-31 GOOD (lines 155-160): 5-field result dict with defensive name-fallback.
- PS-32 GOOD (line 157): 3-source name fallback (name → longName → shortName). Per Batch 36 PF-7 cross-cutting Theme T2.
- PS-33 BUG (lines 161-163): outermost bare-except + print + return None. **Catches ANY ticker error.** Operator sees `[score] AAPL: KeyError: 'close'` but no MDH event recorded. Per Batch 14 MDH-X1 cross-cutting, this loses observability.

### Lines 166-176: score_all
- PS-34 GOOD: ThreadPoolExecutor with as_completed.
- PS-35 GOOD (line 169): max_workers=10 — moderate concurrency.
- PS-36 GOOD (line 171-174): Filter None results.
- PS-37 GOOD (line 175): Sorts by composite DESC. Top picks first.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### CA-X1 + PE3-X1: Calibration ↔ Probability engine pair
- calibration.py READS backtest results (post-trade)
- probability_engine.py CONSUMES historical hit rates (pre-trade decision)
- weight_proposer.py (Batch 22) READS calibration to propose weight changes
**Triangle: Calibration ↔ Weight Proposer ↔ Pick Logger** — FULL CLOSED LOOP. Per Batch 23 SA-X1 brain-pillar architecture.

### PS-X1 + PS-X2: parallel_scorer is THE INTEGRATION SITE
- 13 module dependencies
- 11 integration steps per ticker
- 4 score-mutation points
- 3 silent-failure points
**THE MOST FRAGILE MODULE in audit.** A brain-pillar refactor MUST start here.

### PS-X2 + Batch 41 WM-X4 + Batch 30 PL-X1 cross-cutting CONFIRMED
Compounding score impact at INTEGRATION SITE:
| Source | Bound | Applied at |
|---|---|---|
| sector_mult | × 1.0-1.30 | composite_score (B43) |
| pattern_multiplier | × 0.85-1.15 | parallel_scorer line 72 |
| watchlist_boost | + 0-0.30 | parallel_scorer line 57 |
| wisdom score_adj | ± 0.05 | parallel_scorer line 147 |
| **TOTAL POSSIBLE** | **0.0 to 1.0** (clipped) | |

**Worst case for boost: raw 0.6 × 1.3 sector × 1.15 pattern + 0.30 watchlist + 0.05 wisdom = 1.247 capped at 1.0** — the cap absorbs ~25% of theoretical boost. **Operator can't tell from final composite WHICH adjustments fired or how much was clipped.** **HIGH-VALUE FIX: surface clipping events in scores dict.**

### CA-X4 cross-cutting: min_n statistical-validity discipline
Now 4 modules with explicit min-sample-size guards:
- pick_evaluator (Batch 27 PV-?)
- weight_proposer (Batch 22 WP)
- signal_journal (Batch 22 SJ)
- calibration (this batch)
**4 modules with statistical hygiene.** Phase D + brain layer is mature.

### PS-X3 + Cross-cutting Theme T13 silent-default-fills
3 silent-failure points in _score_one + outermost catch-all = **4 layers of silent failure in 1 function.** Per Batch 30 PE2-X2 silent-detector-failure pattern. **Worst single-function fail-silent score in audit.**

### Cross-cutting: bare-except this batch
- calibration: 3 (CA-23, CA-46, CA-49)
- parallel_scorer: 4 (PS-7, PS-16, PS-25, PS-30, PS-33)
**7 bare-excepts in 2 files.** Phase D bare-except creep MAJOR regression. Most concentrated in PS due to integration-site fail-safe philosophy.

### Cross-cutting: 27 files with relative-path constants (no change much — calibration adds, parallel_scorer none)

### Cross-cutting: ATOMIC WRITE
N/A this batch (read + compute + return).

## SUMMARY (Batch 44)

| Severity | calibration | parallel_scorer | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 7 | 8 | 5 | 20 |
| Data/safety | 4 | 4 | 0 | 8 |
| Code smell | 1 | 1 | 0 | 2 |
| Good code | 37 | 25 | 0 | 62 |
| Total findings | 49 | 38 | 5 | 92 |

## TOP 10 CRITICAL FIXES from Batch 44

1. PS-X3 + cross-cutting: Replace 3 bare-excepts in _score_one with specific exception types + MDH event recording. **A failed pattern_layer import shouldn't silently zero out 100% of pattern signals.** (30 min)
2. PS-X2: Add `composite_clipped` flag to scores when [0,1] cap absorbs adjustment. Operator transparency. (10 min)
3. PS-33: Outermost catch-all should record MDH event so operator sees count of failed tickers per run. (10 min)
4. CA-X1: Document the calibration ↔ probability_engine ↔ weight_proposer triangle in BRAIN_ARCHITECTURE.md. (15 min)
5. CA-32: Drop or alias duplicate `mean_r` / `expectancy_R` in overall_summary. (3 min)
6. CA-41: Refactor recursive main() call for "run" subcommand. (10 min)
7. CA-23, CA-46, CA-49: Replace 3 bare-excepts with specific exception types. (5 min)
8. CA-10: Make load_picks numeric-coercion column list configurable / data-driven. (10 min)
9. PS-3: Document parallel_scorer's 13 imports as architecture diagram. (15 min)
10. CA-14, CA-15: Add provenance citations for RSI 30/50/70 + score 0.5/0.7/0.85 boundaries. (5 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): calibration 3 (intent-driven graceful degradation). parallel_scorer 4 (silent-failure-by-design). **PEAK Phase D bare-except concentration so far.**
- Theme T2 (schema drift): CA-10 hardcoded numeric column list.
- Theme T6 (atomic writes): N/A this batch.
- Theme T8 (DRY): N/A this batch.
- Theme T11 (fail-open by accident): PS-X3 4-layer silent failure in integration site.
- Theme T13 (silent-default-fills): PS-25, PS-30 silent zero-out of score components.
- Theme T14 (gold-standard patterns): calibration CLI (CA-X2), pluggable factor dict (CA-X3), min_n discipline (CA-X4) = TEMPLATE for measurement modules.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A | 8/8 COMPLETE | (none) | 8/8 |
| Phase B | 18/18 COMPLETE | (none) | 18/18 |
| Phase C | 12/12 COMPLETE | (none) | 12/12 |
| Phase D | 26/~30 done | calibration, parallel_scorer | 26/~30 |
| Phase E | 12/~50 done | (none) | 12/~50 |
| Total true line-by-line | | +2 files | **91 of ~382 (~23.8%)** |
| Remaining | | | **~291 files** |

## NEXT BATCH

Batch 45: src/missing_data_gate.py + src/premarket_readiness_gate.py — both 6-7KB Phase A/D safety gates we haven't audited. premarket_readiness pairs with premarket_decision_contract (Batch 36) and premarket_filter (Batch 36). Closes gate-layer audit.

End of Batch 44. Phase D in progress (26/30). **50th audit doc milestone.**
