# Product Architecture Roadmap

**Last updated:** 2026-05-09  
**Status:** canonical product vision / not fully implemented  
**Safety posture:** observe-only until strategy, risk, execution, and reporting gates pass

---

## Purpose

Daily Stock Agent is intended to become a multi-strategy stock intelligence system.

The product should generate, analyze, learn from, and improve stock-picking strategies across multiple time horizons while maintaining strict safety, auditability, validation gates, and controlled promotion from observe-only to execution modes.

The system is not complete yet. Current work has built an important reliability and reporting foundation, but major product capabilities remain to be designed, validated, and promoted safely.

---

## Product North Star

Daily Stock Agent should eventually support:

- premarket official daily stock picks,
- post-open daily stock opportunities,
- intraday stock picks,
- monster hunter opportunities,
- consistent compounder opportunities,
- long-term opportunity picks,
- daily performance intelligence,
- weekly performance intelligence,
- monthly performance intelligence,
- quarterly performance intelligence,
- yearly performance intelligence,
- execution reports,
- x-ray reports,
- missed-opportunity analysis,
- no-pick intelligence,
- market regime awareness,
- chart and technical analysis,
- historical backtesting,
- walk-forward validation,
- controlled learning and calibration loops,
- paper trading only after explicit gates pass,
- live trading only after explicit gates pass.

---

## Current Safety Boundary

Until explicitly promoted:

- observe-only remains the default,
- no official theme-aware scoring effect,
- no unapproved score boosts,
- no automatic self-modification of production logic,
- no paper trading unless explicitly enabled,
- no live trading unless explicitly enabled,
- no buy instructions from observe-only reports,
- all learning must be documented, tested, and committed through controlled changes.

---

## Product Lanes

### 1. Premarket Official Daily Pick

Goal:

Produce an official stock pick before market open when data readiness and strategy gates pass.

Expected capabilities:

- candidate universe construction,
- market-data readiness checks,
- provider failure detection,
- catalyst evidence,
- news evidence,
- fundamental evidence,
- technical evidence,
- risk/reward setup,
- entry,
- stop-loss,
- take-profit,
- no-pick output when conditions are not safe,
- pick rationale,
- rejection diagnostics,
- outcome review.

Important principle:

A no-pick day can be correct if data, provider state, market regime, or opportunity quality is poor.

---

### 2. Post-Open Daily Opportunity Lane

Goal:

Identify opportunities that become valid only after the market opens.

Examples:

- late-breaking news,
- post-open continuation setups,
- earnings reactions,
- catalyst reactions,
- morning gap confirmation,
- midday continuation candidates,
- late-day continuation candidates.

This lane should be separate from the premarket official pick lane and should not blindly override the premarket pick.

---

### 3. Intraday Pick Lane

Goal:

Identify intraday opportunities during market hours.

Current and future sub-lanes:

- opening-range observations,
- opening-range breakout candidates,
- intraday momentum observations,
- watch-only intraday candidates,
- breakout continuation,
- VWAP reclaim,
- volume-confirmed moves,
- false-breakout detection.

Learning areas:

- time-of-day behavior,
- opening-range quality,
- volume confirmation,
- VWAP behavior,
- market regime effect,
- slippage sensitivity,
- false-breakout conditions,
- halt and liquidity risk.

---

### 4. Monster Hunter Lane

Goal:

Find short-term explosive opportunities.

Possible evidence:

- unusual volume,
- catalyst strength,
- float and short-interest dynamics,
- volatility expansion,
- news urgency,
- technical breakout,
- social/news momentum,
- institutional confirmation,
- sector confirmation.

This lane should have separate scoring and risk controls from daily picks.

---

### 5. Consistent Compounder Lane

Goal:

Find durable quality-growth opportunities.

Possible evidence:

- consistent revenue growth,
- consistent earnings growth,
- strong margins,
- durable sector tailwind,
- lower volatility,
- relative strength,
- quality balance sheet,
- long-term trend confirmation,
- management quality proxies.

This lane should not use the same logic as monster or intraday picks.

---

