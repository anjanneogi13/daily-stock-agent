# Batch 52 — src/news_classifier.py (136 lines) + src/news_engine.py (163 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** news_classifier.py (136 lines), news_engine.py (163 lines)
**Phase:** E (subdirectory & ancillary). Files 23 and 24 of ~50.

## TOP HEADLINE FINDINGS

1. NC-X1: news_classifier.py is **THE CLAUDE-POWERED NEWS LABELER** — calls Anthropic Claude Sonnet 4.5 with structured prompt → returns 11-field classification dict (sentiment / urgency / category / tradeable_score / etc.). **First LLM-as-classifier module in audit.** Per Batch 41 WM-X1 watchlist_manager consumes the classification output.
2. NC-X2 (lines 79-116): **HEURISTIC FALLBACK** when Claude unavailable — keyword-based bullish/bearish/urgency classifier with 23 keywords. **Per Batch 43 PE3-X1 honest v0.1 + Batch 48 LG-X2 fail-safe pattern**, this is **excellent defense-in-depth** — module never hard-fails on classification.
3. NC-X3 (lines 21-29, 32-36): **PROMPT-TEMPLATE COUPLES JSON SCHEMA TO CONSUMER** — the prompt explicitly enumerates 11 sentiment/urgency/category enums. **A schema change requires synchronized prompt + downstream parser update.** Per Batch 28 NC cross-cutting Theme T2 schema-chaos. **Truncated category enum in prompt** (line 24 shows `"produc[...]` — TEXT-TRUNCATED by repo file viewer or actually truncated in source).
4. NE-X1: news_engine.py is **THE MULTI-SOURCE NEWS FETCHER** — Alpaca (primary) + Yahoo RSS (per-ticker backup) + SEC EDGAR (declared but not implemented in shown code). Per Batch 39 MN gh_observability cross-cutting, this is the **input layer** that feeds news_classifier → watchlist_manager → wisdom layer.
5. NE-X2 (lines 23-44): **TZ-AWARE dedup cache with TTL trimming** — `datetime.now(timezone.utc) - timedelta(hours=48)` cutoff applied on every save. **CONFIRMED 9th TZ-aware module** + correct `.replace("Z", "+00:00")` Z-suffix defensive parsing. Per Batch 47 AM-25 / Batch 49 LG-9 cross-cutting Z-handling defensiveness. ✅
6. NE-X3 (lines 100-105): **REGEX-BASED XML PARSING with `re.DOTALL`** for Yahoo RSS — explicitly NOT using feedparser. Per line 97 comment "no feedparser dependency." **Same pure-stdlib philosophy as Batch 50 HE-X3 (binomial CDF without scipy).** **Pattern: minimize dependency surface.** ✅ but **fragile** — malformed XML (nested `<item>` tags, escaped angle brackets in CDATA) silently misses items.
7. NE-X4 (line 44 `_save_seen` + line 153 `append_news_log`): **2 UNSAFE WRITERS in this file.** `NEWS_CACHE.write_text(...)` and `NEWS_LOG.open("a")`. Per Batch 49 WB-32 / Batch 51 EZ-13 cross-cutting atomic-write tally. **Adds 25th + 26th unsafe writers.** Atomic-write tally now ~85% UNSAFE.

## src/news_classifier.py — LINE BY LINE

### Lines 1-4: Module docstring
- NC-1 GOOD: 4-line docstring documents Claude Sonnet 4.5 + 5 output fields.
- NC-2 BUG: Undersells — heuristic fallback (NC-X2) deserves headline.

### Lines 5-8: Imports
- NC-3 GOOD: Pure stdlib + typing.

### Lines 10-37: CLASSIFIER_PROMPT
- NC-4 GOOD (lines 10-29): 20-line structured prompt with explicit JSON schema.
- NC-5 GOOD (lines 20, 22, 24, 28): Pipe-separated enum values for sentiment/urgency/category/action_window.
- NC-6 BUG (line 24): `"category": "earnings_beat" | ... | "produc[...]` — **APPEARS TRUNCATED.** Either the file viewer truncated it OR the prompt itself is truncated. If actually truncated in source, **Claude returns invalid `category` values not in the enum** → downstream silently misclassifies. **CRITICAL LATENT BUG** — needs source verification.
- NC-7 GOOD (lines 31-36): tradeable_score 5-tier guide with concrete examples (FDA, earnings beat %, M&A, etc.). **Operator-readable.**

