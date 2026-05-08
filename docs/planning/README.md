# Planning Documentation

This folder contains planning-only documentation for Daily Stock Agent.

These documents define future architecture, safety rules, data contracts, notification language, and candidate lifecycle behavior.

They should guide implementation, but they do not change runtime behavior by themselves.

## Documents

### `FEATURE_BACKLOG.md`

Purpose:

- records the long-term product roadmap
- separates current behavior from future features
- organizes work into implementation phases
- preserves deferred/not-yet features without accidentally implementing them

Use this when:

- planning new features
- deciding implementation order
- checking whether an idea is already captured
- making sure future work respects product philosophy

### `DATA_CONTRACTS.md`

Purpose:

- documents expected data artifacts
- defines artifact ownership
- separates official, watch-only, research-only, operational, evidence, learning, and backtest artifacts
- prevents watch-only or research-only data from polluting official statistics

Use this when:

- adding new files under `data/`
- changing artifact schemas
- writing validators
- deciding whether an artifact may affect official pick statistics
- deciding whether an artifact may affect paper/live trading

### `NOTIFICATION_ARCHITECTURE.md`

Purpose:

- defines how user-facing notifications should be classified and worded
- prevents watch-only ideas from sounding like official picks
- proposes a future shared notification renderer and Telegram client
- centralizes disclaimers and safety language

Use this when:

- editing Telegram sender scripts
- adding a new notification type
- changing message wording
- creating shared notification modules
- testing user-facing output

### `CANDIDATE_LIFECYCLE.md`

Purpose:

- defines how market ideas move through lifecycle states
- separates discovered, rejected, watch-only, research-only, paper-candidate, official-pick, and live-candidate states
- defines allowed transitions and readiness gates
- prevents accidental promotion toward action

Use this when:

- creating candidate schemas
- adding intraday or scanner workflows
- evaluating watch-only outcomes
- designing paper-trading readiness gates
- promoting any behavior toward official model picks

## Planning-Only Rule

These documents are not runtime source code.

They should not be treated as implemented behavior unless matching code, tests, and workflows exist.

## Safety Rule

If code behavior conflicts with these planning docs, do not silently assume the docs are correct.

Instead:

1. document the current behavior
2. decide whether implementation should change
3. add tests before changing behavior
4. update the relevant planning doc if the design changes

## Implementation Rule

Before implementing a future feature, check:

1. `FEATURE_BACKLOG.md`
2. `DATA_CONTRACTS.md`
3. `NOTIFICATION_ARCHITECTURE.md`
4. `CANDIDATE_LIFECYCLE.md`

The feature should preserve:

- official vs watch-only separation
- research-only separation
- safe notification language
- explicit data ownership
- no paper/live trading by default
- no automatic promotion without evidence and approval
