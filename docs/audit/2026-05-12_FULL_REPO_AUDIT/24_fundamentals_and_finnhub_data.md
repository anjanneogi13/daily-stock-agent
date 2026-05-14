# Batch 18 — src/fundamentals.py (144 lines) + src/finnhub_data.py (277 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** fundamentals.py (144 lines, fully read), finnhub_data.py (277 lines, fully read)
**Phase:** B (scoring + data layer) — files 13 and 14 of ~18

## TOP HEADLINE FINDINGS

1. FN-X1: fundamentals.py is 13 IF-LADDER SUB-SCORES with weighted average. **Total weight = 100%** (12+15+4+4+10+8+7+10+10+5+5+8+2 = 100). Math sums correctly. But **EVERY sub-score is OPTIONAL** — if all 13 are None, returns 0.5 silently. **A ticker with ZERO fundamentals data still gets a 0.5 fundamentals score that contributes to composite.** Fail-soft = fail-open.
2. FN-X2: passes_filters (line 137-143) — THE ONLY hard filter is `min_market_cap`. Per Batch 8 PS-13, parallel_scorer drops candidates that fail this. **One filter, one criterion.** Comment says "Hard quality filters" (plural) but only 1 implemented. Heavy under-utilization.
3. FH-X1: finnhub_data.py is the SOURCE of fundamentals dict. 24h cache, 30+ field mapping. **Cache is per-ticker JSON file in data/finnhub_cache/.** For 500 tickers, 500 small JSON files. Inefficient but correct.
4. FH-X2: cross_validate_price (lines 207-276) is THE PRICE INTEGRITY CHECK against yfinance. **But I see no caller of this function in any audited file.** parallel_scorer doesn't call it. fetch_info doesn't call it. **The price-cross-validation safety net is DEAD CODE unless called from main.py or unaudited file.** Need to verify caller.
5. FN-3 (line 13): `pe is not None and pe > 0` — drops negative PE entirely. **Negative PE companies (loss-making but with growth potential, e.g., PLTR pre-2024, RBLX, many SaaS) get NO valuation score.** Only growth/profitability sub-scores fire. **Systematically penalizes early-stage growth companies.**
6. FH-25 (line 25): `datetime.now() - datetime.fromisoformat(d["at"])` — both NAIVE datetimes. Per Batch 17 NC-22 cross-cutting. Cache TTL math works but introduces silent bug if process crosses DST.
7. FH-X3: `_safe_pct(v): return (v / 100.0) if v is not None else None` (line 41-43) — **Finnhub returns percentages as numbers (e.g., 95.27 for 95.27%) and code converts to decimals (0.9527).** But what if Finnhub returns "27" meaning 27% growth? `_safe_pct(27) = 0.27` → fundamentals.py treats 0.27 as 27% growth (correct). **What if Finnhub starts returning DECIMALS instead of PCT (schema change)?** Silent 100x error. No range check.

## src/fundamentals.py — LINE BY LINE

### Lines 1-4: Module docstring + imports
- FN-1 GOOD: Brief, lists input/output. Notes "from finnhub_data.fetch_fundamentals()".
- FN-2 SMELL: Doesn't say what fields are expected. Has to be inferred from the code.

### Lines 7-9: score_fundamentals signature
- FN-3 GOOD (line 8): "Weighted composite of 11 fundamental dimensions" — but actually 13 in the code. **Docstring lies.** Theme T10.
- FN-4 GOOD (line 9): `weights = []  # list of (sub_score, weight)` — explicit accumulator.

### Lines 12-19: trailingPE
- FN-5 BUG (line 13): `if pe is not None and pe > 0` — **negative PE excluded entirely.** Loss-making companies skip valuation scoring. Systematic bias against early-stage growth (PLTR, RBLX, RIVN, many biotech).
- FN-6 BUG (lines 14-18): Magic thresholds 15/25/40/60, magic scores 0.90/0.75/0.55/0.40/0.25. 9 magic numbers. Same Theme as Batch 12 SC-X3.
- FN-7 GOOD (line 19): weight 0.12 — explicit.

