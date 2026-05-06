# Daily Stock Agent — Next Session

**Refresh date:** 2026-05-06
**Status:** monitoring-ready, highest-severity audit issues fixed
**Mode:** monitoring-only

Do not start paper trading yet.

---

## Read first

1. `docs/PROJECT_BLUEPRINT.md`
2. `docs/WORK_LOG.md`
3. `docs/AGENT_MATURITY_TRACKER.md`
4. This file
5. `docs/decisions/2026-05-05-monitoring-first-no-paper-trading.md`
6. `docs/decisions/2026-05-06-paper-trading-activation-checklist.md`
7. `docs/decisions/2026-05-06-opening-range-outcome-join-design.md`
8. `docs/decisions/2026-05-06-session-closeout-reliability-and-opening-range.md`

---

## Current product lesson

The 2026-05-05 monitoring review showed that the agent can find real catalysts, but it still needs stronger execution intelligence.

Observed:

- `POWI` was an older swing pick from 2026-04-28 and hit TP on 2026-05-05: `+2.0R`.
- `EXPD` had a real earnings-beat catalyst but was logged as swing even though news action window was intraday; it hit stop and later recovered.
- `GILT` had a real contract-win catalyst but has speculative/pump-risk concerns and remains pending.
- `NET` was a strong intraday opportunity but was detected late.
- Daily Telegram picks arrived too late / inconsistently due to workflow timing and data freshness issues.

---

## Best next task

### Priority 1 — Resume feature roadmap: opening-range intraday scanner

Audit/hygiene work completed:

- Daily-picks timing hard gate.
- Missed-window Telegram alert.
- Stale/unverified price watch-only protection.
- Monitoring-only default for paper logging.
- News action-window watch-only guard.
- `data/learning_journal.jsonl` test side effects isolated.
- Remaining tracked data isolation audited clean for `data/picks_log.csv` and `data/signal_journal.jsonl`.
- Closed-status logic aligned between readiness scripts.
- Minor documentation consistency cleanup completed.
- 09:35 / 09:45 / 10:00 ET opening-range workflow cadence is wired.

Next feature work:

1. Continue opening-range intraday scanner rollout in monitoring-only mode.
2. Run `python scripts/review_opening_range_observations.py` after market sessions.
3. Review `data/opening_range_observations_YYYY-MM-DD.jsonl` artifacts after market sessions.
4. Add outcome-join/backtest tooling once enough observations exist.
5. Keep outputs observe/watch-only until enough intraday evidence exists.
6. Do not enable paper trading.
7. Use `docs/decisions/2026-05-06-paper-trading-activation-checklist.md` before any future paper-trading integration.

Completed 2026-05-06:

- Fix test/data isolation: `data/learning_journal.jsonl` test side effects are isolated.
- Remaining tracked data isolation audited clean for `data/picks_log.csv` and `data/signal_journal.jsonl`.
- Align closed-status logic between readiness scripts.
- Clean minor documentation consistency issues.

After those are clean, resume feature work with opening-range intraday scanner.

---

## Completed from prior Priority 1 — Daily-picks timing and stale-price protection

### Priority 1 — Fix daily-picks timing and stale-price protection

Problem:

- Fixed 2026-05-06: normal daily picks are blocked after 09:20 ET.
- Fixed 2026-05-06: manual dispatch no longer bypasses the time guard.
- Fixed 2026-05-06: late runs send missed-window alert instead of normal picks.
- Fixed 2026-05-06: stale/unverified prices are marked watch-only.

Goal:

- Official daily picks should only be sent before market open.
- If the premarket window is missed, send a Telegram missed-window alert instead of normal picks.
- If price is stale/unverified, mark idea as watch-only and do not show actionable entry.

Suggested policy:

- Before 09:20 ET: allow official daily picks.
- After 09:20 ET: block normal daily picks.
- If missed: send premarket-window-missed alert.
- After cutoff: allow only intraday monitor alerts.

---

## Completed from prior Priority 2 — Enforce news action window

Problem:

- Fixed 2026-05-06: news signals preserve `action_window`.
- Fixed 2026-05-06: intraday-news swing candidates are marked watch-only instead of normal actionable swing picks.

Goal:

- Intraday news must not silently become a normal swing pick.

Possible behavior:

1. Convert to day/intraday trade.
2. Require additional multi-day confirmation before swing.
3. Mark as watch-only.
4. Penalize/block as swing if confirmation is missing.

---

## Priority 3 — Opening-range intraday scanner

Problem:

- NET was detected after much of the move had already happened.

Goal:

- Add earlier scans:
  - 09:35 ET
  - 09:45 ET
  - 10:00 ET

Use:

- gap,
- volume,
- VWAP,
- opening range,
- news context,
- anti-chase rule.

---

## Priority 4 — Fundamental-quality / pump-risk smell

Problem:

- GILT had real news but may be a speculative name with long-term value destruction.

Goal:

- Add a smell/penalty for speculative news spikes and poor long-term quality.

Signals:

- huge drawdown from all-time high,
- weak long-term trend,
- poor fundamentals,
- small-cap news spike,
- possible dilution/reverse split history,
- low liquidity,
- news-only move.

---

## Priority 5 — Monster-hunt foundation

Goal:

Build a separate long-term compounder lane, not mixed with swing/day picks.

Required pieces:

- monster watchlist,
- thesis states,
- quarterly/yearly P&L analysis,
- secular theme detection,
- fundamental acceleration,
- historical chart base detection,
- long-term exit/trim plan.

---

## Existing engineering hygiene priorities

Still important:

1. Add tests for:
   - `src/performance_stats.py`
   - `src/paper_trader.py`
   - `src/picks_csv.py`
   - `src/monster_data.py`
   - `src/cape_ratio.py`
4. Backtester hardening.

---

## Blocked items

Do not build or activate yet:

- Paper trading integration.
- `SMELL_ENFORCE=true`.
- `BRAIN_ENFORCE_EV=true`.
- `AUTO_PAUSE_ENABLED=true`.

Do not promote these beyond observe-mode without tests and monitoring evidence:

- Reader engine.
- Curiosity engine.
- Historical regime engine.
- Historical chart replay engine.
- Monster-hunt engine.
- Multi-LLM ensemble.

---

## Session start commands

Run:

- `cd /workspaces/daily-stock-agent`
- `git status --short`
- `git pull --rebase origin main`
- `python3 -m pytest tests/ -q --tb=short --disable-warnings`
- `python scripts/audit_journal_consistency.py --strict`
- `python scripts/check_enforcement_readiness.py`
- `python scripts/monitoring_readiness.py`

If tests mutate tracked data, reset only data side effects:

- `git checkout -- data/picks_log.csv data/signal_journal.jsonl data/learning_journal.jsonl data/premarket_check.json`

---

## Documentation update rule

After every bug fix, feature, audit, or process change:

1. Update `docs/WORK_LOG.md`.
2. Update `docs/NEXT_SESSION.md`.
3. Update `docs/PROJECT_BLUEPRINT.md` if architecture, roadmap, or product state changed.
4. Update `docs/AGENT_MATURITY_TRACKER.md` when trading lessons or intelligence roadmap changes.
5. Keep CI/tests green.


Backtest tool: `python scripts/backtest_opening_range_observations.py`

## Closing audit status — 2026-05-06

Final closing audit passed.

Current state:

- Repository clean.
- Full suite passed: `1348 passed, 29 skipped`.
- Targeted opening-range / monitoring tests passed.
- Journal consistency green.
- Enforcement readiness blocked as expected.
- Monitoring readiness blocks paper trading as expected.
- Paper trading remains disabled.
- Opening-range review and backtest tools are available.

Before next work:

1. Run full repo audit.
2. If issues are found, fix issues first.
3. If clean and it is Saturday/Sunday, implement the next planned feature slice.
4. If weekday, prefer monitoring/audit/review work unless urgent.
5. Never enable paper/live trading without readiness gates and founder approval.

Recommended next weekend feature:

- Optional opening-range bar artifact capture, still monitoring-only.

## Daily-picks reliability hardening — 2026-05-06

A live operational miss showed no daily picks were logged for 2026-05-06 by 10:06 ET.

Reliability fix applied:

- Daily-picks workflow now has frequent guarded premarket cron attempts.
- The 09:20 ET hard cutoff remains in place.
- Morning watchdog now runs before cutoff at 09:10 and 09:18 ET.
- Watchdog checks `data/picks_log.csv`, not stale `premarket_check.json`.
- Watchdog sends Telegram alerts while there is still time to manually trigger daily picks.

