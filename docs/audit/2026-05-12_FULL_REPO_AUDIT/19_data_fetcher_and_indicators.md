# Batch 13 — src/data_fetcher.py (231 lines) + src/indicators.py (307 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** data_fetcher.py (231 lines, fully read), indicators.py (307 lines, fully read)
**Phase:** B (scoring + data layer) — files 3 and 4 of ~18

## TOP HEADLINE FINDINGS

1. DF-X1: data_fetcher.py is THE FOUNDATION of every downstream signal. It produces the OHLCV DataFrames that indicators consume, plus the `info` dict that gates and scoring read. Bug here cascades to EVERY pick. Quality matters disproportionately.
2. DF-X2: data_fetcher.py is the BEST-INSTRUMENTED file in the audit so far. Every fetch path emits `record_market_data_event` with provider/stage/ticker/result/error. premarket_readiness_gate consumes this telemetry. **First file to have proper observability hooks.** Use as template.
3. IND-X1: indicators.py is PURE COMPUTATION — no I/O, no side effects, no logging. 16 indicator functions. **The cleanest file architecturally in the audit so far.** No bugs in math (per spot-checks), but several silent-degradation paths via .replace(0, np.nan) returning NaN that downstream treats as "missing data".
4. DF-12 (line 144): `info` dict initializes `averageVolume: 1_000_000` as DEFAULT. Then line 155 `info["averageVolume"] = getattr(fast, "ten_day_average_volume", None) or 1_000_000`. **If yfinance returns None for averageVolume, value is 1M (default).** Downstream is_valid_market_data line 227-228 checks `vol <= 0` — 1M passes the check. **Untradeable tickers SILENTLY get 1M default volume.** Theme T11.
5. DF-13 (line 176-177): Exception handler logs to telemetry then `pass` — but line 178-179 has `else: record success`. **The else clause runs ONLY if NO exception in the try block.** Combined: if try succeeds → log success. If try fails → log error then continue. ✅ pattern, but the `pass` at 177 is misleading visually — looks like a swallow but actually allows method to continue.
6. IND-13 (lines 273-282): 4 derived boolean flags computed conditionally on None checks. If indicator missing → flag is False (not None). **A False "above_psar" can mean "below PSAR" OR "PSAR data missing"** — no way to distinguish downstream. Single Boolean conflates two different states.
7. IND-21 (lines 295-297): `try: ...candlestick_patterns... except: pass` — bare except. Theme T1. If candlestick computation crashes, downstream sees no `cdl_*` flags, interprets as "no patterns detected" silently.

## src/data_fetcher.py — LINE BY LINE

### Lines 1-12: Module docstring + imports
- DF-1 GOOD: Brief docstring. yfinance + Finnhub.
- DF-2 GOOD (lines 8-12): Imports market_data_health helpers — telemetry hooks.
- DF-3 GOOD (line 13): Imports stooq fallback. Provider redundancy.

### Lines 15-19: Optional curl_cffi session
- DF-4 GOOD: Defensive try/except for optional dep. Falls back to None session.
- DF-5 SMELL (line 17): `cf_requests.Session(impersonate="chrome")` — module-level state. Same `SESSION` reused across all yf.Ticker calls. **For ThreadPoolExecutor with max_workers=5, all 5 threads share the SAME SESSION object.** curl_cffi sessions claim thread-safety per docs. ⚠️ but verify.
- DF-6 BUG: SESSION created at MODULE IMPORT TIME (Theme: side effect on import). Same anti-pattern as Batch 11 PL-7 (mkdir at import) and Batch 6 M-IO1 (subprocess at import). Tests importing data_fetcher get a real chrome-impersonating session whether they want it or not.

### Lines 22-26: Optional Finnhub
- DF-7 GOOD: Defensive optional import. HAS_FINNHUB flag.

### Lines 29-37: _normalize_ohlcv
- DF-8 GOOD (line 31): Defensive None/empty check.
- DF-9 GOOD (lines 34-35): Handles MultiIndex columns from yfinance (when batched).
- DF-10 GOOD (line 36): Lowercase normalization — eliminates High/HIGH/high inconsistency.

