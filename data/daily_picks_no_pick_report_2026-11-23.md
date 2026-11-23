# Daily Picks No-Pick Report

Monitoring-only failure evidence. No official picks were generated.

- Date: **2026-11-23**
- Reason: **No official picks generated after scoring/filtering/gating. This is not safe to treat as a successful daily-picks run; check data-provider/rate-limit/no-candidate logs and use watch-only fallback if needed.**
- Primary no-pick cause: **NO_PICK_UNKNOWN_POST_FILTER_GATING**
- Summary: **No official picks were generated after scoring/filtering/gating; inspect candidate diagnostics.**
- Paper trading enabled: **false**
- Live trading enabled: **false**
- Official premarket pick: **false**

## Pipeline
- capped_count: **3**
- data_readiness_passed: **True**
- data_readiness_status: **ready**
- fetched_count: **519**
- filtered_count: **3**
- final_pick_count: **0**
- hard_blocked_count: **2**
- post_hard_block_pick_count: **1**
- pre_hard_block_pick_count: **3**
- scored_count: **7**
- scorer_workers: **4**
- universe_count: **519**

## Market Data Health
- yfinance: attempts=**4200**, successes=**4200**, errors=**0**, rate_limited=**0**, unauthorized=**0**

## Hard-Blocked Finalists
- WRB: **sl_too_tight** — SL too tight (1.3% < 2.0% for $78 stock)
- COST: **catastrophic_news** — catastrophic news (BANKRUPTCY_RISK: Middle-Aged Americans Are Filing for Bankruptcy at the Highest Rate Since 2017 — Debt, Inflation and)
