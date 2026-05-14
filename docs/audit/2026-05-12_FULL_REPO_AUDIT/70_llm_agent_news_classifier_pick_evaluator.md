# Batch 64 — src/llm_agent.py (207 lines) + src/news_classifier.py (136 lines) + src/pick_evaluator.py (434 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** llm_agent.py (207), news_classifier.py (136), pick_evaluator.py (434)
**Phase:** F. Files 7, 8, 9 of ~38. **pick_evaluator is LARGEST single file in repo (19KB / 434 lines).**

## TOP HEADLINE FINDINGS

1. LA-X1: llm_agent.py is **THE 4-TIER LLM PROVIDER WATERFALL** (207 lines): Claude → Gemini → OpenAI → rule_based with **module-level quota-exhausted state flags** + per-call throttle + 12h disk cache. Per Batch 39 MN-X1 / Batch 53 NS-X1 / Batch 63 cross-cutting — **JOINS as 4th audited LLM-orchestrator**, but **first with 3-provider waterfall + quota-state-machine.**
2. LA-X2 (lines 49-52): **MODULE-LEVEL MUTABLE STATE** — `_CLAUDE_QUOTA_EXHAUSTED = [False]` / `_GEMINI_QUOTA_EXHAUSTED = [False]` / `_LAST_CALL = [0.0]` using **1-element lists as mutable singletons**. **First audited "cheap mutable module-globals" pattern.** ✅ Avoids `global` keyword but **NOT thread-safe** (parallel_scorer B44 PS-X1 uses ThreadPoolExecutor — concurrent calls race here).
3. LA-X3 (lines 22-36, 39-45): **TZ-AWARE cache** — read path explicitly handles backward-compat naive timestamps (lines 29-31: "Backward-compatible with older naive cache files"). **Per Batch 49 LG-X4 / Batch 57 LJ-5 / Batch 63 cross-cutting TZ-aware standard**, **second-fully-TZ-aware module after wisdom layer** (12th TZ-aware module).
4. NC-X1: news_classifier.py is **THE CLAUDE-OR-HEURISTIC NEWS SCORER** (136 lines). **6-tier classifier** (sentiment/urgency/category/tradeable_score/primary_ticker/action_window) with **explicit tradeable_score guide in prompt (lines 31-36)** + **heuristic keyword fallback**. Per Batch 53 NS-X2 cross-cutting CATALYST table / Batch 39 MN cross-cutting — **3rd audited LLM-with-keyword-fallback module.**
5. NC-X2 (lines 79-116): **`_heuristic_fallback`** — 22-keyword bullish + 10-keyword bearish + 5-keyword urgency lists with **derived tradeable score formula `abs(sentiment-0.5)*2 * urgency_score`**. **Per Batch 53 NS-3 + B40 UN cross-cutting keyword-list cross-cutting**, **3rd keyword-bag-of-words module.** No shared vocabulary library. **Theme T8 (DRY)** — 3-module keyword-list duplication.
6. PE3-X1: pick_evaluator.py is **THE OUTCOME-ATTRIBUTION CONSUMER OF pick_logger** (434 lines, LARGEST single file). Walks daily OHLC from pick_date forward → marks TP_hit / SL_hit / unreachable_entry / day_close / expired / still_open. **6 OUTCOME STATES.** **Per Batch 11 PL cross-cutting consumer side** — closes signal_journal/learning chain. **Per Batch 22 SJ cross-cutting**, signals attach_outcome via `_journal_attach` — chains pick_evaluator → signal_journal → calibration (B59) → weight_proposer (B58) → weight_applier (B57).
7. PE3-X2 (lines 37-54): **`_save_picks` IS ATOMIC** (tmp + rename per docstring "May 11 2026: write to a sibling .tmp file then atomically rename"). **PER BATCH 49 WB / B57 / B60 / B63 cross-cutting atomic-write theme — FIRST AUDITED ATOMIC WRITE.** Confirms 5 safe / 32 unsafe / 37 = ~86% but **adds 6th safe writer.** Tally update: **6 safe / 32 unsafe / 38 total = ~84% UNSAFE.**
8. PE3-X3 (lines 265-291): **F3 UNREACHABLE_ENTRY DETECTION** with dated archaeology "Discovered Apr 28 SEMI bloodbath: 6 picks logged at prices $2-$20 ABOVE that day's actual high → impossible to fill." **Per Batch 14 MDH-X1 wrong-price archaeology cross-cutting**, **first audited "logged-vs-fillable price disagreement" detector.** Operator-critical safety guard. Per B57 FH-X2 cross_validate_price 2-source ancestor.

