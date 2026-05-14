# Batch 74 — 5-FILE BATCH — TRUE LINE-BY-LINE — PROBABILITY/SCORING/SMELL/BLOCKS/LLM

**Date:** 2026-05-13
**Files (5):** probability_engine (353) + scorer (236) + smell_faculty (271) + hard_blocks (330) + llm_agent (207)
**Phase:** H. **Total LOC audited this batch: ~1,397 lines.**
**Note:** Reduced batch size to 5 due to file complexity (probability_engine + hard_blocks are intricate orchestrators with many branches).

## TOP HEADLINE FINDINGS

1. **PE3-X1: probability_engine.py** (353 lines) is **THE PROBABILITY ENGINE V0.1 INTEGRATION SCAFFOLD — MULTI-SIGNAL DECISION BRAIN**. **6-LAYER orchestrator** (Layer 1 empirical base rates from SS-X1 → Layer 2 regime → Layer 3 news → Layer 4 catalyst/earnings → Layer 5 multi-signal combiner → Layer 6 decision output). **3 adjustment-table dispatchers** (REGIME_ADJUSTMENTS×5 + NEWS_ADJUSTMENTS×6 + CATALYST_ADJUSTMENTS×4) + **2 dataclasses** (SignalState 7-field + ProbabilisticDecision 16-field with audit_trail) + **OPERATOR-EXPLICIT honesty** ("HONEST STATUS: This is v0.1 — REAL integration, HEURISTIC math. The combiner uses simple multiplicative adjustments based on signal strength, NOT proper Bayesian inference. Future v0.2 will replace the combiner with logistic regression"). **3 cross-doc references** (BRAIN_ARCHITECTURE Pillars 1-5 + PROBABILITY_ENGINE_DESIGN + ADR-001). **2nd ADR-referenced module (Theme T40, after SS-X1)**. **First audited "INTEGRATION SCAFFOLD" with explicit v0.1/v0.2 roadmap.** 14th + 15th dataclasses.
2. **SC2-X1: scorer.py** (236 lines) is **THE MULTI-FACTOR COMPOSITE SCORING ENGINE**. **4 factor scorers** (trend / momentum / volatility / volume) + **`_enhanced_indicator_score` 11-sub-score dispatcher** (stochastic / obv / psar / bb_position / sr_setup / fibonacci / adx_strength / di_direction / vwap_position / candlestick) + **`apply_sector_cap` greedy sort+filter with `reduced_sectors` overrides** + **`apply_tag_cap` primary-tag-from-`X / Y` parser** + **`sector_bonus` semiconductor-specific multiplier** with **base_boost + ai_boost × ai_weight formula**. **First audited multi-factor scoring engine.**
3. **SF-X1: smell_faculty.py** (271 lines) is **THE PROACTIVE DANGER-DETECTION FACULTY** ("👃 SMELL FACULTY"). **7-smell registry** (earnings_imminent / extreme_rsi / volume_spike / gap_up / low_liquidity / tight_stop / stale_price) + **4-tier severity** (CRITICAL/HIGH/MED/LOW) with `blocking:bool` flag + **`@dataclass Smell` 4-field** (16th audited dataclass) + **per-smell try/except → continue defensive isolation** + **PHILOSOPHY-archaeology** ("'The agent should warn like a wise friend, not just block silently.'") + **smell_stale_price = E2c.2 cross-validation with finnhub** with 3-tier dispatch (CRITICAL >5% / HIGH 2-5% / clean <2%). **First audited "smell faculty" with explicit founder-philosophy.** **2 OBSERVE-MODE-style severity tiers** with explicit fallback hierarchy. Operator-trust gold standard.
4. **HB2-X1: hard_blocks.py** (330 lines) is **THE PR-#84 HARD-ENFORCEMENT-LAYER (PREFRONTAL CORTEX)**. **5-block pipeline** (catastrophic_news / penny_stock / sl_too_tight / recent_pick / weak_sector) + **NEW SL_MIN_TIERS 4-tier-by-price dispatch** ($100+ → 1.5% / $30-99 → 2.0% / $10-29 → 2.5% / <$10 → 3.0%) BUG-5 fix May 2 2026 + **5-day TICKER COOLDOWN** BUG-4 fix + **SECTOR_ETF 12-mapping + TAG_ETF 5-mapping** + **`get_weak_sectors` premarket sector ETF -2% gate** + **idempotent fail-closed M2/M2b** (`return False, "missing entry"` / `"missing stop_loss"` instead of permitting) + **audit log to `data/hard_blocks_log.json` keep last 100** + **PHILOSOPHY-archaeology** ("The agent's INSTINCTS are good (premarket check correctly flagged ARM/AVGO/RMBS as SKIP TODAY on Apr 28). The agent's IMPULSE CONTROL was missing"). **2nd hard-block module audited (paired with B65 watchlist hard_blocks)**. Founder-archaeology gold standard.
5. **LLM-X1: llm_agent.py** (207 lines) is **THE LLM RATIONALE GENERATION WITH 4-PROVIDER FALLBACK CHAIN** (Claude Sonnet 4.5 → Gemini → OpenAI → rule-based). **md5-keyed 12h disk cache** + **`_LAST_CALL` global throttle (1.5s min interval)** + **2 quota-exhaustion sticky flags** (`_CLAUDE_QUOTA_EXHAUSTED` / `_GEMINI_QUOTA_EXHAUSTED`) — **once exhausted in run, stays exhausted** + **`_is_quota_error` 6-keyword classifier** (resource_exhausted / quota / rate_limit / 429 / insufficient / credit) + **provider-specific lazy import per call** (anthropic / google.genai / openai) + **TZ-aware UTC cache with backward-compat naive→UTC migration** + **rule_based fallback with skip-set + top-3 numeric factor extraction**. **First audited 4-provider LLM fallback chain.** **CLAUDE_MODEL hardcoded again** (4th instance: now 4 modules — Theme T8 keyword for hardcoded model).

