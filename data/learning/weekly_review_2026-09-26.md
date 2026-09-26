# 🧠 Weekend Review — 2026-09-26

_⚠️ Gemini free quota exhausted — using local analysis._

---

# 📊 Weekly Local Analysis (7d)

**Period:** 7d  •  **Picks:** 8  •  **Evaluated:** 2  •  **Pending:** 0


## 🎯 Headline
- **Win rate:** 100.0%  (2 TP / 0 SL)
- **Avg R-multiple:** 1.67
- **Cumulative return:** +5.33%

## 🏆 Top winners
- DHR: +2.68% (R=1.6657)
- WAT: +2.65% (R=1.67)

## 💀 Worst losers
- WAT: +2.65% (R=1.67)
- DHR: +2.68% (R=1.6657)

## 💡 Code Improvement Suggestions (plain English)

📚 **Need more data.** Wait until you have 10-15 evaluated trades before drawing conclusions.


## 🔬 Code-Aware Diagnostic

### 📋 Current strategy parameters

**`config.yaml`**
- `universe.source = sp500`
- `universe.include_watchlist = True`
- `universe.semiconductors.always_include = True`
- `universe.semiconductors.min_ai_weight = 0.0`
- `universe.min_price = 5.0`
- `universe.max_price = 1500.0`
- `universe.min_avg_volume = 500000`
- `strategy.style = swing`
- `strategy.lookback_days = 180`
- `weights.trend = 0.18`
- `weights.momentum = 0.2`
- `weights.volatility = 0.08`
- _… +37 more_

**`main.py`**
- `_safe_trade_type_for_pick(gap_pct) = 0.0` (line 37)

**`src/adaptive_sl.py`**
- `should_tighten_sl(min_profit_pct) = 2.0` (line 19)
- `should_tighten_sl(fade_rsi_threshold) = 55.0` (line 19)
- `should_tighten_sl(peak_rsi_threshold) = 65.0` (line 19)
- `should_tighten_sl(vol_fade_threshold) = 0.7` (line 19)
- `should_tighten_sl(cooldown_min) = 30` (line 19)
- `should_tighten_sl(tighten_pct) = 1.0` (line 19)

**`src/adaptive_tp.py`**
- `should_raise_tp(gain_threshold_pct) = 5.0` (line 17)
- `should_raise_tp(rsi_threshold) = 70.0` (line 17)
- `should_raise_tp(vol_threshold) = 1.8` (line 17)
- `should_raise_tp(cooldown_min) = 60` (line 17)
- `should_raise_tp(headroom_pct) = 5.0` (line 17)

**`src/auto_cooldown.py`**
- `CONSECUTIVE_LOSS_THRESHOLD = 3` (line 20)
- `DEFAULT_COOL_OFF_DAYS = 14` (line 21)
- `scan_and_cool(apply) = False` (line 67)

**`src/auto_pause.py`**
- `MIN_N_FOR_ZERO_WIN = 5` (line 206)
- `LOSS_STREAK_LEN = 3` (line 207)
- `MIN_N_FOR_NEG_R = 4` (line 208)
- `NEG_R_THRESHOLD = -5.0` (line 209)
- `get_paused_set(lookback_days) = 30` (line 251)
- `is_group_paused(lookback_days) = 30` (line 269)

**`src/auto_promote.py`**
- `MIN_SAMPLE = 40` (line 37)
- `MAX_P = 0.01` (line 38)
- `promote_patterns(dry_run) = False` (line 81)

**`src/book_ingest.py`**
- `load_seed(dry_run) = False` (line 60)

**`src/calibration.py`**
- `attribute_by(min_n) = 5` (line 166)
- `per_factor_report(min_n) = 5` (line 218)
- `per_timeframe_report(min_n) = 5` (line 227)
- `telegram_footer_lines(min_n) = 30` (line 356)

**`src/cape_ratio.py`**
- `_CAPE_VALUE = 38.5` (line 6)

**`src/daily_wisdom.py`**
- `N_ANECDOTAL = 20` (line 28)
- `N_DIRECTIONAL = 50` (line 29)
- `N_CONFIDENT = 100` (line 30)

