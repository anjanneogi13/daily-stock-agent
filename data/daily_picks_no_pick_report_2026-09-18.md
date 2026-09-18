# Daily Picks No-Pick Report

Monitoring-only failure evidence. No official picks were generated.

- Date: **2026-09-18**
- Reason: **No official picks generated after scoring/filtering/gating. This is not safe to treat as a successful daily-picks run; check data-provider/rate-limit/no-candidate logs and use watch-only fallback if needed.**
- Primary no-pick cause: **NO_PICK_UNKNOWN_POST_FILTER_GATING**
- Summary: **No official picks were generated after scoring/filtering/gating; inspect candidate diagnostics.**
- Paper trading enabled: **false**
- Live trading enabled: **false**
- Official premarket pick: **false**

## Pipeline
- capped_count: **30**
- data_readiness_passed: **True**
- data_readiness_status: **ready**
- fetched_count: **519**
- filtered_count: **30**
- final_pick_count: **0**
- hard_blocked_count: **4**
- post_hard_block_pick_count: **6**
- pre_hard_block_pick_count: **10**
- scored_count: **114**
- scorer_workers: **4**
- universe_count: **519**

## Market Data Health
- yfinance: attempts=**1157**, successes=**1157**, errors=**0**, rate_limited=**0**, unauthorized=**0**

## Hard-Blocked Finalists
- BRK-B: **sl_too_tight** — SL too tight (0.7% < 1.5% for $509 stock)
- AES: **sl_too_tight** — SL too tight (0.7% < 2.5% for $15 stock)
- TMO: **sl_too_tight** — SL too tight (1.4% < 1.5% for $658 stock)
- EG: **sl_too_tight** — SL too tight (1.1% < 1.5% for $380 stock)
