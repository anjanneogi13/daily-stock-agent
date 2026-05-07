# Daily Stock Agent — Work Log

Append-only history of every meaningful bug fix, feature, audit, and documentation change.

Rules:

1. Newest entries go first.
2. Include date, type, summary, tests, and follow-up.
3. Do not delete historical entries.
4. Update this file after every meaningful codebase move.
5. If architecture, roadmap, or product state changes, update `docs/PROJECT_BLUEPRINT.md`.
6. If next work changes, update `docs/NEXT_SESSION.md`.

---

## 2026-05-07 — Added News Engine run-status artifacts

**Type:** feature / observability / workflow safety

**Summary:**

Added News Engine run-status persistence so scheduled news runs are auditable.

New artifact:

- `data/news_engine_run_status_YYYY-MM-DD.jsonl`

Each run records:

- start/completion/failure event,
- result,
- items fetched,
- items classified,
- signals added,
- hard blocks,
- watchlist additions,
- high-impact internal alerts,
- Telegram enabled/attempted,
- GitHub workflow metadata.

Safety:

- News Engine still does not create official picks.
- No paper/live trading behavior changed.
- No readiness gates changed.
- This is observability only.

Verification:

- targeted tests passed,
- full suite passed: `1360 passed, 29 skipped`,
- journal consistency remained green,
- readiness dashboards remained blocked as expected,
- no official data artifacts were mutated.

---

## 2026-05-07 — Persisted intraday momentum watch-only observations

**Type:** feature / monitoring-only evidence / learning foundation

**Summary:**

Added structured persistence for generic intraday momentum watch-only ideas.

New artifact:

- `data/intraday_momentum_observations_YYYY-MM-DD.jsonl`

Each row records:

- ticker,
- timestamp,
- scanner=`momentum`,
- source=`intraday_scanner`,
- watch-only observation levels,
- score,
- reason,
- safety flags:
  - `watch_only=true`,
  - `mode=monitoring_only`,
  - `paper_trading_enabled=false`,
  - `live_trading_enabled=false`,
  - `ready_for_paper_trading=false`.

The Intraday Monitor now writes generic momentum observations separately from
opening-range observations. The GitHub Actions workflow force-adds the new
runtime artifact.

The watch-only learning report now reads:

- late daily watch-only ideas,
- opening-range observations,
- intraday momentum observations,
- intraday dedupe fingerprints,
- opening-range run status.

Safety:

- No official pick mutation.
- No `picks_log.csv` mutation.
- No `signal_journal.jsonl` mutation.
- No `learning_journal.jsonl` mutation.
- No paper trading.
- No live trading.

---

## 2026-05-07 — Added read-only watch-only learning report v1

**Type:** feature / observability / monitoring-only learning evidence

**Summary:**

Added `scripts/daily_watch_only_learning_report.py` as the first safe slice of the
watch-only learning evidence layer.

The script inventories existing non-official evidence for a date:

- `data/late_daily_ideas_YYYY-MM-DD.jsonl`,
- `data/opening_range_observations_YYYY-MM-DD.jsonl`,
- `data/opening_range_run_status_YYYY-MM-DD.jsonl`,
- `data/intraday_alerts_YYYY-MM-DD.json`,
- optional `data/intraday_alert_YYYY-MM-DD.md`.

Outputs:

- `data/watch_only_learning_report_YYYY-MM-DD.json`,
- `data/watch_only_learning_report_YYYY-MM-DD.md`.

Safety:

- Read-only with respect to official trade state.
- Does not write `data/picks_log.csv`.
- Does not write `data/signal_journal.jsonl`.
- Does not write `data/learning_journal.jsonl`.
- Does not create paper trades.
- Does not enable paper/live trading.
- Keeps official pick statistics separate from watch-only evidence.

Product result:

- Late daily watch-only ideas, opening-range observations, and intraday dedupe
  fingerprints can now be reviewed together even on days with no official
  premarket picks.
- The report explicitly documents gaps before outcome learning:
  - late ideas need outcome joins,
  - opening-range observations need bar artifacts,
  - generic momentum alerts need structured persistence beyond dedupe fingerprints.

---

## 2026-05-07 — Isolated intraday monitor run-status test side effect

**Type:** bug fix / test isolation / runtime artifact safety

**Summary:**

The comprehensive audit found that `tests/test_intraday_monitor_opening_range_observations.py`
mutated the tracked runtime artifact:

- `data/opening_range_run_status_2026-05-06.jsonl`

Root cause:

- The test calls `intraday_monitor.main()`.
- `main()` correctly records `monitor_started` and `monitor_completed` run-status rows.
- The test monkeypatched opening-range observation persistence but did not monkeypatch
  `append_opening_range_run_status`.

Fix:

- Monkeypatch `monitor.append_opening_range_run_status` inside the test.
- Assert the expected status events and counts without writing to tracked data.