### 6. Long-Term Opportunity Lane

Goal:

Identify multi-week, multi-month, or longer-term opportunities.

Possible evidence:

- valuation,
- fundamentals,
- sector rotation,
- institutional accumulation,
- earnings trend,
- macro tailwind,
- technical base formation,
- relative strength.

This lane requires longer-horizon backtests and different risk/reward logic.

---

## Reporting and Learning Loops

### Daily Reports

The system should produce daily intelligence including:

- official daily pick report,
- post-open opportunity report,
- intraday observations report,
- no-pick report,
- missed-opportunity report,
- provider/data readiness report,
- artifact completeness report,
- candidate lifecycle report,
- theme discovery report,
- theme-to-pick bridge,
- daily intelligence brief.

### Performance Reports

The system should produce:

- daily performance report,
- weekly performance report,
- monthly performance report,
- quarterly performance report,
- yearly performance report.

### Execution and X-Ray Reports

The system should eventually include:

- execution quality report,
- slippage report,
- fill quality report,
- stop-loss behavior report,
- take-profit behavior report,
- trailing-stop behavior report,
- pick x-ray report,
- strategy x-ray report,
- feature contribution report,
- rejection x-ray report.

### Learning Principle

The agent should not silently modify production logic.

Correct learning flow:

1. collect outcome evidence,
2. generate lessons,
3. record calibration notes,
4. propose code or config changes,
5. backtest or validate changes,
6. run tests,
7. commit documented changes,
8. promote only through explicit gates.

---

## Missed-Opportunity Intelligence

The system must review not only what it picked, but also what it missed.

Questions to answer:

- Which high-performing stocks were missed?
- Were they in watch-only lanes?
- Were they rejected by filters?
- Were they absent from the candidate universe?
- Did provider or data failure hide them?
- Did scoring under-rank them?
- Did risk controls correctly reject them?
- Should the strategy change or was the miss acceptable?

This is a core learning loop.

---

## No-Pick Intelligence

No-pick days require analysis.

Questions to answer:

- Was no-pick correct?
- Was the pipeline incomplete?
- Was data stale or missing?
- Did provider failure cause no-pick?
- Were filters too strict?
- Did the market regime justify no-pick?
- Did a missed opportunity emerge afterward?

No-pick should be treated as a decision with evidence, not as an absence of output.

---

## Market Regime Awareness

Strategies should be evaluated by regime.

Possible regimes:

- bull trend,
- bear trend,
- sideways/chop,
- high volatility,
- low volatility,
- risk-on,
- risk-off,
- sector rotation,
- earnings-heavy period,
- macro/Fed event risk.

Each strategy should have separate performance statistics by regime.

---

## Risk Management and Portfolio Construction

The product needs explicit risk rules before any execution.

Required areas:

- position sizing,
- max risk per trade,
- max daily loss,
- max weekly loss,
- max open positions,
- sector exposure limits,
- correlation limits,
- strategy allocation,
- stop-loss rules,
- take-profit rules,
- trailing-stop rules,
- capital allocation by lane,
- volatility-adjusted sizing.

A good stock pick can still be a bad trade if risk management is poor.

---

## Execution Promotion Gates

The product should progress through controlled stages:

observe-only -> paper trading -> limited live trading -> scaled live trading

Promotion should require evidence such as:

- sufficient sample size,
- positive expectancy,
- acceptable drawdown,
- stable win rate,
- slippage tolerance,
- data readiness stability,
- provider reliability,
- complete reporting,
- reproducible backtests,
- walk-forward validation,
- human approval.

---

## Historical Backtesting and Walk-Forward Validation

The agent should apply strategy logic to historical time spans.

Required validation types:

- historical backtest,
- walk-forward validation,
- out-of-sample testing,
- regime-specific testing,
- benchmark comparison versus SPY/QQQ,
- slippage and transaction-cost modeling,
- overfitting checks.

No strategy should be promoted to production scoring or execution solely from anecdotal outcomes.

---

## Chart and Technical Analysis

The agent should eventually read charts quantitatively and possibly visually.

Initial quantitative chart evidence:

- trend,
- moving averages,
- support/resistance,
- VWAP,
- volume,
- RSI,
- MACD,
- gap behavior,
- breakout/base patterns,
- relative strength,
- new highs,
- failed breakouts.

Later possible visual chart reading:

- chart-image pattern recognition,
- multi-timeframe chart summaries,
- annotated chart reports.

All chart-derived signals must be validated before promotion.

---

## Book and Research Learning

The agent may study trading and investing concepts, but should not blindly encode them.

Correct flow:

1. extract a principle,
2. convert it into a testable hypothesis,
3. backtest or validate it,
4. compare against baseline,
5. document results,
6. promote only if evidence supports it.

Example:

Principle:

Volume confirms breakouts.

Hypothesis:

Opening-range breakouts with volume ratio above threshold X outperform those below X.

Validation:

Backtest by date, regime, sector, and volatility condition.

---

## Strategy Separation

The system should avoid mixing all picks into one scoring model.

Separate strategy engines should exist for:

- premarket daily picks,
- post-open opportunities,
- intraday/opening-range picks,
- intraday momentum,
- monster hunter,
- consistent compounders,
- long-term opportunities,
- theme discovery,
- no-pick/missed-opportunity intelligence.

A meta-layer can later coordinate which lanes are active and safe.

---

## Explainability and Audit Trail

Every pick or no-pick should answer:

- Why this ticker?
- Why today?
- What evidence supports it?
- What evidence argues against it?
- What data was missing?
- What would invalidate the thesis?
- What rule selected or rejected it?
- What strategy version selected it?
- What config version selected it?
- What provider status existed at selection time?

---

## Versioning and Experiment Tracking

The system should track:

- scoring version,
- config version,
- strategy version,
- prompt version where relevant,
- feature version,
- backtest result,
- promotion date,
- rollback path,
- experiment notes,
- known limitations.

Learning must be auditable.

---

## User Experience and Alerts

The final product should provide clear outputs:

- Telegram alerts,
- dashboard,
- daily founder/operator brief,
- execution-ready cards,
- confidence labels,
- risk labels,
- no-pick explanation,
- missed-opportunity explanation,
- watchlist updates,
- performance summaries.

---

## Already Built Foundations

Recent completed foundations include:

- daily data readiness report,
- candidate lifecycle ledger,
- artifact completeness report,
- legacy sector boost safety guard,
- daily intelligence brief,
- opening-range bar retention repair,
- provider failure taxonomy,
- observe-only theme market evidence,
- downstream propagation of theme market evidence,
- timezone-aware UTC cleanup,
- full test suite green at 1561 passed, 30 skipped.

These are foundations, not the finished product.

---

## Major Remaining Work

High-level remaining work:

1. define strategy-specific product specs,
2. build and validate premarket official pick engine,
3. build and validate post-open opportunity engine,
4. build and validate intraday pick engine,
5. build and validate monster hunter lane,
6. build and validate compounder lane,
7. build and validate long-term opportunity lane,
8. implement missed-opportunity intelligence,
9. implement no-pick intelligence upgrades,
10. add market regime classification,
11. add portfolio/risk management,
12. add historical backtesting infrastructure,
13. add walk-forward validation,
14. add chart/technical-analysis engine,
15. add execution simulation,
16. define paper-trading promotion gates,
17. define live-trading promotion gates,
18. improve dashboard/alert UX,
19. maintain auditability and versioning,
20. keep observe-only safety until promotion gates pass.

---

## Canonical Architecture Summary

Daily Stock Agent is a multi-strategy stock intelligence system.

It generates premarket, post-open, intraday, monster, compounder, and long-term opportunity candidates.

It collects evidence from market data, news, fundamentals, technicals, themes, charts, historical outcomes, and provider health.

It produces daily, weekly, monthly, quarterly, yearly, execution, x-ray, no-pick, and missed-opportunity reports.

It learns from outcomes through controlled calibration loops, backtests, walk-forward validation, and documented experiments.

It remains observe-only until each strategy passes readiness, performance, risk, reporting, and safety gates.
