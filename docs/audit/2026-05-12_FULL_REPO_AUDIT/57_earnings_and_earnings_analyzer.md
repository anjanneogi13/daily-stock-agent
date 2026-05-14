# Batch 51 — src/earnings.py (170 lines) + src/earnings_analyzer.py (215 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** earnings.py (170 lines), earnings_analyzer.py (215 lines)
**Phase:** E (subdirectory & ancillary). Files 21 and 22 of ~50.

## TOP HEADLINE FINDINGS

1. EA-X1: earnings.py is **THE DAYS-TO-EARNINGS CALCULATOR** — produces the integer used by parallel_scorer (B44 PS-27), probability_engine (B43 PE3-22), agent_memoir (B47 AM-20), and Batch 37 OPA-29. **THE central earnings-proximity signal.** **PURE FETCH + PARSE + DELTA.** Defaults to 999 (fail-OPEN sentinel).
2. EA-X2 (lines 17-95): **3-LAYER DEFENSIVE PARSER** for yfinance calendar shape variation (`_first_non_empty` + `_extract_earnings_date` + `_to_date`). Per docstring line 145-148: "yfinance has changed calendar shapes over time. This parser accepts dict and DataFrame-like shapes so earnings-risk filtering does not silently go blind when the upstream object format changes." **GOLD-STANDARD documented schema-drift defense.** Per Batch 36 PF-7 + Batch 42 cross-cutting Theme T2 schema-chaos.
3. EA-X3 (line 14, line 144, line 159, line 164): `UNKNOWN_EARNINGS_DAYS = 999` — **FAIL-OPEN SENTINEL** for unknown earnings. **Per Batch 44 PS-27** parallel_scorer normalizes `999 → None` consciously. **Documented producer/consumer contract.** ✅ But **fail-OPEN** — a yfinance outage = 999 = "no earnings" = pick proceeds. Operator may unknowingly hold over earnings.
4. EZ-X1: earnings_analyzer.py is **THE FUNDAMENTALS-DEEP-ANALYSIS LAYER** — fetches Finnhub earnings history + analyst recommendations, computes 5-component composite earnings_quality score (0-1). **Per Batch 42 DF-X4 cross-cutting**, ANOTHER Finnhub consumer beyond data_fetcher. **2 modules with Finnhub dependency** → **HIGH-VALUE shared module candidate.**
5. EZ-X2 (lines 11, 16): **MODULE-IMPORT SIDE EFFECTS** — `load_dotenv()` at line 11 + `_CACHE_DIR.mkdir()` at line 16. Per Batch 39 MN-X3 / Batch 40 UN-3 / Batch 49 WB-X2 cross-cutting, **5th and 6th instance** of import-time side effects. Test isolation broken twice in one module.
6. EZ-X3 (lines 159-198): **5-COMPONENT WEIGHTED SCORING** with 23 magic threshold-bucket numbers (3 ladders of 5 + 1 ladder of 4 + 1 explicit 3-value mapping). Per Batch 43 SC-X2 cross-cutting magic-number proliferation. **2nd-highest magic-number density in audit** (after scorer.py B43 with ~40).
7. EZ-X4 (line 22): `_cached_get` cache-hit check uses `datetime.now().timestamp() - p.stat().st_mtime < TTL.total_seconds()`. **NAIVE comparison** (timestamp vs file mtime — both Unix epoch, so safe). **Per Batch 49 LG-X4 cross-cutting** TZ-naive theme — **first NON-issue use** of naive datetime in audit (Unix epoch comparison is TZ-agnostic). ✅

## src/earnings.py — LINE BY LINE

### Lines 1-3: Module docstring + imports
- EA-1 GOOD: 1-line docstring documents purpose + WHY (gap risk).
- EA-2 BUG: 1-line undersells — schema-drift defense (EA-X2) deserves headline.

### Lines 4-11: Imports + SESSION setup
- EA-3 GOOD (lines 7-11): try/except curl_cffi fallback to None. **Same pattern as Batch 42 DF-5.** Producer/consumer aligned.
- EA-4 BUG (line 10): bare except. Per cross-cutting Theme T1.

### Line 14: Constants
- EA-5 GOOD: Per EA-X3, named UNKNOWN_EARNINGS_DAYS = 999 sentinel.
- EA-6 BUG: Magic 999 — should document "fail-OPEN: unknown ⇒ assume safe (no near earnings)."

