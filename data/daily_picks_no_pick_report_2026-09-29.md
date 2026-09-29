# Daily Picks No-Pick Report

Monitoring-only failure evidence. No official picks were generated.

- Date: **2026-09-29**
- Reason: **No official picks generated after scoring/filtering/gating. This is not safe to treat as a successful daily-picks run; check data-provider/rate-limit/no-candidate logs and use watch-only fallback if needed.**
- Primary no-pick cause: **NO_PICK_UNKNOWN_POST_FILTER_GATING**
- Summary: **No official picks were generated after scoring/filtering/gating; inspect candidate diagnostics.**
- Paper trading enabled: **false**
- Live trading enabled: **false**
- Official premarket pick: **false**

## Pipeline
- capped_count: **26**
- data_readiness_passed: **True**
- data_readiness_status: **ready**
- fetched_count: **519**
- filtered_count: **30**
- final_pick_count: **0**
- hard_blocked_count: **2**
- post_hard_block_pick_count: **8**
- pre_hard_block_pick_count: **10**
- scored_count: **172**
- scorer_workers: **4**
- universe_count: **519**

## Market Data Health
- yfinance: attempts=**1215**, successes=**1215**, errors=**0**, rate_limited=**0**, unauthorized=**0**

## Hard-Blocked Finalists
- NVDA: **sl_too_tight** — SL too tight (1.4% < 1.5% for $229 stock)
- AES: **sl_too_tight** — SL too tight (0.5% < 2.5% for $15 stock)
