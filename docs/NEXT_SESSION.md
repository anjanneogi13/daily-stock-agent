## 2026-05-09 checkpoint — Daily data readiness report added

Priority 9 is implemented observe-only.

New files:

- `scripts/build_data_readiness_report.py`
- `tests/test_data_readiness_report.py`

Generated artifacts:

- `data/data_readiness_2026-05-08.json`
- `data/data_readiness_2026-05-08.md`
- `data/data_readiness_2026-05-09.json`
- `data/data_readiness_2026-05-09.md`

Validation:

- May 8 readiness classification: `data_provider_failure`
- May 9 readiness classification: `pipeline_incomplete`

Recommended next task:

Priority 10 — Candidate Lifecycle Ledger.

Goal: reconstruct and report where each candidate/theme leader disappeared in the daily pipeline, starting from existing artifacts before wiring direct lifecycle emission into production code.


## 2026-05-09 checkpoint — Next phase is reliability hardening

After completing product-intelligence priorities 1–8, the next implementation phase should follow:

`docs/planning/SYSTEM_RELIABILITY_REPAIR_PLAN.md`

Recommended next task:

1. Build Daily Data Readiness Report:
   - `scripts/build_data_readiness_report.py`
   - `tests/test_data_readiness_report.py`
   - `data/data_readiness_YYYY-MM-DD.json`
   - `data/data_readiness_YYYY-MM-DD.md`

Do not start paper trading, live trading, or production theme-aware scoring. The current product lag is reliability/proof: the system must prove whether no-pick days are strategic, data-failed, pipeline-incomplete, or diagnostics-missing.


## 2026-05-09 checkpoint — Theme-aware scoring remains disabled

Priority 8 added guardrails, not scoring:

- `src/theme_scoring_guardrails.py`
- `tests/test_theme_scoring_guardrails.py`
- `docs/decisions/ADR-002-theme-aware-scoring-disabled.md`

Theme discovery and bridge artifacts remain observe-only. Do not enable production theme-aware scoring until historical validation, forward observation, train/test discipline, overfitting review, clear tests, founder approval, and readiness-gate preservation are complete.


## 2026-05-08 session handoff

A complete handoff is available at:

```text
docs/sessions/SESSION_HANDOFF_2026-05-08.md
```

Critical next step:

```text
Wait for tonight's automatic Daily Picks official-window run, then validate Stooq/OHLCV telemetry before deciding whether to add Finnhub.
```

Do not add Finnhub yet. The decision is intentionally deferred until real provider-health evidence exists.


# Daily Stock Agent — Next Session

**Refresh date:** 2026-05-08
**Status:** monitoring-ready, highest-severity audit issues fixed
**Mode:** monitoring-only

Do not start paper trading yet.

---

## Read first

1. `docs/PROJECT_BLUEPRINT.md`
2. `docs/WORK_LOG.md`
3. `docs/strategy/AGENT_MATURITY_TRACKER.md`
4. This file
5. `docs/decisions/2026-05-05-monitoring-first-no-paper-trading.md`
6. `docs/decisions/2026-05-06-paper-trading-activation-checklist.md`
7. `docs/decisions/2026-05-06-opening-range-outcome-join-design.md`
8. `docs/decisions/2026-05-06-session-closeout-reliability-and-opening-range.md`

---


## 2026-05-08 product-quality priority update

The 2026-05-07 fallback day showed that reliability improved, but late-watch-only product quality needed hardening.

Completed/active safety direction:

- prevent duplicate late-watch-only Telegram sends,
- remove action-like `BUY/Entry` wording from watch-only late ideas,
- suppress unresolved no-quote + blank-company ideas,
- skip acquisition/event-arb ideas until a separate event-arb lane exists.

Still important after this cleanup:

1. Implement official OHLCV provider fallback:
   - yfinance → Stooq → safe empty/failure with provider-health evidence.
2. Add intraday alert quality protections:
   - near-close cutoff,
   - quote/bar freshness,
   - clearer observed/reference level wording.