Next verification:

1. Confirm GitHub Actions schedules fire on the next market day.
2. Confirm daily picks are logged before 09:20 ET.
3. Confirm Telegram receives either picks or an early watchdog alert.
4. Keep paper/live trading disabled.

## Import-safety fix — 2026-05-06

During the daily-picks reliability work, the full suite revealed that `tests/test_scripts_import.py` could mutate tracked `data/picks_log.csv`.

Root cause:

- `scripts/evaluate_picks.py` ran evaluation logic at import time.

Fix:

- `scripts/evaluate_picks.py` is now import-safe.
- Execution is behind `main()` and `if __name__ == "__main__"`.

Continue to verify tracked data stays clean after full-suite runs.

## Daily-picks run-status artifact — 2026-05-06

Added `data/daily_picks_run_status_YYYY-MM-DD.jsonl` as the operational ledger for daily-picks and watchdog attempts.

Use it to answer:

- Did daily-picks workflow start?
- Did the guard skip or proceed?
- Were picks already logged?
- Did main.py run?
- Did CSV verification pass?
- Did Telegram send?
- Did watchdog check and alert?

Next reliability feature after this is clean:

- Add late watch-only daily ideas in a separate ledger, not official picks.

## Late watch-only daily ideas — 2026-05-06

Added a missed-window fallback:

- Official premarket picks remain blocked after 09:20 ET.
- The workflow can generate `data/late_daily_ideas_YYYY-MM-DD.jsonl`.
- Telegram receives a clearly labeled late watch-only message.
- These ideas are not official picks and do not enter `picks_log.csv`.

Use this to avoid wasting the entire day when GitHub scheduled workflows miss the official window, while keeping official statistics clean.

## Session closeout — 2026-05-06 late-picks reliability and opening-range observability

Final status at closeout:

- Main branch head after code work: `27d92f0 intraday: force-add opening-range status artifacts`.
- Latest CI observed green: CI #141.
- Full local audit before closeout passed:
  - full test suite: `1348 passed, 29 skipped`,
  - journal consistency: `41/41 matched`,
  - readiness dashboards remain blocked as expected,
  - opening-range review/backtest remain monitoring-only,
  - tracked data side-effect check clean.
- Paper trading remains disabled.
- Live trading remains disabled.
- Enforcement flags remain disabled.

Completed in this session:

1. Daily-picks missed-window fallback:
   - official premarket picks remain blocked after 09:20 ET,
   - after-cutoff runs generate separate late watch-only ideas,
   - late ideas do not enter `data/picks_log.csv`,
   - late ideas are not official stats.

2. Late idea quality upgrade:
   - filters weak rows such as one-letter headline/evidence,
   - validates ticker shape,
   - requires quote enrichment in workflow,
   - includes company name when available,
   - includes watch-only BUY/Entry, SL, TP, and R/R.

3. Telegram UX fix:
   - missed-window notice and late watch-only ideas are now one combined message,
   - expected heading:
     - `PREMARKET WINDOW MISSED — LATE WATCH-ONLY DAILY IDEAS`.

4. Opening-range run-status ledger:
   - new artifact:
     - `data/opening_range_run_status_YYYY-MM-DD.jsonl`,
   - records monitor started/skipped/completed,
   - records candidate count, alert count, observation count,
   - records Telegram send/skipped/failed result,
   - always monitoring-only/watch-only.

5. Opening-range artifact persistence fix:
   - `.gitignore` ignores `data/`, so Intraday Monitor now uses `git add -f` for:
     - `data/intraday_alerts_*.json`,
     - `data/opening_range_observations_*.jsonl`,
     - `data/opening_range_run_status_*.jsonl`.

Important remaining validation:

- Rerun GitHub Actions `Intraday Monitor` after commit `27d92f0`.
- Pull afterward and confirm a new commit/artifact exists with non-empty GitHub metadata:
  - `github.run_id`,
  - `github.sha`,
  - `github.workflow`.
- If no artifact commit appears, inspect the workflow logs before adding new features.

Next best task:

1. Validate Step 4B artifact persistence from GitHub Actions.
2. If validated, close the reliability lane.
3. Next feature candidate, preferably weekend-only:
   - opening-range bar artifact capture for future backtest joins.
4. Continue monitoring-only mode.
5. Do not enable paper/live trading.
