# Documentation Map

Use this file as the starting point for repository documentation.

Daily Stock Agent currently operates in:

- monitoring-only mode
- no paper trading
- no live trading
- official picks separated from watch-only ideas
- research-only lanes separated from official statistics

## Start Here

Read these first:

| File | Purpose |
|---|---|
| `README.md` | Short public-facing project overview |
| `docs/PROJECT_BLUEPRINT.md` | Canonical current architecture, status, feature inventory, and operating policy |
| `docs/NEXT_SESSION.md` | Current handoff and next recommended work |
| `docs/WORK_LOG.md` | Append-only work history |
| `docs/planning/README.md` | Planning documentation index for future architecture and safety design |

## Planning Docs

Long-term roadmap, data contracts, notification rules, and candidate lifecycle planning live under:

`docs/planning/`

Key files:

| File | Purpose |
|---|---|
| `docs/planning/FEATURE_BACKLOG.md` | Future feature backlog and implementation phases |
| `docs/planning/DATA_CONTRACTS.md` | Expected data artifacts, ownership, schemas, and safety rules |
| `docs/planning/NOTIFICATION_ARCHITECTURE.md` | Notification classification, wording, disclaimers, and future renderer plan |
| `docs/planning/CANDIDATE_LIFECYCLE.md` | Candidate states, transitions, readiness gates, and anti-corruption rules |

Planning docs are not runtime behavior by themselves. Treat them as design guidance until matching code and tests exist.

## Current Core Docs

| File | Purpose |
|---|---|
| `docs/PROJECT_BLUEPRINT.md` | Current source of truth for architecture and operating posture |
| `docs/strategy/AGENT_MATURITY_TRACKER.md` | Real-world trading lessons, maturity scorecard, and intelligence roadmap |
| `docs/strategy/MONSTER_HUNTER_DESIGN.md` | Long-term compounder / monster-stock research architecture |
| `docs/strategy/PRODUCT_FAILURE_AND_WIN_STRATEGY.md` | Product failure modes, mitigations, and market win strategy |
| `docs/DATA_QUALITY_FLOOR.md` | Data-quality expectations and minimum safety floor |
| `docs/REPO_HEALTH.md` | Repository health and audit status, if actively maintained |

## Strategy Docs

| File | Purpose |
|---|---|
| `docs/strategy/AGENT_PHILOSOPHY.md` | Agent product philosophy and faculty model |
| `docs/strategy/BUSINESS_PLAN.md` | Business and go-to-market planning |
| `docs/strategy/MONSTER_HUNTER_DESIGN.md` | Long-term compounder / monster-stock research architecture |
| `docs/strategy/PRODUCT_FAILURE_AND_WIN_STRATEGY.md` | Product failure modes, mitigations, and market win strategy |

## Reference Docs

| File | Purpose |
|---|---|
| `docs/reference/BACKTESTER_DESIGN.md` | Backtester design reference |
| `docs/reference/PROBABILITY_ENGINE_DESIGN.md` | Probability engine design reference |
| `docs/reference/intraday_model_strategy.md` | Intraday model strategy reference |
| `docs/reference/intraday_technical_indicators.md` | Intraday technical indicators reference |

## Operational Docs

| Location | Purpose |
|---|---|
| `docs/playbook/` | Operator playbooks and manual workflow instructions |
| `docs/decisions/` | Decision records and dated architecture/product decisions |
| `docs/sessions/` | Session notes and historical handoffs |
| `reports/` | Generated reports; treat as outputs, not canonical documentation |

## Compatibility / Historical Entry Points

Some older files are kept as compatibility stubs or historical entry points:

| File | Status |
|---|---|
| `docs/ARCHITECTURE.md` | Redirect-style entry point; current architecture is in `PROJECT_BLUEPRINT.md` and planning docs |
| `docs/FINAL_ROADMAP.md` | Redirect-style entry point; future backlog is in `docs/planning/FEATURE_BACKLOG.md` |
| `docs/FUTURE_ROADMAP_PRIORITIZED.md` | Redirect-style entry point; future backlog is in `docs/planning/FEATURE_BACKLOG.md` |
| `docs/TODO_BUGS.md` | Redirect-style entry point; active priorities are in `NEXT_SESSION.md`, `PROJECT_BLUEPRINT.md`, and planning docs |
| `docs/CHANGE_LOG.md` | Historical log; active work history should use `docs/WORK_LOG.md` |

Historical docs should be archived under `docs/archive/`.

## Documentation Policy

Before creating a new documentation file, check whether the content belongs in one of these places:

1. current architecture/status: `docs/PROJECT_BLUEPRINT.md`
2. next work/handoff: `docs/NEXT_SESSION.md`
3. work history: `docs/WORK_LOG.md`
4. future feature planning: `docs/planning/FEATURE_BACKLOG.md`
5. data artifacts/contracts: `docs/planning/DATA_CONTRACTS.md`
6. notification wording/design: `docs/planning/NOTIFICATION_ARCHITECTURE.md`
7. candidate lifecycle/safety: `docs/planning/CANDIDATE_LIFECYCLE.md`
8. operational instructions: `docs/playbook/`
9. decisions: `docs/decisions/`
10. historical material: `docs/archive/`

Avoid creating another roadmap, status, or architecture doc unless it is intentionally temporary or clearly scoped.

## Update Rule

After every meaningful bug fix, feature, audit, or process change:

1. update `docs/WORK_LOG.md`
2. update `docs/NEXT_SESSION.md`
3. update `docs/PROJECT_BLUEPRINT.md` if architecture, roadmap, current status, or operating policy changed
4. update relevant planning docs if future design changed
5. keep tests and audits green

## Safety Rule

If documentation conflicts with code behavior:

1. do not assume the documentation is correct
2. inspect current code and workflows
3. document the current behavior
4. decide whether code or docs should change
5. add tests before changing runtime behavior

## Multi-lane product architecture

The current product architecture and long-term lane separation are documented in:

- [Multi-Lane Product Architecture and Learning System](strategy/MULTI_LANE_PRODUCT_ARCHITECTURE.md)

This document explains the separation between premarket official picks, post-open watch-only opportunities, intraday observations, Monster Hunter / compounder research, reporting, backtesting, learning loops, risk management, and safety gates.