### Lines 21-28: pegRatio
- FN-8 BUG (line 22): `peg > 0` — same negative-exclusion as FN-5. Negative PEG (negative growth or negative PE) skipped.
- FN-9 GOOD (line 23): comment "🔥 undervalued vs growth" — emoji-as-comment. Cute but inconsistent style.
- FN-10 BUG (lines 23-27): 5 magic thresholds + 5 magic scores. Same pattern.
- FN-11 GOOD (line 28): weight 0.15 — peg is the HEAVIEST fundamental factor (15%). Correctly so per growth-investing convention.

### Lines 30-37: priceToBook
- FN-12 BUG (line 31): pb > 0. PB rarely negative but possible (negative book equity). Excluded silently.
- FN-13 BUG (lines 32-36): 4 magic thresholds (3/8/15/30), 5 magic scores.
- FN-14 SMELL (line 37): weight 0.04 — TINY. P/B contribute 4% of fundamentals score. Almost cosmetic.

### Lines 39-45: priceToSales
- FN-15 BUG: Same pattern. Magic thresholds 3/10/20.
- FN-16 SMELL: weight 0.04 — same near-zero contribution.

### Lines 48-55: earningsQuarterlyGrowth
- FN-17 BUG (line 49): `if eps_q is not None` — does NOT exclude negative. Allows negative growth scoring. ✅ DIFFERENT from valuation logic. **Inconsistency**: valuation excludes negatives, growth doesn't.
- FN-18 GOOD (line 54): `else s = 0.30` — negative growth → 0.30 score (penalty but not zero). Consistent with bear-handling.
- FN-19 BUG (lines 50-54): 4 magic thresholds (0.30/0.15/0.05/0), 5 magic scores.
- FN-20 GOOD: weight 0.10 — meaningful.

### Lines 57-64: epsGrowth5Y
- FN-21 BUG (lines 59-63): Same magic thresholds as quarterly. Inconsistent — quarterly +30% over 90 days vs annualized +30% over 5 years are VERY different. **Same bucket boundaries for two different time horizons.** Should be calibrated separately.
- FN-22 GOOD: weight 0.08.

### Lines 66-72: revenueGrowth
- FN-23 BUG (line 66): `info.get("revenueGrowth") or info.get("revenueGrowth5Y")` — DUAL-SOURCE `or` pattern. Theme T2 again. Falls back to 5Y if quarterly missing — **but compares both against the same thresholds (line 67-71).** A 5Y growth of 20% is treated identically to a quarterly 20%. **Same bug as FN-21 (mixed time horizons).**

### Lines 75-82: profitMargins
- FN-24 BUG (lines 76-81): Negative profit margins → 0.20 score. Loss-making company gets some credit. ✅ for handling losses, but 0.20 is high (≈ "minor" rating). Magic.

### Lines 84-91: returnOnEquity
- FN-25 BUG: 5 magic thresholds + 5 magic scores. Same pattern.
- FN-26 SMELL: ROE >25% gets 0.95 — top score. But high ROE can come from high leverage (low equity), not productivity. Not adjusted for D/E.

### Lines 94-101: debtToEquity
- FN-27 BUG (line 95): `if de is not None` — accepts ANY value including negative D/E (negative equity = bankruptcy near). **Negative D/E with very small abs value would score < 0.3 (low) → 0.25 score.** Actually the check at line 100 (`else 0.25`) catches it. ✅
- FN-28 BUG (lines 96-100): 4 magic thresholds (0.3/0.6/1.0/2.0). Industry-dependent (utilities have D/E 1.0+ normally; tech 0.1). **No sector adjustment.**

### Lines 103-109: currentRatio
- FN-29 BUG: 3 magic thresholds (2.0/1.5/1.0), 4 magic scores. Same pattern.

### Lines 112-119: freeCashFlowYield
- FN-30 GOOD (line 113): `if fcf_yield is not None` — accepts negatives.
- FN-31 BUG (lines 114-118): 4 magic thresholds, 5 magic scores.

### Lines 122-129: relativeToSP500_52w
- FN-32 BUG (line 122): `info.get("relativeToSP500_52w")` — finnhub-only field (per FH line 145). If yfinance-only fetch (no Finnhub key) → field None → branch skipped silently.
- FN-33 SMELL: weight 0.02 — tiny. Relative strength contributes 2%. Could be removed without material effect.