**`src/data_fetcher.py`**
- `fetch_universe_data(max_workers) = 5` (line 120)

**`src/day_trading_scorer.py`**
- `day_trading_score(news_boost) = 0.0` (line 90)
- `is_day_tradeable(min_threshold) = 0.65` (line 145)

**`src/dedup_sender.py`**
- `should_send(window_minutes) = 60` (line 62)
- `mark_sent(window_minutes) = 60` (line 78)

**`src/earnings.py`**
- `UNKNOWN_EARNINGS_DAYS = 999` (line 14)
- `earnings_safe(min_days) = 5` (line 167)

**`src/exit_metrics.py`**
- `_safe_float(default) = 0.0` (line 17)

**`src/finnhub_data.py`**
- `cross_validate_price(warn_threshold_pct) = 2.0` (line 207)
- `cross_validate_price(block_threshold_pct) = 5.0` (line 207)

**`src/hard_blocks.py`**
- `MIN_PRICE = 5.0` (line 32)
- `COOLDOWN_DAYS = 3` (line 63)
- `SECTOR_ETF_DROP_THRESHOLD = -5.0` (line 101)
- `apply_hard_blocks(check_sectors) = True` (line 278)

**`src/hypothesis_engine.py`**
- `MIN_SAMPLE_SIZE = 10` (line 23)
- `SIGNIFICANCE_THRESHOLD = 0.05` (line 24)

**`src/indicators.py`**
- `rsi(period) = 14` (line 18)
- `macd(fast) = 12` (line 26)
- `macd(slow) = 26` (line 26)
- `macd(signal) = 9` (line 26)
- `bollinger(period) = 20` (line 35)
- `bollinger(std) = 2.0` (line 35)
- `atr(period) = 14` (line 41)
- `stochastic(k_period) = 14` (line 55)
- `stochastic(d_period) = 3` (line 55)
- `parabolic_sar(af_start) = 0.02` (line 68)
- `parabolic_sar(af_step) = 0.02` (line 68)
- `parabolic_sar(af_max) = 0.2` (line 68)
- _… +5 more_

**`src/layman_translator.py`**
- `pick_to_layman(idx) = 1` (line 97)
- `verdict_line(total_pnl) = 0` (line 218)

**`src/learned_weights.py`**
- `MULT_FLOOR = 0.85` (line 30)
- `MULT_CEIL = 1.15` (line 31)

**`src/learning_journal.py`**
- `summary(days) = 7` (line 61)

**`src/lesson_gc.py`**
- `MAX_AGE_DAYS = 90` (line 25)
- `PROTECT_CONF = 0.9` (line 26)
- `gc_stale(dry_run) = False` (line 67)

**`src/llm_agent.py`**
- `_MIN_INTERVAL = 1.5` (line 52)

**`src/market_calendar.py`**
- `next_trading_day(max_lookahead) = 14` (line 130)
- `previous_trading_day(max_lookback) = 14` (line 140)
- `needs_renewal(threshold_years) = 2` (line 165)

**`src/market_data_health.py`**
- `MAX_SAMPLES = 30` (line 29)

**`src/market_guard.py`**
- `classify_trade_type(gap_pct) = 0.0` (line 53)
- `classify_with_day_score(gap_pct) = 0.0` (line 106)

**`src/market_news.py`**
- `fetch_market_news(limit) = 40` (line 35)

**`src/monster_data.py`**
- `CACHE_TTL_HOURS = 24` (line 14)

**`src/monster_hunt.py`**
- `score_monster(has_bullish_news) = False` (line 26)
- `apply_monster_treatment(account_size) = 10000.0` (line 103)
- `apply_monster_treatment(monster_position_pct) = 1.5` (line 103)

**`src/news_classifier.py`**
- `classify_batch(max_items) = 20` (line 119)

**`src/news_engine.py`**
- `DEDUP_TTL_HOURS = 48` (line 20)
- `fetch_alpaca_news(limit) = 50` (line 47)
- `fetch_alpaca_news(since_minutes) = 60` (line 47)
- `fetch_all_news(since_minutes) = 60` (line 123)

**`src/news_sentiment.py`**
- `fetch_news(limit) = 5` (line 19)