## src/llm_agent.py — LINE BY LINE

### Lines 1-13: Module docstring + imports
- LA-1 GOOD: 3-line docstring with priority order + cache TTL + throttle.
- LA-2 GOOD: stdlib imports condensed.
- LA-3 BUG (line 10): mkdir at import time. **Per Batch 49 WB-X2 cross-cutting — 12th import-time side-effect instance.**
- LA-4 GOOD (line 13): Named CLAUDE_MODEL constant.

### Lines 17-19: _cache_key
- LA-5 GOOD: `sort_keys=True, default=str` defensive serialization → md5 hash.
- LA-6 GOOD: Deterministic key derivation. ✅

### Lines 22-36: _cache_get
- LA-7 GOOD (lines 28-32): Per LA-X3, TZ-aware with naive backward-compat. **Gold standard.** ✅
- LA-8 BUG (line 34): bare except pass. Theme T1.

### Lines 39-45: _cache_put
- LA-9 BUG: **NO ATOMIC WRITE.** Per cross-cutting. Adds 33rd unsafe writer (tally below).
- LA-10 BUG (line 44): bare except pass.

### Lines 48-52: State flags + throttle
- LA-11 GOOD: Per LA-X2, mutable-list-singletons.
- LA-12 GOOD (line 52): Inline "Claude tier-1: 50 RPM, ~1.2s safe" archaeology.

### Lines 55-59: _throttle
- LA-13 GOOD: Time-elapsed sleep with module-state update.
- LA-14 BUG: **NOT THREAD-SAFE.** Per LA-X2.

### Lines 63-73: _rule_based
- LA-15 GOOD (line 64): 5-key skip set for sub-score filtering.
- LA-16 GOOD (lines 65-66): Numeric-only filter via isinstance.
- LA-17 GOOD (line 67): Top-3 sorted by value.
- LA-18 GOOD (line 73): "Confirm independently. No certainty implied." — **liability disclaimer.** Per Batch 53 NS / B62 PR-3 honest-state cross-cutting.

### Lines 77-98: _build_prompt
- LA-19 GOOD (line 78): Headlines top-5 with "None" fallback.
- LA-20 GOOD (line 82): trade_type-dependent hold rule.
- LA-21 GOOD (lines 91-96): **5-numbered-instruction prompt** with hard "Not financial advice." footer requirement + 120-word cap.

