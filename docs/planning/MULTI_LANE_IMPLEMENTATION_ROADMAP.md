# Multi-Lane Implementation Roadmap

Last updated: 2026-05-09

## Purpose

This document converts the multi-lane product architecture into an executable
implementation roadmap.

Related source-of-truth strategy document:

- `docs/strategy/MULTI_LANE_PRODUCT_ARCHITECTURE.md`

This roadmap exists so a fresh agent can understand not only what the product
should become, but also how to implement it safely without blurring product
lanes, weakening trust, or accidentally moving toward paper/live trading too
early.

## Non-negotiable operating rules

The product remains:

- monitoring-only,
- not paper-trading-ready,
- not live-trading-ready,
- not public paid-launch-ready.

Paper trading remains forbidden until readiness gates pass and the founder
explicitly approves.

Live trading remains forbidden.

No lane may silently promote itself from observe-only to trading behavior.

No model, LLM, report, book-derived rule, or learning loop may directly mutate
production scoring without:

1. documented hypothesis,
2. tests,
3. backtest or forward-observation evidence,
4. review,
5. versioning,
6. founder approval when promotion changes product behavior.

## Current immediate priority

### Priority 19 — certify Lane 1 scheduled production run

Before major new feature work, certify the next real scheduled Daily Stock Picks
premarket run.

Certification target:

- Daily Stock Picks workflow runs during the official premarket window.
- Production-readiness audit passes.
- Synthetic official pick dry-run passes.
- Synthetic official no-pick dry-run passes.
- Main workflow completes.
- Exactly one official outcome exists:
  - valid official pick artifact(s), or
  - valid official no-pick artifact.
- User-facing Telegram/GitHub output matches official artifacts.
- Official decision artifacts upload and commit correctly.
- Paper/live trading remains disabled.

Important:

A valid no-pick is a valid official outcome. The failure case is producing
neither valid official pick artifacts nor a valid official no-pick artifact.

## Implementation phases

## Phase 0 — repo/session audit discipline

Every new session starts with audit before implementation.

Minimum audit:

1. `git status -sb`
2. fetch `origin main`
3. confirm local HEAD and `origin/main` match or safely fast-forward
4. verify latest CI for current HEAD
5. read canonical docs
6. run compile check
7. run full tests when non-trivial changes are planned
8. run relevant readiness/audit scripts
9. inspect workflow timing/config
10. check for unintended data mutations
11. summarize health before coding

Acceptance criteria:

- working tree clean or understood,
- CI state known,
- tests/audits known,
- no unexpected data artifacts,
- no implementation starts before reality is verified.

## Phase 1 — Lane 1: premarket official daily decision

### Goal

Operate the official daily premarket decision lane.

The lane must produce either:

- validated official pick artifact(s), or
- validated official no-pick artifact.

### Current status

Known completed hardening:

- user-facing output fails closed if official artifacts are missing/invalid,
- official decision/artifact traceability exists,
- guard-level no-pick artifacts exist for skipped daily-pick runs,
- workflow/run/artifact observability links exist,
- workflow summary CLI import issue fixed,
- CI #233 is green after multi-lane documentation commit.

Remaining:

- real scheduled-run production certification.

### Key implementation components

Existing/expected components:

- `main.py`
- `src/premarket_decision_contract.py`
- `src/official_pick_artifact.py`
- `src/official_artifact_loader.py`
- `src/github_observability.py`
- `scripts/validate_official_pick_artifacts.py`
- `scripts/validate_daily_no_pick.py`
- `scripts/write_guard_no_pick_artifact.py`
- `scripts/write_official_workflow_summary.py`
- `.github/workflows/daily-picks.yml`

### Artifacts

Official pick:

- `data/premarket_official_pick_YYYY-MM-DD_TICKER.json`
- `data/premarket_official_pick_summary_YYYY-MM-DD.json`

Official no-pick:

- `data/daily_picks_no_pick_report_YYYY-MM-DD.json`
- `data/daily_picks_no_pick_report_YYYY-MM-DD.md`

Support:

- `data/daily_picks_run_status_YYYY-MM-DD.jsonl`
- `data/market_data_health_YYYY-MM-DD.json`

### Acceptance criteria

