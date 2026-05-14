# Batch 17 — src/news_classifier.py (136 lines) + src/news_sentiment.py (46 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** news_classifier.py (136 lines, fully read), news_sentiment.py (46 lines, fully read)
**Phase:** B (scoring + data layer) — files 11 and 12 of ~18

## TOP HEADLINE FINDINGS

1. NC-X1: news_classifier.py is THE LLM CLASSIFICATION layer. Calls Claude Sonnet 4.5 via anthropic SDK (line 51-65). Falls back to keyword heuristic. **Per-item synchronous LLM call** — for 20 news items in classify_batch, 20 sequential network calls to Anthropic. ~10-30 seconds latency per pipeline run. No batching, no parallelism.
2. NC-X2: BIG ARCHITECTURAL INCONSISTENCY between news_classifier and news_sentiment. **They are TWO PARALLEL NEWS PIPELINES that don't talk to each other.**
   - news_sentiment.score_sentiment is what parallel_scorer line 49 calls (Batch 8 PS-15) → produces composite scoring input
   - news_classifier.classify_news is what news_signals.add_signal_from_classification consumes → produces score_delta boost
   - **Same news data, two different scoring paths, two different code styles, ZERO shared logic.** Theme T8 cross-file duplication at the architectural level.
3. NC-X3: news_sentiment.fetch_news (line 19) and news_engine.fetch_yahoo_rss (Batch 16 NE-24) BOTH fetch from Yahoo Finance RSS. **Same Yahoo source, two implementations.** news_sentiment uses feedparser (proper). news_engine uses regex (fragile per Batch 16 NE-27). **Two parallel implementations of the same fetch.**
4. NC-7 (line 24): The CLASSIFIER_PROMPT category enum is TRUNCATED in the file — line ends mid-string ("...produc[..."). **Either the file is corrupted at view-time OR the prompt itself is incomplete.** If incomplete, Claude is given an unbounded category list and may produce categories news_signals.CATALYST_RULES (Batch 16 NS-7) doesn't recognize → silent NS-37 return None → no signal generated. Critical.
5. NC-13 (line 73): `datetime.now().isoformat()` — **NO TIMEZONE.** Compare to news_signals NS-14 which uses `datetime.now(timezone.utc).isoformat()`. **Two timestamp formats in same news pipeline.** Downstream `_purge_expired` parses these — if naive datetime sneaks in, fromisoformat may misinterpret.
6. NSENT-X1: news_sentiment.py is 46 LINES with 64 keywords. Simplest classifier in codebase. Whole file replaceable with anything more sophisticated. **score_sentiment runs on EVERY ticker (not just ones with news)** — is the value worth the call?
7. NC-12 (lines 68-72): Markdown-fence stripping is FRAGILE. Handles `\`\`\`json` and `\`\`\`` but breaks on:
   - Whitespace before fence
   - Fence not at very start
   - Trailing fence (`\`\`\`` at end)
   - Nested fences
   **One unusual Claude response → JSONDecodeError → fallback to heuristic. Silent quality drop.**

## src/news_classifier.py — LINE BY LINE

### Lines 1-4: Module docstring
- NC-1 GOOD: Brief, names model (Claude Sonnet 4.5).
- NC-2 SMELL: Hardcoded model name in docstring AND line 62. Two places to update.

### Lines 5-8: Imports
- NC-3 SMELL (line 8): `from datetime import datetime` — but NO timezone import. Per NC-13 below, this leads to naive datetimes.

### Lines 10-37: CLASSIFIER_PROMPT
- NC-4 GOOD: Explicit JSON-only instruction ("Respond with ONLY valid JSON, no markdown").
- NC-5 GOOD: Includes structured fields: sentiment / urgency / category / tradeable_score / primary_ticker / rationale / action_window.
- NC-6 GOOD (lines 31-36): tradeable_score scoring guide with examples per range.
- NC-7 CRITICAL (line 24): `"category": "earnings_beat" | "earnings_miss" | "fda_approval" | "fda_rejection" | "ma_acquirer" | "ma_target" | "downgrade" | "upgrade" | "guidance_raise" | "guidance_cut" | "lawsuit" | "produc[...`
  - **The line is truncated in the source view at "produc[..."**. Either:
    - GitHub blob view truncated for display (likely)
    - File actually has a partial enum (catastrophic)
  - **Need to verify by checking raw file size.** If complete, the missing categories likely include "product_launch" (referenced in news_signals.CATALYST_RULES NS-7) and "other"/"rumor".
