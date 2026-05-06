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

### Priority 1 — Fix lower-severity audit hygiene before new features

Now fixed from the comprehensive audit:

- Daily-picks timing hard gate.
- Missed-window Telegram alert.
- Stale/unverified price watch-only protection.
- Monitoring-only default for paper logging.
- News action-window watch-only guard.

Next cleanup before feature work:

1. Clean documentation consistency issues.
2. Resume feature roadmap with opening-range intraday scanner.

Completed 2026-05-06:

- Fix test/data isolation: `data/learning_journal.jsonl` test side effects are isolated.
- Remaining tracked data isolation audited clean for `data/picks_log.csv` and `data/signal_journal.jsonl`.
- Align closed-status logic between readiness scripts.

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