## CRITICAL CROSS-FILE FINDINGS

- **NEW Theme T41 (PHILOSOPHY/ARCHAEOLOGY-DRIVEN MODULES):** SF-X1 + HB2-X1 + AM-X1 (B73 agent_memoir) + MB-X1 (B73 meta_brain) all carry **explicit PHILOSOPHY.md or founder-quote archaeology** as first-class commentary. **4 modules now formally philosophy-driven.** This is **Pillar 6 (founder-trust) operator discipline**. Document in `docs/PHILOSOPHY_DRIVEN_MODULES.md`.
- **NEW Theme T42 (HEURISTIC vs FUTURE-LEARNED-MODEL HONEST DEMARCATION):** PE3-X1 explicitly demarcates v0.1 HEURISTIC vs v0.2 LEARNED-LOGISTIC roadmap. **First module with EXPLICIT v-version honest-status+roadmap docstring.** Apply pattern to:
  - WP-X1 weight_proposer (B73) — already has "Auto-apply ships in T-future (C6) with safety caps" hint
  - HE-X1 hypothesis_engine (B73) — could state "v0.1 binomial; v0.2 multi-arm bandit"
  - MH-* monster_hunt (B68/B69 era)
  
  **Recommend** `docs/MODULE_VERSIONING_DISCIPLINE.md` template.
- **PE3-X1 Pillars 1-5 reference confirms B73's Theme T39 (BRAIN-MUTATION PIPELINE):**
  - Pillar 1 = SS-X1 + HE-X1 (B73 audited)
  - Pillar 2 = regime (not yet audited)
  - Pillar 3 = news_classifier (not yet audited)
  - Pillar 3.5 = CAL-X1 + WP-X1 (B73)
  - Pillar 4 = WA-X1 (B73 weight_applier)
  - Pillar 5 = PE3-X1 (B74 — THIS BATCH)
  - **Pillar 5 is the integration scaffold that USES the previous 4 pillars.**
- **HB2-X1 SL_MIN_TIERS + PE3-X1 PROBABILITY-BASED SL = TWO CONFLICTING SL-MIN PHILOSOPHIES:**
  - HB2 hard-codes 4 price-tier thresholds (1.5/2.0/2.5/3.0%)
  - PE3 computes SL from `empirical_sl_pct(target_p_noise=0.30)` (per-stock empirical)
  - **HB2 is hard-block GATE; PE3 is probability ENGINE** — both need to coexist but are NOT cross-referenced. **CRITICAL:** HB2 should consult PE3 for `min_sl` instead of hardcoded tier table — once PE3 v0.2 is production-ready. Document this transition path. Per PE3-X1 archaeology comment "Aligns with Probability Engine vision (docs/PROBABILITY_ENGINE_DESIGN.md)" already.
- **LLM-X1 sticky-quota-flag pattern (Theme T43 NEW):** Once Claude or Gemini quota-exhausted within a single run, flag stays True for rest of run → **avoids cascading retries**. **Operator-pragmatic anti-thundering-herd pattern.** Could apply to:
  - DF-X1 (B73 data_fetcher) — yfinance ratelimit could set sticky flag for rest of universe fetch
  - Per-provider STQ-X1 (B71 stooq) — though stooq is fallback, not primary
  - Per-batch in scrapers
  
  **Document in `docs/STICKY_QUOTA_FLAG_PATTERN.md`.**
- **SF-X1 + LLM-X1 + DF-X1 + EAR-X1 = 4 modules with `try/except → optional-dep silent skip` pattern:** finnhub_data, anthropic, google.genai, openai, curl_cffi, finnhub_data again. **All 4 modules use the same defensive optional-import pattern.** Theme T8 candidate: extract `_optional_import(name, attr)` helper. (Low priority but stylistically consistent.)
- **Theme T6 (atomic writes):** HB2-X1 line 325 `log_path.write_text(json.dumps(existing[-100:], indent=2))` — **72nd unsafe writer**. LLM-X1 line 41-43 `_cache_put` — **73rd unsafe writer**. PE3-X1 has no writes (decision-only).
- **HB2-X1 5-keyword sticky-class set:** `MIN_PRICE / SL_MIN_TIERS / COOLDOWN_DAYS / SECTOR_ETF_DROP_THRESHOLD / SECTOR_ETF / TAG_ETF` — **6 module-level magic constants**. All 6 documented inline with archaeology. Acceptable.
- **PE3-X1 sys.path.insert (line 35) ANTI-PATTERN:** Module modifies sys.path at import time to allow dual `python -m src.probability_engine` and `python src/probability_engine.py` invocation. **23rd cross-cutting import-time side-effect.** **CRITICAL** — sys.path manipulation can cause production import bugs. Should be **removed** and rely on proper module-level invocation only.

## src/probability_engine.py — LINE BY LINE