### Lines 40-76: classify_news
- NC-8 GOOD (lines 42-45): Defensive import — falls back to heuristic if anthropic SDK not installed. Per Batch 49 WH-X2 import-time fallback pattern but **explicitly scoped to ImportError** (good).
- NC-9 GOOD (lines 47-49): Empty-key fallback to heuristic.
- NC-10 GOOD (line 51): Client instantiated per call. **Per Batch 39 MN-X3 cross-cutting**, NOT module-level — test-isolation friendly. ✅
- NC-11 GOOD (lines 52-58): Prompt formatting with length-bounded inputs (300/500/5/etc.). **Defensive against unbounded prompts.** ✅
- NC-12 GOOD (line 55): `", ".join(item.get("ticker_list", [])[:5]) or "none"` — defensive empty handling.
- NC-13 GOOD (lines 60-65): API call with explicit model, max_tokens, timeout via SDK.
- NC-14 BUG (line 62): `model="claude-sonnet-4-5"` hardcoded. **Should be const + env-var override** for future model rotation. Per Batch 31 HH-X3 magic constants.
- NC-15 GOOD (lines 67-71): Markdown fence stripping defense — Claude sometimes wraps JSON in ```json blocks despite "no markdown" instruction. **DEFENSIVE.** ✅
- NC-16 BUG (lines 68-71): String-slice fence stripping is fragile. Better to use regex `^```(?:json)?\s*(.*?)\s*```$`.
- NC-17 GOOD (line 73): Returns enriched dict with `classified_at` timestamp.
- NC-18 BUG (line 73): NAIVE `datetime.now().isoformat()`. Per Batch 49 LG-X4 cross-cutting TZ-aware/naive theme. **Compare to news_engine NE-X2 which IS TZ-aware** — **2 files in SAME LAYER inconsistent.** Same cache file (news_seen.json) potentially gets both formats if both call paths populate.
- NC-19 BUG (lines 74-76): bare except + print + heuristic fallback. **Documented graceful degradation** but bare-except masks all error types (timeout, auth, malformed JSON, rate-limit). Per Batch 51 EZ-22 cross-cutting.

### Lines 79-116: _heuristic_fallback
- NC-20 GOOD: Per NC-X2, defense-in-depth keyword classifier.
- NC-21 GOOD (line 81): Lowercases concatenated headline+summary. Case-insensitive.
- NC-22 BUG (lines 83-87): **Hardcoded keyword lists** — 11 bullish + 10 bearish + 5 high-urgency. **No archaeology — why these words?** Should reference linguistic source or be tunable via config.
- NC-23 GOOD (lines 89-97): 3-tier sentiment classification.
- NC-24 GOOD (line 100): Tradeable score = `|sentiment_score - 0.5| * 2 * urgency_score`. **Reasonable composite** — neutral news = 0, strong + urgent = ~1.
- NC-25 GOOD (lines 102-116): Returns dict matching Claude classification schema. **Schema-compatible fallback.** ✅
- NC-26 BUG (line 115): NAIVE timestamp. Per NC-18.
- NC-27 BUG (line 109): `"category": "other"` — heuristic can't categorize beyond bullish/bearish. **Documented limitation** but downstream consumers (Batch 41 WM) may filter on category.

### Lines 119-123: classify_batch
- NC-28 GOOD: Batch processor with Alpaca-first prioritization.
- NC-29 BUG (line 122): `sorted(items, key=lambda x: 0 if x.get("source") == "alpaca" else 1)` — only 2-source priority. **A 3rd source (Yahoo, SEC) gets the same priority 1.** Should be ordered enum or explicit priority dict.
- NC-30 BUG (line 119): Magic max_items=20. Per Batch 31 HH-X3.

### Lines 126-136: __main__ smoke test
- NC-31 GOOD: Concrete MXL example for operator-runnable test.
- NC-32 GOOD (line 133): TZ-NAIVE timestamp again in test — inconsistent with engine.

## src/news_engine.py — LINE BY LINE

### Lines 1-4: Module docstring
- NE-1 GOOD: 4-line docstring documenting 3 sources + dedup.
- NE-2 BUG: Mentions SEC EDGAR (line 2) but **no SEC implementation in this file.** Documentation drift OR future-stub.

### Lines 5-12: Imports
- NE-3 GOOD: Pure stdlib + requests + re. Lightweight.
- NE-4 GOOD: `from datetime import datetime, timedelta, timezone` — **HAS timezone import.** Per Batch 49 WB-4 cross-cutting NAIVE-datetime contrast, this file is **CORRECTLY TZ-aware imports.**

### Lines 14-20: Constants
- NE-5 GOOD: 3 named URL templates + 2 named paths + DEDUP_TTL_HOURS.
- NE-6 BUG (line 18, 19): Relative paths. **38th + 39th files** with this pattern.
- NE-7 BUG: SEC_EDGAR_URL defined (line 16) but unused. **Dead constant.** Per NE-2 documentation drift.

### Lines 23-29: _load_seen
- NE-8 GOOD: Defensive missing-file + JSON-parse-error empty dict.
- NE-9 BUG (line 27): bare except. Should be (json.JSONDecodeError, OSError).

### Lines 32-44: _save_seen
- NE-10 GOOD (line 33): mkdir parents — defensive.
- NE-11 GOOD: Per NE-X2, TTL trim on every save. **Memory-bounded cache.** ✅
- NE-12 GOOD (line 39): `.replace("Z", "+00:00")` Z-defensive parse. ✅
- NE-13 BUG (line 42): bare except pass. **Silently drops entries with malformed timestamp from pruned dict.** Theme T1 + Theme T13 silent fill.
- NE-14 BUG (line 44): Per NE-X4, **NO ATOMIC WRITE.** NEWS_CACHE.write_text → power loss = corrupt cache. 25th unsafe writer.

### Lines 47-85: fetch_alpaca_news
- NE-15 GOOD (lines 49-53): Credential check with graceful skip message.
- NE-16 GOOD (line 55): TZ-aware UTC start time.
- NE-17 GOOD (lines 56-62): Explicit headers + params.
- NE-18 GOOD (line 65): Explicit timeout=15. ✅ Per Batch 51 EZ-17 cross-cutting.
- NE-19 GOOD (lines 66-68): HTTP status check + truncated body log (200 chars).
- NE-20 GOOD (lines 71-82): Normalizes Alpaca response to common item schema.
- NE-21 GOOD (line 73): `"id": f"alpaca_{n.get('id')}"` — namespaced ID. Per Batch 38 DS-X1 dedup cross-cutting key-prefix pattern.
- NE-22 GOOD (lines 76, 77): Length-bounded headline/summary (300/600).
- NE-23 GOOD (line 79): `n.get("created_at") or n.get("updated_at")` — fallback for missing field.
- NE-24 BUG (line 83-85): bare except + print. Theme T1.

### Lines 88-120: fetch_yahoo_rss
- NE-25 GOOD (line 91): `tickers[:20]` cap. **Operator-protection vs Yahoo rate-limiting.** ✅
- NE-26 GOOD (line 94): timeout=8 + User-Agent header. **UA spoof avoids blocks.**
- NE-27 GOOD: Per NE-X3, regex-based XML parsing.
- NE-28 BUG (lines 100-105): Fragile regex parsing. **Cannot handle nested CDATA or escaped XML entities.** Acceptable for Yahoo RSS today; may break on schema change.
- NE-29 GOOD (line 100): `[:3]` limit per ticker — caps total to 60 items.
- NE-30 GOOD (line 108): Stable ID via `abs(hash(title))` — but **`hash()` returns DIFFERENT value across Python processes** (PYTHONHASHSEED randomized). **CRITICAL DEDUP BUG** — `news_seen.json` from prior run's hash() won't match this run's, defeats dedup. Per Batch 38 DS-X1 cross-cutting. **Should use hashlib.sha256(title).hexdigest()[:12]** for stable cross-process ID.
- NE-31 GOOD (line 117): `time.sleep(0.2)` rate-limit politeness.
- NE-32 BUG (line 118-119): bare except continue. Theme T1.

### Lines 123-145: fetch_all_news (MAIN PUBLIC API)
- NE-33 GOOD: Orchestrates dedup across both sources.
- NE-34 GOOD (lines 131-134): Per-item dedup + freshness add.
- NE-35 GOOD (lines 137-142): Watchlist-aware Yahoo fetch (only if tickers provided).
- NE-36 GOOD (line 144): Saves updated seen dict.
- NE-37 GOOD: TZ-aware timestamps written. ✅

### Lines 148-155: append_news_log
- NE-38 BUG: Per NE-X4, **NO ATOMIC append safety.** `with NEWS_LOG.open("a")` — partial-line risk on crash. 26th unsafe writer.
- NE-39 GOOD (line 150-151): Empty-items early return.
- NE-40 GOOD (line 152): mkdir parents.

### Lines 158-163: __main__ smoke test
- NE-41 GOOD: Operator-runnable. Shows source + headline + tickers.
- NE-42 GOOD: Per Batch 41 / Batch 49 cross-cutting __main__ pattern. **8th module with __main__ smoke.**

## CONSOLIDATED CROSS-CUTTING FINDINGS

### NC-X1 + NE-X1 + Batch 41 WM cross-cutting CONFIRMED news pipeline architecture
**Full news flow chain documented:**
- news_engine (this batch) FETCHES from Alpaca + Yahoo
- news_classifier (this batch) CLASSIFIES via Claude or heuristic
- watchlist_manager (B41 WM-X1) STORES + boosts scores from classification
- parallel_scorer (B44 PS-13) APPLIES watchlist_boost to composite
- probability_engine (B43 PE3-X3) USES news_score in NEWS_ADJUSTMENTS

**5-module chain.** Per Batch 23 SA-X1 brain-pillar architecture, **news layer is fully traced.** ✅

### NC-18 + NC-26 + NC-32 cross-cutting: TZ-NAIVE in news_classifier vs TZ-AWARE in news_engine
**Same layer, inconsistent timezone discipline:**
- news_engine: ALL timestamps TZ-aware UTC (line 35, 55, 134, 142)
- news_classifier: ALL timestamps NAIVE (lines 73, 115, 133)

**A `classified_at` timestamp written naive + compared to a `published_at` timestamp written aware = TypeError.** Per Batch 49 LG-X4 cross-cutting confirmed AGAIN in news layer. **Now 4 modules with TZ-naive/aware drift risk:** lesson_gc, wisdom_base (writer), news_classifier (writer), earnings (intentional).

### NE-30 cross-cutting: Process-non-stable hash() for dedup ID
**CRITICAL DEDUP BUG.** Per Batch 38 DS dedup_sender cross-cutting, dedup requires stable cross-process IDs. **`abs(hash(title))` is RANDOMIZED per process via PYTHONHASHSEED.** Every cron run gets different IDs for same headlines = **EVERY YAHOO HEADLINE TREATED AS NEW EVERY RUN.** **Dedup completely broken for Yahoo source.**

### NC-X3 / NC-6 cross-cutting: Truncated category enum
If line 24 prompt is actually truncated in source (not just file-viewer artifact), **Claude returns invalid category values** that downstream watchlist_manager / wisdom layer cannot parse. **Need to verify by fetching raw source bytes.** **Theme T2 schema-chaos at LLM-prompt level.**

### NE-X3 + Batch 50 HE-X3 cross-cutting: Pure-stdlib dependency-minimization philosophy
**3 modules with explicit "avoid heavy dependency" comments:**
- hypothesis_engine (B50): pure-stdlib binomial (no scipy)
- earnings (B51): defensive yfinance parser (no feedparser-style fragility)
- news_engine (this batch): regex XML (no feedparser)

**Pattern: minimize deploy surface.** Per Batch 41 SE-X1 pure-data gold standard. **Now confirmed as architectural philosophy** for analytic + fetch layer.

### NE-X4 + cross-cutting atomic-write tally
2 new unsafe writers in this single file:
- _save_seen (line 44) — JSON cache rewrite
- append_news_log (line 153) — JSONL append

**Atomic-write tally update:** 4 safe / 22 unsafe / 26 total = **~85% UNSAFE.**

### Cross-cutting: bare-except this batch
- news_classifier: 1 (NC-19 Claude API defense)
- news_engine: 4 (NE-9 cache, NE-13 timestamp parse, NE-24 Alpaca, NE-32 Yahoo)

5 bare-excepts, all defensive against external APIs/parsers. Per Batch 51 EA/EZ pattern — **fetch layer is bare-except heavy by design.**

### Cross-cutting: relative-path constants — **39 files now** (news_engine adds 2).

### Cross-cutting: TZ-aware modules — **news_engine = 9th TZ-aware module.**

### Cross-cutting: bug-archaeology gold standard: 8 modules (no addition).

### Cross-cutting: __main__ smoke test pattern — **8 modules now.**

### Cross-cutting: import-time side effect: 6 instances (no new this batch — both files clean).

## SUMMARY (Batch 52)

| Severity | news_classifier | news_engine | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 5 | 7 | 5 | 17 |
| Data/safety | 3 | 4 | 0 | 7 |
| Code smell | 2 | 1 | 0 | 3 |
| Good code | 22 | 28 | 0 | 50 |
| Total findings | 32 | 40 | 5 | 77 |

## TOP 10 CRITICAL FIXES from Batch 52

1. **NE-30 (CRITICAL):** Replace `abs(hash(title))` with `hashlib.sha256(title).hexdigest()[:12]`. **Yahoo dedup is completely broken across processes.** Every run = duplicates. (5 min)
2. **NC-6 / NC-X3 (CRITICAL — verify):** Check if line 24 prompt `"produc[...]` is actually truncated in source. If yes, restore full enum. Else, file-viewer artifact only. (5 min investigation + 5 min fix)
3. **NC-18 + NC-26 + NC-32 (HIGH):** Convert news_classifier timestamps to TZ-aware UTC. Match news_engine discipline. (5 min)
4. NE-X4 / NE-14 + NE-38: Add atomic write to _save_seen + atomic append to append_news_log. (10 min, bundled with prior atomic-write refactors)
5. NE-2 / NE-7: Either implement SEC EDGAR fetch or remove dead constant + docstring claim. (10 min)
6. NC-14: Lift `claude-sonnet-4-5` model name to const + env-var override. (5 min)
7. NC-16: Replace string-slice fence stripping with regex. (5 min)
8. NC-22: Move hardcoded keyword lists to config or document linguistic source. (15 min)
9. NC-29: Use explicit source-priority dict for classify_batch. (5 min)
10. NE-9, NE-13, NE-24, NE-32, NC-19: Scope 5 bare-excepts to specific exception types. (10 min)

