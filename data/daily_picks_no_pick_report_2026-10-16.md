# Daily Picks No-Pick Report

Monitoring-only failure evidence. No official picks were generated.

- Date: **2026-10-16**
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
- fetched_count: **518**
- filtered_count: **30**
- final_pick_count: **0**
- hard_blocked_count: **3**
- post_hard_block_pick_count: **7**
- pre_hard_block_pick_count: **10**
- scored_count: **330**
- scorer_workers: **4**
- universe_count: **519**

## Market Data Health
- yfinance: attempts=**1372**, successes=**1283**, errors=**89**, rate_limited=**89**, unauthorized=**0**

## Secondary Causes
- YFINANCE_PROVIDER_DEGRADED

## Hard-Blocked Finalists
- BBY: **sl_too_tight** — SL too tight (1.7% < 2.0% for $94 stock)
- GILD: **sl_too_tight** — SL too tight (1.5% < 1.5% for $157 stock)
- PM: **sl_too_tight** — SL too tight (1.5% < 1.5% for $200 stock)