3. Keep monitoring-only mode. Do not enable paper/live trading.

---


## 2026-05-08 intraday alert quality hardening

Implemented/active safety direction:

- new intraday opportunities are suppressed after 15:15 ET,
- existing-pick monitoring can continue separately,
- intraday Telegram copy uses `Reference levels: Observed` instead of action-like entry wording,
- timestamps use real America/New_York timezone.

Still important after this cleanup:

1. Add quote/bar freshness metadata to intraday alerts if available.
2. Improve outcome joins for intraday momentum/opening-range observations.
3. Implement official OHLCV provider fallback:
   - yfinance → Stooq → safe empty/failure with provider-health evidence.
4. Keep monitoring-only mode. Do not enable paper/live trading.

---


## 2026-05-08 official OHLCV provider fallback

Implemented/active architecture direction:

- official daily OHLCV path now uses yfinance primary,
- Stooq daily OHLCV is available as no-key fallback,
- fallback is limited to `fetch_ohlcv()` / official daily OHLCV path,
- all-provider failure remains a safe empty dataframe with provider-health evidence.

Still important after this cleanup:

1. Observe the next Daily Picks run and inspect `data/market_data_health_YYYY-MM-DD.json`.
2. Consider provider cooldown/backoff only after evidence shows it is needed.
3. Add quote/company-identity validation improvements for news/intraday paths separately.
4. Keep monitoring-only mode. Do not enable paper/live trading.

---


## 2026-05-08 negative-reaction news penalty

Implemented a conservative news scoring guard:

- positive headline + negative market reaction is not treated as a clean bullish catalyst,
- explicit sold-news phrases now fade bullish boosts into a small penalty,
- catastrophic news still hard-blocks before this logic,
- provider fallback work remains paused pending the next official Daily Picks run.

Next validation:

1. Run targeted/full tests after the patch.
2. Observe future news_signal_evidence reports for `negative_reaction=true`.
3. Continue waiting for the post-Stooq official Daily Picks run before adding Finnhub candles.

---


---

## 2026-05-08 Monster Hunter architecture update

A new long-term research architecture track has been documented:

```text
docs/strategy/MONSTER_HUNTER_DESIGN.md
```

Purpose:

- build a dedicated 6-month to 5-year compounder / multi-bagger research lane,
- keep Monster Hunter separate from day trades, swing picks, intraday alerts, and opening-range observations,
- make the agent a serious long-term analyst for fundamentals, P&L trends, secular themes, ETF/mutual fund focus, institutional accumulation, competitive moat, valuation risk, and thesis invalidation.

Important safety posture:

```text
Monster Hunter is research-only / monitoring-only.
It must not create official picks.
It must not create paper trades.
It must not create live trades.
It must not contaminate official pick statistics.
No failed swing trade may silently become a monster hold.
No speculative news spike may be called a monster without fundamental evidence.
```

Recommended weekend-safe first slice:

1. Validate tonight's Daily Picks yfinance/Stooq telemetry first.
2. Keep provider/Finnhub decisions deferred until telemetry is reviewed.
3. If repo health is clean, implement Monster Hunter v0 as docs/schema/report-only:
   - monster theme schema,
   - monster candidate schema,
   - monster thesis schema,
   - thesis state machine,
   - semiconductor / AI memory pilot universe,
   - watch-only Monster Research Report.
4. Do not wire Monster Hunter into production scoring yet.
5. Do not enable paper/live trading.



---

## 2026-05-08 product failure and win strategy update

A new strategic product document has been added:

```text
docs/strategy/PRODUCT_FAILURE_AND_WIN_STRATEGY.md
```

Purpose:

- document where the product can fail,
- define mitigations without pretending failures can be eliminated completely,
- document where the product can win loudly,
- keep the company focused on trust, evidence, and customer value.

Core strategic message:

```text
Trust is the product.
The company can win if it becomes trusted before it becomes automated.
```

Important product positioning:

- do not position as a magic AI stock picker,
- do not position as guaranteed buy/sell signals,
- do not rush paper/live trading,
- position as transparent AI market research for busy working professionals.

Near-term product focus:

1. reliability and evidence,
2. public trust assets,
3. customer discovery,
4. first product wedge: 5-minute market copilot / watchlist,
5. avoid premature auto-execution or overbuilt SaaS.


## Current product lesson

The 2026-05-05 monitoring review showed that the agent can find real catalysts, but it still needs stronger execution intelligence.

Observed:

- `POWI` was an older swing pick from 2026-04-28 and hit TP on 2026-05-05: `+2.0R`.
- `EXPD` had a real earnings-beat catalyst but was logged as swing even though news action window was intraday; it hit stop and later recovered.
- `GILT` had a real contract-win catalyst but has speculative/pump-risk concerns and remains pending.
- `NET` was a strong intraday opportunity but was detected late.
- Daily Telegram picks arrived too late / inconsistently due to workflow timing and data freshness issues.

---

## Best next task

### Priority 1 — Add scheduled/manual News Evidence workflow

Audit/hygiene and the first News Evidence layers are complete:

- Fix test/data isolation: `data/learning_journal.jsonl`, `data/picks_log.csv`, and `data/signal_journal.jsonl` stayed isolated/clean.
- Daily-picks timing hard gate.
- Missed-window Telegram alert and late watch-only ideas.
- Stale/unverified price watch-only protection.
- Monitoring-only default for paper logging.
- News action-window watch-only guard.
- Opening-range scanner rollout, workflow cadence, observation persistence, run-status, review tool, and read-only backtest skeleton.
- Watch-only learning report v1.
- News Engine run-status artifacts.
- News Engine 120-minute configurable lookback.
- News Signal Evidence Report.
- News signal outcome attribution scaffold.
- News outcomes integrated into the evidence report.

Next feature work:

1. Validate the scheduled/manual News Evidence workflow in monitoring-only mode.
2. The workflow may generate only reporting artifacts:
   - tracked: `data/news_signal_outcomes_YYYY-MM-DD.jsonl`,
   - tracked: `data/news_signal_evidence_report_YYYY-MM-DD.md`,
   - uploaded artifact only: `data/news_signal_evidence_report_YYYY-MM-DD.json`.
3. It must not mutate:
   - `data/picks_log.csv`,
   - `data/signal_journal.jsonl`,
   - `data/learning_journal.jsonl`,
   - paper/live trading state.
4. Manual-run documentation now lives in `docs/playbook/NEWS_EVIDENCE_REPORTS.md`.
5. After that, continue with optional opening-range bar artifact capture, still monitoring-only.
6. Do not enable paper trading.
7. Use `docs/decisions/2026-05-06-paper-trading-activation-checklist.md` before any future paper-trading integration.

---


## Completed from prior Priority 1 — Daily-picks timing and stale-price protection

### Priority 1 — Fix daily-picks timing and stale-price protection

Problem:

- Fixed 2026-05-06: normal daily picks are blocked after 09:20 ET.
- Fixed 2026-05-06: manual dispatch no longer bypasses the time guard.
- Fixed 2026-05-06: late runs send missed-window alert instead of normal picks.
- Fixed 2026-05-06: stale/unverified prices are marked watch-only.

Goal:

- Official daily picks should only be sent before market open.
- If the premarket window is missed, send a Telegram missed-window alert instead of normal picks.
- If price is stale/unverified, mark idea as watch-only and do not show actionable entry.

Suggested policy:

- Before 09:20 ET: allow official daily picks.
- After 09:20 ET: block normal daily picks.
- If missed: send premarket-window-missed alert.
- After cutoff: allow only intraday monitor alerts.

---

## Completed from prior Priority 2 — Enforce news action window

Problem:

- Fixed 2026-05-06: news signals preserve `action_window`.
- Fixed 2026-05-06: intraday-news swing candidates are marked watch-only instead of normal actionable swing picks.

Goal:

- Intraday news must not silently become a normal swing pick.

