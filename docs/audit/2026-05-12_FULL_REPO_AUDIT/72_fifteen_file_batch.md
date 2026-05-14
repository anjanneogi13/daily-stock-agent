# Batch 66 — 15-FILE MEGA BATCH — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files (15):** self_awareness (139), signal_journal (236), smell_faculty (270), agent_memoir (193), candidate_diagnostics (229), missing_data_gate (162), market_guard (115), market_data_health (227), provider_failure_taxonomy (251), market_calendar (214), portfolio_risk_gate (278), opening_range_scanner (277), parallel_scorer (176), picks_csv (46), position_monitor (130)
**Phase:** F. Files 20-34 of ~38. **First 15-file batch — confirms reliable maximum.**
**Total LOC audited this batch: ~2,943 lines.**

## TOP HEADLINE FINDINGS (one per file)

1. **SA-X1: self_awareness.py** is **T45 / Pillar 5 — ROLLING-30D CONFIDENCE INTERVALS** (139 lines). **Wilson-score CI** for win-rate + **mean-R standard error CI** + 3-tier verdict (EDGE_CONFIRMED / EDGE_BROKEN / INCONCLUSIVE). **Pure stdlib (no scipy/numpy)** — first audited "honest statistical CI" module. Per Batch 64 PE3 cross-cutting probability discipline.
2. **SJ2-X1: signal_journal.py** is **THE APPEND-ONLY SIGNAL→OUTCOME LOG** (236 lines). 7 bucketing helpers (composite/d2e/vol/monster/p_win + primary_tag) + build_signals + log_pick + attach_outcome + load_closed. **CALIBRATED 2026-05-04 from 39-pick distribution archaeology in bucket_composite.** Producer for B62 PR-X1 + B58 WP-X1 + B59 CL-X1.
3. **SF-X1: smell_faculty.py** is **THE PROACTIVE-DANGER 7-SMELL DETECTOR** (270 lines). 4-severity enum (CRITICAL/HIGH/MED/LOW) + Smell @dataclass + ALL_SMELLS registry (7 smells). Per founder principle: "warn like a wise friend, not just block silently." **smell_stale_price (E2c) consumes Finnhub cross_validate_price** (B57 FH-X2). **Closes price-integrity defense pipeline** (B14 MDH + B57 FH + B64 PE3 + this batch).
4. **AM2-X1: agent_memoir.py** is **THE PERSISTENT-IDENTITY NARRATIVE** (193 lines). MISSION_STATEMENT const + biggest_win/biggest_loss with narrative text + 4-tier current_focus (n<30 OBSERVATION → wr<40% → wr≥50% → middle) + promise_to_anjan. **Per docstring "founder insight 2026-05-04: Agent should not forget."** **First audited identity/narrative module.**
5. **CD-X1: candidate_diagnostics.py** is **THE LANE-1 FUNNEL EXPLAINER** (229 lines). 4 rejection-stage handlers (hard / sanity / portfolio_risk / missing_data) + 16-key stage_counts + per-candidate summary with 19 fields. **Reporting-only.** **Per Batch 65 PDC + OPA + OAL cross-cutting** — joins as 4th formal-contract-companion module.
6. **MDG-X1: missing_data_gate.py** is **THE FAIL-CLOSED COMPLETENESS GUARD** (162 lines). 8 critical fields + 11 validation rules including **stop_loss<entry AND take_profit>entry semantic checks** + carries-forward premarket_actionable + portfolio_risk_passed downstream signals. **Last gate before OPA artifact write.**
7. **MG-X1: market_guard.py** is **THE MARKET-WIDE TRINITY** (115 lines). vix_level + spy_trend (above_50dma + above_200dma) + sector_strength (12-sector ETF map) + classify_trade_type + classify_with_day_score. **PR #67 archaeology** — old momentum>0.75 AND volume>0.7 was IMPOSSIBLY HIGH (28 picks all "swing"). 5th DATED-archaeology in audit.
8. **MDH2-X1: market_data_health.py** is **THE PROVIDER-HEALTH TELEMETRY DAEMON** (227 lines). **threading.Lock for concurrency safety + ATOMIC WRITE** (lines 76-78 tmp + replace) + per-provider + per-stage + run-counters + samples (max 30) + integrates B66 PFT-X1 canonical taxonomy. **2nd audited atomic writer.**
9. **PFT-X1: provider_failure_taxonomy.py** is **THE 11-CATEGORY CANONICAL FAILURE TAXONOMY** (251 lines). CANONICAL_FAILURE_TYPES set + bidirectional legacy↔canonical maps + frozen ProviderFailureClassification dataclass + classify_provider_failure with **9-keyword-list dispatch** + classify_legacy_provider_error wrapper. **2nd audited frozen dataclass.** Per Batch 14 MDH-X1 cross-cutting failure-bucket evolution.
10. **MC-X1: market_calendar.py** is **T51 — HARDCODED 3-YEAR NYSE CALENDAR** (214 lines). **29 holidays + 9 early-close days** for 2026-2028 + **renewal_urgency 4-tier (none/soft/urgent/critical) by months_left** + plain-English renewal_message. **Renewal warning surfaces in meta_brain weekly digest** (B65 MB-X1). First audited NO-INTERNET-DEPENDENCY data module.
11. **PRG-X1: portfolio_risk_gate.py** is **THE LANE-1 PORTFOLIO-LIMIT GATE** (278 lines). 6 risk_config knobs + 8 per-candidate fail conditions + sector + tag exposure caps + max_positions slot enforcement. **Per Batch 65 cross-cutting Lane 1 4-gate pipeline** — this is gate #3.
12. **ORS-X1: opening_range_scanner.py** is **THE WATCH-ONLY INTRADAY BREAKOUT SCANNER** (277 lines). **TZ-aware** (ET zoneinfo) + opening_range_bounds + calculate_opening_range + detect_opening_range_breakout with 5 anti-chase blockers. **Pure/testable** — no data fetch. 14th TZ-aware module.
13. **PS2-X1: parallel_scorer.py** is **THE THREADPOOLEXECUTOR ORCHESTRATOR** (176 lines). 10-worker pool dispatching `_score_one(tk, df, cfg)` + 8-step per-ticker pipeline (indicators → fund → news → composite → wl_boost → pattern_multiplier → day_score → trade_plan → monster → wisdom_consult). **Per B62 SC-X1 + B63 IN-X1 cross-cutting**, this is the SCORING ORCHESTRATOR for the producer chain. **M1 archaeology** caches regime once-per-run on cfg.
14. **PC-X1: picks_csv.py** is **THE picks_log.csv MUTABLE-FIELD UPDATER** (46 lines, smallest in batch). 2 helpers: read_open_picks + update_pick_row. Used by intraday_monitor for peak_price/current_sl/trail_active mutations. Per Batch 64 PE3-X2 atomic-write cross-cutting — **THIS IS UNSAFE WRITE.**
15. **PM-X1: position_monitor.py** is **THE MAX-HOLD-DAYS LIFECYCLE FLAGGER** (130 lines). 3-tier max_hold by trade_type (day=1 / swing=10 / multi=30 / default=14) + 2-severity (over / near) + Telegram-formatted alerts. **Single source of truth = picks_log.csv** (no positions.json — explicit anti-sync-bug architecture per docstring).

