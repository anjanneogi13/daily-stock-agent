# Intraday Technical Indicators Roadmap

## Purpose

This document defines the technical-analysis features needed to evolve the intraday model from a simple rules-based scanner into a serious chart-aware, self-learning model.

## Current State

The current intraday scanner primarily uses:

- opening range high/low
- opening range breakout %
- opening range width %
- volume ratio
- gap %
- extension %
- intraday price change %
- basic material news/catalyst detection

It does not yet meaningfully use most common chart indicators for candidate selection:

- VWAP
- RSI
- MACD
- moving averages
- stochastic oscillator
- stochastic divergence
- Bollinger Bands
- ATR
- support/resistance
- multi-timeframe trend
- candlestick/wick quality

Some RSI-related logic exists in the existing-pick adaptive SL/TP monitoring path, but not enough to call the intraday scanner a chart-reading system.

## Core Principle

Do not build indicator soup.

More indicators do not automatically make the model better.

The goal is:

- chart-structure model
- indicator confirmation
- outcome learning

Each indicator must answer a useful question and later be measured against actual outcomes.

## Human Chart Reading vs Agent Features

A human chart reader may say:

- this breakout looks clean
- this is chasing
- momentum is fading
- price rejected resistance
- pullback held VWAP

The model should translate those ideas into measurable features.

### Clean breakout

A clean breakout can be measured by:

- price above opening-range high
- close near candle high
- small upper wick
- high volume ratio
- price above VWAP
- market above VWAP
- sector confirming
- not too extended from VWAP
- acceptable risk/reward

### Chasing risk

Chasing risk can be measured by:

- extension above opening-range high too large
- distance from VWAP too large
- RSI too extended
- gap too large
- large upper wick
- poor risk/reward

### Momentum fading

Momentum fading can be measured by:

- lower highs
- MACD histogram falling
- RSI divergence
- volume declining
- break below 9 EMA
- failed VWAP hold

### Rejection

Rejection can be measured by:

- large upper wick
- failed break above prior high
- failed break above premarket high
- close back below breakout level
- declining volume on retest

### VWAP hold

VWAP hold can be measured by:

- pullback touches or approaches VWAP
- price closes back above VWAP
- lower wick forms near VWAP
- volume stabilizes or increases on bounce

## Tier 1 Indicators

These should be implemented first.

### VWAP

VWAP is one of the most important intraday indicators.

Features:

- vwap
- price_above_vwap
- distance_from_vwap_pct
- vwap_slope
- vwap_reclaim
- vwap_hold
- failed_vwap_hold

Initial use:

- hard filter
- score feature
- chase-risk guard

Learning questions:

- Do above-VWAP breakouts outperform below-VWAP breakouts?
- What VWAP distance becomes too extended?
- Do VWAP reclaim setups outperform pure breakouts?

### Relative Volume

Features:

- latest_bar_volume_ratio
- relative_volume_5m
- relative_volume_15m
- cumulative_volume_vs_average
- dollar_volume
- avg_daily_volume
- liquidity_score

Initial use:

- hard filter
- score feature

Learning questions:

- Does volume ratio above 2.0 outperform 1.5?
- Is latest-bar volume more predictive than cumulative volume?
- What minimum dollar volume reduces false signals?

### ATR / Volatility

ATR is needed for realistic stops.

Features:

- atr_14
- atr_pct
- stop_distance_atr
- target_distance_atr
- opening_range_width_vs_atr
- volatility_regime

Initial use:

- risk/reward validation
- stop placement
- hard blocker

Learning questions:

- Do ATR-adjusted stops outperform opening-range-low stops?
- What stop_distance_atr gives best expectancy?
- Does opening_range_width_vs_atr predict false breakouts?

### Moving Averages / EMAs

Use intraday EMAs for short-term trend and daily MAs for higher timeframe context.

Features:

- ema_9
- ema_20
- ema_50
- price_above_9ema
- price_above_20ema
- ema_stack_bullish
- ema_slope
- dma_20
- dma_50
- dma_200
- daily_trend_alignment

Initial use:

- score feature
- trend filter
- momentum-fading signal

Learning questions:

- Do EMA-stacked breakouts outperform non-stacked breakouts?
- Does daily trend alignment improve intraday expectancy?
- Is 9 EMA or 20 EMA more useful for exits?

### RSI

RSI should not be used naively as "overbought means sell."

For intraday momentum, strong stocks can stay overbought.

Features:

- rsi_14
- rsi_slope
- rsi_above_50
- rsi_above_70
- rsi_above_80
- bullish_rsi_divergence
- bearish_rsi_divergence

Initial use:

- momentum confirmation
- overextension warning
- divergence warning

Learning questions:

- Does RSI 55-70 outperform RSI above 75?
- Does RSI above 80 predict continuation or reversal?
- Does bearish RSI divergence predict failed breakouts?

### MACD

MACD can confirm momentum direction and momentum acceleration.

Features:

- macd_line
- macd_signal
- macd_histogram
- macd_histogram_slope
- macd_bullish_cross
- macd_bearish_cross

Initial use:

- score feature
- momentum confirmation

Learning questions:

- Does rising MACD histogram improve TP-before-SL rate?
- Are MACD crosses too late for intraday entries?
- Is MACD more useful for exits than entries?

