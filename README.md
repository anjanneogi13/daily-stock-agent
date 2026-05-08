# Daily Stock Agent

Daily Stock Agent is an AI-assisted US-equity research and monitoring system.

It generates official premarket model picks, monitors active picks, records evidence, evaluates outcomes, and produces reports. It also collects watch-only and research-only market ideas without mixing them into official pick statistics.

## Current Status

Current operating posture:

- monitoring-only
- no paper trading
- no live trading
- official picks are separated from watch-only ideas
- research-only ideas are separated from official statistics
- no-pick days are allowed when candidates fail safety or quality gates
- watch-only ideas must not use buy/sell instruction language

This repository is research software, not financial advice.

## What the Agent Does

Current capabilities include:

- daily official pick generation before the premarket cutoff
- Telegram notifications for official picks and clearly labeled watch-only alerts
- intraday monitoring for TP/SL and position-status updates
- late daily watch-only fallback ideas when the official window is missed
- opening-range and intraday momentum observation capture
- news engine monitoring, run-status evidence, and news outcome attribution scaffolds
- no-pick diagnostics, candidate rejection reports, and market-data health evidence
- end-of-day official pick evaluation
- weekly, monthly, quarterly, and yearly reporting
- repository health, readiness, and journal consistency audits

## Safety Boundaries

The agent may:

- recommend
- monitor
- explain
- evaluate
- report
- learn from evidence

The agent must not:

- execute real-money trades
- enable paper trading by default
- silently promote watch-only ideas into official picks
- mix research-only ideas with official pick statistics
- force picks just to avoid a no-pick day

Paper/live trading remain disabled until explicit readiness gates and founder approval are satisfied.

## Key Documentation

Start here:

| File | Purpose |
|---|---|
| docs/README.md | Documentation map |
| docs/PROJECT_BLUEPRINT.md | Canonical current architecture, state, and operating policy |
| docs/NEXT_SESSION.md | Current handoff and next recommended work |
| docs/WORK_LOG.md | Append-only work history |
| docs/planning/README.md | Planning documentation index |

Planning docs:

| File | Purpose |
|---|---|
| docs/planning/FEATURE_BACKLOG.md | Future feature backlog and implementation phases |
| docs/planning/DATA_CONTRACTS.md | Data artifacts, schemas, ownership, and safety boundaries |
| docs/planning/NOTIFICATION_ARCHITECTURE.md | Notification types, wording rules, and future shared renderer plan |
| docs/planning/CANDIDATE_LIFECYCLE.md | Candidate states, transitions, readiness gates, and anti-corruption rules |

## Local Development

Install dependencies:

    pip install -r requirements.txt

Create local environment file:

    cp .env.example .env

Run tests:

    python3 -m pytest tests/ -q --tb=short --disable-warnings

Run key audits:

    python scripts/audit_journal_consistency.py --strict
    python scripts/check_enforcement_readiness.py
    python scripts/monitoring_readiness.py

Run dashboard locally:

    streamlit run app.py

## Important Workflows

GitHub Actions workflows live under:

    .github/workflows/

Important workflow lanes include:

- CI
- daily picks
- watchdog
- late watch-only fallback
- intraday monitor
- news engine
- news evidence
- end-of-day evaluation
- weekly/monthly/yearly reports
- backup and health routines

The workflow list changes over time. Treat .github/workflows/ as the current implementation source.

## Data and Reports

Runtime and evidence artifacts are primarily under:

    data/
    reports/

Important rule:

- data/picks_log.csv is for official model picks only.
- Watch-only, research-only, rejected, backtest, and paper/live candidate artifacts must remain separate unless explicitly promoted by approved logic.

See docs/planning/DATA_CONTRACTS.md and docs/planning/CANDIDATE_LIFECYCLE.md before adding or changing artifacts.

## Required Secrets

Common GitHub Actions secrets include:

| Secret | Purpose |
|---|---|
| ANTHROPIC_API_KEY | Claude/LLM support where enabled |
| GEMINI_API_KEY | Gemini fallback where enabled |
| FINNHUB_API_KEY | Fundamentals, news, earnings, or future provider lanes |
| TELEGRAM_BOT_TOKEN | Telegram bot identity |
| TELEGRAM_CHAT_ID | Personal Telegram chat ID |
| TELEGRAM_GROUP_CHAT_ID | Optional group Telegram chat ID |

Some workflows can run partially or safely degrade when optional credentials are missing.

## Disclaimer

This project is research and monitoring software only.

It is not financial advice, not an investment adviser, and not an automated trading system. Always verify independently before risking capital.