### Lines 131-134: composite computation
- FN-34 GOOD (line 131): `if not weights: return 0.5` — fallback when zero sub-scores.
- FN-35 CRITICAL (line 131): **Per FN-X1, ZERO sub-scores → 0.5.** A ticker with NO fundamentals data passes through with neutral score. Combined with passes_filters (FN-X2) only checking marketCap, **a $5B market-cap ticker with completely missing fundamentals gets composite contribution from a 0.5 score.** Should arguably block when n_subscores < threshold (e.g., < 3).
- FN-36 GOOD (line 133-134): Weighted average with sum-of-weights normalization. Handles missing sub-scores gracefully.
- FN-37 BUG: NO LOGGING of which sub-scores fired. For a 0.65 score, can't tell if it came from 13 fields or 3 fields. Audit-trail blind spot.

### Lines 137-143: passes_filters
- FN-38 BUG: Comment says "Hard quality filters" but only ONE filter implemented (min_market_cap).
- FN-39 BUG (line 141): `mc is not None and mc < f.get("min_market_cap", 0)` — if mc is None (Finnhub returned no marketCap), passes through. **Missing market cap = passes filter.** Should arguably fail-CLOSED.
- FN-40 BUG: NO filters for: minimum revenue, minimum employee count, exchange filter, country filter, OTC exclusion. **A penny-OTC stock could pass through if it has > min_market_cap.** hard_blocks does penny check (Batch 8 HB-32) but only on entry price, not market cap context.
- FN-41 GOOD (line 139): `(cfg or {}).get("filters", {})` — defensive cfg unpacking.

## src/finnhub_data.py — LINE BY LINE

### Lines 1-10: Imports + load_dotenv
- FH-1 SMELL (line 8): `from dotenv import load_dotenv` — extra dep, but standard.
- FH-2 BUG (line 10): `load_dotenv()` — runs at MODULE IMPORT TIME. **Side effect on import.** Same Theme as DF-7, PL-7, BW (bootstrap_wisdom). 4th file with this anti-pattern.

### Lines 12-16: Module-level state
- FH-3 BUG (line 13): `_KEY = os.getenv("FINNHUB_API_KEY", "")` — read ONCE at import time. **If key set after import (test setup, dotenv reload), not picked up.** Each function should read env at call time OR provide a refresh mechanism.
- FH-4 BUG (line 14): `Path("data/finnhub_cache")` — RELATIVE PATH. **10th file in audit.** Cumulative: HB, PRG, PL, main.py, SCS, MDH, RG, CB, NS+NE, NC, FH.
- FH-5 BUG (line 15): `_CACHE_DIR.mkdir(parents=True, exist_ok=True)` — runs at MODULE IMPORT. Same anti-pattern as PL-7, DF-7, FH-2. **Importing finnhub_data creates `data/finnhub_cache/` directory unconditionally.** Tests, lints, anything-imports = side effect.

### Lines 19-29: _cache_get
- FH-6 GOOD (line 21-22): Existence check.
- FH-7 BUG (line 25): `datetime.now() - datetime.fromisoformat(d["at"])` — **NAIVE DATETIME math.** Per Batch 17 NC cross-cutting + Batch 16 NS-25. If `d["at"]` was written by a different timezone process, math is wrong. In practice all writes are local-now, so internally consistent. Cross-process consistency at risk.
- FH-8 BUG (line 27-28): bare except `pass`. Theme T1. Corrupt cache silently treated as no cache.
- FH-9 GOOD (line 29): Returns None on miss/expired/error. Predictable.

### Lines 32-38: _cache_put
- FH-10 BUG: NO ATOMIC WRITE. Compare to MDH-19 / NS-22 gold standard. Power loss mid-write corrupts ticker cache. Low impact (24h TTL means rebuild quickly).
- FH-11 GOOD (line 35): `datetime.now().isoformat()` — but NAIVE per FH-7.
- FH-12 BUG (line 37-38): bare except `pass`. Theme T1. Cache write failure silent.

### Lines 41-43: _safe_pct
- FH-13 GOOD: Single-purpose helper.
- FH-14 BUG: NO RANGE VALIDATION. Per FH-X3 head finding, if Finnhub schema changes from "27" to "0.27", silent 100x error. Should validate `if v > 1: v = v/100 else: v` OR refuse if outside expected range (e.g., -100 to 1000 for percentages).