Possible behavior:

1. Convert to day/intraday trade.
2. Require additional multi-day confirmation before swing.
3. Mark as watch-only.
4. Penalize/block as swing if confirmation is missing.

---

## Priority 3 — Opening-range intraday scanner

Problem:

- NET was detected after much of the move had already happened.

Goal:

- Add earlier scans:
  - 09:35 ET
  - 09:45 ET
  - 10:00 ET

Use:

- gap,
- volume,
- VWAP,
- opening range,
- news context,
- anti-chase rule.

---

## Priority 4 — Fundamental-quality / pump-risk smell

Problem:

- GILT had real news but may be a speculative name with long-term value destruction.

Goal:

- Add a smell/penalty for speculative news spikes and poor long-term quality.

Signals:

- huge drawdown from all-time high,
- weak long-term trend,
- poor fundamentals,
- small-cap news spike,
- possible dilution/reverse split history,
- low liquidity,
- news-only move.

---

## Priority 5 — Monster-hunt foundation

Goal:

Build a separate long-term compounder lane, not mixed with swing/day picks.

Required pieces:

- monster watchlist,
- thesis states,
- quarterly/yearly P&L analysis,
- secular theme detection,
- fundamental acceleration,
- historical chart base detection,
- long-term exit/trim plan.

---

## Existing engineering hygiene priorities

Still important:

1. Add tests for:
   - `src/performance_stats.py`
   - `src/paper_trader.py`
   - `src/picks_csv.py`
   - `src/monster_data.py`
   - `src/cape_ratio.py`
4. Backtester hardening.

---

## Blocked items

Do not build or activate yet:

- Paper trading integration.
- `SMELL_ENFORCE=true`.
- `BRAIN_ENFORCE_EV=true`.
- `AUTO_PAUSE_ENABLED=true`.

Do not promote these beyond observe-mode without tests and monitoring evidence:

- Reader engine.
- Curiosity engine.
- Historical regime engine.
- Historical chart replay engine.
- Monster-hunt engine.
- Multi-LLM ensemble.

---

## Session start commands

Run:

- `cd /workspaces/daily-stock-agent`
- `git status --short`
- `git pull --rebase origin main`
- `python3 -m pytest tests/ -q --tb=short --disable-warnings`
- `python scripts/audit_journal_consistency.py --strict`
- `python scripts/check_enforcement_readiness.py`
- `python scripts/monitoring_readiness.py`

If tests mutate tracked data, reset only data side effects:

- `git checkout -- data/picks_log.csv data/signal_journal.jsonl data/learning_journal.jsonl data/premarket_check.json`

---

## Planning docs added — 2026-05-08

New planning-only documentation now lives under:

- `docs/planning/README.md`
- `docs/planning/FEATURE_BACKLOG.md`
- `docs/planning/DATA_CONTRACTS.md`
- `docs/planning/NOTIFICATION_ARCHITECTURE.md`
- `docs/planning/CANDIDATE_LIFECYCLE.md`

Before implementing future features, check the planning docs for:

- official vs watch-only separation
- research-only separation
- data artifact ownership
- notification wording safety
- candidate lifecycle readiness gates

These documents are design guidance only until matching code, tests, and workflows exist.

---

## Documentation update rule

After every bug fix, feature, audit, or process change:

1. Update `docs/WORK_LOG.md`.
2. Update `docs/NEXT_SESSION.md`.
3. Update `docs/PROJECT_BLUEPRINT.md` if architecture, roadmap, or product state changed.
4. Update `docs/strategy/AGENT_MATURITY_TRACKER.md` when trading lessons or intelligence roadmap changes.
5. Keep CI/tests green.


Backtest tool: `python scripts/backtest_opening_range_observations.py`

## Closing audit status — 2026-05-06

Final closing audit passed.

Current state:

- Repository clean after import-side-effect fixes.
- Full suite passed: `1372 passed, 30 skipped`.
- Targeted opening-range / monitoring tests passed.
- Journal consistency green.
- Enforcement readiness blocked as expected.
- Monitoring readiness blocks paper trading as expected.
- Paper trading remains disabled.
- Opening-range review and backtest tools are available.

