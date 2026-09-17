# Daily Picks No-Pick Report

Monitoring-only failure evidence. No official picks were generated.

- Date: **2026-09-17**
- Reason: **No official picks generated after scoring/filtering/gating. This is not safe to treat as a successful daily-picks run; check data-provider/rate-limit/no-candidate logs and use watch-only fallback if needed.**
- Primary no-pick cause: **NO_PICK_UNKNOWN_POST_FILTER_GATING**
- Summary: **No official picks were generated after scoring/filtering/gating; inspect candidate diagnostics.**
- Paper trading enabled: **false**
- Live trading enabled: **false**
- Official premarket pick: **false**

## Pipeline
- capped_count: **15**
- data_readiness_passed: **True**
- data_readiness_status: **ready**
- fetched_count: **519**
- filtered_count: **15**
- final_pick_count: **0**
- hard_blocked_count: **3**
- post_hard_block_pick_count: **2**
- pre_hard_block_pick_count: **5**
- scored_count: **99**
- scorer_workers: **4**
- universe_count: **519**

## Market Data Health
- yfinance: attempts=**1142**, successes=**1142**, errors=**0**, rate_limited=**0**, unauthorized=**0**

## Hard-Blocked Finalists
- AES: **sl_too_tight** — SL too tight (0.6% < 2.5% for $15 stock)
- PFG: **sl_too_tight** — SL too tight (1.4% < 1.5% for $117 stock)
- TMO: **sl_too_tight** — SL too tight (1.4% < 1.5% for $648 stock)
