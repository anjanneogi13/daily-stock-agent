# System Reliability Repair Plan

Date: 2026-05-09  
Status: Active planning document  
Scope: Post Priority 1–8 product hardening

## Executive Summary

The system has now implemented the first product-intelligence repair sequence through Priority 8:

1. no-pick explainability,
2. watch-only outcome attribution,
3. performance source separation,
4. late-news score calibration,
5. opening-range quality evaluation,
6. dynamic theme discovery,
7. theme-to-pick bridge,
8. disabled-state guardrails for future theme-aware scoring.

The next product risk is no longer simply lack of intelligence. The next risk is reliability:

> The system can generate useful evidence, but it still cannot always prove whether it made no picks because of discipline, because candidates were weak, or because data/pipeline/candidate lifecycle failed.

This plan prioritizes the next repair tasks required before paper trading, live trading, or production theme-aware scoring.

---

# Current Product Lag

## 1. Data readiness is not visible enough

The system can fail to produce official picks without enough proof of whether the cause was strategic discipline or data failure.

Observed evidence:

- May 8 official no-pick outcome required backfilled no-pick diagnostics.
- Opening-range observations for TSLA / AMD / QQQ had no forward bars after observation.
- May 9 theme bridge had no official pick rows, no rejection artifact, and no watch-only lane artifacts for that date.

Impact:

- The product cannot always distinguish between:
  - no good candidates,
  - failed data provider,
  - no daily run,
  - incomplete pipeline,
  - lost diagnostics,
  - overly strict filters.

Required fix:

- Add an explicit daily data-readiness artifact.

---

## 2. Candidate lifecycle tracking is incomplete

The system does not yet persist a full state transition trail for each candidate.

Missing lifecycle states include:

- universe loaded,
- data fetch attempted,
- data fetch failed,
- quote available,
- history available,
- scored,
- filtered,
- hard-blocked,
- selected,
- not selected,
- watch-only,
- no-candidate evidence.

Impact:

- Theme bridge can identify missing theme leaders, but cannot always say why they were missing.
- No-pick reports are better than before, but candidate-level lifecycle evidence is not guaranteed.

Required fix:

- Add a candidate lifecycle ledger.

---

## 3. Diagnostic artifacts are not guaranteed every day

May 9 had theme artifacts but no official pick/rejection/watch-only artifacts for the same date.

Impact:

- Reports can correctly say "artifact unavailable", but this is still a product gap.
- The system should guarantee diagnostic artifacts even when no picks are generated or when a lane produces zero candidates.

Required fix:

- Add daily artifact completeness checks and zero-row diagnostic outputs.

---

## 4. Legacy blanket sector boost risk remains

The config currently neutralizes old semi/AI boosts:

- `sector.semi_boost: 1.0`
- `sector.ai_boost: 0.0`

But production code still contains the historical boost path in `src/scorer.py`.

Impact:

- A future config change could accidentally reactivate blanket AI/semi boosting.
- This conflicts with the current theme-aware scoring guardrails.

Required fix:

- Add a safety validator/test that prevents blanket sector boosts from being enabled without explicit approval.

---

## 5. Watch-only intelligence is still not synthesized into a daily operating brief

Current observe-only artifacts exist separately:

- watch-only outcomes,
- opening-range quality,
- theme discovery,
- theme-to-pick bridge,
- no-pick diagnostics.

Impact:

- The founder still has to inspect multiple files to answer:
  - What happened today?
  - What did the system learn?
  - What should be monitored tomorrow?
  - Was the no-pick outcome good discipline or a data failure?

Required fix:

- Add a daily intelligence brief that synthesizes all observe-only and diagnostic artifacts.

---

## 6. Theme discovery is useful but still evidence-light

Theme discovery currently relies mostly on:

- watchlist text,
- news-signal text,
- pick-log text,
- source mix,
- sentiment,
- breadth from discovered tickers.

Missing evidence layers:

- 1D / 5D / 20D / 60D returns,
- SPY / QQQ relative strength,
- sector ETF confirmation,
- new-high counts,
- breadth across related names,
- overextension/crowding,
- provider failure awareness at ticker level.

Impact:

- Theme radar is good enough for observe-only discovery, but not enough for scoring.

Required fix:

- Add price/relative-strength confirmation only after data readiness is reliable.

---

## 7. Historical validation tooling does not exist yet

Priority 8 correctly disabled production theme-aware scoring. However, the tooling needed to eventually validate theme signals does not exist.

Missing validation:

- theme score vs future returns,
- lifecycle state vs win rate,
- crowded momentum vs reversal risk,
- distribution warning vs avoided losses,
- train/test split,
- out-of-sample forward observation.

Required fix:

- Build a validation harness later, after data readiness and lifecycle tracking are fixed.

---

# Confirmed Issues and Bugs Found

## Fixed or mitigated already

### 1. Official no-pick explainability was weak

Status: mitigated.

Implemented:

- no-pick diagnostics,
- candidate rejection artifacts,
- May 8 no-pick rejection artifact backfill.

Remaining gap:

- diagnostics are not guaranteed every day.

---

### 2. Watch-only evidence risked contaminating official performance

Status: fixed.

Implemented:

- performance source separation,
- watch-only exclusion tests,
- reporting separation.

Remaining gap:

- watch-only evidence still needs better synthesis into daily intelligence.

---

### 3. Late-news scoring was too aggressive

Status: fixed.

Implemented:

- calibrated late-news scores,
- GIG-style risk caps,
- tests and generated artifact updates.

Remaining gap:

- calibration should continue to be validated with more outcome data.

---

### 4. Opening-range quality could be misread when no forward bars existed

Status: fixed.

Implemented:

- `opening_range_quality_status`,
- `data_insufficient_no_forward_bars`,
- volume status `not_evaluable_no_forward_bars`,
- sustained/false breakout null handling.

Remaining gap:

- opening-range bar retention should be improved so more observations are evaluable.

---

### 5. Dynamic theme discovery did not exist

Status: fixed observe-only.

Implemented:

- `scripts/discover_themes.py`,
- `data/theme_discovery_YYYY-MM-DD.json`,
- `data/theme_discovery_YYYY-MM-DD.md`.

Remaining gap:

- needs price/RS confirmation before use in scoring.

---

### 6. Theme-to-pick bridge did not exist

Status: fixed observe-only.

Implemented:

- `scripts/build_theme_pick_bridge.py`,
- bridge report artifacts.

Remaining gap:

- bridge quality depends on daily candidate lifecycle and rejection artifacts existing.

---

### 7. Future theme-aware scoring had no explicit disabled-state guardrail

Status: fixed.

Implemented:

- `src/theme_scoring_guardrails.py`,
- ADR-002,
- tests proving production scoring does not import theme artifacts.

Remaining gap:

- legacy sector boost config should get a similar explicit guard.

---

# Prioritized Next Tasks

## Priority 9 — Daily Data Readiness Report

Status: next recommended implementation.

Goal:

Determine whether the system was capable of making official picks before judging the pick outcome.

Artifacts:

- `data/data_readiness_YYYY-MM-DD.json`
- `data/data_readiness_YYYY-MM-DD.md`

Inputs:

- daily pick run status,
- candidate rejection diagnostics,
- market data health artifacts if present,
- scanner status rows,
- opening-range bar availability,
- watch-only lane files,
- theme bridge input status,
- provider error logs if available.

Report fields:

- `official_pick_readiness_status`
- `data_provider_status`
- `universe_loaded_count`
- `quote_success_count`
- `quote_failure_count`
- `history_success_count`
- `history_failure_count`
- `bar_sequence_available_count`
- `bar_sequence_missing_count`
- `candidate_diagnostics_available`
- `rejection_artifact_available`
- `watch_only_lanes_available`
- `no_pick_classification`

Possible no-pick classifications:

- `strategy_driven_no_qualified_candidates`
- `data_provider_failure`
- `pipeline_incomplete`
- `diagnostics_missing`
- `market_closed_or_no_run_expected`
- `mixed_or_uncertain`

Implementation approach:

1. Add `scripts/build_data_readiness_report.py`.
2. Load existing daily artifacts by date.
3. Summarize availability and counts.
4. Avoid fabricating reasons when artifacts are missing.
5. Write JSON and Markdown.
6. Add tests with:
   - complete healthy day,
   - no-pick data failure day,
   - missing diagnostics day,
   - opening-range no-forward-bars day.

Acceptance criteria:

- A day with missing rejection artifacts is explicitly marked.
- A day with no forward bars is marked data-insufficient.
- A day with no official picks is classified as either strategy-driven, data-failed, incomplete, or uncertain.
- No scoring behavior changes.

---

## Priority 10 — Candidate Lifecycle Ledger

Goal:

Track every ticker from universe to final outcome/rejection state.

Artifacts:

- `data/candidate_lifecycle_YYYY-MM-DD.json`
- `data/candidate_lifecycle_YYYY-MM-DD.md`

Lifecycle states:

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

Implementation approach:

1. Start as a report builder that reconstructs lifecycle from existing artifacts.
2. Later wire direct lifecycle emission into the daily pick pipeline.
3. Include theme leaders from theme discovery so the system can say where leaders disappeared.
4. Add tests for each lifecycle state.

Acceptance criteria:

- For each top theme leader, report whether it entered the daily universe.
- If it did not enter, state `missing_from_universe` or `diagnostics_unavailable`.
- If it entered but failed, state exact failure category when available.
- No production scoring effect.

---

## Priority 11 — Daily Diagnostic Artifact Completeness Check

Goal:

Guarantee the product emits zero-row diagnostics instead of silently missing artifacts.

Artifacts:

- `data/artifact_completeness_YYYY-MM-DD.json`
- `data/artifact_completeness_YYYY-MM-DD.md`

Checks:

- daily picks artifact exists,
- daily no-pick report exists if no picks,
- candidate rejection artifact exists,
- daily run status exists,
- watch-only lane artifacts exist or zero-row status exists,
- theme discovery exists,
- theme bridge exists,
- data readiness exists.

Implementation approach:

1. Add `scripts/check_daily_artifact_completeness.py`.
2. Generate a missing/present matrix.
3. Mark missing critical artifacts.
4. Add tests for expected missing/present combinations.

Acceptance criteria:

- May 9-like case clearly reports no official/rejection/watch-only artifacts.
- Missing artifacts do not cause false success.
- The report is observe-only.

---

## Priority 12 — Legacy Sector Boost Safety Guard

Goal:

Prevent accidental reactivation of blanket semi/AI sector boosts.

Risk source:

- `src/scorer.py` still contains sector boost logic.
- `config.yaml` currently neutralizes it.

Implementation options:

1. Add config safety validator that rejects:
   - `sector.semi_boost > 1.0`
   - `sector.ai_boost > 0.0`
2. Add tests around `config.yaml`.
3. Optionally add an ADR documenting why blanket boosts are disabled.
4. Later remove dead boost code if safe.

Acceptance criteria:

- Current config passes.
- Config attempting old blanket boost fails a guardrail test.
- No official scoring behavior changes.
- No theme-aware scoring is enabled.

---

## Priority 13 — Daily Intelligence Brief

Goal:

Create one founder-readable report summarizing what happened today.

Artifacts:

- `data/daily_intelligence_brief_YYYY-MM-DD.json`
- `data/daily_intelligence_brief_YYYY-MM-DD.md`

Inputs:

- no-pick diagnostics,
- data readiness report,
- candidate lifecycle ledger,
- watch-only outcomes,
- opening-range quality,
- theme discovery,
- theme-pick bridge,
- artifact completeness report.

Sections:

- daily operating status,
- official pick status,
- data readiness,
- candidate failure summary,
- watch-only lessons,
- opening-range lessons,
- discovered themes,
- theme-to-pick misses,
- tomorrow's observe-only monitoring priorities,
- safety statement.

Acceptance criteria:

- The report explains whether the day was productive, incomplete, or data-failed.
- It does not provide buy instructions.
- It does not alter scoring.

---

## Priority 14 — Theme Discovery Quality Upgrade

Goal:

Improve theme discovery quality with market evidence.

Prerequisite:

- Priority 9 data readiness must exist.

Add evidence layers:

- 1D / 5D / 20D / 60D returns,
- relative strength vs SPY / QQQ,
- sector ETF confirmation,
- new-high / breakout counts,
- overextension/crowding,
- provider failure status.

Implementation approach:

1. Extend `scripts/discover_themes.py`.
2. Keep all fields observe-only.
3. Add provider-status fields per evidence layer.
4. Add tests for missing-provider behavior.

Acceptance criteria:

- Theme status improves only when market evidence exists.
- Missing data is reported, not guessed.
- No scoring effect.

---

## Priority 15 — Theme Signal Validation Harness

Goal:

Determine whether theme signals have predictive value.

Artifacts:

- `data/theme_signal_validation_YYYY-MM-DD.json`
- `data/theme_signal_validation_YYYY-MM-DD.md`

Validation questions:

- Does `confirmed_leadership` outperform?
- Does `crowded_momentum` reverse?
- Does `distribution_warning` avoid losses?
- Does theme breadth predict next-day outcomes?
- Does theme score correlate with future returns?
- Is the effect out-of-sample?

Implementation approach:

1. Build `scripts/validate_theme_signals.py`.
2. Use historical theme artifacts and pick/watch-only outcomes.
3. Require train/test split.
4. Do not write any scoring config.
5. Add tests using synthetic historical data.

Acceptance criteria:

- Validation report includes train/test separation.
- It explicitly warns against overfitting.
- It does not enable scoring.

---

## Priority 16 — Opening-Range Bar Retention Repair

Goal:

Make opening-range outcomes more evaluable.

Problem:

- May 8 TSLA / AMD / QQQ observations had no forward bars after observation.

Implementation approach:

1. Inspect scanner bar retention timing.
2. Ensure candidate bar artifact includes enough forward bars when possible.
3. Add status when bars intentionally stop because market is closed or provider failed.
4. Add tests for retained post-observation bars.

Acceptance criteria:

- More opening-range observations become evaluable.
- If bars are unavailable, the reason is explicit.
- No trading behavior changes.

---

## Priority 17 — Provider Failure Taxonomy

Goal:

Standardize data-provider failure reasons across reports.

Failure reason taxonomy:

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

Implementation approach:

1. Add shared helper module for provider failure labels.
2. Adopt in data readiness, lifecycle, no-pick diagnostics, and opening-range quality.
3. Add tests for mapping raw errors to normalized reasons.

Acceptance criteria:

- Reports use consistent failure labels.
- Unknown failures are still captured.
- No scoring behavior changes.

---

# Recommended Execution Order

1. Priority 9 — Daily Data Readiness Report
2. Priority 10 — Candidate Lifecycle Ledger
3. Priority 11 — Daily Diagnostic Artifact Completeness Check
4. Priority 12 — Legacy Sector Boost Safety Guard
5. Priority 13 — Daily Intelligence Brief
6. Priority 16 — Opening-Range Bar Retention Repair
7. Priority 17 — Provider Failure Taxonomy
8. Priority 14 — Theme Discovery Quality Upgrade
9. Priority 15 — Theme Signal Validation Harness

Rationale:

- Fix observability before adding intelligence.
- Fix candidate lifecycle before judging theme misses.
- Fix legacy boost safety before any future scoring experiments.
- Add daily synthesis only after underlying reports are trustworthy.
- Add market evidence and validation only after data readiness is reliable.

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

