# Product Intelligence Repair Plan

**Date created:** 2026-05-09  
**Mode:** planning / product architecture / monitoring-only repair plan  
**Status:** active next-priority plan

## Purpose

This plan documents the fundamental product-intelligence fixes required before paper trading, live trading, public launch, or major feature expansion.

The goal is not to make the agent more aggressive. The goal is to make the agent more explainable, evidence-driven, dynamically theme-aware, and able to learn from watch-only observations without corrupting official performance statistics.

Core principle:

> Trust is the product.  
> The company can win if the product becomes trusted before it becomes automated.

## Triggering evidence

The 2026-05-08 operating day exposed several important product gaps.

Verified observations:

- Official premarket Daily Picks produced **0 official picks**.
- `data/picks_log.csv` had **0 rows** for 2026-05-08.
- The no-pick safety path worked and generated:
  - `data/daily_picks_no_pick_report_2026-05-08.json`
  - `data/daily_picks_no_pick_report_2026-05-08.md`
  - `data/daily_picks_run_status_2026-05-08.jsonl`
- Pipeline summary showed:
  - `universe_count=619`
  - `fetched_count=616`
  - `scored_count=329`
  - `filtered_count=30`
  - `pre_hard_block_pick_count=2`
  - `hard_blocked_count=2`
  - `final_pick_count=0`
- Market-data health showed yfinance pressure:
  - yfinance attempts: `1573`
  - yfinance successes: `1089`
  - yfinance errors/rate-limits: `482`
- OHLCV mostly succeeded:
  - OHLCV attempts: `626`
  - OHLCV successes: `622`
- Stooq fallback attempted only two TSX-style symbols and failed both.
- Late watch-only ideas were generated:
  - BLLN
  - EVC
  - GIG
  - PRAA
  - ZIM
- Opening-range watch-only observations existed:
  - TSLA
  - AMD
  - QQQ
- Opening-range bar artifacts existed for 2026-05-08:
  - `data/opening_range_bars/2026-05-08/AMD.jsonl`
  - `data/opening_range_bars/2026-05-08/QQQ.jsonl`
  - `data/opening_range_bars/2026-05-08/TSLA.jsonl`
- Existing watch-only learning report code exists:
  - `scripts/daily_watch_only_learning_report.py`
- But report artifacts were missing for 2026-05-08:
  - `data/watch_only_learning_report_2026-05-08.json`
  - `data/watch_only_learning_report_2026-05-08.md`
- News/outcome report artifacts were also missing for 2026-05-08:
  - `data/news_signal_outcomes_2026-05-08.jsonl`
  - `data/news_signal_evidence_report_2026-05-08.md`

## Product diagnosis

The safety architecture behaved correctly:

- no official picks were fabricated,
- paper trading stayed disabled,
- live trading stayed disabled,
- watch-only ideas did not enter official pick statistics.

However, the product-intelligence layer is incomplete.

Main gaps:

1. Official no-pick decisions are not explainable enough from the May 8 artifacts.
2. Watch-only ideas are generated but not fully outcome-attributed.
3. Late-news scores are overconfident.
4. GIG exposed a corporate-action / business-combination scoring weakness.
5. Opening-range observations need outcome-quality analysis.
6. The performance report source needs clearer separation.
7. The product lacks dynamic theme discovery.
8. Theme intelligence must be discovered from evidence, not hardcoded by the founder.

## Non-goals

Do **not** use this plan to justify:

- paper trading,
- live trading,
- relaxing official safety gates,
- forcing daily picks,
- treating watch-only outcomes as official performance,
- hardcoding “AI/semi is hot” as a permanent scoring boost,
- adding Finnhub before yfinance/Stooq telemetry proves it is necessary,
- mixing research-only, watch-only, and official pick statistics.

## Priority list

### Priority 1 — Official no-pick root-cause explainability

Goal:

When official Daily Picks produces zero picks, the system must explain why.

Required questions:

- Which finalists were hard-blocked?
- Why were they hard-blocked?
- Which high-interest names were scanned?
- Which were missing from the universe?
- Which had provider failures?
- Which were filtered?
- Which were capped?
- Which were rejected?
- Which were watch-only only?

Expected artifacts:

- `data/daily_picks_no_pick_report_YYYY-MM-DD.json`
- `data/daily_picks_no_pick_report_YYYY-MM-DD.md`
- `data/daily_picks_candidate_rejections_YYYY-MM-DD.json`
- `data/daily_picks_candidate_rejections_YYYY-MM-DD.md`

Current state:

- Code support appears to exist in `main.py`.
- Tests exist in `tests/test_daily_picks_no_pick_diagnostics.py`.
- May 8 artifacts did not include candidate-level diagnostics, likely because the real run occurred before the latest diagnostic code was active.
- Next zero-pick official-window run must validate this.

Implementation direction:

- Validate current diagnostics with tests/smoke.
- Future failure run-status rows now include compact no-pick diagnostics via `--include-diagnostics`.
- Candidate rejection markdown now includes pre-hard-block finalists and hard-blocked finalist details.
- Pipeline-only historical reports can now infer the primary no-pick cause for run-status diagnostics.
- May 8 candidate rejection artifacts were backfilled honestly from retained pipeline counts only; finalist ticker details were unavailable and not fabricated.
- If missing, ensure no-pick artifacts include:
  - finalist tickers,
  - score summary,
  - sector/tag,
  - hard-block type,
  - hard-block reason,
  - provider-health impact,
  - no-pick primary cause,
  - secondary causes.

Safety:

- No official picks should be fabricated.
- No paper/live trading behavior should change.

---

### Priority 2 — Watch-only outcome attribution v1

Goal:

Let the agent learn from late and intraday watch-only ideas without contaminating official performance.

Inputs:

- `data/late_daily_ideas_YYYY-MM-DD.jsonl`
- `data/opening_range_observations_YYYY-MM-DD.jsonl`
- `data/opening_range_bars/YYYY-MM-DD/*.jsonl`
- future structured intraday momentum observations, if present

Must evaluate:

- BLLN
- EVC
- GIG
- PRAA
- ZIM
- TSLA opening-range
- AMD opening-range
- QQQ opening-range

Expected artifacts:

- `data/watch_only_outcomes_YYYY-MM-DD.jsonl`
- `data/watch_only_outcome_report_YYYY-MM-DD.md`

Current implementation notes:

- `scripts/build_watch_only_outcomes.py` builds monitoring-only outcome artifacts.
- Late daily watch-only ideas are evaluated from retained same-day range only.
- Late range-only TP/SL ordering is marked unknown when both levels are inside the range.
- Opening-range observations use retained bar artifacts when forward bars after the observation are available.
- Opening-range rows with retained bars but no forward bars after the observation are marked as data-insufficient, not failed trades.
- May 8 watch-only outcome artifacts were generated for BLLN, EVC, GIG, PRAA, ZIM, TSLA, AMD, and QQQ.

Outcome fields should include:

- ticker,
- source,
- observation type,
- first observed timestamp,
- reference/entry observation price,
- stop-loss observation level,
- take-profit observation level,
- max favorable excursion,
- max adverse excursion,
- whether TP hit,
- whether SL hit,
- which hit first,
- end-of-window return,
- data sufficiency status,
- safety flags.

Safety:

- Must not write `data/picks_log.csv`.
- Must not write `data/signal_journal.jsonl`.
- Must not write `data/learning_journal.jsonl`.
- Must not create paper trades.
- Must not enable live trading.
- Must clearly label all outputs as watch-only evidence.

---

### Priority 3 — Performance report source separation audit

Goal:

Make performance reporting unambiguous and trust-preserving.

Problem:

A performance message such as:

- `7 wins · 4 losses · +$845.38`

can confuse users if the same day had zero official premarket picks.

Required separation:

- official daily picks performance,
- old swing-position monitoring,
- watch-only late ideas,
- opening-range observations,
- generic intraday observations,
- simulated/paper-like calculations,
- research-only outcomes.

Expected work:

- Audit scripts that generate performance messages.
- Identify source artifacts.
- Ensure reports clearly state what is included and excluded.
- Prevent users from mistaking watch-only or legacy monitored-position results for same-day official pick performance.

Current implementation notes:

- `src/performance_source_separation.py` centralizes source-separation wording and watch-only row detection.
- `src/performance_tracker.py` excludes `watch_only` rows from performance metrics.
- Performance metrics include `source_separation.excluded_watch_only_rows`.
- Weekly report-card messages disclose that performance uses closed non-watch-only `data/picks_log.csv` rows.
- Layman weekly/monthly/evening/yearly performance messages filter watch-only rows and disclose exclusions.
- Watch-only late ideas, opening-range observations, research-only outcomes, and paper-like simulations are explicitly excluded from performance copy.

Safety:

- No blending of official and watch-only statistics.
- No paper-trading implication.

---

### Priority 4 — Late-news score calibration and GIG-style risk caps

Goal:

Prevent overconfident late-news scores and corporate-action traps.

Evidence:

All May 8 late-watch-only ideas displayed `100/100`, even though underlying tradeable scores were `0.88–0.95`.

GIG exposed a risk:

- headline included business-combination / merger-sub language,
- catalyst was classified as `standard`,
- display score became `100/100`.

Required changes:

- News-only ideas should not casually reach `100/100`.
- `score_delta` should not blindly push display score to 100.
- Corporate-action / SPAC / business-combination / merger-sub / deal-vote headlines should be capped, risk-flagged, or suppressed unless a proper event-arb model exists.
- Add `score_explanation`.
- Add `risk_flags`.

Current implementation notes:

- `scripts/generate_late_daily_ideas.py` now computes a capped display score instead of blindly summing `tradeable_score` and positive `score_delta`.
- Standard late news-only display scores are capped below casual `100/100`.
- Corporate-action / event-structure-uncertain ideas are capped lower.
- GIG-style business-combination / merger-sub / deal-vote headlines are classified as `corporate_action_event_structure_uncertain`.
- Late idea JSONL rows include `score_explanation` and `risk_flags`.
- Late idea Markdown reports show the score note and risk flags.
- This remains watch-only and does not affect official pick scoring.