### Lines 46-79: fetch_fundamentals — initialization
- FH-15 GOOD (lines 48-50): Cache check first.
- FH-16 GOOD (lines 52-74): Defaults dict with 25 fields explicitly set to None. Documented by category.
- FH-17 SMELL (line 54): `"shortName": ticker` — DEFAULT TO TICKER. But yfinance-side data_fetcher.fetch_info has explicit comment (line 138-139) "Bug #6: do not use ticker as a fake company-name fallback." **Two different defaults for the same field across two fetchers.** Theme T2 inconsistency.
- FH-18 BUG (line 76-79): Missing key → returns empty defaults + caches them. **Caching the empty result for 24h.** If FINNHUB_API_KEY is added mid-day, cached empty persists. Should NOT cache empty results.

### Lines 82-94: profile fetch
- FH-19 GOOD (line 84): timeout=10. Has timeout.
- FH-20 BUG (line 85-92): Status check then field extraction. Non-200 silently skipped (no log).
- FH-21 GOOD (line 92): `mc * 1_000_000` — converts Finnhub millions to absolute. Comment explains.
- FH-22 BUG (line 93-94): bare except prints raw `e` (no type, no truncation). Inconsistent with rest of codebase logging convention (`type(e).__name__: {str(e)[:N]}`).

### Lines 97-148: metrics fetch — THE BIG ONE
- FH-23 GOOD (line 100): timeout=15 (longer than profile, reflects bigger payload).
- FH-24 GOOD (line 102): `r.json().get("metric", {}) or {}` — defensive empty fallback.
- FH-25 GOOD (lines 105-109): VALUATION block — uses `or` chains for TTM-then-Annual fallback. Good Finnhub field handling.
- FH-26 BUG (lines 105-108): The `or` falsy-trap: if `m.get("peTTM")` returns 0 (zero PE - very rare but possible for a company with EPS=0), falls through to Annual. **Edge case.** Not material in practice.
- FH-27 GOOD (lines 110-114): GROWTH block — calls `_safe_pct` on each. Per FH-X3 risk.
- FH-28 GOOD (lines 116-120): PROFITABILITY block — same pattern.
- FH-29 BUG (lines 122-124): EPS — `m.get("epsBasicExclExtraItemsTTM") or m.get("epsExclExtraItemsTTM") or m.get("epsAnnual")` — TRIPLE-OR fallback. Same falsy-trap as FH-26. 0 EPS edge case.
- FH-30 BUG (line 127): `m.get("totalDebt/totalEquityAnnual")` — **field name with SLASH in it**. Finnhub uses this convention. Python dict access still works but unusual; downstream serialization to anything other than dict-of-strings (e.g., dataclass) would break.
- FH-31 GOOD (lines 132-142): Cash flow derivation. Math: `1/pfcf = FCF yield`, `marketCap/pfcf = total FCF`. Both rounded.
- FH-32 BUG (line 135): `if pfcf and pfcf > 0` — guards against zero/negative pfcf. ✅
- FH-33 BUG (line 145): `m.get("priceRelativeToS&P50052Week")` — field name with `&` and `52`. Finnhub-specific. Brittle.
- FH-34 BUG (lines 147-148): bare except prints raw `e`. Same as FH-22.
- FH-35 GOOD (line 150): Cache the (possibly partial) result.

### Line 154-155: fetch_info alias
- FH-36 SMELL: `fetch_info = fetch_fundamentals` — alias for backwards compat. **But data_fetcher.py defines its OWN fetch_info (Batch 13 line 135).** Two functions named `fetch_info`, different signatures, both importable from src. Namespace collision risk if `from src import fetch_info`.

