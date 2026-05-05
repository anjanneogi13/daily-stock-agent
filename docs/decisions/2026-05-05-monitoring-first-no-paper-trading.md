# Monitoring-first launch — no paper trading yet

**Date:** 2026-05-05  
**Decision owner:** Founder + Copilot co-founder/tech lead  
**Status:** Accepted

## Decision

The Daily Stock Agent is approved for **monitoring-only launch**, not for real-money trading and not for paper-trading integration yet.

This means:

- **No real-money trading**.
- **No paper trading integration yet**.
- Run the agent side-by-side in monitoring mode for **2 weeks**.
- During those 2 weeks, continue fixing issues and completing the architecture roadmap.
- Then run **another 2 weeks** of validation after the architecture is stable.
- Only after both monitoring windows are complete can paper trading be considered.

## Paper trading eligibility gates

Paper trading is allowed only if all gates pass on post-floor data:

| Trade type | Required success rate | Extra requirement |
|---|---:|---|
| day trades | >60% | positive expectancy |
| swing trades | >66% | positive expectancy |
| monster / long holder picks | >90% | positive expectancy |

“Positive expectancy” means the average R-multiple / expected value must be above zero.
Win rate alone is not enough.

## Why the targets differ

Day trades must be sold within a short window, so they need a high hit rate and fast feedback.

Swing trades have more time for the thesis to work, so they can be judged over a longer holding period.

Monster / long holder picks must clear the highest bar because they are rare, high-conviction names intended to compound over longer windows. Examples in the founder thesis include semiconductor and hardware names such as Sandisk, Micron, Intel, Western Digital, MaxLinear, TSMC, and similar multi-fold-return candidates.

## Current status

Engineering is healthy enough for monitoring:

- CI is green.
- Full suite is fast and green: `1140 passed, 22 skipped`.
- Duplicate report issue creation is fixed via report issue upsert.
- Smell verdict persistence is wired.
- `full_repo_audit.py` is import-safe.

Trading performance is **not yet proven**. The system needs more clean post-floor closed picks before any enforcement or paper-trading decision.

## Non-negotiables

- The agent recommends and reports; it does not execute trades.
- Observe-mode gates remain disabled until readiness scripts say otherwise.
- No feature should bypass the data-quality floor.
- New intelligence features must not be promoted without tests and monitoring evidence.