**`src/news_signals.py`**
- `rebuild_from_news_log(days_back) = 30` (line 317)

**`src/nightly_conductor.py`**
- `_load_universe_for_scan(max_tickers) = 100` (line 79)
- `_step_pattern_scan(max_tickers) = 100` (line 108)

**`src/official_pick_artifact.py`**
- `_safe_float(default) = 0.0` (line 56)
- `_safe_int(default) = 0` (line 65)

**`src/opening_range_scanner.py`**
- `DEFAULT_RANGE_MINUTES = 15` (line 29)
- `_num(default) = 0.0` (line 50)
- `calculate_opening_range(min_bars) = 3` (line 91)

**`src/parallel_scorer.py`**
- `score_all(max_workers) = 10` (line 188)

**`src/pattern_engine.py`**
- `load_recent(days) = 30` (line 62)

**`src/pattern_layer.py`**
- `MIN_SAMPLE_FOR_EDGE = 20` (line 20)
- `EDGE_R_THRESHOLD = 0.2` (line 21)
- `MAX_BOOST = 0.15` (line 22)
- `auto_enable_disable(kill_threshold_r) = -0.3` (line 94)
- `auto_enable_disable(min_n) = 30` (line 94)

**`src/pause_state.py`**
- `trigger_pause(days) = 3` (line 88)
- `trigger_pause(manual) = False` (line 88)

**`src/performance_tracker.py`**
- `_safe_float(default) = 0.0` (line 40)
- `_sharpe(risk_free_pct) = 0.0` (line 72)

**`src/pick_evaluator.py`**
- `MAX_DAYS_OPEN = 20` (line 24)
- `EVAL_LOOKBACK_DAYS = 30` (line 25)

**`src/portfolio_risk_gate.py`**
- `DEFAULT_MAX_NEW_PICKS_PER_DAY = 5` (line 29)
- `DEFAULT_MAX_PER_SECTOR = 2` (line 30)
- `DEFAULT_MAX_PER_TAG = 2` (line 31)
- `DEFAULT_MIN_RISK_REWARD = 1.0` (line 32)
- `DEFAULT_MAX_PAIRWISE_CORRELATION = 0.7` (line 33)
- `DEFAULT_CORR_LOOKBACK_DAYS = 60` (line 34)
- `MIN_CORR_OVERLAP_OBS = 30` (line 35)
- `_safe_int(default) = 0` (line 47)

**`src/post_open_scanner.py`**
- `MIN_TRADEABLE_SCORE = 0.6` (line 40)
- `MAX_OPPORTUNITIES = 5` (line 41)
- `STANDARD_SCORE_CAP = 90.0` (line 45)
- `CORPORATE_ACTION_SCORE_CAP = 70.0` (line 46)
- `_as_float(default) = 0.0` (line 57)

**`src/premarket_filter.py`**
- `gap_check(max_gap_up) = 0.03` (line 4)
- `gap_check(max_gap_down) = -0.05` (line 4)

**`src/premarket_readiness_gate.py`**
- `DEFAULT_MIN_FETCH_COVERAGE = 0.05` (line 18)
- `DEFAULT_MIN_FETCHED_COUNT = 15` (line 19)
- `_safe_int(default) = 0` (line 22)
- `_safe_float(default) = 0.0` (line 29)

**`src/premarket_sanity_gate.py`**
- `_PRICE_CACHE_TTL = 60.0` (line 32)
- `_FETCH_TIMEOUT = 5.0` (line 33)
- `_BATCH_TIMEOUT = 60.0` (line 34)

**`src/price_sanity.py`**
- `DEFAULT_MAX_MOVE_PCT = 25.0` (line 32)
- `CORROBORATION_TOLERANCE_PCT = 2.0` (line 35)
- `_SPLIT_FACTOR_TOLERANCE = 0.03` (line 39)

**`src/probability_engine.py`**
- `DEFAULT_P_WIN_PRIOR = 0.5` (line 77)
- `compute_probabilistic_decision(holding_days) = 5` (line 166)

**`src/quarterly_report.py`**
- `_top_movers(k) = 5` (line 96)
- `generate_report(days) = 90` (line 148)

