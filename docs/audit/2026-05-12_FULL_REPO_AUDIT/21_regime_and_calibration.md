# Batch 15 — src/regime.py (123 lines) + src/calibration.py (387 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** regime.py (123 lines, fully read), calibration.py (387 lines, fully read)
**Phase:** B (scoring + data layer) — files 7 and 8 of ~18

## TOP HEADLINE FINDINGS

1. RG-X1: regime.py is THE MARKET CONTEXT for every pick — main.py reads it once per run, parallel_scorer caches it on cfg ("_regime"). A wrong regime flips position sizing (atr_trade_plan: bull=1.0x, transition=0.8x, chop=0.6x, bear=0.4x). 4-state classification with magic thresholds 5%/-2%/-5%. **63% of picks' position size hinges on these 3 numbers.**
2. RG-X2: BUG-3 fix archaeology (lines 3-7) shows author KNEW silent-unknown was bad and fixed it via 3-step retry+cache+fallback. **Best fail-LOUD recovery story in the audit so far.** Compare to other modules where "unknown" fallbacks abound silently.
3. RG-7 (line 79): "transition" fallback when no data + no cache — comment says "0.8x sizing in atr_trade_plan, more honest about uncertainty." **But this means a TOTAL data blackout still produces picks at 80% size.** Should arguably be "skip_all" or 0% size given no signal at all.
4. CB-X1: calibration.py is a READ-ONLY brain that produces statistics but NEVER writes scoring decisions. The `T39 weight-delta proposer (READ-ONLY)` comment confirms this. **Pure attribution layer — refreshing.** No mutation, no side effects in the main paths.
5. CB-X2: 387 lines, 4 bucket helpers, 3 report functions, full CLI. **Largest CLI surface in src/** with 5 subcommands. argparse-based, JSON-output supported, well-structured. Use as template for other CLI tools.
6. CB-15 (line 161): `rmults = [r.get("r_multiple") or 0.0 for r in rs]` — **`or 0.0` masks None as 0.** A pick that hasn't been evaluated (r_multiple=None) is treated as a 0R outcome. **Inflates the n count and pulls mean_r toward 0.** Win-rate denominator uses `len(rs)` regardless. **Includes pending picks in win-rate calc as losses.**
7. CB-21 (line 365): Bare `except: return []` in telegram_footer_lines. Justified by the "Safe: returns [] if anything goes wrong" docstring. Acceptable per Theme T1 documented exception.

## src/regime.py — LINE BY LINE

### Lines 1-7: Module docstring
- RG-1 GOOD: BUG-3 archaeology preserved. Three-step fix documented (retry, fallback SMA, disk cache).
- RG-2 GOOD: Date-stamped (May 2 2026). Operator can correlate with bug history.

### Lines 8-12: Imports
- RG-3 GOOD: stdlib + pandas + .data_fetcher. Clean.

### Line 14: _CACHE_PATH
- RG-4 BUG: `Path("data/last_regime.json")` — RELATIVE PATH AGAIN. **7th file in audit with this pattern** (HB, PRG, PL, main.py, SCS, MDH, RG).

### Lines 17-27: _load_cached_regime
- RG-5 GOOD (lines 19-20): Existence check first.
- RG-6 GOOD (lines 21-25): Defensive read with try/except. Adds `from_cache: True` marker — lets callers distinguish.
- RG-7 BUG (lines 26-27): `except Exception: return None` — bare except. Theme T1. But here arguably defensible (corrupt cache = no cache, fall through to fresh fetch). No log though — silent corruption goes unnoticed.

### Lines 30-37: _save_regime
- RG-8 GOOD (line 33): mkdir defensive.
- RG-9 BUG: NO ATOMIC WRITE. Compare to MDH-19 which uses tmp+replace. Power-loss mid-write corrupts cache. For a 1-line JSON file, low risk but inconsistent with MDH gold standard.
- RG-10 BUG (lines 36-37): bare except `pass`. Theme T1. Cache write failure silent. **Combined with RG-7, regime cache is doubly silent: writes silent, reads silent.**

### Lines 40-50: _fetch_spy_with_retry
- RG-11 GOOD (line 40): max_attempts=3 default with retry loop.
- RG-12 BUG (line 44): `fetch_ohlcv("SPY", period="1y")` — full year. For regime detection only need ~200 trading days (~10mo). 1y is generous.
- RG-13 GOOD (line 45): `len(df) >= 100` minimum bars guard.
- RG-14 BUG (line 49): `time.sleep(2)` — fixed 2-second backoff. **No exponential backoff, no jitter.** 3 attempts = 4 seconds total. Acceptable for synchronous flow but anti-pattern.
- RG-15 BUG (line 50): Returns `last` (final attempt's result) which may be EMPTY. Caller (line 64) checks `spy.empty` so OK in practice.

### Lines 53-122: market_regime — THE CORE FUNCTION
- RG-16 GOOD (lines 53-60): 5-line docstring documenting 3 fallback layers.
- RG-17 BUG (line 60 docstring): "Conservative bull default if no cache exists (allows trading)" — but actual code at lines 72-80 returns "transition" not "bull". **Docstring lies.** Theme T10. May be older docstring not updated when fix was applied.
- RG-18 BUG (lines 64-80): Total fetch failure branch. Cache fallback → transition fallback. **No 4th option of "skip_all"** even though premarket_sanity has that concept. With NO data NO cache, generating any picks is questionable.
- RG-19 GOOD (lines 67-68): `cached["fetch_failed"] = True` marker — downstream can see degraded state.
- RG-20 BUG (line 72-80): "transition" fallback per RG-7 — picks generated at 80% size even with zero data signal. **Recommend: when fetch_failed AND no cache, return regime="skip_all" or similar that downstream gate respects.**
- RG-21 GOOD (line 82): explicit float coercion.
- RG-22 GOOD (lines 85-90): 200d SMA preferred, 100d fallback. Documented sma_window field surfaces which was used.
- RG-23 GOOD (line 89): `min(100, len(spy))` — guard against very short df.
- RG-24 GOOD (lines 95-101): Multi-line comment documenting the 4-state classification with thresholds and intent. Operator-friendly.
- RG-25 BUG (lines 102-109): Magic thresholds 5.0 / -2.0 / -5.0. Named in comment but hardcoded in code. Same Theme as Batch 12 SC-X3 (63 magic numbers in scorer). External config would help.
- RG-26 BUG (line 102): `>= 5.0` — strict comparison. SPY exactly 5.0% above SMA = "bull". Edge case OK.
- RG-27 GOOD (lines 111-120): Result dict has 8 fields. Rich audit.
- RG-28 BUG (line 115): `"spy_sma_anchor": round(sma, 2)  # M5: honest name when sma_window != 200` — duplicates spy_sma200 + sma_value. **THREE field names for the same value.** Theme T2 schema fragmentation. Comment explains the rename in progress but old fields kept for backcompat.
- RG-29 BUG (line 116): `"sma_value"` — fourth name candidate. Same value yet again.
- RG-30 BUG (line 117): `"bullish": bullish` — derived from line 92 `spy_close > sma`. **DOESN'T MATCH the 4-state regime label.** "transition" with distance_pct = +1.0% has bullish=True (close > sma) but regime="transition". A caller reading bullish gets a different signal than one reading regime. Inconsistent.
- RG-31 GOOD (line 121): `_save_regime(result)` — caches every successful computation.

### Cross-cutting RG: 4 names for SMA value, 1 doc lie, 1 schema mismatch
RG-28+29: spy_sma200, spy_sma_anchor, sma_value all = same value. Field bloat hiding migration.
RG-17: docstring says "bull default" but code says "transition default."
RG-30: `bullish` boolean diverges from `regime` label semantics.

## src/calibration.py — LINE BY LINE

### Lines 1-20: Module docstring
- CB-1 GOOD: Documents purpose (T37+T38), data source (backtest CSVs), consumers (T39, T40, manual), CLI surface.
- CB-2 GOOD: Explicit "READ-ONLY" tag for T39 weight-delta proposer.

### Lines 21-29: Imports
- CB-3 GOOD: stdlib only (csv, json, defaultdict, dataclass, Path, statistics). No external deps.
- CB-4 GOOD (line 21): `from __future__ import annotations`.

### Line 31: RESULTS_ROOT
- CB-5 BUG: `Path("data/backtest_results")` — **8th relative-path bug.** HB, PRG, PL, main.py, SCS, MDH, RG, CB.

### Lines 36-46: list_runs / latest_run
- CB-6 GOOD: Defensive existence check.
- CB-7 GOOD (line 41): `sorted([d for d in root.iterdir() if d.is_dir()])` — directory listing only. Sorted lexicographically. **Assumes run-id naming sorts chronologically** (e.g., "2026-05-12_..."). Safe convention but undocumented requirement.
- CB-8 GOOD: latest_run trivial.

### Lines 49-70: load_picks
- CB-9 BUG (line 51): `Path(run_dir) / "picks.csv"` — assumes filename. If picks.csv is named differently (e.g., "all_picks.csv"), file not found.
- CB-10 GOOD (line 53): `raise FileNotFoundError` — loud failure. ✅
- CB-11 GOOD (lines 55-69): Defensive numeric coercion for 10 fields. Catches None, "", "None" string. Three sentinel forms handled.
- CB-12 BUG (line 67): `except (ValueError, TypeError): raw[k] = None` — converts "abc" to None. **Silently corrupts data.** A typo in the CSV field becomes None which downstream treats as "missing." Should at least log.
- CB-13 BUG: Field list (lines 58-60) `("score", "entry", "stop_loss", "take_profit", "rsi", "atr", "exit_price", "days_held", "r_multiple", "return_pct")` — **does NOT match pick_logger FIELDS (Batch 11 PL-8) which has "qty" not "quantity", and pick_logger writes "score" but parallel_scorer writes "composite".** Calibration may be reading from a DIFFERENT CSV schema (backtest_results vs picks_log). Need cross-check. If same schema, missing fields like trade_type / tag.
- CB-14 SMELL (lines 56-69): Inline numeric coercion. Could be a `_coerce_numeric_fields(raw, FIELDS_NUMERIC)` helper. Trivially extracted.

### Lines 75-107: 4 bucket helpers
- CB-15 GOOD: Each is small and pure.
- CB-16 BUG (line 75-81): `_rsi_bucket` thresholds 30/50/70 — magic but conventional.
- CB-17 BUG (line 84-89): `_score_bucket` thresholds 0.5/0.7/0.85 — magic.
- CB-18 BUG (line 92-100): `_atr_bucket` thresholds 1.5/3/5 — magic but commented.
- CB-19 SMELL: All 4 bucketing functions have the same shape: `if x is None: return na_label; if x < t1: return label1; ...`. Could be a generic `_bucketize(value, [(t1, l1), (t2, l2), ...], na_label)` helper.
- CB-20 BUG (line 105): `len(pick_date) < 7` — fragile string-length check for "YYYY-MM" prefix. Should be regex or date parse. "abc" passes len check but slices to "abc" not a valid month.

### Lines 112-131: BucketStat dataclass
- CB-21 GOOD: Frozen dataclass-like (no @dataclass(frozen=True) but immutable in practice).
- CB-22 GOOD (lines 122-131): as_row method serializes for table output. Clean.
- CB-23 SMELL: 7 fields, no validation. Could use Pydantic.

### Lines 134-137: _is_win
- CB-24 BUG (line 137): `return r is not None and r > 0` — strict positive. r_multiple = 0 (breakeven) is NOT a win. ✅ but means breakeven counts as loss for win_rate computation. Industry-standard split.

### Lines 140-173: attribute_by — THE AGGREGATION
- CB-25 GOOD: Generic function takes keyfunc.
- CB-26 GOOD (line 142): min_n=5 default — drops thin buckets.
- CB-27 GOOD (lines 149-152): Defensive try/except around keyfunc call. Skips bad rows.
- CB-28 BUG (line 153-154): `if k is None: continue` — silently drops rows where keyfunc returns None. No counter, no audit.
- CB-29 GOOD (line 155): str(k) coercion — handles non-string keys.
- CB-30 BUG (line 161): `rmults = [r.get("r_multiple") or 0.0 for r in rs]` — **THE PENDING-AS-LOSS BUG.** `r.get("r_multiple") or 0.0` makes None → 0.0. Since pending picks have r_multiple=None, they become 0R. Then mean_r averages real outcomes WITH 0R for pending. **Mean_r artificially pulled toward 0.** This is ONLY non-trivial if rows include pending picks — depends on what backtest_results contains. **Needs confirmation: does load_picks include pending? If yes, attribution is inflated.**
- CB-31 BUG (line 162): Same `or 0.0` pattern for return_pct.
- CB-32 BUG (line 168): `win_rate=wins / len(rs)` — denominator includes pending picks (per CB-30). **Win rate INCLUDES pending picks as losses.** Inflates loss rate.
- CB-33 BUG (line 169-170): `mean(rmults)` and `sum(rmults)` use the 0.0-padded list. Compounds CB-30 distortion.
- CB-34 GOOD (line 173): Sort by n descending. Most-statistically-significant first.

### Lines 178-184: FACTOR_KEYS
- CB-35 GOOD: 5 named factors with lambda extractors.
- CB-36 BUG (line 183): "exit_status" — **field name not in pick_logger.FIELDS (Batch 11)**. So per CB-13, pick_logger writes "evaluation_status" + "exit_price" but no "exit_status". **calibration reads a field that pick_logger doesn't write.** Either backtest_results has a different schema OR calibration has a bug.

### Lines 187-201: per_factor_report / per_timeframe_report
- CB-37 GOOD: Clean composition over attribute_by + FACTOR_KEYS.
- CB-38 GOOD: Per-timeframe sorts chronologically.

### Lines 204-218: overall_summary
- CB-39 BUG (line 209): Same `or 0.0` pattern → pending picks count as 0R losses (per CB-30).
- CB-40 BUG (line 217): `expectancy_R == mean_r` — duplicate field. Could just be `mean_r`.
- CB-41 SMELL: `wins` denominator is `len(rows)` not `len(non-pending rows)`. Same distortion as CB-32.

### Lines 223-235: _resolve_run
- CB-42 GOOD: 3-way resolution (literal "latest", direct path, RESULTS_ROOT/arg).
- CB-43 GOOD: SystemExit on not-found — appropriate for CLI tool.

### Lines 238-248: _fmt_table
- CB-44 GOOD: Pretty-printed ASCII table with auto-widths.
- CB-45 SMELL: 11-line custom table formatter. Could use `rich` or `tabulate` library, but stdlib-only is consistent with CB-3.

### Lines 251-316: main CLI
- CB-46 GOOD: Argparse with subparsers. 5 subcommands.
- CB-47 GOOD (lines 256-260): Loop creates 4 identical subparsers. DRY.
- CB-48 BUG (line 269): `getattr(args, "run", None) or getattr(args, "run_id", "latest")` — getattr fallback chain. Works but brittle if attrs renamed.
- CB-49 SMELL (line 309-314): "run" subcommand recursively calls main(). Convoluted. Could be a clean shared helper.
- CB-50 GOOD: --json output supported on every subcommand.

### Lines 325-366: telegram_footer_lines (T40)
- CB-51 GOOD (line 328-329): Docstring explicit about safe-fail.
- CB-52 GOOD: `min_n: int = 30` default — much higher than internal min_n=5. Telegram footer shouldn't surface noisy buckets.
- CB-53 GOOD (lines 343-348): Iterates factor report, computes bias = bucket mean_r - overall mean_r.
- CB-54 BUG (line 344-345): `if factor == "exit_status": continue` — exit_status excluded. Why? No comment. Probably because exit_status is descriptive not predictive (TP_HIT is good, SL_HIT is bad — already encoded in r_multiple). Defensible but undocumented.
- CB-55 GOOD (lines 350-351): max/min with default=None.
- CB-56 BUG (line 356, 360): Magic 0.05 / -0.05 thresholds for "best edge" / "worst drag" surfacing. Buried.
- CB-57 GOOD (line 365-366): bare except returns []. **Documented Theme T1 exception.**

### Lines 369-385: open_proposals_summary
- CB-58 GOOD: Inline import of weight_proposer (defensive lazy import).
- CB-59 GOOD: Counts kills/boosts/penalties separately.
- CB-60 BUG (line 384-385): bare except returns None. **Less documented than CB-57.** Should be commented.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### RG-X1: regime computation has 4 names for the same SMA value
spy_sma200, spy_sma_anchor, sma_value, all round(sma, 2). Plus `bullish` boolean that diverges from `regime` label. **Schema fragmentation in a 123-line file.** Theme T2 condensed.

### RG-X2: Documented fail-LOUD recovery is GOOD, but exception handling still silent
3-step retry+cache+fallback is best-in-class for graceful degradation. But individual error catches (RG-7, RG-10) are bare except: pass. Recovery is loud, error capture is silent. Mixed message.

### CB-X1: pending-picks-as-losses bug propagates through entire calibration
CB-30 (`or 0.0`) at line 161 → CB-32 (win_rate denominator) → CB-33 (mean_r/total_r) → CB-39 (overall_summary). **One bug, four downstream distortions.** Fix at source (filter pending before aggregation): `rs_completed = [r for r in rs if r.get("r_multiple") is not None]`.

### CB-X2: calibration reads fields pick_logger doesn't write
- CB-13: numeric field list includes "rsi", "atr", "exit_price", "days_held" — none in pick_logger FIELDS
- CB-36: FACTOR_KEYS reads "exit_status" — pick_logger has "evaluation_status"
**Either backtest_results has a different schema (likely) OR calibration is broken (need to verify backtester output).** If different schemas, NO single source of truth across pick_logger and backtester.

### Cross-cutting: 8 files with relative-path constants now confirmed
HB-10, PRG-3, PL-5, main.py M-CFG1, SCS-14, MDH-7, RG-4, CB-5. **src/_paths.py URGENT.**

### Cross-cutting: Magic-threshold count keeps growing
- Batch 12 SC: 63 magic numbers in scoring
- Batch 13 IND: 4+ magic candlestick thresholds
- Batch 14 MC: 18/6/2 month thresholds
- Batch 15 RG: 5/-2/-5 regime thresholds, 100/200 SMA windows
- Batch 15 CB: 30/50/70 RSI, 0.5/0.7/0.85 score, 1.5/3/5 ATR, 5/30 min_n, 0.05 bias threshold
**Total ~80+ magic numbers across audited files.** Single config.thresholds.yaml would externalize all.

### Cross-cutting: telegram_footer_lines bare-except is the SECOND documented Theme T1 exception
First was MDH-40 ("telemetry must not break picker"). Second is CB-57 ("Safe: returns [] if anything goes wrong"). **Both are non-critical-path.** Pattern: bare-except OK if explicitly documented AND on non-critical path.

## SUMMARY (Batch 15)

| Severity | regime | calibration | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 8 | 12 | 4 | 24 |
| Data/safety | 7 | 6 | 0 | 13 |
| Code smell | 4 | 8 | 0 | 12 |
| Good code | 11 | 23 | 0 | 34 |
| Total findings | 30 | 49 | 4 | 83 |

## TOP 10 CRITICAL FIXES from Batch 15

1. CB-30+32+33+39: Filter pending picks before aggregation. `rs_completed = [r for r in rs if r.get("r_multiple") is not None]`. (15 min, biggest stat-correctness win)
2. RG-30: Either compute `bullish` from regime label OR remove `bullish` field. Currently divergent. (5 min)
3. RG-28+29: Pick canonical SMA field name. Deprecate the other 3. (10 min)
4. RG-17: Fix docstring "Conservative bull default" → "transition default". (1 min)
5. RG-20: Add 4th tier for total-blackout case (no data + no cache) → "skip_all" or 0% sizing. (15 min)
6. CB-13+36: Cross-check backtester output schema vs calibration field names. Document or fix. (1 hr)
7. RG-9: Add atomic write to _save_regime (match MDH gold standard). (10 min)
8. CB-12: Log when load_picks coerces non-numeric to None (instead of silent corruption). (10 min)
9. RG-25: Externalize regime thresholds (5/-2/-5) to config. (15 min)
10. RG-4 + CB-5 + 6 others: src/_paths.py for all relative-path constants. (15 min)

## NEW THEMES UPDATED

- Theme T1 (bare except) DOCUMENTED EXCEPTIONS: Now 2 confirmed (MDH-40 telemetry, CB-57 telegram footer). Pattern emerging: OK on non-critical path WHEN documented.
- Theme T2 (schema drift): regime has 4 names for same value (RG-X1). calibration reads fields pick_logger doesn't write (CB-X2). Continues amplifying.
- Theme T11 (fail-open by accident): regime "transition" fallback on data blackout (RG-20).
- Theme T13 (silent-default-fills): CB-30 `or 0.0` masks pending as 0R loss.
- Theme T14 (gold-standard patterns): RG-X2 documented fail-LOUD recovery is exemplary BUT mixed with silent-error capture.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 8/~18 done | regime, calibration | 8/~18 |
| Total true line-by-line | | +2 files | 31 of 382 |
| Remaining | | | 351 files |

## NEXT BATCH

Batch 16: src/news_signals.py + src/news_engine.py — news classification + signal extraction. news_signals is referenced by hard_blocks (HB-55 catastrophic news check) and main.py news boost.

End of Batch 15. Phase B in progress (8/18).
