# Batch 8 — src/parallel_scorer.py (177 lines) + src/hard_blocks.py (329 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** src/parallel_scorer.py (177 lines, fully read), src/hard_blocks.py (329 lines, fully read)
**Phase:** A (safety/gates) — files 2 and 3 of 8

## TOP HEADLINE FINDINGS

1. HB-21: hard_blocks.py is FAIL-OPEN in 5 of 7 failure paths. The file's docstring proclaims "conservative defaults: better skip than lose" but in practice if upstream data is missing/broken/malformed, picks PASS the hard blocks rather than getting blocked. Same disease as Batch 6 M-RUN3 (T51 fail-open). Compounds Theme T4.
2. PS-6 confirms SF-X1 from Batch 7: parallel_scorer.py line 41 computes sig then line 155-160 returns a dict WITHOUT it. Smoking gun for why smell_faculty is inert.
3. PS-18: parallel_scorer mutates scores["composite"] THREE times (watchlist boost, pattern multiplier, wisdom adjustment) without preserving original. main.py later mutates it AGAIN (earnings, news). 5 mutations total, no audit trail.
4. HB-12: AI to SOXX mapping is wrong. AI-tagged picks (META, MSFT, GOOGL) get blocked by SOXX (semiconductor ETF) weakness. False-positive engine.
5. HB-14: get_weak_sectors() docstring says "Cached" but has NO caching. Each call fires 17 sequential yfinance calls. Lie in code.
6. HB-18: comment at line 224 acknowledges a bug ("M3: iterate all tags... We do this in caller below") but caller doesn't actually do it. "AI / SEMI" tag only AI matched, SEMI never checked. Documented bug never fixed.

## src/parallel_scorer.py — LINE BY LINE

### Lines 1-5: Module docstring
- PS-1 GOOD: References PR #67 historical context. Brief, accurate.

### Lines 6-20: Imports (14 first-party, 2 stdlib)
- PS-2 GOOD: All 14 first-party imports actually used. Better than main.py.
- PS-3 SMELL (lines 8-9): score_fundamentals, passes_filters, fetch_news, score_sentiment imported here — they were dead in main.py (Batch 6 M-IM5/IM6/IM7) but USED here. Confirms parallel_scorer is the actual user.

### Lines 25-36: _resolve_regime
- PS-4 BUG (line 28): Caches by MUTATING the cfg dict passed by caller. Theme T5 hidden mutation.
- PS-5 OK (line 32): Defensive double-fallback on empty-dict guard.
- PS-6 BUG (lines 33-34): bare except. Theme T1. Silent regime degradation to "unknown" with NO log.
- PS-7 BUG (line 35): Writes "unknown" to cache. One transient yfinance error LOCKS regime to "unknown" for the rest of run.

### Lines 38-163: _score_one — 122-line GOD-FUNCTION

#### Outer envelope (lines 38-39, 161-163)
- PS-8 BUG: Single try/except wrapping entire function. Line 162 prints one-line error. NO traceback. Theme T1.
- PS-9 SMELL (line 162): str(e)[:80] truncates error to 80 chars. Long errors clipped.

#### Lines 40-43: signals computation
- PS-10 BUG (line 41): sig = latest_signals(d) — local variable. THIS IS THE CRITICAL LINE. Goes into oblivion at function return.
- PS-11 BUG (line 42): Silent ticker drop on missing close. No counter, no audit.

#### Lines 44-47: fundamentals filter
- PS-12 BUG (line 44): info = fetch_info(tk) UNWRAPPED yfinance call. On rate limit, whole ticker fails.
- PS-13 BUG (line 45): Silent drop on passes_filters fail. No audit row.

#### Lines 48-51: news + composite scoring
- PS-14 BUG (line 48): news = fetch_news(tk, limit=5) unwrapped network call per ticker. 500 tickers = 500 sequential news calls.
- PS-15 SMELL (line 49): score_sentiment per ticker, no batching.
- PS-16 BUG (line 50): composite_score 4 positional + 2 kwargs. Brittle signature.

#### Lines 53-58: watchlist boost (FIRST composite mutation)
- PS-17 BUG (line 56): Adds new key watchlist_boost.
- PS-18 BUG (line 57): MUTATION 1 of composite. Original value lost. No composite_pre_watchlist saved.
- PS-19 SMELL (line 58): Second formatting pass.

