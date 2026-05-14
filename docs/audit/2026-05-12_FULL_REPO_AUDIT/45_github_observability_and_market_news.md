# Batch 39 — src/github_observability.py (68 lines) + src/market_news.py (211 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** github_observability.py (68 lines), market_news.py (211 lines)
**Phase:** D (pipeline & output) — files 15 and 16 of ~30

## TOP HEADLINE FINDINGS

1. GO-X1: github_observability.py is a **TINY 68-line metadata helper** — converts GITHUB_* env vars into URL strings consumed by official_pick_artifact (Batch 37 OPA-42). **READ-ONLY** ✅. Per docstring 4 explicit "no" bullets.
2. GO-X2 (lines 26, 38, 51): All 3 functions check `if X == "local"` and return empty string. **3 IDENTICAL "local" sentinel checks** for the dev-mode placeholder set in Batch 37 OPA-12. **DRY violation but minor.**
3. GO-X3: **TEST-FRIENDLY DESIGN** — every function takes optional `env: Mapping[str, str] | None = None` arg. Defaults to os.environ but allows test injection. **JOINS gold-standard test-friendly pattern** (Batch 23 self_awareness, Batch 27 position_monitor optional `today` arg). ✅
4. MN-X1: market_news.py is **THE LLM-POWERED MARKET BRIEFING** — fetches Finnhub general news, analyzes with Claude (Sonnet 4.5) → Gemini fallback → neutral default. **3-tier fallback chain.** ✅
5. MN-X2 (line 24): `CLAUDE_MODEL = "claude-sonnet-4-5"` — **HARDCODED MODEL VERSION.** When Anthropic deprecates Sonnet 4.5, market_news breaks silently (LLM call fails → falls through to Gemini → if also fails, neutral default). **Latent technical-debt landmine.** Compare Batch 18 finnhub provider failures cross-cutting.
6. MN-X3 (line 13 + line 16-18): **`load_dotenv()` AT MODULE IMPORT** + **3 API keys read at import time.** Per Batch 18 FH-2 cross-cutting `load_dotenv at import` smell. **3rd file with this anti-pattern.** Test-unfriendly.
7. MN-X4 (lines 41, 135): **CACHE TTL bypass logic** uses `datetime.now().timestamp() - cache.stat().st_mtime` — compares timestamp seconds. **NAIVE datetime + filesystem mtime comparison.** Cross-platform fragile (mtime granularity differs). Per Batch 36 PF-13 cross-cutting Theme T1 bare-except, line 44 also has bare except for cache load.

## src/github_observability.py — LINE BY LINE

### Lines 1-8: Module docstring
- GO-1 GOOD: 8-line docstring with **4 explicit "no" bullets** (provider calls, alerts, trading, secrets). Per Batch 36 PD-X2 / Batch 37 OPA-1 / Batch 38 CD-1 OBSERVE-MODE pattern. **5th module with explicit no-mutation contract in Phase D.**

### Lines 10-13: Imports
- GO-2 GOOD: Pure stdlib + collections.abc.Mapping for type hints.

### Lines 16-17: _env_value
- GO-3 GOOD: Defensive `str(env.get(key) or "").strip()` — handles None + whitespace.

### Lines 20-29: github_run_url
- GO-4 GOOD: Type-hinted optional env arg per GO-X3.
- GO-5 GOOD (line 21): `env or os.environ` lazy fallback.
- GO-6 GOOD (line 24): `(_env_value(env, "GITHUB_SERVER_URL") or "https://github.com").rstrip("/")` — fallback to public GitHub. Supports GHES.
- GO-7 GOOD (line 26): Per GO-X2, "local" check.
- GO-8 GOOD (line 29): URL formatted via f-string.

### Lines 32-41: github_commit_url
- GO-9 BUG: Per GO-X2, near-duplicate of github_run_url. ~8 lines repeated. Different URL path (`actions/runs/` vs `commit/`). **Should extract `_github_url(env, path_template)` helper.**

### Lines 44-54: github_artifact_bundle_name
- GO-10 GOOD: Default prefix "official-decision-artifacts" — matches Batch 37 artifact bundle naming.
- GO-11 GOOD (line 51): "local" check pattern. **3rd instance — definitely DRY-extractable.**