### Lines 17-55: _first_non_empty
- EA-7 GOOD (lines 18-25): 8-line docstring with 4 example shapes.
- EA-8 GOOD (lines 26-27): None passthrough.
- EA-9 GOOD (lines 30-36): pandas .iloc unwrap with try/except. Defensive against length-0 series.
- EA-10 BUG (line 35): bare except pass. Theme T1 second instance in this file.
- EA-11 GOOD (lines 39-40): String passthrough — "iterable but scalar" trap avoided.
- EA-12 GOOD (lines 43-44): datetime/date passthrough.
- EA-13 GOOD (lines 46-53): Generic iterable handling with recursion + empty guard.
- EA-14 BUG (line 49): bare except. Third instance.

### Lines 58-95: _extract_earnings_date
- EA-15 GOOD: Per EA-X2, **3 yfinance shape branches with example structures inline.**
- EA-16 GOOD (line 60-61): None passthrough.
- EA-17 GOOD (lines 64-69): pandas DataFrame `.empty` check first.
- EA-18 BUG (line 68): bare except. Fourth instance.
- EA-19 GOOD (lines 72-73): Shape 1: dict.
- EA-20 GOOD (lines 78-83): Shape 2: DataFrame with column.
- EA-21 BUG (line 82): bare except. Fifth instance.
- EA-22 GOOD (lines 88-93): Shape 3: DataFrame with index.
- EA-23 BUG (line 92): bare except. Sixth instance.

### Lines 98-123: _to_date
- EA-24 GOOD (line 99): Docstring documents "or None if unknown."
- EA-25 GOOD (line 100): Pre-unwraps with _first_non_empty.
- EA-26 GOOD (lines 104-105): datetime → date.
- EA-27 GOOD (lines 108-112): pandas Timestamp `.date()` with try/except.
- EA-28 BUG (line 111): bare except. Seventh instance.
- EA-29 GOOD (line 114-115): date passthrough.
- EA-30 GOOD (lines 117-121): ISO string parse with scoped ValueError.
- EA-31 GOOD (line 120): Scoped ValueError. ✅ NOT bare-except.

### Lines 126-140: _as_of_date
- EA-32 GOOD (lines 126-131): 6-line docstring documenting historical-backfill use case.
- EA-33 GOOD: 4-tier dispatch (None / datetime / date / str) + TypeError on unknown.
- EA-34 BUG (line 133): NAIVE `datetime.now().date()`. Per Batch 49 LG-X4 cross-cutting. **Per cross-cutting** acceptable for date-only comparison since calendar dates are TZ-naive.
- EA-35 GOOD (line 140): TypeError raised explicitly on unknown type. **Loud-fail** vs default None. ✅

### Lines 143-164: days_to_earnings (MAIN PUBLIC API)
- EA-36 GOOD (lines 143-154): 12-line docstring documenting yfinance schema-drift defense + as_of parameter.
- EA-37 GOOD (line 156): SESSION-aware yfinance instantiation.
- EA-38 GOOD (line 157): Pipeline composition `_to_date(_extract_earnings_date(t.calendar))`.
- EA-39 GOOD (lines 158-159): None earnings → 999 fail-OPEN sentinel.
- EA-40 GOOD (line 161): Subtraction returns timedelta, `.days` extracts int.
- EA-41 GOOD (line 162): `max(delta, 0)` floors at 0 — prevents negative days when earnings just past.
- EA-42 BUG (line 163): bare except return 999. **Eighth bare-except in file.** Documented intent ("999 if unknown") but unscoped. **A network failure = 999 = pick proceeds = OPERATOR HOLDS THROUGH EARNINGS.** Per EA-X3 fail-OPEN risk.

### Lines 167-169: earnings_safe
- EA-43 GOOD: 1-line min_days check wrapper.
- EA-44 BUG (line 167): Magic min_days=5 default. Per Batch 31 HH-X3.

## src/earnings_analyzer.py — LINE BY LINE

### Lines 1-2: Module docstring
- EZ-1 GOOD: 2-line docstring.
- EZ-2 BUG: Undersells — 5-component composite scoring, Finnhub dependency, cache layer all undocumented.

### Lines 3-9: Imports
- EZ-3 BUG (line 5): `import requests` — synchronous HTTP. Per Batch 39 MN-X3 cross-cutting, no timeout default — has explicit timeout=15 below (line 46) ✅.
- EZ-4 BUG (line 9): dotenv at module level.