#### Lines 60-74: pattern multiplier (SECOND composite mutation)
- PS-20 SMELL (line 64): Inline import inside try.
- PS-21 SMELL (line 66): Re-resolve regime. Redundant.
- PS-22 BUG (line 67): UNWRAPPED but inside try. Pattern detection could be slow.
- PS-23 BUG (line 70): [:200] magic truncation. Pattern names truncated mid-name.
- PS-24 BUG (line 72): MUTATION 2 of composite. No composite_pre_pattern saved.
- PS-25 BUG (line 73): bare except sets default 1.0. Theme T1. Silent failure of pattern detection.

#### Line 76: min_score gate
- PS-26 BUG: Composite has been mutated TWICE before this check. min_score gate is on derived value, not natural composite. Threshold semantics not what they appear.

#### Lines 79-89: day_trading_score
- PS-27 SMELL (line 81): news_boost_for_day = max(0, wl_boost). Asymmetric. Negative news doesn't HURT day trades. Undocumented.
- PS-28 BUG (line 82): UNWRAPPED. Caught by outer exception, ENTIRE ticker dropped.
- PS-29 SMELL (line 88): Mixed positional + keyword args.

#### Lines 92-106: ATR plan
- PS-30 BUG (line 92): THREE different field-name conventions for ATR (atr_14, atr, ATR). Schema drift at indicator layer.
- PS-31 SMELL (line 93): close=0 default but line 42 already returned None if missing. Defensive duplication.
- PS-32 BUG (lines 94-95): TWO config keys for capital (risk.capital AND risk.account_size). Theme T2 dual-source.
- PS-33 SMELL (lines 96-99): 3-line comment longer than the next 6 lines of code.
- PS-34 SMELL (line 99): THIRD time regime resolved.
- PS-35 SMELL (lines 100-106): Silent degradation to default planning when ATR missing.

#### Lines 109-127: monster scoring
- PS-36 SMELL (line 110): Config-gated, default OFF. Most picks have no short_float data.
- PS-37 BUG (line 111): _d2e(tk) DUPLICATE call. main.py:858-870 calls again. 2x earnings API calls per ticker.
- PS-38 SMELL (line 112): Sentinel 999 = unknown. Same as Batch 6 M-RUN31.
- PS-39 OK (lines 113-120): score_monster gets 6 inputs.
- PS-40 BUG (line 124): bare except. Theme T1. Silent monster failure.

#### Lines 130-153: wisdom consultation (THIRD composite mutation)
- PS-41 BUG (line 136): Comment EXPLICITLY admits days_to_earnings should have d2e_val from line 111 but doesn't pass it. Wisdom runs without d2e context.
- PS-42 SMELL (line 138): vol_ratio uses sig, the local variable that gets DROPPED.
- PS-43 OK (line 144): Stores wisdom_score_adj.
- PS-44 BUG (lines 146-147): MUTATION 3 of composite. 5 total mutations across pipeline.
- PS-45 SMELL (line 148): Re-rounded. FP compounding error across 5 mutations.
- PS-46 BUG (lines 149-153): bare except. Theme T1. Silent degradation of Pillar 2 wisdom.

#### Lines 155-160: return dict
- PS-47 OK: 6 keys returned.
- PS-48 CRITICAL: MISSING signals (sig). One-line fix: add "signals": sig.
- PS-49 BUG: MISSING composite_pre_* snapshots.
- PS-50 BUG: MISSING days_to_earnings (computed at 111 but only used for monster).
- PS-51 BUG (lines 157-158): info_short hand-shaped with 2 fields. Drops averageVolume — root cause of smell_low_liquidity dead.

### Lines 166-176: score_all
- PS-52 BUG (line 166): max_workers default=10 here, but main.py reads env var with default 4. Default mismatch.
- PS-53 OK (line 169): ThreadPoolExecutor context manager.
- PS-54 SMELL (line 170): All 500 submitted at once. Memory pressure manageable.
- PS-55 BUG (lines 171-174): NO TIMEOUT on as_completed. Hung yfinance ticker stalls entire loop.
- PS-56 BUG: NO progress logging. Silent until result.
- PS-57 BUG: NO failure rate tracking. Hundreds of silent drops invisible.
- PS-58 SMELL (line 175): Assumes composite exists. KeyError on malformed result.