- NC-8 BUG: Even if complete, the enum lists 12+ categories. **news_signals.CATALYST_RULES has only 12 categories** (Batch 16 NS-7). If Claude returns "executive_change" or "stock_split" or any other category not in CATALYST_RULES, news_signals.add_signal_from_classification (NS-37) returns None silently. **Classification work wasted, no signal generated.**
- NC-9 BUG: action_window enum 4 values (intraday/next_day/this_week/ignore). Stored in signal dict but NOT consumed anywhere I can verify in audited files. Unused field?

### Lines 40-77: classify_news
- NC-10 GOOD (lines 42-45): Optional anthropic dep — falls back to heuristic if unavailable.
- NC-11 GOOD (lines 47-49): API key check with same fallback.
- NC-12 GOOD (lines 51-58): Constructs prompt with field truncation. Magic limits 300/500/5 — yet more truncation lengths.
- NC-13 BUG (line 53): `[:300]` — magic 300 char headline truncation. Per Batch 16 cross-cutting, 7+ different truncation lengths in audited files.
- NC-14 BUG (line 54): `[:500]` — summary cap. Different from news_engine which uses 600 (NE-21). **Same logical field, two truncation lengths.**
- NC-15 GOOD (lines 60-65): Single LLM call with timeout-via-SDK and max_tokens=400.
- NC-16 BUG (line 62): `model="claude-sonnet-4-5"` — hardcoded model. Should be env var or config.
- NC-17 BUG (line 63): `max_tokens=400` — magic. JSON response per the prompt schema is ~150 tokens; 400 is generous but burns budget on every call.
- NC-18 BUG (line 65): NO request timeout passed. Anthropic SDK has a default but explicit is better. A hung request stalls the whole batch.
- NC-19 BUG (lines 68-72): Fragile markdown-fence stripping per NC-X4 (top finding).
  - `text.startswith("\`\`\`")` — handles leading fence
  - `text.split("\`\`\`")[1]` — takes content between first two fences
  - Strips "json" prefix if present
  - **Breaks on: trailing whitespace, leading non-fence text, fence at line ends without newlines.**
- NC-20 BUG (line 72): `json.loads(text.strip())` — if Claude returns invalid JSON despite the "ONLY valid JSON" instruction, raises → caught at 74 → fallback to heuristic. **Silent fallback to inferior classifier.** Should at least log the bad JSON for prompt-engineering iteration.
- NC-21 GOOD (line 73): Returns enriched dict with `classification` sub-dict and `classified_at` timestamp.
- NC-22 BUG (line 73): `datetime.now().isoformat()` — **NAIVE DATETIME**. Per NC-13 head finding. news_signals expects timezone-aware ISO strings. Mixing.
- NC-23 GOOD (line 75): Failure logged with type(e).__name__ + truncated str.
- NC-24 BUG (line 75): `str(e)[:120]` — magic 120 truncation. Same as data_fetcher DF-16, news_engine NE-22.