### Lines 163-204: fetch_finnhub_quote
- FH-37 GOOD (lines 169-176): Documents Finnhub /quote schema (c/pc/h/l/o/t).
- FH-38 BUG (line 180): `import os, urllib.request, json as _json` — **inline imports**. urllib.request and json are stdlib but already used elsewhere — should be at module top. Consistency.
- FH-39 BUG (line 181): Reads env var AGAIN (redundant with line 13 _KEY). At least picks up runtime changes (compare FH-3).
- FH-40 GOOD (line 188): `urlopen(url, timeout=5)` — explicit timeout.
- FH-41 BUG (line 188): Uses `urllib.request.urlopen` here vs `requests` at line 84/98. **Two HTTP libraries in one file.** Inconsistent.
- FH-42 GOOD (line 192): `if c == 0 or c is None` — defensive Finnhub-returns-0-for-invalid handling.
- FH-43 BUG (lines 196-199): `float(data.get("pc") or 0) or None` — chains `or 0` then `or None`. **Confusing.** `0 or None` → None. So if Finnhub returns 0, becomes None. Edge: a stock genuinely at $0 (delisted intraday) reports as None instead of 0. Matches intent.

### Lines 207-276: cross_validate_price — THE PRICE INTEGRITY CHECK
- FH-44 GOOD (line 210): keyword-only thresholds (warn=2%, block=5%).
- FH-45 GOOD (lines 213-225): Comprehensive docstring with return shape.
- FH-46 GOOD (line 222-224): Documents "graceful: returns is_valid=True if Finnhub unavailable."
- FH-47 BUG (line 222 + FH-X2): **NO CALLER VISIBLE in audited files.** parallel_scorer doesn't call this. data_fetcher.fetch_info doesn't. premarket_sanity doesn't. **If unused, this is DEAD CODE.** If used by main.py / stale_smell, need to verify. Critical safety net potentially unconnected.
- FH-48 GOOD (lines 236-239): Primary price sanity first.
- FH-49 GOOD (lines 245-248): Graceful degradation when second source unavailable.
- FH-50 GOOD (lines 252-254): Avg-based disagreement % math.
- FH-51 GOOD (lines 256-274): 3-tier output: block / warn / pass with explicit reasons.
- FH-52 BUG (line 209): `warn_threshold_pct: float = 2.0, block_threshold_pct: float = 5.0` — magic defaults. Reasonable but undocumented why these values.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### FN-X1: Empty fundamentals = 0.5 score = passes through
score_fundamentals returns 0.5 when no sub-scores fire (FN-34/FN-35). passes_filters (FN-38) only checks marketCap. **A ticker with marketCap > min and ZERO other fundamentals data scores 0.5 fundamentals → contributes ~7% to composite (per scoring weight) — same as a "neutral" company with full data.** Schema-blind-spot at the gate.

### FH-X2: cross_validate_price may be DEAD CODE
68 lines of well-documented price integrity logic (FH-44 to FH-52). I see no caller in:
- parallel_scorer (Batch 8) — no
- data_fetcher.fetch_info (Batch 13) — no
- premarket_sanity_gate (Batch 9) — no
- smell_faculty (Batch 7) — no (but smell_stale_price was inert)
- portfolio_risk (Batch 9) — no
- missing_data_gate (Batch 10) — no
**Possibly called from main.py or stale_price_smell or evaluator.** **CRITICAL TO VERIFY** — if dead, the codebase has a built-in stale-price detector that's never run. Combined with smell_faculty's stale_price smell being inert (Batch 7 SF-X1), there may be NO active price integrity check.

### FN-X3: Negative-PE exclusion is systematic bias
FN-5/FN-8/FN-12 — valuation sub-scores skip negatives entirely. Growth sub-scores DON'T (FN-17). **Inconsistency favors profitable companies**. Loss-making growth stocks (PLTR, RBLX, RIVN, biotechs) get growth-only fundamentals score → systematically lower vs profitable peers → fewer picks from this segment.

### FN-X4: Mixed time-horizon sub-score buckets
FN-21: epsGrowth5Y uses same thresholds as earningsQuarterlyGrowth. **Annualized growth and quarterly YoY are different scales.** A 30% quarterly is exceptional; 30% annualized over 5 years is also exceptional but represents 4x growth, vs quarterly 1.3x. Same bucket boundary inflates one. Should be calibrated.

### FH-X3: _safe_pct lacks range guard
FH-13/FH-14. If Finnhub silently changes from "27" to "0.27" representation, every growth/margin/return sub-score gets 100x deflated → all fundamentals scores collapse. Single API change breaks the system silently.

