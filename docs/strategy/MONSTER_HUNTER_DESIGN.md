# Monster Hunter / Long-Term Compounder Analyst — Design

Status: planned architecture track
Mode: research-only / monitoring-only
Trading impact: no official picks, no paper trades, no live trades

## Purpose

Monster Hunter is a separate long-term research lane for identifying potential 6-month to 5-year compounders and multi-bagger candidates.

It must not behave like the day-trading or swing-trading engine.

The goal is to make the agent a serious long-term analyst that can understand:

- company fundamentals,
- quarterly and yearly P&L trends,
- future business prospects,
- secular 5-10 year themes,
- ETF and mutual fund focus areas,
- institutional accumulation,
- competitive moat,
- management execution,
- valuation risk,
- long-term chart structure,
- thesis invalidation.

Monster candidates should be treated as research theses first, not buy instructions.

## Non-negotiables

- Monster Hunter is research-only until explicitly promoted.
- No monster output may enter paper trading or live trading.
- No monster output may contaminate official daily pick statistics.
- No failed swing trade may silently become a monster hold.
- No speculative news spike may be called a monster without fundamental evidence.
- All monster conclusions must include evidence, risks, and thesis-break conditions.
- Any rule learned from history, books, filings, or research must start in observe mode.
- Founder/co-founder approval is required before any monster rule affects production scoring.

## Why this matters

Daily and swing picks can create frequent engagement, but true long-term compounder identification can create life-changing outcomes and a stronger product moat.

The agent should eventually be able to say:

- why a sector may grow for the next 10 years,
- which companies are likely to benefit most,
- whether fundamentals support the story,
- whether institutional/ETF ownership confirms the theme,
- what risks could break the thesis,
- when to add, trim, hold, or exit.

Example theme logic:

AI creates demand for data centers.
Data centers require advanced semiconductors and high-bandwidth memory.
That can benefit semiconductor designers, foundries, memory suppliers, equipment makers, networking companies, power infrastructure, and cooling providers.
The agent should identify both first-order and second-order beneficiaries.

## Separate trading lane

Monster Hunter is a separate lane from:

- premarket swing picks,
- intraday opportunities,
- opening-range observations,
- late watch-only daily ideas.

Monster Hunter has different rules:

| Area | Day/Swing | Monster Hunter |
|---|---|---|
| Time horizon | intraday to weeks | 6 months to 5 years |
| Main driver | price/news/setup | business quality + secular theme |
| Stop logic | technical/risk stop | thesis invalidation |
| Evidence | catalyst + chart + score | fundamentals + theme + moat + valuation |
| Output | pick/alert/watch-only | research thesis/watchlist state |
| Evaluation | R multiple / TP / SL | thesis progress, fundamental trend, multi-year return |

## Core architecture

### Layer 1 — Theme Radar

Purpose:

Identify sectors and themes that may grow for 5-10 years.

Inputs may include:

- news trends,
- earnings call themes,
- SEC filing language,
- company guidance,
- ETF holdings and weight changes,
- mutual fund and institutional ownership,
- sector relative strength,
- macro policy,
- capex cycles,
- analyst estimate revisions,
- supply-demand imbalance,
- technology adoption curves.

Example themes:

- AI infrastructure,
- high-bandwidth memory,
- semiconductor equipment,
- data centers,
- power grid and electrification,
- cybersecurity,
- robotics,
- GLP-1 and obesity drugs,
- defense modernization,
- space infrastructure,
- nuclear power,
- cloud infrastructure,
- edge AI,
- autonomous systems.

Outputs:

- theme_name,
- theme_stage: emerging, accelerating, mature, crowded, fading,
- theme_score,
- likely beneficiaries,
- second-order beneficiaries,
- major risks,
- evidence links,
- review date.

### Layer 2 — Fundamental Deep Analyzer

Purpose:

Understand the actual business quality behind a candidate.

Analyze:

- revenue growth: 1Y, 3Y, 5Y,
- gross margin trend,
- operating margin trend,
- net income trend,
- EPS growth,
- free cash flow trend,
- free cash flow margin,
- return on invested capital,
- return on equity,
- debt and liquidity,
- share dilution or buybacks,
- guidance trend,
- earnings surprise history,
- analyst revisions,
- valuation versus history,
- valuation versus peers,
- customer concentration,
- cyclicality,
- management credibility.

Outputs:

- growth_score,
- margin_score,
- earnings_quality_score,
- balance_sheet_score,
- cash_flow_score,
- valuation_risk_score,
- dilution_risk_score,
- quality_score,
- fundamental_summary,
- red_flags.

### Layer 3 — Moat and Future Prospects Analyzer

Purpose:

Determine whether the company can win for years.

Questions:

- What is the company's durable advantage?
- Is the moat based on IP, scale, ecosystem, data, switching costs, cost advantage, regulation, brand, or network effects?
- Is the total addressable market expanding?
- Is the company gaining market share?
- Are customers locked in?
- Can competitors copy the product?
- Are margins sustainable?
- Is pricing power improving?
- Does management allocate capital well?
- What would break the long-term thesis?

Outputs:

- moat_score,
- moat_type,
- market_share_trend,
- pricing_power_score,
- competitive_risk,
- thesis_break_conditions.

### Layer 4 — ETF / Mutual Fund / Institutional Focus Analyzer

Purpose:

Understand where long-term capital is flowing.

Analyze:

- ETF sector inflows,
- thematic ETF holdings,
- ETF weight changes,
- mutual fund concentration,
- 13F ownership changes where available,
- institutional accumulation,
- top holders,
- overcrowding risk,
- sector rotation.

Signals:

- stock added to important ETF,
- weight rising in thematic ETF,
- ownership increasing across multiple high-conviction funds,
- sector fund inflows accelerating,
- company appears as a top holding in several relevant funds.

Risks:

- crowded ownership,
- bubble-like flows,
- valuation disconnected from fundamentals,
- theme peak risk.

Outputs:

- institutional_confirmation_score,
- etf_flow_score,
- ownership_trend,
- crowding_risk,
- fund_focus_summary.

### Layer 5 — Monster Candidate Scorer

Purpose:

Rank long-term candidates using multiple evidence types.

Example score components:

- theme_tailwind_score,
- revenue_acceleration_score,
- margin_expansion_score,
- earnings_quality_score,
- moat_score,
- institutional_confirmation_score,
- long_term_relative_strength_score,
- valuation_risk_adjustment,
- balance_sheet_risk_adjustment,
- dilution_risk_adjustment.

Outputs:

- monster_score,
- monster_confidence,
- candidate_rank,
- reason_summary,
- risk_summary,
- required_followup.

### Layer 6 — Thesis State Machine

Every monster candidate must have a state.

Allowed states:

- Candidate,
- Researching,
- Watchlist,
- Starter Position Candidate,
- Confirmed Compounder,
- Core Hold,
- Add-on Zone,
- Trim Zone,
- Exit Watch,
- Thesis Broken,
- Rejected.

Example state rules:

Candidate to Watchlist:

- strong theme score,
- fundamentals improving,
- no major balance-sheet red flags,
- valuation not extreme relative to growth.

Watchlist to Confirmed Compounder:

- multiple quarters of revenue acceleration,
- margin expansion,
- positive free cash flow or clear path to it,
- strong relative strength,
- institutional or ETF confirmation,
- no thesis-breaking risk.

Confirmed Compounder to Exit Watch:

- guidance cut,
- margin deterioration,
- theme demand weakening,
- valuation extreme while growth slows,
- long-term chart breakdown.

Exit Watch to Thesis Broken:

- fundamentals deteriorate,
- moat weakens,
- competitors gain share,
- management loses credibility,
- secular theme fades.

### Layer 7 — Long-Term Risk and Exit System

Monster Hunter should not use ordinary tight swing stops.

Risk should be based on:

- thesis invalidation,
- earnings deterioration,
- long-term moving average breaks,
- valuation extreme plus slowing growth,
- major management issue,
- competitive displacement,
- balance-sheet deterioration,
- theme fading,
- position-size concentration.

Outputs:

- hold_reason,
- add_reason,
- trim_reason,
- exit_watch_reason,
- thesis_broken_reason.

## Historical learning connection

Monster Hunter should eventually study historical true monsters and fake monsters.

True monster examples to study:

- AAPL,
- MSFT,
- AMZN,
- NVDA,
- TSLA,
- NFLX,
- AVGO,
- AMD,
- ASML,
- TSM,
- COST,
- UNH,
- META,
- GOOGL.

Fake or failed monster categories to study:

- dot-com bubble failures,
- SPAC bubble failures,
- meme stocks,
- profitless growth collapses,
- dilutive small caps,
- contract-news pump stocks,
- overhyped biotech names.

Questions to answer:

- What did true monsters look like early?
- What separated them from fake hype?
- Which fundamental signals appeared before multi-bagger returns?
- Which valuation levels were survivable?
- What drawdowns were normal?
- What broke the thesis?
- Which sectors created monsters in each market era?

## Data sources

Near-term possible sources:

- yfinance financials,
- SEC filings,
- company investor relations,
- earnings call transcripts if legally available,
- ETF issuer holdings files,
- FRED macro data,
- public sector/theme classifications,
- Stooq/yfinance price history.

Later possible sources:

- Finnhub fundamentals and news,
- Financial Modeling Prep,
- Polygon,
- Tiingo,
- TIKR,
- 13F data providers,
- ETF data providers.

Only legal and allowed data sources may be used.

## Output artifacts

Future research-only artifacts may include:

- data/monster_themes_YYYY-MM-DD.jsonl,
- data/monster_candidates_YYYY-MM-DD.jsonl,
- data/monster_theses_YYYY-MM-DD.jsonl,
- data/monster_state_transitions_YYYY-MM-DD.jsonl,
- reports/monster_hunter_report_YYYY-MM-DD.md.

These artifacts must remain separate from:

- data/picks_log.csv,
- data/signal_journal.jsonl,
- data/learning_journal.jsonl,
- paper-trade artifacts,
- live-trade artifacts.

## First safe implementation slice

Monster Hunter v0 should be documentation and research-only.

Recommended first slice:

1. Define schema for monster themes, candidates, theses, and state transitions.
2. Create a small semiconductor / AI memory pilot universe.
3. Generate a watch-only Monster Research Report.
4. Include fundamentals, theme evidence, risks, and thesis-break conditions.
5. Do not produce official picks.
6. Do not send buy/sell instructions.
7. Do not enable paper/live trading.

Possible pilot universe:

- NVDA,
- AMD,
- AVGO,
- MRVL,
- MU,
- WDC,
- STX,
- TSM,
- ASML,
- AMAT,
- LRCX,
- KLAC.

## Product value

Monster Hunter supports the product mission:

- transparent long-term research,
- explainable thesis,
- audited evidence,
- working-professional friendly summaries,
- stronger public content,
- stronger trust layer,
- potential future premium feature.

It also supports the business plan differentiators:

- probability-based decisions,
- audited/open research,
- built for working professionals who lack time to do deep research.

## Promotion path

Monster Hunter outputs should mature through this path:

Research-only report
to watchlist
to thesis state tracking
to historical validation
to forward observation
to founder-approved scoring influence
to possible future premium product feature.

No direct production trading effect is allowed before validation.
