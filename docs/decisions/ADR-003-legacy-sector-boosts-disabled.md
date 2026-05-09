# ADR-003: Legacy blanket sector boosts remain disabled

Date: 2026-05-09

## Status

Accepted.

## Context

The production scorer still contains legacy SEMI/AI sector boost logic. The current config neutralizes it:

- `sector.semi_boost: 1.0`
- `sector.ai_boost: 0.0`

The config also documents the old unsafe setting:

- `semi_boost: 1.1`
- `ai_boost: 0.2`

Prior backtesting indicated this blanket sector bias was unsafe and could leak performance by making the model too aggressive toward SEMI/AI names without enough validation.

The system now has observe-only theme discovery and theme-to-pick bridge artifacts, but Priority 8 explicitly keeps theme-aware official scoring disabled pending validation and founder approval.

## Decision

Legacy blanket sector boosts remain disabled.

The allowed neutral/defensive bounds are:

- `sector.semi_boost <= 1.0`
- `sector.ai_boost <= 0.0`

Any config attempting to exceed those bounds should fail safety validation.

## Guardrails

`src/scoring_safety.py` enforces:

- legacy sector boost disablement,
- theme-aware scoring disablement by calling `assert_theme_scoring_disabled`.

`tests/test_scoring_safety.py` verifies:

- current `config.yaml` passes,
- old unsafe SEMI/AI boost config fails,
- invalid sector config fails,
- theme scoring enablement still fails,
- the combined scoring safety guard reports disabled/no-production-effect status.

## Consequences

This does not change production scoring behavior. It prevents future config edits from silently reactivating unsafe blanket boosts.

Future theme or sector-aware scoring must go through validation, tests, founder approval, and readiness-gate preservation before it can affect official picks.