- official cutoff remains enforced after 09:20 ET,
- manual dispatch does not bypass cutoff,
- official artifacts validate,
- no-pick reports validate,
- output fails closed without valid official artifacts,
- workflow summary shows official outcome clearly,
- Telegram/GitHub issue output shows official trace,
- provider health is available when relevant,
- paper/live trading disabled.

### What not to do

- Do not force a pick when no-pick is safer.
- Do not treat no-pick as failure if valid artifact exists.
- Do not add Finnhub unless real telemetry proves yfinance/Stooq is inadequate.
- Do not enable paper/live trading.

## Phase 2 — provider reliability and telemetry validation

### Goal

Verify real provider behavior during official windows before adding more data
providers or changing scoring.

### Implementation idea

1. Inspect `data/market_data_health_YYYY-MM-DD.json` from real runs.
2. Confirm yfinance attempt/success/failure rates.
3. Confirm Stooq fallback behavior if present.
4. Confirm failures are visible in no-pick reports.
5. Confirm provider degradation does not create fake/stale official picks.
6. Decide whether provider changes are needed based on evidence.

### Acceptance criteria

- real official-window telemetry exists,
- failure modes are categorized,
- no-pick report includes provider-health context,
- all-provider failure is failure-loud,
- data quality is not silently degraded.

### What not to do

- Do not add Finnhub because of anxiety.
- Do not add providers without evidence and tests.
- Do not mask provider failure with stale/cached official data unless freshness
  rules explicitly allow it.

## Phase 3 — Lane 2: post-open / late-daily watch-only opportunity lane

### Goal

Create a separate after-open opportunity lane without confusing it with official
premarket picks.

This lane starts as:

- watch-only,
- monitoring-only,
- not official picks,
- not paper trades,
- not buy instructions.

### Product definition

Better wording:

> Post-open / late-daily watch-only opportunity lane.

It can capture:

- stocks that became valid only after the open,
- earnings/news/catalyst moves,
- late-day continuation setups,
- watch-only opportunities until validated.

### Implementation sequence

1. Define a lane contract.
2. Define output schema.
3. Define run-status ledger.
4. Define no-op/no-opportunity artifact.
5. Define user-facing copy rules.
6. Build read-only scanner/report first.
7. Add outcome attribution.
8. Add tests.
9. Add workflow only after script behavior is stable.
10. Keep outputs separate from official daily statistics.

### Proposed files

Possible source files:

- `src/post_open_contract.py`
- `src/post_open_scanner.py`
- `src/post_open_artifacts.py`

Possible scripts:

- `scripts/run_post_open_watch_only.py`
- `scripts/validate_post_open_artifacts.py`
- `scripts/post_open_outcome_attribution.py`

Possible tests:

- `tests/test_post_open_contract.py`
- `tests/test_post_open_artifacts.py`
- `tests/test_post_open_watch_only.py`
- `tests/test_validate_post_open_artifacts.py`
- `tests/test_post_open_safety.py`

Possible artifacts:

- `data/post_open_watchlist_YYYY-MM-DD.json`
- `data/post_open_opportunity_report_YYYY-MM-DD.md`
- `data/post_open_run_status_YYYY-MM-DD.jsonl`
- `data/post_open_no_opportunity_YYYY-MM-DD.json`
- `data/post_open_outcomes_YYYY-MM-DD.jsonl`

### Safety requirements

- must not mutate `data/picks_log.csv`,
- must not mutate official pick artifacts,
- must not create paper trades,
- must not enable live trading,
- must not use executable buy/sell wording,
- must label outputs watch-only,
- must include data-readiness/provider status,
- must include reason against the idea when available.

### Acceptance criteria for v0

- script can run safely after open,
- produces watch-only artifact or no-opportunity artifact,
- validates schema,
- Telegram/report copy avoids buy instructions,
- tests prove no official/paper/live mutation,
- artifacts are not counted in official pick stats.

## Phase 4 — Lane 3: opening-range / intraday observations

### Goal

Improve intraday observation quality before considering any intraday pick engine.

### Implementation sequence

1. Verify current opening-range workflow and artifacts.
2. Add or harden opening-range bar artifact capture.
3. Ensure run-status ledger records start/skip/complete/send events.
4. Add missing-bar-data reporting.
5. Attribute outcomes using retained bars.
6. Build quality summaries.
7. Keep all outputs watch-only.