- PE3-1 GOOD (1-25): **25-line MASSIVE docstring** with **6-layer integration scaffold + HONEST STATUS + WHAT IT REPLACES + 3 cross-doc references.** ✅ Operator-trust gold standard.
- PE3-2 GOOD (12-15): **HONEST STATUS** explicit ("v0.1 — REAL integration, HEURISTIC math...Future v0.2 will replace the combiner with logistic regression"). ✅ NEW Theme T42 gold standard.
- PE3-3 GOOD (22-24): 3 cross-doc references including ADR-001. **2nd Theme T40 ADR-referenced module.**
- PE3-4 BUG (33-35): **sys.path.insert at module-level** to allow `python src/probability_engine.py` direct invocation. **CRITICAL anti-pattern.** **23rd cross-cutting import-time side-effect.** Should be removed.
- PE3-5 GOOD (37-41): import 3 helpers from B73 SS-X1 stock_stats.
- PE3-6 GOOD (49-55): REGIME_ADJUSTMENTS 5-bucket dispatch table (bull/bear/transition/chop/unknown).
- PE3-7 GOOD (53): "chop": "Finding #5: SPY -2 to -5% from SMA" archaeology. ✅
- PE3-8 GOOD (57-65): NEWS_ADJUSTMENTS 6-bucket dispatch table.
- PE3-9 GOOD (67-73): CATALYST_ADJUSTMENTS 4-bucket dispatch table — earnings proximity widens SL + caps TP.
- PE3-10 GOOD (77): DEFAULT_P_WIN_PRIOR = 0.50 — **honest 50/50 prior** + archaeology comment "later: actually compute from picks_log.csv". ✅ NEW Theme T42.
- PE3-11 GOOD (82-91): @dataclass SignalState 7-field. **14th audited dataclass.**
- PE3-12 GOOD (94-124): @dataclass ProbabilisticDecision 16-field with **adjustments_applied list** for audit trail + 3-tier confidence (low/medium/high). **15th dataclass.**
- PE3-13 GOOD (120): `field(default_factory=list)` — correct mutable-default pattern. ✅
- PE3-14 GOOD (129-137): _classify_news with **score-tier + sentiment dispatch** producing 6-bucket key.
- PE3-15 GOOD (132): `if score >= 0.9: return "huge_positive" if sentiment == "bullish" else "strong_negative"` — **score-magnitude maps to STRONG bucket regardless of sentiment direction**. ✅ Operator-correct.
- PE3-16 GOOD (140-150): _classify_catalyst 4-tier dispatch.
- PE3-17 GOOD (153-161): _confidence_label 3-tier with **n_signals + |p_win-0.5| heuristic.**
- PE3-18 GOOD (166-272): compute_probabilistic_decision 6-LAYER orchestrator — **operator-readable Layer comments throughout.**
- PE3-19 GOOD (185-186): None-defensive SignalState default.
- PE3-20 GOOD (191-201): Layer 1 empirical base rates with **2-fallback dispatch (no-stats → safe-default + audit-trail flag).**
- PE3-21 GOOD (193): `has_stats = base_sl is not None and base_tp is not None` — explicit boolean for audit.
- PE3-22 GOOD (197): "FALLBACK_SL_NO_STATS" audit flag + "FALLBACK_TP_NO_STATS" — operator-readable. ✅
- PE3-23 GOOD (213): `regime_key = signals.regime if signals.regime in REGIME_ADJUSTMENTS else "unknown"` — defensive whitelist.
- PE3-24 GOOD (218-220): Audit-trail append only when non-default ("unknown"/"neutral"/"far"). ✅ Reduces noise.
- PE3-25 GOOD (242-245): watchlist_boost as Layer 4b — extra signal counted toward n_signals.
- PE3-26 GOOD (248-250): Layer 5 clip + min-floor + R:R≥1.2 enforcement.
- PE3-27 GOOD (250): `tp_pct = max(sl_pct * 1.2, tp_pct)` — **post-conditioning enforce R:R floor**. ✅
- PE3-28 GOOD (253): EV formula = `P(win)*TP - P(loss)*SL` — operator-correct expectancy.
- PE3-29 GOOD (256-266): Layer 6 conversion to actual price levels with **2-decimal rounding for cents.**
- PE3-30 GOOD (262-263): Buy zone ±0.5% — **room for limit orders**. ✅ Operator-pragmatic.
- PE3-31 GOOD (266): Trigger price +0.3% above entry — **momentum confirmation**. ✅
- PE3-32 GOOD (277-290): format_decision 7-line Telegram-friendly summary with emoji.
- PE3-33 GOOD (295-353): `__main__` 4-test smoke test. **35th smoke test.**
- PE3-34 GOOD (300-352): 4 test scenarios (base / bull+positive / bear+earnings / best-case) — **operator-readable demonstration.**

## src/scorer.py — LINE BY LINE

