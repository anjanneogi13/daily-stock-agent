# Daily Stock Agent — Next Session

**Refresh date:** 2026-05-05
**Status:** monitoring-ready, CI green, 1273 passed / 28 skipped
**Mode:** monitoring-only

Do not start paper trading yet.

---

## Read first

1. `docs/PROJECT_BLUEPRINT.md`
2. `docs/WORK_LOG.md`
3. This file

---

## Best next task

### Priority 1 — Fix test/data isolation

Problem:

Full suite runs can mutate:

- `data/picks_log.csv`
- `data/signal_journal.jsonl`

Goal:

Running the full suite should leave `git status --short` clean.

Commands:

```bash
git status --short
python3 -m pytest tests/ -q --tb=short --disable-warnings
git status --short
git diff -- data/picks_log.csv data/signal_journal.jsonl
```

---

## Priority 2 — Add remaining module tests

Recommended order:

1. `src/performance_stats.py`
2. `src/paper_trader.py`
3. `src/picks_csv.py`
4. `src/monster_data.py`
5. `src/cape_ratio.py`

---

## Priority 3 — Align readiness closed statuses

Check whether `day_close` should count as closed everywhere.

Current mismatch:

- `scripts/monitoring_readiness.py` includes `day_close`.
- `scripts/check_enforcement_readiness.py` excludes `day_close`.

---

## Priority 4 — Backtester hardening

Harden `src/backtester/` after hygiene/tests.

---

## Blocked items

Do not build or activate yet:

- Paper trading integration.
- `SMELL_ENFORCE=true`.
- `BRAIN_ENFORCE_EV=true`.
- `AUTO_PAUSE_ENABLED=true`.
- Curiosity engine.
- Reader engine.
- Historical regime engine.
- Multi-LLM ensemble.

---

## Session start commands

```bash
cd /workspaces/daily-stock-agent
git status --short
git pull --rebase origin main
python3 -m pytest tests/ -q --tb=short --disable-warnings
python scripts/check_enforcement_readiness.py
python scripts/monitoring_readiness.py
```

If tests mutate tracked data:

```bash
git checkout -- data/picks_log.csv data/signal_journal.jsonl
```

---

## Documentation update rule

After every bug fix, feature, audit, or process change:

1. Update `docs/WORK_LOG.md`.
2. Update `docs/NEXT_SESSION.md`.
3. Update `docs/PROJECT_BLUEPRINT.md` if architecture, roadmap, or product state changed.
4. Keep CI green.