Safety:

- Production run-status behavior is unchanged.
- GitHub Actions still records operational evidence.
- Tests no longer mutate tracked runtime artifacts.

---

## 2026-05-07 — Fixed intraday Telegram sender import side effect

**Type:** bug fix / test isolation / runtime artifact safety

**Summary:**

The comprehensive audit found that running the full test suite left
`data/opening_range_run_status_2026-05-06.jsonl` modified.

Root cause:

- `tests/test_scripts_import.py` imports scripts to catch broken imports.
- `scripts/send_intraday_telegram.py` still executed Telegram/run-status logic at import time.
- Importing the sender could append to the tracked opening-range run-status artifact.

Fix:

- Moved Telegram sender runtime behavior into `main()`.
- Kept `if __name__ == "__main__": raise SystemExit(main())`.
- Added regression tests proving:
  - importing the sender has no run-status side effects,
  - executing `main()` still records operational status when credentials are missing.

Safety:

- Monitoring-only.
- No official picks.
- No paper trades.
- No live trades.
- No enforcement flags changed.

---

## 2026-05-06 — Fixed Intraday Monitor Telegram sender import path

**Type:** bug fix / workflow reliability / GitHub Actions

**Summary:**

The manual GitHub Actions `Intraday Monitor` validation failed in
`scripts/send_intraday_telegram.py`:

- `ModuleNotFoundError: No module named 'src'`

Root cause:

- `send_intraday_telegram.py` imports `intraday_scanner`.
- `intraday_scanner.py` imports `src.opening_range_scanner`.
- When Actions runs `python scripts/send_intraday_telegram.py`, the script directory is on `sys.path`, but the repo root may not be.
- Therefore `src.*` imports can fail.

Fix:

- Add both `scripts/` and repo root to `sys.path` before importing `intraday_scanner`.
- Add a regression test that executes the sender from a temporary working directory with no Telegram credentials and confirms it exits successfully while writing the run-status artifact.

Safety:

- Monitoring-only.
- No official picks.
- No paper/live trading.
- No enforcement flags.

---

## 2026-05-06 — Session closeout after late-picks reliability and opening-range status work

**Type:** closeout / audit / documentation / monitoring-only

**Summary:**

Closed the session after completing the late-picks reliability lane and opening-range run-status observability lane.

Completed:

- Added late watch-only daily ideas for missed official premarket windows.
- Improved late idea quality with evidence filtering, ticker validation, quote enrichment, company names, watch-only BUY/Entry, SL, TP, and R/R.
- Combined the missed-window warning and late watch-only ideas into one Telegram message.
- Added `data/opening_range_run_status_YYYY-MM-DD.jsonl`.
- Recorded intraday/opening-range monitor start, skip, completion, candidate counts, alert counts, observation counts, and Telegram send/skipped/failed state.
- Fixed artifact persistence by force-adding ignored runtime files in Intraday Monitor.

Audit result:

- CI green through `27d92f0`.
- Full local audit passed before documentation closeout:
  - full suite: `1348 passed, 29 skipped`,
  - journal consistency: `41/41 matched`,
  - readiness dashboards remain blocked as expected,
  - opening-range audits remain monitoring-only,
  - tracked data side-effect check clean.

Remaining validation:

- Rerun GitHub Actions `Intraday Monitor` after commit `27d92f0`.
- Pull and confirm `data/opening_range_run_status_YYYY-MM-DD.jsonl` is committed from Actions with non-empty GitHub metadata.
- If this does not happen, inspect workflow logs before adding features.

Safety:

- Official premarket picks remain blocked after 09:20 ET.
- Late watch-only ideas remain separate from `picks_log.csv`.
- Opening-range observations/status remain watch-only and monitoring-only.
- Paper trading remains disabled.
- Live trading remains disabled.
- Enforcement flags remain disabled.

---

## 2026-05-06 — Forced commit of opening-range status artifacts

**Type:** workflow reliability / artifact persistence

**Summary:**

`data/` is ignored by `.gitignore`, so the Intraday Monitor workflow must use
`git add -f` for runtime artifacts that are intended to be committed.

Updated the workflow to force-add:

- `data/intraday_alerts_*.json`
- `data/opening_range_observations_*.jsonl`
- `data/opening_range_run_status_*.jsonl`

This ensures opening-range run-status evidence persists after GitHub Actions runs.

---

## 2026-05-06 — Added opening-range run-status ledger

**Type:** workflow observability / monitoring-only / intraday reliability

**Summary:**

Added a durable run-status artifact for intraday/opening-range monitoring.

New artifact:

- `data/opening_range_run_status_YYYY-MM-DD.jsonl`

Records:

- intraday monitor start,
- monitor skip reason,
- monitor completion,
- opening-range candidate count,
- total alert count,
- opening-range observation count,
- Telegram send/skipped/failed result.

