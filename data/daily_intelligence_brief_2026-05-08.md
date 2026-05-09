# Daily Intelligence Brief

Observe-only founder operating report. This report does not alter scoring or create picks.

- Date: **2026-05-08**
- Daily operating status: **data_failed_or_degraded**
- Summary: Daily operating evidence indicates data/provider degradation. Official pick quality cannot be judged normally.
- Official pick count: **0**
- Official tickers: `none`
- Readiness status: **not_ready_data_provider_failure**
- No-pick classification: **data_provider_failure**

## Artifact Completeness
- Status: **missing_or_empty_noncritical_artifacts**
- Missing critical: `none`
- Warnings: `theme_discovery, theme_pick_bridge, intraday_momentum_observations`

## Data Readiness
- Provider/data status: **provider_or_market_data_failure_evidence_detected**
- Warnings: `provider_or_market_data_failure_evidence_detected`

## Candidate Lifecycle
- Candidate count: **8**
- State counts: `{'watch_only': 8}`
- Watch-only tickers: `AMD, BLLN, EVC, GIG, PRAA, QQQ, TSLA, ZIM`
- Diagnostics unavailable count: **0**

## Watch-Only Evidence
- Total watch-only rows: **8**
- Unique watch-only tickers: `AMD, BLLN, EVC, GIG, PRAA, QQQ, TSLA, ZIM`
- **late_daily_ideas**: rows=5, exists=True, parse_errors=0
- **opening_range_observations**: rows=3, exists=True, parse_errors=0
- **intraday_momentum_observations**: rows=0, exists=False, parse_errors=0

## No-Pick Diagnostics
- Mode: **monitoring_only**
- Next action: Use watch-only fallback only; do not fabricate official picks.
- Pipeline: `{'capped_count': 2, 'fetched_count': 616, 'filtered_count': 30, 'final_pick_count': 0, 'hard_blocked_count': 2, 'post_hard_block_pick_count': 0, 'pre_hard_block_pick_count': 2, 'scored_count': 329, 'scorer_workers': 4, 'universe_count': 619}`
- Provider summary: `{'stooq': {'attempts': 2, 'successes': 0, 'errors': 2, 'rate_limited': 0, 'empty': 0}, 'yfinance': {'attempts': 1573, 'successes': 1089, 'errors': 482, 'rate_limited': 482, 'empty': 2}}`

## Discovered Themes
- No theme discovery artifact available.

## Theme-to-Pick Bridge
- No theme-to-pick bridge artifact available.

## Tomorrow Observe-Only Monitoring Priorities
- Review data readiness warnings: provider_or_market_data_failure_evidence_detected
- Investigate provider/rate-limit/data-health degradation before judging model quality.
- Review watch-only candidates for lessons, not official performance: AMD, BLLN, EVC, GIG, PRAA, QQQ, TSLA, ZIM

## Scoring Safety
- Safety status: **passed**
- Legacy sector boosts disabled: **True**
- Theme-aware official scoring enabled: **False**
- Production scoring effect: **False**

## Safety
- Observe-only daily intelligence brief.
- Does not alter official scoring.
- Does not create picks.
- Does not enable paper or live trading.
- No buy instructions.
