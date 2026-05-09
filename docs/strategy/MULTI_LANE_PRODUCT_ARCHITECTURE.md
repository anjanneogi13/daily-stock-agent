# Multi-Lane Product Architecture and Learning System

Last updated: 2026-05-09

## Executive summary

Daily Stock Agent is not a single stock-tip bot. It is intended to become a
multi-strategy, monitoring-first stock intelligence system.

The product should earn trust before it earns automation. The company can win
only if users can see:

- what the agent decided,
- why it decided that,
- what evidence was missing,
- what risks could invalidate the thesis,
- whether the decision was official or watch-only,
- whether the result was measured honestly,
- and whether the system stayed inside its safety boundaries.

Current operating posture:

- monitoring-only,
- not paper-trading-ready,
- not live-trading-ready,
- not public paid-launch-ready,
- official picks are separate from watch-only ideas,
- research-only ideas are separate from official statistics,
- no paper/live trading until readiness gates pass and founder explicitly approves.

Core product principle:

> Trust is the product.

## Product positioning

Preferred positioning:

> Transparent AI market research copilot for busy working professionals.

Avoid positioning:

- AI stock tip machine,
- guaranteed trading bot,
- automated wealth builder,
- personal financial advisor,
- black-box buy/sell signal service,
- market-beating promise,
- autonomous execution system.

The product can recommend research priorities and structured opportunities, but
it must not overclaim certainty. Every lane must make uncertainty visible.

## Lane overview

The intended product is composed of separate lanes. Each lane has its own data
needs, timing, scoring logic, risk profile, reporting, outcome attribution, and
promotion gates.

Do not collapse all lanes into one generic scoring model.

### Lane 1 — Premarket official daily stock pick before market open

Purpose:

- Make exactly one official premarket decision before market open.
- The decision can be:
  - validated official pick, or
  - validated official no-pick.

Better wording:

> Premarket official daily stock pick before market open, with clear rationale,
> risk/reward, entry/stop/take-profit, and no-pick handling when data is not
> ready.

Important correction:

A no-pick is not automatically a failure. Sometimes the correct official
decision is no-pick because data readiness, provider health, market state, risk
gates, or candidate quality is not good enough.

Current status as of this document:

- Lane 1 is code-complete / pre-cert ready.
- Priorities 15-18 are completed.
- CI #232 was green for the latest known pushed state.
- Priority 19 remains: observe/certify the next real scheduled premarket run.

Acceptance principle:

- The product requirement is not "always pick a stock."
- The product requirement is:
  - make one official premarket decision before market open,
  - produce either validated official pick artifacts or validated official no-pick artifacts,
  - publish only validated official outputs,
  - keep auditability and traceability,
  - keep paper/live trading disabled.

Key artifacts:

- `data/premarket_official_pick_YYYY-MM-DD_TICKER.json`
- `data/premarket_official_pick_summary_YYYY-MM-DD.json`
- `data/daily_picks_no_pick_report_YYYY-MM-DD.json`
- `data/daily_picks_no_pick_report_YYYY-MM-DD.md`
- `data/daily_picks_run_status_YYYY-MM-DD.jsonl`
- `data/market_data_health_YYYY-MM-DD.json`

Required behavior:

- Official daily picks remain blocked after 09:20 ET.
- Manual dispatch must not bypass the official cutoff.
- User-facing output must fail closed if matching official artifacts are missing or invalid.
- Missing both valid official pick artifacts and valid official no-pick artifact is a failure.
- Paper/live trading must remain disabled.

Current improvement gap:

- Priority 19 still needs real scheduled-run certification.
- Stooq/yfinance fallback needs real automatic official-window telemetry validation.
- Do not add Finnhub unless provider telemetry proves yfinance/Stooq is insufficient.

### Lane 2 — Post-open / late-daily watch-only opportunity lane

Purpose:

Capture opportunities that become visible only after the open without confusing
them with premarket official picks.

Better wording:

> Post-open / late-daily opportunity lane.

This lane can catch:

- stocks that became valid only after the open,
- earnings/news/catalyst moves,
- late-day continuation setups,
- watch-only opportunities until validated.

Safety boundary:

This lane must begin as watch-only / monitoring-only. It must not blindly
override the premarket official pick. It must not enter official daily-pick
statistics until separately validated and approved.

Initial implementation idea:

1. Define a dedicated post-open lane contract.
2. Reuse provider-health telemetry and data-readiness checks.
3. Produce post-open watch-only artifacts separate from official pick artifacts.
4. Add Telegram/GitHub copy that avoids executable "BUY now" language.
5. Track outcomes separately from premarket official decisions.
6. Add no-op / no-opportunity reports.
7. Only consider paper-trading readiness after enough evidence exists.

Potential artifacts:

- `data/post_open_watchlist_YYYY-MM-DD.json`
- `data/post_open_opportunity_report_YYYY-MM-DD.md`
- `data/post_open_run_status_YYYY-MM-DD.jsonl`
- `data/post_open_outcomes_YYYY-MM-DD.jsonl`

Current improvement gap:

- The repo should not call this an official after-open pick engine yet.
- It needs distinct contract, status ledger, reporting, tests, and outcome attribution.
- It must not mutate `data/picks_log.csv` until explicitly promoted.

### Lane 3 — Intraday scanner / opening-range / market-session observations

Purpose:

Observe intraday setups and learn from them without pretending they are validated
official picks.

Current examples:

- opening-range observations,
- intraday momentum observations,
- watch-only intraday candidates,
- retained bars and outcome review.

Future form:

> Intraday pick engine with strict gates, risk limits, and real-time alerting.

Current posture:

- observe-only,
- watch-only,
- not official picks,
- not paper trades,
- not buy instructions.

Implementation idea:

1. Preserve opening-range bars and runtime artifacts.
2. Capture timestamps using America/New_York.
3. Suppress new intraday opportunities after 15:15 ET.
4. Separate existing-pick monitoring from new-opportunity discovery.
5. Use observed/reference-level wording instead of executable entry wording.
6. Attribute outcomes by time of day, volume, VWAP behavior, and market regime.
7. Promote only after evidence, backtests, forward observation, and founder approval.

Key learning dimensions:

- opening-range breakout quality,
- false breakout conditions,
- volume confirmation,
- VWAP behavior,
- market regime effect,
- time-of-day performance,
- news/catalyst confirmation,
- slippage sensitivity.

Current improvement gap:

- Opening-range backtests may still have missing-bar-data rows.
- Opening-range bar artifact capture may still need hardening.
- Opening-range remains watch-only.

### Lane 4 — Monster Hunter, Compounder, and Long-Term Opportunity lanes

Purpose:

Research longer-horizon and thesis-driven opportunities without contaminating
short-term trading logic.

These should be separate product lanes:

1. Monster Hunter
   - short-term explosive opportunity,
   - high volatility,
   - high catalyst,
   - high failure risk,
   - requires strong guardrails.

2. Consistent Compounder
   - quality growth,
   - durable earnings,
   - lower churn,
   - longer holding horizon.

3. Long-Term Opportunity
   - multi-week/month thesis,
   - valuation,
   - sector trend,
   - institutional support.

4. Turnaround / Deep Value
   - optional later,
   - higher uncertainty,
   - requires stronger fundamental evidence.

Safety boundary:

These lanes must not use the same scoring logic as intraday or daily picks. They
must remain research-only / monitoring-only until historically validated and
explicitly approved.

Implementation idea:

1. Define separate schemas for thesis, catalyst, risk, invalidation, and horizon.
2. Keep outputs separate from day/swing/intraday/opening-range stats.
3. Do not allow failed swing trades to silently become monster holds.
4. Do not call speculative news spikes "monsters" without fundamental evidence.
5. Use watchlist/report artifacts first.
6. Backtest and forward observe before scoring influence.
7. Require founder approval before any production scoring impact.

Current improvement gap:

- Monster Hunter is primarily documented, not production-validated.
- It must not influence official daily picks yet.

## Learning and calibration architecture

The agent should learn, but not by silently changing itself.

Correct loop:

1. Agent reviews outcomes.
2. Agent extracts lessons.
3. Agent records calibration notes.
4. Agent proposes code/config changes.
5. Changes are tested.
6. Changes are reviewed and committed through controlled workflow.
7. Results are monitored after promotion.