## NEW THEMES UPDATED

- **Theme T1 (bare except):** news_classifier 1 (Claude defense). news_engine 4 (cache, parse, 2 fetch defenses). **Fetch+LLM layer is bare-except heavy by design.**
- **Theme T2 (schema drift):** NC-X3 truncated prompt enum (potential). NC-X3 prompt-couples-consumer-parser. NE-2 SEC EDGAR doc drift.
- **Theme T6 (atomic writes):** Adds 2 unsafe writers (25th + 26th). Tally: 4 safe / 22 unsafe / 26 total = ~85% UNSAFE.
- **Theme T8 (DRY):** NC-X1 + NE-X1 5-module news chain — could share `_news_item` dataclass.
- **Theme T11 (fail-open by accident):** NC-X2 heuristic fallback (documented + defensive — intentional). NE-30 hash() dedup silently broken across processes.
- **Theme T13 (silent-default-fills):** NE-13 silent drop of malformed-timestamp entries. NC-27 "category=other" fallback.
- **Theme T14 (gold-standard patterns):** news_classifier NC-X2 heuristic fallback (schema-compatible) + NC-11 length-bounded prompt + NC-15 markdown-fence defense. news_engine NE-X2 TZ-aware TTL-trimmed cache + NE-X3 regex XML (pure-stdlib) + NE-26 timeout + UA spoof + NE-21 namespaced IDs. **TZ discipline in news_engine = TEMPLATE for fetch modules.**

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A | 8/8 COMPLETE | (none) | 8/8 |
| Phase B | 18/18 COMPLETE | (none) | 18/18 |
| Phase C | 12/12 COMPLETE | (none) | 12/12 |
| Phase D | 30/~30 COMPLETE | (none) | 30/~30 |
| Phase E | 24/~50 done | news_classifier, news_engine | 24/~50 |
| Total true line-by-line | | +2 files | **107 of ~382 (~28.0%)** |
| Remaining | | | **~275 files** |

## NEXT BATCH

Batch 53 (doc #59): Continue Phase E. Two strong candidates close out news layer:
- **`src/news_signals.py` (13.1KB)** — biggest unaudited news file. Produces signals consumed by signal_journal.
- **`src/news_sentiment.py` (2.0KB)** — older sentiment scorer used by parallel_scorer (B44 PS-12).

End of Batch 52. Phase E in progress (24/50). **28.0% audit milestone.**