- SC2-1 GOOD (1): 1-line docstring undersells.
- SC2-2 GOOD (3): import is_semi + get_semi_meta from semiconductors.
- SC2-3 GOOD (7-19): apply_sector_cap with **score-sort greedy fill + reduced_sectors override dict.** ✅
- SC2-4 GOOD (8): "reduced_sectors = {'Technology': 2}" docstring example — operator-readable.
- SC2-5 GOOD (15): Per-pick `cap = reduced_sectors.get(sector, max_per_sector)` — per-sector dynamic cap.
- SC2-6 GOOD (22-40): apply_tag_cap with **`tag.split(' / ')[0]` primary-tag parser + score-sort greedy fill.**
- SC2-7 GOOD (23-25): "Tag format: 'SEMI / AI' → primary='SEMI'" docstring — operator-clear convention.
- SC2-8 GOOD (29-32): Empty-tag → kept (no cap applies).
- SC2-9 GOOD (48-126): **_enhanced_indicator_score 11-SUB-SCORE DISPATCHER**.
- SC2-10 GOOD (53-59): Stochastic 3-tier (≤20 oversold = 0.85 bounce / <80 healthy = 0.70 / overbought = 0.30).
- SC2-11 GOOD (62): OBV trend binary 0.85 vs 0.40.
- SC2-12 GOOD (65): Parabolic SAR binary 0.85 vs 0.30.
- SC2-13 GOOD (67-72): BB position 4-tier dispatch.
- SC2-14 GOOD (75-79): SR setup with **upside_room × 0.6 + safety × 0.4 weighted blend.**
- SC2-15 GOOD (82-90): Fibonacci 4-tier with **golden buy zone (38.2-50%) prefer.**
- SC2-16 GOOD (94-101): ADX 4-tier (>40 / >25 / >20 / else) — Wilder-correct thresholds.
- SC2-17 GOOD (104): +DI vs -DI direction binary.
- SC2-18 GOOD (107-114): VWAP with **above-vwap + 3-tier distance dispatch (sweet spot 0-3%).**
- SC2-19 GOOD (117-124): Candlestick 4-way dispatch (bullish_signal / bearish_signal / doji / else).
- SC2-20 GOOD (129-132): score_indicators wrapper averaging all sub-scores.
- SC2-21 GOOD (139-147): score_trend with **3-condition price-vs-MA dispatch + 3-MA all-required guard.**
- SC2-22 GOOD (150-161): score_momentum with **RSI 3-tier + MACD-vs-signal dispatch.**
- SC2-23 GOOD (164-170): score_volatility with **ATR/close ratio range 1-3% = 0.75 sweet spot, >6% = 0.30 penalty.**
- SC2-24 GOOD (173-179): score_volume with **vol_ratio 4-tier dispatch.**
- SC2-25 GOOD (186-199): sector_bonus semiconductor-specific with **base_boost + ai_boost × ai_weight formula** + **"SEMI / AI" tag construction with ai_weight ≥ 0.75 threshold.**
- SC2-26 GOOD (206-235): composite_score 7-component weighted sum + sector multiplier + **all 11 individual indicator sub-scores surfaced for transparency/LLM context** (`f"ind_{k}"`). ✅ **Audit-trail discipline gold standard.**
- SC2-27 GOOD (221): `raw = sum(components[k] * weights.get(k, 0) for k in components)` — weight-from-config dispatch.
- SC2-28 GOOD (223): Final boosted clipped to [0, 1].

## src/smell_faculty.py — LINE BY LINE

- SF-1 GOOD (1-17): 17-line docstring with **PHILOSOPHY.md founder-quote archaeology + 4-tier severity definition + per-smell pure-function discipline.** ✅ NEW Theme T41 gold standard.
- SF-2 GOOD (6-7): "'The agent should warn like a wise friend, not just block silently.'" Founder-quote archaeology.
- SF-3 GOOD (23-28): @dataclass Smell 4-field with `blocking:bool=False` default. **16th dataclass.**
- SF-4 GOOD (35-56): smell_earnings_imminent with **3-tier dispatch (≤1d CRITICAL+blocking / ≤3d HIGH / ≤7d MED) + try/except int-coerce defensive.**
- SF-5 GOOD (38-39): `if d2e is None or d2e == "": return None` — explicit None+empty check.
- SF-6 BUG (42-43): bare ValueError/TypeError caught (acceptable narrow).
- SF-7 GOOD (44-45): negative-days-to-earnings → None (already passed).
- SF-8 GOOD (59-76): smell_extreme_rsi with **3-source RSI lookup** (sig / pick / pick.scores) + **2-tier dispatch (≥85 CRITICAL+blocking / ≥75 HIGH).**
- SF-9 GOOD (61): "Finding #2 fix: real picks store these in pick['scores'][...] not flat" — operator-archaeology.
- SF-10 GOOD (79-92): smell_volume_spike — **4x volume → HIGH** (single-tier).
- SF-11 GOOD (95-111): smell_gap_up with **2-tier dispatch (≥5% HIGH chasing / ≥3% MED be-patient).**
- SF-12 GOOD (114-132): smell_low_liquidity with **4-source lookup + 2-tier dispatch (<100k CRITICAL+blocking / <500k HIGH).**
- SF-13 GOOD (135-148): smell_tight_stop with **<0.8% from entry → HIGH whipsaw warn.**
- SF-14 GOOD (154-224): **smell_stale_price = E2c.2 cross-validation with finnhub** — most complex smell.
- SF-15 GOOD (155-170): 16-line smell-specific docstring with **catches list + 3-severity-tier explanation + overhead disclosure.** ✅
- SF-16 GOOD (157-159): "Wrong-ticker disasters (would have caught the XXYYZZ123 case)" — operator-archaeology.
- SF-17 GOOD (165-167): "~0.3-1s per pick (one HTTP call). Acceptable overhead for end-of-day pipeline running on ~5-15 final picks." — operator-readable performance disclosure.
- SF-18 GOOD (172-176): Defensive missing-input → None (lets other smells catch).
- SF-19 BUG (179): Inline `from src.finnhub_data import cross_validate_price` (44th cross-cutting inline import) — but in this case, **try/except → return None** is correct optional-dep pattern. Acceptable.
- SF-20 BUG (180-181): bare Exception. Acceptable optional-dep guard.
- SF-21 BUG (185): bare Exception. Acceptable for cross_validate_price failure.
- SF-22 GOOD (188-208): 2-stage hard-block dispatch (disagreement_pct → CRITICAL+blocking with 4-line message vs. invalid → CRITICAL+blocking with reason).
- SF-23 GOOD (210-221): Soft-warn HIGH for 2-5% disagreement.
- SF-24 GOOD (227-235): ALL_SMELLS registry — easy to add new smells.
- SF-25 GOOD (238-252): sniff orchestrator with **per-smell try/except → continue defensive isolation + severity-sort.**
- SF-26 GOOD (247-249): "A broken smell shouldn't break the agent" — operator-readable + bare Exception acceptable.
- SF-27 GOOD (250-251): severity_order map for sort.
- SF-28 GOOD (255-260): has_blocking_smell convenience.
- SF-29 GOOD (263-270): format_for_telegram Telegram-friendly bullet list.