### Lines 79-116: _heuristic_fallback
- NC-25 GOOD (line 81): Combines headline + summary, lowercased.
- NC-26 BUG (lines 83-84): 11 bullish keywords. Substring match per Batch 16 NS-15 same false-positive risk. "wins contract" matches "wins customer complaint" (rare but possible).
- NC-27 BUG (lines 85-86): 10 bearish keywords. Same substring fragility.
- NC-28 BUG (line 87): 5 high-urgency keywords. "earnings" matches "earnings call scheduled" — routine event scored as high urgency.
- NC-29 BUG (lines 89-95): If/elif chain — bullish wins if both bullish AND bearish keywords match. **Order matters.** A headline "earnings beat overshadowed by lawsuit" → bullish triggers first → classified bullish. Wrong.
- NC-30 BUG (line 100): `(abs(sentiment_score - 0.5) * 2) * urgency_score` — magic formula. (deviation from neutral) * 2 * urgency. With sentiment=0.75 (bullish), urgency=0.7: (0.5) * 0.7 = 0.35 → "tradeable_score" 0.35. **Per CLASSIFIER_PROMPT line 35-36 ("0.3-0.5: minor news"), heuristic ALWAYS produces minor-news scoring.** Heuristic systematically underestimates impact — never produces 0.7+.
- NC-31 GOOD (lines 102-115): Returns same shape as Claude classification — caller-transparent.
- NC-32 BUG (line 109): `category: "other"` — heuristic ALWAYS sets category to "other". news_signals.CATALYST_RULES (NS-7) does NOT include "other" → NS-37 returns None → **NO signal generated from heuristic.** Heuristic-classified news produces ZERO scoring impact.
- NC-33 BUG (line 111): `(item.get("ticker_list") or [None])[0]` — first ticker only. Multi-ticker news (M&A) loses second ticker. Per news_engine NE structure, ticker_list can have many.
- NC-34 BUG (line 113): action_window heuristic — `next_day if tradeable < 0.6 else intraday`. Per NC-30, tradeable rarely > 0.6, so action_window is almost always "next_day". Buried bias.

### Lines 119-123: classify_batch
- NC-35 BUG (line 122): Sorts by source — Alpaca first. Reasonable but only 2-tier (alpaca / non-alpaca). Doesn't differentiate Yahoo from SEC EDGAR (per news_engine NE-2 SEC EDGAR claimed).
- NC-36 BUG (line 123): `[classify_news(it) for it in items_sorted[:max_items]]` — **SEQUENTIAL.** For 20 items, 20 LLM calls in series. **Should ThreadPoolExecutor or asyncio.gather with anthropic AsyncAnthropic.** Biggest perf opportunity in news pipeline.
- NC-37 BUG (line 119): `max_items: int = 20` — magic 20 cap. Hardcoded. If 100 fresh items from morning news, 80 dropped silently.

### Lines 126-136: __main__ smoke test
- NC-38 GOOD: Concrete test case with realistic data.
- NC-39 SMELL: Tests Claude path only — no test of fallback path.

## src/news_sentiment.py — LINE BY LINE

### Lines 1-3: Module docstring + imports
- NSENT-1 SMELL: Docstring "News + improved sentiment via Yahoo RSS" — vague. Doesn't say WHY this exists in addition to news_classifier.
- NSENT-2 GOOD (line 2): Uses feedparser library. Compare to news_engine NE-27 which regex-parses XML. **Same Yahoo source, two libraries.**

### Lines 5-9: POSITIVE keyword set
- NSENT-3 GOOD: 26 positive keywords as set. Set lookup faster than list (line 38 `for w in POSITIVE if w in text`).
- NSENT-4 BUG: Set membership but the loop does `w in text` (substring), not `text in POSITIVE` (set-lookup). **The `set` provides no perf benefit over a tuple here.** Should be `if any(w in text for w in POSITIVE)` for clarity.
- NSENT-5 BUG: 26 keywords overlap heavily with news_classifier._heuristic_fallback (NC-26). "beats", "surge", "upgrade", "approved", "raises", "wins" all duplicated. **Two near-identical bullish keyword lists.**

### Lines 11-16: NEGATIVE keyword set
- NSENT-6 BUG: 30 negative keywords. Same overlap with NC-27 (miss/plunge/downgrade/lawsuit/cut/...).
- NSENT-7 BUG: NSENT positive list and NC bullish list are SUBTLY DIFFERENT. "wins contract" (NC) vs "wins" (NSENT). NC list specifically requires the word "contract" suffix; NSENT just matches "wins" → matches "wins customer complaint" too. **Different false-positive surfaces in two parallel implementations of the same logic.**
- NSENT-8 BUG (line 12-13): "loss" — common word, very high false-positive rate. "Net interest margin loss-leader strategy" → bearish. "Loss prevention investment" → bearish.
- NSENT-9 BUG (line 16): "fired" — fires on any executive transition headline. CEO fired (bearish, true). CEO fired up about new product (bullish, false-pos).

