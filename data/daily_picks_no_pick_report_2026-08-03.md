# Daily Picks No-Pick Report

Monitoring-only failure evidence. No official picks were generated.

- Date: **2026-08-03**
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
- filtered_count: **30**
- final_pick_count: **0**
- hard_blocked_count: **2**
- post_hard_block_pick_count: **0**
- pre_hard_block_pick_count: **2**
- scored_count: **293**
- scorer_workers: **4**
- universe_count: **532**

## Market Data Health
- yfinance: attempts=**1362**, successes=**1351**, errors=**11**, rate_limited=**11**, unauthorized=**0**

## Secondary Causes
- YFINANCE_PROVIDER_DEGRADED

## Hard-Blocked Finalists
- BEN: **sl_too_tight** — SL too tight (1.7% < 2.0% for $34 stock)
- IRD: **penny_stock** — penny stock ($3.71 < $5.0)