### Lines 11-17: load_dotenv + cache setup
- EZ-5 BUG (line 11): Per EZ-X2, **load_dotenv() at module top.** Test pollution.
- EZ-6 BUG (line 14): `_KEY = os.getenv("FINNHUB_API_KEY", "")` at MODULE LOAD time. **Frozen at import.** Per Batch 39 MN-X3 cross-cutting.
- EZ-7 BUG (line 16): Per EZ-X2, **mkdir at import.** Same anti-pattern as Batch 49 WB-X2.
- EZ-8 GOOD (line 17): Named TTL constant.

### Lines 20-27: _cached_get
- EZ-9 GOOD (line 22): TTL check before read.
- EZ-10 BUG (line 22): Per EZ-X4, NAIVE timestamp — but Unix epoch comparison so safe.
- EZ-11 GOOD (line 23-26): try/except + None fallback.
- EZ-12 BUG (line 25): bare except pass. Theme T1.

### Lines 30-34: _cache_put
- EZ-13 BUG: NO atomic write. Per Batch 49 WB-32 cross-cutting. **Per atomic-write tally now 24 audited writers, still ~83% UNSAFE.**
- EZ-14 BUG (line 33): bare except pass.

### Lines 37-54: fetch_earnings_history
- EZ-15 GOOD (lines 39-41): Cache-first read.
- EZ-16 GOOD (lines 42-43): Empty-key short-circuit.
- EZ-17 GOOD (lines 45-46): Explicit timeout=15 ✅.
- EZ-18 GOOD (line 47-48): HTTP status check.
- EZ-19 GOOD (line 49): `r.json() or []` defensive.
- EZ-20 BUG (line 52-54): bare except + print. Theme T1.

### Lines 57-74: fetch_recommendations
- EZ-21 GOOD: Mirror of fetch_earnings_history — symmetric API.
- EZ-22 BUG (line 72-74): bare except + print. Theme T1.

### Lines 77-204: analyze_earnings
- EZ-23 GOOD (lines 79-91): 13-key out dict initialized with sensible defaults (None for missing data, 0.5 for earnings_quality neutral).
- EZ-24 GOOD (line 80): `"earnings_quality": 0.5` neutral default — caller can distinguish "no data" via None of other fields.
- EZ-25 GOOD (lines 97-99): Filter to rows with both actual and estimate.
- EZ-26 GOOD (line 102): beat = actual > estimate (correct semantics).
- EZ-27 GOOD (lines 105-110): Surprise % computation with abs() denominator (handles negative estimates).
- EZ-28 GOOD (line 107): `if e["estimate"] != 0` — div-by-zero guard.
- EZ-29 GOOD (lines 113-118): Latest quarter extraction.
- EZ-30 GOOD (lines 121-125): YoY momentum requires ≥5 quarters. **Statistical-validity floor.** Per cross-cutting min-sample discipline.
- EZ-31 GOOD (line 123): `older["actual"] != 0` — div-by-zero guard.
- EZ-32 GOOD (lines 128-154): Analyst recommendations with 3-tier trend (improving/stable/deteriorating).
- EZ-33 GOOD (lines 130-137): Total + buys count with safe defaults.
- EZ-34 GOOD (lines 139-154): Trend analysis requires ≥3 months data.
- EZ-35 BUG (lines 149, 151): Magic ±5 percentage-point thresholds for trend classification. Per Batch 31 HH-X3.
- EZ-36 GOOD: Per EZ-X3, 5-component weighted scoring at lines 159-198.
- EZ-37 BUG (lines 161-198): 23 magic threshold-bucket numbers. **Per scorer SC-X2 cross-cutting** — scorer ~40, here 23, pattern detectors ~70 cumulative. **Scoring-layer total magic-number tally rising fast.**
- EZ-38 GOOD (lines 159-166): Beat-rate 5-tier with explicit 35% weight comment.
- EZ-39 GOOD (lines 169-175): Avg-surprise 5-tier (-5 to ≥10) with 20% weight.
- EZ-40 GOOD (lines 178-184): EPS YoY momentum 5-tier with 20% weight.
- EZ-41 GOOD (lines 187-193): Analyst-buy 5-tier with 15% weight.
- EZ-42 GOOD (lines 196-198): Rec-trend explicit 3-value mapping with 10% weight.
- EZ-43 GOOD (lines 200-202): **Composite normalized by `total_w`** — handles missing components correctly (if only 3 of 5 components present, weight sums to less than 1.0 but normalized).
- EZ-44 GOOD: Composite weights sum to 35+20+20+15+10 = 100. ✅

