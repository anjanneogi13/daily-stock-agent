# Daily Picks No-Pick Report

Monitoring-only failure evidence. No official picks were generated.

- Date: **2026-07-10**
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
- fetched_count: **567**
- filtered_count: **30**
- final_pick_count: **0**
- hard_blocked_count: **2**
- post_hard_block_pick_count: **0**
- pre_hard_block_pick_count: **2**
- scored_count: **348**
- scorer_workers: **4**
- universe_count: **570**

## Market Data Health
- stooq: attempts=**8**, successes=**0**, errors=**0**, rate_limited=**0**, unauthorized=**0**
- yfinance: attempts=**5953**, successes=**4777**, errors=**1168**, rate_limited=**1167**, unauthorized=**0**

## Secondary Causes
- YFINANCE_PROVIDER_DEGRADED

## Hard-Blocked Finalists
- SNY: **sl_too_tight** — SL too tight (1.4% < 2.0% for $44 stock)
- PERF: **penny_stock** — penny stock ($1.74 < $5.0)