Before next work:

1. Run full repo audit.
2. If issues are found, fix issues first.
3. If clean and it is Saturday/Sunday, implement the next planned feature slice.
4. If weekday, prefer monitoring/audit/review work unless urgent.
5. Never enable paper/live trading without readiness gates and founder approval.

Recommended next feature:

- Scheduled/manual News Evidence workflow, still monitoring-only.
- Then optional opening-range bar artifact capture, still monitoring-only.

## News Signal Evidence Report outcome integration — 2026-05-07

Integrated news signal outcome summaries into the News Signal Evidence Report.

The evidence report now reads this optional artifact when present:

- `data/news_signal_outcomes_YYYY-MM-DD.jsonl`

It summarizes:

- total outcome rows,
- status counts,
- evaluated rows,
- average 1D return,
- average horizon return,
- top evaluated rows.

Safety:

- report remains read-only,
- no official pick stats mutation,
- no signal/learning journal mutation,
- no paper/live trading behavior changed.

Next:

- Once enough outcome rows exist, review catalyst categories and score deltas.

---

## News signal outcome attribution scaffold — 2026-05-07

Added a monitoring-only scaffold for news signal outcome attribution:

- script: `scripts/news_signal_outcome_attribution.py`,
- optional output: `data/news_signal_outcomes_YYYY-MM-DD.jsonl`,
- supports `--no-write` for read-only smoke/audit.

The scaffold:

- loads evidence from:
  - `data/news_signals.json`,
  - `data/watchlist.json`,
  - `data/news_log.jsonl`,
- dedupes evidence rows,
- fetches daily price history with `yfinance` when available,
- computes:
  - 1D return,
  - configurable horizon return, default 3 trading days,
- marks unavailable cases as structured statuses instead of failing:
  - `quote_unavailable`,
  - `missing_price_data`,
  - `missing_future_data`,
  - `invalid_ticker`.

Safety:

- no official pick stats mutated,
- no signal journal mutation,
- no learning journal mutation,
- no paper/live trading behavior changed.

Next:

- Integrate outcome summaries into the News Signal Evidence Report.
- Later: use enough sample size to tune catalyst score deltas.

---

## News Signal Evidence Report — 2026-05-07

Added a read-only report for news evidence:

- script: `scripts/news_signal_evidence_report.py`,
- outputs:
  - `data/news_signal_evidence_report_YYYY-MM-DD.md`,
  - full JSON reports as short-retention workflow artifacts,
- supports `--no-write` for read-only smoke/audit.

The report inventories:

- `data/news_log.jsonl`,
- active `data/news_signals.json`,
- `data/watchlist.json`,
- `data/news_engine_run_status_YYYY-MM-DD.jsonl`,
- `data/late_daily_ideas_YYYY-MM-DD.jsonl`,
- `data/picks_log.csv` rows with news-related fields for the date.

Safety:

- read-only inventory,
- no official pick stats mutated,
- no paper/live trading behavior changed,
- no learning journal mutation.

Remaining evidence gap:

- outcome attribution is not implemented yet. The next layer should join news signal timestamps to 1D/3D future price outcomes.

---

## News Engine lookback hardening — 2026-05-07

Changed News Engine fetch lookback from a fixed 60 minutes to a safer configurable lookback:

- default: `120` minutes,
- env override: `NEWS_LOOKBACK_MINUTES`,
- clamp range: `30` to `360` minutes,
- run-status now records `lookback_minutes`.

Why:

- GitHub scheduled workflows are best-effort and can be delayed or skipped.
- A 120-minute lookback reduces missed broad-market news.
- Existing `data/news_seen.json` dedupe prevents already-seen items from being reprocessed.

Safety:

- no official pick logic changed,
- no paper/live trading behavior changed,
- no readiness-gate changes.

---

## News Engine run-status observability — 2026-05-07

