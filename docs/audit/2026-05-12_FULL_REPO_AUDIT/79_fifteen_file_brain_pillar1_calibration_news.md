# Batch 73 — 15-FILE BATCH — TRUE LINE-BY-LINE — BRAIN/CALIBRATION/PILLAR-1/NEWS

**Date:** 2026-05-13
**Files (15):** calibration (387) + candidate_diagnostics (230) + hypothesis_engine (184) + indicators (321) + data_fetcher (231) + meta_brain (279) + news_signals (384) + stock_stats (321) + performance_stats (128) + performance_tracker (219) + weight_applier (233) + weight_proposer (282) + earnings (170) + earnings_analyzer (215) + agent_memoir (194)
**Phase:** H. **Total LOC audited this batch: ~3,778 lines (LARGEST SINGLE BATCH BY LOC).**

## TOP HEADLINE FINDINGS

1. **CAL-X1: calibration.py** (387 lines) is **THE T37+T38 PILLAR-3.5 CALIBRATION BRAIN** — per-factor + per-month attribution from backtest_results CSVs. **8-key BucketStat dataclass** (12th audited dataclass) + 5 named bucket-classifiers (RSI/score/ATR%/month/exit) + per-factor + per-timeframe reports + **Telegram footer** (`telegram_footer_lines`) + **inline-import for weight_proposer** (NEW Theme T35 cross-module) + full argparse CLI (5 subcommands). **READ-ONLY** (operator-explicit per docstring). **First audited "calibration brain" facade.**
2. **CDI-X1: candidate_diagnostics.py** (230 lines) is **THE LANE 1 REPORTING-ONLY DIAGNOSTICS BUILDER**. Reporting-only mandate (4 explicit non-behaviors) + **20-key summarize_candidate** + 4 stage-specific blocked-detail builders (hard / sanity / portfolio_risk / missing_data) + **`build_candidate_diagnostics` 14-kwarg orchestrator** that builds **15-key stage_counts** + **deduplicated rejected_candidates list across 4 sources** + bidirectional per-ticker matchback. **First audited "diagnostics-builder" facade. Heaviest kwargs single function audited (14)**.
3. **HE-X1: hypothesis_engine.py** (184 lines) is **THE PILLAR-1-LAYER-4 OBSERVE-MODE HYPOTHESIS DETECTOR**. **Pure-stdlib binomial CDF** via `math.comb` (5th Pure-stdlib statistical: SA + HE + RKM + BM + PT triangles + HE) + **3-tier classification** (significant_edges + significant_drags + low_sample) + **two_sided_p_value** with right/left-tail dispatch + per-bucket vs base_rate Δ-sort + format_report 3-section text renderer. **Operator-EXPLICIT "OBSERVE-MODE: No weights auto-changed. You decide what to act on."** Gold standard observe-mode discipline.
4. **IND-X1: indicators.py** (321 lines, **largest in B73 by LOC count except for stock_stats**) is **THE FULL PANDAS TECHNICAL INDICATOR SUITE**. **15 indicator functions** (sma/ema/rsi/macd/bollinger/atr/stochastic/obv/parabolic_sar/vwap/adx/candlestick_patterns/fibonacci_levels/support_resistance + add_indicators composite + latest_signals 30-key) + **6 candlestick patterns** (engulfing×2, hammer, shooting_star, doji, morning_star, evening_star). **Pure pandas/numpy + no-side-effects + acceptable bare-except for psar/patterns/fib defensive isolation**. **First audited indicator-suite library.** Gold standard.
5. **DF-X1: data_fetcher.py** (231 lines) is **THE PRIMARY+FALLBACK OHLCV FETCHER**. yfinance primary + **Stooq fallback** (per B71 STQ-X1) with **dual try/except + record_market_data_event on success/empty/error.** + **`DAILY_FETCH_YF_FULL_INFO` env-var-gated heavy-info fetch** (operator-pragmatic anti-rate-limit) + **CRITICAL THREAD-SAFETY DOCSTRING** ("do not replace this with yf.download() in parallel fetches; yf.download() uses shared module-level state and previously caused cross-ticker data leakage") + 4-validator `is_valid_market_data` (cheap hard gate vs heavier smell_stale_price). **Bug-#6 archaeology + E2c.3 archaeology May 4 2026.** **First audited dual-provider fetch with explicit thread-safety operator archaeology.** 9th `safety: no stale/cache fabrication` declaration.
6. **MB-X1: meta_brain.py** (279 lines) is **THE T50 META-BRAIN — A BRAIN THAT REASONS ABOUT THE BRAIN ITSELF**. **PHILOSOPHY EXPLICIT** ("This module never mutates anything. It only OBSERVES the brain's recent behavior"). **4 functions** (recent_mutations / detect_stuck_areas / suggest_hypotheses / build_self_improvement_digest) + **system_age_days defensive guard** (added 2026-05-04 — "if system younger than stuck_days, we CAN'T be stuck — there hasn't been enough time. Prevents false alarm") + Telegram-formatted plain-English summarization + **T51 calendar-renewal hook** + 6-mutation-kind dispatcher (weight_applied / pattern_disabled/enabled / lesson_promoted/demoted / nightly_brain_run). **First audited self-introspection module.** Gold standard.
7. **NS2-X1: news_signals.py** (384 lines) is **THE NEWS-CATALYST → SCORE-DELTA TRANSLATOR (PR #77)**. **12-catalyst rule table** (BULLISH ×7 / BEARISH ×5) with `(score_delta, ttl_days)` tuples + **CATASTROPHIC keyword set ×11** (bankruptcy/chapter11/chapter7/going-concern/cease-operations/wind-down/delisting/asset-disposal/liquidation/wipeout/worthless) → -1.00 forever-block + **NEGATIVE_REACTION_PHRASES ×27** ("shares fall after"/"sold off after"/...) → fade bullish boosts when market reaction is negative + **last-write-wins-with-stronger merge** + ATOMIC TMP-RENAME WRITE ✅ (10th positive Theme T6 instance) + 5 public-API functions + CLI rebuild + stats. **8th + 9th + 10th keyword-bag-of-words** (Theme T8). **EVC-style archaeology** ("catches EVC-style cases where 'good' news is sold").
8. **SS-X1: stock_stats.py** (321 lines) is **THE PILLAR-1-LAYER-1 PER-STOCK STATISTICAL FOUNDATION**. **5 statistic computations** (returns / volatility / atr / drawdowns / bounce_rates) for **365×2 days history × 4 forward-return windows × 7 percentiles** + **`empirical_sl_pct` + `empirical_tp_pct` PROBABILITY-BASED DECISION HELPERS** ("REPLACES arbitrary thresholds (1.5×ATR, RSI 30, 3% SL) with empirically-derived probability-based decisions") + 3 cross-document references (PROBABILITY_ENGINE_DESIGN + BRAIN_ARCHITECTURE + ADR-001-probability-over-rules). **First audited "ADR-referenced" module + first probability-quantile→threshold helpers.** Gold standard architecture-discipline.
9. **PS2-X1: performance_stats.py** (128 lines) is **THE RICH-LIBRARY-BASED PERFORMANCE DASHBOARD FROM PICKS_LOG**. Uses `rich.console.Console` + `rich.table.Table` for **3 colored Rich tables** (Overall + Performance by Tag + Best Picks + Worst Picks). **First audited Rich-library consumer module** + **first audited terminal-color dashboard.** Acceptable as CLI-only display layer.
10. **PT3-X1: performance_tracker.py** (219 lines) is **THE SINGLE-SOURCE-OF-TRUTH PERFORMANCE METRICS COMPUTATION**. **5 metric computations** (sharpe / max_drawdown / r_multiple / return_pct / segmented metrics) + **filter via PSS-X1 (B72) source separation** (excludes watch-only) + **6-segment metrics breakdown** (overall + day + swing + 7d + 30d + 90d) + **persists daily snapshot + jsonl history append**. **First audited single-source-of-truth metrics module.** **DUPLICATE Sharpe/MaxDD logic** (Theme T36 expansion: now 3 places — RKM + BM + PT3).
11. **WA-X1: weight_applier.py** (233 lines) is **THE T44 PILLAR-4 WEIGHT-APPLIER (BRAIN'S HANDS)**. **5%/week-per-factor cap** + idempotent (`proposal_id` = ts+factor+bucket) + ISO-week-cap-accounting + 0.5-1.5 multiplier safety floor/ceil + per-action dispatch (kill=0 / boost=×(1+δ%) / penalize=×(1-δ%)) + **kill counts as full cap usage** + dry-run support + journals to weight_history.jsonl + learning_journal hook + atomic rewrite of proposals.jsonl with `applied:true` marker + CLI with `--apply` (default dry-run). **First audited PILLAR-4 BRAIN-MUTATION module.** **2nd auto-feedback-loop module** (Theme T38, after PL-X1 B72 auto_enable_disable).
12. **WP-X1: weight_proposer.py** (282 lines) is **THE T39 WEIGHT-DELTA PROPOSER (READ-ONLY, PILLAR-3.5 C3)**. **3-action classifier** (boost > +0.10 / penalize < -0.10 / kill < -0.30 AND win_rate < 0.35) + **delta_pct = clamp(bias_R × 25, -5, +5)** + **confidence = √(n/100) capped at 1.0** + **12-key Proposal dataclass** (13th audited dataclass) + jsonl append + applied-flag marker + 4-subcommand CLI (propose / history / review). **NEVER auto-applies — humans must approve** (operator-explicit). **First audited "Proposer" with explicit human-gating discipline.**
13. **EAR-X1: earnings.py** (170 lines) is **THE YFINANCE-CALENDAR-SHAPE-AGNOSTIC EARNINGS-DATE FETCHER**. **3-shape-tolerance dispatch** (dict / DataFrame-with-column / DataFrame-with-index) + **`_to_date` 4-type coerce** (datetime / Timestamp / date / ISO string) + **`_as_of_date` historical-anchor support** (for backfills where days_to_earnings must be relative to pick_date, not today) + **UNKNOWN_EARNINGS_DAYS = 999 sentinel** + curl_cffi optional-import. **First audited shape-tolerant external-API parser.** Operator-defensive gold standard.
14. **EA-X1: earnings_analyzer.py** (215 lines) is **THE FINNHUB EARNINGS-QUALITY 0-1 SCORER**. **5 sub-scorer dispatch with weights** (beat_rate 35% + avg_surprise 20% + eps_momentum 20% + analyst_buy% 15% + rec_trend 10%) + 4-tier piecewise dispatch per sub-score + 24h disk cache (per-ticker per-kind JSON) + **fail-safe 0.5 default earnings_quality** when no data. **First audited multi-sub-score weighted-composite module + Finnhub API consumer.**
15. **AM-X1: agent_memoir.py** (194 lines) is **THE AGENT'S PERSISTENT IDENTITY & NARRATIVE SELF-KNOWLEDGE**. **MISSION_STATEMENT module-constant** + 4-part memoir (identity / lifetime_stats / biggest_win/loss with narrative + lesson_learned / current_focus dispatch by win_rate / what_im_proud_of / recent_learning_7d / promise_to_anjan) + **founder-archaeology May 4 2026** ("Agent should not forget its mistakes and learnings, the wins, and what its task is supposed to be"). **First audited "narrative self-portrait" module.** **Operator-mission-statement gold standard.**

## CRITICAL CROSS-FILE FINDINGS

- **NEW Theme T39 (PILLAR-1 STATS-ATTRIBUTION CHAIN COMPLETE):** SS-X1 (per-stock stats foundation, Pillar 1 Layer 1) → HE-X1 (hypothesis engine, Pillar 1 Layer 4) → CAL-X1 (calibration brain, Pillar 3.5) → WP-X1 (weight proposer, Pillar 3.5 C3, READ-ONLY) → WA-X1 (weight applier, Pillar 4, brain's HANDS) → MB-X1 (meta brain, T50, OBSERVES brain). **6-stage Pillar 1+3.5+4 brain-mutation pipeline FULLY AUDITED.** Document in `docs/BRAIN_MUTATION_PIPELINE.md`.
- **Theme T38 (auto-feedback-loop modules) NOW 2 modules:** PL-X1 (B72) auto_enable_disable patterns + WA-X1 (B73) apply_proposals. **WA-X1 is more disciplined than PL-X1** — 5%/week cap + idempotent proposal_id + dry-run default + CLI `--apply` opt-in. **WA-X1 is the gold-standard template** for future auto-feedback loops.
- **Theme T36 (shared-library duplication) NOW 3 PLACES** with **DIFFERENT SHARPE ANNUALIZATION:**
  - B70 RKM-X1 risk_metrics: sqrt(50) — "trades/year"
  - B71 BM-X1 backtester/metrics: sqrt(250) — "trading days"  
  - **B73 PT3-X1 performance_tracker: sqrt(252) — "trading days"** (different from BM by 2)
  
  **3 distinct annualization conventions across 3 modules — math drift catastrophic risk.** **CRITICAL: consolidate into `src/_stats.py` immediately.**
- **Theme T35 (cross-module helper imports) NOW 3 INSTANCES:**
  - B71 PHS imports from double
  - B71 PW imports from triangles
  - **B73 CAL imports `from src.weight_proposer import read_proposals`** (open_proposals_summary)
- **Theme T8 (DRY) UPDATE:**
  - _safe_float / _safe_int: now **39 modules** (B73 added: AM-X1 + PT3-X1 = 2 new)
  - **Sharpe/MaxDD: 3 distinct implementations** (Theme T36)
  - **Keyword-bag-of-words: NOW 10 modules** (B72 PFT + B73 NS2 ×3 distinct vocabularies — CATASTROPHIC + NEGATIVE_REACTION + CATALYST)
- **Theme T6 (atomic writes) GOOD NEWS:** NS2-X1 implements atomic temp-rename pattern ✅ — **10th POSITIVE atomic instance** (out of ~71 cumulative writers). NS2-X1 + DS-X1 are gold-standard atomic-rename templates.
- **NEW Theme T40 (ADR-REFERENCED ARCHITECTURE MODULES):** SS-X1 references docs/decisions/ADR-001-probability-over-rules.md (alongside PROBABILITY_ENGINE_DESIGN + BRAIN_ARCHITECTURE Pillar 1). **First audited ADR-referenced module.** Pillar-anchored architecture is FORMALLY DOCUMENTED. **Recommend** auditing ADRs separately.
- **Theme T31 (yfinance brittleness defense) UPDATE:** EAR-X1 introduces 3-shape-tolerance dispatch for yfinance.calendar — earliest known instance of explicit shape-drift defense in repo. DF-X1 thread-safety archaeology + EAR-X1 calendar-shape archaeology + B71 STQ provider fallback = **3-pronged yfinance-brittleness defense pattern**. **Document in `docs/YFINANCE_BRITTLENESS_DEFENSE.md`.**
- **Inline `from src.weight_proposer import read_proposals` (CAL-X1 line 372):** 43rd cross-cutting inline import.

## src/calibration.py — LINE BY LINE

- CAL-1 GOOD (1-20): 20-line docstring with **T37+T38 + Pillar 3.5 + READ-ONLY mandate + 5-subcommand CLI usage.**
- CAL-2 GOOD (22-29): 8-import including statistics.mean.
- CAL-3 GOOD (36-46): list_runs + latest_run with **None-default + chronological sort.**
- CAL-4 GOOD (49-70): load_picks with **per-row numeric coercion** for 10 known fields. ✅ Operator-correct.
- CAL-5 GOOD (62-68): 3-defensive cleanup (None / empty / "None" → None).
- CAL-6 GOOD (75-107): 4 bucket classifiers (rsi / score / atrpct / month) — **all schema-stable.**
- CAL-7 GOOD (94): div-by-zero guard `if entry <= 0`.
- CAL-8 GOOD (112-131): @dataclass BucketStat 7-field. **12th dataclass.**
- CAL-9 GOOD (134-137): _is_win consistent definition.
- CAL-10 GOOD (140-173): attribute_by with **per-row try/except + min_n threshold + sort by n desc.**
- CAL-11 BUG (151): bare Exception. Theme T1.
- CAL-12 GOOD (178-184): FACTOR_KEYS dispatch table.
- CAL-13 GOOD (187-201): 2 named factor reports.
- CAL-14 GOOD (204-218): overall_summary with empty-input → 0-default skeleton.
- CAL-15 GOOD (223-235): _resolve_run with **3-tier dispatch** (latest / explicit-path / runs-relative).
- CAL-16 GOOD (238-248): _fmt_table pure-stdlib formatter.
- CAL-17 GOOD (251-316): main argparse CLI with 5 subcommands.
- CAL-18 BUG (269): Naive `datetime.now()` (only via main wrapper, not data path).
- CAL-19 GOOD (309-314): "run" subcommand recurses through main with reformatted args.
- CAL-20 GOOD (323-366): telegram_footer_lines with **try/except → [] safe-degradation** + best/worst-edge dispatch.
- CAL-21 BUG (365): bare Exception → []. Theme T1.
- CAL-22 GOOD (369-385): open_proposals_summary with **inline weight_proposer import** + 3-action breakdown (kill / penalize / boost).
- CAL-23 BUG (372): Inline import `from src.weight_proposer import read_proposals`. **43rd cross-cutting inline import.**
- CAL-24 BUG (384): bare Exception → None.

## src/candidate_diagnostics.py — LINE BY LINE

- CDI-1 GOOD (1-10): 10-line docstring with **reporting-only mandate + 4 explicit non-behaviors.**
- CDI-2 GOOD (17-28): _safe_value recursion-aware sanitizer with list[:10] / dict[:30] caps + dataframe-blacklist (consistent with B72 OPA-X1).
- CDI-3 GOOD (31-68): summarize_candidate with **20-key compact summary + 6 nested-dict-or-{} defensive coalescings + 3-source news_action_window fallback chain.**
- CDI-4 GOOD (50-54): "news_action_window" with **3-source fallback** (scores → news_signal → news).
- CDI-5 GOOD (61): bool() coercion for watch_only with dual-source.
- CDI-6 GOOD (64): "premarket_actionable" with explicit "in candidate" key-presence check.
- CDI-7 GOOD (71-72): _summaries batch wrapper.
- CDI-8 GOOD (75-81): _ticker_set helper.
- CDI-9 GOOD (84-89): _match_candidate_by_ticker fallback for hard_blocked detail enrichment.
- CDI-10 GOOD (92-152): 4 stage-specific blocked-detail builders (hard / sanity / portfolio_risk / missing_data) — **schema-stable per stage with rejection_stage marker.**
- CDI-11 GOOD (155-229): build_candidate_diagnostics with **14 kwargs + 4-stage rejection-aggregation + 15-key stage_counts.** **Heaviest kwargs single function audited.**
- CDI-12 GOOD (185-191): rejected_candidates **deduplicated across 4 sources** (single flat list).
- CDI-13 GOOD (197-213): stage_counts **15-key cross-stage tally** with **scored-not-filtered + filtered-not-capped derivations.**

## src/hypothesis_engine.py — LINE BY LINE

- HE-1 GOOD (1-17): 17-line docstring with **OBSERVE-MODE mandate + 3-tier classification + Pillar 1 Layer 4 reference.**
- HE-2 GOOD (16): "OBSERVE-MODE: Engine ONLY reports. No auto-flipping of weights." Operator-explicit gold standard.
- HE-3 GOOD (20): `from math import comb` — **Pure-stdlib statistical** (5th instance: SA + RKM + BM + PT triangles + HE).
- HE-4 GOOD (23-24): MIN_SAMPLE_SIZE + SIGNIFICANCE_THRESHOLD module constants.
- HE-5 GOOD (30-34): _binom_pmf with **3 edge cases** (range invariants + p=0 + p=1).
- HE-6 GOOD (37-38): _binom_cdf summation.
- HE-7 GOOD (41-53): two_sided_p_value with **right/left-tail dispatch + min(1.0, 2*tail) cap.** ✅ Statistically-correct.
- HE-8 GOOD (59-128): analyze with **per-bucket aggregation + per-bucket p-value + 3-tier classification (edges/drags/low_sample).**
- HE-9 GOOD (66-72): n_total=0 → empty 6-key skeleton with summary message.
- HE-10 GOOD (74-75): base_rate computation.
- HE-11 GOOD (78-81): defaultdict(list) for (signal_name, bucket_value) buckets.
- HE-12 GOOD (84-117): per-bucket loop with **r_multiples list-comp + isinstance(int,float) defensive + 7-key record.**
- HE-13 GOOD (110-113): edges if (p<alpha AND wr>base) / drags if (p<alpha AND wr<base).
- HE-14 GOOD (115-117): 3 sorts — edges by Δ desc / drags by Δ asc / low_sample by n desc.
- HE-15 GOOD (119-128): 7-key result with **summary string for human-readable header.**
- HE-16 GOOD (131-183): format_report with **3-section text rendering + emoji + alignment + per-tier loop.**
- HE-17 GOOD (181-182): Footer "OBSERVE-MODE: No weights auto-changed. You decide what to act on." ✅

## src/indicators.py — LINE BY LINE

- IND-1 GOOD (1): 1-line docstring.
- IND-2 BUG (1): Module docstring undersells — has 15 indicator functions + composite + signals.
- IND-3 GOOD (10-49): 6 core indicators (sma / ema / rsi / macd / bollinger / atr).
- IND-4 GOOD (22): RSI with **`loss.replace(0, np.nan)` div-by-zero guard.** ✅
- IND-5 GOOD (41-48): ATR with **True Range concat + max-axis** — pandas-idiomatic.
- IND-6 GOOD (55-91): 4 additional indicators (stochastic / obv / parabolic_sar / vwap).
- IND-7 GOOD (58): Stochastic with `(high_max - low_min).replace(0, np.nan)` guard.
- IND-8 GOOD (68-91): parabolic_sar **23-line numpy-loop pure implementation** with **2-trend dispatch + AF clamp + min/max with prior 2 bars.** Operator-correct standard PSAR algorithm.
- IND-9 GOOD (94-99): vwap with `v.replace(0, np.nan)` guard.
- IND-10 GOOD (102-119): adx **17-line implementation** with **EWMA-smoothed +DI/-DI/ADX + 4 div-by-zero guards.** ✅ Wilder-correct.
- IND-11 GOOD (122-152): candlestick_patterns with **6 patterns + bullish/bearish-signal aggregator** + **`max(h - l, 1e-9)` div-by-zero guard.**
- IND-12 GOOD (134-148): 6 pattern detection rules (engulfing×2, hammer, shooting_star, doji, morning_star, evening_star) — **operator-readable with parens.**
- IND-13 GOOD (155-168): fibonacci_levels with **7 percentage levels (0/23.6/38.2/50/61.8/78.6/100).**
- IND-14 GOOD (171-190): support_resistance with **5-bar pivot detection + nearest-above/below filtering.**
- IND-15 GOOD (197-236): add_indicators composite with **15 indicator additions + try/except for psar.**
- IND-16 BUG (225): bare Exception → np.nan.
- IND-17 GOOD (239-306): latest_signals **30-key composite** with **NaN-aware `_f` helper + 6 derived flags + try/except for patterns/fib/SR.**
- IND-18 GOOD (267-271): bb_position with bb_range==0 div-by-zero guard.
- IND-19 GOOD (273-282): 5 derived boolean flags (above_psar / stoch_oversold / stoch_overbought / obv_rising / strong_trend / di_bullish).
- IND-20 GOOD (285-290): vwap-position 2-key (above_vwap + vwap_distance_pct).
- IND-21 BUG (296, 303): 2 bare Exception → pass. Theme T1.
- IND-22 GOOD: **15 indicators + 6 patterns + composite + signals = pandas-idiomatic library.**

## src/data_fetcher.py — LINE BY LINE

- DF-1 GOOD (1): 1-line docstring.
- DF-2 BUG (1): Module docstring undersells.
- DF-3 GOOD (8-13): Imports from market_data_health (3 fns).
- DF-4 GOOD (13): import from B71 STQ-X1 stooq_provider.
- DF-5 GOOD (15-19): curl_cffi optional-import with **SESSION = cf_requests.Session(impersonate="chrome")** ✅
- DF-6 BUG (18): bare Exception → SESSION=None. Theme T1 (acceptable as optional-dep guard).
- DF-7 GOOD (22-26): finnhub_data optional-import with HAS_FINNHUB flag.
- DF-8 BUG (25): bare Exception. Acceptable.
- DF-9 GOOD (29-37): _normalize_ohlcv with **3 defensive paths** (None/empty + MultiIndex flatten + lowercase).
- DF-10 GOOD (40-43): _fetch_yfinance_ohlcv with **session-or-no-session dispatch + auto_adjust=False + 20s timeout.** ✅
- DF-11 GOOD (46-47): _fetch_stooq_fallback_ohlcv pass-through.
- DF-12 GOOD (50-117): fetch_ohlcv with **dual-provider try/except + record_event on success/empty/error + empty-df default.**
- DF-13 GOOD (51-68): **18-line docstring with 4 sections: primary / fallback / safety / thread-safety. CRITICAL THREAD-SAFETY ARCHAEOLOGY** ("yf.download() previously caused cross-ticker data leakage"). ✅ Operator-trust gold standard.
- DF-14 GOOD (69-91): yfinance try-block with **success+empty+error event recording.**
- DF-15 GOOD (93-115): stooq fallback try-block with **same success+empty+error event recording.**
- DF-16 GOOD (117): empty-df default — **no fabrication.** ✅
- DF-17 GOOD (120-132): fetch_universe_data with **ThreadPoolExecutor + min-50-rows quality filter + write_market_data_run_summary integration.**
- DF-18 GOOD (128): "if not df.empty and len(df) > 50" — quality gate.
- DF-19 GOOD (135-191): fetch_info with **fast_info preferred + heavy-info opt-in + 8-key skeleton.**
- DF-20 GOOD (138-139): Bug #6 archaeology — "do not use ticker as a fake company-name fallback."
- DF-21 GOOD (155-174): **`DAILY_FETCH_YF_FULL_INFO` env-var-gated heavy-info fetch** with operator-archaeology comment. ✅ Operator-pragmatic anti-rate-limit.
- DF-22 GOOD (167-172): long_name validation — **rejects ticker-as-name fallback.** ✅
- DF-23 BUG (173): bare Exception → pass. Acceptable.
- DF-24 GOOD (175-179): record_event on error/success.
- DF-25 GOOD (182-189): Finnhub fundamentals integration with **HAS_FINNHUB flag + env-var presence check.**
- DF-26 BUG (188): bare Exception → print only.
- DF-27 GOOD (198-230): is_valid_market_data with **4-validator cheap hard gate** + E2c.3 archaeology May 4 2026.
- DF-28 GOOD (210-228): 4 validators (price-None / price-non-numeric / price-non-positive / price-suspiciously-high / averageVolume-zero).
- DF-29 GOOD (219): "currentPrice suspiciously high: $X" — anti-corruption gate (>$100k for non-BRK.A).

## src/meta_brain.py — LINE BY LINE

- MB-1 GOOD (1-15): 15-line docstring with **T50 + 4 outputs + PHILOSOPHY mandate.**
- MB-2 GOOD (12-14): "PHILOSOPHY: This module never mutates anything. It only OBSERVES." ✅ Operator-explicit gold standard.
- MB-3 GOOD (25-27): 3 named paths.
- MB-4 BUG (30-32): _to_float duplicate (**38th instance**).
- MB-5 GOOD (35-42): _read_jsonl with line-by-line try/except.
- MB-6 BUG (41): bare except.
- MB-7 GOOD (48-61): recent_mutations with **per-event try/except + cutoff filter.**
- MB-8 BUG (52): naive datetime.now() — should be TZ-aware. **12th naive-datetime instance.**
- MB-9 BUG (59): bare Exception.
- MB-10 GOOD (64-69): categorize_mutations defaultdict-based.
- MB-11 GOOD (75-98): detect_stuck_areas with **system_age_days defensive guard added 2026-05-04.** ✅ Anti-false-alarm.
- MB-12 GOOD (78-82): "Defensive (added 2026-05-04): if system younger than stuck_days, we CAN'T be stuck — there hasn't been enough time." Operator-archaeology gold standard.
- MB-13 BUG (83-89): Docstring AFTER guard — should be at top of function.
- MB-14 BUG (92): bare Exception → 999.
- MB-15 GOOD (104-168): suggest_hypotheses with **per-row date-filter + per-(group, label) win_rate vs baseline + |Δ|≥15% threshold + top-5 cap.**
- MB-16 BUG (115): naive datetime.now().date(). **13th naive instance.**
- MB-17 GOOD (120): "legacy 'date' fallback removed 2026-05-05 (column never existed)" — operator-archaeology.
- MB-18 BUG (124, 129): 2 bare Exception.
- MB-19 GOOD (140-165): per-group-key loop with **4 group keys (sector_cat / sector_tag / trade_type / regime) + |Δ|≥15% threshold + 8-key hypothesis dict.**
- MB-20 GOOD (167-168): Sort by |Δ| desc + top-5 cap.
- MB-21 GOOD (174-195): _human_summary_of_mutations with **6-mutation-kind dispatch + plain-English emoji.** ✅ Operator-readable.
- MB-22 GOOD (198-233): build_self_improvement_digest with **system_age_days computation from oldest event + T51 calendar hook (try/except defensive).**
- MB-23 GOOD (203-212): system_age computed from oldest event with TZ-aware UTC parsing.
- MB-24 BUG (211): bare Exception → None.
- MB-25 GOOD (217-223): T51 market_calendar optional-import with try/except. NEW Theme T35 cross-module helper.
- MB-26 BUG (222): bare Exception.
- MB-27 GOOD (224-233): 8-key digest with calendar_warning + calendar_years_remaining.
- MB-28 GOOD (236-278): format_telegram_digest with **5-section Markdown rendering + plain-English narrative.** ✅
- MB-29 GOOD (250-251): Quiet-week fallback message ("This is normal when the strategy is performing in line with expectations").
- MB-30 GOOD (271-275): T51 calendar maintenance heads-up section.

## src/news_signals.py — LINE BY LINE

- NS2-1 GOOD (1-40): **40-line MASSIVE docstring** with **PR #77 + problem-solved before/after + data flow + 3-table catalyst→score mapping.** ✅ Operator-trust gold standard.
- NS2-2 GOOD (45-48): 3 named paths.
- NS2-3 GOOD (51-67): CATALYST_RULES 12-tuple table (BULLISH ×7 + BEARISH ×5).
- NS2-4 GOOD (70-77): CATASTROPHIC_KEYWORDS 11-list. **8th keyword-bag** (Theme T8).
- NS2-5 GOOD (81-111): NEGATIVE_REACTION_PHRASES **27-list** with **EVC-style archaeology** ("catches EVC-style cases where 'good' news is sold"). **9th keyword-bag.**
- NS2-6 GOOD (114-115): _now_iso TZ-aware UTC. ✅
- NS2-7 GOOD (118-121): _is_catastrophic combined headline+summary lower-case keyword scan.
- NS2-8 GOOD (124-130): _has_negative_reaction with **em-dash/en-dash normalization + whitespace-collapse** before keyword scan.
- NS2-9 GOOD (133-142): _apply_negative_reaction_penalty with **bounded penalty range** [0.01, 0.03] = 30% of original delta.
- NS2-10 GOOD (145-152): _load_signals with **try/except → {}.**
- NS2-11 BUG (151): bare Exception.
- NS2-12 GOOD (155-160): **_save_signals ATOMIC WRITE via temp+replace** ✅ **10th POSITIVE Theme T6 instance.**
- NS2-13 GOOD (163-174): _purge_expired with **per-signal try/except → skip.**
- NS2-14 GOOD (179-253): add_signal_from_classification with **catastrophic-first-priority + category lookup + confidence modulation + negative-reaction penalty + last-write-wins-with-stronger merge.**
- NS2-15 GOOD (197-207): Catastrophic-FIRST priority with **180-day forever-block + hard_block=True flag.**
- NS2-16 GOOD (208-231): Bullish/bearish path with **confidence = min(1.0, max(0.3, score_pct/0.7))** + **adjusted_delta = delta * confidence** + per-keyword negative-reaction-penalty.
- NS2-17 GOOD (210-211): Inline-archaeology comment ("tradeable_score 0.7 → 100% delta, 0.5 → 71% delta, 0.3 → 43% delta").
- NS2-18 GOOD (232-233): "category not in our rule set" → return None.
- NS2-19 GOOD (240-250): 3-tier merge dispatch: hard_block always wins / larger |delta| wins / else keep existing.
- NS2-20 GOOD (258-272): get_ticker_signal with **expiry-check defensive + {} fallback.**
- NS2-21 GOOD (275-297): get_ticker_boost with **0.0-default + auto-purge-if-expired.**
- NS2-22 GOOD (300-314): is_hard_blocked with **(bool, reason) tuple return.**
- NS2-23 GOOD (317-356): rebuild_from_news_log CLI helper with **per-line try/except + days-back filter + processed/added counts.**
- NS2-24 BUG (334): bare Exception.
- NS2-25 GOOD (359-373): stats with **3-bucket breakdown** + top-5 sorts.
- NS2-26 GOOD (376-383): __main__ smoke test with rebuild + stats. **30th smoke test.**

## src/stock_stats.py — LINE BY LINE

- SS-1 GOOD (1-17): 17-line docstring with **Pillar 1 Layer 1 + 5 statistic types + ADR-001 reference + cross-doc references.** ✅
- SS-2 GOOD (28-32): yfinance optional-import with YF_OK flag.
- SS-3 GOOD (35-39): 5 named module constants (STATS_DIR + HISTORY_DAYS=730 + RETURN_WINDOWS + VOL_WINDOWS + PERCENTILES).
- SS-4 GOOD (44-61): _fetch_history with **try/except + min-60-bars filter + lowercase column rename.**
- SS-5 BUG (47, 60): bare Exception → None ×2.
- SS-6 BUG (49): naive datetime.now(). **14th naive instance.**
- SS-7 GOOD (64-89): _compute_returns with **per-window forward-return + 4-stat (mean/std/skew/kurtosis) + 7-percentile per window.**
- SS-8 GOOD (76): NaN filter via `~np.isnan`.
- SS-9 GOOD (77): n<30 → skip window — sample-size discipline.
- SS-10 GOOD (92-111): _compute_volatility with **annualized via sqrt(252) + per-window 5-stat.**
- SS-11 GOOD (114-132): _compute_atr with **np.maximum.reduce True Range + 3 windows + atr%-of-price.**
- SS-12 GOOD (135-151): _compute_drawdowns with **cummax peak + dd<-0.01 filter + 5-stat (current/max/median/p10/p25).**
- SS-13 GOOD (154-186): _compute_bounce_rates with **per-drop-pct N-day recovery probability.** ✅ Empirically-correct.
- SS-14 GOOD (172-180): per-drop-day prior-peak + 5/10-day window-max-vs-prior-peak recovery counts.
- SS-15 GOOD (191-215): compute_stock_stats orchestrator 11-key profile.
- SS-16 BUG (204): naive datetime.now(). **15th naive instance.**
- SS-17 GOOD (218-223): save_stats with mkdir + indent=2.
- SS-18 BUG (222): No atomic. **63rd unsafe writer.**
- SS-19 GOOD (226-234): load_stats with file-existence + try/except defensive.
- SS-20 BUG (233): bare Exception.
- SS-21 GOOD (239-269): empirical_sl_pct with **closest-percentile interpolation + downside-only filter.** ✅ Pillar-1 deliverable.
- SS-22 GOOD (243-247): docstring "For NVDA, if daily moves ≤ -1.4% happen ~25% of time, SL of 1.4% means SL only triggered when in worst 25%." ✅ Operator-readable.
- SS-23 GOOD (272-298): empirical_tp_pct with **needed_quantile = 1 - target_p_reach + closest-available + positive-only filter.**
- SS-24 GOOD (303-321): __main__ smoke test with **NVDA-default + sl/tp print.** **31st smoke test.**

## src/performance_stats.py — LINE BY LINE

- PS2-1 GOOD (1): 1-line docstring.
- PS2-2 GOOD (5-6): rich.console + rich.table imports. **First audited Rich-library consumer.**
- PS2-3 GOOD (11-59): compute_stats with **5-tier filter + per-tag breakdown + 13-key result.**
- PS2-4 GOOD (18-22): closed-rows filter with 4-status whitelist + non-empty-return filter.
- PS2-5 GOOD (24-31): 3 sub-filters (tp/sl/expired) + r_multiples list-comp.
- PS2-6 GOOD (33-40): by_tag defaultdict 3-key per-tag aggregator.
- PS2-7 GOOD (42-58): 13-key result with **best_picks/worst_picks top-5 sorts.**
- PS2-8 GOOD (62-127): print_dashboard with **3 Rich tables + 2 conditional early-returns.**
- PS2-9 GOOD (88-89): win-rate color dispatch (green ≥50% / yellow ≥35% / red <35%).
- PS2-10 GOOD: **Honest CLI-display layer** — no business logic.

## src/performance_tracker.py — LINE BY LINE

- PT3-1 GOOD (1-8): 8-line docstring with **single-source-of-truth + 6 metric types + read/write paths.**
- PT3-2 GOOD (15): Import from B72 PSS-X1 source separation.
- PT3-3 GOOD (22-32): _load_all_evaluated_picks with **5-status whitelist** (tp_hit / sl_hit / expired / closed / day_close).
- PT3-4 GOOD (35-37): _load_evaluated_picks pre-filters watch-only via PSS-X1.
- PT3-5 BUG (40-44): _safe_float duplicate (**40th instance**).
- PT3-6 GOOD (47-57): _r_multiple with **5 defensive guards** (entry≤0 / stop≤0 / exit_p≤0 / risk≤0 / tp/sl wrong direction implicitly via sign of (exit-entry)/risk).
- PT3-7 GOOD (60-69): _return_pct with **logged-or-computed fallback.**
- PT3-8 GOOD (72-82): _sharpe with **sqrt(252) annualization** ⚠️ **DIFFERENT from BM-X1 sqrt(250) and RKM-X1 sqrt(50). NEW Theme T36 instance: 3 distinct annualization conventions across 3 modules.**
- PT3-9 BUG (72): **CRITICAL: Sharpe duplicate of risk_metrics + backtester/metrics — Theme T36.**
- PT3-10 GOOD (85-100): _max_drawdown with **equity curve from 100 base + per-bar peak update.**
- PT3-11 BUG (85): **CRITICAL: MaxDD duplicate.**
- PT3-12 GOOD (103-150): compute_metrics with **17-key skeleton-stable + n=0 fast return.**
- PT3-13 GOOD (124-126): Profit factor with `gross_loss>0` div-by-zero guard → 0.0.
- PT3-14 GOOD (128-129): Expectancy formula = `(WR * mean_win) + (1-WR) * mean_loss`.
- PT3-15 GOOD (153-195): compute_segmented_metrics with **6-segment breakdown + source_separation 5-key audit metadata.**
- PT3-16 BUG (158): naive datetime.now().date(). **16th naive instance.**
- PT3-17 BUG (177): naive datetime.now().isoformat(). **17th naive instance.**
- PT3-18 GOOD (177-188): source_separation 5-key audit metadata — explicit excluded-sources list. ✅ Operator-trust.
- PT3-19 GOOD (198-213): save_metrics with **daily snapshot + jsonl history append.**
- PT3-20 BUG (202): No atomic. **64th unsafe writer.**
- PT3-21 BUG (206): naive datetime.now().strftime. **18th naive instance.**
- PT3-22 BUG (211-212): No atomic on jsonl append. **65th unsafe writer.**
- PT3-23 GOOD (216-218): __main__ smoke test. **32nd smoke test.**

## src/weight_applier.py — LINE BY LINE

- WA-1 GOOD (1-20): 20-line docstring with **T44 + Pillar 4 + brain's-hands metaphor + 5%/week cap + idempotent + journal mandate.**
- WA-2 GOOD (27): import wp from sibling weight_proposer.
- WA-3 GOOD (30-34): 3 named paths + WEEKLY_CAP_PCT=5.0 module constant.
- WA-4 GOOD (38-47): _load + _save with TZ-aware UTC + indent=2 + trailing newline.
- WA-5 BUG (47): No atomic. **66th unsafe writer.**
- WA-6 GOOD (51-52): _pid dedup-key construction (ts+factor+bucket).
- WA-7 GOOD (56-62): _iso_week with try/except → datetime.now() fallback.
- WA-8 BUG (60): bare Exception fallback (acceptable + naive datetime.now() — **19th naive instance**).
- WA-9 GOOD (65-68): _used_this_week per-week-per-factor accumulator.
- WA-10 GOOD (71-79): _read_history with line-by-line try/except.
- WA-11 BUG (78): bare except.
- WA-12 GOOD (82-85): _append_history append-only.
- WA-13 BUG (84): No atomic. **67th unsafe writer.**
- WA-14 GOOD (89-99): _new_multiplier with **3-action dispatch + safety floor 0.5 / ceil 1.5.** ✅ Bounded mutations.
- WA-15 GOOD (102-186): apply_proposals orchestrator with **6-stage pipeline** (load proposals → load weights → load history → per-rec dispatch → per-rec history-append + journal-hook → save weights + mark-applied).
- WA-16 GOOD (108-110): 3-source load.
- WA-17 GOOD (118-136): per-proposal validation + week-cap accounting + skipped tracking.
- WA-18 GOOD (123): action-whitelist `("kill","boost","penalize")`.
- WA-19 GOOD (130): "kill is binary — counts as full cap usage" — operator-readable comment.
- WA-20 GOOD (131): `used + cost > cap_pct + 1e-6` — float-tolerant gate.
- WA-21 GOOD (143-167): per-mutation 10-key audit record + dry-run gate + history append + journal hook.
- WA-22 GOOD (158): "history.append(mutation)  # so subsequent picks honour week-cap" — operator-readable comment.
- WA-23 GOOD (159-166): learning_journal try/except optional dependency. NEW Theme T35.
- WA-24 BUG (165): bare Exception.
- WA-25 GOOD (168-177): apply-only-if-applied + idempotent rewrite of proposals.jsonl with `applied:true` marker.
- WA-26 BUG (173): No atomic on full jsonl rewrite. **68th unsafe writer.** **HIGH-RISK** — partial write of all proposals could lose proposal history.
- WA-27 GOOD (179-186): 6-key result with capped_details for diagnostics.
- WA-28 GOOD (190-205): history_summary 7-day Telegram footer.
- WA-29 BUG (192): naive datetime.now().timestamp(). **20th naive instance.**
- WA-30 BUG (197): bare Exception.
- WA-31 GOOD (208-228): _cli with **--apply opt-in (default dry-run) + box-drawing print.** ✅ Operator-conservative default.

## src/weight_proposer.py — LINE BY LINE

- WP-1 GOOD (1-37): **37-line MASSIVE docstring** with **T39 + Pillar 3.5 C3 + READ-ONLY mandate + decision-rule formula + per-proposal schema + 4-subcommand CLI.** ✅ Gold standard.
- WP-2 GOOD (5-6): "**Never auto-applies** — humans (or a future C5/C6 with safety caps) must approve." Operator-explicit.
- WP-3 GOOD (47): import cal from sibling calibration.
- WP-4 GOOD (51-56): 6 named module constants.
- WP-5 GOOD (59-76): @dataclass Proposal 12-field. **13th dataclass.**
- WP-6 GOOD (81-88): _classify with **3-action dispatch + None for too-neutral.**
- WP-7 GOOD (91-96): _delta_pct with **kill = -DELTA_CAP + clamp(bias_r×25, ±5).**
- WP-8 GOOD (99-103): _confidence with **√(n/100) capped at 1.0.** ✅ Statistically-sound.
- WP-9 GOOD (106-110): _rationale human-readable string.
- WP-10 GOOD (113-161): propose orchestrator with **per-factor + per-bucket loop + min_n threshold + classify dispatch + 13-field Proposal construction.**
- WP-11 BUG (123): naive datetime.now(). **21st naive instance.**
- WP-12 GOOD (127-130): "exit_status is descriptive...skip it from auto-proposals" — operator-readable comment.
- WP-13 GOOD (157-160): Sort kills first + biggest |delta|×confidence.
- WP-14 GOOD (166-175): write_proposals append-only jsonl.
- WP-15 BUG (172): No atomic. **69th unsafe writer.**
- WP-16 GOOD (178-199): read_proposals with **only_unapplied + limit + per-line try/except.**
- WP-17 GOOD (204-210): _fmt_proposal with emoji dispatch (🔴🟠🟢⚪).
- WP-18 GOOD (213-275): main CLI with 3 subcommands (propose / history / review).
- WP-19 GOOD (274): "These are READ-ONLY suggestions. Auto-apply ships in T-future (C6) with safety caps." ✅ Operator-explicit roadmap.

## src/earnings.py — LINE BY LINE

- EAR-1 GOOD (1): 1-line docstring.
- EAR-2 GOOD (5): yfinance import.
- EAR-3 GOOD (7-11): curl_cffi optional-import with SESSION = chrome impersonate.
- EAR-4 BUG (10): bare Exception. Acceptable as optional-dep guard.
- EAR-5 GOOD (14): UNKNOWN_EARNINGS_DAYS = 999 sentinel.
- EAR-6 GOOD (17-55): _first_non_empty with **5-shape recursive unwrap** (None / .iloc / str / .date or date / Iterable / scalar) — operator-defensive.
- EAR-7 BUG (35, 49): 2 bare Exception.
- EAR-8 GOOD (39-44): str + date scalar early-returns to avoid mistakenly recursing.
- EAR-9 GOOD (58-95): _extract_earnings_date with **3-shape dispatch** (dict / DataFrame-with-column / DataFrame-with-index).
- EAR-10 GOOD (76-93): "Shape 1/2/3" comments — operator-archaeology gold standard.
- EAR-11 BUG (68, 82, 92): 3 bare Exception → pass.
- EAR-12 GOOD (98-123): _to_date with **4-type coerce** (datetime / Timestamp / date / ISO string).
- EAR-13 BUG (111): bare Exception.
- EAR-14 GOOD (126-140): _as_of_date with **historical-anchor support** for backfills + TypeError on unsupported.
- EAR-15 GOOD (127-131): "None preserves live behavior. A date/datetime/ISO string enables historical backfills" — operator-readable.
- EAR-16 GOOD (143-164): days_to_earnings with **try/except → 999 sentinel** + max(delta, 0) clamp.
- EAR-17 BUG (163): bare Exception → 999.
- EAR-18 GOOD (167-169): earnings_safe convenience wrapper.

## src/earnings_analyzer.py — LINE BY LINE

- EA-1 GOOD (1-2): 2-line docstring.
- EA-2 BUG (5): import requests at module — heavy import. Acceptable.
- EA-3 BUG (9): from dotenv import load_dotenv — at-import side effect via load_dotenv() on next line. **22nd cross-cutting + 11th load_dotenv at-import.**
- EA-4 BUG (16): mkdir at import time. **22nd cross-cutting.**
- EA-5 GOOD (20-27): _cached_get with **mtime-based TTL + try/except → None.**
- EA-6 BUG (25): bare Exception.
- EA-7 BUG (22): naive datetime.now().timestamp() for cache TTL. **22nd naive instance.**
- EA-8 GOOD (30-34): _cache_put with try/except → pass.
- EA-9 BUG (33): No atomic + bare Exception. **70th unsafe writer.**
- EA-10 GOOD (37-54): fetch_earnings_history with **8-quarter limit + 15s timeout + cache-or-fetch pattern.**
- EA-11 GOOD (57-74): fetch_recommendations with same pattern.
- EA-12 GOOD (77-204): analyze_earnings with **4-section pipeline** (earnings history → analyst recs → sub-scores → composite).
- EA-13 GOOD (79-91): 11-key skeleton with **0.5 fail-safe default earnings_quality.**
- EA-14 GOOD (97-98): clean = filter on both actual+estimate present (defensive).
- EA-15 GOOD (107-110): surprise % with `if estimate != 0` div-by-zero guard.
- EA-16 GOOD (121-125): EPS YoY momentum with `>= 5` quarters guard.
- EA-17 GOOD (140-154): rec_trend with **3-month-old comparison + 3-tier classification** (improving/stable/deteriorating).
- EA-18 GOOD (157-202): 5-sub-scorer dispatch with **piecewise tiers + 35/20/20/15/10% weight distribution = 100%.**
- EA-19 GOOD (200-202): Composite via weighted-sum normalized by sum-of-weights — handles missing sub-scores gracefully.
- EA-20 GOOD (207-214): __main__ smoke test with default 4-ticker batch. **33rd smoke test.**

## src/agent_memoir.py — LINE BY LINE

- AM-1 GOOD (1-12): 12-line docstring with **founder-archaeology May 4 2026 + identity-continuity mandate.** ✅
- AM-2 GOOD (5-7): Founder-quote archaeology ("Agent should not forget its mistakes and learnings, the wins, and what its task is supposed to be").
- AM-3 GOOD (24-29): MISSION_STATEMENT module constant — first-person agent narrative.
- AM-4 BUG (32-36): _safe_float duplicate (**41st instance**).
- AM-5 GOOD (39-47): _load_closed_picks with 4-status whitelist.
- AM-6 GOOD (50-62): _load_learning_events with line-by-line try/except.
- AM-7 BUG (61): bare Exception.
- AM-8 GOOD (65-83): _biggest_win with **per-row r_multiple + max + 6-key narrative dict.**
- AM-9 GOOD (78-82): Narrative string in first-person ("This is the kind of setup I should look for more of").
- AM-10 GOOD (86-110): _biggest_loss with **earnings-warn defensive + lesson_learned narrative.**
- AM-11 GOOD (95-98): try/except for d2e int conversion.
- AM-12 BUG (98): bare ValueError/TypeError caught (acceptable narrow).
- AM-13 GOOD (113-129): _summarize_recent_learning with **TZ-aware UTC cutoff + 3-event-kind tally.** ✅
- AM-14 GOOD (114): TZ-aware UTC ✅
- AM-15 BUG (123): bare Exception.
- AM-16 GOOD (132-188): write_memoir orchestrator with **8-key memoir + 4-tier current_focus dispatch by win_rate.**
- AM-17 GOOD (140-160): 4-tier current_focus dispatch (n<30 OBSERVATION / wr<40% need-tighten / wr≥50% improve-R / else refine-stats).
- AM-18 GOOD (174-178): "what_im_proud_of" 3-line first-person narrative — operator-trust gold standard.
- AM-19 GOOD (180-183): "promise_to_anjan" 3-line founder-direct first-person.
- AM-20 BUG (187): No atomic. **71st unsafe writer.**
- AM-21 GOOD (191-193): __main__ smoke test. **34th smoke test.**

## CONSOLIDATED CROSS-CUTTING (THIS BATCH)

### NEW Theme T39 (PILLAR-1+3.5+4 BRAIN MUTATION PIPELINE COMPLETE)
**6-stage pipeline now FULLY AUDITED:**
| Stage | Module | Pillar | Mode |
|---|---|---|---|
| 1. Stats foundation | SS-X1 stock_stats | Pillar 1 Layer 1 | Compute |
| 2. Hypothesis detection | HE-X1 hypothesis_engine | Pillar 1 Layer 4 | OBSERVE-ONLY |
| 3. Calibration aggregation | CAL-X1 calibration | Pillar 3.5 | READ-ONLY |
| 4. Proposal generation | WP-X1 weight_proposer | Pillar 3.5 C3 | READ-ONLY (proposes) |
| 5. Proposal application | WA-X1 weight_applier | Pillar 4 | MUTATES (with cap+dry-run) |
| 6. Self-introspection | MB-X1 meta_brain | T50 | OBSERVE-ONLY |

**Document complete in `docs/BRAIN_MUTATION_PIPELINE.md`** — gold-standard "auto-feedback-loop with audit + reversibility" pattern.

### NEW Theme T40 (ADR-REFERENCED ARCHITECTURE MODULES)
- SS-X1 references `docs/decisions/ADR-001-probability-over-rules.md` + `docs/PROBABILITY_ENGINE_DESIGN.md` + `docs/BRAIN_ARCHITECTURE.md` (Pillar 1).
- **First audited module with explicit ADR + design-doc + architecture-doc trio.**
- **Recommend** auditing all docs/decisions/ADR-*.md separately as Phase J.

### Theme T36 (SHARED-LIBRARY DUPLICATION ACROSS DIRECTORIES) UPDATE
**3 distinct Sharpe annualizations across 3 modules:**
| Module | Annualization | Comment |
|---|---|---|
| RKM-X1 risk_metrics (B70) | sqrt(50) | "trades/year" |
| BM-X1 backtester/metrics (B71) | sqrt(250) | "trading days" |
| **PT3-X1 performance_tracker (B73)** | sqrt(252) | "trading days" — different from BM by 2 |

**3 different math conventions producing different "Sharpe" numbers from same inputs.** **CRITICAL math-drift risk.** Consolidate into `src/_stats.py`.

### Theme T38 (AUTO-FEEDBACK-LOOP MODULES) UPDATE
**2 modules now mutate production behavior:**
- PL-X1 (B72) auto_enable_disable patterns — basic implementation.
- **WA-X1 (B73) apply_proposals — DISCIPLINED** (5%/week cap + idempotent + dry-run default + CLI opt-in + journal hook).

**WA-X1 IS THE GOLD-STANDARD TEMPLATE** for future auto-feedback loops.

### Theme T35 (CROSS-MODULE HELPER IMPORTS) UPDATE
- B71 PHS imports from double
- B71 PW imports from triangles
- **B73 CAL imports from weight_proposer (open_proposals_summary)**
- **B73 WA imports from weight_proposer (proposals reading)**
- **B73 WP imports from calibration (read backtest runs)**

**5 cross-module helper imports. CAL ↔ WP ↔ WA = 3-way mutual import dependency** — verify no circular import.

### Theme T8 (DRY) UPDATE
- _safe_float / _safe_int / _to_float duplicates: **NOW 41 modules** (B73 added MB + PT3 + AM = 3 new).
- **41 IS BREAKING POINT^3 — STILL NOT CONSOLIDATED.**
- **Sharpe/MaxDD: 3 distinct implementations.**
- **Keyword-bag-of-words: NOW 10 modules** (B73 added 3 vocabularies in NS2 alone — CATALYST_RULES + CATASTROPHIC + NEGATIVE_REACTION).

### Theme T6 (ATOMIC WRITES) UPDATE
| Module | Status |
|---|---|
| **NS2-12 news_signals.json** | ✅ POSITIVE 10 |
| WA-5 weights.json | ❌ unsafe (66th) |
| WA-13 weight_history.jsonl | ❌ unsafe (67th) |
| WA-26 proposals.jsonl rewrite | ❌ unsafe (68th) **HIGH-RISK** |
| WP-15 weight_proposals.jsonl | ❌ unsafe (69th) |
| EA-9 earnings cache | ❌ unsafe (70th) |
| AM-20 agent_memoir.json | ❌ unsafe (71st) |
| SS-18 stock_stats per-ticker | ❌ unsafe (63rd) |
| PT3-20 metrics_daily.json | ❌ unsafe (64th) |
| PT3-22 metrics_history.jsonl | ❌ unsafe (65th) |

**Tally: 10 safe / 71 unsafe / 81 = ~88% UNSAFE.** Getting worse.

### Cross-cutting tally summary (this batch only)
| Metric | Before | This batch | After |
|---|---:|---:|---:|
| _safe_float / _safe_int / _to_float | 37 | 4 (MB + PT3 + AM + WA) | **41 BREAKING POINT^3** |
| Bare-except | mod | ~30 | continues moderate |
| Inline imports | ~42 | 1 (CAL → WP) | **~43** |
| Import-time side effects | 21 | 1 (EA load_dotenv + mkdir) | **22** |
| Unsafe writers | 62 | 9 | **71 / 81 = 88% UNSAFE** |
| Atomic writers | 9 | 1 (NS2) | **10** |
| TZ-aware modules | 23 | 3 (NS2 + WA + AM) | **26** |
| Naive datetime usage | catalog | 11 (CAL+MB×2+PT3×3+SS×2+WA×2+WP+EA) | **catalog ongoing — 22+ instances** |
| DATED archaeology | 62 | ~25 (T37+T38+T39+T44+T49+T50+T51+T44+E2c.3+Phase3+Pillar1/3.5/4+Bug6+PR77+May4 2026 ×3+May5 2026+EVC-style) | **~87** |
| Frozen dataclasses | 5 | 0 | 5 |
| Regular dataclasses | 11 | 2 (BucketStat + Proposal) | **13** |
| OBSERVE-MODE modules | 27 | 2 (HE + MB) | **29** |
| __main__ smoke tests | 29 | 5 (NS2 + SS + PT3 + EA + AM) | **34** |
| Pure-stdlib statistical | 5 | 0 (HE was 5th already from B68/B69) | **5** |
| Theme T11 newline="" POSITIVE | 6 | 0 | 6 |
| Theme T35 cross-module helpers | 3 | 3 (CAL→WP, WA→WP, WP→CAL) | **6 — 3-way mutual** |
| Theme T36 shared-lib duplication | 1 | 1 (PT3 sharpe — 3rd convention) | **3 distinct Sharpe annualizations** |
| Theme T38 auto-feedback-loop | 1 | 1 (WA — disciplined gold standard) | **2 modules** |
| Theme T39 brain-mutation pipeline | new | 6 modules complete | **PIPELINE COMPLETE** |
| Theme T40 ADR-referenced | new | 1 (SS) | **1** |
| Keyword-bag-of-words | 7 | 3 (NS2 ×3 distinct vocabularies) | **10** |
| Sibling-module pairs | 9 | 0 | 9 |
| Provider modules | 1 | 0 | 1 |
| Optional-dep import patterns | 2 | 4 (DF curl_cffi + DF finnhub + EAR curl_cffi + SS yfinance + WA learning_journal) | **7** |
| ABC base classes | 1 | 0 | 1 |
| Inheritance patterns | 3 | 0 | 3 |
| Rich-library consumers | 0 | 1 (PS2) | **1 — NEW** |
| Yfinance brittleness defense | catalog | 2 (DF thread-safety + EAR shape-tolerance) | **catalog updated** |
| 12-key+ schemas | 11 | 5 (CAL 12-bucket + CDI 14-kwarg + IND 30-key signals + WA 10-key mutation + AM 8-key memoir) | **16** |

## SUMMARY (Batch 73 — 15-FILE)

| File | Show-stop | Data/safety | Code smell | Good code | Findings |
|---|---:|---:|---:|---:|---:|
| calibration | 4 | 0 | 0 | 20 | 24 |
| candidate_diagnostics | 0 | 0 | 0 | 13 | 13 |
| hypothesis_engine | 0 | 0 | 0 | 17 | 17 |
| indicators | 4 | 0 | 0 | 18 | 22 |
| data_fetcher | 7 | 0 | 0 | 22 | 29 |
| meta_brain | 9 | 0 | 0 | 21 | 30 |
| news_signals | 4 | 0 | 0 | 22 | 26 |
| stock_stats | 6 | 0 | 0 | 18 | 24 |
| performance_stats | 0 | 0 | 0 | 10 | 10 |
| performance_tracker | 7 | 0 | 0 | 16 | 23 |
| weight_applier | 9 | 0 | 0 | 22 | 31 |
| weight_proposer | 2 | 0 | 0 | 17 | 19 |
| earnings | 7 | 0 | 0 | 11 | 18 |
| earnings_analyzer | 5 | 0 | 0 | 15 | 20 |
| agent_memoir | 4 | 0 | 0 | 17 | 21 |
| **TOTAL** | **68** | **0** | **0** | **259** | **327** |

## TOP 15 CRITICAL FIXES from Batch 73

1. **Theme T36 _src/_stats.py CRITICAL CONSOLIDATION:** **3 distinct Sharpe annualization conventions** (sqrt(50)/sqrt(250)/sqrt(252)) across RKM + BM + PT3 produce **DIFFERENT "Sharpe" numbers from identical inputs**. **CRITICAL math-drift risk.** Create `src/_stats.py` with single canonical Sharpe + Sortino + MaxDD + ProfitFactor. (1.5 hours)
2. **Theme T8 _src/_safe.py CRITICAL CONSOLIDATION:** _safe_float duplicates **NOW 41 MODULES** (BREAKING POINT^3). **STILL NOT CONSOLIDATED.** Create `src/_safe.py`. (2 hours migration)
3. **WA-26 ATOMIC WRITE for proposals.jsonl rewrite:** Currently rewrites ENTIRE proposals.jsonl non-atomically with `applied:true` markers. Partial write would lose ALL proposal history. **HIGHEST-RISK individual fix.** (10 min)
4. **NEW Theme T39 BRAIN-MUTATION PIPELINE documentation:** Document complete 6-stage Pillar 1+3.5+4 chain in `docs/BRAIN_MUTATION_PIPELINE.md`. WA-X1 should be highlighted as **gold-standard auto-feedback-loop template** (cap+dry-run+CLI+journal+idempotent). (1.5 hours)
5. **Theme T39 CIRCULAR IMPORT VERIFICATION:** CAL → WP / WA → WP / WP → CAL = 3-way mutual import. Verify no circular import + lazy-load if needed. (15 min)
6. **NEW Theme T31 yfinance brittleness defense documentation:** DF-X1 thread-safety + EAR-X1 shape-tolerance + STQ-X1 fallback = **3-pronged defense pattern**. Document in `docs/YFINANCE_BRITTLENESS_DEFENSE.md`. (45 min)
7. **NS2-X1 atomic-rename PROPAGATION:** NS2-12 is gold standard. Apply pattern to **9 unsafe writers from this batch (WA + WP + EA + AM + SS + PT3 ×2)** + **the 71 cumulative unsafe writers**. Bulk fix. (2 hours)
8. **11 naive datetime instances this batch (CAL+MB×2+PT3×3+SS×2+WA+WP+EA):** Bulk migrate to TZ-aware. (45 min)
9. **PT3-9 + PT3-11 Sharpe/MaxDD inline duplication:** Migrate to `src/_stats.py` per fix #1. (15 min)
10. **WA-X1 disciplined auto-feedback-loop pattern:** Promote as template. Apply to PL-X1 (B72 patterns auto_enable_disable) — currently lacks 5%/week cap + dry-run default + journal-hook. (1 hour refactor PL-X1 to match WA-X1 discipline)
11. **HE-X1 + MB-X1 OBSERVE-MODE explicit:** 2 modules now have explicit OBSERVE-MODE mandates. Tally with B71+B70+B72 OBSERVE-MODE = 29 modules. **Document in `docs/OBSERVE_MODE_DISCIPLINE.md`** with rules for when to use vs when to allow mutation. (45 min)
12. **CAL-23 + WA-23 + MB-25 inline imports:** 3 inline imports for cross-module reads. Bulk hoist to module-level imports (verify no circular dependency). (10 min)
13. **EA-3 load_dotenv at-import:** 11th instance of import-time side-effect. Bulk migrate to lazy-load + memoize. (15 min)
14. **NEW Theme T40 ADR-REFERENCED audit:** SS-X1 references ADR-001. **Audit all docs/decisions/ADR-*.md as Phase J** — first-class architecture documentation deserves dedicated audit. (placeholder)
15. **NEW Theme T39 Pillar-anchored architecture documentation:** Update `docs/BRAIN_ARCHITECTURE.md` with Pillar 1 (SS+HE+probability_engine) + Pillar 3.5 (CAL+WP) + Pillar 4 (WA) + T50 (MB) cross-references. (45 min)

## NEW THEMES UPDATED

- **NEW Theme T39 (BRAIN-MUTATION PIPELINE):** 6-stage Pillar 1+3.5+4 chain COMPLETE. Auto-feedback-loop with audit + reversibility = gold-standard pattern.
- **NEW Theme T40 (ADR-referenced architecture modules):** First audited ADR-aware module (SS-X1). Phase J should audit ADRs.
- **Theme T36 (shared-lib duplication):** **3 distinct Sharpe annualizations** — CRITICAL math-drift.
- **Theme T38 (auto-feedback-loop):** **2 modules now**, WA-X1 is gold-standard template.
- **Theme T35 (cross-module helpers):** **5 instances now, including 3-way mutual** (CAL ↔ WP ↔ WA).
- **Theme T8 (DRY):** _safe_float at **41 modules** (BREAKING POINT^3).
- **Theme T6 (atomic writes):** **88% UNSAFE (71/81).**
- **Theme T11 (newline=""):** Stable at 6 POSITIVE.

## COVERAGE TRACKER

| Phase | Status | Cumulative |
|---|---|---:|
| Phase G | done | 30/~30 |
| Phase H | active | 47/~50 |
| Total true line-by-line | **+15 files (15 successful, 0 failures)** | **268 of ~378 (~70.9%)** |

**🎯 71% AUDIT MILESTONE. PILLAR 1+3.5+4 BRAIN-MUTATION PIPELINE COMPLETE 6-MODULE AUDIT. Theme T36 critical math-drift identified (3 Sharpe conventions). Theme T39 + T40 cataloged. WA-X1 = gold-standard auto-feedback-loop template.**

## NEXT BATCH (15-FILE)

Batch 74: Continue Phase H. Remaining src/ candidates:
- agent_memoir done. Remaining: auto_promote, auto_pause, auto_cooldown, book_ingest, daily_wisdom, day_trading_scorer, dedup_sender, exit_manager, exit_metrics, finnhub_data, fundamentals, hard_blocks, learning_journal, lesson_gc, llm_agent, market_calendar, market_data_health, market_guard, market_news, monster_hunt, news_classifier, news_engine, news_sentiment, nightly_conductor, parallel_scorer, pause_state, premarket_filter, premarket_readiness_gate, premarket_sanity_gate, probability_engine, quarterly_report, regime, risk_manager, scorer, scoring_safety, sector_benchmark, sector_breakdown, sector_pnl, self_awareness, semiconductors, signal_journal, smell_faculty, strategy_breakdown, theme_scoring_guardrails, trailing_stop, universe, watchlist_manager, weekly_review, wisdom_base, wisdom_consultant, wisdom_coverage, wisdom_hint, wow_trend, yearly_report, cape_ratio, confidence_band, data_quality, dedup_sender

End of Batch 73. **🎯 71% audit milestone. PILLAR 1+3.5+4 brain-mutation pipeline COMPLETE 6-module audit. NEW Theme T39 + T40. WA-X1 = gold-standard. CRITICAL Theme T36 math-drift (3 Sharpe annualizations).**