Purpose:

- Distinguish “scanner did not run” from “scanner ran and found no qualified observations.”
- Preserve operational evidence even when no Telegram alert is sent.
- Keep opening-range monitoring watch-only and separate from official picks.

Safety:

- Monitoring-only.
- watch_only=true.
- No paper trading.
- No live trading.
- Does not write official picks.

---

## 2026-05-06 — Combined missed-window and late-ideas Telegram notice

**Type:** UX fix / monitoring-only / alert clarity

**Summary:**

After late watch-only daily ideas were added, manual after-cutoff daily-picks runs sent two Telegram messages:

1. missed premarket window alert,
2. late watch-only ideas.

This was noisy and confusing. The workflow now sends a single combined message:

- premarket window missed,
- official daily picks were not sent,
- late watch-only ideas are monitoring-only,
- BUY/Entry, SL, TP, and R/R are watch-only levels.

Safety:

- Official picks remain blocked after 09:20 ET.
- Late ideas remain separate from `picks_log.csv`.
- No paper/live trading is enabled.

---

## 2026-05-06 — Improved late watch-only idea quality and levels

**Type:** reliability fallback / monitoring-only / content quality

**Summary:**

Improved the late watch-only daily ideas after the first live run showed low-quality rows such as a one-letter headline and no trade-plan-style levels.

Fix:

- Filter weak evidence rows with too-short headlines/rationales.
- Validate ticker shape before surfacing ideas.
- Enrich late ideas with current quote context when available.
- Require quote enrichment in the workflow before sending late ideas.
- Add watch-only BUY/Entry, SL, TP, and R/R fields.
- Include company name when available.
- Avoid Markdown parsing issues in Telegram by sending the late-ideas message as plain text.
- Display source labels as `news-signal` instead of Markdown-sensitive `news_signal`.

Safety:

- Still monitoring-only.
- Still not official premarket picks.
- Still not written to `picks_log.csv`.
- Still not paper/live trades.

---

## 2026-05-06 — Added late watch-only daily ideas

**Type:** reliability fallback / monitoring-only / learning evidence

**Summary:**

Added a late-day monitoring fallback for missed official daily picks.

If the Daily Stock Picks workflow runs after the 09:20 ET official cutoff, it still refuses to create normal premarket picks, but it can now generate a separate watch-only idea artifact from current news/watchlist evidence.

New artifacts:

- `data/late_daily_ideas_YYYY-MM-DD.jsonl`
- `data/late_daily_ideas_YYYY-MM-DD.md`

Behavior:

- Official daily picks remain blocked after 09:20 ET.
- Late ideas are labeled `late_daily_watch_only`.
- Late ideas are sent to Telegram with explicit warnings.
- Late ideas are not written to `data/picks_log.csv`.
- Late ideas are not treated as official pick statistics.
- Run status records `late_ideas_generated` and `late_ideas_telegram`.

Safety:

- Monitoring-only.
- Not buy instructions.
- Not paper trades.
- Not live trades.
- Does not enable enforcement flags.

---

## 2026-05-06 — Fixed intraday scanner opening-range priority

**Type:** bug fix / monitoring-only / test stability

**Summary:**

The full suite exposed that legacy momentum candidates could outrank opening-range candidates in `scan_for_new_opportunities()` because the combined candidate list was sorted only by numeric score.

Fix:

- Preserve opening-range priority over legacy momentum candidates.
- Sort opening-range candidates first, then by score.
- Keeps all intraday candidates watch-only and monitoring-only.

Safety:

- No paper trading enabled.
- No live trading enabled.
- No official picks created.
- Intraday outputs remain watch-only observations.

---

## 2026-05-06 — Added daily-picks run-status artifact

**Type:** workflow observability / reliability / monitoring-only

**Summary:**

Added durable run-status logging for daily-picks and watchdog workflows.

New artifact:

- `data/daily_picks_run_status_YYYY-MM-DD.jsonl`

Records events such as:

- guard started,
- before-window skip,
- missed-window skip,
- duplicate-picks skip,
- guard passed,
- agent started/completed,
- CSV verification success/failure,
- Telegram send success/failure,
- watchdog checked,
- watchdog alert sent/failed.

Purpose:

- Distinguish "workflow did not run" from "workflow ran but skipped".
- Preserve operational evidence when GitHub cron/external scheduler timing is unreliable.
- Support future missed-run learning without mixing late/failed runs into official pick statistics.

Safety:

- Monitoring-only artifact.
- Does not create picks.
- Does not create paper trades.
- Does not enable live trading.
- Does not flip enforcement flags.

---

## 2026-05-06 — Fixed evaluate_picks import side effect

**Type:** bug fix / test isolation / data safety

**Summary:**

Fixed a tracked-data mutation discovered during the daily-picks reliability audit.