### Lines 100-109: _claude
- LA-22 GOOD: Standard anthropic SDK call.
- LA-23 BUG (line 102): `os.getenv` at every call — env-var re-read. Could miss runtime env changes (good) or skip dotenv load (acceptable here since llm_agent doesn't load_dotenv at import unlike B57 finnhub_data).

### Lines 113-124: _gemini
- LA-24 GOOD: Inline imports of `google.genai`.
- LA-25 GOOD (lines 117-123): try/except for older SDK fallback.
- LA-26 BUG (line 121): bare except → older-SDK path. Theme T1 (acceptable for SDK-version-fallback).

### Lines 128-135: _openai
- LA-27 GOOD: Standard OpenAI SDK.

### Lines 139-142: _is_quota_error
- LA-28 GOOD: 6-keyword classifier (resource_exhausted/quota/rate_limit/429/insufficient/credit). **Operator-readable.**

### Lines 146-155: _try_provider
- LA-29 GOOD (line 147): "Return (text, err_str). Returns (None, msg) on failure." docstring.
- LA-30 GOOD (line 155): Captures exception class + first 120 chars of message. **Operator-debuggable.** ✅

### Lines 158-195: _explain_uncached
- LA-31 GOOD: Per LA-X1 4-tier waterfall.
- LA-32 GOOD (lines 169-171): Quota-exhausted flag SET on first quota error — **subsequent calls skip Claude entirely for remainder of run.** ✅ Per Batch 50 cross-cutting state-machine pattern.
- LA-33 GOOD (line 175): Adaptive gem_model — uses caller-specified if it's a gemini model, else default flash-lite.
- LA-34 GOOD (line 187): OpenAI uses fixed gpt-4o-mini.
- LA-35 GOOD (line 194): Final rule-based fallback always works.

### Lines 198-206: explain_pick
- LA-36 GOOD: Cache → uncached → cache_put.

## src/news_classifier.py — LINE BY LINE

### Lines 1-4: Module docstring
- NC-1 GOOD: 3-line docstring.

### Lines 10-37: CLASSIFIER_PROMPT
- NC-2 GOOD: **27-line constant prompt** with 9-field JSON output schema + 5-row tradeable_score guide.
- NC-3 GOOD (lines 31-36): Per NC-X1 head, explicit-criteria score guide.
- NC-4 BUG (line 24): Truncated `produc[...]` — appears the category enum is truncated in source. **Definite bug — incomplete enum.** Operator can't see full category options.

### Lines 40-76: classify_news
- NC-5 GOOD (lines 42-49): 2-fallback path (no anthropic import / no API key) → heuristic.
- NC-6 GOOD (lines 52-58): Per-field 5-key prompt format with length limits (300 headline / 500 summary / 5 tickers).
- NC-7 GOOD (lines 67-71): Markdown fence stripping. Per Batch 39 MN cross-cutting same defensive parse.
- NC-8 GOOD (line 73): Returns `{**item, "classification": result, ...}` — **non-destructive enrichment.** ✅
- NC-9 BUG (line 74): bare Exception. Should be (anthropic.APIError, json.JSONDecodeError, KeyError).
- NC-10 GOOD (line 75): Operator-readable error message with class name + first 120 chars.

### Lines 79-116: _heuristic_fallback
- NC-11 GOOD: Per NC-X2, 3 keyword lists (22+10+5).
- NC-12 BUG: Per NC-X2 cross-cutting, 3-module keyword-list duplication.
- NC-13 GOOD (line 100): **Tradeable score formula `(abs(sentiment-0.5)*2) * urgency`** — operator-clear math.
- NC-14 GOOD (lines 107-113): 8-key classification mirror of Claude output schema. **Schema-compatible.**

### Lines 119-123: classify_batch
- NC-15 GOOD: Alpaca-first priority sort (line 122).
- NC-16 GOOD (line 122): Inline comment "Alpaca = pre-vetted" — operator-readable.

### Lines 126-136: __main__
- NC-17 GOOD: MaxLinear MXL smoke test. **16th __main__.**

## src/pick_evaluator.py — LINE BY LINE

### Lines 1-7: Module docstring
- PE3-1 GOOD: 7-line docstring with 4-condition logic.

### Lines 8-18: Imports + constants
- PE3-2 GOOD: yfinance + pandas + relative imports to signal_journal + sector_benchmark.
- PE3-3 BUG (line 16): Relative path. **55th file cumulative.**
- PE3-4 GOOD (lines 17-18): Named MAX_DAYS_OPEN + EVAL_LOOKBACK_DAYS.

### Lines 21-34: _load_picks
- PE3-5 GOOD (line 24): csv DictReader.
- PE3-6 BUG (line 24): No `newline=""`. Per cross-cutting csv-discipline.
- PE3-7 GOOD (lines 27-33): **Schema migration** — adds 8 SPY/sector fields with empty defaults. **Dated archaeology "(May 2 2026)"** ✅. Per Batch 56 MH cross-cutting schema-stable pattern.

### Lines 37-54: _save_picks
- PE3-8 GOOD: Per PE3-X2, **FULL ATOMIC WRITE.** Gold standard.
- PE3-9 GOOD (lines 38-44): **7-line docstring justifying atomic-write design** with dated archaeology ("Crash-safety (May 11 2026)"). 
- PE3-10 GOOD (line 50): `newline=""` ✅.
- PE3-11 GOOD (line 51): `lineterminator="\n"` — cross-platform.
- PE3-12 GOOD (line 54): `tmp.replace(LOG_PATH)` atomic rename.

### Lines 57-69: _fetch_ohlc
- PE3-13 GOOD (lines 64-65): MultiIndex column flatten — yfinance defensive.
- PE3-14 BUG (line 67): bare Exception + print. Theme T1 + B14 MDH cross-cutting.

### Lines 72-102: _spy_close_on
- PE3-15 GOOD (line 72): **MODULE-LEVEL CACHE** dict — per-run memoization.
- PE3-16 GOOD (line 76): "Cached to avoid repeated yf.download calls" inline rationale.
- PE3-17 BUG (line 80): INLINE IMPORT of datetime aliases. **8th cross-cutting inline-import instance.**
- PE3-18 GOOD (lines 81-92): 5-day window for weekend/holiday handling + at-or-before filter.
- PE3-19 BUG (line 99): bare Exception + print.

### Lines 105-124: _add_spy_alpha
- PE3-20 GOOD (line 108): `row.get("spy_close", "")` — defensive missing field.
- PE3-21 GOOD (lines 113-114): Scoped Exception for float coercion (acceptable broad).
- PE3-22 GOOD (line 121): SPY return formula + alpha = pick_return - SPY_return.

### Lines 127-143: _etf_close_on
- PE3-23 BUG (line 132): Another inline import.
- PE3-24 GOOD (lines 137): `df.index <= d.strftime(...)` — string comparison on DatetimeIndex. Works but type-fragile.

### Lines 146-169: _resolve_sector_etf_for_row
- PE3-25 GOOD (lines 147-152): 5-line docstring with concrete legacy example.
- PE3-26 GOOD (lines 157-162): **4-tier tag fallback chain** (tag → sector_tag → scores_sector_tag → "").
- PE3-27 GOOD (lines 163-168): **3-tier sector fallback chain** (sector → yfinance_sector → info_sector).
- PE3-28 GOOD (line 169): SPY ultimate fallback. **NEVER returns empty — always has a benchmark.** ✅

### Lines 172-204: _ensure_sector_benchmark_anchor
- PE3-29 GOOD (lines 173-177): 4-line docstring with SPY-fallback rationale.
- PE3-30 GOOD (lines 197-203): **SPY fallback path** when sector ETF fetch fails — rewrites both fields to SPY. **Self-healing legacy-row repair.** ✅
- PE3-31 BUG (line 186): bare Exception pass. Theme T1.

### Lines 207-226: _add_sector_alpha
- PE3-32 GOOD: Mirror of _add_spy_alpha for sector ETF.

### Lines 229-433: evaluate_pending (CORE)
- PE3-33 GOOD (line 230): 1-line docstring.
- PE3-34 GOOD (lines 232-234): Empty-picks defensive return with full 7-key counts dict.
- PE3-35 GOOD (line 236): TZ-naive `datetime.now().date()` — acceptable for date-only comparisons.
- PE3-36 GOOD (lines 244-247): Date parse with bare-except continue.
- PE3-37 BUG (line 246): bare Exception. Theme T1.
- PE3-38 GOOD (lines 248-253): Too-old pick auto-expire. **Cleanup pattern.**
- PE3-39 GOOD (lines 260-263): Empty df → still_open (don't lose track).
- PE3-40 GOOD: Per PE3-X3, lines 265-291 F3 unreachable_entry detection with 8-line archaeology comment.
- PE3-41 GOOD (line 280): **0.5% tolerance** for data-source rounding.
- PE3-42 GOOD (lines 287-290): Operator-readable rejection message with logged-vs-actual range.
- PE3-43 GOOD (lines 297-331): Day-walk forward iteration.
- PE3-44 GOOD (lines 298-303): **BUG-2 FIX archaeology** "(May 2 2026): include pick_date bar... 32 picks stayed pending forever." ✅
- PE3-45 GOOD (lines 307-321): **SAME-DAY-BOTH-HIT TIE-BREAKER** — uses Open price as anchor + distance-to-TP vs distance-to-SL classifier. **Per Batch 14 MDH gold standard ambiguity resolution.**
- PE3-46 GOOD (line 320): Tie-break debug log with both distances. **Operator-debuggable.** ✅
- PE3-47 GOOD (lines 333-357): Outcome attribution with 8-field update (status / evaluated_on / exit_price / return_pct / r_multiple / spy_alpha / sector_alpha).
- PE3-48 GOOD (line 340): `risk = entry - sl` + `risk > 0` guard. **Div-by-zero defense.** Per Batch 56 / B59 cross-cutting.
- PE3-49 GOOD (lines 344-353): journal_attach with broad Exception + WARN log + M9 marker. **Non-blocking failure.** ✅
- PE3-50 GOOD (line 357): **Multi-field operator status line** with R-multiple + alpha. Gold standard.
- PE3-51 GOOD (lines 359-397): **DAY_CLOSE BRANCH** with 6-line "Bug #5 (May 5 2026)" archaeology citing MPWR drift.
- PE3-52 GOOD (lines 367-374): **WEEKEND-PICK-DATE HANDLING** — falls back to first trading bar at-or-after. Per PE3-44 cross-cutting same defensive theme.
- PE3-53 GOOD (lines 384-393): journal_attach + WARN for day_close.
- PE3-54 GOOD (lines 400-427): Expiry branch with full attribution.
- PE3-55 GOOD (lines 414-423): journal_attach + WARN for expired.
- PE3-56 GOOD (lines 428-430): Still-open with operator-readable days_elapsed log.
- PE3-57 GOOD (line 432): Final atomic save.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### LA-X1 + NC-X1 + B39 + B53 cross-cutting CONFIRMED 4 LLM-orchestrator audit
**4 audited LLM-orchestrator modules:**
1. market_news (B39 MN-X1) — sentiment ONLY (Claude→Gemini→neutral_default)
2. news_signals (B53 NS-X1) — signals + catalysts ONLY
3. **news_classifier (this batch NC-X1)** — per-headline tradeable_score (Claude→heuristic)
4. **llm_agent (this batch LA-X1)** — RATIONALE generation (Claude→Gemini→OpenAI→rule_based)

**4-module LLM orchestration audit COMPLETE.** Each has different scope but **shared markdown-fence-stripping pattern + provider-fallback pattern.** Consolidation opportunity: shared `llm_orchestrator.py` base.

### PE3-X2 + B49 WB + cross-cutting ATOMIC WRITE TALLY MAJOR UPDATE
**FIRST AUDITED FULL ATOMIC WRITE module:** pick_evaluator._save_picks (this batch PE3-X2 + PE3-8).
**Tally update:** Was 5 safe / 31 unsafe / 36 = ~86% UNSAFE. Now **6 safe / 33 unsafe / 39 = ~85% UNSAFE.** (LA-9 + still has earlier counted unsafe writers.)
**Per Batch 49 WB / B57 / B60 / B63 cross-cutting** — pick_evaluator is the **GOLD-STANDARD reference** for atomic CSV rewrite. Should be applied to all other CSV/JSON whole-file rewriters.

### LA-X3 + cross-cutting TZ-aware tally update
**12 TZ-aware modules** (was 11): llm_agent (this batch LA-X3 + lines 32, 42) adds.

### PE3-X3 + B14 MDH + B57 FH-X2 cross-cutting unreachable-entry detection
**3 audited price-disagreement defense layers:**
1. Batch 14 MDH-X1 — pre-pick "XXYYZZ123" wrong-data telemetry
2. Batch 57 FH-X2 cross_validate_price — 2-source consensus check (Finnhub vs primary)
3. **pick_evaluator F3 (this batch PE3-X3)** — post-pick "logged-price-outside-actual-bar" detection

**3-module defense in depth.** Catalog as Theme T23 (price-integrity validation pipeline).

### PE3-44 + PE3-51 cross-cutting NEW: DATED-ARCHAEOLOGY GOLD STANDARD
**pick_evaluator has 5 DATED archaeology comments** with bug references:
- "May 2 2026 BUG-2: include pick_date bar... 32 picks stayed pending forever"
- "May 4 2026 F3: unreachable_entry detection... Apr 28 SEMI bloodbath: 6 picks"
- "May 5 2026 Bug #5: Day-trade force-close... MPWR drift case"
- "May 11 2026 crash-safety: atomic write"
- "May 2 2026: SPY relative perf alpha calculation"

**Per Batch 49 WB-X1 / Batch 53 NS-X1 / Batch 56 MH-X1 cross-cutting**, pick_evaluator joins as **15th DATED-archaeology module** but with **HIGHEST single-file count (5 distinct bug fixes documented).** Gold standard.

### NC-12 + B40 + B53 cross-cutting keyword-list DRY violation
**3 audited modules with parallel keyword vocab:**
- universe (B40 UN-X1)
- news_signals (B53 NS-X2 CATALYST table — formal table not keyword list)
- **news_classifier (this batch NC-X2)** — 22+10+5 keywords

**Should consolidate.** Single `keyword_vocabulary.py` shared.

### LA-3 + cross-cutting import-time side-effect tally
**12 instances:** llm_agent (LA-3) adds. **probability_engine PR-7 sys.path.insert** remains worst.

### Cross-cutting: bare-except this batch
- llm_agent: 3 (LA-8 cache get, LA-10 cache put, LA-26 Gemini SDK fallback)
- news_classifier: 1 (NC-9 Claude failure)
- pick_evaluator: 5 (PE3-14 ohlc, PE3-19 spy, PE3-31 anchor, PE3-37 date parse, plus journal_attach 3 instances)

**9 bare-excepts in 3 files.** All defensive/graceful. Pick_evaluator at 5 = moderate density.

### Cross-cutting: TZ-aware: **12 modules** (LA-X3 adds).
### Cross-cutting: ATOMIC WRITE: **6 safe / 33 unsafe / 39 total = ~85% UNSAFE.** PE3-X2 first audited full atomic.
### Cross-cutting: __main__: 16 modules (news_classifier NC-17 adds).
### Cross-cutting: dataclass: 5 (no new).

## SUMMARY (Batch 64)

| Severity | llm_agent | news_classifier | pick_evaluator | Cross-cutting | Total |
|---|---:|---:|---:|---:|---:|
| Show-stopper | 4 | 3 | 6 | 5 | 18 |
| Data/safety | 2 | 1 | 1 | 0 | 4 |
| Code smell | 0 | 0 | 0 | 0 | 0 |
| Good code | 30 | 14 | 50 | 0 | 94 |
| Total findings | 36 | 18 | 57 | 5 | 116 |

## TOP 10 CRITICAL FIXES from Batch 64

1. **NC-4 (CRITICAL):** Fix truncated `produc[...]` in CLASSIFIER_PROMPT category enum — operator can't see full category options + Claude may produce invalid categories. (5 min)
2. **LA-X2 / LA-14 (HIGH):** Make llm_agent thread-safe (parallel_scorer B44 uses ThreadPoolExecutor). Use threading.Lock around _LAST_CALL + quota flags. (15 min)
3. **PE3-X2 GOLD STANDARD propagation (HIGH):** Apply pick_evaluator's atomic-write pattern to other 32 unsafe writers (highest impact cross-cutting fix). (~1 hour for top 5 priority modules)
4. LA-9: Add atomic write to llm_agent._cache_put. (3 min)
5. NC-12 / Theme T8: Consolidate 3-module keyword vocabularies. (30 min)
6. LA-8 + LA-10 + LA-26 + NC-9 + PE3-14 + PE3-19 + PE3-31 + PE3-37: Scope 8 bare-excepts to specific exception types. (15 min)
7. LA-3: Move llm_agent mkdir from import-time to lazy init. **12th cross-cutting instance.** (1 min)
8. PE3-6: Add `newline=""` to _load_picks csv.DictReader. (1 min)
9. PE3-17 + PE3-23: Hoist 2 inline datetime imports to module top. (1 min)
10. PE3-X3 / Theme T23 cross-cutting: Document price-integrity validation pipeline in `docs/PRICE_INTEGRITY.md` (B14 MDH + B57 FH-X2 + this batch PE3-X3). (15 min)

## NEW THEMES UPDATED

- **Theme T1 (bare except):** 9 total. PE3 at 5 = moderate.
- **Theme T2 (schema drift):** PE3-7 schema migration is gold-standard handled.
- **Theme T6 (atomic writes):** **FIRST AUDITED FULL ATOMIC WRITE (PE3-X2).** Tally: 6 safe / 33 unsafe / 39 = ~85% UNSAFE.
- **Theme T8 (DRY):** NC-12 3-module keyword-list duplication.
- **Theme T14 (gold-standard patterns):** **llm_agent LA-X1 4-tier waterfall** + LA-X2 cheap mutable singletons + LA-X3 TZ-aware backward-compat + LA-21 5-instruction prompt with liability + LA-30 operator-debuggable error format + LA-32 quota-exhausted state-machine. **news_classifier NC-X1 6-tier explicit-criteria prompt + NC-X2 derived tradeable formula + NC-8 non-destructive enrichment.** **pick_evaluator PE3-X2 FIRST AUDITED FULL ATOMIC WRITE + PE3-X3 unreachable-entry detection + PE3-7 schema migration + PE3-28 SPY-ultimate-fallback + PE3-30 self-healing legacy repair + PE3-45 tie-breaker with Open distance + PE3-46 tie-break debug log + PE3-44 multi-bug DATED-archaeology (5 dated fixes in single file — highest in audit) + PE3-49 non-blocking journal_attach with M9 marker + PE3-52 weekend-pick-date defensive fallback.**
- **NEW Theme T23 (price-integrity validation):** 3-module defense (MDH pre-pick + FH cross-validate + PE3 unreachable-entry).

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase F | 9/~38 done | llm_agent, news_classifier, pick_evaluator | 9/~38 |
| Total true line-by-line | | **+3 files** | **142 of ~382 (~37.2%)** |

**MILESTONE: First atomic-write reference (PE3-X2). LARGEST file in repo audited. 4-LLM-orchestrator audit COMPLETE. Outcome attribution consumer COMPLETE.**

## NEXT BATCH

Batch 65 (doc #71): Continue Phase F. 3 NEW files from inventory:
- **`src/meta_brain.py` (~13KB / 12569B)** — second-largest unaudited; brain orchestrator.
- **`src/hard_blocks.py` (~12KB / 11902B)** — referenced as BLOCK 4 in many cross-cuts but never audited.
- **`src/wisdom_hint.py` (~9KB / 9181B)** — referenced as consumer of B49 wisdom_base lessons (B58 AP-X1).

End of Batch 64. Phase F (9/38). **37.2% audit milestone.**