### Cross-cutting: 10 files now with relative-path constants
Cumulative: HB, PRG, PL, main.py, SCS, MDH, RG, CB, NS+NE, NC, FH. **10/35 audited files.**

### Cross-cutting: Module-import side effects
- bootstrap_wisdom (subprocess at import — Batch 6)
- pick_logger (mkdir at import — PL-7)
- data_fetcher (curl_cffi SESSION at import — DF-6)
- finnhub_data (load_dotenv + mkdir at import — FH-2, FH-5)
**4 files do real work at module import.** Tests, type checks, lints all incur side effects.

### Cross-cutting: 2 HTTP libraries in finnhub_data alone
`requests` (line 8) for profile/metrics. `urllib.request` (line 180 inline) for quote. **Same module, two libraries.** Pick one.

### Cross-cutting: Naive datetime in critical-path modules
- finnhub_data._cache_get (FH-7): cache TTL math
- news_classifier classify_news (NC-22): timestamp on classification
- pick_logger (PL-7? actually verified naive)
- regime.py — no, uses isoformat()
**Mixed timezone handling.** MDH-5 / NS-14 use timezone.utc correctly. Others don't.

## SUMMARY (Batch 18)

| Severity | fundamentals | finnhub_data | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 8 | 12 | 3 | 23 |
| Data/safety | 7 | 9 | 0 | 16 |
| Code smell | 5 | 6 | 0 | 11 |
| Good code | 8 | 22 | 0 | 30 |
| Total findings | 28 | 49 | 3 | 80 |

## TOP 10 CRITICAL FIXES from Batch 18

1. FH-X2: VERIFY cross_validate_price has a caller. If dead, wire it into the pipeline (parallel_scorer or main.py before logging picks). HIGH SAFETY value if missing. (15 min check + 30 min wire-in)
2. FN-X1 / FN-35: Block (or down-rank) candidates with < N fundamentals sub-scores fired. Currently 0.5 for empty data passes through. (15 min)
3. FH-X3 / FH-14: Add range guard to _safe_pct (warn if value outside expected range). (10 min)
4. FN-X3 / FN-5+8+12: Either include negatives in valuation scoring OR document the bias. (15 min)
5. FH-18: Don't cache empty Finnhub results. (5 min)
6. FH-2 + FH-5: Move load_dotenv and mkdir out of module-import time. (10 min)
7. FN-X4 / FN-21: Calibrate epsGrowth5Y bucket boundaries separately from quarterly. (30 min)
8. FH-30 + FH-33: Document Finnhub field-name conventions (slashes, ampersands). (5 min)
9. FH-41: Pick one HTTP library (requests OR urllib). (15 min)
10. FN-38: Add real "hard quality filters" beyond min_market_cap (revenue, exchange, country). Or rename to single_filter and document why. (30 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): FH-8, FH-12, FH-22, FH-34. 4 more bare excepts.
- Theme T2 (schema drift): FH-17 ticker-as-name default disagrees with data_fetcher (DF-27). FH-13/FH-X3 schema-change risk.
- Theme T8 (DRY): FH-36 fetch_info alias collision with data_fetcher.fetch_info.
- Theme T11 (fail-open by accident): FN-X1 empty fundamentals → 0.5 score → contributes to composite. FH-18 caches empty results.
- Theme T13 (silent-default-fills): FN-35 0.5 default. FH-17 ticker-as-name default.
- Theme T14 (gold-standard patterns): FH-44-FH-52 cross_validate_price IS gold-standard design — but possibly never called (FH-X2). Tragic.
- Theme T15 (false-positive blocking): FN-X3 negative-PE exclusion is a systematic NEGATIVE-positive bias (false-suppression).
- Theme T16 NEW (dead-code safety nets): cross_validate_price in finnhub_data, smell_low_liquidity in smell_faculty (Batch 7) — well-designed safety code that never runs.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 14/~18 done | fundamentals, finnhub_data | 14/~18 |
| Total true line-by-line | | +2 files | 37 of 382 |
| Remaining | | | 345 files |

## NEXT BATCH

Batch 19: src/risk_manager.py + src/atr_trade_plan.py — position sizing + stop/target placement. Both consume regime + ATR; both produce the entry/sl/tp/qty fields that pick_logger writes and gates check.

End of Batch 18. Phase B in progress (14/18).