Forbidden loop:

- Agent observes an outcome and directly mutates production scoring with no
  test, no audit trail, no versioning, and no human approval.

### Premarket official pick learning

The system should review:

- whether the official pick worked,
- whether the official no-pick was correct,
- whether readiness gates behaved correctly,
- whether provider health affected the outcome,
- whether risk/reward was realistic,
- whether rationale matched outcome.

### Post-open learning

Post-open setups behave differently from premarket setups. They need their own:

- outcome review,
- reason attribution,
- no-opportunity analysis,
- timing analysis,
- volatility and liquidity analysis,
- calibration notes.

### Intraday learning

Intraday learning should study:

- opening-range breakouts,
- false breakouts,
- VWAP reclaim/failure,
- volume confirmation,
- time-of-day edge,
- market regime,
- news confirmation,
- slippage sensitivity,
- alert fatigue and duplicate alerts.

## Reporting system

The product needs a reporting stack, not just alerts.

Required report families:

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
- Watch-only vs official pick comparison.

Reports should feed controlled calibration, not automatic self-modification.

## Book / wisdom / historical learning system

The agent may study trading/investing concepts, but it must not copy books or
blindly encode untested aphorisms.

Correct process:

1. Use only legally accessible/public-domain/licensed/founder-provided materials.
2. Extract reusable principles.
3. Convert principles into hypotheses.
4. Convert hypotheses into testable rules.
5. Backtest with train/test split.
6. Walk-forward test.
7. Forward observe.
8. Promote only after evidence and founder approval.

Example:

Book principle:

> Volume confirms breakouts.

Testable rule candidate:

> Opening-range breakouts with volume ratio greater than X outperform those
> below X after costs and slippage.

Rules start observe-only. No book-derived rule may bypass data-quality or
readiness gates.

## Historical backtesting and validation

Before promoting logic into production scoring, the agent should run:

- historical backtests,
- walk-forward tests,
- out-of-sample validation,
- regime-separated evaluation,
- slippage and transaction cost assumptions,
- SPY/QQQ benchmark comparison.

Critical anti-overfit rules:

- Never test on the same period used to derive the rule.
- Validate across bull, bear, sideways, high-volatility, and low-volatility regimes.
- Track drawdown, expectancy, sample size, and stability.
- Prefer robust simple rules over fragile curve-fit rules.

## Chart and technical-analysis layer

The first version should be quantitative chart reading, not image interpretation.

Initial chart features:

- trend,
- support/resistance,
- moving averages,
- volume,
- VWAP,
- RSI/MACD,
- gap behavior,
- breakout/base patterns,
- relative strength,
- multi-timeframe confirmation.

Later, visual/chart-image interpretation can be considered if it improves
evidence quality and can be validated.

Goal:

> Agent performs multi-timeframe technical analysis and chart-pattern
> recognition, then validates which chart patterns actually improve expectancy.

## First-class product pillars

### Data readiness and provider reliability

The agent must always know:

- Is data available?
- Is data stale?
- Did provider fail?
- Was the market closed?
- Was the signal based on complete or partial evidence?

No pick should be made from broken data.

Provider fallback safety rules:

- no fake official picks,
- no stale/cached official picks unless explicit freshness rules allow it,
- provider-health observable,
- failure-loud if all providers fail,
- monitoring-only,
- no paper/live trading.

### Risk management and portfolio construction

A great stock idea can still be a bad trade if sizing/risk is wrong.

Future risk rules should cover:

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

Current gap:

- The product is not paper-trading-ready because risk-management and execution
  readiness are not mature enough.

### Execution simulation and staged promotion

Promotion ladder:

1. Observe-only.
2. Paper trading.
3. Limited live trading.
4. Scaled live trading.

Each stage needs explicit promotion criteria:

- minimum sample size,
- positive expectancy,
- acceptable drawdown,
- stable win rate,
- slippage tolerance,
- no data-readiness failures,
- all reports generated correctly,
- founder approval.

Paper trading remains forbidden until gates pass.

Live trading remains forbidden.

### Missed-opportunity analysis

The agent must study what it missed, not only what it picked.

Questions:

- What did we miss?
- Did a high-performing stock appear in watch-only but not official picks?
- Was it blocked correctly?
- Did the scoring system under-rank it?
- Did provider/data failure hide it?
- Did timing rules exclude it correctly?

This is one of the most important learning loops.

### No-pick intelligence

A no-pick day is not a failure if data, market, or quality was poor.

The system should learn:

- when no-pick was correct,
- when no-pick missed opportunity,
- whether filters were too strict,
- whether data failure caused no-pick,
- whether provider fallback needs improvement,
- whether no-pick rationale was clear to users.

### Market regime awareness

Every strategy behaves differently depending on regime.

The product should classify:

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

Reports and backtests should evaluate each strategy by regime.

### Strategy separation

Separate engines should exist for:

- Premarket daily pick engine,
- Post-open daily watch-only/opportunity engine,
- Opening-range/intraday engine,
- Momentum continuation engine,
- Monster Hunter engine,
- Compounder engine,
- Long-term opportunity engine,
- Theme discovery engine.

A meta-layer may eventually decide which lane is active and safe, but only after
each lane has its own evidence and safety gates.

### Explainability and audit trail

Every pick or watch-only candidate should answer:

- Why this ticker?
- Why today?
- What evidence supports it?
- What evidence argues against it?
- What would invalidate the thesis?
- What data was missing?
- What rule selected it?
- What model/config version selected it?
- Was it official, watch-only, research-only, or blocked?

This is essential for trust.

### Model, config, and experiment tracking

Every scoring change should be traceable:

- scoring version,
- config version,
- prompt version if LLM is used,
- feature version,
- backtest result,
- promotion date,
- rollback path.

Without versioning, learning becomes messy and unverifiable.

### Alerts and user experience

Future user-facing surfaces:

- Telegram alerts,
- dashboard,
- daily brief,
- execution-ready card only after appropriate product stage,
- confidence/risk labels,
- "why not picked" explanation,
- watchlist updates,
- no-pick explanations,
- missed-opportunity summaries.

Current reports are a foundation, not a finished consumer UX.

### Compliance and safety boundary

Because this is stock-picking software, the product must maintain clear
boundaries:

- observe-only until validated,
- no buy instructions unless product mode explicitly allows,
- risk disclosures,
- audit logs,
- human approval before execution,
- no hidden self-modifying production behavior,
- no paper/live trading without explicit readiness and founder approval.

## Extended product, business, and operational lanes (23–31)

These lanes were added on 2026-05-09 after a brutally honest co-founder review of the original 22 lanes. They cover product/business and operational pillars that were missing from the technical lane list but materially affect whether the product can succeed.

### Lane 23 — Customer / product validation

The product is currently strong on engineering discipline and weak on customer evidence.

- Goal: prove (or disprove) that target users will pay for the product before scaling lane work.
- Evidence required:
  - structured customer interviews (call, email, WhatsApp),
  - documented pain points in users' own words,
  - real willingness-to-pay data (not polite yes),
  - referrals as a leading indicator.
- Safety:
  - interview notes stay outside the repo (privacy, personal data),
  - no public claims about user demand without evidence,
  - no over-promising features to prospects.
- Trigger to advance other lanes: at least 5 strangers (not friends) describe the same core pain.
- Trigger to pivot: 4+ of 5 say they only care about a different market (e.g. Indian stocks vs US-only product).

### Lane 24 — Latency / freshness contract

The "premarket pick before market open" promise is a latency contract. There is currently no formal latency budget.

- Goal: make freshness/latency a first-class, measured pillar.
- Required artifacts (future):
  - per-stage latency budget (fetch, score, decide, format, send),
  - per-run latency telemetry,
  - alerting if any stage exceeds budget,
  - clear "data freshness" labels in user-facing output.
- Safety:
  - no official pick may be sent past the official cutoff,
  - if budget is breached, prefer no-pick over late-pick,
  - never silently relax freshness requirements.

### Lane 25 — Failure mode + incident response runbooks

`PRODUCT_FAILURE_AND_WIN_STRATEGY.md` lists failure modes. There are no documented runbooks for what to do when each one fires.