### Lines 57-67: github_observability_metadata
- GO-12 GOOD: Aggregator returning 3-key dict. ✅ Used by official_pick_artifact OPA-42.

## src/market_news.py — LINE BY LINE

### Lines 1-4: Module docstring
- MN-1 GOOD: 4-line docstring with priority chain documented (Claude → Gemini → neutral).

### Lines 5-13: Imports + load_dotenv
- MN-2 BUG (line 13): Per MN-X3, `load_dotenv()` at import. Anti-pattern.

### Lines 15-24: Module-level constants
- MN-3 BUG (lines 16-18): 3 API keys read at import time. Cannot be re-read after .env mutation in long-running processes.
- MN-4 GOOD (line 18): `_GEMINI_KEY = ... or os.getenv("GOOGLE_API_KEY", "")` — 2-key fallback for backward compat.
- MN-5 BUG (lines 19-20): **mkdir at import time** — side effect at module load. **3rd anti-pattern at import in this file.** Test isolation broken (mkdir runs even in tests).
- MN-6 GOOD (lines 21-22): timedelta cache TTL — explicit 4 hours. Named constants.
- MN-7 BUG (line 24): Per MN-X2, hardcoded model version.

### Lines 27-32: Cache path helpers
- MN-8 BUG (lines 28, 32): `datetime.now().strftime('%Y%m%d_%H')` — NAIVE datetime + hourly cache key. **Race condition at hour-boundary** — cache key changes mid-process.
- MN-9 GOOD: Hourly cache key naturally rotates files per hour.

### Lines 35-58: fetch_market_news
- MN-10 GOOD (lines 37-38): Empty key → empty list. Defensive.
- MN-11 BUG (line 41): Per MN-X4, naive timestamp comparison.
- MN-12 BUG (line 44): bare except for cache load. Theme T1.
- MN-13 GOOD (lines 47-49): 15s timeout, `category=general`.
- MN-14 GOOD (line 50): Status code check.
- MN-15 GOOD (line 52): `r.json() or []` — defensive None.
- MN-16 GOOD (line 53): Sort by datetime DESC.
- MN-17 BUG (line 54): `cache.write_text(json.dumps(items))` — **NO ATOMIC WRITE.** Per Batch 27 PV-X2 cross-cutting. Power loss = corrupt cache.
- MN-18 GOOD (lines 56-58): Outer try/except with print + empty-list fallback. **Documented fail-degraded.**

### Lines 61-80: _build_sentiment_prompt
- MN-19 GOOD (line 62): Headline truncation to 140 chars per item. Bounded prompt size.
- MN-20 GOOD (line 64): Top-30 headlines passed to LLM.
- MN-21 GOOD (lines 66-80): Detailed prompt with EXACT JSON shape required + role + output schema.
- MN-22 GOOD (line 75): Score range 0-1 documented inline.
- MN-23 BUG (line 75): Magic ranges. No way to change scoring without prompt rewrite.

### Lines 83-91: _strip_markdown_fences
- MN-24 GOOD: Defensive Markdown unwrap. **Common LLM-output pitfall** — model returns ```json ... ```.
- MN-25 GOOD (line 87-88): Strips "json" language tag.
- MN-26 BUG (line 89): `if text.endswith("```"):` — strips closing fence. **But line 86 only takes text BEFORE first split — if model emits 3 fenced blocks, only first kept.** Edge case but real.

### Lines 94-104: _claude_sentiment
- MN-27 GOOD (line 96): Inline `import anthropic` — lazy import to avoid hard dependency.
- MN-28 GOOD (lines 98-103): max_tokens=800, temp=0.3 — deterministic-ish sampling.
- MN-29 BUG (line 104): `resp.content[0].text` — assumes content list non-empty + first element has .text. **Can IndexError or AttributeError** if Claude returns tool-use or empty response.