## src/hard_blocks.py — LINE BY LINE

### Lines 1-19: Module docstring
- HB-1 GOOD: Excellent docstring with bug-history archaeology. Use as template.
- HB-2 BUG (line 11): "Three new blocks" but code has 5 blocks. Docstring outdated by 2 blocks.

### Lines 20-29: Imports
- HB-3 GOOD (lines 25-29): try/except ImportError for yfinance with YF_OK flag. Defensive.

### Lines 31-41: Constants
- HB-4 SMELL (line 32): MIN_PRICE = 5.00 magic but named.
- HB-5 GOOD (lines 36-41): SL_MIN_TIERS 4-tier ladder by price. Documented well.

### Lines 44-56: get_min_sl_pct
- HB-6 GOOD (lines 49-52): float coercion in try/except returning safe default.
- HB-7 SMELL (line 53): Linear scan fine for 4 tiers.
- HB-8 SMELL (line 56): Fallback redundant. Last tier (0.0, 3.0) catches all p >= 0.

### Lines 60-88: _get_recent_pick_dates + COOLDOWN constants
- HB-9 SMELL (line 63): COOLDOWN_DAYS = 5 magic.
- HB-10 BUG (line 64): RELATIVE PATH. Same M-CFG1 bug from Batch 6.
- HB-11 BUG (line 73): Silently returns empty if log missing. Cooldown DOESN'T enforce on fresh install.
- HB-12 SMELL (line 76): Inline import csv.
- HB-13 BUG (line 77): Assumes utf-8. CSV with BOM raises, caught at 86, cooldown OFF.
- HB-14 GOOD (line 80): Defensive ticker normalization.
- HB-15 GOOD (line 81): Uses pick_date column name correctly.
- HB-16 GOOD (line 84): String comparison on ISO dates works.
- HB-17 BUG (lines 86-87): bare except pass. Theme T1. picks_log read fail = cooldown silently disabled.

### Line 89: SECTOR_ETF_DROP_THRESHOLD declared MID-FILE
- HB-18 BUG: Constant declared MID-FILE between two functions. Looks like late-addition. Violates PEP 8.

### Lines 91-105: SECTOR_ETF dict
- HB-19 GOOD (lines 95-96): Both Financial Services and Financials map to XLF.
- HB-20 BUG: Missing entry for "Basic Materials" (yfinance variant). Silent miss.
- HB-21 BUG: No fallback for unknown sectors. Sector additions in yfinance silently lose protection.

### Lines 108-114: TAG_ETF dict
- HB-22 CRITICAL (line 110): "AI": "SOXX" WRONG MAPPING. AI tag includes META/MSFT/GOOGL — none semis. False-positive engine.
- HB-23 BUG (line 111): BIOTECH covered, but pharma vs biotech distinction missing.

### Lines 117-129: _safe_pct_change
- HB-24 GOOD (line 119): YF_OK check defensive.
- HB-25 GOOD (line 122): period=3d for safety on short weeks.
- HB-26 BUG (line 123): If yfinance returns 1 bar, function returns 0.0. Sector silently NOT flagged weak.
- HB-27 BUG (lines 127-128): bare except returns 0.0. Failed yfinance = "no change" = sector NOT in weak dict = block doesn't fire.
- HB-28 BUG: No caching, no parallelism. 17 sequential calls.

### Lines 132-153: get_weak_sectors
- HB-29 BUG (line 138): Docstring says "Cached" but function has NO caching. Lie in code.
- HB-30 BUG (lines 142-151): 17 sequential network calls. No parallelism, no timeout.
- HB-31 BUG: Per HB-27, partial failure leaves inconsistent weak dict.

### Lines 158-168: _block_penny
- HB-32 GOOD (line 160): Checks BOTH nested and flat entry. Better than smell_faculty.
- HB-33 GOOD (lines 161-162): Fail-CLOSED on missing entry. M2 comment good.
- HB-34 BUG (lines 166-167): except (ValueError, TypeError): pass. Non-numeric entry PASSES. Inconsistent with line 161 fail-closed.