## src/hard_blocks.py — LINE BY LINE

- HB2-1 GOOD (1-19): **19-line MASSIVE docstring** with **PR #84 + PHILOSOPHY-ARCHAEOLOGY (Apr 28 ARM/AVGO/RMBS) + 5-block list + audit-log mandate.** ✅ NEW Theme T41 gold standard.
- HB2-2 GOOD (3-7): "The agent's INSTINCTS are good (premarket check correctly flagged ARM/AVGO/RMBS as SKIP TODAY on Apr 28). The agent's IMPULSE CONTROL was missing (it traded them anyway)." Founder-archaeology gold standard.
- HB2-3 GOOD (8-9): "This module is the prefrontal cortex: NON-NEGOTIABLE filters that override the scoring system." Operator metaphor.
- HB2-4 GOOD (25-29): yfinance optional-import with YF_OK flag.
- HB2-5 GOOD (32): MIN_PRICE = 5.00 — penny stock floor.
- HB2-6 GOOD (33-41): SL_MIN_TIERS 4-tier price dispatch — **BUG-5 fix May 2 2026 + cross-doc reference to PROBABILITY_ENGINE_DESIGN.md** ("Aligns with Probability Engine vision").
- HB2-7 GOOD (35-37): Inline-archaeology comment for the 4 tiers — operator-readable.
- HB2-8 GOOD (44-56): get_min_sl_pct with **try/except → 3.0 safe default + tiered loop dispatch.**
- HB2-9 BUG (52): bare ValueError/TypeError caught (acceptable narrow).
- HB2-10 GOOD (60-65): COOLDOWN_DAYS=5 + PICKS_LOG_PATH — **BUG-4 fix archaeology + Pillar 4 Feedback Loop reference.**
- HB2-11 GOOD (62-63): "Aligns with Pillar 4 (Feedback Loop): wait for outcome before re-picking" — Pillar-cross-reference. ✅
- HB2-12 GOOD (67-88): _get_recent_pick_dates with **try/except → empty dict fail-safe + per-row most-recent-date dedup.**
- HB2-13 BUG (76): Inline `import csv` (acceptable for narrow optional-import within try block).
- HB2-14 BUG (86): bare Exception → empty dict.
- HB2-15 GOOD (84-85): "Keep most recent date per ticker (rows are chronological)" — operator-readable comment.
- HB2-16 GOOD (89): SECTOR_ETF_DROP_THRESHOLD = -2.0.
- HB2-17 GOOD (92-105): SECTOR_ETF 12-mapping (yfinance-style sector names → SPDR ETFs).
- HB2-18 GOOD (108-114): TAG_ETF 5-mapping for tag-based dispatch (catches what yfinance sector misses).
- HB2-19 GOOD (110): "AI": "SOXX" — operator-pragmatic ("AI plays often = semis").
- HB2-20 GOOD (117-129): _safe_pct_change with **3-day history + last-2-bar pct-change + try/except → 0.0 fail-safe.**
- HB2-21 BUG (127): bare Exception → 0.0 (acceptable for resilience).
- HB2-22 GOOD (132-153): get_weak_sectors with **dual sector + tag ETF check + threshold filter.**
- HB2-23 GOOD (158-168): _block_penny **fail-closed M2** with explicit "missing entry price (broken upstream pick)" message.
- HB2-24 GOOD (162): **M2: fail-closed** — `return False, "missing entry price"` instead of silently allowing. ✅ Operator-defensive.
- HB2-25 BUG (166): bare ValueError/TypeError caught (acceptable).
- HB2-26 GOOD (171-193): _block_sl_buffer with **fail-closed M2b + tier-aware min_sl + 3-arg try/except.**
- HB2-27 GOOD (179-180): **M2b fail-closed:** if entry present but SL missing → `return False, "missing stop_loss (broken upstream pick)"`. ✅
- HB2-28 GOOD (188): Per-stock min_sl from get_min_sl_pct dispatch.
- HB2-29 BUG (191): bare ValueError/TypeError/ZeroDivisionError caught (acceptable narrow).
- HB2-30 GOOD (197-215): _block_recent_pick with **per-ticker last-date lookup + days_since vs COOLDOWN_DAYS.**
- HB2-31 BUG (209): naive `datetime.now().date()`. **23rd naive-datetime instance.**
- HB2-32 BUG (213): bare ValueError/TypeError caught (acceptable).
- HB2-33 GOOD (217-237): _block_weak_sector with **tag-split-first parser + sector AND tag dual-check.**
- HB2-34 GOOD (224): "M3: iterate all tags so 'AI / SEMI' checks BOTH" — operator-archaeology comment hints at incomplete fix (only primary tag is checked).
- HB2-35 BUG (224-225): Comment says "iterate all tags" but code only takes primary_tag — **partial M3 fix**. Investigate.
- HB2-36 GOOD (240-252): _block_catastrophic_news with **inline `from src.news_signals import is_hard_blocked`** + try/except.
- HB2-37 BUG (243): Inline import. **45th cross-cutting inline import.** Acceptable as optional-feature.
- HB2-38 BUG (250): bare Exception → True.
- HB2-39 GOOD (257-329): apply_hard_blocks orchestrator with **5-block priority order + per-pick first-block-wins dispatch + audit log.**
- HB2-40 GOOD (270): "Fetch weak sectors ONCE (single network round-trip)" — operator-readable.
- HB2-41 GOOD (273): "Fetch recent pick dates ONCE (BUG-4 cooldown check)" — operator-readable.
- HB2-42 GOOD (282-288): 5-block priority list with archaeology references (PR #77 / BUG-4).
- HB2-43 GOOD (290-296): First-block-wins dispatch (cheapest first).
- HB2-44 GOOD (298-303): Per-block 3-key payload (ticker / reason / block_type).
- HB2-45 GOOD (308-327): Audit log to `data/hard_blocks_log.json` with **last-100 cap + try/except → print-only fail-safe.**
- HB2-46 BUG (319): naive `datetime.now().strftime`. **24th naive instance.**
- HB2-47 BUG (325): No atomic write. **72nd unsafe writer.**
- HB2-48 BUG (326): bare Exception → print only.

## src/llm_agent.py — LINE BY LINE

- LLM-1 GOOD (1-4): 4-line docstring with **fallback chain order + caching mandate + throttle/quota mandate.**
- LLM-2 BUG (5): import `os, time, random, json, hashlib` — `random` imported but never used. Dead import.
- LLM-3 BUG (10): mkdir at import. **24th cross-cutting import-time side effect.**
- LLM-4 BUG (13): **CLAUDE_MODEL = "claude-sonnet-4-5" hardcoded — 4th instance** (Theme T8 / catalogued in earlier batches).
- LLM-5 GOOD (17-19): _cache_key with **md5 of sorted-keys JSON + default=str** for non-serializable defensive.
- LLM-6 GOOD (22-36): _cache_get with **TZ-aware UTC + backward-compat naive→UTC migration + try/except → None.**
- LLM-7 GOOD (29-31): "Backward-compatible with older naive cache files" — operator-readable migration comment.
- LLM-8 BUG (34): bare Exception → None (acceptable for cache).
- LLM-9 GOOD (39-45): _cache_put with try/except → pass + TZ-aware UTC.
- LLM-10 BUG (40-43): No atomic. **73rd unsafe writer.**
- LLM-11 BUG (44): bare Exception → pass.
- LLM-12 GOOD (49-52): 4 module-level state flags (2 quota-exhausted + last_call + min_interval).
- LLM-13 BUG (49-51): **Module-level mutable state via list-of-1 hack** — common Python pattern but error-prone. Could use a small dataclass or threading.Lock-protected state object.
- LLM-14 GOOD (52): _MIN_INTERVAL = 1.5 with archaeology "Claude tier-1: 50 RPM, ~1.2s safe" — operator-pragmatic.
- LLM-15 GOOD (55-59): _throttle with **time-based since-last-call gate.**
- LLM-16 BUG (55-59): **Not thread-safe** — _LAST_CALL[0] read+write without lock. If `parallel_scorer` calls explain_pick concurrently, throttle could be bypassed. Add threading.Lock or asyncio-aware throttle.
- LLM-17 GOOD (63-73): _rule_based fallback with **skip-set + top-3 numeric factor extraction + plain-text 4-line summary.**
- LLM-18 GOOD (64): skip = {"composite", "raw_composite", "sector_mult", "sector_tag"} — explicit skip-list.
- LLM-19 GOOD (73): "Confirm independently. No certainty implied." — disclaimer. ✅
- LLM-20 GOOD (77-98): _build_prompt with **5-element instruction list + DAY/SWING-specific holding rule + 120-word cap.**
- LLM-21 GOOD (82): trade_type-specific holding rule with operator-readable hold_rule string.
- LLM-22 GOOD (96): "End with: 'Not financial advice.'" — disclaimer enforcement. ✅
- LLM-23 GOOD (100-109): _claude provider with **model + max_tokens + temperature kwargs + content[0].text extraction.**
- LLM-24 BUG (101): Inline `import anthropic` — **46th cross-cutting inline import.** Acceptable as optional-dep.
- LLM-25 GOOD (113-124): _gemini provider with **try/except for newer SDK (GenerateContentConfig) + older SDK fallback.**
- LLM-26 BUG (114): Inline `from google import genai`. **47th cross-cutting.**
- LLM-27 BUG (121): bare Exception. Acceptable for SDK-version-dispatch.
- LLM-28 GOOD (128-135): _openai provider straightforward.
- LLM-29 BUG (129): Inline `from openai import OpenAI`. **48th cross-cutting.**
- LLM-30 GOOD (139-142): _is_quota_error with **6-keyword bag** (resource_exhausted / quota / rate_limit / 429 / insufficient / credit). **11th keyword-bag** (Theme T8).
- LLM-31 GOOD (146-155): _try_provider with **throttle + try/except → (None, msg) tuple.**
- LLM-32 GOOD (155): `f"{type(e).__name__}: {str(e)[:120]}"` — operator-readable error truncation.
- LLM-33 GOOD (158-195): _explain_uncached with **4-tier provider fallback + sticky-quota flag dispatch.**
- LLM-34 GOOD (163-171): Claude path with **2-state guard + sticky-quota set on quota-error.**
- LLM-35 GOOD (170): **Once Claude exhausted in run, sticky flag stays True for rest of run** — NEW Theme T43 gold standard.
- LLM-36 GOOD (174-183): Gemini path with **same sticky-quota dispatch + version-coerce model name.**
- LLM-37 GOOD (175): `gem_model = "gemini-2.5-flash-lite" if "gemini" not in model.lower() else model` — operator-pragmatic default.
- LLM-38 GOOD (186-191): OpenAI path (no sticky flag — last resort).
- LLM-39 GOOD (194-195): Rule-based final fallback with print message.
- LLM-40 GOOD (198-206): explain_pick public-API with **cache-check → uncached → cache-put dispatch.**

## CONSOLIDATED CROSS-CUTTING (THIS BATCH)

### NEW Theme T41 (PHILOSOPHY/ARCHAEOLOGY-DRIVEN MODULES)
**4 modules now formally philosophy-driven:**
| Module | Philosophy quote/source |
|---|---|
| AM-X1 (B73) agent_memoir | Founder May 4 2026 quote |
| MB-X1 (B73) meta_brain | Explicit PHILOSOPHY mandate |
| **SF-X1 (B74) smell_faculty** | "wise friend, not block silently" PHILOSOPHY.md quote |
| **HB2-X1 (B74) hard_blocks** | "INSTINCTS good, IMPULSE CONTROL missing" Apr 28 archaeology |

**Document `docs/PHILOSOPHY_DRIVEN_MODULES.md`** — Pillar 6 (founder-trust) operator discipline.

### NEW Theme T42 (HEURISTIC vs FUTURE-LEARNED HONEST DEMARCATION)
- **PE3-X1 (B74) probability_engine = first explicit v0.1/v0.2 roadmap module.**
- "v0.1 — REAL integration, HEURISTIC math...Future v0.2 will replace the combiner with logistic regression"
- DEFAULT_P_WIN_PRIOR = 0.50 + "later: actually compute from picks_log.csv" archaeology
- **Apply pattern to:** WP-X1 (B73) / HE-X1 (B73) / monster_hunt / others.
- Document `docs/MODULE_VERSIONING_DISCIPLINE.md` template.

### NEW Theme T43 (STICKY QUOTA-EXHAUSTED FLAG PATTERN)
- **LLM-X1 (B74) llm_agent = first audited sticky-flag pattern.**
- Once Claude/Gemini quota-exhausted in single run, flag stays True for rest of run — avoids cascading retries.
- **Apply pattern to:** DF-X1 yfinance / per-provider scrapers.
- Document `docs/STICKY_QUOTA_FLAG_PATTERN.md`.

### Theme T39 (BRAIN-MUTATION PIPELINE) UPDATE — PILLAR 5 NOW AUDITED
- **Pillar 5 = PE3-X1 probability_engine integration scaffold (B74)**
- Pillars 1, 3.5, 4, T50 already audited (B73)
- **Pillar 2 (regime) + Pillar 3 (news_classifier) remaining for future batches.**

### Theme T40 (ADR-REFERENCED) UPDATE
- **2nd ADR-referenced module: PE3-X1.**
- ADR-001 = "probability over rules"
- Phase J should audit `docs/decisions/ADR-*.md` (placeholder).

### Theme T6 (atomic writes) UPDATE
- HB2-47 hard_blocks_log.json — **72nd unsafe writer**.
- LLM-10 llm cache JSON — **73rd unsafe writer.**
- **Tally: 10 safe / 73 unsafe / 83 = ~88% UNSAFE.**

### Theme T8 (DRY) UPDATE
- Keyword-bag-of-words: **NOW 11 modules** (LLM-30 6-keyword quota classifier).
- CLAUDE_MODEL hardcoded: **NOW 4 modules.**
- _safe_float duplicates: stable at 41.

### Theme T31 (yfinance brittleness defense) UPDATE
- HB2-X1 _safe_pct_change uses 3-day window + try/except → 0.0 fail-safe — operator-defensive.
- 4 modules now have explicit yfinance-brittleness defense (DF + EAR + SS + HB2).

### Cross-cutting tally summary (this batch only)
| Metric | Before | This batch | After |
|---|---:|---:|---:|
| _safe_float / _safe_int / _to_float | 41 | 0 (none added) | 41 |
| Bare-except | mod | ~14 | continues moderate |
| Inline imports | ~43 | 5 (SF + HB2×2 + LLM×3) | **~48** |
| Import-time side effects | 22 | 2 (PE3 sys.path + LLM mkdir) | **24 — sys.path is CRITICAL anti-pattern** |
| Unsafe writers | 71 | 2 (HB2 + LLM) | **73 / 83 = 88% UNSAFE** |
| Atomic writers | 10 | 0 | 10 |
| TZ-aware modules | 26 | 1 (LLM cache) | **27** |
| Naive datetime usage | 22+ | 2 (HB2×2) | **catalog ongoing** |
| DATED archaeology | ~87 | ~14 (Apr 28 + BUG-4 + BUG-5 + May 2 2026 + E2c.2 + Finding #2 + Finding #5 + PR #77 + PR #84 + M2/M2b/M3) | **~101** |
| Frozen dataclasses | 5 | 0 | 5 |
| Regular dataclasses | 13 | 3 (SignalState + ProbabilisticDecision + Smell) | **16** |
| OBSERVE-MODE modules | 29 | 0 | 29 |
| __main__ smoke tests | 34 | 1 (PE3 4-test) | **35** |
| Theme T11 newline="" POSITIVE | 6 | 0 | 6 |
| Theme T35 cross-module helpers | 6 | 1 (HB2 → news_signals) | **7** |
| Theme T36 shared-lib duplication | 3 distinct Sharpe | 0 | 3 |
| Theme T38 auto-feedback-loop | 2 | 0 | 2 |
| Theme T39 brain-mutation pipeline | 6 (Pillars 1+3.5+4+T50) | 1 (PE3 = Pillar 5) | **7 modules — Pillar 5 added** |
| Theme T40 ADR-referenced | 1 (SS) | 1 (PE3) | **2** |
| **NEW Theme T41 philosophy-driven** | 2 (AM + MB) | 2 (SF + HB2) | **4** |
| **NEW Theme T42 versioning discipline** | new | 1 (PE3) | **1** |
| **NEW Theme T43 sticky-quota-flag** | new | 1 (LLM) | **1** |
| Keyword-bag-of-words | 10 | 1 (LLM 6-keyword) | **11** |
| Hardcoded CLAUDE_MODEL | 3 | 1 (LLM 4th) | **4** |
| Optional-dep import patterns | 7 | 4 (HB2 yfinance + LLM anthropic+gemini+openai) | **11** |
| Yfinance brittleness defense | 3 (DF + EAR + STQ) | 1 (HB2) | **4** |

## SUMMARY (Batch 74 — 5-FILE)

| File | Show-stop | Data/safety | Code smell | Good code | Findings |
|---|---:|---:|---:|---:|---:|
| probability_engine | 1 | 0 | 0 | 33 | 34 |
| scorer | 0 | 0 | 0 | 28 | 28 |
| smell_faculty | 4 | 0 | 0 | 25 | 29 |
| hard_blocks | 11 | 0 | 0 | 37 | 48 |
| llm_agent | 14 | 0 | 0 | 26 | 40 |
| **TOTAL** | **30** | **0** | **0** | **149** | **179** |

## TOP 12 CRITICAL FIXES from Batch 74

1. **PE3-4 sys.path.insert at module-level CRITICAL ANTI-PATTERN:** `sys.path.insert(0, str(Path(__file__).parent.parent))` modifies global Python path at import time to support `python src/probability_engine.py` direct invocation. **Remove** — should rely on `python -m src.probability_engine` only. **Production import bug risk.** (5 min)
2. **NEW Theme T41 documentation:** 4 philosophy-driven modules now. Document `docs/PHILOSOPHY_DRIVEN_MODULES.md` with template (10-15 line philosophy-archaeology docstring + founder-quote + non-behaviors). (45 min)
3. **NEW Theme T42 documentation:** PE3-X1 v0.1/v0.2 roadmap pattern. Document `docs/MODULE_VERSIONING_DISCIPLINE.md` and apply to WP-X1 + HE-X1 + monster_hunt. (45 min)
4. **NEW Theme T43 documentation:** LLM-X1 sticky-flag pattern. Document `docs/STICKY_QUOTA_FLAG_PATTERN.md` and consider extending to DF-X1 yfinance fetcher (yfinance ratelimit flag). (45 min)
5. **HB2-35 PARTIAL FIX archaeology:** "M3: iterate all tags so 'AI / SEMI' checks BOTH" comment claims fix but code only checks `primary_tag`. **CONFIRM intent and either complete fix or remove misleading comment.** (15 min)
6. **PE3-X1 + HB2-X1 SL-MIN ALIGNMENT documentation:** PE3 computes per-stock empirical SL; HB2 hard-codes 4-tier table. Document transition path in `docs/SL_MIN_TRANSITION.md` — when PE3 v0.2 is production, HB2 should consult PE3 for `min_sl`. (30 min)
7. **LLM-16 _throttle thread-safety:** Module-level `_LAST_CALL[0]` shared mutable state without lock. **If parallel_scorer calls concurrent explain_pick, throttle bypassed.** Add threading.Lock. (15 min)
8. **LLM-13 module-level mutable state via list-of-1:** Replace with small `@dataclass` or threading.Lock-protected state object. (15 min)
9. **LLM-2 dead `random` import:** Remove. (1 min)
10. **HB2-47 + LLM-10 atomic writes:** 2 more unsafe writers (now 73 cumulative). Apply NS2-X1 (B73) atomic-rename template. (10 min)
11. **HB2-46 + HB2-31 naive datetime instances:** Migrate to TZ-aware. (5 min)
12. **PE3-X1 PILLAR-5 MAP UPDATE:** Document complete 7-module pipeline in `docs/BRAIN_MUTATION_PIPELINE.md` (B73 had 6 modules + B74 adds Pillar 5 PE3 = scaffold that USES previous pillars). (30 min)

## NEW THEMES UPDATED

- **NEW Theme T41 (philosophy-driven modules):** 4 modules now (AM + MB + SF + HB2).
- **NEW Theme T42 (heuristic vs future-learned roadmap):** PE3-X1 first explicit v0.1/v0.2 demarcation.
- **NEW Theme T43 (sticky-quota-flag pattern):** LLM-X1 first audited.
- **Theme T39 (brain-mutation pipeline):** 7 modules now — Pillar 5 PE3 added.
- **Theme T40 (ADR-referenced):** 2 modules now (SS + PE3).
- **Theme T8 (DRY):** Keyword-bag at 11 modules; CLAUDE_MODEL hardcoded at 4.
- **Theme T6 (atomic writes):** 88% UNSAFE (73/83).
- **Theme T31 (yfinance brittleness defense):** 4 modules now (DF + EAR + SS + HB2).

## COVERAGE TRACKER

| Phase | Status | Cumulative |
|---|---|---:|
| Phase G | done | 30/~30 |
| Phase H | active | 52/~70 |
| Total true line-by-line | **+5 files (5 successful, 0 failures)** | **273 of ~378 (~72.2%)** |

**🎯 72.2% AUDIT MILESTONE. PILLAR 5 (PE3 probability engine integration scaffold) NOW AUDITED. NEW Themes T41 (philosophy-driven) + T42 (heuristic-vs-learned versioning) + T43 (sticky-quota-flag) cataloged. CRITICAL: PE3 sys.path.insert anti-pattern + LLM throttle thread-safety risk.**

## NEXT BATCH

Batch 75: Continue Phase H. Recommended next files (10-15):
- regime (Pillar 2 — completes pillar map), news_classifier + news_engine (Pillar 3), market_calendar, market_data_health, market_guard, premarket_filter / premarket_readiness_gate / premarket_sanity_gate, monster_hunt, signal_journal, learning_journal, lesson_gc, finnhub_data, fundamentals, parallel_scorer, nightly_conductor, watchlist_manager, exit_manager, trailing_stop, scoring_safety, sector_benchmark, day_trading_scorer, dedup_sender, daily_wisdom, wisdom_*

End of Batch 74. **🎯 72.2% milestone. PE3 Pillar 5 scaffold + 3 new themes (T41/T42/T43) cataloged.**