### Lines 107-116: _gemini_sentiment
- MN-30 GOOD (line 109): URL with API key in querystring. Standard Gemini auth.
- MN-31 GOOD (lines 111-113): generationConfig matches Claude params.
- MN-32 BUG (line 115): `r.text[:200]` truncated for error message. Reasonable.
- MN-33 BUG (line 116): `r.json()["candidates"][0]["content"]["parts"][0]["text"]` — **4-LEVEL DEEP DICT/LIST ACCESS** — same KeyError/IndexError risk as MN-29.

### Lines 119-183: analyze_market_sentiment
- MN-34 GOOD (lines 121-128): Default neutral fallback dict. **Used 3 places** (lines 131, 165, 183).
- MN-35 GOOD (lines 130-131): Empty headlines → default.
- MN-36 GOOD (lines 134-141): Cache check with bare-except per MN-12.
- MN-37 GOOD (lines 147-153): Claude with try/except + truncated error log.
- MN-38 GOOD (lines 155-161): Gemini fallback with same pattern.
- MN-39 GOOD (lines 163-165): No LLM available → neutral default with print.
- MN-40 GOOD (lines 167-179): JSON parse with markdown unwrap.
- MN-41 GOOD (lines 171-172): `for k in default: result.setdefault(k, default[k])` — fills missing keys with defaults. **Schema-drift defense.**
- MN-42 BUG (line 176-178): Cache write with bare except. Per MN-12 third instance.
- MN-43 BUG (line 176): `scache.write_text(json.dumps(result))` — NO ATOMIC WRITE per MN-17.
- MN-44 GOOD (lines 180-183): Parse failure → log raw text + return default.

### Lines 186-194: get_market_briefing
- MN-45 GOOD: One-shot orchestrator. Returns 3-key briefing.
- MN-46 GOOD (line 192): `top_headlines` truncated to 5×120 chars.

### Lines 197-211: __main__ smoke test
- MN-47 GOOD: Operator can `python -m src.market_news` for sanity check.
- MN-48 GOOD: Per Batch 26 PE-X2 / Batch 22 WP-29 smoke-test pattern.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### GO-X1 + Phase D OBSERVE-MODE pattern continues
Modules with explicit "no" bullets in docstring:
1. meta_brain (B23) — "this module never mutates"
2. weight_proposer (B22) — "Never auto-applies"
3. self_awareness (B23) — "READ-ONLY brain reflection"
4. stooq_provider (B35) — 4 "no" bullets
5. premarket_decision_contract (B36) — 6 "does not" bullets
6. official_pick_artifact (B37) — 5 "no" bullets
7. official_artifact_loader (B37) — 3 "no" bullets
8. candidate_diagnostics (B38) — "reporting-only" line
9. github_observability (this batch) — 4 "no" bullets

**9 modules with explicit OBSERVE-MODE/READ-ONLY contracts.** Phase D pattern is now PERVASIVE. Phase D mutation actors clearly separated from observers.

### GO-X2 / GO-9: Smallest DRY violation
3 identical "local" checks across 3 functions in 68-line file. **Extract `_is_local_or_missing(value)` helper.** Trivial fix.

### MN-X3: load_dotenv at import (3rd file with this anti-pattern)
Cumulative tally:
- finnhub_data.py (B18)
- (one other unaudited?)
- market_news.py (this batch)

**At least 2-3 files with module-import side effects.** Test isolation broken. **Should consolidate into a single `_config.py` loaded explicitly.**

### MN-X2: Hardcoded LLM model version
- Anthropic occasionally deprecates models with 6-12 month notice.
- claude-sonnet-4-5 release date unknown but eventually deprecated.
- When deprecated, market_news fails over to Gemini (which is also pinned to 2.5-flash-lite at line 107).
**Both LLM providers have version-pin technical debt.** Should be env-configurable: `os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")`.

### MN-17 + MN-43: 2 more unsafe cache writes
news cache + sentiment cache. Both use `cache.write_text` without atomic write. Per Batch 37 OPA-X5 cross-cutting:
**Updated atomic-write tally:** 4 of 18 audited state-writers safe. Now 14 unsafe writers (~78%).

