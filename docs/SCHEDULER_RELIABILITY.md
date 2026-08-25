# Scheduler Reliability & PAT Rotation

How the "Daily Stock Picks" pipeline stays running when any single trigger
fails, and what to do when the scheduler PAT nears expiry.

## Trigger redundancy (no single point of failure)

| Layer | Mechanism | Covers |
|---|---|---|
| Primary | cron-job.org fires `workflow_dispatch` with a GitHub PAT | exact-time premarket trigger |
| Backup | native GitHub Actions `schedule:` cron in `daily-picks.yml` (`5,20,35,50 11-14 * * 1-5`) | external scheduler down, PAT expired |
| Guard | ET-window guard inside the workflow | duplicate/late fires — official picks only run 08:00–09:20 ET, dedup via `picks_log.csv` |
| Self-check | missed-window path → `scripts/send_missed_premarket_alert.py` sends one actionable alert; late ideas emitted watch-only | both triggers missed the window |
| Audit | `scripts/record_daily_picks_run_status.py` appends every attempt to `data/daily_picks_run_status_<date>.jsonl`, classifying the cause (`NO_PICK_WINDOW_MISSED`, `NO_PICK_ALL_FINALISTS_HARD_BLOCKED`, …) | distinguishing "genuinely nothing qualified" from "data/scheduler failed" |

A genuine no-pick day is a *chosen* outcome recorded with a cause; a missing
run is detected and alerted the same day. On no-pick days the Execution
Report still runs and prints "No premarket picks logged; N carryovers
monitored" (see `scripts/daily_execution_report.py`) so the daily report set
stays coherent.

## PAT expiry pre-alert

`scripts/check_pat_expiry.py` warns **before** the external scheduler's PAT
expires (the 2026-08-18 outage mode):

- Add the scheduler's fine-grained PAT as the optional repo secret
  `SCHEDULER_PAT`. GitHub exposes fine-grained PAT expiry via the
  `github-authentication-token-expiration` response header.
- The script alerts on Telegram when ≤ 7 days remain (`--warn-days` to tune).
- Without the secret (or for classic PATs with no expiry header) it logs and
  exits 0 — the check is additive, never blocking.

## PAT rotation procedure

1. Create a new **fine-grained PAT**: repo `daily-stock-agent`, permission
   *Actions: Read and write* (enough for `workflow_dispatch`), expiry ≤ 90 d.
2. Update the cron-job.org job's Authorization request header with the new
   token value.
3. Update the `SCHEDULER_PAT` repo secret with the same token so the
   pre-alert keeps tracking the right expiry.
4. Fire the cron job manually once and confirm a `workflow_dispatch` run
   appears in Actions.
5. Revoke the old PAT.

Even if rotation is missed, the native `schedule:` cron keeps premarket runs
going; the PAT only adds exact-time precision.