Root cause:

- `tests/test_scripts_import.py` smoke-imports scripts to catch broken imports.
- `scripts/evaluate_picks.py` executed evaluation logic at import time.
- Importing the script could run `evaluate_pending()` and mutate `data/picks_log.csv`.

Fix:

- Moved evaluation execution into `main()`.
- Added an explicit `if __name__ == "__main__"` guard.
- Importing `scripts/evaluate_picks.py` is now safe and should not mutate tracked data.

Safety:

- Reset accidental `data/picks_log.csv` side effects before continuing.
- Paper trading remains disabled.
- No enforcement flags changed.

---

## 2026-05-06 — Hardened daily-picks premarket reliability

**Type:** workflow reliability / monitoring safety

**Summary:**

Hardened the daily-picks automation after a live operational miss where no 2026-05-06 daily picks were logged by 10:06 ET.

Root cause:

- GitHub scheduled workflows are best-effort and cannot be prioritized.
- The prior design had too few useful premarket attempts before the 09:20 ET hard cutoff.
- The watchdog ran at 09:35 ET, after market open, which was too late to help.
- The watchdog checked `premarket_check.json` instead of the authoritative `data/picks_log.csv`.

Fix:

- Replaced sparse daily-picks cron slots with frequent guarded premarket attempts:
  - `5,20,35,50 12-14 * * 1-5`
- Kept the 09:20 ET hard cutoff for normal official daily picks.
- Reworked the morning watchdog to run at 09:10 and 09:18 ET.
- Watchdog now checks today's rows in `data/picks_log.csv`.
- Watchdog alerts Telegram before cutoff if no picks are logged.
- Added workflow reliability tests.

Safety:

- No paper trading enabled.
- No live trading enabled.
- No enforcement flags changed.
- Late/missed windows still do not send normal actionable picks.

---

## 2026-05-06 — Final closing audit passed

**Type:** audit / documentation / session closeout

**Summary:**

Completed final repository closing audit after the opening-range monitoring rollout and outcome-backtest stub work.

Audit result: clean.

Verified:

- Python compile passed.
- Targeted opening-range / monitoring tests passed: `39 passed`.
- Dead-code audit passed: `9 passed`.
- Full test suite passed: `1323 passed, 28 skipped`.
- Journal consistency audit passed with 41 matched entries and no mismatches.
- Enforcement readiness remains blocked due to insufficient evidence.
- Monitoring readiness remains blocked; paper trading remains forbidden.
- Opening-range review and backtest smoke tests passed.
- Safety grep found no true paper/live trading enablement flags.
- Tracked data files remained clean.
- Final working tree was clean after removing local audit logs.

Created closeout doc:

- `docs/decisions/2026-05-06-closing-audit-and-weekend-plan.md`

**Policy:**

New feature implementation should wait for weekends, Saturday/Sunday. Weekdays should prioritize monitoring, audits, observation review, and fixes if issues appear.

---

## 2026-05-06 — Added opening-range outcome-join/backtest skeleton

**Type:** tooling / monitoring-only / backtest design

**Summary:**

Added a read-only outcome-join/backtest skeleton for opening-range observations.

New script:

- `scripts/backtest_opening_range_observations.py`

New design doc:

- `docs/decisions/2026-05-06-opening-range-outcome-join-design.md`

Safety:

- Script is read-only.
- `paper_trading_enabled=false`.
- `ready_for_paper_trading=false`.
- Conservative same-bar ambiguity: if TP and SL both touch in the same bar, count `sl_hit`.
- Missing bar data is explicit and does not imply readiness.

**Next:**

Collect real opening-range observation and bar artifacts before using backtest results for any policy decision.

---

## 2026-05-06 — Added opening-range observation review tool

**Type:** tooling / monitoring-only / review

**Summary:**

Added a read-only review tool for opening-range observation artifacts.

New script:

- `scripts/review_opening_range_observations.py`

Reads:

- `data/opening_range_observations_*.jsonl`

Reports:

- total observations,
- unique tickers,
- observations by date,
- watch-only / monitoring-only compliance,
- average breakout percentage,
- average volume ratio,
- top observations by score,
- explicit paper-trading-disabled reminder.

Safety:

- Tool is read-only.
- Tool does not create official picks.
- Tool does not create paper trades.
- Tool does not imply buy instructions.
- `ready_for_paper_trading` is always `false`; readiness still belongs to the monitoring readiness dashboards and founder approval.

Usage:

- `python scripts/review_opening_range_observations.py`
- `python scripts/review_opening_range_observations.py --json`

**Tests:**

