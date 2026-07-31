# Daily Picks No-Pick Report

Monitoring-only failure evidence. No official picks were generated.

- Date: **2026-07-31**
- Reason: **No official picks generated after scoring/filtering/gating. This is not safe to treat as a successful daily-picks run; check data-provider/rate-limit/no-candidate logs and use watch-only fallback if needed.**
- Primary no-pick cause: **NO_PICK_ALL_FINALISTS_HARD_BLOCKED**
- Summary: **No official picks were generated because all 2 finalist candidate(s) were hard-blocked.**
- Paper trading enabled: **false**
- Live trading enabled: **false**
- Official premarket pick: **false**

## Pipeline
- capped_count: **2**
- data_readiness_passed: **True**
- data_readiness_status: **ready**
- fetched_count: **588**
- filtered_count: **15**
- final_pick_count: **0**
- hard_blocked_count: **2**
- post_hard_block_pick_count: **0**
- pre_hard_block_pick_count: **2**
- scored_count: **347**
- scorer_workers: **4**
- universe_count: **597**

## Market Data Health
- stooq: attempts=**7**, successes=**0**, errors=**0**, rate_limited=**0**, unauthorized=**0**
- yfinance: attempts=**1537**, successes=**1315**, errors=**215**, rate_limited=**215**, unauthorized=**0**

## Secondary Causes
- YFINANCE_PROVIDER_DEGRADED

## Hard-Blocked Finalists
- CVX: **sl_too_tight** — SL too tight (1.3% < 1.5% for $192 stock)
- AAPL: **sl_too_tight** — SL too tight (1.5% < 1.5% for $333 stock)