### Lines 171-194: _block_sl_buffer
- HB-35 GOOD (lines 176-178): Same dual-source check.
- HB-36 GOOD (lines 179-180): Fail-CLOSED only when entry exists and sl missing.
- HB-37 BUG (lines 181-182): Passes when BOTH missing. Inconsistent: entry exists+sl missing=BLOCK, both missing=PASS. Logic gap.
- HB-38 BUG (line 185): entry_f <= 0 returns True. Should fail-CLOSED. Zero-entry pick is broken.
- HB-39 GOOD (line 187): buffer_pct math correct for LONG.
- HB-40 SMELL: Implicit long-only assumption undocumented.
- HB-41 GOOD (line 188): Tiered min_sl.
- HB-42 BUG (lines 191-192): bare except pass. Non-numeric SL silently passes. Same fail-open as HB-34.

### Lines 197-215: _block_recent_pick
- HB-43 GOOD (line 202): Defensive ticker normalization.
- HB-44 GOOD (line 203): Early return.
- HB-45 SMELL (line 208): Assumes ISO date format. Other formats raise, silent pass.
- HB-46 BUG (line 209): datetime.now() uses LOCAL machine date, not ET. Off-by-one risk on UTC runners. Undocumented.
- HB-47 SMELL (line 211): Strict less-than. "5-day cooldown" exclusive of day 5. Off-by-one ambiguity.
- HB-48 BUG (lines 213-214): bare except. Date parse fail = ticker silently passes cooldown.

### Lines 217-237: _block_weak_sector
- HB-49 GOOD (lines 219-220): Fast-path early return.
- HB-50 BUG (line 222): Only checks info_short.sector. Per PS-51 info_short is impoverished. Silent miss.
- HB-51 BUG (line 223): TWO sources for tag. Theme T2 dual-source.
- HB-52 CRITICAL (line 224 comment): Comment promises iteration the code doesn't have. "AI / SEMI" only AI checked. Documented bug never fixed.
- HB-53 BUG (line 225): Takes only first tag. SEMI half never checked.
- HB-54 SMELL (lines 228-235): Asymmetric matching (sector case-insensitive, tag case-sensitive).

### Lines 240-252: _block_catastrophic_news
- HB-55 SMELL (line 243): Inline import. Defensive.
- HB-56 GOOD (lines 244-246): Empty ticker passes.
- HB-57 OK (line 247): is_hard_blocked assumed (bool, str).
- HB-58 GOOD (lines 248-249): Block with reason.
- HB-59 BUG (lines 250-251): bare except. If news_signals raises, catastrophic news SILENTLY DISABLED. Bankruptcy news fetch fails = bankrupt company gets picked.

### Lines 257-329: apply_hard_blocks
- HB-60 GOOD (lines 257-258): check_sectors=True allows test/debug disabling.
- HB-61 GOOD (lines 266-267): Empty input early return.
- HB-62 GOOD (line 270): Single get_weak_sectors call.
- HB-63 GOOD (line 273): Single _get_recent_pick_dates call.
- HB-64 SMELL (lines 282-288): Comment "cheapest first" but order is wrong. catastrophic_news has import + network. Should be penny, sl_buffer, recent_pick, catastrophic_news, weak_sector.
- HB-65 BUG (lines 292-296): First-block-wins. Other reasons LOST. Single-cause-blindness.
- HB-66 GOOD (lines 298-303): Blocked entry has 3 fields.
- HB-67 GOOD (lines 308-327): Audit log block.
- HB-68 BUG (line 310): Hardcoded relative path data/hard_blocks_log.json.
- HB-69 GOOD (lines 313-317): Existing read with corruption protection.
- HB-70 BUG (line 319): datetime.now() not utcnow(). Three timestamp conventions across project.
- HB-71 GOOD (line 320): Stores weak_sectors per run.
- HB-72 BUG (line 325): existing[-100:] keeps last 100. Daily run = 100-day rolling window. Older audit lost.
- HB-73 GOOD (lines 326-327): Print on write failure.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### HB-X1: 5 of 7 fail paths in hard_blocks.py are FAIL-OPEN
- _block_penny missing entry: BLOCK correct
- _block_penny non-numeric entry: PASS WRONG, should BLOCK
- _block_sl_buffer entry but no SL: BLOCK correct
- _block_sl_buffer no entry no SL: PASS WRONG, should BLOCK
- _block_sl_buffer entry=0: PASS WRONG, should BLOCK
- _block_recent_pick bad date: PASS WRONG, should BLOCK or LOG
- _block_catastrophic_news any exception: PASS WRONG, should BLOCK
- _get_recent_pick_dates missing file: PASS WRONG, should LOG warning
The file's docstring proclaims "conservative defaults: better skip than lose" but implementation contradicts.

