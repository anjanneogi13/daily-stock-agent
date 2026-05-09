# Daily Artifact Completeness Report

Observe-only. This report does not alter scoring or create picks.

- Date: **2026-05-09**
- Completeness status: **missing_critical_artifacts**
- Official pick count: **0**
- Present artifacts: **4**
- Missing artifacts: **6**
- Missing critical artifacts: **3**
- Warnings: **3**

## Missing Critical Artifacts
- `daily_run_status`
- `no_pick_report`
- `candidate_rejections`

## Warning Artifacts
- `late_daily_ideas`
- `opening_range_observations`
- `intraday_momentum_observations`

## Artifact Matrix
- **daily_run_status** — `missing` / severity=`critical` / required=`True`
  - Path: `data/daily_picks_run_status_2026-05-09.jsonl`
  - Level: `critical`
  - Rows: **0**
  - Parse errors: **0**
- **no_pick_report** — `missing` / severity=`critical` / required=`True`
  - Path: `data/daily_picks_no_pick_report_2026-05-09.json`
  - Level: `conditional_no_pick`
  - Parse error: **False**
- **candidate_rejections** — `missing` / severity=`critical` / required=`True`
  - Path: `data/daily_picks_candidate_rejections_2026-05-09.json`
  - Level: `critical`
  - Parse error: **False**
- **data_readiness** — `present` / severity=`ok` / required=`True`
  - Path: `data/data_readiness_2026-05-09.json`
  - Level: `critical`
  - Parse error: **False**
- **candidate_lifecycle** — `present` / severity=`ok` / required=`True`
  - Path: `data/candidate_lifecycle_2026-05-09.json`
  - Level: `critical`
  - Parse error: **False**
- **theme_discovery** — `present` / severity=`ok` / required=`False`
  - Path: `data/theme_discovery_2026-05-09.json`
  - Level: `observe_only`
  - Parse error: **False**
- **theme_pick_bridge** — `present` / severity=`ok` / required=`False`
  - Path: `data/theme_pick_bridge_2026-05-09.json`
  - Level: `observe_only`
  - Parse error: **False**
- **late_daily_ideas** — `missing` / severity=`warning` / required=`False`
  - Path: `data/late_daily_ideas_2026-05-09.jsonl`
  - Level: `watch_only`
  - Rows: **0**
  - Parse errors: **0**
- **opening_range_observations** — `missing` / severity=`warning` / required=`False`
  - Path: `data/opening_range_observations_2026-05-09.jsonl`
  - Level: `watch_only`
  - Rows: **0**
  - Parse errors: **0**
- **intraday_momentum_observations** — `missing` / severity=`warning` / required=`False`
  - Path: `data/intraday_momentum_observations_2026-05-09.jsonl`
  - Level: `watch_only`
  - Rows: **0**
  - Parse errors: **0**

## Safety
- Observe-only artifact completeness report.
- Does not alter official scoring.
- Does not create picks.
- Does not enable paper or live trading.
- No buy instructions.