## CRITICAL CROSS-FILE FINDINGS (this batch)

- **PRICE-INTEGRITY DEFENSE-IN-DEPTH NOW 4-LAYER (Theme T23 update):** B14 MDH-X1 pre-pick wrong-data telemetry → B57 FH-X2 cross_validate_price 2-source consensus → **B66 SF-X1 smell_stale_price (this batch) blocks at smell-faculty stage** → B64 PE3-X3 unreachable_entry post-pick detection. **First audited END-TO-END price-integrity pipeline.** ✅
- **THEME T26 (NIGHTLY ORCHESTRATOR) cross-cutting:** B65 NC2-X1 8-step + this batch PS2-X1 ThreadPoolExecutor + this batch SA-X1 Pillar 5 monthly_calibration form **3-pillar orchestration architecture.**
- **PFT-X1 + MDH2-X1 cross-cutting:** Bidirectional legacy↔canonical taxonomy mapping is **first audited backward-compat schema-evolution helper.** Catalog as Theme T27 (taxonomy-evolution bridge).
- **MDH2-X1 cross-cutting:** ATOMIC WRITE tally update — **7 safe / 38 unsafe / 45 = ~84% UNSAFE** (PC-X1 unsafe + MDH2-X1 safe).
- **TZ-aware tally:** 13 → 15 (MDH2 + ORS).
- **Lane 1 pipeline 5-gate composite NOW COMPLETE:** PRG2 readiness (B65) → PSG sanity (B65) → PRG portfolio_risk (this batch PRG-X1) → MDG missing_data (this batch MDG-X1) → OPA artifact (B65) → OAL re-validation (B65). **5-gate lifecycle audited end-to-end.**

## src/self_awareness.py — LINE BY LINE

- SA-1 GOOD (1-12): 12-line docstring with **"Pure stdlib — no scipy/numpy"** explicit dep statement.
- SA-2 GOOD (19): Single import from signal_journal — minimal coupling.
- SA-3 GOOD (23-31): wilson_ci with z=1.96 default + n<=0 defensive.
- SA-4 GOOD (34-44): mean_r_ci with **n<2 degenerate-case shortcut** (mean only, no variance).
- SA-5 GOOD (48-59): _within_days with 2-key fallback (evaluated_on → pick_date).
- SA-6 BUG (57): bare Exception → continue (graceful but Theme T1).
- SA-7 GOOD (63-107): rolling_window with **6-line example output in docstring.**
- SA-8 GOOD (88-94): **3-condition verdict logic** — needs n≥20 AND CI not straddling 0/0.5.
- SA-9 GOOD (96-107): Schema-stable 11-key return dict.
- SA-10 GOOD (110-122): format_footer with **🟢/🔴/🟡 emoji per verdict** + 95% CI suffix.
- SA-11 GOOD (125-139): monthly_calibration runs 3 windows (30/60/90d) + **0.20-mean-R delta trend classification** (improving/stable/decaying).

## src/signal_journal.py — LINE BY LINE

