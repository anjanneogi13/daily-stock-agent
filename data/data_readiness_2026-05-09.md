# Daily Data Readiness Report

Observe-only. This report does not alter scoring or create picks.

- Date: **2026-05-09**
- Official pick readiness status: **not_ready_pipeline_incomplete**
- No-pick classification: **pipeline_incomplete**
- Data provider status: **no_provider_failure_evidence_in_available_artifacts**
- Official pick count: **0**
- Official tickers: `none`

## Input Status
- daily_run_status_available: **False**
- daily_run_status_parse_errors: **0**
- no_pick_report_available: **False**
- rejection_artifact_available: **False**
- candidate_diagnostics_available: **False**
- picks_log_available: **True**
- theme_bridge_available: **True**
- late_daily_ideas_available: **False**
- opening_range_observations_available: **False**
- intraday_momentum_observations_available: **False**

## Candidate Diagnostics
- path: **data/daily_picks_candidate_rejections_2026-05-09.json**
- available: **False**
- pre_hard_block_candidate_count: **0**
- hard_blocked_candidate_count: **0**
- rejected_candidate_count: **0**
- selected_pick_count: **0**

## Watch-Only Lanes
- **late_daily_ideas**
  - path: **data/late_daily_ideas_2026-05-09.jsonl**
  - exists: **False**
  - rows: **0**
  - parse_errors: **0**
- **opening_range_observations**
  - path: **data/opening_range_observations_2026-05-09.jsonl**
  - exists: **False**
  - rows: **0**
  - parse_errors: **0**
  - observation_count: **0**
  - quality_status_counts: **{}**
  - volume_status_counts: **{}**
  - no_forward_bars_count: **0**
  - has_no_forward_bars: **False**
- **intraday_momentum_observations**
  - path: **data/intraday_momentum_observations_2026-05-09.jsonl**
  - exists: **False**
  - rows: **0**
  - parse_errors: **0**

## Theme Bridge Input Status
- daily_rejection_artifact_exists: **False**
- hard_blocked_candidate_count: **0**
- invalid_watch_only_lines: **{'intraday_momentum_watch_only': 0, 'late_daily_watch_only': 0, 'opening_range_watch_only': 0}**
- picks_log_official_rows_for_date: **0**
- rejected_candidate_count: **0**
- theme_count_available: **626**
- theme_discovery_exists: **True**
- watch_only_lane_count: **0**

## Readiness Warnings
- `daily_run_status_missing`
- `no_pick_report_missing`
- `candidate_rejection_artifact_missing`
- `candidate_diagnostics_missing`
- `watch_only_lanes_missing_or_empty`
- `theme_bridge_reports_missing_daily_inputs`

## Safety
- Observe-only readiness report.
- Does not alter official scoring.
- Does not create picks.
- Does not enable paper or live trading.
- No buy instructions.