Added run-status persistence for News Engine:

- artifact: `data/news_engine_run_status_YYYY-MM-DD.jsonl`,
- records:
  - items fetched,
  - items classified,
  - signals added,
  - hard blocks,
  - watchlist additions,
  - high-impact internal alerts,
  - Telegram enabled/attempted,
  - GitHub workflow metadata.

Purpose:

- Prove whether the News Engine ran throughout the day.
- Distinguish no-news runs from failed runs.
- Preserve schedule/fetch/classify/signal evidence without changing stock-picking behavior.

Safety:

- no official picks created by News Engine,
- no paper trading,
- no live trading,
- no readiness-gate changes.

Next News Engine fixes:

1. Increase or dynamicize fetch lookback to reduce missed news during GitHub schedule delays.
2. Add a News Signal Evidence Report.
3. Add outcome attribution for news signals.

---

## Intraday momentum observation persistence — 2026-05-07

Added structured persistence for generic intraday momentum watch-only ideas:

- artifact: `data/intraday_momentum_observations_YYYY-MM-DD.jsonl`,
- scanner: `momentum`,
- mode: `monitoring_only`,
- watch-only only,
- no official picks,
- no paper trades,
- no live trades.

The watch-only learning report now reads this artifact and can distinguish:

- structured momentum observations from current/future runs,
- older dedupe-only momentum evidence from prior runs.

Still not implemented:

- outcome join for momentum observations,
- learning-journal integration,
- promotion to paper trading.

Safety remains unchanged.

---

## Watch-only learning report v1 — 2026-05-07

Added the first safe slice of the watch-only learning evidence layer:

- script: `scripts/daily_watch_only_learning_report.py`,
- tests: `tests/test_daily_watch_only_learning_report.py`,
- outputs:
  - `data/watch_only_learning_report_YYYY-MM-DD.json`,
  - `data/watch_only_learning_report_YYYY-MM-DD.md`.

Purpose:

- Inventory late daily watch-only ideas.
- Inventory opening-range observations.
- Inventory intraday dedupe fingerprints.
- Explain why some watch-only ideas cannot be outcome-scored yet.
- Keep all of this separate from official picks and readiness statistics.

Still not implemented:

- Generic intraday momentum structured observation persistence.
- Watch-only outcome join for late ideas.
- Bar artifact capture for opening-range backtest.
- Learning-journal integration.

Safety remains unchanged:

- monitoring-only,
- no official pick mutation,
- no paper trading,
- no live trading.

---

## 2026-05-07 audit checkpoint — watch-only learning direction

Comprehensive audit after overnight workflow/data commits:

- Full suite passed: `1372 passed, 30 skipped`.
- Journal consistency remained green: `41/41 matched`.
- Enforcement readiness remained blocked as expected.
- Monitoring readiness continued blocking paper trading as expected.
- Opening-range observations now exist:
  - total observations: 4,
  - tickers: AAPL, NET, SPY, XLK,
  - all are `watch_only=true`,
  - all are `mode=monitoring_only`,
  - all are `scanner=opening_range`.
- Opening-range backtest cannot evaluate them yet because bar data is missing:
  - `missing_bar_data: 4`.

Audit fixes completed:

- `scripts/send_intraday_telegram.py` no longer executes Telegram/run-status logic at import time.
- `tests/test_intraday_monitor_opening_range_observations.py` no longer mutates tracked `data/opening_range_run_status_2026-05-06.jsonl`.

Product direction agreed:

- The agent should learn from official premarket picks, late watch-only daily ideas, intraday watch-only ideas, and opening-range observations.
- These must remain separated by evidence type.
- Watch-only ideas must not contaminate official pick stats, paper trading readiness, or live trading readiness.
- Recommended next feature after health is clean:
  - build a watch-only learning evidence layer and daily learning report,
  - still monitoring-only,
  - no paper/live trading.

---

## Daily-picks reliability hardening — 2026-05-06

A live operational miss showed no daily picks were logged for 2026-05-06 by 10:06 ET.