### Lines 207-214: __main__
- EZ-45 GOOD: 4-ticker default smoke test (NVDA, AVGO, TSM, AMD).
- EZ-46 GOOD: Per Batch 41 WM-44 / Batch 49 WH-46 cross-cutting __main__ pattern. **Now 7 modules with operator-runnable __main__.**

## CONSOLIDATED CROSS-CUTTING FINDINGS

### EA-X3 + Batch 43 PE3 + Batch 44 PS cross-cutting CONFIRMED earnings producer/consumer
**Earnings sentinel chain:**
- earnings.py (this batch) WRITES `999` for unknown
- parallel_scorer (B44 PS-27) NORMALIZES `999 → None`
- probability_engine (B43 PE3-22) CONSUMES None as "far" bucket
- agent_memoir (B47 AM-20) CONSUMES days_to_earnings ≤7 in narrative

**4-module chain.** Producer/consumer contract via 999 sentinel = **DOCUMENTED** in earnings.py docstring + PS comment + AM check. **Excellent contract clarity.** ✅

### EA-X2 + Batch 36 PF-7 + Batch 42 DF cross-cutting CONFIRMED schema-drift defense pattern
**Modules with explicit yfinance / upstream schema-drift defense:**
- premarket_filter (B36 PF-7) — yfinance prepost defense
- data_fetcher (B42 DF-9) — MultiIndex flatten
- earnings (this batch EA-X2) — 3-shape calendar parser

**3 modules with documented schema-drift defense.** **Pattern is mature.** earnings.py is the gold-standard with explicit shape examples in inline comments.

### EZ-X2 + Cross-cutting import-time side-effect tally
Modules with import-time side effects:
- market_news (B39 MN-X3) — load_dotenv + _KEY freeze
- universe (B40 UN-3) — SESSION init
- wisdom_base (B49 WB-X2) — ROOT.mkdir
- earnings_analyzer (this batch EZ-X2) — load_dotenv + mkdir + _KEY freeze

**6 instances across 4 modules.** **Test-isolation theme.**

### EZ-X3 + scorer cross-cutting magic-number proliferation
**Magic-number tally (scoring-layer):**
| Module | Magic threshold count |
|---|---:|
| scorer.py (B43 SC-X2) | ~40 |
| earnings_analyzer (this batch EZ-X3) | 23 |
| pattern detectors (B30-33 HH-X3 cumulative) | ~70 |
| **Total** | **~133** |

**133 magic threshold-bucket numbers across scoring layer with ZERO calibration archaeology.** Per Batch 31 HH-X3. Single biggest "tech-debt comment opportunity" in audit.

### EA-42 + cross-cutting fail-OPEN sentinel
- earnings.py 999 → fail-OPEN (network failure = pick proceeds through earnings)
- Batch 36 PF (premarket_filter) — fail-OPEN
- Batch 40 MG (market_guard) — fail-OPEN
- Batch 46 PG-22 — hidden fail-OPEN inside fail-CLOSED gate

**4 audited fail-OPEN points.** earnings.py is **higher impact** than the others — operator could unknowingly hold through earnings = blowup risk. **Should add MDH event when 999 sentinel returned** so operator sees count of "earnings-blind" picks per run.

### Cross-cutting: bare-except this batch
- earnings: 8 (EA-4, EA-10, EA-14, EA-18, EA-21, EA-23, EA-28, EA-42) — all schema-drift defense
- earnings_analyzer: 4 (EZ-12, EZ-14, EZ-20, EZ-22) — all network/cache defense

**12 bare-excepts in 2 files. Per Batch 44 PS / Batch 49 wisdom-layer concentration**, this is the new HIGH-WATERMARK file pair for bare-excepts. Fundamentals-layer is bare-except-heavy by design (graceful degradation under provider failure).

### Cross-cutting: relative-path constants
earnings_analyzer adds _CACHE_DIR. **37 files now.** earnings adds nothing (no path constants).

### Cross-cutting: TZ-aware modules: 8 (no addition; earnings consciously uses date-only naive comparison).

### Cross-cutting: bug-archaeology gold standard: 8 modules (no addition).

### Cross-cutting: ATOMIC WRITE
- earnings: N/A (read-only)
- earnings_analyzer: 1 unsafe writer (_cache_put). **24th audited unsafe writer.** ~83% UNSAFE.

### Cross-cutting: __main__ pattern: 7 modules now (earnings_analyzer adds).