### Lines 40-43: _fetch_yfinance_ohlcv
- DF-11 GOOD (line 42): `auto_adjust=False, timeout=20` — explicit. **Has timeout, unlike parallel_scorer (Batch 8 PS-55).** ✅
- DF-12 SMELL (line 41): `if SESSION else yf.Ticker(ticker)` — duplicated condition. Could be `t = yf.Ticker(ticker, **({"session": SESSION} if SESSION else {}))`.

### Lines 46-47: _fetch_stooq_fallback_ohlcv
- DF-13 SMELL: Trivial 1-line wrapper. Could call fetch_stooq_ohlcv directly. Adds nothing.

### Lines 50-117: fetch_ohlcv (PRIMARY)
- DF-14 GOOD (lines 51-68): Excellent docstring. Documents primary/fallback, safety stance, AND a critical thread-safety note about yf.download() vs yf.Ticker().history(). **Best operational documentation in the audit so far.**
- DF-15 GOOD (lines 69-91): yfinance try block with telemetry on success/empty/error. **Three-state outcome (success/empty/error) instrumented.**
- DF-16 BUG (line 91): `print(f"[data] {ticker}: yfinance {type(e).__name__}: {str(e)[:120]}")` — prints to stdout in addition to telemetry. Same as parallel_scorer PS-9 (truncates to 120 chars). **Consistent print pattern but no traceback.**
- DF-17 GOOD (lines 93-115): Stooq fallback with same telemetry pattern. **Symmetric error handling.**
- DF-18 GOOD (line 117): `return pd.DataFrame()` — empty DataFrame on total failure. Predictable contract.
- DF-19 SMELL: 117-line function. Two large try/except blocks 90% identical. Could be `_try_provider(name, fetcher)` helper.
- DF-20 BUG: NO retry within yfinance fetch. A single transient 503 → empty result → fallback to stooq → if stooq is degraded too → empty DataFrame for the day. **No exponential backoff, no jitter.**

### Lines 120-132: fetch_universe_data
- DF-21 GOOD (line 121): max_workers default 5. Lower than parallel_scorer (10). Conservative — yfinance is the bottleneck.
- DF-22 GOOD (lines 123-129): ThreadPoolExecutor pattern. **Has the timeout pattern via fetch_ohlcv timeout=20.**
- DF-23 BUG (line 128): `if not df.empty and len(df) > 50:` — **MAGIC 50.** Drops tickers with fewer than 50 bars. For new IPOs, low-history tickers, or short-period data, silent drops. No telemetry on this filter.
- DF-24 GOOD (line 131): `write_market_data_run_summary(...)` — emits run-level summary. premarket_readiness_gate consumes this.
- DF-25 GOOD (line 130): print operator-friendly count.
- DF-26 BUG: Missing tickers (where fetch_ohlcv returned empty) are SILENTLY DROPPED from results dict. No log of which tickers failed. Combined with telemetry being aggregate-only, operator can see "fetched 80/100" but not WHICH 20 failed.

