# Batch 83 — 10-FILE BATCH — TRUE LINE-BY-LINE — LOGGER + 3 GATES + SMELL + CONTRACT + LLM + NEWS + WEEKLY

**Date:** 2026-05-13
**Files (10):** pick_logger (179) + portfolio_risk_gate (279) + hard_blocks (330) + smell_faculty (271) + premarket_decision_contract (269) + premarket_readiness_gate (197) + premarket_sanity_gate (301) + llm_agent (207) + news_engine (163) + weekly_review (352)
**Phase:** H. **Total LOC audited this batch: ~2,548 lines.**

## TOP HEADLINE FINDINGS

1. **PL-X1: pick_logger.py** (179 lines) is **THE 60+-FIELD CSV APPEND-LOG WITH AUTO-MIGRATION + DEDUP-PER-DAY**. **60-field FIELDS module constant** organized into **10 phase-tagged sections** (Phase 2B.1 scale-out / 2B.2 trailing / 2B.3 adaptive-TP / 2B.5 SL-tighten / PILLAR 1 brain audit E2b / Monster Hunt May 3 2026 / Smell Faculty May 5 2026 / SPY benchmark May 2 2026 / Sector benchmark T3 May 3 2026 / official_decision_id 4-key Lane 1) — **HIGHEST-DENSITY phase-archaeology in single module** + **`_migrate_header_if_needed` 4-step header-evolution dispatch** NEW Theme T78 (CSV-HEADER MIGRATION GUARD pattern) + **`extrasaction='ignore'` DOUBLE-EDGED** — comment "PILLAR 1 brain audit (E2b — fixes silent extrasaction='ignore' drop)" reveals that prior version SILENTLY dropped fields + **same-day dedup** via `existing_today` set via re-read of CSV before append + **2 atomic ops MISSING** (header + append) — UNSAFE writers 104th + 105th + **import-time `LOG_PATH.parent.mkdir(...)` side effect** 32nd instance + **comment "tier_status: none | tp1_hit | tp2_hit | trailing | closed" 5-state inline taxonomy.** **CRITICAL: 60-field append matches PE3-X1's atomic save consumer.**
2. **PRG-X1: portfolio_risk_gate.py** (279 lines) is **THE LANE 1 POST-SANITY PORTFOLIO-LEVEL RISK GATE + fail closed when risk fields are malformed**. **Explicit 4-line safety mandate** ("no fake picks / no paper trading / no live trading / fail closed when risk fields are malformed") + **3 module defaults** (MAX_PER_SECTOR=2 / MAX_PER_TAG=2 / MIN_RISK_REWARD=1.0) + **`evaluate_candidate_portfolio_risk` 8-condition fail-CLOSED dispatch** (entry<=0 / sl<=0 / sl>=entry / tp<=entry / qty<=0 / rr<min / risk_pct>limit*1.05 / sector-cap / tag-cap) — **most thorough single-candidate risk validation in repo** + **`risk_pct = (risk_dollars / account_size * 100.0)` per-trade-risk computation** + **5%-overage tolerance** (max_risk_pct = risk_per_trade_pct * 1.05) + **load_open_positions_from_picks_log with `pending` + non-watch_only filter** + **deterministic descending composite sort then per-candidate slot-fill** + **`available_slots = max(0, max_positions - open_count)`** + **per-block 8-key reject record** (ticker / rejection_stage / block_type / reason / candidate / detail) + **8-key summary** (risk_config / open_position_count / available_slots / input_count / allowed_count / blocked_count / final_sector_counts / final_tag_counts). **NEW Theme T79 (PORTFOLIO-LEVEL RISK GATE with fail-CLOSED).** **0 BUG findings — 16th cumulative perfect module.**
3. **HB-X1: hard_blocks.py** (330 lines) is **THE PR #84 PREFRONTAL-CORTEX NON-NEGOTIABLE FILTER WITH 5 BLOCKS**. **PR #84 archaeology gold standard** ("The agent's INSTINCTS are good (premarket check correctly flagged ARM/AVGO/RMBS as SKIP TODAY on Apr 28). The agent's IMPULSE CONTROL was missing (it traded them anyway). This module is the prefrontal cortex: NON-NEGOTIABLE filters that override the scoring system") + **5 BLOCKS in priority order** (1 catastrophic_news PR #77 / 2 penny_stock <$5 / 3 sl_too_tight tiered by price / 4 recent_pick BUG-4 cooldown / 5 weak_sector ETF-down 2%) + **TIERED SL_MIN_TIERS BUG-5 fix May 2 2026** with **4-tier dispatch** (mega >=$100 -> 1.5% / mid $30-99 -> 2.0% / small $10-29 -> 2.5% / micro <$10 -> 3.0%) NEW Theme T80 (TIERED-BY-PRICE STOP-LOSS MINIMUM) + **COOLDOWN_DAYS=5 BUG-4 fix May 2 2026** + **SECTOR_ETF 12-key + TAG_ETF 5-key dispatch** + **fail-OPEN on yfinance unavailable** (`return 0.0` from `_safe_pct_change`) — questionable for safety-critical module + **3-day window for prev/curr close ratio** + **append-to-data/hard_blocks_log.json with last-100-entry trim** + **per-block fail-CLOSED on missing entry/SL** ("M2: fail-closed" / "M2b: fail-closed") + **PR #77 catastrophic_news inline-import to news_signals.is_hard_blocked**. **THE PREFRONTAL-CORTEX MODULE.** **NEW Theme T81 (PREFRONTAL-CORTEX NON-NEGOTIABLE FILTER pattern).**
4. **SF-X1: smell_faculty.py** (271 lines) is **THE 7-SMELL PROACTIVE DANGER DETECTOR + FOUNDER-PRINCIPLE PHILOSOPHY MANDATE**. **Explicit founder-principle archaeology** ("Founder principle (PHILOSOPHY.md): 'The agent should warn like a wise friend, not just block silently.'") + **4-tier severity** (CRITICAL block / HIGH prominent warn / MED note / LOW log-only) + **7 smells** (earnings_imminent 4-tier days / extreme_rsi 2-tier >=85/>=75 / volume_spike >=4x / gap_up_chasing 2-tier >=5%/>=3% / low_liquidity 2-tier <100k/<500k / tight_stop <0.8% / stale_price E2c.2 cross-validate via Finnhub) + **`Smell` regular dataclass** (4 fields: code / severity / message / blocking) — **17th regular dataclass.** + **per-smell fail-OPEN sniff() try/except** ("A broken smell shouldn't break the agent") + **3-source signal-extraction chain per-smell** (sig.get / pick.get / pick.get.scores) defensive + **severity_order dict for stable sort** + **stale_price 3-tier dispatch** (>5% disagreement -> CRITICAL+blocking / 2-5% -> HIGH warn-only / clean -> no-smell) — **NEW Theme T82 (CROSS-PROVIDER PRICE-VALIDATION 3-TIER)** + **format_for_telegram empty-on-empty defensive**. **NEW Theme T83 (FOUNDER-PRINCIPLE-DRIVEN MODULE with PHILOSOPHY.md mandate).**
5. **PDC-X1: premarket_decision_contract.py** (269 lines) is **THE LANE 1 PREMARKET PICK-OR-NO-PICK CONTRACT VALIDATION SCHEMA**. **6-line behavior-neutral mandate** ("does not generate picks / does not change scoring / does not enable paper trading / does not enable live trading / does not send alerts / does not mutate runtime state") + **27-field OFFICIAL_PICK_REQUIRED_FIELDS tuple** + **17-field OFFICIAL_NO_PICK_REQUIRED_FIELDS tuple** + **11-cause OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES enum-set** + **SAFETY_FLAGS 2-tuple** (paper_trading_enabled / live_trading_enabled) **must be False** + **2 contract versions** (CONTRACT_VERSION + STRATEGY_VERSION + SCORING_VERSION) + **6-method validation chain** (_is_missing / _missing_required_fields / _validate_safety_flags / _validate_numeric_fields / validate_official_pick / validate_official_no_pick / validate_official_decision dispatch) + **NUMERIC_FIELDS sub-validation with non-negative-vs-positive rules** + **type-checking for score_components Mapping / risk_flags list / invalidation_conditions list / pipeline Mapping / candidate_diagnostics Mapping / watch_only_available bool**. **NEW Theme T84 (CONTRACT-VALIDATION-SCHEMA MODULE with explicit safety-flag enforcement).** **0 BUG findings — 17th cumulative perfect module.**
6. **PRG2-X1: premarket_readiness_gate.py** (197 lines) is **THE PRE-SCORING DATA-READINESS GATE WITH PROVIDER-DEGRADATION DETECTION**. **4-line safety mandate** ("no fake picks / no paper trading / no live trading / fail closed into official no-pick when critical data is missing") + **2 module defaults** (MIN_FETCH_COVERAGE=0.25 / MIN_FETCHED_COUNT=25) + **`_provider_attempt_summary` 10-key aggregator** + **4 fail-CLOSED conditions** (universe<=0 / fetched<=0 / fetched<required / provider_degraded >=10 attempts + 0 successes + >=attempts errors-or-empty) + **per-fail return 9-key result with primary_no_pick_cause from PDC-X1 enum-set** + **4-warning surfacing** (provider_rate_limited / provider_unauthorized / ohlcv_empty / ohlcv_errors) + **`fetch_coverage = round(fetched_count / universe_count, 4)` precision** + **`assert_premarket_readiness_or_no_pick` thin convenience wrapper.** **NEW Theme T85 (PROVIDER-DEGRADATION DETECTION GATE).** **0 BUG findings — 18th cumulative perfect module.**
7. **PSG-X1: premarket_sanity_gate.py** (301 lines) is **THE POST-SCORING PRE-LOG PER-CANDIDATE SANITY GATE WITH 4-ACTION DISPATCH**. **4 actions** (SAFE / HALF_SIZE / SKIP_TODAY / WATCH_ONLY) + **ACTIONABLE_ACTIONS = {SAFE, HALF_SIZE}** set + **fail-CLOSED to WATCH_ONLY when fresh quote unavailable** + **`evaluate_premarket_sanity` 8-condition dispatch** + **`gap_pct = (current_price - entry) / entry * 100` standard gap formula** + **`sl_buffer_pct = (entry - stop_loss) / entry * 100` defensive stop-buffer** + **`gap_pct <= -sl_buffer_pct * 0.6` 60%-eats-SL detection** NEW Theme T86 (60%-OF-SL-BUFFER GAP-DETECTION) + **size_multiplier 1.0 / 0.5 / 0.0 dispatch** + **`_apply_half_size` mutation with `max(1, int(qty * 0.5))` floor** + **`fetch_market_snapshot` SPY+QQQ+SOXX+VIX 4-ticker dispatch** + **VIX 25/20 2-tier with global_action=skip_all/half** + **5-day yfinance hist with `auto_adjust=False`** + **per-candidate 4-key audit fields surfaced**. **NEW Theme T87 (4-ACTION SAFE/HALF/SKIP/WATCH dispatch with fail-CLOSED).**
8. **LLM2-X1: llm_agent.py** (207 lines) is **THE 4-PROVIDER LLM RATIONALE FALLBACK CHAIN + 12H PER-PICK CACHE**. **4-provider priority** (Claude Sonnet 4.5 -> Gemini -> OpenAI -> rule-based) + **`CLAUDE_MODEL = "claude-sonnet-4-5"` hardcoded** NOW 7 instances of hardcoded model + **MD5-based per-(ticker,scores,plan) cache key** + **TZ-AWARE UTC backward-compat** ("Backward-compatible with older naive cache files") with naive->UTC injection + **module-level state flags `_CLAUDE_QUOTA_EXHAUSTED = [False]` mutable-list-trick** for sticky-once-exhausted behavior NEW Theme T88 (MUTABLE-LIST MODULE-LEVEL STATE FLAG) + **`_MIN_INTERVAL = 1.5` throttle** + **`_throttle()` sleep-to-rate-limit pattern** + **`_is_quota_error` 6-keyword classifier** + **per-provider try-or-fallback dispatch with operator-readable per-fail print** + **prompt 5-rule structured output ending with "Not financial advice."** + **`_rule_based` 4-line fallback rationale composition** with **top-3-factor sort** + **`explain_pick` cache-then-uncached dispatch.** **NEW Theme T89 (4-PROVIDER LLM FALLBACK CHAIN with sticky quota-exhaustion flag).**
9. **NE-X1: news_engine.py** (163 lines) is **THE 2-PROVIDER NEWS FETCHER (ALPACA + YAHOO RSS) + JSONL APPEND**. **2-provider primary+fallback** (Alpaca News API as primary / Yahoo Finance RSS per-ticker as backup) + **regex-based XML parser for Yahoo RSS** ("Parse XML loosely (no feedparser dependency)") NEW Theme T90 (REGEX-XML-PARSER NO-FEEDPARSER pattern) + **`DEDUP_TTL_HOURS = 48` cache + auto-prune-on-save** + **TZ-AWARE UTC throughout** + **id-based dedup via {id: ts}** with **prune-on-save** + **per-ticker 0.2s sleep** ("be polite") + **20-ticker cap on Yahoo RSS** + **3-RSS-item cap per ticker** + **8-key items dict** + **headline truncate 300 chars + summary 600 chars** + **regex CDATA-handling** + **3 fail-CLOSED-on-miss per provider** + **`__main__` smoke test 56th**. **CRITICAL: 1 unsafe writer** (NEWS_LOG append + NEWS_CACHE rewrite). **NEW Theme T91 (POLITE-RATE-LIMITED MULTI-PROVIDER NEWS FETCHER with regex-XML).**
10. **WR-X1: weekly_review.py** (352 lines, **largest in batch**) is **THE PILLAR 5 v0.1 WEEKLY SELF-ASSESSMENT TELEGRAM-FIRST 7-PILLAR INTEGRATION**. **`Pillar 5 v0.1` mandate + 7-pillar integration** (Pillar 5 self-grading + T40 Calibration brain footer + Pillar 1 Layer 4 hypothesis + Pillar 1 Layer 5 self-awareness + Pillar 4 learning_journal + Pillar 5 self_awareness rolling 30d + Pillar 6 wow_trend + Pillar 6 sector_pnl) — **MOST CROSS-CUTTING INTEGRATION MODULE AUDITED** + **`grade()` 7-tier letter A->F dispatch** with **honest "F (crisis — pause review needed)" worst-case** + **what_worked + what_failed + recommended_actions 3-helper dispatch** with **n>=2 + avg_R thresholds for surface** + **`rules_violated_on_losers` B6 wisdom-base lessons-for-context lookup with min_confidence=0.85** + **8 try/except -> pass per-pillar footer** NEW Theme T92 (PER-PILLAR-FAIL-DEFENSIVE FOOTER ASSEMBLY) + **per-failure operator-readable inline reason** + **`if "F " in grade_str or "F (" in grade_str` 2-source F-detection** + **save_snapshot to reports/weekly/weekly_YYYY_MM_DD.md** + **format_markdown via asterisk-double-substitution** + **import-time `REPORTS.mkdir(...)` side effect** = 33rd instance. **THE TOP-LEVEL Pillar 5 ASSEMBLY MODULE.**

