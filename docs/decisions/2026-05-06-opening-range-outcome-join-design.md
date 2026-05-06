# Opening-Range Outcome Join / Backtest Design

**Date:** 2026-05-06
**Status:** read-only design + skeleton implemented
**Mode:** monitoring-only
**Paper trading:** disabled

## Purpose

Opening-range scanner observations are watch-only evidence. Future sessions need a safe way to join observations to later intraday price action without promoting them into trades.

This design separates observation generation, observation review, outcome evaluation, and paper-trading activation.

No script may promote observations to paper trades.

## Inputs

Observation artifact:

- `data/opening_range_observations_YYYY-MM-DD.jsonl`

Optional future bar artifact layouts:

- `data/opening_range_bars/YYYY-MM-DD/TICKER.jsonl`
- `data/opening_range_bars/TICKER_YYYY-MM-DD.jsonl`

Expected bar row fields:

- `ts`
- `high`
- `low`
- `close`

## Outcome rules

1. Use `entry_observe`, `stop_loss_observe`, and `take_profit_observe`.
2. Evaluate only bars after the observation timestamp.
3. Default max hold window: 240 minutes.
4. If low touches stop loss first: `sl_hit`.
5. If high touches take profit first: `tp_hit`.
6. If the same bar touches both stop and take profit, use conservative assumption: `sl_hit`.
7. If neither target is touched before timeout: `timeout`.
8. If bar data is unavailable: `missing_bar_data`.

## Safety rules

The tool must remain read-only.

It must not:

- write to `data/picks_log.csv`,
- write to `data/signal_journal.jsonl`,
- write to `data/trades.csv`,
- create official picks,
- create paper trades,
- alter workflow environment variables.

It must always report:

- `mode=monitoring_only`
- `paper_trading_enabled=false`
- `ready_for_paper_trading=false`

## Implemented script

Run:

- `python scripts/backtest_opening_range_observations.py`
- `python scripts/backtest_opening_range_observations.py --json`

If matching bar files do not exist, it reports `missing_bar_data`.

## Promotion policy

Even if early backtest results look good, do not enable paper trading until:

1. Monitoring readiness dashboards pass.
2. Minimum sample size is reached.
3. Results are reviewed for data quality and survivorship bias.
4. Telegram wording remains safe.
5. Founder explicitly approves paper trading.
6. `docs/decisions/2026-05-06-paper-trading-activation-checklist.md` is followed.