## SUMMARY (Batch 51)

| Severity | earnings | earnings_analyzer | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 8 | 5 | 5 | 18 |
| Data/safety | 3 | 4 | 0 | 7 |
| Code smell | 2 | 1 | 0 | 3 |
| Good code | 31 | 35 | 0 | 66 |
| Total findings | 44 | 45 | 5 | 94 |

## TOP 10 CRITICAL FIXES from Batch 51

1. **EA-42 / EA-X3 (HIGH):** Add MDH event recording when days_to_earnings returns 999. Operator must see count of "earnings-blind" picks per run. **Earnings-blindness is highest-impact silent failure in audit.** (10 min)
2. **EZ-X3 + scorer SC-X2 cross-cutting (MEDIUM):** Add provenance comments for 23 earnings-quality threshold-buckets. Cite source (Bloomberg/Refinitiv beat-rate norms?). (30 min)
3. **EZ-X2 / EZ-5 + EZ-7 (MEDIUM):** Move load_dotenv() and mkdir() into lazy init function. Test isolation. Per cross-cutting 4-module pattern. (10 min)
4. EA-1: Expand earnings.py docstring — surface schema-drift defense + 999-sentinel contract. (5 min)
5. EZ-1: Expand earnings_analyzer.py docstring — surface 5-component scoring + Finnhub dependency. (5 min)
6. EA-43 / EA-44: Lift magic 5 days `min_days` to MIN_SAFE_EARNINGS_DAYS const + earnings archaeology. (3 min)
7. EZ-13: Add atomic write to _cache_put. (5 min — bundled with prior atomic-write refactors)
8. EA-4, EA-10, EA-14, EA-18, EA-21, EA-23, EA-28: Replace 7 bare-excepts with scoped (TypeError, AttributeError) — preserves intent without masking real bugs. (15 min)
9. EZ-35: Lift magic ±5 trend thresholds to const REC_TREND_THRESHOLD_PCT. (3 min)
10. EZ-3 cross-cutting: Verify earnings_analyzer Finnhub usage matches data_fetcher (B42 DF-X4) Finnhub usage — possible consolidation into shared `finnhub_client.py`. (15 min investigation)

## NEW THEMES UPDATED

- **Theme T1 (bare except):** earnings 8 (schema-drift defense). earnings_analyzer 4 (network/cache defense). **12 bare-excepts in 2 files = NEW high-watermark for the audit.**
- **Theme T2 (schema drift):** EA-X2 yfinance calendar shape variation = gold-standard documented defense. EZ-37 magic-number proliferation continues.
- **Theme T6 (atomic writes):** EZ-13 _cache_put adds 24th unsafe writer. **Atomic-write tally: 4 safe / 20 unsafe / 24 total = ~83% UNSAFE.**
- **Theme T8 (DRY):** EA-X1 earnings consumer chain (4 modules) needs `_NORMALIZE_999_TO_NONE` helper to centralize sentinel handling.
- **Theme T11 (fail-open by accident):** EA-42 + EA-X3 999-sentinel fail-OPEN = highest-impact silent failure in audit.
- **Theme T13 (silent-default-fills):** EZ-24 `earnings_quality": 0.5` neutral default. EZ-23 None defaults for unknown.
- **Theme T14 (gold-standard patterns):** earnings.py EA-X2 3-shape parser with inline shape examples + EA-X3 documented producer/consumer sentinel contract. earnings_analyzer EZ-43 weighted-composite normalization for missing components + EZ-30 5-quarter min-sample for YoY momentum.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A | 8/8 COMPLETE | (none) | 8/8 |
| Phase B | 18/18 COMPLETE | (none) | 18/18 |
| Phase C | 12/12 COMPLETE | (none) | 12/12 |
| Phase D | 30/~30 COMPLETE | (none) | 30/~30 |
| Phase E | 22/~50 done | earnings, earnings_analyzer | 22/~50 |
| Total true line-by-line | | +2 files | **105 of ~382 (~27.5%)** |
| Remaining | | | **~277 files** |

## NEXT BATCH

Batch 52 (doc #58): Continue Phase E. Two strong candidates from news layer (consumed by parallel_scorer + watchlist_manager):
- **`src/news_classifier.py` (5.4KB)** — produces classification consumed by watchlist_manager (B41 WM-X1).
- **`src/news_engine.py` (6.1KB)** — orchestrates news pipeline.

End of Batch 51. Phase E in progress (22/50). **27.5% audit milestone.**