## Tier 2 Indicators

These should be implemented after candidate and outcome tracking exists.

### Stochastic Oscillator

Useful for momentum exhaustion and short-term turns, but noisy.

Features:

- stoch_k
- stoch_d
- stoch_cross
- stoch_overbought
- stoch_oversold
- stoch_bearish_divergence
- stoch_bullish_divergence

Initial use:

- low-weight confirmation
- divergence warning
- exhaustion warning

Learning questions:

- Does stochastic divergence help?
- Is stochastic useful in trending setups?
- Should stochastic be ignored during strong momentum?

### Bollinger Bands

Useful for volatility expansion and squeeze breakouts.

Features:

- bb_upper
- bb_middle
- bb_lower
- bb_width
- bb_width_percentile
- price_near_upper_band
- band_expansion
- squeeze_breakout

Initial use:

- volatility expansion confirmation
- chase-risk warning

Learning questions:

- Do squeeze breakouts outperform normal breakouts?
- Does price above upper band predict continuation or reversal?
- What band width percentile is best?

### Support / Resistance

Very important, but harder to implement robustly.

Features:

- prior_day_high
- prior_day_low
- premarket_high
- premarket_low
- break_prior_day_high
- break_premarket_high
- near_round_number
- near_recent_swing_high
- near_recent_swing_low
- resistance_distance_pct
- support_distance_pct

Initial use:

- hard blocker
- score feature
- target placement

Learning questions:

- Do premarket-high breaks outperform opening-range-only breaks?
- Does prior-day-high breakout improve win rate?
- How close to resistance is too close?

### Candlestick / Wick Quality

Useful for avoiding fake breakouts.

Features:

- candle_body_pct
- upper_wick_pct
- lower_wick_pct
- close_near_high
- close_near_low
- wide_range_bar
- inside_bar_breakout
- rejection_wick

Initial use:

- score feature
- false-breakout guard

Learning questions:

- Does close_near_high improve follow-through?
- What upper_wick_pct predicts failure?
- Do wide-range bars create continuation or exhaustion?

## Market and Sector Confirmation

These are not classic indicators, but they are critical.

### Index Alignment

Features:

- spy_above_vwap
- qqq_above_vwap
- iwm_above_vwap
- spy_intraday_trend
- qqq_intraday_trend
- market_risk_on

Initial use:

- score feature
- hard blocker during weak market

Learning questions:

- Do long candidates fail more often when QQQ is below VWAP?
- Is SPY or QQQ more predictive for tech-heavy names?
- Should market alignment be a hard blocker or only score input?

### Sector Alignment

Features:

- sector_etf
- sector_etf_above_vwap
- sector_intraday_return
- stock_vs_sector_return
- sector_relative_strength

Initial use:

- score feature
- relative strength confirmation

Learning questions:

- Do sector-confirmed breakouts outperform isolated breakouts?
- Does stock relative strength vs sector predict continuation?
- Which sector ETF is most useful per ticker?

## Proposed Initial Score

Suggested explainable score out of 100:

- price action / structure: 25
- volume / liquidity: 20
- VWAP / trend alignment: 15
- relative strength / market alignment: 15
- technical momentum indicators: 10
- risk/reward quality: 10
- catalyst / time quality: 5

Technical momentum subscore:

- RSI confirmation: 3
- MACD confirmation: 3
- EMA alignment: 2
- stochastic confirmation: 1
- Bollinger expansion/squeeze: 1

Do not overweight indicators initially.

Price action, volume, VWAP, risk/reward, and market context should matter more.

## Hard Blockers

Reject long candidates if:

- spread too wide
- dollar volume too low
- price below VWAP unless reclaim setup
- distance above VWAP too extended
- gap too large
- opening-range extension too large
- risk/reward too poor
- stop distance too wide
- stop distance too tight
- market strongly against candidate
- sector strongly against candidate
- known halt risk
- same ticker already alerted today

## Candidate Feature Snapshot

Every intraday candidate should write a feature snapshot.

Suggested file:

- `data/intraday_candidates_YYYY-MM-DD.jsonl`

Important fields:

- date
- timestamp_et
- ticker
- scanner
- model_version
- watch_only
- score
- entry
- stop_loss
- take_profit
- risk_reward
- features
- blockers
- reason

## Outcome Snapshot

Suggested file:

- `data/intraday_outcomes_YYYY-MM-DD.jsonl`

Important fields:

- date
- ticker
- candidate timestamp
- evaluation timestamp
- horizon
- entry
- stop_loss
- take_profit
- price_at_horizon
- max favorable excursion
- max adverse excursion
- TP before SL
- SL before TP
- R multiple

## Build Order

Recommended implementation order:

1. Fix Telegram UX and active-pick loading
2. Add candidate snapshot file
3. Add outcome tracking file
4. Add VWAP
5. Add EMA
6. Add RSI
7. Add MACD
8. Add ATR
9. Add market/sector alignment
10. Add support/resistance
11. Add candlestick/wick quality
12. Add stochastic/Bollinger/divergence
13. Add daily intraday learning report
14. Add weekly recalibration report

## Final Rule

Every indicator must earn its place.

If a feature does not improve future outcomes, it should be down-weighted or removed.

The product should become smarter through evidence, not complexity.