- `python3 -m pytest tests/test_opening_range_observation_review.py -q --tb=short --disable-warnings`
- `python3 -m pytest tests/ -q --tb=short --disable-warnings`
- `python scripts/audit_journal_consistency.py --strict`
- `python scripts/check_enforcement_readiness.py`
- `python scripts/monitoring_readiness.py`
- `git diff -- data/picks_log.csv data/signal_journal.jsonl data/learning_journal.jsonl`
- `git diff --check`

**Next:**

Use review output after market sessions to decide what outcome-join/backtest tooling is needed.

---

## 2026-05-06 — Refined opening-range workflow schedule

**Type:** workflow / monitoring-only / intraday scanner

**Summary:**

Refined `.github/workflows/intraday_monitor.yml` so the opening-range scanner can run early enough to catch moves closer to market open.

Schedule now includes:

- 09:35 ET targeted opening-range check
- 09:45 ET targeted opening-range check
- 10:00 ET follow-up through the baseline 30-minute monitor

Implementation details:

- Added targeted cron:
  - `35,45 13-14 * * 1-5`
- Kept baseline cron:
  - `0,30 13-21 * * 1-5`
- Added ET guard logic so `:35` / `:45` scheduled runs are allowed only when they are actually 09:35 / 09:45 ET.
- This avoids DST/EST duplicate off-target scans such as 10:35 / 10:45 ET.

Safety:

- Output remains `WATCH ONLY`.
- Observations persist only to `data/opening_range_observations_YYYY-MM-DD.jsonl`.
- No paper trades are created.
- Paper trading remains disabled.

**Tests:**

- `python3 -m pytest tests/test_intraday_monitor_workflow_schedule.py tests/test_intraday_monitor_workflow_observations.py -q --tb=short --disable-warnings`
- `python3 -m pytest tests/ -q --tb=short --disable-warnings`
- `python scripts/audit_journal_consistency.py --strict`
- `python scripts/check_enforcement_readiness.py`
- `python scripts/monitoring_readiness.py`
- `git diff -- data/picks_log.csv data/signal_journal.jsonl data/learning_journal.jsonl`
- `git diff --check`

**Next:**

Continue monitoring-only rollout:

1. Review opening-range observation artifacts after market sessions.
2. Add review/backtest tooling once enough observations exist.
3. Do not enable paper trading.

---

## 2026-05-06 — Persist opening-range observations

**Type:** feature / monitoring-only / observability / data artifact

**Summary:**

Added a dedicated monitoring-only observation artifact for opening-range scanner output.

New artifact:

- `data/opening_range_observations_YYYY-MM-DD.jsonl`

Purpose:

- Preserve opening-range scanner observations for later review/backtesting.
- Keep these observations separate from:
  - official picks,
  - paper trades,
  - future live trades.
- Avoid confusing future agents by explicitly marking rows as:
  - `watch_only=true`
  - `mode=monitoring_only`
  - `scanner=opening_range`

Implementation:

- `scripts/intraday_scanner.py`
  - added `opening_range_observation_path()`
  - added `build_opening_range_observation()`
  - added `append_opening_range_observations()`
- `scripts/intraday_monitor.py`
  - records opening-range observations after scanning new opportunities.
- `.github/workflows/intraday_monitor.yml`
  - commits `data/opening_range_observations_*.jsonl` alongside alert dedupe logs.

Safety:

- Non-opening-range opportunities are ignored by the observation writer.
- Non-watch-only opportunities are ignored by the observation writer.
- This artifact does not create trades or paper trades.

**Tests:**

- `python3 -m pytest tests/test_intraday_scanner_opening_range.py tests/test_intraday_monitor_workflow_observations.py -q --tb=short --disable-warnings`
- `python3 -m pytest tests/ -q --tb=short --disable-warnings`
- `python scripts/audit_journal_consistency.py --strict`
- `python scripts/check_enforcement_readiness.py`
- `python scripts/monitoring_readiness.py`
- `git diff -- data/picks_log.csv data/signal_journal.jsonl data/learning_journal.jsonl`
- `git diff --check`

**Next:**

Continue opening-range scanner rollout one slice at a time:

1. Consider 09:35 / 09:45 / 10:00 ET workflow schedule refinement.
2. Keep all opening-range output watch-only until evidence proves edge.
3. Do not enable paper trading.

---

## 2026-05-06 — Opening-range scanner slice and paper-trading checklist

**Type:** feature / monitoring-only / documentation

**Summary:**

Started opening-range intraday scanner implementation.

Implemented so far:

- Pure opening-range scanner core in `src/opening_range_scanner.py`.
- Opening-range breakout detection with:
  - opening range completeness checks,
  - volume confirmation,
  - anti-chase extension guard,
  - large-gap guard,
  - watch-only / monitoring-only candidate output.
- Wired opening-range candidates into `scripts/intraday_scanner.py` ahead of legacy momentum opportunities.
- Updated intraday Telegram message generation to label new opportunities as `WATCH ONLY`.
- Added paper-trading activation checklist:
  - `docs/decisions/2026-05-06-paper-trading-activation-checklist.md`