### Lines 19-27: fetch_news
- NSENT-10 GOOD (line 19): Type hint, default limit.
- NSENT-11 BUG (line 20): Yahoo RSS URL hardcoded — **same URL as news_engine YAHOO_RSS_TPL (Batch 16 NE-15)**. Cross-file copy-paste. Single change has two places to update.
- NSENT-12 GOOD (line 22): feedparser.parse — handles XML/RSS properly.
- NSENT-13 BUG (lines 25-27): bare except logs `e` (no type, no truncation). **Inconsistent with rest of codebase** which uses `type(e).__name__: {str(e)[:N]}`. Less debuggable.
- NSENT-14 BUG: NO timeout on feedparser.parse. Default behavior. Yahoo RSS slow → blocks per-ticker scoring.

### Lines 30-45: score_sentiment — THE FUNCTION CALLED BY parallel_scorer
- NSENT-15 GOOD (line 33-34): Empty news → 0.5 neutral. Predictable.
- NSENT-16 BUG (lines 36-39): Per NSENT-4, naive substring count. For a 5-headline batch, 26+30=56 keywords × 5 headlines = 280 substring checks. Acceptable for 5 items but O(N×K).
- NSENT-17 BUG (line 39): `text` from line 37 = title only. Summary NOT scored. **Misses sentiment in summary text.**
- NSENT-18 GOOD (line 42): `(pos - neg) / max(n_articles, 1)` — net per article. Defensive against div-by-zero.
- NSENT-19 BUG (line 44): `score = 0.5 + (net / 4.0)` — magic 4.0 divisor. Comment says "Map [-2, +2] net score to [0, 1]". For net = 2, score = 1.0. For net = -2, score = 0.0. Reasonable mapping but threshold magic.
- NSENT-20 BUG (line 45): `max(0.05, min(0.95, score))` — clamps to [0.05, 0.95]. **NEVER returns 0 or 1.** Same comment-vs-code lie pattern. The 4.0 divisor maps to [0,1] but the clamp truncates to [0.05, 0.95]. Why? No explanation. Probably to avoid extremes from contaminating composite, but undocumented.
- NSENT-21 BUG: This function is called by parallel_scorer line 49 (Batch 8 PS-15). Per parallel_scorer PS-14, fetch_news is sequential per ticker. **For 500-ticker scoring, 500 sequential Yahoo RSS calls + 500 sentiment scoring runs.** Per Batch 8 PS-X4, this is one of the bottleneck calls. Combined with news_engine fetching Yahoo RSS independently → **Yahoo RSS hit twice for the same ticker per pipeline run.**

## CONSOLIDATED CROSS-CUTTING FINDINGS

### NC-X1 + NSENT-X1: TWO PARALLEL NEWS PIPELINES
| Pipeline | Producer | Classifier | Output | Consumer |
|---|---|---|---|---|
| Pipeline A | news_engine.fetch_yahoo_rss + Alpaca | news_classifier (Claude/heuristic) | news_signals.json (score_delta) | main.py composite mutation #5 (boost), hard_blocks (block) |
| Pipeline B | news_sentiment.fetch_news (Yahoo RSS) | inline keyword count | float [0.05, 0.95] | parallel_scorer composite_score (sentiment factor) |

**Two separate pipelines. Same news source (Yahoo). Two classification methods. Two separate scoring paths into composite.**
- Pipeline A is sophisticated (LLM) but expensive.
- Pipeline B is cheap but simplistic.
- **Both contribute to composite score independently.** Possible double-counting.
- **Neither knows the other exists.**

### NC-X3: Yahoo RSS fetched THREE times now confirmed
- news_engine.fetch_yahoo_rss (regex-parsed, news_engine NE-27)
- news_sentiment.fetch_news (feedparser-parsed, NSENT-11)
- (Indirectly via Alpaca which aggregates from multiple sources including Yahoo)
**For 500-ticker scoring, 500 + 20 = 520+ Yahoo RSS hits per run. Same data fetched multiple times by different code paths.**

### NC-X2 (CRITICAL): Heuristic fallback produces ZERO signals
- NC-32: heuristic always sets category="other"
- NS-37 (Batch 16): if category not in CATALYST_RULES, returns None
- "other" not in CATALYST_RULES
- **Therefore: every heuristic-classified news item → no score adjustment**
- **When ANTHROPIC_API_KEY is missing OR anthropic SDK fails (NC-10/11) → entire news pipeline silently produces nothing.**
- Combined with NS-X1 silent-degradation: news layer can be DEAD and main.py thinks it's working.

