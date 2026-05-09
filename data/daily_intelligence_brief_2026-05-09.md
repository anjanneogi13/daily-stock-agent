# Daily Intelligence Brief

Observe-only founder operating report. This report does not alter scoring or create picks.

- Date: **2026-05-09**
- Daily operating status: **incomplete_pipeline**
- Summary: Daily operating evidence is incomplete. Do not interpret the day as a strategy-driven no-pick outcome.
- Official pick count: **0**
- Official tickers: `none`
- Readiness status: **not_ready_pipeline_incomplete**
- No-pick classification: **pipeline_incomplete**

## Artifact Completeness
- Status: **missing_critical_artifacts**
- Missing critical: `daily_run_status, no_pick_report, candidate_rejections`
- Warnings: `late_daily_ideas, opening_range_observations, intraday_momentum_observations`

## Data Readiness
- Provider/data status: **no_provider_failure_evidence_in_available_artifacts**
- Warnings: `daily_run_status_missing, no_pick_report_missing, candidate_rejection_artifact_missing, candidate_diagnostics_missing, watch_only_lanes_missing_or_empty, theme_bridge_reports_missing_daily_inputs`

## Candidate Lifecycle
- Candidate count: **98**
- State counts: `{'diagnostics_unavailable': 98}`
- Watch-only tickers: `none`
- Diagnostics unavailable count: **98**

## Watch-Only Evidence
- Total watch-only rows: **0**
- Unique watch-only tickers: `none`
- **late_daily_ideas**: rows=0, exists=False, parse_errors=0
- **opening_range_observations**: rows=0, exists=False, parse_errors=0
- **intraday_momentum_observations**: rows=0, exists=False, parse_errors=0

## No-Pick Diagnostics
- No no-pick report available.

## Discovered Themes
- **ai** — state=`emerging_theme`, score=`100.0`, breadth=`25`, tickers=`AAPL, AIIO, ALAB, ANET, APLD, ARM, ASML, AVGO, CDNS, CRDO`
- **semi** — state=`candidate_theme`, score=`97.19`, breadth=`21`, tickers=`ADI, ALAB, ANET, ARM, ASML, AVGO, CDNS, CRDO, DELL, LRCX`
- **semi ai** — state=`candidate_theme`, score=`95.02`, breadth=`15`, tickers=`ALAB, ANET, ARM, ASML, AVGO, CDNS, CRDO, LRCX, MPWR, NVDA`
- **selling** — state=`distribution_warning`, score=`92.48`, breadth=`12`, tickers=`ARHS, DCOY, DV, EFR, FLOC, HRTG, IREN, MSFT, OWLT, PAX`
- **pharmaceuticals** — state=`confirmed_leadership`, score=`90.15`, breadth=`7`, tickers=`ADIL, ANIP, ARWR, LGND, MIRM, RYTM, TNXP`
- **momentum** — state=`confirmed_leadership`, score=`88.78`, breadth=`9`, tickers=`CART, ENOV, GCMG, GCT, IIIV, MIRM, RYTM, SEZL, SMCI`
- **health** — state=`emerging_theme`, score=`88.75`, breadth=`9`, tickers=`AGL, ARDT, BTSG, CLOV, CVS, ELAN, LFST, OMDA, WHR`
- **massive** — state=`confirmed_leadership`, score=`86.31`, breadth=`8`, tickers=`BLLN, CRI, DCH, EVC, ONC, PRAA, TKO, WBD`

## Theme-to-Pick Bridge
- Themes analyzed: **12**
- Gap reason counts: `{'missing_from_official_and_watch_only': 12, 'no_daily_rejection_artifact_available': 12}`
- **ai** — official=0, rejected=0, hard_blocked=0, watch_only=0, gaps=`missing_from_official_and_watch_only, no_daily_rejection_artifact_available`
- **semi** — official=0, rejected=0, hard_blocked=0, watch_only=0, gaps=`missing_from_official_and_watch_only, no_daily_rejection_artifact_available`
- **semi ai** — official=0, rejected=0, hard_blocked=0, watch_only=0, gaps=`missing_from_official_and_watch_only, no_daily_rejection_artifact_available`
- **selling** — official=0, rejected=0, hard_blocked=0, watch_only=0, gaps=`missing_from_official_and_watch_only, no_daily_rejection_artifact_available`
- **pharmaceuticals** — official=0, rejected=0, hard_blocked=0, watch_only=0, gaps=`missing_from_official_and_watch_only, no_daily_rejection_artifact_available`
- **momentum** — official=0, rejected=0, hard_blocked=0, watch_only=0, gaps=`missing_from_official_and_watch_only, no_daily_rejection_artifact_available`

## Tomorrow Observe-Only Monitoring Priorities
- Restore missing critical daily artifacts: daily_run_status, no_pick_report, candidate_rejections
- Review data readiness warnings: daily_run_status_missing, no_pick_report_missing, candidate_rejection_artifact_missing, candidate_diagnostics_missing, watch_only_lanes_missing_or_empty, theme_bridge_reports_missing_daily_inputs
- Trace 98 diagnostics-unavailable candidates/theme leaders after pipeline diagnostics are restored.
- Observe top discovered themes without score boosts: ai, semi, semi ai, selling, pharmaceuticals
- Review theme-to-pick gaps: missing_from_official_and_watch_only=12, no_daily_rejection_artifact_available=12

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
