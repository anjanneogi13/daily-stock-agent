# Daily Picks No-Pick Report

Monitoring-only failure evidence. No official picks were generated.

- Date: **2026-08-18**
- Reason: **No official picks generated after scoring/filtering/gating. This is not safe to treat as a successful daily-picks run; check data-provider/rate-limit/no-candidate logs and use watch-only fallback if needed.**
- Primary no-pick cause: **NO_PICK_ALL_FINALISTS_HARD_BLOCKED**
- Summary: **No official picks were generated because all 1 finalist candidate(s) were hard-blocked.**
- Paper trading enabled: **false**
- Live trading enabled: **false**
- Official premarket pick: **false**

## Pipeline
- capped_count: **1**
- data_readiness_passed: **True**
- data_readiness_status: **ready**
- fetched_count: **612**
- filtered_count: **1**
- final_pick_count: **0**
- hard_blocked_count: **1**
- post_hard_block_pick_count: **0**
- pre_hard_block_pick_count: **1**
- scored_count: **1**
- scorer_workers: **4**
- universe_count: **618**

## Market Data Health
- stooq: attempts=**5**, successes=**0**, errors=**0**, rate_limited=**0**, unauthorized=**0**
- yfinance: attempts=**1235**, successes=**1230**, errors=**0**, rate_limited=**0**, unauthorized=**0**

## Hard-Blocked Finalists
- NTWO: **sl_too_tight** — SL too tight (0.1% < 2.5% for $11 stock)
