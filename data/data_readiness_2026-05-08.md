# Daily Data Readiness Report

Observe-only. This report does not alter scoring or create picks.

- Date: **2026-05-08**
- Official pick readiness status: **not_ready_data_provider_failure**
- No-pick classification: **data_provider_failure**
- Data provider status: **provider_or_market_data_failure_evidence_detected**
- Official pick count: **0**
- Official tickers: `none`

## Input Status
- daily_run_status_available: **True**
- daily_run_status_parse_errors: **0**
- no_pick_report_available: **True**
- rejection_artifact_available: **True**
- candidate_diagnostics_available: **True**
- picks_log_available: **True**
- theme_bridge_available: **False**
- late_daily_ideas_available: **True**
- opening_range_observations_available: **True**
- intraday_momentum_observations_available: **False**

## Candidate Diagnostics
- path: **data/daily_picks_candidate_rejections_2026-05-08.json**
- available: **True**
- pre_hard_block_candidate_count: **0**
- hard_blocked_candidate_count: **0**
- rejected_candidate_count: **0**
- selected_pick_count: **0**

## Watch-Only Lanes
- **late_daily_ideas**
  - path: **data/late_daily_ideas_2026-05-08.jsonl**
  - exists: **True**
  - rows: **5**
  - parse_errors: **0**
- **opening_range_observations**
  - path: **data/opening_range_observations_2026-05-08.jsonl**
  - exists: **True**
  - rows: **3**
  - parse_errors: **0**
  - observation_count: **3**
  - quality_status_counts: **{'unknown': 3}**
  - volume_status_counts: **{'unknown': 3}**
  - no_forward_bars_count: **0**
  - has_no_forward_bars: **False**
- **intraday_momentum_observations**
  - path: **data/intraday_momentum_observations_2026-05-08.jsonl**
  - exists: **False**
  - rows: **0**
  - parse_errors: **0**

## Theme Bridge Input Status
- No theme bridge input status available.

## Readiness Warnings
- `provider_or_market_data_failure_evidence_detected`

## Safety
- Observe-only readiness report.
- Does not alter official scoring.
- Does not create picks.
- Does not enable paper or live trading.
- No buy instructions.
