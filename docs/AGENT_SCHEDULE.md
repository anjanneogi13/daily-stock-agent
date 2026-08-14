# Agent Schedule

This document is a human-readable schedule overview.

The implementation source of truth is always:

    .github/workflows/

If this document conflicts with workflow YAML, trust the workflow YAML and update this document.

## Current Operating Mode

Daily Stock Agent currently runs in:

- monitoring-only mode
- no paper trading
- no live trading
- official picks separated from watch-only ideas
- research-only lanes separated from official statistics

## Timezone Rule

Most trading logic is guarded in America/New_York time.

Some cron expressions are written in UTC because GitHub Actions schedules use UTC. Workflow guards convert to ET and act inside explicit ET windows.

GitHub cron is best-effort and frequently 30-90 minutes late. Premarket-critical workflows therefore schedule earlier nominal slots than their target ET times (delay compensation), and their guards use ET time windows plus ledger dedup instead of exact-hour "wrong DST slot" checks. Exact-hour checks previously caused delayed correct-slot runs to be silently skipped (2026-08-06 to 2026-08-13: six straight NO_PICK_WINDOW_MISSED days with no watchdog rescue or alert).

## External Scheduler Redundancy (cron-job.org)

GitHub schedules alone cannot guarantee an in-window premarket run. cron-job.org jobs POST `workflow_dispatch` for `daily-picks.yml` (08:05, 08:35, 09:05, 09:15 ET) and `late_watch_only.yml` (09:25, 09:40 ET) using a GitHub PAT in the Authorization header.

Health check: today's `data/daily_picks_run_status_YYYY-MM-DD.jsonl` must contain runs with `"event_name": "workflow_dispatch"`. If it only contains `"schedule"` triggers, the external scheduler is down. The last recorded external dispatch was 2026-08-05; the PAT was configured 2026-05-07, so a 90-day token expiry is the most likely cause. The watchdog alert now includes an "External scheduler appears DOWN" note when no dispatch is seen.

Restore procedure (manual, cannot be done from this repo):

1. Create a new GitHub fine-grained PAT with Actions read/write on `anjanneogi13/daily-stock-agent` (or classic PAT with `repo` + `workflow`), noting the expiry date.
2. In cron-job.org, replace the token in the `Authorization` header on all six jobs and re-enable any auto-disabled jobs.
3. Test one job manually and confirm a `204 No Content` response and a matching `workflow_dispatch` run in GitHub Actions.

## Core Weekday Workflows

| Workflow | File | Purpose |
|---|---|---|
| Daily Stock Picks | `.github/workflows/daily-picks.yml` | Runs guarded official premarket pick generation attempts before the 09:20 ET cutoff |
| Morning Run Watchdog | `.github/workflows/watchdog.yml` | Checks in the 08:30-11:00 ET window whether official picks were logged; rescues before cutoff and alerts if missing |
| Late Watch-Only Daily Ideas | `.github/workflows/late_watch_only.yml` | After cutoff, sends clearly labeled watch-only fallback ideas only if official picks are missing |
| Intraday Monitor | `.github/workflows/intraday_monitor.yml` | Runs intraday monitoring, opening-range checks, alerts, observations, and run-status artifacts |
| News Engine | `.github/workflows/news_engine.yml` | Fetches/classifies news, updates watchlist/news evidence, and records run status |
| News Evidence | `.github/workflows/news_evidence.yml` | Generates monitoring-only news evidence and outcome reports |
| Evaluate | `.github/workflows/evaluate.yml` | Evaluates official picks after market close |

## Recurring Report / Reflection Workflows

| Workflow | File | Purpose |
|---|---|---|
| Nightly Brain | `.github/workflows/nightly_brain.yml` | Runs learning/reflection style routines where enabled |
| Weekly Report | `.github/workflows/weekly_report.yml` | Generates weekly reporting |
| Weekend Reflection | `.github/workflows/weekend_reflection.yml` | Generates weekend reflection / review artifacts |
| Monthly X-Ray | `.github/workflows/monthly_xray.yml` | Generates monthly analysis |
| Yearly Recap | `.github/workflows/yearly_recap.yml` | Generates yearly recap |
| Hypothesis Weekly | `.github/workflows/hypothesis_weekly.yml` | Runs weekly hypothesis review |

## Maintenance Workflows

