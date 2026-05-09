# System Reliability Repair Plan

Date: 2026-05-09  
Status: Active planning document  
Scope: Reliability hardening after Product Intelligence Priorities 1–8

## Executive Summary

The product-intelligence repair sequence is now implemented through Priority 8:

1. official no-pick explainability,
2. watch-only outcome attribution,
3. performance source separation,
4. late-news score calibration,
5. opening-range quality evaluation,
6. dynamic theme discovery,
7. theme-to-pick bridge,
8. theme-aware scoring disabled guardrails.

The system is now more intelligent and more explainable than before. However, the largest remaining product weakness is reliability/proof:

> The agent can generate useful evidence, but it still cannot always prove whether a no-pick day happened because of discipline, weak candidates, data-provider failure, incomplete pipeline execution, or missing diagnostics.

This plan defines the next reliability-hardening phase before any paper trading, live trading, or production theme-aware scoring.

---

# Product Lag and Current Failure Areas

## 1. Data readiness is not visible enough

### Problem

The product cannot always prove whether the daily pipeline had enough valid data to make official picks.

Observed evidence:

- May 8 required no-pick diagnostic backfill.
- May 8 opening-range observations for TSLA / AMD / QQQ had no forward bars after observation.
- May 9 theme bridge had:
  - no official pick rows,
  - no rejection artifact,
  - no watch-only lane artifacts.

### Product impact

The system cannot always distinguish between:

- disciplined no-pick day,
- no qualified candidates,
- data-provider failure,
- no daily run,
- incomplete pipeline,
- missing diagnostics,
- overly strict filters.

### Needed fix

Add a daily data readiness report.

Expected artifacts:

- `data/data_readiness_YYYY-MM-DD.json`
- `data/data_readiness_YYYY-MM-DD.md`

---

## 2. Candidate lifecycle tracking is incomplete

### Problem

The system does not persist a full candidate journey from universe loading through final selection/rejection.

Missing lifecycle states include:

- `universe_loaded`
- `data_fetch_attempted`
- `data_fetch_failed`
- `quote_available`
- `history_available`
- `scored`
- `filtered`
- `hard_blocked`
- `selected_official`
- `not_selected`
- `watch_only`
- `missing_from_universe`
- `diagnostics_unavailable`

### Product impact

When theme leaders are missing from official picks, the system cannot always answer:

- Were they missing from the universe?
- Did data fetch fail?
- Were they filtered?
- Were they hard-blocked?
- Were they only watch-only?
- Were diagnostics missing?

### Needed fix

Add a candidate lifecycle ledger.

Expected artifacts:

- `data/candidate_lifecycle_YYYY-MM-DD.json`
- `data/candidate_lifecycle_YYYY-MM-DD.md`

---

## 3. Diagnostic artifacts are not guaranteed every day

### Problem

Some days may have no official pick/rejection/watch-only artifacts even when downstream reports exist.

### Product impact

Reports may correctly say artifacts are unavailable, but this still leaves the founder without a full explanation.

### Needed fix

Add daily artifact completeness checks and zero-row diagnostic outputs.

Expected artifacts:

- `data/artifact_completeness_YYYY-MM-DD.json`
- `data/artifact_completeness_YYYY-MM-DD.md`

---

## 4. Legacy blanket sector boost risk remains

### Problem

`config.yaml` currently neutralizes old semi/AI boosts:

- `sector.semi_boost: 1.0`
- `sector.ai_boost: 0.0`

But production code still contains the historical boost path in `src/scorer.py`.

### Product impact

A future config change could accidentally reactivate blanket AI/semi boosting. This conflicts with the current theme-aware scoring guardrails.

### Needed fix

Add a legacy boost safety validator/test.

Acceptance criteria:

- Current config passes.
- Config with `semi_boost > 1.0` fails.
- Config with `ai_boost > 0.0` fails.
- No official scoring behavior changes.

---

## 5. Watch-only intelligence is not yet synthesized into one daily operating brief

### Problem

The system now emits multiple observe-only artifacts:

- watch-only outcomes,
- opening-range quality,
- theme discovery,
- theme-to-pick bridge,
- no-pick diagnostics.

But these are not synthesized into one founder-readable daily brief.

### Product impact

The founder still has to inspect multiple files to answer:

- What happened today?
- Was today data-failed or strategy-driven?
- What did watch-only evidence teach us?
- What themes are emerging?
- What should be monitored tomorrow?

### Needed fix

Add a daily intelligence brief.

Expected artifacts:

- `data/daily_intelligence_brief_YYYY-MM-DD.json`
- `data/daily_intelligence_brief_YYYY-MM-DD.md`

---

## 6. Theme discovery is useful but evidence-light

### Problem

Current theme discovery relies mostly on:

- watchlist text,
- news-signal text,
- pick-log text,
- sentiment,
- source mix,
- breadth from discovered tickers.

Missing evidence layers:

- 1D / 5D / 20D / 60D returns,
- relative strength vs SPY / QQQ,
- sector ETF confirmation,
- new-high counts,
- breakout counts,
- overextension/crowding,
- ticker-level provider failure awareness.

### Product impact

Theme discovery is good enough for observe-only discovery, but not good enough for production scoring.

### Needed fix

Only after data readiness is reliable, extend theme discovery with price and relative-strength confirmation.

---

## 7. Historical validation tooling does not exist yet

### Problem

Priority 8 correctly prevents theme-aware official scoring. But the system still lacks validation tooling to determine whether theme signals have predictive value.

### Missing validation

- theme score vs future return,
- lifecycle state vs win rate,
- crowded momentum vs reversal risk,
- distribution warning vs avoided losses,
- train/test split,
- out-of-sample validation.

### Needed fix

Build a validation harness later.

Expected artifacts:

- `data/theme_signal_validation_YYYY-MM-DD.json`
- `data/theme_signal_validation_YYYY-MM-DD.md`

---

# Confirmed Issues and Current Status

## Issue 1 — Official no-pick explainability was weak

Status: mitigated.

Implemented:

- no-pick diagnostics,
- candidate rejection artifacts,
- May 8 no-pick rejection artifact backfill.

Remaining gap:

- diagnostics are not guaranteed every day.

---

## Issue 2 — Watch-only rows risked contaminating official performance

Status: fixed.

Implemented:

- performance source separation,
- watch-only exclusion tests,
- reporting separation.

Remaining gap:

- watch-only evidence still needs better daily synthesis.

---

## Issue 3 — Late-news scoring was too aggressive

Status: fixed.

Implemented:

- calibrated late-news scores,
- GIG-style risk caps,
- tests and updated artifacts.

Remaining gap:

- continue validating with future outcome data.

---

## Issue 4 — Opening-range quality could be misread when no forward bars existed

Status: fixed.

Implemented:

- `opening_range_quality_status`,
- `data_insufficient_no_forward_bars`,
- volume status `not_evaluable_no_forward_bars`,
- sustained/false breakout null handling.

Remaining gap:

- improve opening-range bar retention so more observations become evaluable.

---

## Issue 5 — Dynamic theme discovery did not exist

Status: fixed observe-only.

Implemented:

- `scripts/discover_themes.py`,
- `data/theme_discovery_YYYY-MM-DD.json`,
- `data/theme_discovery_YYYY-MM-DD.md`.

Remaining gap:

- add price/RS confirmation later.

---

## Issue 6 — Theme-to-pick bridge did not exist

Status: fixed observe-only.

Implemented:

- `scripts/build_theme_pick_bridge.py`,
- `data/theme_pick_bridge_YYYY-MM-DD.json`,
- `data/theme_pick_bridge_YYYY-MM-DD.md`.

Remaining gap:

- bridge quality depends on candidate lifecycle and daily diagnostics.

---

## Issue 7 — Future theme-aware scoring had no explicit disabled-state guardrail

Status: fixed.

Implemented:

- `src/theme_scoring_guardrails.py`,
- ADR-002,
- tests proving production scorers do not import theme artifacts.

Remaining gap:

- add a similar explicit guard for legacy semi/AI sector boosts.