Reliability fix applied:

- Daily-picks workflow now has frequent guarded premarket cron attempts.
- The 09:20 ET hard cutoff remains in place.
- Morning watchdog now runs before cutoff at 09:10 and 09:18 ET.
- Watchdog checks `data/picks_log.csv`, not stale `premarket_check.json`.
- Watchdog sends Telegram alerts while there is still time to manually trigger daily picks.

Next verification:

1. Confirm GitHub Actions schedules fire on the next market day.
2. Confirm daily picks are logged before 09:20 ET.
3. Confirm Telegram receives either picks or an early watchdog alert.
4. Keep paper/live trading disabled.

## Import-safety fix — 2026-05-06

During the daily-picks reliability work, the full suite revealed that `tests/test_scripts_import.py` could mutate tracked `data/picks_log.csv`.

Root cause:

- `scripts/evaluate_picks.py` ran evaluation logic at import time.

Fix:

- `scripts/evaluate_picks.py` is now import-safe.
- Execution is behind `main()` and `if __name__ == "__main__"`.

Continue to verify tracked data stays clean after full-suite runs.

## Daily-picks run-status artifact — 2026-05-06

Added `data/daily_picks_run_status_YYYY-MM-DD.jsonl` as the operational ledger for daily-picks and watchdog attempts.

Use it to answer:

- Did daily-picks workflow start?
- Did the guard skip or proceed?
- Were picks already logged?
- Did main.py run?
- Did CSV verification pass?
- Did Telegram send?
- Did watchdog check and alert?

Next reliability feature after this is clean:

- Add late watch-only daily ideas in a separate ledger, not official picks.

## Late watch-only daily ideas — 2026-05-06

Added a missed-window fallback:

- Official premarket picks remain blocked after 09:20 ET.
- The workflow can generate `data/late_daily_ideas_YYYY-MM-DD.jsonl`.
- Telegram receives a clearly labeled late watch-only message.
- These ideas are not official picks and do not enter `picks_log.csv`.

Use this to avoid wasting the entire day when GitHub scheduled workflows miss the official window, while keeping official statistics clean.

## Session closeout — 2026-05-06 late-picks reliability and opening-range observability

Final status at closeout:

- Main branch head after code work: `27d92f0 intraday: force-add opening-range status artifacts`.
- Latest CI observed green: CI #141.
- Full local audit before closeout passed:
  - full test suite: `1351 passed, 29 skipped`,
  - journal consistency: `41/41 matched`,
  - readiness dashboards remain blocked as expected,
  - opening-range review/backtest remain monitoring-only,
  - tracked data side-effect check clean.
- Paper trading remains disabled.
- Live trading remains disabled.
- Enforcement flags remain disabled.

Completed in this session:

1. Daily-picks missed-window fallback:
   - official premarket picks remain blocked after 09:20 ET,
   - after-cutoff runs generate separate late watch-only ideas,
   - late ideas do not enter `data/picks_log.csv`,
   - late ideas are not official stats.

2. Late idea quality upgrade:
   - filters weak rows such as one-letter headline/evidence,
   - validates ticker shape,
   - requires quote enrichment in workflow,
   - includes company name when available,
   - includes watch-only BUY/Entry, SL, TP, and R/R.

3. Telegram UX fix:
   - missed-window notice and late watch-only ideas are now one combined message,
   - expected heading:
     - `PREMARKET WINDOW MISSED — LATE WATCH-ONLY DAILY IDEAS`.

4. Opening-range run-status ledger:
   - new artifact:
     - `data/opening_range_run_status_YYYY-MM-DD.jsonl`,
   - records monitor started/skipped/completed,
   - records candidate count, alert count, observation count,
   - records Telegram send/skipped/failed result,
   - always monitoring-only/watch-only.

5. Opening-range artifact persistence fix:
   - `.gitignore` ignores `data/`, so Intraday Monitor now uses `git add -f` for:
     - `data/intraday_alerts_*.json`,
     - `data/opening_range_observations_*.jsonl`,
     - `data/opening_range_run_status_*.jsonl`.