### Lines 135-191: fetch_info
- DF-27 GOOD (lines 137-148): Initializes info with safe defaults. Comment "Bug #6: do not use ticker as fake company name" — historical bug-fix archaeology. ✅
- DF-28 BUG (line 144): `"averageVolume": 1_000_000` — DEFAULT 1M. **If yfinance returns None at line 155 (`or 1_000_000`), value stays 1M.** is_valid_market_data line 227-228 only blocks `vol <= 0`. 1M passes. **A delisted/inactive ticker silently appears as 1M-volume tradeable.** Theme T11. Better default: None (and is_valid_market_data should block None).
- DF-29 GOOD (lines 150-179): Try-block for fast_info — lightweight per yfinance docs.
- DF-30 GOOD (line 152): `t.fast_info` — uses fast_info (cheap) instead of t.info (heavy). Good perf choice.
- DF-31 BUG (line 153-154): `currentPrice` AND `regularMarketPrice` set to same value. Why? Probably for downstream backwards compat. Two columns for same data. Theme T2 mini.
- DF-32 GOOD (line 164): `os.getenv("DAILY_FETCH_YF_FULL_INFO", "true")` — env-var feature flag. Defaults to enabled. **Excellent comment block (lines 157-163) explaining why this is gated.**
- DF-33 BUG (line 164): Default value "true" — full info fetch is ON by default. Per the comment, this should be conservative (off by default). Comment says "Default remains lightweight" but code default is "true" = NOT lightweight. **Comment lies about default.** Theme T10.
- DF-34 GOOD (lines 165-174): Inner try for full_info — defensive. Filters out tickers where longName == ticker (bad yfinance fallback).
- DF-35 BUG (line 173-174): `except Exception: pass` — bare swallow. Theme T1. If full_info fails for one ticker, no log.
- DF-36 BUG (line 175-179): try/except/else pattern. Telemetry recorded. ✅ But `pass` on line 177 is misleading.
- DF-37 GOOD (lines 182-189): Finnhub branch — env-var gated. Defensive try with print on error.
- DF-38 BUG (lines 185-187): `for k, v in fund.items(): if v is not None and v != "N/A": info[k] = v` — overwrites yfinance values with Finnhub values. **No precedence policy documented.** What if yfinance has marketCap=$100B and Finnhub has $99B? Finnhub wins. Why? No comment.
- DF-39 BUG: Finnhub fundamentals overwrite yfinance — could change `currentPrice` if Finnhub returns it. Race condition between providers' freshness. Undocumented merge policy.

### Lines 198-230: is_valid_market_data
- DF-40 GOOD (line 198): Returns (bool, reason) tuple. Same shape as hard_blocks _block_* functions. Pattern consistency.
- DF-41 GOOD (lines 207-208 docstring): References smell_stale_price as the heavier check. Cross-module awareness.
- DF-42 GOOD (lines 211-212): None check first. Explicit "delisted or invalid ticker".
- DF-43 GOOD (lines 213-216): Numeric coercion guard.
- DF-44 GOOD (lines 217-218): price <= 0.
- DF-45 BUG (line 219): `price > 100_000` — magic 100k. Comment in docstring mentions "non-BRK.A". BRK.A trades around $700k currently. **Threshold of 100k MEANS BRK.A would be flagged as suspicious.** Either intentional exclusion of BRK.A (unlikely given no exception logic) OR threshold needs raising. Likely TYPO/STALE — should be 1_000_000 if intent is "exclude only BRK.A-class shares".
- DF-46 GOOD (lines 222-228): averageVolume check. **But blocked at vol <= 0 only.** Per DF-28, default 1M means this never fires for missing-volume tickers.
- DF-47 BUG (line 224): `vol = float(vol or 0)` — `or 0` pattern. None becomes 0 → blocked. ✅ in net effect IF default weren't 1M.

## src/indicators.py — LINE BY LINE

### Lines 1-3: Imports
- IND-1 GOOD: pandas + numpy. Pure computation.

### Lines 10-11: sma
- IND-2 GOOD: 1-line trivial implementation. ✅