Potential risk flags:

- `business_combination`
- `spac_or_de_spac`
- `merger_sub`
- `deal_vote`
- `event_structure_uncertain`
- `no_event_arb_model`
- `low_liquidity`
- `news_only_no_breadth_confirmation`

Safety:

- Still watch-only.
- No official scoring change until validated.

---

### Priority 5 — Opening-range quality evaluator

Goal:

Understand why one opening-range observation worked and another failed.

Required analysis:

- Did SL hit?
- Did TP hit?
- Which hit first?
- Was breakout sustained?
- Was it a false breakout?
- Was volume confirmation meaningful?
- Was there relative strength versus QQQ/SPY/sector?
- Was the move already overextended?
- Did time-of-day affect quality?

Expected artifact integration:

- May share infrastructure with Priority 2.
- Opening-range outcomes must remain separate from official picks.

Current implementation notes:

- Opening-range quality is integrated into `scripts/build_watch_only_outcomes.py`.
- Opening-range watch-only outcomes now include quality status, quality score, sustained/false-breakout markers, retest status, volume-confirmation status, overextension marker, and time-of-day bucket.
- If retained bars end before the observation timestamp, quality is marked `data_insufficient_no_forward_bars`.
- May 8 TSLA/AMD/QQQ opening-range observations are explicitly marked data-insufficient because no forward bars exist after observation.
- Watch-only outcome Markdown renders opening-range quality details.
- This remains watch-only and separate from official picks/performance.

Safety:

- Opening-range remains watch-only.
- No paper/live trading.
- No buy instructions.

---

### Priority 6 — Dynamic Theme Discovery Radar v0, observe-only

Goal:

Let the agent independently discover strengthening sectors/themes instead of the founder naming them manually.

Important principle:

Do not hardcode AI / Semiconductor / Memory / Storage as the answer.

Those themes may be used as a validation case:

> If the radar is working, it should independently discover AI / Semiconductor / Memory / Storage leadership from evidence.

Evidence layers:

- price leadership,
- 1D / 5D / 20D / 60D returns,
- relative strength versus SPY and QQQ,
- sector ETF confirmation,
- breadth across related names,
- new-high / breakout counts,
- news clustering,
- earnings and guidance confirmation,
- analyst/estimate revision evidence if available,
- overextension/crowding risk,
- data-provider failure awareness.

Theme lifecycle states:

- `candidate_theme`
- `emerging_theme`
- `confirmed_leadership`
- `crowded_momentum`
- `distribution_warning`
- `failed_theme`
- `news_hype_unconfirmed`

Expected artifacts:

- `data/theme_discovery_YYYY-MM-DD.json`
- `data/theme_discovery_YYYY-MM-DD.md`

Safety:

- Observe-only.
- No official score boost yet.
- No paper/live trading.
- No buy instructions.

---

### Priority 7 — Theme-to-pick bridge v0, observe-only

Goal:

Compare discovered themes against official pick behavior.

Required questions:

- What were the top discovered themes today?
- Did official picks include leaders from those themes?
- If not, why?
- Were leaders missing from the universe?
- Were they data-failed?
- Were they overextended?
- Were they filtered?
- Were they hard-blocked?
- Were they only watch-only?
- Did late/intraday lanes catch them?

Expected artifact:

- section inside theme-discovery report or a separate bridge report.

Safety:

- Observe-only.
- No production scoring effect.

---

### Priority 8 — Future theme-aware scoring only after validation

Goal:

Eventually allow theme intelligence to influence official scoring.

Strict prerequisites:

- historical validation,
- forward observation,
- train/test discipline,
- no overfitting,
- clear tests,
- founder approval,
- no readiness-gate bypass.

Potential future scoring fields:

- `theme_strength_score`
- `theme_breadth_score`
- `theme_quality_score`
- `theme_overextension_penalty`
- `theme_confirmation_count`

Safety:

- Not active now.
- Do not implement production scoring changes in v0.

## Implementation discipline

Work must proceed one priority at a time.

For each priority:

1. inspect existing code/tests,
2. design smallest safe patch,
3. add/update tests,
4. run targeted tests,
5. run full tests if non-trivial,
6. verify no unintended data mutation,
7. update docs,
8. commit only when clean.

## Documentation requirements

After meaningful work, update:

- `docs/WORK_LOG.md`
- `docs/NEXT_SESSION.md`
- `docs/PROJECT_BLUEPRINT.md` if architecture/current-state changes
- this plan if priorities or implementation details change
- relevant `docs/decisions/*` if a major safety/product decision is made

## Current best next implementation

After this plan is committed, start with:

1. validate existing official no-pick diagnostics,
2. implement or improve watch-only outcome attribution v1,
3. then calibrate late-news scores.

Do not start with theme-aware scoring.  
Do not start with paper trading.  
Do not start with live trading.  
Do not start with a major provider refactor unless provider telemetry proves it is necessary.
