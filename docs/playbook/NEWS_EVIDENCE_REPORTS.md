# News Evidence Reports Playbook

**Mode:** monitoring-only
**Paper trading:** disabled
**Live trading:** disabled
**Last updated:** 2026-05-07

This playbook explains how to generate and validate News Signal Evidence reports and news signal outcome attribution artifacts.

These reports are for evidence collection only. They must not create official picks, paper trades, live trades, or journal mutations.

## What this produces

For a report date YYYY-MM-DD, the News Evidence workflow/scripts may create:

- data/news_signal_outcomes_YYYY-MM-DD.jsonl
- data/news_signal_evidence_report_YYYY-MM-DD.json
- data/news_signal_evidence_report_YYYY-MM-DD.md

These are reporting artifacts only.

They must not mutate:

- data/picks_log.csv
- data/signal_journal.jsonl
- data/learning_journal.jsonl
- data/premarket_check.json
- data/telegram_sent.json

## Safety rules

Non-negotiable:

1. Do not start paper trading.
2. Do not enable real-money trading.
3. Do not manually enable enforcement flags.
4. Do not treat news evidence rows as official picks.
5. Do not use outcome rows to tune score deltas until enough sample size exists.
6. Do not commit accidental runtime files beyond the intended reporting artifacts.

Expected safety fields:

- mode=monitoring_only
- read_only=true
- official_pick_stats_mutated=false
- paper_trading_enabled=false
- live_trading_enabled=false

## Manual local no-write smoke

Use no-write mode first when auditing or debugging:

- python scripts/news_signal_outcome_attribution.py --date YYYY-MM-DD --max-items 3 --horizon-days 3 --no-write
- python scripts/news_signal_evidence_report.py --date YYYY-MM-DD --no-write

No files should be written by these commands.

After no-write smoke, check:

- git status -sb
- git diff -- data/picks_log.csv data/signal_journal.jsonl data/learning_journal.jsonl data/premarket_check.json data/telegram_sent.json

Expected: no official data diff.

## Manual local write

Only write reporting artifacts after no-write smoke passes:

- python scripts/news_signal_outcome_attribution.py --date YYYY-MM-DD --max-items 100 --horizon-days 3
- python scripts/news_signal_evidence_report.py --date YYYY-MM-DD

Expected files:

- data/news_signal_outcomes_YYYY-MM-DD.jsonl
- data/news_signal_evidence_report_YYYY-MM-DD.json
- data/news_signal_evidence_report_YYYY-MM-DD.md

Then verify official data did not change:

- git diff -- data/picks_log.csv data/signal_journal.jsonl data/learning_journal.jsonl data/premarket_check.json data/telegram_sent.json

## GitHub Actions manual workflow

Workflow:

- .github/workflows/news_evidence.yml

GitHub UI:

- Actions -> News Evidence -> Run workflow

Recommended safe manual inputs:

- Branch: main
- date: YYYY-MM-DD
- max_items: 3
- horizon_days: 3

For normal scheduled/report generation:

- max_items: 100
- horizon_days: 3

After it completes, verify the bot commit changed only:

- data/news_signal_outcomes_YYYY-MM-DD.jsonl
- data/news_signal_evidence_report_YYYY-MM-DD.json
- data/news_signal_evidence_report_YYYY-MM-DD.md

The commit message should look like:

- news evidence report YYYY-MM-DD [skip ci]

## Pulling workflow artifacts locally

After a successful workflow run:

- git status -sb
- git pull --ff-only origin main
- git log -5 --oneline --decorate

Then verify artifacts exist:

- data/news_signal_outcomes_YYYY-MM-DD.jsonl
- data/news_signal_evidence_report_YYYY-MM-DD.json
- data/news_signal_evidence_report_YYYY-MM-DD.md

## Interpreting common outcome statuses

Common statuses:

- evaluated
- missing_price_data
- missing_future_data
- quote_unavailable
- invalid_ticker

A status such as missing_price_data is not a workflow failure. It means price data was not available for that signal/date yet.

For same-day signals before market close, missing future/price data can be expected.

## When to use outcomes for tuning

Do not tune catalyst scoring from a tiny sample.

Minimum before review:

- 30–50 evaluated rows per catalyst/action-window bucket

Until then, treat outcome artifacts as evidence collection only.

Do not adjust these from small samples:

- score_delta
- hard-block categories
- action windows
- Telegram thresholds
- paper/live trading readiness

## Quick closeout checklist

Before committing any docs or workflow changes:

- python -m compileall -q scripts src tests
- python3 -m pytest tests/ -q --tb=short --disable-warnings
- python scripts/audit_journal_consistency.py --strict
- python scripts/check_enforcement_readiness.py
- python scripts/monitoring_readiness.py
- git diff --check
- git status -sb

Paper trading must remain blocked unless readiness gates pass and the founder explicitly approves.
