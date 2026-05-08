# ADR-001: Probability-Based Decisions Over Rule-Based Thresholds

**Status:** Accepted
**Date:** 2026-05-02
**Decided by:** Anjan Neogi
**Discussion:** Saturday afternoon co-founder session

## Context

The agent currently uses arbitrary thresholds for all price decisions:
- Stop Loss: `1.5 × ATR` (or 3% minimum)
- Take Profit: `3.0 × ATR`
- RSI overbought/oversold: 70/30
- Volume threshold: 1.2× average

These are industry-standard but ARBITRARY. Different stocks have different volatility profiles, regime behavior, and noise bands. A 3% SL on NVDA is too wide; on a high-vol small cap it's too tight.

## Decision

ALL price decisions will be EMPIRICALLY DERIVED from per-stock historical probability distributions, conditioned on current market regime.

Specifically:
- **SL** = price level where P(reversal | level hit) > 70%
- **TP1** = price level where P(reach within 5 days) > 50%
- **TP2** = price level where P(reach within 10 days) > 25%
- **Buy zone** = price range where P(rally from here) > 55%
- **Sell signal** = price level where P(further upside) < 25%
- **Pattern enable** = hypothesis test p-value < 0.05

## Consequences

### Positive
- Levels adapt to each stock's actual behavior
- Levels adapt to market regime
- System has empirical justification for every decision
- Enables proper hypothesis testing
- Foundation for self-learning (Layer 5: confidence tracking)

### Negative
- Requires 6-month minimum historical data per stock
- Requires regime classification first
- Initial implementation: 3-week build (4 phases)
- Risk of overfitting if discipline not maintained
- More complex debugging

## Anti-Overfitting Safeguards (Mandatory)

1. Train/test split: ALWAYS hold 20% of history out
2. Walk-forward validation: NEVER look ahead
3. 95% confidence intervals for go/no-go
4. Pre-register hypotheses BEFORE testing
5. Bonferroni correction for multiple tests

## Alternatives Considered

1. **Keep ATR-based with better tuning** — Rejected: still arbitrary, doesn't adapt per stock
2. **ML black-box model** — Rejected: needs 10K+ trades, not interpretable, regulatory risk
3. **LLM vision pattern recognition** — Rejected: tech immature in 2026

## Implementation

See `docs/reference/PROBABILITY_ENGINE_DESIGN.md` for full 5-layer architecture and 4-phase rollout plan.

## References

- Original chat session: May 2, 2026 PM
- Related: `docs/reference/PROBABILITY_ENGINE_DESIGN.md`