- SJ2-1 GOOD (1-29): **29-line docstring with full row schema example.**
- SJ2-2 BUG (36): mkdir at import time. **14th cross-cutting import-time side-effect.**
- SJ2-3 GOOD (42-64): bucket_composite with **CALIBRATED 2026-05-04 archaeology** — 11-line comment explaining old (93% mid) vs new distribution. Per B65 cross-cutting calibration archaeology gold standard.
- SJ2-4 GOOD (61-64): 4 thresholds with operator-readable comments per bucket.
- SJ2-5 GOOD (67-76): bucket_d2e with 4-state output ("none" for None/empty/negative).
- SJ2-6 GOOD (79-92): bucket_vol with **'extreme' tier 2026-05-04 archaeology** (2.5x split).
- SJ2-7 GOOD (95-103): bucket_monster 3-tier.
- SJ2-8 GOOD (106-119): bucket_p_win 4-tier with operator-readable per-tier rationale.
- SJ2-9 GOOD (122-124): primary_tag 1-line helper. Per B62 SC-12 + this PRG-X1 cross-cutting **3-module tag-extraction duplication** (now 4 with PRG-X1).
- SJ2-10 GOOD (127-166): build_signals with **DEFENSIVE multi-field-naming archaeology** (lines 130-133) — "100% buckets were 'unknown'" bug documented.
- SJ2-11 GOOD (138-155): 5 chained-or fallbacks for composite/tag/vol/monster/p_win.
- SJ2-12 GOOD (172-188): log_pick — append-only.
- SJ2-13 BUG (187): No `newline=""` in csv-style write (here it's jsonl so less critical, but pattern issue).
- SJ2-14 BUG (187-188): **NO ATOMIC append write.** Acceptable for append-only log. ✅
- SJ2-15 GOOD (191-220): attach_outcome with **find-and-rewrite-whole-file pattern.**
- SJ2-16 BUG (217-219): Whole-file rewrite WITHOUT atomic. **39th unsafe writer.** Per B64 PE3-X2 cross-cutting — should use tmp+replace for this jsonl rewrite (could lose journal on crash).
- SJ2-17 GOOD (199, 208): Avoids re-attaching to already-closed rows (`r.get("outcome") is None`).
- SJ2-18 GOOD (212-213): **win/loss derived from r_multiple sign.**
- SJ2-19 GOOD (223-236): load_closed filters to outcome ∈ {win, loss}.

## src/smell_faculty.py — LINE BY LINE

- SF-1 GOOD (1-17): **17-line docstring with founder principle PHILOSOPHY.md citation + 4-severity enum + per-smell purity statement.**
- SF-2 GOOD (23-28): Smell @dataclass with 4 fields + blocking default False.
- SF-3 GOOD (35-56): smell_earnings_imminent with **3-tier (1d=CRITICAL+block, 3d=HIGH, 7d=MED).** Per B53 NS / B62 PR-X2 catalyst tables cross-cutting — **5th audited earnings-proximity dispatcher.**
- SF-4 GOOD (62): "Finding #2 fix" archaeology — 3-key fallback for rsi extraction. Theme T13 silent-default-fill defense.
- SF-5 GOOD (59-76): smell_extreme_rsi 2-tier (85=CRITICAL, 75=HIGH).
- SF-6 GOOD (79-92): smell_volume_spike 4x threshold.
- SF-7 GOOD (95-111): smell_gap_up 2-tier (5%=HIGH, 3%=MED).
- SF-8 GOOD (114-132): smell_low_liquidity 2-tier (100k=CRITICAL+block, 500k=HIGH).
- SF-9 GOOD (135-148): smell_tight_stop with `0 < risk_pct < 0.8%` whipsaw threshold.
- SF-10 GOOD (154-224): smell_stale_price (E2c) — **THE FINNHUB CROSS-VALIDATION SMELL.**
- SF-11 GOOD (155-170): **17-line docstring** with 4 catch-cases + 3-tier severity + ~0.3-1s overhead disclosure.
- SF-12 GOOD (174-176): "Can't validate without inputs — let other smells catch" rationale comment.
- SF-13 GOOD (178-181): try/except around finnhub_data import — **lambda-no-op fallback equivalent** (return None silent).
- SF-14 GOOD (184-208): cross_validate_price call with **distinguish primary_invalid from disagreement** branches.
- SF-15 GOOD (211-221): Soft-warn 2-5% disagreement tier.
- SF-16 GOOD (227-235): **ALL_SMELLS registry** with 7 entries. **Per B59 PI-X1 detector registry cross-cutting** — 2nd audited registry pattern.
- SF-17 GOOD (238-252): sniff with **try/except per smell** ("broken smell shouldn't break the agent") + severity-sorted output.
- SF-18 BUG (247): bare Exception → continue. Theme T1 (acceptable defensive).
- SF-19 GOOD (255-260): has_blocking_smell short-circuit.
- SF-20 GOOD (263-270): format_for_telegram bullet renderer.

## src/agent_memoir.py — LINE BY LINE

- AM2-1 GOOD (1-12): **12-line docstring with FOUNDER QUOTE archaeology.**
- AM2-2 GOOD (24-29): MISSION_STATEMENT const — **first audited mission-statement constant.**
- AM2-3 BUG (32-36): _safe_float duplicate (**17th instance**).
- AM2-4 GOOD (39-47): _load_closed_picks with 4-state filter (tp_hit/sl_hit/expired/day_close).
- AM2-5 BUG (43): No `newline=""`.
- AM2-6 GOOD (50-62): _load_learning_events.
- AM2-7 BUG (60): bare Exception. Theme T1.
- AM2-8 GOOD (65-83): _biggest_win with **NARRATIVE TEXT** for the win — first-person narrative.
- AM2-9 GOOD (86-110): _biggest_loss with **EARNINGS-WARNING ENRICHMENT** when d2e≤7. **Per Batch 51 EA + B62 PR-X1 catalyst cross-cutting.**
- AM2-10 GOOD (113-129): _summarize_recent_learning with **TZ-aware datetime.now(timezone.utc)** + 7-day cutoff. ✅ TZ-aware adds to tally.
- AM2-11 GOOD (132-188): write_memoir with **4-tier current_focus narrative dispatch** based on n + win_rate.
- AM2-12 GOOD (140-145): n<30 → "OBSERVATION MODE — collecting data, not making big changes." **Per Batch 50 cross-cutting OBSERVE-MODE theme** — 21st instance.
- AM2-13 GOOD (162-184): **11-key memoir** with identity / lifetime_stats / biggest_win / biggest_loss / current_focus / what_im_proud_of / recent_learning / promise_to_anjan.
- AM2-14 BUG (187): **NO ATOMIC WRITE.** **40th unsafe writer.**
- AM2-15 GOOD (191-193): __main__ smoke test with json.dumps. **17th __main__.**

## src/candidate_diagnostics.py — LINE BY LINE

- CD-1 GOOD (1-10): 10-line docstring with 4 explanation purposes + reporting-only safety.
- CD-2 BUG (17-28): _safe_value duplicate of B65 OPA-7 (similar but list-cap=10 vs 25, dict-cap=30 vs 75). **Drift between modules.**
- CD-3 GOOD (31-68): summarize_candidate with **19-key compact summary.**
- CD-4 GOOD (50-54): news_action_window 3-key chained fallback.
- CD-5 GOOD (61-64): premarket_action 4-key chained fallback.
- CD-6 GOOD (71-72): _summaries 1-line wrapper.
- CD-7 GOOD (75-81): _ticker_set with strip + upper normalization.
- CD-8 GOOD (84-89): _match_candidate_by_ticker with normalized comparison.
- CD-9 GOOD (92-152): 4 PARALLEL rejection-stage handlers (_hard_blocked / _sanity / _portfolio_risk / _missing_data). **Architectural symmetry.** Per Batch 65 cross-cutting Lane 1 pipeline.
- CD-10 GOOD (94-105): _hard_blocked_details with **fallback to candidate-by-ticker lookup** when item.candidate is empty.
- CD-11 GOOD (155-229): build_candidate_diagnostics with **16 named kwargs + 16-key stage_counts.**
- CD-12 GOOD (197-213): Stage counts include set-difference math (scored_not_filtered / filtered_not_capped) — **bidirectional integrity check.** ✅
- CD-13 GOOD (185-191): rejected_candidates accumulator + extra_rejections support.

## src/missing_data_gate.py — LINE BY LINE

- MDG-1 GOOD (1-15): **15-line docstring with 4 SAFETY contracts + fail-closed mission.**
- MDG-2 GOOD (22-31): CRITICAL_OFFICIAL_PICK_FIELDS 8-tuple.
- MDG-3 BUG (38-53): _safe_float + _safe_int duplicates (**18th + 19th instance**).
- MDG-4 GOOD (56-78): official_pick_required_field_snapshot with **13-key normalized output** including sanity + portfolio_risk passed-flags.
- MDG-5 GOOD (81-127): validate_official_pick_required_data with **11 distinct validation rules.**
- MDG-6 GOOD (96-97): trade_type ∈ {"day", "swing"} membership check.
- MDG-7 GOOD (116-119): **stop_loss < entry AND take_profit > entry semantic checks.** Operator-critical sanity. ✅
- MDG-8 GOOD (122-125): **Carries-forward upstream gate signals** (premarket_actionable + portfolio_risk_passed) — fail-closed if either is False.
- MDG-9 GOOD (130-162): apply_missing_data_gate with **per-rejection rich error envelope** (5 keys: ticker / rejection_stage / block_type / reason / missing_or_invalid_fields / required_field_snapshot).
- MDG-10 GOOD (149-152): On pass → stamps `missing_data_gate.passed=True` + snapshot for downstream traceability.

## src/market_guard.py — LINE BY LINE

- MG-1 GOOD (1): 1-line docstring.
- MG-2 BUG (1): UNDERSELLS — 5 functions deserve mention.
- MG-3 GOOD (5-11): vix_level with 0.0 fail-safe.
- MG-4 BUG (10): bare Exception → 0.0. Theme T1.
- MG-5 GOOD (13-26): spy_trend with **DEFAULT-TRUE on length<200** — defaults to bullish stance when insufficient data. **Theme T11 fail-OPEN-by-accident** — should default to False/None on insufficient data per safety principle.
- MG-6 BUG (25-26): Same fail-open default. **Critical: returns above_50dma=True on EXCEPTION** — masks data outage as bullish.
- MG-7 GOOD (28-51): sector_strength with 12-sector default ETF map.
- MG-8 BUG (49): bare Exception continue.
- MG-9 GOOD (53-103): classify_trade_type with **PR #67 archaeology (lines 56-61)** — old impossible thresholds → 28 picks all swing. ✅
- MG-10 GOOD (87-93): 4-condition is_day check with operator comments per condition.
- MG-11 GOOD (102-103): Default to swing as "safer default for marginal setups." ✅
- MG-12 GOOD (106-116): classify_with_day_score uses dedicated day_trading_score gate.

## src/market_data_health.py — LINE BY LINE

- MDH2-1 GOOD (1-10): 10-line docstring with **3 distinguish-cases mission** + dependency-free claim.
- MDH2-2 GOOD (14): `import threading` — concurrency awareness.
- MDH2-3 GOOD (17): zoneinfo import.
- MDH2-4 GOOD (19-24): 4 imports from sister taxonomy module.
- MDH2-5 GOOD (26-29): 4 module constants (DATA_DIR / ET / _LOCK / MAX_SAMPLES).
- MDH2-6 GOOD (28): **`threading.Lock()` module-level singleton** — explicit concurrency safety. Per Batch 64 LA-X2 cross-cutting parallel-safety theme — first audited proper Lock usage.
- MDH2-7 GOOD (32-33): _today_et with TZ-aware UTC→ET conversion.
- MDH2-8 GOOD (36-38): health_path with date-stamped filename.
- MDH2-9 GOOD (41-47): classify_provider_error backward-compat wrapper.
- MDH2-10 GOOD (50-59): _blank_summary with **6-key skeleton** including timestamp_utc.
- MDH2-11 GOOD (62-70): _load with isinstance check + blank fallback.
- MDH2-12 BUG (68): bare Exception → blank. Theme T1.
- MDH2-13 GOOD (73-78): **_save IS ATOMIC** (tmp + replace) + sort_keys=True. ✅ **2nd audited atomic writer.**
- MDH2-14 GOOD (81-94): _provider_bucket with **canonical-keyed failure_types dict initialization.**
- MDH2-15 GOOD (97-104): _stage_bucket 4-counter init.
- MDH2-16 GOOD (107-186): record_market_data_event with **with _LOCK:** wrapping all mutations.
- MDH2-17 GOOD (123): result whitelist normalization to {"success", "empty", "error"}.
- MDH2-18 GOOD (125-134): failure_detail computation only when not success.
- MDH2-19 GOOD (156-159): If safe_error in pb increment specific else fallback to provider_error.
- MDH2-20 GOOD (171-181): Sample buffer with 30-cap + 240-char message truncation.
- MDH2-21 GOOD (184-186): **"Telemetry must never break the picker."** — top-level swallow Exception with comment justification.
- MDH2-22 GOOD (189-214): write_market_data_run_summary with kwargs-only enforcement.
- MDH2-23 GOOD (217-227): summarize_market_data_health 1-call reader.

## src/provider_failure_taxonomy.py — LINE BY LINE

- PFT-1 GOOD (1-8): 8-line docstring with **observe-only labels mission.**
- PFT-2 GOOD (15-27): CANONICAL_FAILURE_TYPES set with **11 distinct categories.**
- PFT-3 GOOD (30-42): LEGACY_ERROR_BUCKET_BY_FAILURE_TYPE 11-row dict.
- PFT-4 GOOD (45-52): FAILURE_TYPE_BY_LEGACY_ERROR_BUCKET 6-row reverse dict.
- PFT-5 GOOD (55-62): @dataclass(frozen=True) ProviderFailureClassification 3-field.
- PFT-6 GOOD: **2nd audited frozen dataclass** (after B63 TG-9). Per Theme T22 BEST PRACTICE.
- PFT-7 GOOD (64-67): _raw_text with BaseException subclass-aware formatting.
- PFT-8 GOOD (70-183): classify_provider_failure with **9-keyword-list dispatch** — operator-readable and extensible.
- PFT-9 GOOD (84-93): Multi-source raw text composition (exc + result + stage + status).
- PFT-10 GOOD (96-97): Empty-input fallback.
- PFT-11 GOOD (99-106): rate_limited 5-keyword detection (incl yfinance-specific YFRateLimitError).
- PFT-12 GOOD (108): timeout 3-keyword detection.
- PFT-13 GOOD (111-116): market_closed 4-keyword.
- PFT-14 GOOD (119-125): stale_data 4-keyword.
- PFT-15 GOOD (127-135): symbol_not_found 7-keyword (incl 404, delisted).
- PFT-16 GOOD (138-145): missing_quote 6-keyword.
- PFT-17 GOOD (148-155): missing_intraday_bars 6-keyword (incl opening-range-specific).
- PFT-18 GOOD (158-164): missing_history 5-keyword.
- PFT-19 GOOD (167): empty_response 3-keyword.
- PFT-20 GOOD (170-180): provider_exception 9-keyword catch-all (BEFORE unknown).
- PFT-21 GOOD (183): unknown_provider_failure final fallback.
- PFT-22 GOOD (186-198): legacy_error_bucket_for_failure_type + reverse helpers.
- PFT-23 GOOD (202-214): classify_legacy_provider_error with **special unauthorized handling** preserving legacy bucket name. **Schema-preservation gold standard.** ✅
- PFT-24 GOOD (217-247): classify_provider_failure_detail with **legacy-first dispatch then canonical fallback.**
- PFT-25 GOOD (250-251): is_canonical_failure_type 1-line membership check.

## src/market_calendar.py — LINE BY LINE

- MC-1 GOOD (1-17): **17-line docstring with API + ANNUAL RENEWAL contract.**
- MC-2 GOOD (27-62): US_MARKET_HOLIDAYS set with **per-holiday inline comment naming the holiday + observance rule.** **Calibration archaeology gold standard.** Per B62 PR-X2 cross-cutting.
- MC-3 GOOD (35, 47, 50, 53): Inline observance-rule explanations ("Jul 4 = Sat", "Dec 25 = Sat", "Jan 1 = Sat, no observance NYE 2028").
- MC-4 GOOD (65-80): US_MARKET_EARLY_CLOSE 9-day set.
- MC-5 GOOD (86-96): _to_date with **5-input-type normalization** (None/datetime/date/str/error).
- MC-6 GOOD (99-117): 4 simple bool checks (weekend / holiday / early_close / trading_day).
- MC-7 GOOD (120-127): reason_market_closed 3-state return.
- MC-8 GOOD (130-137): next_trading_day with **max_lookahead 14d guard** + RuntimeError.
- MC-9 GOOD (140-147): previous_trading_day mirror.
- MC-10 GOOD (153-162): cached_years + years_remaining.
- MC-11 GOOD (165-167): needs_renewal 2-arg threshold check.
- MC-12 GOOD (170-178): renewal_urgency **4-tier (none/soft/urgent/critical) by months_left math.**
- MC-13 GOOD (181-196): renewal_message with **escalating icons + 3-suffix dispatch** including critical "agent will silently break on next holiday."
- MC-14 GOOD (202-214): market_status_today 7-key snapshot.

## src/portfolio_risk_gate.py — LINE BY LINE

- PRG-1 GOOD (1-13): 13-line docstring with **4-Safety contracts.**
- PRG-2 GOOD (24-26): 3 DEFAULT constants.
- PRG-3 BUG (29-42): _safe_float + _safe_int duplicates (**20th + 21st instance**).
- PRG-4 GOOD (45-47): _candidate_sector with "Unknown" default.
- PRG-5 BUG (50-53): _candidate_tag — **4th tag-extraction duplicate**. Per cross-cutting Theme T8.
- PRG-6 GOOD (56-58): _candidate_score with 0.0 default.
- PRG-7 GOOD (66-88): _risk_profile with **risk_dollars + risk_pct computed from quantity × (entry-stop)** + None-safe handling.
- PRG-8 GOOD (91-106): load_open_positions_from_picks_log with **`newline=""` + encoding="utf-8"** + watch_only filter. ✅
- PRG-9 BUG (104): bare Exception → []. Theme T1.
- PRG-10 GOOD (109-123): _existing_sector + _existing_tag counts.
- PRG-11 GOOD (126-140): build_portfolio_risk_config with **6-key normalized config** + per-key max(1, ...) floor enforcement.
- PRG-12 GOOD (130-131): account_size + risk_per_trade_pct sane defaults (10000 / 1.0).
- PRG-13 GOOD (143-192): evaluate_candidate_portfolio_risk with **8 sequential fail conditions** + early-return tuple-style.
- PRG-14 GOOD (170-174): stop_loss < entry + take_profit > entry semantic checks. Same as MDG-7 cross-cutting.
- PRG-15 GOOD (182): **5% tolerance on per-trade-risk vs configured limit** (`* 1.05`).
- PRG-16 GOOD (186-190): Sector + tag exposure caps (after open-positions baseline).
- PRG-17 GOOD (195-278): apply_portfolio_risk_gate with **score-sorted iteration + slot consumption + counter mutation.**
- PRG-18 GOOD (218): `sorted(..., key=_candidate_score, reverse=True)` — best-score-first.
- PRG-19 GOOD (221-234): max_positions slot enforcement BEFORE risk check (cheaper).
- PRG-20 GOOD (244-252): rich block envelope (5 keys + nested detail).
- PRG-21 GOOD (260-264): On pass → stamp candidate.portfolio_risk for downstream traceability.
- PRG-22 GOOD (267-276): 9-key summary with final counts.

## src/opening_range_scanner.py — LINE BY LINE

- ORS-1 GOOD (1-18): **18-line docstring with bar-shape example.**
- ORS-2 GOOD (27-29): TZ-aware ET zoneinfo + named constants.
- ORS-3 GOOD (32-47): _as_dt with **naive→ET interpretation default + Z→+00:00 normalization.**
- ORS-4 GOOD (43): Defensive TypeError raise on unknown type.
- ORS-5 GOOD (50-57): _num with 3-state defensive (None / "" / "None").
- ORS-6 GOOD (60-61): _vol 1-line wrapper.
- ORS-7 GOOD (64-73): _session_date inference with **explicit ValueError on empty bars.**
- ORS-8 GOOD (76-88): opening_range_bounds with TZ-aware datetime.combine.
- ORS-9 GOOD (91-155): calculate_opening_range with **ready=False+blockers schema-stable error path.** Per cross-cutting schema-stable gold standard.
- ORS-10 GOOD (102): bars sorted by ts deterministically.
- ORS-11 GOOD (114-117): Window filter on opening range half-open `[start, end)`.
- ORS-12 GOOD (120-128): 2 distinct blockers (incomplete + missing_prices).
- ORS-13 GOOD (140-155): Width % computation + integer volume sum.
- ORS-14 GOOD (158-171): latest_post_range_bar with same sorting.
- ORS-15 GOOD (174-277): detect_opening_range_breakout with **5 anti-chase blockers + 6 thresholds + 1.5R fixed risk-reward.**
- ORS-16 GOOD (193): Same sorting via list().
- ORS-17 GOOD (201-220): 2 schema-stable not-ready/no-post-bar early returns.
- ORS-18 GOOD (228-229): avg_range_bar_volume defense vs zero with max(1, ...).
- ORS-19 GOOD (236-248): 5 distinct blockers with operator-readable messages incl values.
- ORS-20 GOOD (250-256): accepted = not blockers + entry/stop/risk/take_profit derivation.
- ORS-21 GOOD (256-277): **Watch-only mode hardcoded** + 12-key schema-stable return.

## src/parallel_scorer.py — LINE BY LINE

- PS2-1 GOOD (1-5): 5-line docstring with PR #67 archaeology.
- PS2-2 GOOD (6-20): 14 imports — **highest single-module import count in audit.**
- PS2-3 GOOD (25-36): _resolve_regime with **M1 cache-on-cfg pattern** + try/except fail-safe to "unknown".
- PS2-4 BUG (31): Inline import. **20th cross-cutting inline-import.**
- PS2-5 GOOD (38-163): _score_one — **8-step per-ticker pipeline** wrapped in single try/except.
- PS2-6 GOOD (40-48): indicators → fundamentals → news → sentiment chain.
- PS2-7 GOOD (50-51): composite_score consumes B62 SC-X1.
- PS2-8 GOOD (53-58): Phase 2A watchlist boost with composite clamping.
- PS2-9 GOOD (60-74): **Pillar 3 Layer 6 pattern_multiplier with try/except defensive fail-safe to 1.0.**
- PS2-10 BUG (64): Inline import. **21st cross-cutting.**
- PS2-11 GOOD (66): Reuses cached regime via `cfg.get("_regime") or _resolve_regime(cfg)`.
- PS2-12 GOOD (76-77): min_score gate.
- PS2-13 GOOD (79-89): PR #67 day_score + classify_with_day_score chain.
- PS2-14 GOOD (81): `news_boost_for_day = max(0, wl_boost)` — only positive news helps day trades.
- PS2-15 GOOD (91-106): ATR-based stops with **regime-conditioned position sizing** (E3b archaeology). 4-tier multipliers (bull=1.0/transition=0.8/chop=0.6/bear=0.4) inline comment.
- PS2-16 GOOD (94-95): capital chained-or fallback (capital → account_size → 10000).
- PS2-17 GOOD (108-127): Monster Hunt try/except with 3-key fallback on error.
- PS2-18 GOOD (110): `cfg.get("monster", {}).get("fetch_short_float", False)` — feature-flag guard.
- PS2-19 GOOD (112): `if d2e_val is not None and d2e_val < 999` — **999 sentinel handling.** Per Batch 51 EA cross-cutting.
- PS2-20 GOOD (129-153): Pillar 2 wisdom_consult with **observe-mode ±0.05 cap inline comment.** Per Batch 50/65 OBSERVE-MODE cross-cutting.
- PS2-21 GOOD (149-153): On exception → 4 default-zero fallbacks.
- PS2-22 GOOD (155-160): 5-key compact return.
- PS2-23 GOOD (161-163): **Top-level catch-all with operator-readable per-ticker error log** — non-blocking single-ticker failure. ✅
- PS2-24 GOOD (166-176): score_all with **ThreadPoolExecutor max_workers=10 default.**
- PS2-25 GOOD (175): Final composite-sorted descending.

## src/picks_csv.py — LINE BY LINE

- PC-1 GOOD (1-5): 5-line docstring with use case.
- PC-2 GOOD (10): Module-level LOG_PATH.
- PC-3 GOOD (13-22): read_open_picks with date + status filter.
- PC-4 BUG (18): No `newline=""`.
- PC-5 GOOD (25-46): update_pick_row with **fieldnames preservation + extrasaction=ignore** safety.
- PC-6 BUG (31): No `newline=""` in read.
- PC-7 GOOD (37-38): `if k in fieldnames` guard before mutation.
- PC-8 BUG (42): **NO ATOMIC WRITE.** **41st unsafe writer.** Per Batch 64 PE3-X2 — should use tmp+replace pattern.
- PC-9 GOOD (42): `newline=""` on write ✅.
- PC-10 GOOD (43): extrasaction="ignore" defensive.

## src/position_monitor.py — LINE BY LINE

- PM-1 GOOD (1-17): 17-line docstring with usage example + max_hold table.
- PM-2 GOOD (22-29): 3-tier MAX_HOLD_DAYS dict + DEFAULT_MAX_HOLD=14 named.
- PM-3 GOOD (32-38): _parse_date with bare-except None.
- PM-4 BUG (37): bare Exception. Theme T1.
- PM-5 GOOD (41-42): _max_hold_for with case-insensitive lookup.
- PM-6 GOOD (45-112): scan_open_positions with **alert dict shape in docstring** + 2-severity classification.
- PM-7 GOOD (60-63): today/PICKS_LOG None defaults.
- PM-8 BUG (65): No `newline=""`.
- PM-9 GOOD (78-83): 2-condition severity dispatch + **continue on within-budget** (don't emit alert).
- PM-10 GOOD (85-88): entry float-coerce with bare-except 0.0.
- PM-11 BUG (87): bare Exception.
- PM-12 GOOD (91-92): Emoji + verb dispatch by severity.
- PM-13 GOOD (93-97): HTML-format Telegram message (b tag).
- PM-14 GOOD (110-111): Sort by overdue-magnitude descending.
- PM-15 GOOD (115-130): format_telegram_summary with over/near segregation.

## CONSOLIDATED CROSS-CUTTING (THIS BATCH)

### Theme T23 (PRICE INTEGRITY) — NOW 4-LAYER COMPLETE
- B14 MDH-X1 wrong-data telemetry
- B57 FH-X2 cross_validate_price 2-source consensus
- **B66 SF-X1 smell_stale_price (this batch) blocking smell**
- B64 PE3-X3 unreachable_entry post-pick detection

**End-to-end audited.**

### Theme T6 (ATOMIC WRITES) UPDATE
| Module | Status |
|---|---|
| pick_evaluator (B64 PE3-X2) | ✅ ATOMIC |
| **market_data_health (this batch MDH2-13)** | ✅ ATOMIC |
| signal_journal SJ2-16 | ❌ unsafe (39th) |
| agent_memoir AM2-14 | ❌ unsafe (40th) |
| picks_csv PC-8 | ❌ unsafe (41st) |
| OPA (B65) | ❌ unsafe |

**Tally: 7 safe / 41 unsafe / 48 = ~85% UNSAFE.** PC-8 + AM2-14 + SJ2-16 are CRITICAL — these are operator-trail writers.

### Theme T8 (DRY) MASSIVE UPDATE
- _safe_float / _to_float duplicates: **21 modules** (was 16). 
- Tag-extraction duplicates: **4 modules** (B62 SC-12 + B65 PRG cross-batch + this batch SJ2-9 + PRG-5).
- _safe_value duplicates with DRIFT (CD-2): list-cap 10 vs 25 between OPA and CD.

### Theme T11 (FAIL-OPEN) CRITICAL FINDING
**MG-5 + MG-6:** market_guard.spy_trend defaults to above_50dma=True + above_200dma=True on insufficient data OR exception. **MASKS DATA OUTAGE AS BULLISH STANCE.** Should default to None or False per safety principle. **2nd audited fail-open-by-accident.**

### Theme T22 (FROZEN DATACLASS)
**3 audited frozen dataclasses** now: TG-9 (B63), PFT-5 (this batch), agent_memoir AM2 not frozen but mission_statement is const.

### Theme T26 (NIGHTLY ORCHESTRATOR) UPDATE
3-pillar architecture: NC2-X1 (B65 8-step) + PS2-X1 (this batch ThreadPool 10-worker per-ticker) + SA-X1 (this batch monthly_calibration windowing).

### NEW Theme T27 (TAXONOMY-EVOLUTION BRIDGE)
PFT-X1 + MDH2-X1: bidirectional legacy↔canonical mapping for backward compat. **First audited schema-evolution helper module-pair.**

### Cross-cutting tally summary (this batch only)
| Metric | Before | This batch | After |
|---|---:|---:|---:|
| _safe_float duplicates | 16 | 5 | **21 modules** |
| Bare-except | mod | 11 | continues moderate |
| Inline imports | 19 | 2 | **21 cumulative** |
| Import-time side effects | 13 | 1 (SJ2-2) | **14** |
| Unsafe writers | 37 | 4 (SJ2 + AM2 + PC + PRG read-only) | **41 / 48 = ~85% UNSAFE** |
| Atomic writers | 6 | 1 (MDH2) | **7** |
| TZ-aware modules | 13 | 2 (MDH2 + ORS, AM2 partial) | **15** |
| DATED archaeology | 17 | 5 (SJ2 + SF + AM2 + MG + PS2) | **22 cumulative** |
| Frozen dataclasses | 1 | 1 (PFT) | **3 (TG + PFT)** |
| OBSERVE-MODE modules | 20 | 2 (AM2 + PS2 wisdom) | **22** |
| __main__ smoke tests | 17 | 1 (AM2-15) | **18** |

## SUMMARY (Batch 66 — 15-FILE)

| File | Show-stop | Data/safety | Code smell | Good code | Findings |
|---|---:|---:|---:|---:|---:|
| self_awareness | 1 | 0 | 0 | 10 | 11 |
| signal_journal | 4 | 0 | 0 | 15 | 19 |
| smell_faculty | 2 | 0 | 0 | 18 | 20 |
| agent_memoir | 4 | 0 | 0 | 11 | 15 |
| candidate_diagnostics | 1 | 0 | 0 | 12 | 13 |
| missing_data_gate | 1 | 0 | 0 | 9 | 10 |
| market_guard | 5 | 1 | 0 | 7 | 13 |
| market_data_health | 1 | 0 | 0 | 22 | 23 |
| provider_failure_taxonomy | 0 | 0 | 0 | 25 | 25 |
| market_calendar | 0 | 0 | 0 | 14 | 14 |
| portfolio_risk_gate | 3 | 0 | 0 | 19 | 22 |
| opening_range_scanner | 0 | 0 | 0 | 21 | 21 |
| parallel_scorer | 2 | 0 | 0 | 23 | 25 |
| picks_csv | 3 | 0 | 0 | 7 | 10 |
| position_monitor | 4 | 0 | 0 | 11 | 15 |
| **TOTAL** | **31** | **1** | **0** | **224** | **256** |

## TOP 15 CRITICAL FIXES from Batch 66

1. **MG-5 + MG-6 / Theme T11 (CRITICAL):** market_guard.spy_trend defaults to bullish on data outage — **silent fail-open masks data degradation as buy-signal.** Change to defensive None or False. (5 min)
2. **PC-8 (HIGH):** picks_csv.update_pick_row uses non-atomic whole-file rewrite — **intraday_monitor calls this many times per day**, crash mid-write would corrupt picks_log.csv. Apply PE3-X2 atomic pattern. (5 min) **HIGHEST IMPACT atomic-write fix in audit.**
3. **SJ2-16 (HIGH):** signal_journal.attach_outcome non-atomic jsonl rewrite — could lose entire signal journal on crash. Apply atomic pattern. (5 min)
4. **AM2-14 (HIGH):** agent_memoir non-atomic write — though regenerated nightly, partial-write would expose corrupt JSON to readers between rewrite + nightly rebuild. (3 min)
5. **CD-2 (Theme T8):** _safe_value drift between OPA (B65) and CD (this batch) — list-cap 10 vs 25, dict-cap 30 vs 75. Consolidate into shared helper. (10 min)
6. **_safe_float/_safe_int consolidation NOW 21 MODULES — MUST address.** Create `src/_safe_helpers.py` with shared utilities. **Most-deferred cross-cutting fix.** (1 hour with import migrations)
7. **MG-2:** Expand market_guard module docstring — 5 functions undersold. (3 min)
8. **PRG-5 / Theme T8:** Tag-extraction now 4 modules — consolidate into shared `src/_pick_helpers.py`. (15 min)
9. **PS2-4 + PS2-10 (cross-cutting inline imports):** Hoist to module top. (2 min)
10. **MDH2-X1 atomic write GOLD STANDARD propagation:** Apply MDH2-13 pattern (tmp+replace+sort_keys+timestamp injection on save) to next 5 unsafe writers (PC + SJ2 + AM2 + OPA + HB log). (30 min for all 5)
11. **MC-X1 / NEW T28:** Extend NYSE holiday cache to 2029 NOW (3-year minimum policy) — currently at exactly 3 years, will hit "soft" urgency in months. Per renewal_message logic. (20 min)
12. **PFT-X1 + MDH2-X1 / Theme T27:** Document taxonomy-evolution-bridge pattern in `docs/SCHEMA_EVOLUTION.md`. (15 min)
13. **MDG-7 + PRG-14 cross-cutting:** Both modules implement entry/sl/tp semantic checks independently — consolidate into shared validator. (15 min)
14. **PM-8, PC-4/6, AM2-5, NC2 (B65), HB (B65):** Add `newline=""` to ~10 csv.DictReader calls cumulative. Bundle as single PR. (10 min)
15. **PS2-X1 / Theme T26 (NIGHTLY ORCHESTRATOR):** Document the 8-step per-ticker pipeline in `docs/SCORING_PIPELINE.md` — references B62 SC-X1 + B63 IN-X1 + B66 SJ2 + this batch PS2-X1. (30 min)

## NEW THEMES UPDATED

- **Theme T1 (bare except):** ~11 in this batch. SF-18, MG-4/8, AM2-7, MDH2-12, PRG-9, PM-4/11, SA-6 all defensive.
- **Theme T2 (drift):** CD-2 _safe_value drift vs OPA (B65). 9th drift instance.
- **Theme T6 (atomic writes):** **7 safe / 41 unsafe = 85% UNSAFE.** MDH2 second audited atomic. PC-8 highest-impact missing.
- **Theme T8 (DRY):** **21-module _safe_float duplication** + 4-module tag-extraction duplication.
- **Theme T11 (fail-open):** **MG-5 + MG-6 — 2nd audited fail-open-by-accident, MORE DANGEROUS than first.**
- **Theme T14 (gold standard):** SA-X1 pure-stdlib Wilson CI + monthly_calibration windowing. SJ2-X1 calibrated bucketing with 39-pick archaeology. SF-X1 7-smell registry + per-smell try/except + founder-quote docstring + Smell @dataclass + smell_stale_price 2-tier severity. AM2-X1 mission statement + 4-tier current_focus narrative + 11-key memoir + earnings-warning enrichment + first-person narrative text. CD-X1 19-key compact summary + 4-handler architectural symmetry + 16-key stage_counts + bidirectional set-difference integrity. MDG-X1 11-rule validator + carries-forward upstream gate signals + entry/sl/tp semantic checks. MDH2-X1 threading.Lock + atomic write + canonical-keyed bucket init + 30-sample buffer + telemetry-must-never-break-picker safety. PFT-X1 11-category taxonomy + 9-keyword dispatch + frozen dataclass + bidirectional legacy↔canonical bridge + classify_legacy preserves "unauthorized" bucket name. MC-X1 hardcoded 3-year cache + 4-tier renewal urgency + plain-English message + per-holiday inline observance comments. PRG-X1 5% tolerance + 8 sequential fail conditions + score-sorted iteration + slot consumption + downstream traceability stamp. ORS-X1 18-line docstring with bar-shape example + naive→ET interpretation + 5 anti-chase blockers + watch-only-hardcoded. PS2-X1 ThreadPoolExecutor + cfg-cached regime + 8-step pipeline + per-step try/except + per-ticker error log + observe-mode cap inline + 999-sentinel handling. PM-X1 Telegram-shape in docstring + 2-severity dispatch + most-overdue-first sort + emoji-by-severity.
- **Theme T22 (frozen dataclass):** 3 instances now — TG, PFT, MDH2 implicit (lock-protected dict).
- **NEW Theme T27 (taxonomy-evolution bridge):** PFT + MDH2 first audited bidirectional legacy↔canonical mapping pair.
- **NEW Theme T28 (hardcoded-cache renewal awareness):** MC-X1 first audited self-aware-aging-data module with renewal_urgency + automated weekly digest reminder (B65 MB-X1).

## COVERAGE TRACKER

| Phase | Status | Cumulative |
|---|---|---:|
| Phase F | 34/~38 done | 34/~38 |
| Total true line-by-line | **+15 files** | **167 of ~382 (~43.7%)** |

**MILESTONE: ~44% AUDIT MARK. Phase F nearly COMPLETE (4 files left). Lane 1 5-gate pipeline + Price-integrity 4-layer defense + 3-pillar nightly orchestrator architecture all AUDITED.**

## CONFIRMED RELIABLE BATCH SIZE: 15 FILES

15-file batch executed successfully: ~2,943 LOC, 15 parallel `getfile` calls, 1 audit doc with 15 file-by-file sections + cross-cutting + summary. **Output token budget consumed but doc complete.** Recommend continuing at 15-file rate.

## NEXT BATCH (15-FILE)

Batch 67: Final Phase F files + start Phase G if any. Candidates from inventory:
- intraday_monitor, monitor_loop, watchlist_manager, news_sentiment, news_signals  
- pattern_layer, pattern_engine, pattern_stats, hypothesis_engine, calibration
- weight_proposer, weight_applier, lesson_gc, learning_journal, auto_promote

End of Batch 66. **43.7% audit milestone. Lane 1 + Price-integrity + Nightly-orchestrator architectures FULLY AUDITED.**