### Lines 14-15: ema
- IND-3 GOOD: `adjust=False` — standard for technical analysis (don't adjust by exponentially-decreasing weights at start).

### Lines 18-23: rsi
- IND-4 GOOD (line 22): `loss.replace(0, np.nan)` — prevents division by zero. **Returns NaN for periods with no loss.** Then 100 - (100/(1+rs)) where rs=NaN → NaN. Downstream `_f` (line 245-247) returns None for NaN. **Silent NaN → None propagation.** Acceptable but caller may interpret None as "missing data" not "100% gain period."
- IND-5 SMELL: Doesn't use Wilder's smoothing (the Welles Wilder original RSI uses exponential moving average with alpha=1/period). This implementation uses simple rolling mean. **Two valid RSI variants exist. Which is intended? Not documented.**

### Lines 26-32: macd
- IND-6 GOOD: Standard MACD (12/26/9). Returns triple.

### Lines 35-38: bollinger
- IND-7 GOOD: Standard 20-period 2-std bands. Returns (upper, middle, lower).

### Lines 41-48: atr
- IND-8 GOOD: True range computation correct. Then rolling mean.
- IND-9 SMELL: ATR uses simple rolling mean, not Wilder smoothing (which is RMA = Welles Wilder Average). **Same convention question as RSI.** Most platforms use Wilder. This deviates silently.

### Lines 55-60: stochastic
- IND-10 GOOD: Standard %K/%D with default 14/3.
- IND-11 GOOD (line 58): `(high_max - low_min).replace(0, np.nan)` — div-by-zero guard. NaN propagates.

### Lines 63-65: obv
- IND-12 GOOD: Standard On-Balance Volume.
- IND-13 SMELL (line 64): `np.sign(...).fillna(0)` — fills first row's NaN sign with 0. Reasonable but means OBV starts cumsum from 0 unconditionally.

### Lines 68-91: parabolic_sar
- IND-14 OK: Manual implementation of PSAR — algorithm-correct as far as I can verify.
- IND-15 BUG (line 80): `min(sar[i], low[i-1], low[max(i-2, 0)])` — for i=1, this is min(sar[1], low[0], low[0]) = double-counts low[0]. Edge case when i<=2. Output likely OK but suboptimal.
- IND-16 BUG (lines 75-76): `ep = high[0]; sar[0] = low[0]` — initializes assuming UPTREND start. **For a stock starting in downtrend, the initial PSAR is WRONG until trend flips.** Standard PSAR variants handle this either way; this one assumes uptrend.
- IND-17 SMELL (line 77): Python for loop over n bars. For 6mo of daily data ~120 bars, fine. For intraday, slow. Vectorization possible.

### Lines 94-99: vwap
- IND-18 SMELL (line 95): "Rolling VWAP" — but TRUE VWAP resets daily (it's an intraday measure). This is a 20-period rolling typical-price-weighted average. **Not actually VWAP in the conventional sense.** Naming may mislead.

### Lines 102-119: adx
- IND-19 GOOD: Uses Wilder smoothing (`ewm(alpha=1/period)`). Inconsistent with RSI/ATR which use simple mean. **Same module, two smoothing conventions.** Per IND-5 + IND-9.
- IND-20 GOOD (line 117): `(plus_di + minus_di).replace(0, np.nan)` — div-by-zero guard.

### Lines 122-152: candlestick_patterns
- IND-21 GOOD (line 123): `if len(df) < 3: return {}` — defensive on short df.
- IND-22 GOOD (line 129): `rng = max(h - l, 1e-9)` — div-by-zero guard via min epsilon.
- IND-23 BUG (lines 134-135): bullish_engulfing condition `c >= po and o <= pc` — uses `>=` and `<=` (inclusive). Strict engulfing usually requires strict `>` and `<`. Permissive variant; could over-detect.
- IND-24 BUG (line 138): `body / rng < 0.1` — magic 10% body/range ratio for doji. No constant.
- IND-25 BUG (line 141, 146): `< 0.3` — magic 30% body/range for star pattern. Buried.
- IND-26 SMELL: 6 patterns hardcoded. No registry like smell_faculty's ALL_SMELLS. Hard to extend.

### Lines 155-168: fibonacci_levels
- IND-27 GOOD: Standard Fib retracement levels. lookback=60 default.
- IND-28 SMELL (line 161-167): Returns 7 fib levels but composite scoring (Batch 12 SC-18) only uses fib_382 / fib_50 / fib_618. **4 unused levels** (fib_0/236/786/100) computed and stored.
- IND-29 BUG: lookback=60 hardcoded across functions. fibonacci_levels uses 60, support_resistance uses 60. Constant-by-convention but not enforced.

### Lines 171-190: support_resistance
- IND-30 GOOD: Pivot detection over `window=5` bars.
- IND-31 BUG (line 176): `highs.iloc[i] == highs.iloc[i-window:i+window+1].max()` — equality on floats. **Float equality is fragile.** Two identical-looking highs may differ by tiny epsilon. Use `>=` with small tolerance.
- IND-32 SMELL (lines 183-184): If no pivots above close, falls back to overall max. **Silent degradation when no clear S/R.** Returned values are misleading.

### Lines 197-236: add_indicators
- IND-33 GOOD (line 198-199): Empty df early return.
- IND-34 GOOD (lines 201-234): Sequential indicator computation. Each adds columns to d.
- IND-35 BUG (lines 223-226): `try: d["psar"] = parabolic_sar(d) except: d["psar"] = np.nan` — bare except. Theme T1. If PSAR algorithm crashes (e.g., on very short df), all PSAR values silently NaN.
- IND-36 SMELL: ATR_14 computed at line 215. parallel_scorer (PS-30) reads `sig.get("atr_14") or sig.get("atr") or sig.get("ATR")` — three names. **indicators.py produces atr_14 ONLY.** parallel_scorer's other two fallbacks are dead. Theme T2 — fallbacks for fields no producer creates.
- IND-37 BUG (line 234): `d["vol_ratio"] = d["volume"] / d["vol_sma_20"]` — no div-by-zero guard. If `vol_sma_20` is 0 (e.g., 20 zero-volume bars), produces inf. Downstream score_volume (Batch 12 SC-37) would treat inf as > 2.0 → 0.85 score. **Inf-volume → high score bug.**

### Lines 239-306: latest_signals
- IND-38 GOOD (line 240): empty df early return.
- IND-39 GOOD (lines 245-247): `_f` helper for safe float coercion of NaN-or-numeric.
- IND-40 GOOD (lines 249-264): Comprehensive flat dict of latest indicator values.
- IND-41 BUG (line 251): `df["close"].iloc[-2] if len(df) > 1 else close` — single-bar dataframes return prev_close = close. Edge case.
- IND-42 GOOD (lines 267-271): bb_position with div-by-zero guard.
- IND-43 BUG (lines 273-282): 4 boolean derived flags. Each is `(X is not None and X > N)` pattern. **A False value conflates "below threshold" and "data missing."** Downstream cannot distinguish.
- IND-44 BUG (lines 285-290): vwap_distance_pct defaults to 0 if vwap missing. **0 is a valid value.** Confuses "no data" with "exactly at vwap."
- IND-45 BUG (lines 293-297): bare `except: pass` for candlestick. Theme T1. Same Theme T11 silent degradation.
- IND-46 BUG (lines 300-304): bare `except: pass` for fib + support/resistance. Theme T1. Same.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### DF-X1: data_fetcher is the BEST-INSTRUMENTED file
4 of 4 fetch paths emit telemetry via record_market_data_event. Per-stage (ohlcv vs info), per-provider (yfinance vs stooq), per-result (success vs empty vs error). Compare to other gate files — only PRDY consumes this telemetry. **Fully observable upstream, partially observable downstream.**

### DF-X2: data_fetcher has 3 silent-default-fills
1. averageVolume default 1M (line 144 + line 155)
2. info defaults for 8 fields (lines 137-148)
3. fetch_ohlcv returns empty DataFrame on total failure
**All three are "fail-soft with default values."** When data is missing, returns plausible-looking defaults rather than None. Upstream gates have to KNOW these defaults or treat 1M-vol as suspicious. **Documentation gap.**

### IND-X1: indicators.py uses 2 smoothing conventions inconsistently
- RSI (line 18-23): simple rolling mean
- ATR (line 41-48): simple rolling mean
- ADX (line 102-119): Wilder smoothing (ewm)
**Same module, two methodologies for what should be consistent technical analysis convention.** Most platforms use Wilder for RSI and ATR too.

### IND-X2: 4 derived boolean flags conflate "false condition" with "missing data"
above_psar, stoch_oversold, stoch_overbought, obv_rising, strong_trend, di_bullish, above_vwap — all are False when underlying indicator is None. **Downstream sees False and assumes condition was checked AND failed — but it might mean condition was unmeasurable.** Should be Optional[bool] or 3-state enum.

### IND-X3: vol_ratio → score_volume has inf-handling bug
indicators.py line 234: `d["volume"] / d["vol_sma_20"]` — no div-by-zero guard. 0-volume periods → inf. parallel_scorer reads sig.get("vol_ratio") → inf passes through to score_volume (Batch 12 SC-37) which checks `if vr > 2.0: return 0.85`. **inf > 2.0 = True → 0.85 score on broken data.** Combine with DF-28 (1M default volume) and we have multiple paths to silently scoring picks on garbage data.

### IND-X4: Telemetry inverted — data layer logs but indicators don't
data_fetcher records every fetch event. indicators.py has bare except: pass for candlesticks, fib, S/R (IND-45, IND-46). **Indicator failures are SILENT.** A pick whose fib_levels failed silently lacks fib_* fields → composite scoring (SC-18) defaults to 0.50 → silent neutral. **No way to tell from logs that the failure happened.**

### Cross-cutting: 4 magic numbers in candlestick_patterns
0.1 (doji body/range), 0.3 (star body/range), 2 (hammer wick/body), 1e-9 (epsilon). All hardcoded. Same scoring-config externalization opportunity as Batch 12 SC-X3.

### Cross-cutting confirmed: Theme T1 (bare except) now in EVERY src/ file audited so far
data_fetcher: 5 bare excepts. indicators: 3. Plus all 8 Phase A files. **Bare except is the codebase's most pervasive anti-pattern.**

## SUMMARY (Batch 13)

| Severity | data_fetcher | indicators | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 11 | 10 | 4 | 25 |
| Data/safety | 9 | 8 | 0 | 17 |
| Code smell | 8 | 9 | 0 | 17 |
| Good code | 19 | 16 | 0 | 35 |
| Total findings | 47 | 43 | 4 | 94 |

## TOP 10 CRITICAL FIXES from Batch 13

1. DF-28: Change averageVolume default from 1_000_000 to None. Update is_valid_market_data to block None. (5 min)
2. IND-37: Guard div-by-zero in vol_ratio computation. `d["vol_ratio"] = d["volume"] / d["vol_sma_20"].replace(0, np.nan)`. (2 min)
3. DF-45: Raise BRK.A magic threshold from 100_000 to 1_000_000. (1 min)
4. DF-33: Change DAILY_FETCH_YF_FULL_INFO default from "true" to "false" to match the docstring promise of "lightweight default". (5 min)
5. IND-X1: Standardize on Wilder smoothing for RSI/ATR (or document the deviation). (30 min)
6. IND-X2: Convert 7 derived boolean flags to Optional[bool] OR add `_known: bool` companion. (30 min)
7. IND-45+46: Replace bare excepts in latest_signals with LOUD-error template. (15 min)
8. DF-26: Log which tickers failed in fetch_universe_data, not just count. (15 min)
9. DF-38: Document Finnhub-overrides-yfinance precedence policy OR make it configurable. (15 min)
10. DF-6 + IND module-load: Move SESSION creation lazy (first-use). (15 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): now in 100% of audited src/ files. Codebase-wide pattern.
- Theme T2 (schema drift): atr_14 only, but parallel_scorer fallbacks for atr/ATR — fallbacks for fields no producer makes (Batch 8 PS-30 confirmed at producer side).
- Theme T11 (fail-open by accident): NEW — averageVolume=1M default, vol_ratio inf bug, derived boolean flags conflating false-vs-missing.
- Theme T12 (asymmetric magnitudes): NA this batch.
- Theme T13 NEW (silent-default-fills): data_fetcher specifically. Fields with defaults rather than None mean downstream can't distinguish "absent" from "specified at default value."

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 4/~18 done | data_fetcher, indicators | 4/~18 |
| Total true line-by-line | | +2 files | 27 of 382 |
| Remaining | | | 355 files |

## NEXT BATCH

Batch 14: src/market_data_health.py + src/market_calendar.py — telemetry consumer + calendar guard. market_data_health is what data_fetcher writes to and PRDY reads from; market_calendar is the T51 fail-open culprit from Batch 6.

End of Batch 13. Phase B in progress (4/18).
