# Daily Picks No-Pick Report

Monitoring-only failure evidence. No official picks were generated.

- Date: **2026-06-16**
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
- fetched_count: **532**
- filtered_count: **5**
- final_pick_count: **0**
- hard_blocked_count: **2**
- post_hard_block_pick_count: **0**
- pre_hard_block_pick_count: **2**
- scored_count: **5**
- scorer_workers: **4**
- universe_count: **535**

## Market Data Health
- stooq: attempts=**3**, successes=**0**, errors=**0**, rate_limited=**0**, unauthorized=**0**
- yfinance: attempts=**3199**, successes=**3195**, errors=**1**, rate_limited=**0**, unauthorized=**0**

## Hard-Blocked Finalists
- NIXX: **penny_stock** — penny stock ($0.87 < $5.0)
- CNTN: **penny_stock** — penny stock ($3.21 < $5.0)
