# Documentation Map

Use these docs first:

| File | Purpose |
|---|---|
| `PROJECT_BLUEPRINT.md` | Canonical architecture, current state, feature inventory, roadmap, and known gaps |
| `WORK_LOG.md` | Append-only history of meaningful work |
| `NEXT_SESSION.md` | Daily refreshed next-session handoff |
| `AGENT_MATURITY_TRACKER.md` | Real-world trading lessons, maturity scorecard, and intelligence roadmap |
| `MONSTER_HUNTER_DESIGN.md` | Long-term compounder / monster-stock research architecture |
| `PRODUCT_FAILURE_AND_WIN_STRATEGY.md` | Product failure modes, mitigations, and market win strategy |

Historical docs should be archived under `docs/archive/`.

Decision records live under `docs/decisions/`.

Operational playbooks live under `docs/playbook/`.

Documentation policy:

- Do not create another roadmap, status, or architecture doc unless intentionally temporary.
- Update `PROJECT_BLUEPRINT.md` when product, architecture, or roadmap status changes.
- Update `WORK_LOG.md` after every meaningful codebase move.
- Update `NEXT_SESSION.md` at the end of each work session.

## Latest handoff status

As of 2026-05-06 closeout:

- Start with `NEXT_SESSION.md`.
- Then read `PROJECT_BLUEPRINT.md` and `WORK_LOG.md`.
- The repo is monitoring-only.
- Paper/live trading remain disabled.
- Latest completed reliability lanes:
  - daily-picks missed-window late watch-only ideas,
  - combined missed-window Telegram alert,
  - opening-range run-status ledger,
  - forced persistence of ignored runtime artifacts.