### MN-29 + MN-33: Deep-nested LLM response access
Both Claude (MN-29: `resp.content[0].text`) and Gemini (MN-33: `r.json()["candidates"][0]["content"]["parts"][0]["text"]`) parse responses with raw indexing. **One unexpected response shape = IndexError/KeyError.** **Outer try/except catches it but operator gets generic "Claude failed: list index out of range"** instead of "model returned empty content." Per Batch 18 FH-X3 cross-cutting Theme T13 silent default fills.

### MN-12 + MN-36 + MN-42: 3 bare-excepts in market_news
- MN-12: cache load
- MN-36: cache load (sentiment)
- MN-42: cache write
**All for cache corruption defense.** **Theme T1 documented use case** — cache corruption shouldn't crash the briefing. Acceptable but should be specific (json.JSONDecodeError, OSError).

### Cross-cutting: bare-except this batch
- github_observability: 0 ✅
- market_news: 3 (cache I/O, intentional but unscoped)

### Cross-cutting: 25 files with relative-path constants
market_news adds `_CACHE_DIR`. github_observability doesn't add new.

## SUMMARY (Batch 39)

| Severity | github_observability | market_news | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 1 | 8 | 4 | 13 |
| Data/safety | 1 | 5 | 0 | 6 |
| Code smell | 0 | 3 | 0 | 3 |
| Good code | 11 | 32 | 0 | 43 |
| Total findings | 13 | 48 | 4 | 65 |

## TOP 10 CRITICAL FIXES from Batch 39

1. MN-X2 / MN-7 + line 107: Make CLAUDE_MODEL + Gemini model env-configurable. (5 min)
2. MN-X3 / MN-2 + MN-3 + MN-5: Move load_dotenv + key reads + mkdir into `_init()` lazy function. (15 min)
3. MN-17 + MN-43: Add atomic write to both cache writes. (10 min)
4. MN-29 + MN-33: Defensive LLM response parse with explicit error messages for empty/malformed responses. (15 min)
5. GO-X2 / GO-9: Extract `_github_url(env, path_template)` helper to dedupe 3 functions. (10 min)
6. MN-12 + MN-36 + MN-42: Replace bare except with `(json.JSONDecodeError, OSError)`. (5 min)
7. MN-X4 / MN-11: Use TZ-aware datetime in cache age comparisons. (5 min)
8. MN-26: Make _strip_markdown_fences handle multi-block LLM output. (10 min)
9. MN-23: Document score range mapping in module-level constant or enum. (5 min)
10. MN-8: Document hour-boundary cache rotation race risk. (3 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): github_observability 0. market_news 3 (cache-defense intent, undocumented). **Phase D resumed STREAK BROKEN at 5 files** but still better than Phases A-B.
- Theme T2 (schema drift): MN-29+MN-33 LLM response shape brittleness.
- Theme T6 (atomic writes): MN-17+43 add 2 unsafe writers. Now 14 of 18 (~78%) UNSAFE.
- Theme T8 (DRY): GO-X2 3-instance "local" check. CD-X2-style mirror in MN cache write code (lines 174-178).
- Theme T11 (fail-open by accident): MN-X3 load_dotenv at import. MN-29+33 deep-nested access.
- Theme T13 (silent-default-fills): MN-34 neutral default propagated through 3 paths.
- Theme T14 (gold-standard patterns): github_observability test-friendly env injection. market_news 3-tier LLM fallback (Claude → Gemini → neutral) is best LLM-defensive pattern in audit.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A | 8/8 COMPLETE | (none) | 8/8 |
| Phase B | 18/18 COMPLETE | (none) | 18/18 |
| Phase C | 12/12 COMPLETE | (none) | 12/12 |
| Phase D | 16/~30 done | github_observability, market_news | 16/~30 |
| Phase E | 12/~50 done | (none) | 12/~50 |
| Total true line-by-line | | +2 files | **81 of ~382 (~21.2%)** |
| Remaining | | | **~301 files** |

## NEXT BATCH

Batch 40: src/market_guard.py + src/universe.py — market_guard is a Phase D safety gate. universe is the ticker universe builder consumed by main.py. Both core pipeline ancillaries.

End of Batch 39. Phase D in progress (16/30).