- Goal: every known failure mode has a written response procedure.
- Required artifacts (future):
  - `docs/runbooks/` directory,
  - per-failure runbook (Telegram down, providers down, schedule missed, workflow failed, secret expired, etc.),
  - clear escalation path,
  - post-incident review template.
- Safety:
  - runbooks must default to safe-stop (no-pick) over risky-recover,
  - no runbook may bypass paper/live trading prohibitions,
  - founder must be notified for any incident affecting users.

### Lane 26 — Cost / budget / unit economics

Solo founders die from compounding infrastructure costs (GitHub Actions minutes, LLM API calls, data provider fees, hosting). There is currently no explicit budget tracking.

- Goal: make cost a first-class pillar tracked per-run and per-month.
- Required artifacts (future):
  - per-run cost telemetry,
  - monthly cost roll-up,
  - per-user cost projection at hypothetical scale,
  - kill-switch if a run exceeds N× normal cost.
- Safety:
  - no production behavior may silently increase cost beyond a budget threshold without alert,
  - LLM/provider keys must have hard spend caps where supported.

### Lane 27 — Legal / regulatory / disclaimer / marketing-copy boundaries

US stock-picking software has SEC implications (Investment Advisers Act considerations, "investment advice" boundaries, marketing rules). The product is currently safe because monitoring-only and not commercially distributed, but the boundary becomes existential the moment users pay or marketing copy claims advice.

- Goal: explicit, lawyer-reviewed legal boundaries before public/paid launch.
- Required artifacts (future):
  - disclaimer copy for every user-facing surface,
  - documented "research, not advice" positioning,
  - terms of service,
  - privacy policy,
  - separation of "research output" vs "advice",
  - if Indian-stocks expansion happens later: SEBI considerations.
- Safety:
  - no marketing copy may claim alpha, guaranteed returns, advisory service, or trade execution capability,
  - "not investment advice" disclaimer required on every official user-facing artifact before public distribution,
  - founder may not give individualized investment advice in any user channel.

### Lane 28 — Observability + alerting on the agent itself (not on stocks)

We monitor markets and provider health, but we do not yet monitor the agent system as an operational system. Silent agent failures are invisible until users complain — and we don't have users yet.

- Goal: treat the agent system as a production system with operational telemetry, alerts, and uptime tracking.
- Required artifacts (future):
  - workflow run success-rate dashboard,
  - missed-cron alerts,
  - secret-expiry alerts,
  - Telegram-send failure alerts,
  - GitHub-Actions-minute usage tracking,
  - simple uptime page (internal).
- Safety:
  - agent-self alerts go only to founder,
  - no user data exposed in agent telemetry,
  - alert fatigue is a real risk; tune thresholds before adding more.

### Lane 29 — Data lineage + reproducibility

P16 traceability adds decision/artifact IDs. Full reproducibility requires more — anyone should be able to ask "why did the agent pick AAPL on 2026-04-15" and get the exact data, config, code, prompt, and model versions used, deterministically.

- Goal: every official decision is reproducible from inputs to output.
- Required artifacts (future):
  - data snapshot per official run,
  - config snapshot per official run,
  - code commit SHA per official run (already partially done),
  - LLM prompt + response capture (sanitized),
  - "replay" tool to re-run a past decision deterministically.
- Safety:
  - reproducibility data may contain prompt content; classify as private,
  - no PII may enter prompts or get captured,
  - replay must never trigger live external calls (no LLM, no Telegram).

### Lane 30 — Privacy + secrets management

API keys, Telegram tokens, future broker tokens, and (eventually) user data live in this system. Current setup is fine for solo development. It is not fine for any of: a co-founder, an employee, a customer-data path, or a public open-sourcing decision.

- Goal: explicit secrets and privacy posture suitable for the next-stage company.
- Required artifacts (future):
  - secrets inventory + rotation schedule,
  - documented access boundaries,
  - encryption-at-rest policy for any future user data,
  - data retention policy,
  - documented deletion path for any future user data,
  - explicit "no PII in logs / artifacts / commits" rule.
- Safety:
  - no secret may be committed to the repo (already enforced),
  - no LLM call may include a secret in the prompt,
  - any future user data must default to deny-by-default access.

### Lane 31 — Onboarding / setup-from-scratch

