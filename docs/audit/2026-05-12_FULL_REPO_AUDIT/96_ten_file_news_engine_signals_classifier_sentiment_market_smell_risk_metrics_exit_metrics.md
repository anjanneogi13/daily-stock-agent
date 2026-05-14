# Batch 96 — 10-FILE BATCH — TRUE LINE-BY-LINE — NEWS PIPELINE + SMELL + RISK + EXIT

**Date:** 2026-05-14  
**Commit ref:** 37565c4d757a9f819a3ddd2059f73a51bb98af49  
**Files (10):** news_engine (163) + news_signals (384) + news_classifier (136) + news_sentiment (46) + market_news (211) + smell_faculty (271) + risk_manager (126) + risk_metrics (167) + exit_manager (63) + exit_metrics (173)  
**Phase:** H continuation — NEWS + SMELL + RISK + EXIT CORE  
**Total LOC audited this batch:** ~1,740 lines  
**Reliability:** ✅ All 10 files actually fetched at the listed commit and audited line-by-line.

---

## TOP HEADLINE FINDINGS

1. **NE-X1: news_engine.py** (163) — Multi-source news puller (Alpaca primary, Yahoo RSS backup). **TZ-aware UTC** ✅ throughout (L9 import, L35/L55/L134/L142). **Dedup via `_load_seen`/`_save_seen`** with **48h TTL pruning** on save (L34-44). **Yahoo cap to 20 tickers** (L91 "to avoid spamming") + **0.2s sleep politeness** (L117). **CRITICAL:** L100-105 regex XML parsing — fragile (no feedparser). **`append_news_log` non-atomic append** (L153).
2. **NS-X1: news_signals.py** (384) — **PR #77 News-to-score-adjustment translator**. **CATALYST_RULES 12-bucket lookup** (7 bullish + 5 bearish, each `(delta, ttl_days)`). **CATASTROPHIC_KEYWORDS 13 phrases** (bankruptcy/wind-down/delisting). **`NEGATIVE_REACTION_PHRASES` 27-phrase lexicon** for "good news sold" (EVC-style detection — Theme T177). **Atomic write** ✅ (L156-160 tmp+rename). **TZ-aware UTC** ✅. NEW Theme T177 (NARRATIVE-PRICE-DIVERGENCE penalty).
3. **NC-X1: news_classifier.py** (136) — **Claude Sonnet 4.5 LLM classifier** with **CLASSIFIER_PROMPT 28-line schema**. **Heuristic fallback** (L79-116) when no anthropic/key. **Markdown fence stripper** (L68-71). **CRITICAL:** L73/L115 naive `datetime.now().isoformat()`. L62 hard-coded model name `claude-sonnet-4-5`. L122 sort prioritizes Alpaca > Yahoo. NEW Theme T178 (LLM-WITH-HEURISTIC-FALLBACK pattern).
4. **NSn-X1: news_sentiment.py** (46) — **TINIEST module this batch.** Yahoo RSS + 28-positive/30-negative keyword sets. **`feedparser` direct dependency**. **`score_sentiment` dampened by article count** (L42 `net = (pos - neg) / max(n_articles, 1)`) + **clip `[0.05, 0.95]`** (L45 — never strictly 0/1 to avoid edge-case multipliers). **0 BUG findings.** Theme T57 (PERFECT MODULE).
5. **MN-X1: market_news.py** (211) — **Macro market briefing — Claude → Gemini → neutral fallback ladder**. **2 cache layers** (general news 4h, sentiment 4h, both hour-bucketed in filenames). **`_build_sentiment_prompt`** asks for 6-field JSON (sentiment/score/narratives/key_risks/key_catalysts/summary). **Defensive markdown fence strip + JSON setdefault for missing keys** (L168-179). **CRITICAL:** L20 mkdir at import time (T118). L41/L135 naive datetime cache mtime check. NEW Theme T179 (3-TIER LLM PROVIDER FALLBACK with neutral default).
6. **SF-X1: smell_faculty.py** (271) — **THE PROACTIVE-DANGER FACULTY** with **PHILOSOPHY.md docstring** ("warn like a wise friend, not just block silently"). **7 individual smells** (each pure function): earnings_imminent (CRITICAL @ d≤1) / extreme_rsi (CRITICAL @ ≥85) / volume_spike (HIGH @ ≥4x) / gap_up (HIGH @ ≥5%) / low_liquidity (CRITICAL @ <100k shares) / tight_stop (HIGH @ <0.8%) / **stale_price (E2c.2 cross-validates yfinance vs Finnhub)**. **`@dataclass Smell` 4 fields**. **`sniff` defensive try/except per smell** ("A broken smell shouldn't break the agent" L249). **Severity-sorted output** (CRITICAL first). NEW Theme T180 (FAIL-OPEN PER-CHECK ISOLATION). **0 critical bugs in core logic.**
7. **RM-X1: risk_manager.py** (126) — **REGIME-AWARE POSITION SIZING (E3b May 4 2026)** with **5-key REGIME_RISK_MULT lookup** (bull=1.0, transition=0.8, chop=0.6, bear=0.4, unknown=0.7 defensive). **PR #67 day-trade tightening** comment ("0.6×ATR SL → ~1-1.5% stop"). **ATR fallback to 2% of price** (L82). **`max_hold_minutes=240` for day trades** (4-hour hard cap, L102). **CRITICAL:** L98 inline `from src.exit_manager import compute_exit_tiers` — circular-dep avoidance, undocumented.
8. **RX-X1: risk_metrics.py** (167) — **PURE-MATH RISK METRICS** (Sharpe / Sortino / Max DD / Calmar). **Stdlib-only** (no scipy). **Per-trade AND naive annualized** (assumes ~50 trades/year, sqrt(50)≈7.07 multiplier — L116-120). **`_max_drawdown` correct equity-curve walk** with peak-tracking (L74-94). **`sample_warning` flag at n<30** (L128). **0 critical bugs. Theme T57 (PERFECT MODULE).** ✅
9. **EM-X1: exit_manager.py** (63) — **PHASE 2B.1 SCALE-OUT TIER ENGINE** — **3-tier 1/3-1/3-1/3 split** (TP1 lock at 1.5×ATR, TP2 at 2.5×ATR, TP3 trail). **Day-trade tighter** (0.75×ATR / 1.5×ATR). **Edge case qty<3 → all in tier 2** (L48-51). **ATR fallback 2% of entry** (L35-36). **0 critical bugs. Theme T57 (PERFECT MODULE).** ✅
10. **EX-X1: exit_metrics.py** (173) — **PHASE 2B.4 CAPTURE EFFICIENCY METRIC** = `avg(realized_return) / avg(MFE)`. **Headline metric:** old=30-50%, target≥70%. **4 stat functions:** tier_hit_breakdown / trail_stats / tp_raise_stats / capture_efficiency. **`_safe_float` triple-None defense** (`v not in (None, "", "None")` L19). **MFE lookup via optional `exec_report` injection** (L132-138 — picks_log doesn't have MFE column). **0 critical bugs.** ✅

---

## TOP-LEVEL CRITICAL FIXES (priority order)

1. **NE-X1: Yahoo XML parsing via raw regex (L100-105)** — fragile, breaks on CDATA-edge-case. **Fix: switch to `feedparser` (already a dependency from NSn-X1).** **30 min.**
2. **NE-X1: `append_news_log` non-atomic append (L153-155)** — partial write on crash corrupts JSONL. **Fix: tmp+rename whole file OR document accepted append-truncation risk.** **15 min.**
3. **NC-X1 + MN-X1: 4 naive `datetime.now()` calls** — file-cache mtime + classified_at timestamps. **Fix: TZ-aware UTC.** **30 min.**
4. **NC-X1: Hard-coded model name `claude-sonnet-4-5` (L62)** — duplicated in MN-X1 (`CLAUDE_MODEL` constant). **Fix: extract to shared `src.llm_config` constant.** **15 min.**
5. **MN-X1: Cache files use hour-bucketed filenames (`%Y%m%d_%H`) but no cleanup** — old files accumulate forever. **Fix: add nightly `_purge_old_caches`.** **30 min.**
6. **RM-X1: Inline import `from src.exit_manager import compute_exit_tiers` (L98)** — circular-dep workaround should be documented OR fixed via lazy property.
7. **NS-X1: `_purge_expired` only runs in `add_signal_from_classification` and `stats`** — `get_ticker_boost`/`get_ticker_signal` re-check inline but don't purge file. Stale entries linger until next add. **Fix: schedule periodic purge OR purge on every read.**

---

## NEW THEMES INTRODUCED THIS BATCH

- **T177 (NARRATIVE-PRICE-DIVERGENCE):** NS-X1 — "good news sold" detection via 27-phrase lexicon → fades bullish boost into small penalty. Operator sophistication.
- **T178 (LLM-WITH-HEURISTIC-FALLBACK):** NC-X1 — Claude classifier degrades gracefully to keyword-based heuristic when API unavailable.
- **T179 (3-TIER LLM PROVIDER FALLBACK):** MN-X1 — Claude → Gemini → neutral default, with explicit `used` tracking variable for observability.
- **T180 (FAIL-OPEN PER-CHECK ISOLATION):** SF-X1 — `sniff` wraps each smell in try/except so one broken smell doesn't break the entire faculty. Critical for safety-faculty design.

---

## src/news_engine.py (163 lines) — LINE BY LINE

- NE-1 GOOD (L1-4): Module docstring describing 3 sources (Alpaca primary + Yahoo RSS + SEC EDGAR — though SEC URL defined L16 but **never used in code**).
- NE-2 BUG-INFO (L16): `SEC_EDGAR_URL` defined but no consumer in this module — dead code or future stub.
- NE-3 GOOD (L18-20): 3 module constants — `NEWS_CACHE` + `NEWS_LOG` + `DEDUP_TTL_HOURS=48`.
- NE-4 GOOD (L23-29): `_load_seen` defensive try/except → empty dict.
- NE-5 GOOD (L32-44): `_save_seen` **TTL-pruning on every save** (L35-43) — keeps cache bounded. **TZ-aware UTC** ✅.
- NE-6 GOOD (L47-85): `fetch_alpaca_news` — env-var credential check (L49-53) + 15s timeout + 200-status check + fallback `created_at`/`updated_at`. Header truncation `[:300]` and summary `[:600]`.
- NE-7 GOOD (L52): Operator-friendly print on missing credentials.
- NE-8 BUG (L83-85): `except Exception` with print only — no structured error log.
- NE-9 GOOD (L88-120): `fetch_yahoo_rss` with **20-ticker hard cap** + **3-item cap per ticker** (L100) + **0.2s politeness sleep** (L117) + **`User-Agent: Mozilla/5.0` header** (L94 — required by Yahoo).
- NE-10 BUG-CRITICAL (L100-105): **Raw regex XML parsing** — fragile against:
  - Nested CDATA blocks
  - HTML-entity-escaped `<` in titles  
  - Yahoo schema drift  
  Should use `feedparser` (already a dependency in `news_sentiment.py`).
- NE-11 GOOD (L108): `id` includes `abs(hash(title))` for stable dedup.
- NE-12 GOOD (L118-119): Silent per-ticker continue — operator-friendly (one bad ticker doesn't poison the batch).
- NE-13 GOOD (L123-145): `fetch_all_news` master orchestrator — Alpaca first, Yahoo for watchlist tickers, dedup via `seen` set, **TZ-aware UTC timestamps** ✅.
- NE-14 BUG (L148-155): `append_news_log` — uses `"a"` append mode, NOT atomic. Partial line on crash corrupts JSONL.
- NE-15 GOOD (L158-163): `__main__` smoke test with operator-friendly output.

---

## src/news_signals.py (384 lines) — LINE BY LINE

- NS-1 GOOD (L1-40): **40-line docstring with PROBLEM SOLVED narrative + DATA FLOW diagram + complete CATALYST→SCORE table** + CATASTROPHIC keyword examples. Operator-pedagogy.
- NS-2 GOOD (L46-48): 3 path constants.
- NS-3 GOOD (L51-67): `CATALYST_RULES` 12-key tuple-value lookup. Inline comments explain bucket rationale.
- NS-4 GOOD (L70-77): `CATASTROPHIC_KEYWORDS` 13-phrase lexicon including warning-shot category ("nasdaq letter").
- NS-5 GOOD (L79-111): `NEGATIVE_REACTION_PHRASES` **27-phrase lexicon** with **EVC archaeology comment** ("EVC-style cases where 'good' news is sold"). Theme T177.
- NS-6 GOOD (L114-115): `_now_iso` TZ-aware UTC helper.
- NS-7 GOOD (L118-121): `_is_catastrophic` lower-case substring scan.
- NS-8 GOOD (L124-130): `_has_negative_reaction` with **em-dash + en-dash normalization** (L127 `replace("—", " ").replace("–", " ")`) — handles smart-quote/typography variation in headlines.
- NS-9 GOOD (L133-142): `_apply_negative_reaction_penalty` — bullish boost on negative-reaction news → **flip to small penalty `[-0.03, -0.01]`** (modest "distribution risk" tilt, not a hard kill).
- NS-10 GOOD (L145-152): `_load_signals` defensive try/except → empty dict.
- NS-11 GOOD (L155-160): `_save_signals` **ATOMIC WRITE** ✅ tmp+rename + parents=True mkdir.
- NS-12 GOOD (L163-174): `_purge_expired` — defensive `(KeyError, ValueError, TypeError)` triple in except. **TZ-aware UTC**.
- NS-13 GOOD (L179-253): `add_signal_from_classification` master:
  - L186-189: ticker required, else None
  - L198-207: catastrophic check FIRST + **180-day TTL** (vs 30 for other catalysts) + `hard_block: True`
  - L208-231: catalyst-rule path with **confidence modulation** (L211-212 `confidence = min(1.0, max(0.3, score_pct / 0.7))`) + negative-reaction fade
  - L232-233: unknown category → None
  - L237: purge expired BEFORE merge (defensive)
  - L240-247: merge logic — **hard_block always wins** (L243), else **larger absolute delta wins** (L246)
- NS-14 GOOD (L211-212): Confidence formula maps tradeable_score 0.7→1.0x, 0.5→0.71x, 0.3→0.43x with `0.3` floor — sensible non-linear.
- NS-15 GOOD (L246): `abs(signal["score_delta"]) > abs(existing.get("score_delta", 0))` — magnitude-based dominance, NOT recency.
- NS-16 GOOD (L258-272): `get_ticker_signal` re-validates expiry inline (read-side defense).
- NS-17 GOOD (L275-297): `get_ticker_boost` returns float for direct math use + `0.0` on no-signal/expired.
- NS-18 GOOD (L300-314): `is_hard_blocked` returns `(bool, reason)` tuple — operator-readable reason for hard_blocks.py.
- NS-19 GOOD (L317-356): `rebuild_from_news_log` one-shot reseed for ops use.
- NS-20 BUG (L334): Silent `except Exception: continue` swallows JSON corruption — operator can't tell if news_log is partially corrupted.
- NS-21 GOOD (L347-355): Operator-readable rebuild summary print.
- NS-22 GOOD (L359-373): `stats` for diagnostics — top 5 bullish + top 5 bearish (sorted).
- NS-23 GOOD (L364): **M7 archaeology comment** ("catches deltas <-0.5 too").
- NS-24 GOOD (L376-383): CLI with `rebuild` subcommand.

---

## src/news_classifier.py (136 lines) — LINE BY LINE

- NC-1 GOOD (L1-4): Docstring describes Claude Sonnet 4.5 + 5-field output.
- NC-2 GOOD (L10-37): **`CLASSIFIER_PROMPT` 28-line schema** with **9-category enum + tradeable_score guide** (5 bands with examples).
- NC-3 GOOD (L40-49): `classify_news` — `import anthropic` inside try (graceful degradation when anthropic not installed) + env-key check.
- NC-4 BUG (L62): Hard-coded model `"claude-sonnet-4-5"` — duplicated in MN-X1.
- NC-5 GOOD (L67-71): Markdown fence strip — handles ```json prefix.
- NC-6 BUG (L73): `datetime.now().isoformat()` — naive datetime.
- NC-7 GOOD (L74-76): Falls back to heuristic on Claude failure with operator-friendly print.
- NC-8 GOOD (L79-116): `_heuristic_fallback` — **11 bullish + 10 bearish + 5 high-urgency keywords** + tradeable score formula `(abs(sentiment_score - 0.5) * 2) * urgency_score` (L100).
- NC-9 BUG (L115): Same naive datetime.
- NC-10 GOOD (L107): Urgency 0.7 if any high-urgency keyword found, else 0.4.
- NC-11 GOOD (L113): Action window `next_day` for tradeable<0.6, `intraday` otherwise.
- NC-12 GOOD (L119-123): `classify_batch` — **Alpaca-priority sort** (Alpaca = pre-vetted) + max_items cap.
- NC-13 GOOD (L126-136): `__main__` smoke test with realistic MaxLinear example.

---

## src/news_sentiment.py (46 lines) — LINE BY LINE

- NSn-1 GOOD (L1-3): Tiny docstring + 2 imports.
- NSn-2 GOOD (L5-9): `POSITIVE` 28-keyword set (literal Python set for O(1) membership).
- NSn-3 GOOD (L11-16): `NEGATIVE` 30-keyword set.
- NSn-4 GOOD (L19-27): `fetch_news` with **defensive try/except + operator-friendly print on failure**. Returns 3-field dicts (title/link/published).
- NSn-5 GOOD (L30-45): `score_sentiment` with:
  - L33-34: empty-news → 0.5 baseline
  - L36-39: count pos/neg keyword hits
  - L42: **dampened by article count** (`/ max(n_articles, 1)`) — prevents tiny-sample tilt
  - L44: maps `[-2, +2]` net → `[0, 1]` via `+ net/4`
  - L45: clip to `[0.05, 0.95]` — **never strictly 0/1** to avoid downstream multiplier explosion
- **NSn-6: 0 BUG findings. Theme T57 (PERFECT MODULE) — 41st cumulative perfect.** ✅

---

## src/market_news.py (211 lines) — LINE BY LINE

- MN-1 GOOD (L1-4): Docstring lists provider ladder (Claude → Gemini → neutral).
- MN-2 GOOD (L13): `load_dotenv()` at import time — sensible for CLI module.
- MN-3 GOOD (L15-18): 4 env-var constants with **two GEMINI_KEY fallbacks** (`GEMINI_API_KEY` OR `GOOGLE_API_KEY` L18).
- MN-4 BUG-MINOR (L20): `_CACHE_DIR.mkdir(parents=True, exist_ok=True)` at import time (T118 — module side effect).
- MN-5 GOOD (L21-22): Two TTL constants (general 4h, sentiment 4h).
- MN-6 GOOD (L24): `CLAUDE_MODEL` extracted as constant (better than NC-X1's hard-coding!).
- MN-7 GOOD (L27-32): Two cache-path helpers — **hour-bucketed filenames** (`%Y%m%d_%H`) means new file every hour.
- MN-8 BUG (L28/L32): `datetime.now().strftime(...)` — naive datetime in cache filenames (TZ-inconsistent across DST/server-relocation).
- MN-9 GOOD (L35-58): `fetch_market_news` — env-key check + cache check + sort by datetime desc + cache write + operator print on failure.
- MN-10 BUG (L41): `datetime.now().timestamp() - cache.stat().st_mtime` — naive datetime arithmetic.
- MN-11 GOOD (L61-80): `_build_sentiment_prompt` — clean 30-headline cap + 6-field JSON schema.
- MN-12 GOOD (L83-91): `_strip_markdown_fences` — handles both leading and trailing ``` fences.
- MN-13 GOOD (L94-104): `_claude_sentiment` — `temperature=0.3` (low for consistency) + 800 max tokens.
- MN-14 GOOD (L107-116): `_gemini_sentiment` REST call with explicit RuntimeError on non-200.
- MN-15 GOOD (L119-183): `analyze_market_sentiment` master:
  - L121-128: 6-field neutral default
  - L130-131: empty-headlines → default
  - L134-141: cache hit check with cache-name in print
  - L148-154: Claude (primary) try
  - L156-161: Gemini fallback
  - L163-165: Both failed → neutral default with operator print
  - L168-179: Parse + setdefault for missing keys + cache write
  - L180-183: Operator-readable JSON-parse-error trace with raw text first 300 chars
- MN-16 GOOD (L172): `for k in default: result.setdefault(k, default[k])` — prevents downstream KeyError if LLM omits a field.
- MN-17 GOOD (L182): `print(f"[market_news] raw text was: {raw_text[:300]}")` — invaluable for debugging LLM-format drift.
- MN-18 GOOD (L186-194): `get_market_briefing` one-shot composition with **top 5 headlines** in output.
- MN-19 GOOD (L197-210): `__main__` smoke test with full operator-readable output.

---

## src/smell_faculty.py (271 lines) — LINE BY LINE

- SF-1 GOOD (L1-17): **17-line docstring with PHILOSOPHY.md citation + 4-severity rubric + design contract** ("Each smell is a pure function of (pick, signals) → optional Warning. Easy to test, easy to add new ones").
- SF-2 GOOD (L23-28): `@dataclass Smell` with 4 fields + `blocking: bool = False` default.
- SF-3 GOOD (L35-56): `smell_earnings_imminent` — **3-tier ladder** (≤1 CRITICAL+blocking, ≤3 HIGH, ≤7 MED) with **`d < 0` defense** (post-earnings — no smell).
- SF-4 GOOD (L40-43): Defensive `try/except (TypeError, ValueError)` on int coerce.
- SF-5 GOOD (L59-76): `smell_extreme_rsi` — **Finding #2 archaeology** ("real picks store these in pick['scores'][...] not flat") — checks 3 locations (sig, pick, pick.scores). 2-tier ladder (≥85 CRITICAL+blocking, ≥75 HIGH).
- SF-6 GOOD (L79-92): `smell_volume_spike` — single tier (≥4x HIGH).
- SF-7 GOOD (L95-111): `smell_gap_up` — 2-tier ladder (≥5% HIGH chasing, ≥3% MED be-patient).
- SF-8 GOOD (L114-132): `smell_low_liquidity` — 2-tier ladder (<100k CRITICAL+blocking, <500k HIGH). **4-location lookup** including `avg_daily_volume` legacy key (L118).
- SF-9 GOOD (L135-148): `smell_tight_stop` — single tier `0 < risk_pct < 0.8` HIGH (excludes 0/inverted SL via `> 0` check).
- SF-10 GOOD (L154-224): `smell_stale_price` — **E2c.2 cross-validation** with **60-line operator docstring** explaining 4 use-cases + 3 severity tiers + cost note ("~0.3-1s per pick").
- SF-11 GOOD (L172-176): Pre-flight check — silent None return if ticker/price missing (let upstream handle).
- SF-12 GOOD (L178-181): Inline `from src.finnhub_data import cross_validate_price` with except-fallthrough (helper missing → skip silently).
- SF-13 GOOD (L189-208): **Two-branch CRITICAL logic** — distinguishes "primary invalid" from "disagreement" with explicit operator-readable messages.
- SF-14 GOOD (L211-221): Soft-warn HIGH non-blocking for 2-5% drift.
- SF-15 GOOD (L227-235): `ALL_SMELLS` registry — operator can disable a smell by commenting one line. Add E2c.2 archaeology comment.
- SF-16 GOOD (L238-252): `sniff` — **Theme T180 fail-open per-check isolation** ("A broken smell shouldn't break the agent"). Severity-sorted output.
- SF-17 GOOD (L255-260): `has_blocking_smell` returns first blocking — early-out for callers who only need block decision.
- SF-18 GOOD (L263-270): `format_for_telegram` — empty-string for empty warnings (caller-safe).
- **SF-19: 0 critical bugs. 7 smells, 1 fail-open registry, 1 dataclass. Theme T180 newly introduced. Module is a model of safety-faculty design.**

---

## src/risk_manager.py (126 lines) — LINE BY LINE

- RM-1 GOOD (L1-2): Tiny docstring.
- RM-2 GOOD (L5-20): **E3b May 4 2026 archaeology** with full per-regime rationale comments. 5-key REGIME_RISK_MULT dict.
- RM-3 GOOD (L23-31): `regime_risk_multiplier` — **defensive 0.7x for None/missing/unknown** ("never accidentally size up in murky conditions" L27).
- RM-4 GOOD (L35-41): `position_size` — risk_dollars / risk_per_share with `<= 0` defense → 0 (no zero-division).
- RM-5 GOOD (L43-62): `trade_plan` (legacy non-ATR path) — config-driven SL/TP multipliers + risk_reward computation. **`if not (entry and atr): return {}`** defense (L47-48).
- RM-6 GOOD (L66-125): `atr_trade_plan` master:
  - L75-79: PR #67 day-trade tightening with archaeology comment
  - L81-82: ATR fallback to 2% of price (defensive)
  - L86-89: Inverted SL early-return with `quantity=0`
  - L91-94: **E3b regime-aware risk capital** = `capital * risk_pct * regime_mult` (multiplicative composition)
  - L94: `qty = max(1, int(...))` — never zero shares (might be a bug — should preserve 0 if regime says so?)
  - L99: Phase 2B.1 scale-out tier integration
  - L102: Day-trade `max_hold_minutes=240` (4 hours)
  - L104-125: 14-field result dict with full audit trail (`atr`, `stop_method`, `regime`, `regime_risk_mult`)
- RM-7 BUG-INFO (L98): `from src.exit_manager import compute_exit_tiers` inline — circular-dep avoidance, undocumented.
- RM-8 BUG-MINOR (L94): `max(1, int(...))` floors at 1 share — **could be incorrect when regime_mult forces sub-1-share allocation** (better: return 0 to mean "skip this trade").

---

## src/risk_metrics.py (167 lines) — LINE BY LINE

- RX-1 GOOD (L1-19): **19-line docstring with conventions section** (per-trade vs annualized, holding period inferred, max DD on cumulative R-curve, Calmar formula).
- RX-2 GOOD (L25-27): 3 module constants — PICKS_LOG + CLOSED_STATUSES (4-status set) + TRADING_DAYS_PER_YEAR=252.
- RX-3 GOOD (L30-40): `_load_closed_chrono` — filter to closed-with-return, **chronological sort with fallback** (`evaluated_on` then `pick_date`).
- RX-4 GOOD (L43-47): `_f` defensive float coerce → None.
- RX-5 GOOD (L50-58): `_sharpe` per-period — requires n≥2, sd>0, returns None defensively.
- RX-6 GOOD (L61-71): `_sortino` per-period — **downside deviation = sqrt(mean(downside²))** (correct formula, not just stdev of negatives).
- RX-7 GOOD (L74-94): `_max_drawdown` correct equity-curve walk:
  - L81: `equity = [1.0]` baseline
  - L82-83: cumulative compound
  - L84-93: peak-tracking with running max DD update
  - L94: returns rounded `(max_dd_pct, trough_idx)`
- RX-8 GOOD (L97-140): `compute_risk_metrics` master:
  - L101-102: empty-defense
  - L104-107: parallel pct + R-multiple aggregation
  - L109-114: 4-metric computation
  - L116-120: **naive annualization** with archaeology comment (~50 trades/year, sqrt(50)≈7.07)
  - L122-124: Calmar = `annual_return / |max_dd|` with zero-defense
  - L126-140: 13-field result dict with `sample_warning: n<30` flag
- RX-9 GOOD (L128): `sample_warning` flag at n<30 — operator honesty about statistical floor.
- RX-10 GOOD (L143-166): `format_risk_text` — operator-readable plain-text block with **`fmt(v, sfx)` helper for None→"—"** (graceful display for missing metrics).
- **RX-11: 0 BUG findings. Theme T57 (PERFECT MODULE) — 42nd cumulative perfect.** ✅

---

## src/exit_manager.py (63 lines) — LINE BY LINE

- EM-1 GOOD (L1-7): **7-line docstring with Phase 2B.1 + 3-tier mathematical contract** (TP1 1.5×ATR, TP2 2.5×ATR, TP3 trail).
- EM-2 GOOD (L11-26): `compute_exit_tiers` signature with **6-field-typed dict return docstring**.
- EM-3 GOOD (L29-32): Day-trade tighter mults (0.75 / 1.5 vs swing 1.5 / 2.5).
- EM-4 GOOD (L35-36): ATR fallback 2% of entry (defensive).
- EM-5 GOOD (L38-39): TP1 + TP2 round to 2 decimals.
- EM-6 GOOD (L42-45): **1/3-1/3-remainder split** with `qty = max(1, int(qty))` floor.
- EM-7 GOOD (L48-51): **Edge case `qty < 3` → all in tier 2 (single exit)** — correct handling for small positions.
- EM-8 GOOD (L53-62): 8-field result dict including audit fields (`atr_mult_tp1`, `atr_mult_tp2`).
- **EM-9: 0 BUG findings. Theme T57 (PERFECT MODULE) — 43rd cumulative perfect.** ✅

---

## src/exit_metrics.py (173 lines) — LINE BY LINE

- EX-1 GOOD (L1-8): **8-line docstring with HEADLINE METRIC declaration** (capture_efficiency + old=30-50% / target≥70%).
- EX-2 GOOD (L17-21): `_safe_float` with **triple-None defense** (`v not in (None, "", "None")` — covers all CSV-deserialization edge cases).
- EX-3 GOOD (L24-33): `load_picks_for_date` — date-filtered CSV reader with empty-defense.
- EX-4 GOOD (L36-45): `tier_hit_breakdown` — 5-status counter with `counts.get(status, 0)` fallback for unknown statuses (forward-compat).
- EX-5 GOOD (L48-73): `trail_stats`:
  - L61: case-insensitive `(p.get("trail_active") or "false").lower() == "true"` — defensive against bool-serialized-as-string
  - L65: `entry > 0 and current_sl > 0` defense before division
  - L67-68: zero-defense rounding
- EX-6 GOOD (L76-109): `tp_raise_stats`:
  - L91: JSON-deserialize `tp_raises` audit list
  - L92: `isinstance(history, list)` defense
  - L97-101: % bump computation against ORIGINAL TP (not previous raise — slight semantic question, see below)
  - L102-103: defensive try/except continue on bad JSON
- EX-7 BUG-MINOR (L97-101): "% raise" computed against `original_tp` for EVERY event in history, not against previous raise. Means later raises are reported as cumulative-from-original, not delta-per-raise. Operator-readable but semantically ambiguous — should clarify in docstring.
- EX-8 GOOD (L112-172): `capture_efficiency` master:
  - L132-138: MFE lookup from injected `exec_report` (picks_log lacks MFE column — clean dependency injection pattern)
  - L142-152: zip-aligned realized/MFE pairs with double-defense (return present AND MFE > 0)
  - L154-161: zero-defense empty result
  - L163-171: avg-of-avgs computation (NOT total realized / total MFE — see below)
- EX-9 BUG-MINOR (L165): `capture = avg_real / avg_mfe` is **avg-of-avgs**, not the more rigorous `sum(realized) / sum(mfe)`. For per-trade equal weighting it's correct; for capital-weighted it would understate. Consider documenting.

---

## CONSOLIDATED CROSS-CUTTING (THIS BATCH)

### NEW Themes T177-T180 (4 new)

- **T177 (NARRATIVE-PRICE-DIVERGENCE):** NS-X1 — 27-phrase lexicon for "good news sold" → fade boost into small penalty.
- **T178 (LLM-WITH-HEURISTIC-FALLBACK):** NC-X1 — graceful degradation to keyword-based heuristic when LLM unavailable.
- **T179 (3-TIER LLM PROVIDER FALLBACK):** MN-X1 — Claude → Gemini → neutral default with explicit `used` tracking.
- **T180 (FAIL-OPEN PER-CHECK ISOLATION):** SF-X1 — `sniff` wraps each smell in try/except so one broken smell doesn't break the entire faculty.

### Theme T57 (PERFECT MODULES) NOW 43 cumulative
- +4 this batch: NSn (news_sentiment) + RX (risk_metrics) + EM (exit_manager) + SF (smell_faculty has 0 critical bugs in core).

### Theme T6 (atomic writes) UPDATE
- **+1 atomic** (NS-X1 _save_signals tmp+rename).
- **+1 unsafe** (NE-X1 append_news_log).
- Running tally: ~18 safe / ~133 unsafe.

### Cross-cutting tally summary (this batch only)

| Metric | Count this batch |
|---|---:|
| Files actually fetched & line-audited | 10/10 ✅ |
| Total lines audited | 1,740 |
| Bare `except:` | 0 |
| Silent `except Exception` (with continue/None default, no log) | 6 (NE×3, NS×1, NC×1, MN×2) |
| Silent `except` with `print()` only | 4 (NE×2, NSn×1, MN×3, NC×2) |
| Naive datetime usage | 5 (NC×2, MN×3) |
| TZ-aware UTC | 8 (NE×4, NS×4) |
| Atomic writers | 1 (NS-X1) |
| Unsafe writers | 1 (NE-X1) |
| Inline imports | 3 (RM L98, SF L179, NC L43) |
| Module-level side effects | 2 (MN L20 mkdir, MN L13 dotenv) |
| Dataclasses | 1 (SF Smell) |
| `__main__` smoke tests | 4 (NE, NS, NC, MN) |
| 0-BUG perfect modules | 4 (NSn, RX, EM, SF-core) |
| Operator-readable archaeology | 7+ (E3b, PR #67, PR #77, PR #84, EVC, MPWR, M7, Finding #2, E2c.2, Phase 2B.1/2B.4) |
| LLM provider integrations | 3 (Claude in NC + MN, Gemini in MN, anthropic SDK) |

---

## SUMMARY (Batch 96 — 10-FILE)

| File | Critical | Bug | Code smell | Good | Total findings |
|---|---:|---:|---:|---:|---:|
| news_engine | 1 | 2 | 1 | 11 | 15 |
| news_signals | 0 | 1 | 0 | 23 | 24 |
| news_classifier | 0 | 3 | 0 | 10 | 13 |
| news_sentiment | 0 | 0 | 0 | 6 | 6 |
| market_news | 0 | 3 | 1 | 15 | 19 |
| smell_faculty | 0 | 0 | 0 | 19 | 19 |
| risk_manager | 0 | 1 | 1 | 7 | 9 |
| risk_metrics | 0 | 0 | 0 | 11 | 11 |
| exit_manager | 0 | 0 | 0 | 9 | 9 |
| exit_metrics | 0 | 2 | 0 | 9 | 11 |
| **TOTAL** | **1** | **12** | **3** | **120** | **136** |

---

## TOP 10 PRIORITY FIXES FROM BATCH 96

1. **NE-X1 Yahoo regex XML parsing (L100-105)** — switch to `feedparser`. **30 min.**
2. **NE-X1 atomic JSONL append** — tmp+rename. **15 min.**
3. **NC-X1 + MN-X1 5 naive datetime calls** — TZ-aware UTC migration. **30 min.**
4. **NC-X1 + MN-X1 model name duplication** — extract to `src.llm_config`. **15 min.**
5. **MN-X1 hour-bucketed cache files accumulate forever** — add nightly purge. **30 min.**
6. **EX-X1 `tp_raise_stats` % computation semantics** — clarify (cumulative-from-original vs per-raise-delta) in docstring. **10 min.**
7. **EX-X1 `capture_efficiency` avg-of-avgs vs sum/sum** — document semantic choice. **10 min.**
8. **NS-X1 `_purge_expired` not run on every read** — schedule periodic OR purge on every read. **20 min.**
9. **RM-X1 inline import + `max(1, int(...))` floor** — document or fix. **15 min.**
10. **SF-X1 `smell_stale_price` adds 0.3-1s per pick** — already documented as acceptable; consider adding `if final_pick_count > 30: skip` guard for backtest scaling.

---

## COVERAGE TRACKER (HONEST)

| Phase | Files in `src/` | Verifiably audited (this convo, line-by-line) |
|---|---:|---:|
| Pre-batch-96 | 92 | 46 |
| **Post-batch-96** | **92** | **56** |
| Remaining `src/` top-level | — | **36 files (~39%)** |

Plus subdirectories: `src/backtester/` (5), `src/market_data_providers/` (2), `src/patterns/` (10) — all unverified.

End of Batch 96.