---

# Prioritized Next Tasks

## Priority 9 — Daily Data Readiness Report

Status: next recommended implementation.

### Goal

Determine whether the system was capable of making official picks before judging the pick outcome.

### Artifacts

- `data/data_readiness_YYYY-MM-DD.json`
- `data/data_readiness_YYYY-MM-DD.md`

### Inputs

- daily pick run status,
- candidate rejection diagnostics,
- no-pick report,
- picks log,
- watch-only lane files,
- opening-range observations,
- theme bridge input status,
- provider/bar availability where present.

### Report fields

- `official_pick_readiness_status`
- `data_provider_status`
- `official_pick_count`
- `daily_run_status_available`
- `candidate_diagnostics_available`
- `rejection_artifact_available`
- `watch_only_lanes_available`
- `opening_range_forward_bar_status`
- `no_pick_classification`
- `readiness_warnings`

### No-pick classifications

- `strategy_driven_no_qualified_candidates`
- `data_provider_failure`
- `pipeline_incomplete`
- `diagnostics_missing`
- `market_closed_or_no_run_expected`
- `mixed_or_uncertain`

### Implementation approach

1. Add `scripts/build_data_readiness_report.py`.
2. Load available daily artifacts by date.
3. Count official picks, diagnostics, watch-only lanes, opening-range quality statuses.
4. Avoid fabricating reasons when artifacts are missing.
5. Write JSON and Markdown.
6. Add tests for:
   - complete healthy day,
   - no-pick data failure day,
   - missing diagnostics day,
   - opening-range no-forward-bars day.

### Acceptance criteria

- Missing rejection artifacts are explicitly reported.
- No-forward-bars opening-range cases are identified.
- No-pick days are classified as strategic, data-failed, incomplete, or uncertain.
- No scoring behavior changes.

---

## Priority 10 — Candidate Lifecycle Ledger

### Goal

Track every ticker from universe to final outcome/rejection state.

### Artifacts

- `data/candidate_lifecycle_YYYY-MM-DD.json`
- `data/candidate_lifecycle_YYYY-MM-DD.md`

### Implementation approach

1. Start as a reconstruction report from existing artifacts.
2. Later wire direct lifecycle emission into the daily pick pipeline.
3. Include top theme leaders from theme discovery.
4. Report where each ticker disappeared.

### Acceptance criteria

- For each top theme leader, the report states whether it entered the daily universe.
- If it did not enter, state `missing_from_universe` or `diagnostics_unavailable`.
- If it entered but failed, state exact failure category when available.
- No production scoring effect.

---

## Priority 11 — Daily Diagnostic Artifact Completeness Check

### Goal

Ensure missing artifacts are visible and zero-row diagnostics are preferred over silent absence.

### Artifacts

- `data/artifact_completeness_YYYY-MM-DD.json`
- `data/artifact_completeness_YYYY-MM-DD.md`

### Checks

- daily pick artifact,
- no-pick report,
- candidate rejection artifact,
- daily run status,
- watch-only lane artifacts,
- theme discovery,
- theme bridge,
- data readiness.

### Acceptance criteria

- Missing critical artifacts are clearly marked.
- Missing artifacts do not produce false success.
- The report is observe-only.

---

## Priority 12 — Legacy Sector Boost Safety Guard

### Goal

Prevent accidental reactivation of blanket semi/AI sector boosts.

### Implementation approach

1. Add config safety validator.
2. Reject:
   - `sector.semi_boost > 1.0`
   - `sector.ai_boost > 0.0`
3. Add tests around current and unsafe configs.
4. Optionally add an ADR.

### Acceptance criteria

- Current config passes.
- Old blanket boost config fails.
- No official scoring behavior changes.

---

## Priority 13 — Daily Intelligence Brief

### Goal

Create one founder-readable daily summary.

### Artifacts

- `data/daily_intelligence_brief_YYYY-MM-DD.json`
- `data/daily_intelligence_brief_YYYY-MM-DD.md`

### Sections