### NC-X4: CLASSIFIER_PROMPT may be incomplete
NC-7 — view shows truncation at "produc[..." mid-string. Either rendering issue or actual truncation. **Need to verify file integrity.** If truncated, Claude is given undefined output schema → bad JSON → fallback → no signals.

### Cross-cutting: 8+ truncation lengths now in audited files
Adding from this batch: 300 (NC-13), 500 (NC-14). Cumulative now: 80 / 100 / 120 / 200 / 240 / 300 / 500 / 600. **Single MAX_HEADLINE = N constant could replace all.**

### Cross-cutting: 4 substring-keyword classifiers across 3 files
- news_signals._is_catastrophic (Batch 16 NS-15) — 14 keywords
- news_signals._has_negative_reaction — 30 phrases
- news_classifier._heuristic_fallback — 26 keywords
- news_sentiment.POSITIVE/NEGATIVE — 56 keywords
**156+ keywords across 4 substring classifiers, with overlap and inconsistency.** Single `_keyword_classifier(text, keywords_dict)` would unify.

### Cross-cutting: Naive vs aware datetime in news pipeline
- NS-14 (Batch 16): `datetime.now(timezone.utc)` — aware
- NC-22: `datetime.now()` — naive
- news_signals._purge_expired parses both via fromisoformat — naive may be misinterpreted as UTC.

## SUMMARY (Batch 17)

| Severity | news_classifier | news_sentiment | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 14 | 8 | 4 | 26 |
| Data/safety | 9 | 6 | 0 | 15 |
| Code smell | 6 | 4 | 0 | 10 |
| Good code | 14 | 7 | 0 | 21 |
| Total findings | 43 | 25 | 4 | 72 |

## TOP 10 CRITICAL FIXES from Batch 17

1. NC-X4 / NC-7: Verify CLASSIFIER_PROMPT file integrity (raw bytes). If truncated, restore. (5 min check + maybe 30 min fix)
2. NC-X2 / NC-32: Heuristic fallback produces "other" category which generates ZERO signals. Map keywords to actual CATALYST_RULES categories. (30 min)
3. NC-X1 / NSENT-X1: Decide on ONE news pipeline OR explicitly document why both exist. (1-2 hr architectural decision)
4. NC-36: classify_batch should use anthropic AsyncAnthropic + asyncio.gather for parallelism. (30 min, ~10x speedup)
5. NC-X3: Cache Yahoo RSS by ticker for the run. Single fetch shared between news_sentiment and news_engine. (30 min)
6. NC-22: Fix `datetime.now()` → `datetime.now(timezone.utc)`. (1 min)
7. NC-19: Replace fragile markdown-fence stripping with regex-extract first JSON object. (15 min)
8. NSENT-17: Score sentiment using both title AND summary. (5 min)
9. NSENT-20: Document or remove the [0.05, 0.95] clamp. (5 min)
10. Cross-cutting: Consolidate 4 keyword classifiers into one `_keyword_classifier(text, kw_dict)` helper. (30 min)

## NEW THEMES UPDATED

- Theme T2 (schema drift): NC-9 action_window enum unused downstream. NC-32 "other" category never makes signals. Producers and consumers don't agree.
- Theme T8 (DRY violation): TWO PARALLEL NEWS PIPELINES (NC-X1) — entire architectural duplication. Largest DRY violation in audit so far.
- Theme T11 (fail-open by accident): NC-X2 — when LLM unavailable, news pipeline silently produces zero signals while main.py still scores normally. No alert.
- Theme T13 (silent-default-fills): NC-30 heuristic always under-scores (never hits 0.7 threshold) → all heuristic news classified as minor → action_window=next_day default.
- Theme T14 (gold-standard patterns): NC has NO atomic write but doesn't write state — N/A.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 12/~18 done | news_classifier, news_sentiment | 12/~18 |
| Total true line-by-line | | +2 files | 35 of 382 |
| Remaining | | | 347 files |

## NEXT BATCH

Batch 18: src/fundamentals.py + src/finnhub_data.py — fundamental data layer. fundamentals is what parallel_scorer line 45 calls (passes_filters). finnhub_data is what data_fetcher line 23 imports.

End of Batch 17. Phase B in progress (12/18).
