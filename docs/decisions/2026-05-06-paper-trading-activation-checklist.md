# Paper Trading Activation Checklist

**Date:** 2026-05-06  
**Status:** NOT ENABLED  
**Current mode:** monitoring-only

Paper trading must remain disabled until the monitoring architecture proves it has real edge and the execution path is safe.

---

## Current rule

Do not enable paper trading yet.

The following must remain false / unset in production workflows:

- `TRADING_MODE=paper`
- `SMELL_ENFORCE=true`
- `BRAIN_ENFORCE_EV=true`
- `AUTO_PAUSE_ENABLED=true`

The current code intentionally requires `TRADING_MODE=paper` before legacy local paper logging can write paper-trade artifacts.

---

## What must be true before enabling paper trading

Paper trading can be considered only when all of these are true:

1. `python scripts/monitoring_readiness.py` shows readiness for the relevant lane:
   - day trades: `>60%` win rate and positive average R,
   - swing trades: `>66%` win rate and positive average R,
   - monster/long-holder picks: `>90%` win rate and positive average R.
2. Each lane has at least the required minimum sample size:
   - default `n_closed >= 30` per lane.
3. `python scripts/check_enforcement_readiness.py` remains appropriately blocked or explicitly ready based on data:
   - no calendar-based flipping,
   - only data-backed flipping.
4. `python scripts/audit_journal_consistency.py --strict` passes.
5. Full test suite passes.
6. Tracked-data isolation remains clean:
   - tests must not mutate `data/picks_log.csv`,
   - tests must not mutate `data/signal_journal.jsonl`,
   - tests must not mutate `data/learning_journal.jsonl`.
7. Intraday scanner candidates are still marked `WATCH ONLY` until their lane has enough monitored evidence.
8. Telegram wording must distinguish:
   - official premarket picks,
   - watch-only intraday observations,
   - paper-trade candidates,
   - actual future live-trade candidates.
9. Paper-trade logging must be schema-safe and auditable.
10. A rollback path must exist:
    - unset `TRADING_MODE`,
    - disable all enforcement env vars,
    - leave monitoring-only reports running.

---

## What to enable when ready

When readiness gates pass and the founder explicitly approves paper trading, enable paper trading in a small PR/commit that does only this:

1. Set production workflow environment:
   - `TRADING_MODE=paper`
2. Keep these off unless their own readiness script says ready:
   - `SMELL_ENFORCE`
   - `BRAIN_ENFORCE_EV`
   - `AUTO_PAUSE_ENABLED`
3. Add or verify tests that prove:
   - paper trades are written only when `TRADING_MODE=paper`,
   - no paper trades are written in monitoring-only mode,
   - watch-only ideas are never logged as paper trades,
   - intraday observations are never shown as buy instructions unless promoted by policy.
4. Run:
   - `python3 -m pytest tests/ -q --tb=short --disable-warnings`
   - `python scripts/audit_journal_consistency.py --strict`
   - `python scripts/check_enforcement_readiness.py`
   - `python scripts/monitoring_readiness.py`
   - `git diff --check`

---

## What must be fixed or verified during paper-trading integration

Before `TRADING_MODE=paper` is enabled, verify:

- `src/paper_trader.py` has tests for:
  - schema/header,
  - append behavior,
  - missing field behavior,
  - no write unless explicitly called by paper mode.
- `main.py` never paper-logs:
  - watch-only picks,
  - stale/unverified price picks,
  - intraday-news swing candidates marked watch-only,
  - opening-range scanner observations.
- Paper-trade artifacts are committed by workflow only if intended.
- Telegram does not imply real money execution.
- Paper trades can be reconciled against `data/picks_log.csv` and `data/signal_journal.jsonl` without creating confusing duplicate sources of truth.

---

## Current opening-range scanner status

The opening-range scanner is monitoring-only.

Workflow cadence includes 09:35 / 09:45 / 10:00 ET monitoring checks.

Review command:

- `python scripts/review_opening_range_observations.py`
- `python scripts/backtest_opening_range_observations.py`

It may produce:

- `watch_only=True`
- `mode=monitoring_only`
- `scanner=opening_range`

It may persist observations to:

- `data/opening_range_observations_YYYY-MM-DD.jsonl`

It must not produce:

- real orders,
- paper trades,
- official buy instructions.

Promotion from observation to paper candidate requires a later evidence-backed policy change.


Related outcome-join design:

- `docs/decisions/2026-05-06-opening-range-outcome-join-design.md`