- daily operating status,
- official pick status,
- data readiness,
- candidate failure summary,
- watch-only lessons,
- opening-range lessons,
- discovered themes,
- theme-to-pick misses,
- tomorrow observe-only monitoring priorities,
- safety statement.

### Acceptance criteria

- The report explains whether the day was productive, incomplete, or data-failed.
- It provides no buy instructions.
- It does not alter scoring.

---

## Priority 14 — Opening-Range Bar Retention Repair

### Goal

Make more opening-range observations evaluable.

### Problem

May 8 TSLA / AMD / QQQ had no forward bars after observation.

### Implementation approach

1. Inspect scanner bar retention timing.
2. Ensure candidate bar artifacts retain forward bars when possible.
3. Add explicit status when bars stop due to provider failure or market timing.
4. Add tests.

### Acceptance criteria

- More observations become evaluable.
- If bars are unavailable, the reason is explicit.
- No trading behavior changes.

---

## Priority 15 — Provider Failure Taxonomy

### Goal

Standardize provider failure labels across reports.

### Failure taxonomy

- `rate_limited`
- `timeout`
- `empty_response`
- `stale_data`
- `missing_quote`
- `missing_history`
- `missing_intraday_bars`
- `market_closed`
- `symbol_not_found`
- `provider_exception`
- `unknown_provider_failure`

### Acceptance criteria

- Reports use consistent failure labels.
- Unknown failures are captured.
- No scoring behavior changes.

---

## Priority 16 — Theme Discovery Quality Upgrade

### Goal

Add market evidence to theme discovery after data readiness exists.

### Add evidence layers

- 1D / 5D / 20D / 60D returns,
- SPY / QQQ relative strength,
- sector ETF confirmation,
- new-high / breakout counts,
- overextension/crowding,
- provider status.

### Acceptance criteria

- Missing data is reported, not guessed.
- Theme quality improves only when evidence exists.
- No scoring effect.

---

## Priority 17 — Theme Signal Validation Harness

### Goal

Validate whether theme signals have predictive value.

### Artifacts

- `data/theme_signal_validation_YYYY-MM-DD.json`
- `data/theme_signal_validation_YYYY-MM-DD.md`

### Validation questions

- Does `confirmed_leadership` outperform?
- Does `crowded_momentum` reverse?
- Does `distribution_warning` avoid losses?
- Does theme breadth predict next-day outcomes?
- Does theme score correlate with future returns?
- Is the effect out-of-sample?

### Acceptance criteria

- Train/test separation is included.
- Overfitting warning is explicit.
- No scoring is enabled.

---

# Recommended Execution Order

1. Priority 9 — Daily Data Readiness Report
2. Priority 10 — Candidate Lifecycle Ledger
3. Priority 11 — Daily Diagnostic Artifact Completeness Check
4. Priority 12 — Legacy Sector Boost Safety Guard
5. Priority 13 — Daily Intelligence Brief
6. Priority 14 — Opening-Range Bar Retention Repair
7. Priority 15 — Provider Failure Taxonomy
8. Priority 16 — Theme Discovery Quality Upgrade
9. Priority 17 — Theme Signal Validation Harness

## Rationale

Fix observability before adding intelligence.

Fix candidate lifecycle before judging theme misses.

Guard legacy scoring before any future scoring experiments.

Add daily synthesis only after the underlying reports are trustworthy.

Add market evidence and validation only after data readiness is reliable.

---

# Explicit Non-Goals For This Phase

Do not:

- enable paper trading,
- enable live trading,
- enable theme-aware official scoring,
- add theme score boosts,
- loosen readiness gates,
- bypass hard blocks,
- create buy instructions,
- hide missing artifacts,
- treat missing data as negative evidence.

---

# Product Readiness Gate

The product should not advance to paper trading or production theme-aware scoring until:

- daily data readiness is reliable,
- candidate lifecycle is available,
- diagnostic artifacts are guaranteed,
- legacy boost reactivation is guarded,
- daily intelligence brief is stable,
- theme quality includes market evidence,
- validation harness shows out-of-sample evidence,
- founder explicitly approves the next stage.