### Existing/expected artifacts

- `data/opening_range_run_status_YYYY-MM-DD.jsonl`
- `data/opening_range_observations_YYYY-MM-DD.jsonl`
- `data/intraday_alerts_YYYY-MM-DD.json`

Possible new artifacts:

- `data/opening_range_bars_YYYY-MM-DD.jsonl`
- `data/opening_range_quality_report_YYYY-MM-DD.json`
- `data/opening_range_quality_report_YYYY-MM-DD.md`

### Acceptance criteria

- observations include real ET timestamps,
- new opportunities suppressed after 15:15 ET,
- existing-pick monitoring is separate,
- artifacts are force-added when intentionally ignored by gitignore,
- missing bars are visible,
- outputs remain watch-only.

### What not to do

- Do not call opening-range outputs official picks.
- Do not paper trade opening-range alerts.
- Do not use action-like entry wording.

## Phase 5 — reports and evidence loops

### Goal

Turn raw outputs into trust-building evidence.

### Report families

- Daily performance report,
- Weekly performance report,
- Monthly performance report,
- Quarterly performance report,
- Yearly performance report,
- Execution quality report,
- Pick X-ray report,
- No-pick report,
- Missed-opportunity report,
- Regime report,
- Strategy-by-strategy report,
- Watch-only vs official comparison.

### Implementation idea

1. Inventory all relevant artifacts.
2. Build report generators with `--no-write`.
3. Write reports only when explicitly requested or in workflows.
4. Keep reporting read-only with respect to journals/logs unless explicitly designed.
5. Make reports compare official vs watch-only vs blocked candidates.
6. Feed lessons into calibration notes, not automatic scoring changes.

### Acceptance criteria

- reports are reproducible,
- reports show missing data,
- reports separate lanes,
- reports do not overclaim,
- reports produce actionable calibration hypotheses.

## Phase 6 — missed-opportunity and no-pick intelligence

### Goal

Learn from what the system did not pick.

### Missed-opportunity questions

- What did we miss?
- Was the missed ticker present in watch-only candidates?
- Was it blocked correctly?
- Did provider/data failure hide it?
- Did timing rules exclude it correctly?
- Did scoring under-rank it?
- Was the opportunity outside the lane's mandate?

### No-pick questions

- Was no-pick correct?
- Was no-pick caused by data/provider failure?
- Were filters too strict?
- Did no-pick avoid a bad trade?
- Did no-pick miss a strong opportunity?
- Was explanation clear to users?

### Implementation idea

1. Build daily missed-opportunity report.
2. Join official candidates, watch-only candidates, no-pick reports, and market movers.
3. Attribute reasons.
4. Generate calibration hypotheses.
5. Track repeated miss patterns.

### Acceptance criteria

- no-pick is treated as a decision, not absence of work,
- missed opportunities are classified without hindsight overclaim,
- reports produce testable improvement ideas.

## Phase 7 — risk management and portfolio construction

### Goal

Prepare for eventual paper-trading readiness without enabling it prematurely.

### Future rules

- position sizing,
- max daily risk,
- max loss per trade,
- max open positions,
- max sector exposure,
- correlation between picks,
- stop-loss policy,
- take-profit policy,
- trailing stop policy,
- capital allocation by strategy.

### Implementation idea

1. Define risk contract.
2. Add risk simulation only.
3. Run historical and forward-observed scenarios.
4. Report drawdowns and exposure.
5. Keep paper trading disabled.
6. Promote only after readiness gates and founder approval.

### Acceptance criteria

- risk simulator exists,
- no execution side effects,
- risk assumptions are explicit,
- strategy-level and portfolio-level risk are separate,
- promotion gates are documented.

## Phase 8 — market regime awareness

### Goal

Evaluate strategy behavior under different market states.

### Regime labels

- bull trend,
- bear trend,
- sideways/chop,
- high volatility,
- low volatility,
- risk-on,
- risk-off,
- sector rotation,
- earnings-heavy period,
- Fed/macro event risk.

### Implementation idea

1. Build regime classifier as observe-only.
2. Attach regime to artifacts and reports.
3. Evaluate outcomes by regime.
4. Do not let regime classifier change production scoring until validated.

### Acceptance criteria

