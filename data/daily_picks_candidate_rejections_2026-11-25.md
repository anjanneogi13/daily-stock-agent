# Daily Picks Candidate Rejection Report

Monitoring-only diagnostic artifact. Not official picks. Not buy instructions.

- Date: **2026-11-25**
- Primary no-pick cause: **NO_PICK_PREMARKET_SANITY_BLOCKED_ALL**
- Summary: **No official picks were generated because all finalists were blocked by the premarket sanity gate.**
- Paper trading enabled: **false**
- Live trading enabled: **false**

## Pre-Hard-Block Finalists
- SNDK: score=0.808, sector=Unknown, trade_type=swing, watch_only=False
- ORLY: score=0.691, sector=Unknown, trade_type=swing, entry=95.43, stop_loss=91.35, take_profit=100.54, risk_reward=1.25, watch_only=False
- VZ: score=0.691, sector=Unknown, trade_type=swing, entry=47.16, stop_loss=45.22, take_profit=49.59, risk_reward=1.25, watch_only=False
- HRL: score=0.688, sector=Unknown, trade_type=day, entry=23.27, stop_loss=22.9, take_profit=23.9, risk_reward=1.7, watch_only=False
- DLTR: score=0.683, sector=Unknown, trade_type=day, entry=154.65, stop_loss=150.84, take_profit=161.0, risk_reward=1.67, watch_only=False

## Hard-Blocked Finalists
- SNDK: **penny_stock** — missing entry price (broken upstream pick) (score=0.808, sector=Unknown, trade_type=swing, watch_only=False)
- HRL: **sl_too_tight** — SL too tight (1.6% < 2.5% for $23 stock) (score=0.688, sector=Unknown, trade_type=day, entry=23.27, stop_loss=22.9, take_profit=23.9, risk_reward=1.7, watch_only=False)