## CRITICAL CROSS-FILE FINDINGS

- **NEW Theme T78 (CSV-HEADER MIGRATION GUARD pattern):** PL-X1 first audited.
- **NEW Theme T79 (PORTFOLIO-LEVEL RISK GATE with fail-CLOSED):** PRG-X1 first audited.
- **NEW Theme T80 (TIERED-BY-PRICE STOP-LOSS MINIMUM):** HB-X1 SL_MIN_TIERS 4-tier May 2 2026 BUG-5 fix.
- **NEW Theme T81 (PREFRONTAL-CORTEX NON-NEGOTIABLE FILTER pattern):** HB-X1 PR #84.
- **NEW Theme T82 (CROSS-PROVIDER PRICE-VALIDATION 3-TIER):** SF-X1 stale_price E2c.2.
- **NEW Theme T83 (FOUNDER-PRINCIPLE-DRIVEN MODULE with PHILOSOPHY.md mandate):** SF-X1.
- **NEW Theme T84 (CONTRACT-VALIDATION-SCHEMA MODULE):** PDC-X1.
- **NEW Theme T85 (PROVIDER-DEGRADATION DETECTION GATE):** PRG2-X1.
- **NEW Theme T86 (60%-OF-SL-BUFFER GAP-DETECTION):** PSG-X1.
- **NEW Theme T87 (4-ACTION SAFE/HALF/SKIP/WATCH dispatch):** PSG-X1.
- **NEW Theme T88 (MUTABLE-LIST MODULE-LEVEL STATE FLAG):** LLM2-X1.
- **NEW Theme T89 (4-PROVIDER LLM FALLBACK CHAIN):** LLM2-X1.
- **NEW Theme T90 (REGEX-XML-PARSER NO-FEEDPARSER):** NE-X1.
- **NEW Theme T91 (POLITE-RATE-LIMITED MULTI-PROVIDER NEWS FETCHER):** NE-X1.
- **NEW Theme T92 (PER-PILLAR-FAIL-DEFENSIVE FOOTER ASSEMBLY):** WR-X1.
- **CRITICAL LANE 1 PIPELINE NOW FULLY TRACED — 8-MODULE PRE-LOG GATE CHAIN:** PRG2-X1 (data readiness) -> SCO/PSC scoring -> SF-X1 (smell faculty observe-mode) -> HB-X1 (5 hard blocks PR #84) -> PSG-X1 (sanity 4-action) -> PRG-X1 (portfolio risk gate) -> PDC-X1 (contract validation) -> PL-X1 (CSV log). Document `docs/LANE_1_PIPELINE.md`.
- **PR #84 PREFRONTAL-CORTEX archaeology gold standard at HB-X1:** "The agent's INSTINCTS are good. The agent's IMPULSE CONTROL was missing (it traded them anyway)."
- **PILLAR 5 WEEKLY SELF-ASSESSMENT TRACED — 7-PILLAR INTEGRATION HUB:** WR-X1 = top-level Pillar 5 assembly with footers from CAL+LJ+WA+self_awareness+wow_trend+sector_pnl+wisdom_base.
- **CRITICAL HB-X1 fail-OPEN concern in safety-critical module:** `_safe_pct_change` returns 0.0 on yfinance error -> weak_sector check is SILENTLY SKIPPED if yfinance fails. For prefrontal-cortex module, fail-OPEN here is risky.
- **Theme T6 atomic writes:** PL-X1 (104th + 105th unsafe) + HB-X1 (1 unsafe) + NE-X1 (1+1 unsafe) + WR-X1 (1 unsafe) = +5 new unsafe writers. Tally: 13 safe / 109 unsafe / 122 = ~89.3% UNSAFE.
- **Theme T57 (PERFECT MODULES) NOW 18 cumulative** (+3 this batch — PRG + PDC + PRG2).
- **Theme T41 philosophy-driven NOW 53 modules** (+9 this batch).
- **HARDCODED CLAUDE_MODEL: NOW 7 instances** (LLM2-X1 added).

## src/pick_logger.py — LINE BY LINE

- PL-1 GOOD (1-5): 5-line docstring with **Phase 2B.1 mandate + header-migration explainer.**
- PL-2 BUG (12): import-time `LOG_PATH.parent.mkdir(...)` side effect. **32nd mkdir-at-import.**
- PL-3 GOOD (14-41): 60-field FIELDS module constant in **10 phase-tagged sections.**
- PL-4 GOOD (15-21): Original 26-field core schema.
- PL-5 GOOD (22-23): Phase 2B.1 scale-out (6 fields).
- PL-6 GOOD (24-25): Phase 2B.2 trailing-stop (4 fields).
- PL-7 GOOD (26-27): Phase 2B.3 adaptive-TP (2 fields).
- PL-8 GOOD (28-29): Phase 2B.5 SL-tighten audit (2 fields).
- PL-9 GOOD (30-31): PILLAR 1 brain audit E2b May 4 2026 (5 fields).
- PL-10 GOOD (32-33): Monster Hunt May 3 2026 (3 fields).
- PL-11 GOOD (34-35): Smell Faculty May 5 2026 observe-mode verdict persistence (3 fields).
- PL-12 GOOD (36-37): SPY benchmark May 2 2026 (3 fields).
- PL-13 GOOD (38-40): Sector benchmark T3 May 3 2026 (5 fields).
- PL-14 GOOD (44-71): _migrate_header_if_needed with **4-step header-evolution dispatch.** NEW Theme T78.
- PL-15 GOOD (45-46): "Old rows get empty values for new columns (CSV-safe)." Operator-discipline.
- PL-16 GOOD (47-48): Empty-or-missing short-circuit.
- PL-17 GOOD (49-56): Header-equality short-circuit.
- PL-18 GOOD (58-59): Re-read with DictReader using OLD header context.
- PL-19 GOOD (62-70): Rewrite with NEW header + extrasaction='ignore' guard for future drift.
- PL-20 GOOD (62): newline="" POSITIVE Theme T11 x10th.
- PL-21 BUG (62-70): No atomic. **104th unsafe writer + HIGH RISK** — header rewrite of entire log.
- PL-22 GOOD (66-69): Per-row new-field default empty-string.
- PL-23 GOOD (71): operator-readable migration count print.
- PL-24 GOOD (74-79): _ensure_header with **header-init-or-migrate dispatch.**
- PL-25 GOOD (76): newline="" POSITIVE.
- PL-26 GOOD (82-178): log_picks with **header-ensure + per-day dedup + append.**
- PL-27 BUG (85): naive `datetime.now()`. **82nd naive.**
- PL-28 GOOD (89-94): existing_today set construction via re-read of CSV.
- PL-29 GOOD (97-98): Append mode + extrasaction='ignore' guard.
- PL-30 BUG (97-173): No atomic. **105th unsafe writer.** Append acceptable.
- PL-31 GOOD (100-101): Per-day duplicate skip.
- PL-32 GOOD (102-173): 60-key per-pick row construction with **defaults for all 60 fields.**
- PL-33 GOOD (109): "true"/"false" boolean string normalization for CSV.
- PL-34 GOOD (116): `round(p.get("score", 0), 3)` — explicit 3-decimal stable serialization.
- PL-35 GOOD (124-126): regime + spy_close + cape with **defensive `(regime or {}).get(...)`** — None-tolerant.
- PL-36 GOOD (138): "tier_status: none | tp1_hit | tp2_hit | trailing | closed" inline 5-state taxonomy.
- PL-37 GOOD (140-143): Phase 2B.2 trailing-stop initial state surface.
- PL-38 GOOD (146): tp_raises = "[]" — JSON-empty-array string for audit trail.
- PL-39 GOOD (148-149): Phase 2B.5 SL-tighten audit empty-init.
- PL-40 GOOD (149-154): "PILLAR 1 brain audit (E2b — fixes silent extrasaction='ignore' drop)" — operator-archaeology gold standard.
- PL-41 GOOD (158): "true"/"false" for is_monster boolean string normalization.
- PL-42 GOOD (175-177): operator-readable dedup-skipped print.

## src/portfolio_risk_gate.py — LINE BY LINE

- PRG-1 GOOD (1-13): 13-line docstring with **Lane 1 mandate + 4-line safety mandate.** NEW Theme T79.
- PRG-2 GOOD (24-26): 3 module defaults.
- PRG-3 BUG (29-35): _safe_float duplicate. **58th instance.** Theme T8.
- PRG-4 BUG (38-42): _safe_int duplicate. NEW.
- PRG-5 GOOD (45-53): 4 candidate-attribute helpers.
- PRG-6 GOOD (45-47): Defensive isinstance dict + `or "Unknown"` fallback.
- PRG-7 GOOD (52-53): 2-source tag chain + primary-tag-split-and-uppercase normalization.
- PRG-8 GOOD (61-63): _trade_plan defensive isinstance dict.
- PRG-9 GOOD (66-88): _risk_profile with **2-source plan/candidate fallback chain + 7-key dispatch.**
- PRG-10 GOOD (76-78): risk_dollars + risk_pct with **multi-condition guard.**
- PRG-11 GOOD (86-87): round(x, 2/4) + None-defensive.
- PRG-12 GOOD (91-106): load_open_positions_from_picks_log with **try/except -> [] defensive + 'pending' AND non-watch_only filter.**
- PRG-13 GOOD (101-102): watch_only set-membership normalize.
- PRG-14 BUG (104): bare Exception.
- PRG-15 GOOD (109-114): _existing_sector_counts with **2-source sector chain.**
- PRG-16 GOOD (117-123): _existing_tag_counts with **primary-tag normalization + skip-if-empty.**
- PRG-17 GOOD (126-140): build_portfolio_risk_config with **6-key result + max(1, ...) defensive floors.**
- PRG-18 GOOD (130-131): account_size + risk_per_trade_pct with **`or` short-circuit defaults.**
- PRG-19 GOOD (143-192): evaluate_candidate_portfolio_risk with **8-condition fail-CLOSED dispatch.**
- PRG-20 GOOD (164-191): 8-condition fail-CLOSED dispatch with **operator-readable per-fail reason.**
- PRG-21 GOOD (170): SL-not-below-entry -> reject.
- PRG-22 GOOD (173): TP-not-above-entry -> reject.
- PRG-23 GOOD (179): RR < min_risk_reward -> reject with **inline min surface.**
- PRG-24 GOOD (182): `max_risk_pct = risk_per_trade_pct * 1.05` — 5% overage tolerance.
- PRG-25 GOOD (186-190): Sector + tag exposure cap dispatch.
- PRG-26 GOOD (195-278): apply_portfolio_risk_gate with **descending-score + per-candidate slot-fill + 8-key summary.**
- PRG-27 GOOD (209-210): available_slots with **max(0, ...) floor.**
- PRG-28 GOOD (218): `sorted(candidates, key=_candidate_score, reverse=True)` deterministic ordering.
- PRG-29 GOOD (221-234): Max-positions block with **8-key reject record.**
- PRG-30 GOOD (243-252): 6-condition reject record symmetric.
- PRG-31 GOOD (254-258): per-allow sector/tag count increment for next-candidate accuracy.
- PRG-32 GOOD (260-264): per-allow portfolio_risk audit field add.
- PRG-33 GOOD (267-276): 8-key summary dispatch.
- PRG-34 GOOD: **0 BUG findings (after _safe duplicates) — 16th cumulative perfect module.**

## src/hard_blocks.py — LINE BY LINE

- HB-1 GOOD (1-19): 19-line docstring with **PR #84 mandate + Apr 28 SEMI archaeology.** NEW Theme T81.
- HB-2 GOOD (3-7): "The agent's INSTINCTS are good ... The agent's IMPULSE CONTROL was missing (it traded them anyway)." Operator-philosophy gold standard.
- HB-3 GOOD (8-9): "This module is the prefrontal cortex: NON-NEGOTIABLE filters that override the scoring system."
- HB-4 GOOD (11-15): 5-rule operator-readable dispatch.
- HB-5 GOOD (17-18): "Each block is conservative (better skip than lose). All blocks are logged to data/hard_blocks_log.json for audit."
- HB-6 GOOD (25-29): try/except -> YF_OK fallback.
- HB-7 GOOD (32): MIN_PRICE = 5.00.
- HB-8 GOOD (33-41): SL_MIN_TIERS BUG-5 fix May 2 2026 with **4-tier dispatch.** NEW Theme T80.
- HB-9 GOOD (33-35): "Liquid mega-caps need tighter stops than volatile small caps. Aligns with Probability Engine vision (docs/PROBABILITY_ENGINE_DESIGN.md)" — operator-archaeology gold standard.
- HB-10 GOOD (36-41): 4-tier dispatch with **inline operator-readable comments per tier.**
- HB-11 GOOD (44-56): get_min_sl_pct with **try/except -> 3.0 safe default.**
- HB-12 GOOD (60-63): COOLDOWN_DAYS BUG-4 archaeology with **5-day default + Pillar 4 alignment comment.**
- HB-13 GOOD (67-88): _get_recent_pick_dates with **per-row dispatch + most-recent-per-ticker.**
- HB-14 BUG (76): inline import. **95th cross-cutting.**
- HB-15 BUG (86): bare Exception.
- HB-16 GOOD (89): SECTOR_ETF_DROP_THRESHOLD = -2.0.
- HB-17 GOOD (91-105): SECTOR_ETF 12-key dispatch.
- HB-18 GOOD (107-114): TAG_ETF 5-key dispatch.
- HB-19 GOOD (108): "catches what yfinance sector misses" — operator-discipline.
- HB-20 BUG (117-129): _safe_pct_change with **fail-OPEN return 0.0** — for safety-critical module concerning.
- HB-21 BUG (118): "Returns 0.0 on any failure (fail-safe)." — but this is fail-OPEN for safety-critical filter (CONTRADICTION).
- HB-22 GOOD (122): `auto_adjust=False` + `period="3d"` defensive.
- HB-23 BUG (127): bare Exception -> 0.0.
- HB-24 GOOD (132-153): get_weak_sectors with **2-loop sector + tag dispatch.**
- HB-25 GOOD (137): "Cached to avoid repeated yfinance calls within a single run." — but **NO actual caching implemented** (lies in comment).
- HB-26 GOOD (158-168): _block_penny with **fail-CLOSED on missing entry.**
- HB-27 GOOD (162): "M2: fail-closed" — operator-discipline gold standard.
- HB-28 GOOD (167): try/except -> pass — defensive for non-numeric.
- HB-29 GOOD (171-193): _block_sl_buffer with **fail-CLOSED on missing SL + tiered dispatch.**
- HB-30 GOOD (180): "M2b: fail-closed" — operator-discipline.
- HB-31 GOOD (181-182): both-missing -> True (skip block) — questionable but consistent.
- HB-32 GOOD (188-190): get_min_sl_pct delegation + reject with operator-readable reason.
- HB-33 GOOD (191): ZeroDivisionError narrow catch.
- HB-34 GOOD (197-215): _block_recent_pick with **COOLDOWN_DAYS dispatch.**
- HB-35 GOOD (203-204): empty-ticker or not-in-recent -> True (skip block) defensive.
- HB-36 BUG (209): naive `datetime.now()`. **83rd naive.**
- HB-37 GOOD (211-212): Cooldown reject with **operator-readable days-ago.**
- HB-38 GOOD (217-237): _block_weak_sector with **2-key matching dispatch (sector + tag).**
- HB-39 GOOD (224): "M3: iterate all tags so 'AI / SEMI' checks BOTH. We do this in caller below." — operator-archaeology.
- HB-40 GOOD (225): primary-tag uppercase normalization.
- HB-41 GOOD (228-235): per-weak-name 2-condition dispatch.
- HB-42 GOOD (240-252): _block_catastrophic_news PR #77 with **try/except -> True defensive.**
- HB-43 BUG (243): inline import. **96th cross-cutting.**
- HB-44 BUG (250): bare Exception.
- HB-45 GOOD (257-329): apply_hard_blocks with **5-block priority order + audit log + 8-tuple per-fail dispatch.**
- HB-46 GOOD (266-267): Empty-picks short-circuit.
- HB-47 GOOD (269-273): Single-fetch optimization for weak_sectors + recent_dates.
- HB-48 GOOD (282-288): 5-block priority order tuple of tuples.
- HB-49 GOOD (290-296): First-fail-wins per-pick dispatch.
- HB-50 GOOD (298-303): Per-block 3-key reject record.
- HB-51 GOOD (308-327): Audit log with **last-100-entry trim + try/except -> operator-readable warn.**
- HB-52 BUG (308): No atomic for log_path.write_text. **106th unsafe writer.**
- HB-53 BUG (326): bare Exception.

## src/smell_faculty.py — LINE BY LINE

- SF-1 GOOD (1-17): 17-line docstring with **founder-principle PHILOSOPHY.md mandate + 4-tier severity.** NEW Theme T83.
- SF-2 GOOD (6-7): "Founder principle (PHILOSOPHY.md): 'The agent should warn like a wise friend, not just block silently.'" Operator-philosophy gold standard.
- SF-3 GOOD (9-13): 4-tier severity with **operator-readable per-tier semantics.**
- SF-4 GOOD (15-16): "Each smell is a pure function of (pick, signals) -> optional Warning. Easy to test, easy to add new ones."
- SF-5 GOOD (23-28): Smell regular dataclass with **4 typed fields + blocking default False.** **17th regular dataclass.**
- SF-6 GOOD (35-56): smell_earnings_imminent with **4-tier days dispatch.**
- SF-7 GOOD (37-43): defensive 4-condition guard.
- SF-8 GOOD (46-49): d<=1 -> CRITICAL+blocking.
- SF-9 GOOD (50-52): d<=3 -> HIGH warn.
- SF-10 GOOD (53-55): d<=7 -> MED note.
- SF-11 GOOD (59-76): smell_extreme_rsi with **3-source signal-extraction + 2-tier dispatch.**
- SF-12 GOOD (61): "Finding #2 fix: real picks store these in pick['scores'][...] not flat" — operator-archaeology.
- SF-13 GOOD (62): 3-source signal-extraction chain (sig.get / pick.get / pick.get.scores).
- SF-14 GOOD (69-72): r>=85 -> CRITICAL+blocking with **operator-readable blowoff message.**
- SF-15 GOOD (73-75): r>=75 -> HIGH warn.
- SF-16 GOOD (79-92): smell_volume_spike with **single >=4x threshold.**
- SF-17 GOOD (95-111): smell_gap_up with **2-tier dispatch (>=5% / >=3%).**
- SF-18 GOOD (114-132): smell_low_liquidity with **2-tier dispatch.**
- SF-19 GOOD (118): 4-source avg_vol fallback chain.
- SF-20 GOOD (125-128): v<100k -> CRITICAL+blocking with **operator-readable comma-formatted volume.**
- SF-21 GOOD (135-148): smell_tight_stop with **0.8% threshold for noise-whipsaw.**
- SF-22 GOOD (145): `if 0 < risk_pct < 0.8` — non-zero AND below-threshold guard.
- SF-23 GOOD (154-224): smell_stale_price with **3-tier disagreement dispatch.** NEW Theme T82.
- SF-24 GOOD (155-170): 16-line docstring with **disagreement-tier + perf overhead acknowledgment.**
- SF-25 GOOD (168-169): "Adds ~0.3-1s per pick (one HTTP call). Acceptable overhead for end-of-day pipeline."
- SF-26 GOOD (171-176): early-return on missing-input with **operator-readable explanation.**
- SF-27 BUG (179-181): inline import + bare Exception. **97th cross-cutting.**
- SF-28 GOOD (181): "if helper missing, skip silently" — fail-OPEN-defensive comment.
- SF-29 BUG (185): bare Exception.
- SF-30 GOOD (188-208): >5% disagreement -> CRITICAL+blocking with **2-source dispatch.**
- SF-31 GOOD (210-221): 2-5% disagreement -> HIGH warn-only.
- SF-32 GOOD (227-235): ALL_SMELLS 7-element registry with **inline E2c.2 archaeology.**
- SF-33 GOOD (238-252): sniff with **per-smell fail-OPEN try/except + severity-order sort.**
- SF-34 GOOD (247-249): "A broken smell shouldn't break the agent" — operator-philosophy gold standard.
- SF-35 GOOD (250): severity_order dict for stable sort.
- SF-36 GOOD (255-260): has_blocking_smell convenience.
- SF-37 GOOD (263-270): format_for_telegram with **empty-on-empty defensive.**

## src/premarket_decision_contract.py — LINE BY LINE

- PDC-1 GOOD (1-16): 16-line docstring with **Lane 1 mandate + 6-line behavior-neutral mandate.** NEW Theme T84.
- PDC-2 GOOD (4-5): "Lane 1: Premarket Official Daily Stock Pick" — operator-philosophy.
- PDC-3 GOOD (7-13): 6-line behavior-neutral mandate (no picks / no scoring change / no paper / no live / no alerts / no runtime mutation).
- PDC-4 GOOD (24): STRATEGY_LANE module constant.
- PDC-5 GOOD (26-28): 3 version constants. Theme T42 expansion.
- PDC-6 GOOD (30-36): 2-decision enum-set + VALID_DECISIONS frozenset.
- PDC-7 GOOD (38-69): OFFICIAL_PICK_REQUIRED_FIELDS 27-tuple.
- PDC-8 GOOD (71-95): OFFICIAL_NO_PICK_REQUIRED_FIELDS 17-tuple.
- PDC-9 GOOD (97-105): OFFICIAL_PICK_NUMERIC_FIELDS 7-tuple.
- PDC-10 GOOD (107-119): OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES 11-cause enum-set.
- PDC-11 GOOD (121-124): SAFETY_FLAGS 2-tuple — must be False enforcement.
- PDC-12 GOOD (127-137): _is_missing with **None+empty-string definition + dict/list-allowed exception.**
- PDC-13 GOOD (132): "Empty dict/list are allowed because some diagnostics may be intentionally present but empty."
- PDC-14 GOOD (140-141): _missing_required_fields list-comprehension.
- PDC-15 GOOD (144-149): _validate_safety_flags with **`is not False` strict-equality enforcement.**
- PDC-16 GOOD (148): "must be false for Lane 1 production-readiness work" — operator-readable error.
- PDC-17 GOOD (152-165): _validate_numeric_fields with **per-field type-coerce + non-negative-vs-positive rule dispatch.**
- PDC-18 GOOD (168-200): validate_official_pick with **6-step validation chain.**
- PDC-19 GOOD (179-180): decision-must-equal enforcement.
- PDC-20 GOOD (182-183): strategy_lane-must-equal enforcement.
- PDC-21 GOOD (188-198): score_components Mapping + risk_flags list + invalidation_conditions list type-checking.
- PDC-22 GOOD (203-241): validate_official_no_pick symmetric to validate_official_pick.
- PDC-23 GOOD (220-222): primary_no_pick_cause whitelist enforcement.
- PDC-24 GOOD (224-234): 4 type-checks.
- PDC-25 GOOD (236-237): watch_only_available strict-bool-enforcement.
- PDC-26 GOOD (244-251): validate_official_decision with **3-way dispatch.**
- PDC-27 GOOD (254-268): contract_summary with **JSON-safe 11-key result.**
- PDC-28 GOOD: **0 BUG findings — 17th cumulative perfect module.**

## src/premarket_readiness_gate.py — LINE BY LINE

- PRG2-1 GOOD (1-11): 11-line docstring with **Lane 1 mandate + 4-line conservative safety.** NEW Theme T85.
- PRG2-2 GOOD (6-10): "no fake picks / no paper trading / no live trading / fail closed into official no-pick when critical data is missing."
- PRG2-3 GOOD (18-19): 2 module defaults.
- PRG2-4 BUG (22-26): _safe_int duplicate. NEW.
- PRG2-5 BUG (29-33): _safe_float duplicate. **59th instance.**
- PRG2-6 GOOD (36-75): _provider_attempt_summary with **10-key aggregator dispatch + isinstance dict guards.**
- PRG2-7 GOOD (38-39): defensive isinstance-dict checks for providers + by_stage.
- PRG2-8 GOOD (48-56): per-provider 6-stat aggregation.
- PRG2-9 GOOD (58-62): ohlcv 4-stat extraction.
- PRG2-10 GOOD (78-191): build_premarket_readiness_decision with **4-fail-CLOSED + ready=True dispatch.**
- PRG2-11 GOOD (86-92): 6-line docstring with **gate semantics.**
- PRG2-12 GOOD (94-97): 4 input normalizations with **min(1.0, ...) + max(1, ...) defensive clamps.**
- PRG2-13 GOOD (100): `int(universe_count * min_fetch_coverage)` — coverage-derived threshold.
- PRG2-14 GOOD (101): `max(1, min(min_fetched_count, required_by_coverage or min_fetched_count))` — 2-min dispatch.
- PRG2-15 GOOD (103): `round(fetched_count / universe_count, 4)` — 4-decimal precision with div-by-zero guard.
- PRG2-16 GOOD (105-114): 4-warning surfacing dispatch.
- PRG2-17 GOOD (116-128): universe_count<=0 -> fail-CLOSED with **NO_PICK_DATA_READINESS_FAILED cause.**
- PRG2-18 GOOD (121): "Official premarket pick skipped because the candidate universe was empty." — operator-readable.
- PRG2-19 GOOD (130-142): fetched_count<=0 -> fail-CLOSED with **NO_PICK_DATA_PROVIDER_DEGRADED cause.**
- PRG2-20 GOOD (144-159): fetched < required -> fail-CLOSED with **inline N/M coverage operator-readable.**
- PRG2-21 GOOD (161-178): provider_degraded >=10 attempts + 0 successes + (errors+empty)>=attempts -> fail-CLOSED.
- PRG2-22 GOOD (180-191): ready=True 9-key result.
- PRG2-23 GOOD (194-196): assert_premarket_readiness_or_no_pick thin convenience wrapper.
- PRG2-24 GOOD: **0 BUG findings (after _safe duplicates) — 18th cumulative perfect module.**

## src/premarket_sanity_gate.py — LINE BY LINE

- PSG-1 GOOD (1-13): 13-line docstring with **Lane 1 mandate + 4-line safety.** NEW Theme T87.
- PSG-2 GOOD (8-12): "fail closed to watch-only/skip when fresh price cannot be verified."
- PSG-3 GOOD (20-23): 4-action module constants.
- PSG-4 GOOD (25): ACTIONABLE_ACTIONS = {SAFE, HALF_SIZE} set.
- PSG-5 BUG (28-34): _safe_float duplicate. **60th instance.**
- PSG-6 GOOD (37-41): _extract_entry_stop with **2-source plan/pick fallback chain.**
- PSG-7 GOOD (44-156): evaluate_premarket_sanity with **8-condition dispatch.**
- PSG-8 GOOD (50): "Returns a JSON-safe decision object." Operator-discipline.
- PSG-9 GOOD (59-69): base 8-key skeleton with **fail-CLOSED defaults to WATCH_ONLY + actionable=False.**
- PSG-10 GOOD (66): "fresh quote unavailable" — operator-readable default reason.
- PSG-11 GOOD (71-77): entry-invalid -> WATCH_ONLY.
- PSG-12 GOOD (79-85): SL-invalid -> WATCH_ONLY.
- PSG-13 GOOD (87-93): current_price-invalid -> WATCH_ONLY.
- PSG-14 GOOD (91): "could not verify fresh price before official selection" — operator-readable.
- PSG-15 GOOD (95-97): gap_pct + sl_buffer_pct compute with **div-by-zero guard.**
- PSG-16 GOOD (99-105): global_action=skip_all -> SKIP_TODAY.
- PSG-17 GOOD (107-113): current_price <= stop_loss -> SKIP_TODAY with **operator-readable inline prices.**
- PSG-18 GOOD (115-121): `gap_pct <= -sl_buffer_pct * 0.6` 60%-eats-SL detection. NEW Theme T86.
- PSG-19 GOOD (123-130): gap>=3% -> HALF_SIZE with **chasing-risk reason.**
- PSG-20 GOOD (132-139): global_action=half -> HALF_SIZE.
- PSG-21 GOOD (141-148): gap<=-1.5% -> HALF_SIZE with **negative-gap reason.**
- PSG-22 GOOD (150-156): default -> SAFE with **size_multiplier=1.0.**
- PSG-23 GOOD (159-166): _apply_half_size with **`max(1, int(qty * 0.5))` floor + 2 audit fields.**
- PSG-24 GOOD (164-165): premarket_size_multiplier + premarket_sanity_reason audit fields.
- PSG-25 GOOD (169-205): apply_premarket_sanity_decisions with **per-candidate 4-audit-field surface.**
- PSG-26 GOOD (186-189): 4 audit fields surfaced.
- PSG-27 GOOD (191-192): half-size mutation if HALF_SIZE.
- PSG-28 GOOD (194-203): actionable -> official OR blocked with **5-key reject record.**
- PSG-29 GOOD (208-222): fetch_latest_price with **try/except -> None defensive + 5-day window.**
- PSG-30 GOOD (211-213): "fail closed" — operator-discipline.
- PSG-31 BUG (215): inline import. **98th cross-cutting.**
- PSG-32 BUG (220): bare Exception.
- PSG-33 GOOD (217): `auto_adjust=False`.
- PSG-34 GOOD (225-279): fetch_market_snapshot with **4-ticker (SPY+QQQ+SOXX+VIX) + global_action 3-tier dispatch.**
- PSG-35 BUG (234): inline import. **99th cross-cutting.**
- PSG-36 BUG (241): bare Exception.
- PSG-37 GOOD (252-254): SPY<=-1.5% -> skip_all.
- PSG-38 GOOD (255-257): SPY<=-0.7% -> half.
- PSG-39 GOOD (259-264): VIX>=25 -> skip_all / VIX>=20 -> half.
- PSG-40 GOOD (266-267): SOXX<=-2% -> warning-only (no global_action change).
- PSG-41 GOOD (282-300): run_premarket_sanity_gate with **fresh-prices fetch + apply + 4-key result.**
- PSG-42 GOOD (286-289): per-ticker fresh-price dict-comprehension with **strip + ticker-empty-skip.**

## src/llm_agent.py — LINE BY LINE

- LLM2-1 GOOD (1-4): 4-line docstring with **4-provider priority + cache + throttle + quota mandate.** NEW Theme T89.
- LLM2-2 GOOD (1-3): "Priority: Claude Sonnet 4.5 (ANTHROPIC_API_KEY) -> Gemini -> OpenAI -> rule-based."
- LLM2-3 BUG (10): import-time `_CACHE_DIR.mkdir(...)` side effect. **33rd mkdir-at-import.**
- LLM2-4 GOOD (11): _CACHE_TTL = timedelta(hours=12).
- LLM2-5 GOOD (13): CLAUDE_MODEL hardcoded. **7th instance.**
- LLM2-6 GOOD (17-19): _cache_key with **MD5 of (ticker, scores, plan).**
- LLM2-7 GOOD (18): `sort_keys=True, default=str` — deterministic.
- LLM2-8 GOOD (22-36): _cache_get with **TZ-aware UTC backward-compat.**
- LLM2-9 GOOD (29-31): "Backward-compatible with older naive cache files" — operator-archaeology gold standard.
- LLM2-10 GOOD (32): `datetime.now(timezone.utc)` — TZ-aware.
- LLM2-11 BUG (34): bare Exception.
- LLM2-12 GOOD (39-45): _cache_put with **try/except -> pass + TZ-aware UTC.**
- LLM2-13 BUG (44): bare Exception.
- LLM2-14 GOOD (49-51): 3 module-level mutable-list state flags. NEW Theme T88.
- LLM2-15 GOOD (52): `_MIN_INTERVAL = 1.5` with **operator-readable Claude tier-1 50RPM justification.**
- LLM2-16 GOOD (55-59): _throttle with **sleep-to-rate-limit pattern.**
- LLM2-17 GOOD (63-73): _rule_based with **top-3-factor sort + 4-line composition + Not-financial-advice footer.**
- LLM2-18 GOOD (64): skip-set for non-numeric scores fields.
- LLM2-19 GOOD (73): "Confirm independently. No certainty implied." — operator-philosophy gold standard.
- LLM2-20 GOOD (77-98): _build_prompt with **trade-type-aware hold-rule dispatch + 5-rule structured output.**
- LLM2-21 GOOD (82): Day-trade hold-rule "intraday only — exit by 3:55 PM ET".
- LLM2-22 GOOD (96): "End with: 'Not financial advice.'" enforcement.
- LLM2-23 GOOD (98): "Plain prose only. No bullets. No markdown. Under 120 words. Complete every sentence." — operator-discipline.
- LLM2-24 GOOD (100-109): _claude with **anthropic SDK + 0.4 temperature + 400 max_tokens.**
- LLM2-25 BUG (101): inline import. **100th cross-cutting.**
- LLM2-26 GOOD (113-124): _gemini with **2-SDK-version fallback + try/except for newer/older SDK.**
- LLM2-27 BUG (114-118): inline imports. **101st + 102nd cross-cutting.**
- LLM2-28 GOOD (115-116): "Note: removed thinking_config (broke in newer SDK). Use simple call." — operator-archaeology.
- LLM2-29 BUG (121): bare Exception.
- LLM2-30 GOOD (128-135): _openai with **gpt-4o-mini + 0.4 temp + 400 tokens.**
- LLM2-31 BUG (129): inline import. **103rd cross-cutting.**
- LLM2-32 GOOD (139-142): _is_quota_error with **6-keyword classifier.**
- LLM2-33 GOOD (146-155): _try_provider with **(text, err) tuple result + throttle.**
- LLM2-34 GOOD (155): `f"{type(e).__name__}: {str(e)[:120]}"` — type-aware error format.
- LLM2-35 GOOD (158-195): _explain_uncached with **4-provider sticky-quota-exhaustion dispatch.**
- LLM2-36 GOOD (163-171): Claude primary with **sticky-quota-exhaust flag flip + operator-readable warn.**
- LLM2-37 GOOD (170-171): "Claude quota/credit exhausted — falling back to Gemini for rest of run" — operator-readable.
- LLM2-38 GOOD (174-183): Gemini fallback with **sticky-flag dispatch.**
- LLM2-39 GOOD (186-191): OpenAI last-resort dispatch.
- LLM2-40 GOOD (193-195): rule-based final fallback.
- LLM2-41 GOOD (198-206): explain_pick with **cache-then-uncached dispatch.**

## src/news_engine.py — LINE BY LINE

- NE-1 GOOD (1-4): 4-line docstring with **2-provider mandate.** NEW Theme T90+T91.
- NE-2 GOOD (14-16): 3 URL templates as module constants.
- NE-3 GOOD (18-20): 3 path/duration module constants.
- NE-4 GOOD (23-29): _load_seen with **try/except -> {} defensive.**
- NE-5 BUG (27): bare Exception.
- NE-6 GOOD (32-44): _save_seen with **TZ-aware UTC + auto-prune older-than-48h.**
- NE-7 GOOD (35): TZ-aware UTC cutoff.
- NE-8 BUG (42): bare Exception.
- NE-9 BUG (44): No atomic. **107th unsafe writer + HIGH RISK** — full rewrite of seen-cache.
- NE-10 GOOD (47-85): fetch_alpaca_news with **env-var-based credential gate + try/except -> [] defensive.**
- NE-11 GOOD (49-53): No-credentials -> operator-readable skip + return [].
- NE-12 GOOD (55): TZ-aware UTC start time.
- NE-13 GOOD (56-62): Headers + params explicit construction.
- NE-14 GOOD (61): `"include_content": "false"` — bandwidth-saving.
- NE-15 GOOD (66-67): Non-200 -> operator-readable HTTP-status print + return [].
- NE-16 GOOD (71-81): Per-item 8-key dict construction with **string-truncation 300/600 chars.**
- NE-17 GOOD (79): published_at fallback chain (created_at -> updated_at).
- NE-18 BUG (83): bare Exception with **operator-readable type+truncated-msg print.**
- NE-19 GOOD (88-120): fetch_yahoo_rss with **20-ticker cap + per-ticker 0.2s sleep + regex-XML parse.**
- NE-20 GOOD (89): "Pull recent news from Yahoo Finance RSS for specific tickers (lightweight backup)." Operator-readable.
- NE-21 GOOD (91): `tickers[:20]` cap ("avoid spamming").
- NE-22 GOOD (94): User-Agent Mozilla — defensive against blocking.
- NE-23 GOOD (97-99): "Parse XML loosely (no feedparser dependency)" — operator-discipline gold standard.
- NE-24 GOOD (100-105): regex with **CDATA-handling 4-pattern (title / link / pub / desc).**
- NE-25 GOOD (106-116): per-item 8-key dict construction with **abs(hash(title)) for unique-id.**
- NE-26 GOOD (117): `time.sleep(0.2)` "be polite".
- NE-27 BUG (118): bare Exception.
- NE-28 GOOD (123-145): fetch_all_news with **2-source dedup-by-id + cache update.**
- NE-29 GOOD (132-134): per-item dedup against seen + add to seen with **TZ-aware UTC.**
- NE-30 GOOD (148-155): append_news_log with **mkdir + jsonl append.**
- NE-31 BUG (153-155): No atomic. **108th unsafe writer.** Append acceptable.
- NE-32 GOOD (158-162): __main__ smoke test. **56th smoke test.**

## src/weekly_review.py — LINE BY LINE

- WR-1 GOOD (1-11): 11-line docstring with **Pillar 5 v0.1 mandate + 4-section grading.** NEW Theme T92.
- WR-2 GOOD (4): "Every Sunday the agent grades itself on the past 7 days" — operator-philosophy.
- WR-3 GOOD (16-19): 4 sibling-module imports for delegation.
- WR-4 BUG (23): import-time `REPORTS.mkdir(...)` side effect. **34th mkdir-at-import.**
- WR-5 GOOD (26-37): grade with **7-tier letter A->F dispatch + emoji-color severity.**
- WR-6 GOOD (37): "F (crisis — pause review needed)" — operator-philosophy gold standard.
- WR-7 GOOD (40-60): what_worked with **n>=2 + avg_R>0.5 thresholds + 2-axis breakdown (trade_type + tag).**
- WR-8 GOOD (60): `notes or ["(no clearly winning categories yet)"]` — defensive non-empty fallback.
- WR-9 GOOD (64-101): rules_violated_on_losers with **B6 wisdom-base lookup + min_confidence=0.85 + max-5 cap.**
- WR-10 BUG (71): inline import. **104th cross-cutting.**
- WR-11 BUG (72): bare Exception.
- WR-12 GOOD (80): `if r >= 0: continue` — only-losers filter.
- WR-13 GOOD (82-89): 6-key context dict for wisdom matching.
- WR-14 BUG (92): bare Exception.
- WR-15 GOOD (96-98): best-by-confidence + truncate to 80-char + operator-readable formatted note.
- WR-16 GOOD (99-100): max-5 cap.
- WR-17 GOOD (103-121): what_failed symmetric to what_worked with **avg_R<-0.3 thresholds.**
- WR-18 GOOD (124-144): recommended_actions with **6-condition dispatch + default + always-append run-script suggestion.**
- WR-19 GOOD (126-127): "F " or "F (" 2-pattern detection — defensive against grade-string variation.
- WR-20 GOOD (129-138): 5-condition dispatch (alpha<-2 / win<30% / SWING-failed / DAY-failed).
- WR-21 GOOD (140-141): default operator-readable ("Continue current strategy — nothing flagged").
- WR-22 GOOD (143): always-append run-hypothesis-review suggestion.
- WR-23 GOOD (147-169): build_report with **9-key result + sibling delegation.**
- WR-24 BUG (148): naive `datetime.now()`. **84th naive.**
- WR-25 GOOD (150-157): 6-helper dispatch (load_picks / metrics / grade / worked / failed / actions / wstats / sectors).
- WR-26 GOOD (172-337): format_telegram with **7-pillar integration + per-pillar try/except -> pass.**
- WR-27 GOOD (175): "Weekly Self-Assessment" — operator-readable header.
- WR-28 GOOD (179-191): 7d Performance section with **closed-picks gate.**
- WR-29 GOOD (193-205): What worked + What failed sections.
- WR-30 GOOD (218-230): T40 Calibration brain footer with **try/except -> pass defensive.**
- WR-31 BUG (220): inline import. **105th + 106th cross-cutting.**
- WR-32 BUG (229): bare Exception.
- WR-33 GOOD (233-267): Pillar 1 status footer (Layer 4 + Layer 5) with **2-pillar try/except.**
- WR-34 BUG (235-237): 3 inline imports. **107th + 108th + 109th cross-cutting.**
- WR-35 BUG (249, 259, 266): 3 bare Exceptions.
- WR-36 GOOD (243-249): Layer 5 self-awareness with **PAUSED/active dispatch + score format.**
- WR-37 GOOD (252-260): Layer 4 hypothesis-journal with **base WR computation.**
- WR-38 GOOD (270-294): Pillar 4 learning-journal & weight-history footer with **5-key by_kind dispatch.**
- WR-39 BUG (272-273): 2 inline imports. **110th + 111th cross-cutting.**
- WR-40 BUG (293): bare Exception.
- WR-41 GOOD (282-285): 4-key by_kind dispatch (lesson_added / pattern_promoted / kill_listed / lesson_deactivated).
- WR-42 GOOD (288-292): Weights moved 3-action breakdown (boost / penalize / kill).
- WR-43 GOOD (297-307): Pillar 5 rolling 30d with **try/except -> pass.**
- WR-44 BUG (299): inline import. **112th cross-cutting.**
- WR-45 BUG (306): bare Exception.
- WR-46 GOOD (310-330): Pillar 6 wow_trend + sector_pnl with **2 try/except.**
- WR-47 BUG (312, 323): 2 inline imports. **113th + 114th cross-cutting.**
- WR-48 BUG (319, 329): 2 bare Exceptions.
- WR-49 GOOD (332-335): Recommended action footer.
- WR-50 GOOD (340-344): format_markdown with **asterisk-double-substitution.**
- WR-51 GOOD (347-351): save_snapshot with **YYYY_MM_DD filename.**
- WR-52 BUG (348): naive `datetime.now()`. **85th naive.**
- WR-53 BUG (350): No atomic for write_text. **109th unsafe writer.**

## CONSOLIDATED CROSS-CUTTING (THIS BATCH)

### NEW Themes T78-T92 (15 new themes in single batch)
- T78 (CSV-HEADER MIGRATION GUARD): PL-X1
- T79 (PORTFOLIO-LEVEL RISK GATE with fail-CLOSED): PRG-X1
- T80 (TIERED-BY-PRICE STOP-LOSS MINIMUM): HB-X1 BUG-5 fix
- T81 (PREFRONTAL-CORTEX NON-NEGOTIABLE FILTER): HB-X1 PR #84
- T82 (CROSS-PROVIDER PRICE-VALIDATION 3-TIER): SF-X1 stale_price
- T83 (FOUNDER-PRINCIPLE-DRIVEN MODULE): SF-X1 PHILOSOPHY.md
- T84 (CONTRACT-VALIDATION-SCHEMA MODULE): PDC-X1
- T85 (PROVIDER-DEGRADATION DETECTION GATE): PRG2-X1
- T86 (60%-OF-SL-BUFFER GAP-DETECTION): PSG-X1
- T87 (4-ACTION SAFE/HALF/SKIP/WATCH dispatch): PSG-X1
- T88 (MUTABLE-LIST MODULE-LEVEL STATE FLAG): LLM2-X1
- T89 (4-PROVIDER LLM FALLBACK CHAIN): LLM2-X1
- T90 (REGEX-XML-PARSER NO-FEEDPARSER): NE-X1
- T91 (POLITE-RATE-LIMITED MULTI-PROVIDER NEWS FETCHER): NE-X1
- T92 (PER-PILLAR-FAIL-DEFENSIVE FOOTER ASSEMBLY): WR-X1

### Theme T57 (PERFECT MODULES) EXPANSION -> 18 cumulative
- +3 this batch: PRG (16th) + PDC (17th) + PRG2 (18th).

### Theme T6 (atomic writes) UPDATE
- **+5 new unsafe writers** (PL x2 + HB + NE + WR) — 109 cumulative.
- **Tally: 13 safe / 109 unsafe / 122 = ~89.3% UNSAFE.**

### Lane 1 Pipeline END-TO-END TRACED — 8-MODULE CHAIN
- PRG2 (data readiness) -> SCO/PSC (scoring) -> SF (smell faculty) -> HB (5 hard blocks PR #84) -> PSG (sanity 4-action) -> PRG (portfolio risk gate) -> PDC (contract validation) -> PL (CSV log).
- Document `docs/LANE_1_PIPELINE.md`.

### Pillar 5 Weekly Self-Assessment END-TO-END TRACED — 7-PILLAR INTEGRATION HUB
- WR top-level Pillar 5 + 6 footer pillars.
- Document `docs/PILLAR_5_WEEKLY_REVIEW.md`.

## SUMMARY (Batch 83 — 10-FILE)

| File | Show-stop | Data/safety | Code smell | Good code | Findings |
|---|---:|---:|---:|---:|---:|
| pick_logger | 4 | 0 | 0 | 38 | 42 |
| portfolio_risk_gate | 3 | 0 | 0 | 34 | 37 |
| hard_blocks | 11 | 0 | 0 | 45 | 56 |
| smell_faculty | 4 | 0 | 0 | 33 | 37 |
| premarket_decision_contract | 0 | 0 | 0 | 28 | 28 |
| premarket_readiness_gate | 2 | 0 | 0 | 22 | 24 |
| premarket_sanity_gate | 5 | 0 | 0 | 37 | 42 |
| llm_agent | 11 | 0 | 0 | 30 | 41 |
| news_engine | 7 | 0 | 0 | 25 | 32 |
| weekly_review | 22 | 0 | 0 | 30 | 52 |
| **TOTAL** | **69** | **0** | **0** | **322** | **391** |

## TOP 12 CRITICAL FIXES from Batch 83

1. **15 NEW THEMES T78-T92 — DOCUMENT IN BULK:** `docs/THEMES_T78_T92.md`. (3 hours)
2. **LANE 1 PIPELINE end-to-end DOC** (8-module chain PRG2->SCO/PSC->SF->HB->PSG->PRG->PDC->PL): `docs/LANE_1_PIPELINE.md`. (1.5 hours)
3. **PILLAR 5 WEEKLY REVIEW 7-pillar integration DOC:** `docs/PILLAR_5_WEEKLY_REVIEW.md`. (1 hour)
4. **CRITICAL HB-X1 fail-OPEN FIX in safety-critical module:** `_safe_pct_change` returns 0.0 on yfinance error -> SILENTLY SKIPS weak_sector check. For prefrontal-cortex module, fail-OPEN is risky. Add fail-LOUD warn or treat-all-sectors-as-weak fallback. (30 min)
5. **HB-X1 cache-comment-lies FIX:** Comment says "Cached to avoid repeated yfinance calls" but NO actual caching implemented. Either implement cache or fix comment. (30 min)
6. **PL-X1 ATOMIC WRITE for header migration (104th unsafe + HIGH RISK):** Apply PE3-X1 pattern (tmp+rename) to _migrate_header_if_needed. (15 min)
7. **PR #84 PREFRONTAL-CORTEX archaeology DOC:** Document `docs/PREFRONTAL_CORTEX_PATTERN.md` using HB-X1 as exemplar. (45 min)
8. **PDC-X1 SAFETY_FLAGS gold standard PATTERN DOC:** `docs/SAFETY_FLAGS_ENFORCEMENT_PATTERN.md`. (30 min)
9. **WR-X1 PER-PILLAR-FAIL-DEFENSIVE FOOTER ASSEMBLY DOC:** `docs/MULTI_PILLAR_DEFENSIVE_FOOTER.md`. (30 min)
10. **NE-X1 atomic write for NEWS_CACHE rewrite (107th HIGH RISK):** Apply tmp+rename. (15 min)
11. **WR-X1 14 inline imports** — consolidate at top-of-module if practical. (1 hour)
12. **Theme T36 _safe_float at 60 modules — TOP PRIORITY EXTRACTION:** Extract `src/_safe.py`. (4 hours)

## COVERAGE TRACKER

| Phase | Status | Cumulative |
|---|---|---:|
| Phase G | done | 30/~30 |
| Phase H | active | 161/~135 |
| Total true line-by-line | **+10 files (10 successful, 0 failures)** | **~382 of ~395 (~96.7%)** |

End of Batch 83.