- regime labels are explainable,
- labels are stored with reports/artifacts,
- performance by regime is visible,
- no scoring impact until approved.

## Phase 9 — Probability Engine Phase 2 observe-only

### Goal

Improve probability estimates without creating false precision.

### Implementation idea

1. Keep probability engine observe-only.
2. Version features and scoring.
3. Compare probability buckets to outcomes.
4. Track calibration error.
5. Avoid using probabilities as buy instructions.
6. Promote only after out-of-sample validation.

### Acceptance criteria

- probability outputs are calibrated and versioned,
- reports show reliability by bucket,
- no production scoring impact without approval.

## Phase 10 — book/wisdom/historical learning

### Goal

Use external concepts safely as hypotheses, not authority.

### Implementation idea

1. Use only legal/licensed/founder-provided material.
2. Extract principles.
3. Convert to structured rule candidates.
4. Backtest with train/test split.
5. Walk-forward test.
6. Forward observe.
7. Promote only after evidence.

### Acceptance criteria

- no copied copyrighted text in product logic/docs,
- every principle becomes a testable hypothesis,
- every promoted rule has evidence and versioning,
- no self-modifying production behavior.

## Phase 11 — Monster Hunter / Compounder / Long-Term research

### Goal

Build long-horizon research lanes without contaminating short-term engines.

### Implementation idea

1. Define separate schemas:
   - thesis,
   - catalyst,
   - quality,
   - valuation,
   - risk,
   - invalidation,
   - horizon.
2. Produce reports/watchlists only.
3. Track outcomes separately.
4. Require fundamental evidence.
5. Avoid converting failed swing trades into long-term holds.
6. Keep separate from official pick stats.

### Acceptance criteria

- research-only artifacts,
- no production scoring influence,
- no paper/live trading,
- no mixing with intraday/day/swing stats,
- founder approval required for any promotion.

## Phase 12 — customer-facing trust assets

### Goal

Convert internal evidence into user trust.

### Possible assets

- daily brief,
- weekly transparency report,
- no-pick explanation,
- missed-opportunity review,
- provider-health transparency,
- strategy scorecard,
- watch-only vs official comparison,
- product safety statement.

### Implementation idea

1. Build from validated reports.
2. Avoid performance overclaims.
3. Show uncertainty and failure modes.
4. Use simple language for busy professionals.
5. Keep advice boundaries clear.

### Acceptance criteria

- user can understand what happened and why,
- reports do not imply guaranteed returns,
- evidence is traceable to artifacts,
- compliance/safety language is clear.

## Phase 13 — promotion gates

No lane can progress to paper trading until it passes gates.

Possible gates:

- minimum sample size,
- positive expectancy,
- acceptable drawdown,
- stable win rate,
- slippage tolerance,
- provider reliability,
- no data-readiness failures,
- reports generated correctly,
- no hidden mutations,
- founder approval.

Promotion ladder:

1. Observe-only.
2. Paper trading.
3. Limited live trading.
4. Scaled live trading.

Current status:

- all lanes remain observe-only / monitoring-only,
- paper trading forbidden,
- live trading forbidden.

## Implementation discipline for every phase

For every implementation:

1. Read current docs/code/workflows/tests first.
2. Define exact lane and safety boundary.
3. Add schema/contract before output complexity.
4. Add artifacts before user-facing claims.
5. Add validators before workflows.
6. Add tests before relying on behavior.
7. Add workflow only after script behavior is safe.
8. Run targeted tests.
9. Run full tests for non-trivial changes.
10. Run `git diff --check`.
11. Verify no unintended data mutations.
12. Update docs.
13. Commit only after clean verification.
14. Push only after clean verification.
15. Watch CI.

## Next-session recommendation

If Priority 19 scheduled run has completed:

1. Certify Priority 19 first.
2. Inspect real artifacts and workflow summary.
3. Document certification result.
4. Only then start next lane.

If Priority 19 has not completed:

1. Audit repo and CI.
2. Do not start major feature work unless fixing repo-health issue.
3. Optionally inspect scheduler/workflow readiness.
4. Prepare Lane 2 design only if no blockers exist.

The next implementation lane should be:

> Lane 2 — post-open / late-daily watch-only opportunity lane.

It must not be called official after-open picks until separately validated.