Important policy:

- Opening-range scanner outputs are monitoring-only.
- They must not create trades, orders, or paper-trade artifacts.
- Paper trading remains disabled until readiness dashboards pass and founder explicitly approves activation.

**Next:**

- Finish tests and commit the opening-range scanner batch.
- Continue keeping all intraday scanner candidates watch-only.

---

## 2026-05-06 — Minor documentation consistency cleanup

**Type:** documentation / roadmap hygiene

**Summary:**

Cleaned up stale documentation after completing audit/hygiene work.

Updated docs to reflect that:

- `data/learning_journal.jsonl` test side effects are isolated.
- Remaining tracked-data isolation was audited clean for:
  - `data/picks_log.csv`
  - `data/signal_journal.jsonl`
- Closed-status logic is aligned between enforcement and monitoring readiness dashboards.
- The next roadmap item is now the opening-range intraday scanner.
- Paper trading remains forbidden.

**Tests:**

- `python3 -m pytest tests/test_monitoring_first_docs.py -q --tb=short --disable-warnings`
- `python3 -m pytest tests/ -q --tb=short --disable-warnings`
- `python scripts/audit_journal_consistency.py --strict`
- `python scripts/check_enforcement_readiness.py`
- `python scripts/monitoring_readiness.py`
- `git diff --check`

**Next:**

Resume feature roadmap with opening-range intraday scanner in monitoring-only mode.

---

## 2026-05-06 — Audited remaining tracked-data test isolation

**Type:** test / data isolation / audit

**Summary:**

Audited the full test suite for remaining tracked-data side effects after fixing `data/learning_journal.jsonl` isolation.

Checked tracked files:

- `data/picks_log.csv`
- `data/signal_journal.jsonl`
- `data/learning_journal.jsonl`

Method:

- Reset all three tracked data files.
- Ran every `tests/test_*.py` file individually.
- After each test file, checked `git diff` for all three tracked data files.
- Reset any side-effect file before continuing.

Result:

- No tests mutate `data/picks_log.csv`.
- No tests mutate `data/signal_journal.jsonl`.
- No regressions mutate `data/learning_journal.jsonl`.

**Conclusion:**

Tracked-data test isolation is clean as of 2026-05-06.

**Follow-up:**

Remaining lower-severity cleanup:

1. Clean minor documentation consistency issues.
2. Then resume feature roadmap with opening-range intraday scanner.

---

## 2026-05-06 — Aligned readiness closed-status logic

**Type:** bug fix / readiness dashboard consistency / test

**Summary:**

Aligned closed-trade status handling between readiness dashboards.

Problem:

- `scripts/monitoring_readiness.py` counted `day_close` as a closed outcome.
- `scripts/check_enforcement_readiness.py` only counted `tp_hit`, `sl_hit`, and `expired`.
- This made enforcement readiness undercount post-floor closed picks compared with monitoring readiness.

Fix:

- Added shared-style `CLOSED_STATUSES` in `scripts/check_enforcement_readiness.py`.
- Included `day_close`.
- Added regression tests that:
  - enforcement closed statuses match monitoring readiness statuses.
  - `day_close` rows are counted as closed by enforcement readiness.

Current effect:

- Enforcement readiness post-floor closed count moved from `2` to `3`.
- Monitoring readiness still reports day `1` + swing `2` = total `3`.
- Both dashboards remain correctly blocked by minimum sample requirements.

**Tests:**

- `python3 -m pytest tests/test_enforcement_readiness.py tests/test_monitoring_readiness.py tests/test_smell_enforcement_readiness.py -q --tb=short --disable-warnings`
  - `22 passed`
- `python3 -m pytest tests/ -q --tb=short --disable-warnings`
  - `1286 passed, 28 skipped`
- `python scripts/audit_journal_consistency.py --strict`
- `python scripts/check_enforcement_readiness.py`
- `python scripts/monitoring_readiness.py`
- `git diff -- data/learning_journal.jsonl`
  - no diff
- `git diff --check`

**Follow-up:**

Remaining lower-severity cleanup:

1. Audit remaining test/data isolation for `picks_log.csv` and `signal_journal.jsonl`.
2. Clean minor documentation consistency issues.
3. Then resume feature roadmap with opening-range intraday scanner.

---

## 2026-05-06 — Fixed learning journal test/data isolation

**Type:** test / data isolation / hygiene

**Summary:**

Fixed full-suite side effects that mutated tracked `data/learning_journal.jsonl`.

Root cause:

- `tests/test_nightly_conductor.py`
- `tests/test_pattern_layer.py`
- `tests/test_weight_applier.py`

were exercising code paths that append to `src.learning_journal.JOURNAL` without monkeypatching it away from the tracked production data file.

Fix:

- Patched each test/fixture to redirect `learning_journal.JOURNAL` to `tmp_path / "learning_journal.jsonl"`.
- Verified targeted and full-suite runs no longer mutate tracked `data/learning_journal.jsonl`.

**Tests:**

- `python3 -m pytest tests/test_nightly_conductor.py tests/test_pattern_layer.py tests/test_weight_applier.py -q --tb=short --disable-warnings`
  - `26 passed`
- `python3 -m pytest tests/ -q --tb=short --disable-warnings`
  - `1284 passed, 28 skipped`
- `python scripts/audit_journal_consistency.py --strict`
- `python scripts/check_enforcement_readiness.py`
- `python scripts/monitoring_readiness.py`
- `git diff -- data/learning_journal.jsonl`
  - no diff
- `git diff --check`

**Follow-up:**

Continue lower-severity audit cleanup:

1. Align closed-status logic between readiness scripts.
2. Clean minor documentation consistency issues.
3. Then resume feature roadmap with opening-range intraday scanner.

---

## 2026-05-06 — Comprehensive audit fixes for monitoring safety

**Type:** audit / bug fix / workflow hardening / monitoring safety

**Summary:**

Performed comprehensive repo-health audit before new feature work and fixed the highest-severity issues first.

Fixed:

- Intraday monitor CSV close regression:
  - `scripts/intraday_monitor.py` now uses module `TODAY` when closing picks, so test/backfill/manual monitor runs update the same `pick_date` selected by `load_todays_picks()`.
  - Prevents repeated SL/TP alerts from leaving rows stuck as `pending`.

- Daily-picks timing hard gate:
  - `.github/workflows/daily-picks.yml` now blocks normal daily picks after 09:20 ET.
  - Manual dispatch no longer bypasses the official premarket timing gate.
  - Late runs send a missed-window Telegram alert instead of normal actionable picks.

- Stale/unverified price protection:
  - `scripts/premarket_check.py` now marks unverified prices as `👀 WATCH ONLY`.
  - Telegram daily sender does not show actionable buy instructions for watch-only picks.
  - GitHub issue formatter documents the watch-only state.

- Monitoring-only paper logging safety:
  - `main.py` no longer defaults to paper-trade logging when `TRADING_MODE` is unset.
  - Legacy local paper logging is now opt-in only with `TRADING_MODE=paper`.

- News action-window guard:
  - `src/news_signals.py` preserves `action_window`.
  - `main.py` marks intraday-news swing candidates as watch-only instead of silently presenting them as normal swing entries.
  - `src/pick_logger.py` persists `watch_only`, `watch_only_reason`, and `news_action_window`.

Added tests for:

- Missed premarket-window alert.
- Daily-picks 09:20 ET hard cutoff.
- Watch-only stale-price behavior.
- Monitoring mode paper-logging default.
- News action-window preservation and watch-only guard.
- Pick logger watch-only/news-action-window persistence.

**Tests:**

- `python3 -m pytest tests/ -q --tb=short --disable-warnings`
  - `1284 passed, 28 skipped`
- `python scripts/audit_journal_consistency.py --strict`
- `python scripts/check_enforcement_readiness.py`
- `python scripts/monitoring_readiness.py`
- `git diff --check`

**Follow-up:**

Highest-severity audit issues are fixed. Next lower-severity cleanup should address:

1. Test/data isolation for `data/learning_journal.jsonl` and related tracked data side effects.
2. Closed-status alignment between readiness scripts.
3. Documentation consistency cleanup.
4. Then resume feature roadmap with opening-range intraday scanner.

---

## 2026-05-06 — Created agent maturity tracker and intelligence roadmap

**Type:** documentation / product strategy

**Summary:**

Created `docs/AGENT_MATURITY_TRACKER.md` to preserve the May 5 trading-day analysis and track how the agent matures.

Documented:

- Premarket swing, intraday, and monster-hunt lanes.
- POWI as an older 2026-04-28 swing pick that hit `+2.0R` on 2026-05-05.
- EXPD as a valid earnings catalyst but poor intraday/swing classification case.
- GILT as a valid catalyst with speculative/pump-risk concerns.
- NET as a strong intraday opportunity detected too late.
- Daily Telegram timing and stale-price issues.
- Fundamental/P&L analysis roadmap.
- Reader/wisdom learning roadmap.
- Historical regime learning roadmap.
- Historical chart/pattern replay roadmap.
- Monster-hunt long-term compounder roadmap.

Updated:

- `docs/README.md`
- `docs/PROJECT_BLUEPRINT.md`
- `docs/NEXT_SESSION.md`

**Follow-up:**

Next implementation should start with daily-picks timing and stale-price protection before deeper intelligence features.

**Tests:**

Documentation-only change. Run markdown/file sanity and startup health before next coding task.

---

