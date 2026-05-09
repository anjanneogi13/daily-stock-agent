# ADR-002: Theme-aware official scoring remains disabled pending validation

Date: 2026-05-09

## Status

Accepted.

## Context

The system now has observe-only theme intelligence:

- dynamic theme discovery,
- theme-to-pick bridge reporting,
- watch-only outcome attribution.

These artifacts can reveal whether the agent is missing leadership themes, but they are not yet validated enough to influence official picks.

The product repair plan requires strict prerequisites before theme intelligence can affect official scoring:

- historical validation,
- forward observation,
- train/test discipline,
- no overfitting,
- clear tests,
- founder approval,
- no readiness-gate bypass.

## Decision

Theme-aware official scoring is disabled.

Theme artifacts may be generated and analyzed observe-only, but they must not:

- boost official scores,
- modify composite scoring,
- create picks,
- bypass hard blocks,
- bypass readiness gates,
- enable paper trading,
- enable live trading,
- provide buy instructions.

Future scoring fields are reserved only for post-validation work:

- `theme_strength_score`
- `theme_breadth_score`
- `theme_quality_score`
- `theme_overextension_penalty`
- `theme_confirmation_count`

## Guardrails

`src/theme_scoring_guardrails.py` records the disabled status and required prerequisites.

`tests/test_theme_scoring_guardrails.py` verifies:

- default theme-aware scoring status is disabled,
- configs attempting to enable theme scoring are rejected,
- production scorer modules do not import theme discovery or bridge artifacts,
- `config.yaml` does not enable theme scoring.

## Consequences

The agent can learn from theme artifacts without corrupting official performance or quietly making the model more aggressive.

Production scoring can only change after a future explicit implementation that includes validation evidence, tests, founder approval, and readiness-gate preservation.