**`src/regime.py`**
- `_fetch_spy_with_retry(max_attempts) = 3` (line 40)

**`src/risk_manager.py`**
- `atr_trade_plan(risk_pct) = 0.01` (line 66)
- `atr_trade_plan(atr_mult_sl) = 2.0` (line 66)
- `atr_trade_plan(atr_mult_tp) = 2.5` (line 66)

**`src/risk_metrics.py`**
- `TRADING_DAYS_PER_YEAR = 252` (line 27)
- `_sharpe(rf_per_period) = 0.0` (line 50)
- `_sortino(rf_per_period) = 0.0` (line 61)

**`src/scorer.py`**
- `apply_sector_cap(max_per_sector) = 4` (line 16)
- `apply_tag_cap(max_per_tag) = 2` (line 38)

**`src/scoring_safety.py`**
- `MAX_ALLOWED_SEMI_BOOST = 1.0` (line 18)
- `MAX_ALLOWED_AI_BOOST = 0.0` (line 19)

**`src/self_awareness.py`**
- `wilson_ci(z) = 1.96` (line 23)
- `mean_r_ci(z) = 1.96` (line 34)
- `rolling_window(days) = 30` (line 63)

**`src/semiconductors.py`**
- `get_semi_tickers(min_ai_weight) = 0.0` (line 53)

**`src/stock_stats.py`**
- `empirical_sl_pct(target_p_noise) = 0.3` (line 239)
- `empirical_tp_pct(days) = 5` (line 272)
- `empirical_tp_pct(target_p_reach) = 0.5` (line 272)

**`src/trade_state.py`**
- `FLAT_EPSILON_PCT = 0.05` (line 78)
- `DEFAULT_MAX_HOLD = 14` (line 88)

**`src/trailing_stop.py`**
- `compute_trailing_sl(activation_pct) = 3.0` (line 9)
- `compute_trailing_sl(trail_pct) = 2.0` (line 9)

**`src/watchlist_manager.py`**
- `WATCHLIST_TTL_HOURS = 72` (line 14)
- `MIN_TRADEABLE_SCORE = 0.5` (line 15)
- `get_watchlist_tickers(bullish_only) = False` (line 125)

**`src/weight_applier.py`**
- `WEEKLY_CAP_PCT = 5.0` (line 35)
- `apply_proposals(dry_run) = False` (line 115)
- `history_summary(days) = 7` (line 203)

**`src/weight_proposer.py`**
- `BIAS_BOOST_THRESHOLD = 0.1` (line 51)
- `BIAS_PENALIZE_THRESHOLD = -0.1` (line 52)
- `KILL_BIAS_THRESHOLD = -0.3` (line 53)
- `KILL_WIN_RATE_MAX = 0.35` (line 54)
- `DELTA_CAP = 5.0` (line 55)
- `DELTA_MULTIPLIER = 25` (line 56)
- `propose(min_n) = 30` (line 113)
- `read_proposals(only_unapplied) = False` (line 178)

**`src/wisdom_base.py`**
- `add_lesson(confidence) = 0.5` (line 31)
- `load_active_lessons(min_confidence) = 0.5` (line 58)
- `add_to_kill_list(cool_off_days) = 14` (line 154)
- `lessons_for_ticker(min_confidence) = 0.7` (line 218)
- `lessons_for_context(min_confidence) = 0.7` (line 296)

**`src/wisdom_consultant.py`**
- `SCORE_ADJ_CAP = 0.05` (line 22)

**`src/wisdom_hint.py`**
- `_format_lesson(max_len) = 90` (line 30)
- `wisdom_hint(min_confidence) = 0.7` (line 51)
- `pattern_hint(min_sample) = 20` (line 88)
- `pattern_hint(max_p) = 0.05` (line 88)
- `context_hint(min_confidence) = 0.8` (line 235)

**`src/wow_trend.py`**
- `_arrow(good_positive) = True` (line 70)

### 🩺 Code-targeted suggestions
_(based on last 7d, 2 evaluated trades)_


📚 Need at least 5 evaluated trades for code-aware diagnosis.


---
_Deterministic rules, not AI. Use as hypotheses to test._

---

Raw observations: 2 this week.