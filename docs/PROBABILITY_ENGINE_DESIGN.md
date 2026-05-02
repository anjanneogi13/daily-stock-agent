# 🎯 Statistical Probability Engine — Architecture Design

> **Founder vision:** Every price decision (SL, TP, buy, sell, trigger) must be PROBABILITY-BASED, not rule-based. The agent must know its own probability of working.
> **Status:** Design locked May 2, 2026. Implementation phased over 3-4 weeks.

## 🎯 NORTH STAR

Replace ALL arbitrary thresholds (1.5×ATR, 3% SL, RSI 30, etc.) with EMPIRICALLY-DERIVED probability-based decisions:

- **Stop Loss** = price where P(noise vs reversal) crosses 70%
- **Take Profit** = price where P(reach within N days) > target%
- **Buy Price** = price where P(rally from here) > 55%
- **Sell Price** = price where P(further upside) < 25%
- **Trigger Price** = level where P(continued momentum) > 65%
- **Pattern Validity** = hypothesis test, p < 0.05 to enable

## 🏗️ FIVE-LAYER ARCHITECTURE

### Layer 1: Historical Data Foundation
Per-stock statistical profile:
- Return distributions (1d, 5d, 10d, 20d)
- Volatility (rolling 20/60/180 day windows)
- ATR at multiple windows
- Drawdown profiles
- Bounce-back rates from various drawdown levels
- Volume patterns
- Storage: `data/stock_stats/{TICKER}.json`

### Layer 2: Regime-Conditional Statistics
For each (stock, regime) pair compute:
- Typical 1d/5d/10d return distributions
- Noise band (where most returns fall)
- MFE (max favorable excursion) distribution
- MAE (max adverse excursion) distribution
- Historical win rate in this regime
- Storage: `data/stock_stats/{TICKER}_regime.json`

### Layer 3: Probabilistic Price Level Calculator
Given: stock + current price + market state
Outputs:
- SL = price where P(reversal | hit) > 70%
- TP1 = price where P(reach within 5 days) > 50%
- TP2 = price where P(reach within 10 days) > 25%
- Buy zone where P(rally) > 55%
- Trigger above which P(momentum) > 65%

### Layer 4: Hypothesis Testing Engine
For every pattern/strategy:
- H0: pattern has no edge vs random
- H1: pattern beats baseline by X%
- Bootstrap or t-test to compute p-value
- ENABLE if p < 0.05, DISABLE if p > 0.20, MONITOR otherwise
- Storage: `data/pattern_stats.json` (weekly update)

### Layer 5: Algorithm Self-Awareness
System-level confidence tracker:
- Rolling 30-day win rate with 95% CI
- Average R-multiple with CI
- Sharpe ratio with CI
- Vs SPY benchmark
- Per-strategy breakdown (day/swing/multi)
- Telegram weekly: "Confidence 62% (CI 55-69%), trend stable"
- Auto-pause if confidence drops below threshold

## 📦 IMPLEMENTATION PHASES

### Phase 1 (May 2-3 weekend) — Data Foundation
Build `src/stock_stats.py` + `scripts/build_stock_stats.py`
Generate stats for top 50 stocks
Effort: 4-6 hours

### Phase 2 (May 9-10 weekend) — Regime-Aware Levels
Replace ATR-based SL/TP with empirical
Per-stock, per-regime calibration
Effort: 4-6 hours

### Phase 3 (May 16-17 weekend) — Hypothesis Testing
Pattern stats accumulator
Bootstrap p-value calculator
Auto-enable/disable patterns
Effort: 6-8 hours

### Phase 4 (May 23-24 weekend) — Self-Awareness
Confidence tracker
Telegram weekly confidence report
Auto-pause if confidence drops
Effort: 4-6 hours

## ⚠️ ANTI-OVERFITTING DISCIPLINE (NON-NEGOTIABLE)

1. **Train/test split:** NEVER fit on test data
2. **Walk-forward validation:** NEVER look ahead
3. **Conservative CIs:** 95% minimum for go/no-go decisions
4. **Multiple regime testing:** Not just bull markets
5. **Pre-registration:** Decide hypotheses BEFORE testing
6. **Multiple testing correction:** Bonferroni when running many tests
7. **Out-of-sample-only deployment:** Live only after holdout passes

## 🚫 EXPLICITLY NOT BUILDING

- LLM vision chart reading (tech immature, 2026)
- Deep learning models (need 10K+ trades minimum)
- High-frequency strategies (latency unrealistic for retail)
- Options pricing models (separate complex domain)
- Tick-level microstructure (no data access)

## 🔄 INTEGRATION WITH EXISTING SYSTEM

Current rule-based components to be REPLACED:
- `src/risk.py` ATR-based SL/TP → empirical levels
- `src/adaptive_tp.py` rule-based → probability-based
- `src/trailing_stop.py` 3% rule → adaptive empirical
- `src/regime.py` → keep, but enhance with probabilistic confidence

Current components to KEEP:
- `src/data_fetcher.py` (data source)
- `src/indicators.py` (calculate, but don't decide on)
- `src/news_engine.py` (catalyst layer separate from probability)
- `src/parallel_scorer.py` (scoring engine)

## 📊 SUCCESS METRICS (How We Know It Works)

After Phase 4 deployed:
- Agent shows 95% CI on every prediction
- Win rate within predicted CI 95% of time (calibration)
- Sharpe ratio CI lower bound > 0
- Per-stock SL respect rate matches predicted P(noise)
- Pattern enable/disable decisions backtested
- Self-awareness identifies regime changes within 5 days

## 🤝 WORKING AGREEMENT

This document is the FOUNDATION. Every PR touching probability/statistics must reference back to this design. If you (founder) want to change the design, edit this doc FIRST, then write code. No "I'll just try this real quick" — that's how overfitting happens.