| Workflow | File | Purpose |
|---|---|---|
| CI | `.github/workflows/ci.yml` | Runs tests and repository checks |
| Backup | `.github/workflows/backup.yml` | Backs up important data/artifacts |
| Holiday Renewal Reminder | `.github/workflows/holiday_renewal_reminder.yml` | Reminds maintainers to update market holiday/calendar support |

## Daily Picks Safety Schedule

Official daily picks are allowed only during the guarded premarket window.

Important behavior:

- normal official picks must run before the cutoff
- cutoff is 09:20 ET
- manual dispatch does not bypass the cutoff
- duplicate official rows are skipped if picks already exist for the ET date
- failed or zero-pick runs should preserve diagnostics
- no-pick days are acceptable when explained by candidate rejection or data-quality evidence

Related artifacts include:

- `data/picks_log.csv`
- `data/daily_picks_run_status_YYYY-MM-DD.jsonl`
- `data/market_data_health_YYYY-MM-DD.json`
- `data/daily_picks_candidate_rejections_YYYY-MM-DD.json`
- `data/daily_picks_candidate_rejections_YYYY-MM-DD.md`
- `data/daily_picks_no_pick_report_YYYY-MM-DD.md`

## Watchdog Safety Schedule

The watchdog checks between 08:30 and 11:00 ET whether picks have been logged, and dedups to one successful alert per day.

It may:

- send an urgent Telegram alert (including external-scheduler health)
- attempt to dispatch Daily Stock Picks before cutoff
- record run-status evidence

It must not:

- create picks itself
- bypass the official-picks timing gate
- enable paper/live trading

## Late Watch-Only Safety Schedule

Late watch-only fallback ideas run only after the official window is missed, between the 09:20 ET cutoff and 12:00 ET, with sent-ledger dedup.

They must:

- be clearly labeled watch-only
- avoid buy/sell instruction language
- avoid mutating `data/picks_log.csv`
- avoid official pick statistics
- avoid paper/live trading state

Related artifacts include:

- `data/late_daily_ideas_YYYY-MM-DD.jsonl`
- `data/late_daily_ideas_YYYY-MM-DD.md`
- `data/late_daily_ideas_sent_YYYY-MM-DD.json`

## Intraday Monitor Schedule

Intraday Monitor covers:

- opening-range checks
- intraday momentum observations
- active official-pick monitoring
- Telegram alerts where appropriate
- run-status and observation persistence

Important safety rules:

- opening-range and intraday momentum ideas are watch-only unless explicit official logic promotes them in the future
- new intraday opportunity alerts should avoid late-day chase behavior
- notification copy should use observed/reference-level wording, not action-like entry language
- watch-only observations must not affect official statistics

Related artifacts include:

- `data/intraday_alerts_YYYY-MM-DD.json`
- `data/intraday_momentum_observations_YYYY-MM-DD.jsonl`
- `data/opening_range_observations_YYYY-MM-DD.jsonl`
- `data/opening_range_run_status_YYYY-MM-DD.jsonl`
- `data/opening_range_bars/`

## News Schedule

News Engine runs throughout premarket, market hours, and postmarket windows according to the workflow cron and internal guards.

It may:

- fetch news
- classify headlines
- update watchlist/news evidence
- record run status
- produce watch-only or research evidence

It must not:

- silently create official picks
- mutate official pick statistics
- enable paper/live trading

Related artifacts include:

- `data/news_log.jsonl`
- `data/news_seen.json`
- `data/news_signals.json`
- `data/watchlist.json`
- `data/news_engine_run_status_YYYY-MM-DD.jsonl`
- `data/news_signal_outcomes_YYYY-MM-DD.jsonl`
- `data/news_signal_evidence_report_YYYY-MM-DD.md`

## Reports

Generated reports live under:

    reports/

Treat generated reports as outputs, not canonical documentation.

## Update Rule

When workflow schedules or guards change:

1. update the workflow YAML first
2. update this document second
3. update `docs/PROJECT_BLUEPRINT.md` if operating policy changed
4. update `docs/planning/DATA_CONTRACTS.md` if artifacts changed
5. update `docs/planning/NOTIFICATION_ARCHITECTURE.md` if notification behavior changed
6. update `docs/planning/CANDIDATE_LIFECYCLE.md` if lifecycle states or transitions changed