A future collaborator (or future-you on a fresh machine) should be able to clone the repo, follow a README, and have a working agent running locally inside ~30 minutes. Current state: not verified, possibly broken.

- Goal: a reproducible, friction-free setup path that does not require tribal knowledge.
- Required artifacts (future):
  - tested `make setup` or equivalent,
  - dev-environment doc with version pins,
  - sample `.env.example` with every required key,
  - one-command smoke test post-setup,
  - quarterly verification that setup still works.
- Safety:
  - sample `.env.example` must contain only placeholders (never real keys),
  - smoke-test must not write to live providers, send Telegram, or hit the real GitHub API,
  - new-collaborator setup must default to monitoring-only flags.

### Honest sequencing recommendation for lanes 23–31

These do not all need to happen now, and they cannot all happen at once. Suggested order based on co-founder review:

1. **Lane 23 (Customer validation)** — start now, in parallel with Lane 1 cert. Highest ROI activity in the entire product.
2. **Lane 27 (Legal boundaries)** — needed before any public/paid launch, but can be quietly drafted in parallel.
3. **Lane 25 (Runbooks)** — needed before the first real user-facing failure.
4. **Lane 30 (Privacy/secrets)** — needed before second contributor or first user data.
5. **Lane 28 (Agent observability)** — needed before scaling beyond founder use.
6. **Lane 24 (Latency contract)** — formalize after Lane 1 P19 cert observed live.
7. **Lane 26 (Cost)** — needed before scaling LLM/provider usage.
8. **Lane 29 (Reproducibility)** — needed for trust marketing and post-incident analysis.
9. **Lane 31 (Onboarding)** — needed before second contributor.

None of these justify pausing Lane 1 P19 certification or postponing the first 5 customer interviews. Customer validation comes first.

## Current lag / improvement map

### Strong areas

- Monitoring-only discipline is explicit.
- Lane 1 official/no-pick artifact architecture is now strong.
- User-facing output now fails closed when official artifacts are missing/invalid.
- Official traceability and workflow observability are improved.
- Tests are broad and currently green as of latest known CI.
- Safety posture is better than typical hobby stock bots.

### Weak or immature areas

- Priority 19 still requires real scheduled-run certification.
- Provider fallback needs real official-window telemetry observation.
- Post-open lane is not yet formally designed/implemented.
- Opening-range bar capture and outcome quality need improvement.
- Paper-trading readiness remains blocked.
- Risk management and portfolio construction are not mature enough.
- Market regime awareness is not yet first-class enough.
- Customer validation is still weak.
- Documentation is strong, but market validation is not the same as product-market fit.

### Near-term recommended order

1. Certify Priority 19 from the next real scheduled premarket run.
2. Validate yfinance/Stooq/provider telemetry from real official-window evidence.
3. Do not add Finnhub unless telemetry proves it is needed.
4. Begin Lane 2 as post-open watch-only opportunity lane, not official picks.
5. Add opening-range bar artifact capture if still missing.
6. Improve opening-range outcome analysis after bars exist.
7. Build watch-only vs official comparison reports.
8. Continue news evidence workflow validation.
9. Convert evidence into customer-facing trust assets.
10. Start Probability Engine Phase 2 only as observe-only.
11. Keep Monster Hunter research-only until evidence supports promotion.

## Fresh-session recovery instruction

A new agent should recover product state from:

1. `README.md`
2. `docs/README.md`
3. `docs/PROJECT_BLUEPRINT.md`
4. `docs/NEXT_SESSION.md`
5. `docs/WORK_LOG.md`
6. `docs/planning/LANE1_FINAL_PRODUCTION_HARDENING_PLAN.md`
7. this document:
   `docs/strategy/MULTI_LANE_PRODUCT_ARCHITECTURE.md`

But the agent must verify reality from:

- code,
- tests,
- workflows,
- data artifacts,
- GitHub Actions,
- git history.

Docs are the map. Code/tests/workflows/actions are reality.

## Companion implementation roadmap

The executable implementation plan for this architecture is:

- `docs/planning/MULTI_LANE_IMPLEMENTATION_ROADMAP.md`

Use the architecture document to understand what the product should become. Use the implementation roadmap to decide what to build next, in what order, with what safety gates.