## 2026-05-06 — Reviewed 2026-05-05 pick outcomes

**Type:** monitoring / data evaluation

**Summary:**

Reviewed the 2026-05-05 agent picks and current evaluated outcomes:

- `EXPD` had a valid bullish earnings-beat catalyst but hit stop loss: `-1.0R`.
- `GILT` had a bullish contract-win catalyst and remains pending.
- `POWI` was evaluated as a strong take-profit win: `+2.0R`.

**Lesson:**

The agent is finding real catalysts, but news action windows are not yet fully connected to trade classification. Both `EXPD` and `GILT` had news classified as `intraday`, while the picks were logged as `swing`.

**Risks observed:**

- Missing company/tag metadata on 2026-05-05 picks.
- Premarket check could not verify prices and marked both picks half-size.
- Brain probability / EV fields were blank.
- Smell faculty did not flag missing verification or intraday/swing mismatch.

**Follow-up:**

Consider adding a guard or scoring adjustment so high-urgency news catalysts with `action_window=intraday` are either:

1. logged as day/intraday trades,
2. given tighter monitoring rules, or
3. penalized/blocked as swing picks unless confirmed by stronger multi-day setup.

**Tests:**

- `python scripts/audit_journal_consistency.py --strict`
- `python3 -m pytest tests/test_journal_consistency.py tests/test_signal_journal_quality.py -q --tb=short`

---

## 2026-05-05 — Signal journal quality repair

**Type:** data fix

**Summary:**

Set post-fix `vol_ratio_bucket` values for the newly repaired 2026-05-05 signal journal rows:

- `EXPD` -> `low`
- `GILT` -> `low`

Also reset full-suite evaluation side effects on those signal rows so they match the pending state in `data/picks_log.csv`.

**Tests:**

- `python3 -m pytest tests/test_signal_journal_quality.py tests/test_journal_consistency.py -q --tb=short`
- Full suite

---

## 2026-05-05 — Signal journal consistency repair

**Type:** data fix

**Summary:**

Added missing signal journal rows for post-send picks:

- `2026-05-05 EXPD`
- `2026-05-05 GILT`

**Reason:**

The post-send state commit added rows to `data/picks_log.csv` without matching rows in `data/signal_journal.jsonl`, breaking the journal consistency invariant.

**Tests:**

- `python3 -m pytest tests/test_journal_consistency.py -q --tb=short`
- Full suite

**Follow-up:**

Investigate and harden the post-send persistence path so picks cannot be persisted without matching signal journal entries.

---

## 2026-05-05 — Documentation consolidation

**Type:** docs / process

**Summary:**

Created canonical documentation structure:

- `docs/PROJECT_BLUEPRINT.md`
- `docs/WORK_LOG.md`
- `docs/NEXT_SESSION.md`
- `docs/README.md`

**Reason:**

Older docs repeated architecture, roadmap, current state, bug ledger, and next-session content.

**Follow-up:**

Keep this file updated after every bug fix, feature, audit, or process change.

---

## 2026-05-05 — LLM agent coverage and cache fix

**Commit:** `0deccc5`

**Type:** test / bug fix

**Summary:** Added `llm_agent` provider fallback/cache tests and fixed timezone-aware cache timestamps.

**Tests:** 1273 passed, 28 skipped

**CI:** green

---

## 2026-05-05 — Market news coverage

**Commit:** `5036ad0`

**Type:** test

**Summary:** Added tests for market news cache, Finnhub fetch fallbacks, Claude/Gemini parsing, and briefing assembly.

**CI:** green

---

## 2026-05-05 — Earnings analyzer coverage

**Commit:** `a1f2a70`

**Type:** test

**Summary:** Added tests for earnings cache, Finnhub fallbacks, recommendations, and composite score math.

**CI:** green

---

## 2026-05-05 — Hard blocks coverage

**Commit:** `6c4fc03`

**Type:** test

**Summary:** Added tests for hard-block gate logic and audit-log behavior.

**CI:** green

---

## 2026-05-05 — Tiered exits reserved schema

**Commit:** `c17d2dd`

**Type:** docs / product decision

**Summary:** Marked tiered TP columns as reserved schema in monitoring mode.

**CI:** green

---

## 2026-05-05 — Telegram delivery reliability

**Commit:** `aa9829f`

**Type:** bug fix

**Summary:** Daily sender marks dedup only after confirmed delivery.

**CI:** green

---

## 2026-05-05 — Daily picks persistence hardening

**Commit:** `caf5e9b`

**Type:** workflow fix

**Summary:** Daily picks workflow now recovers/persists state and fails if persistence cannot be pushed.

**CI:** green

---

## 2026-05-05 — CI audit syntax repair

**Commit:** `6dd5dd5`

**Type:** CI fix

**Summary:** Repaired full repo audit syntax/import-safety issues.

**CI:** green