Important remaining validation:

- Rerun GitHub Actions `Intraday Monitor` after commit `27d92f0`.
- Pull afterward and confirm a new commit/artifact exists with non-empty GitHub metadata:
  - `github.run_id`,
  - `github.sha`,
  - `github.workflow`.
- If no artifact commit appears, inspect the workflow logs before adding new features.

Next best task:

1. Validate Step 4B artifact persistence from GitHub Actions.
2. If validated, close the reliability lane.
3. Next feature candidate, preferably weekend-only:
   - opening-range bar artifact capture for future backtest joins.
4. Continue monitoring-only mode.
5. Do not enable paper/live trading.

## 2026-05-08 Daily Picks no-pick reliability follow-up

Latest Daily Picks incident:
- 2026-05-08 Daily Stock Picks failed loudly after zero official final picks.
- The pipeline did not find zero ideas; it found 2 finalists and hard-blocked both:
  - pre_hard_block_pick_count=2
  - hard_blocked_count=2
  - final_pick_count=0
- The failure alert was correct and safety-preserving:
  - no official picks should be used,
  - watch-only fallback only,
  - paper trading disabled,
  - live trading disabled.

Fixes completed:
1. Failed Daily Picks artifact recovery now persists:
   - `data/market_data_health_*.json`
   - `data/hard_blocks_log.json`
   - `data/daily_picks_candidate_rejections_*.json`
   - `data/daily_picks_candidate_rejections_*.md`
   - no-pick reports and run-status ledgers.
2. No-pick reports now classify primary cause and secondary causes.
3. Candidate rejection diagnostics now capture:
   - pre-hard-block candidates,
   - hard-blocked finalists,
   - block type,
   - block reason,
   - compact candidate context.
4. Official Daily Picks yfinance pressure was reduced:
   - `monster_data` enrichment is disabled by default unless explicitly enabled,
   - Daily Picks workflow sets `DAILY_FETCH_YF_FULL_INFO=false`,
   - `fetch_info()` default company-name contract remains intact outside workflow.
5. Stooq fallback now rejects unsupported symbols such as `TSX:AQN` before HTTP/CSV parsing.

Validation completed after these fixes:
- Full test suite passed:
  - 1433 passed
  - 30 skipped
- Python compile passed.
- Journal consistency passed.
- Enforcement readiness remained blocked as expected.
- Monitoring readiness kept paper trading disabled.
- Opening-range review passed as watch-only.
- Opening-range backtest remained read-only with known missing bar data.
- News evidence smoke passed.
- News outcome smoke passed.
- `git diff --check` passed.
- Protected data diff check was clean.

Next recommended action:
1. Final documentation review and final full audit.
2. Commit and push only if final audit remains clean.
3. Watch the next official-window Daily Picks run.
4. Inspect new artifacts if another no-pick day occurs:
   - no-pick report,
   - candidate rejection report,
   - market-data health,
   - hard-block log.
5. Do not add Finnhub yet unless real telemetry still proves official OHLCV/provider coverage is insufficient.

Important:
- Do not loosen filters blindly.
- Do not force official picks.
- No-pick days are acceptable only when clearly explained.
- Paper trading remains forbidden.
- Live trading remains forbidden.

## Active product-intelligence repair plan

The current priority roadmap for product-intelligence repair is documented in:

- `docs/planning/PRODUCT_INTELLIGENCE_REPAIR_PLAN.md`

Priority order:

1. Official no-pick root-cause explainability.
2. Watch-only outcome attribution v1.
3. Performance report source separation audit.
4. Late-news score calibration / GIG-style risk caps.
5. Opening-range quality evaluator.
6. Dynamic Theme Discovery Radar v0 — observe-only.
7. Theme-to-pick bridge v0 — observe-only.
8. Future theme-aware scoring only after validation.

Do not start paper trading, live trading, production theme-aware scoring, or official gate-loosening before these evidence and trust gaps are addressed.