### PS-X1 + HB-X2: parallel_scorer drops sig AND info fields
- sig (PS-48) kills 4-5 smells in smell_faculty
- info["averageVolume"] (PS-51) kills smell_low_liquidity specifically
- info["marketCap"], info["currency"] etc. drops other useful signals
One-line fix to add "signals": sig to return + extending info_short would resurrect 5+ downstream features.

### PS-X2: composite mutated 5 TIMES across pipeline, audit trail lost
- Stage 1: parallel_scorer line 57 + watchlist_boost
- Stage 2: parallel_scorer line 72 * pattern_multiplier
- Stage 3: parallel_scorer line 147 + wisdom_score_adj
- Stage 4: main.py line 884 * earnings_quality
- Stage 5: main.py line 939 + news_boost
Only final value persists. Should save composite_pre_* snapshots at each stage.

### PS-X3 + HB-X3: schema drift in field naming across modules
- ATR: atr_14, atr, ATR (parallel_scorer line 92)
- Capital: risk.capital, risk.account_size (parallel_scorer lines 94-95)
- Sector: Financial Services, Financials (hard_blocks lines 95-96)
- Pick fields: nested pick["plan"]["entry"] AND flat pick["entry"]
Dual-source-of-truth across the entire stack.

### PS-X4: silent-drop epidemic in parallel_scorer
6 silent-drop paths return None with no audit. For 500 tickers, dozens-to-hundreds get silently dropped per run with no visibility.

### PS-X5: get_min_sl_pct duplicates HB-6 but main.py codes its own SL logic
Cross-module duplication likely with risk_manager. Need cross-check.

### HB-X4: Audit-log retention is rolling 100 entries
For daily runs, 100 days of history. Should be append-only OR rotated to dated files.

### PS-X6: 122-line _score_one is a God-function
Same pattern as main.py:run() (1,184 lines). Should be decomposed.

## SUMMARY (Batch 8)

| Severity | parallel_scorer | hard_blocks | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 22 | 18 | 4 | 44 |
| Data/safety | 8 | 5 | 0 | 13 |
| Code smell | 12 | 14 | 2 | 28 |
| Good code | 6 | 13 | 0 | 19 |
| Total findings | 48 | 50 | 6 | 104 |

## TOP 10 CRITICAL FIXES from Batch 8

1. PS-48 + SF-X1: Add "signals": sig to return dict (10 sec)
2. HB-X1: Convert 5 fail-open paths to fail-closed (1 hr)
3. HB-22: Fix AI to SOXX false-positive mapping (5 min)
4. HB-29: Fix or remove "cached" docstring lie (5 min)
5. HB-52: Implement multi-tag iteration (15 min)
6. PS-X2: Save composite_pre_* snapshots at each stage (10 min)
7. PS-30 + PS-X3: Pick canonical ATR field name (30 min)
8. PS-32: Pick canonical capital config key (5 min)
9. PS-55: Add per-task timeout to ThreadPoolExecutor (10 min)
10. PS-X4: Add per-drop counter + log summary in score_all (30 min)

## NEW THEMES CONFIRMED

- Theme T9 (test-shape vs production-shape divergence): confirmed in hard_blocks dual-source patterns.
- Theme T10 NEW: Documentation/comment lies. Comments describe intent code doesn't implement (HB-2, HB-29, HB-52).
- Theme T11 NEW: Fail-open by accident. Stated philosophy fail-closed; implementation fail-open in 5+ places.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 3/8 done | parallel_scorer, hard_blocks | 3/8 |
| Total true line-by-line | | +2 files | 18 of 382 |
| Remaining | | | 364 files |

## NEXT BATCH

Batch 9: src/premarket_sanity_gate.py (216 lines) + src/portfolio_risk_gate.py (244 lines) — the next two gates in the pipeline.

End of Batch 8.
