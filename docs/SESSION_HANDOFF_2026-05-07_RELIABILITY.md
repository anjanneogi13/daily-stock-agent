# Daily Stock Agent Reliability Handoff — 2026-05-07

## Session Status

Status: CLOSED  
Production readiness for tomorrow: READY  
Known blocking issues: NONE  
CI status: GREEN through CI #166  
Final reliability commit: `cae4b3c ci: persist market data health artifacts`

## Executive Summary

This session focused on preventing another missed trading window.

The root issue was not one single bug. The system had several reliability gaps:

1. GitHub scheduled workflows are best-effort and can miss/delay runs.
2. There was no external scheduler redundancy.
3. Official Daily Picks could produce zero rows and still look operationally confusing.
4. Late watch-only fallback was not independent enough.
5. Late watch-only ideas could be suppressed by yfinance quote failures.
6. There was limited evidence explaining whether failures came from:
   - no qualifying candidates
   - data-provider/rate-limit failure
   - workflow scheduling failure
   - post-send/push artifact failure

The session implemented layered reliability so tomorrow should not be silent.

Expected tomorrow outcomes are now:

- Official Daily Picks sent before market open, OR
- failure/no-pick alert with evidence, OR
- Late Watch-Only Daily Ideas sent after cutoff.

Silence should not happen.

---

## What Was Completed

## 1. External Scheduler Added

Configured cron-job.org jobs to trigger GitHub workflow_dispatch externally.

### Daily Picks External Jobs

Enabled:

```text
Daily Picks External 08:05 ET
Daily Picks External 08:35 ET
Daily Picks External 09:05 ET
Daily Picks External 09:15 ET
```

Endpoint:

```text
POST https://api.github.com/repos/anjanneogi13/daily-stock-agent/actions/workflows/daily-picks.yml/dispatches
```

Body:

```json
{"ref":"main"}
```

Headers:

```text
Authorization: Bearer <token>
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
User-Agent: daily-stock-agent-external-scheduler
```

Timezone:

```text
America/New_York
```

Test result:

```text
204 No Content
```

Verified GitHub workflow_dispatch runs appeared.

### Late Watch-Only External Jobs

Enabled:

```text
Late Watch-Only External 09:25 ET
Late Watch-Only External 09:40 ET
```

Endpoint:

```text
POST https://api.github.com/repos/anjanneogi13/daily-stock-agent/actions/workflows/late_watch_only.yml/dispatches
```

Body:

```json
{"ref":"main"}
```

Test result:

```text
204 No Content
```

Verified GitHub workflow_dispatch run appeared and succeeded.

### Old Failed External Jobs Deleted

Deleted from cron-job.org:

```text
Daily Picks - Primary (8:30 AM ET)
Daily Picks - Backup (8:45 AM ET)
Daily Picks - Safety Net (9:15 AM ET)
```

Only the six correct external jobs remain enabled.

---

## 2. Independent Late Watch-Only Workflow Added

Added:

```text
.github/workflows/late_watch_only.yml
```

Purpose:

```text
If official Daily Picks do not produce rows before/near market open,
send monitoring-only late daily ideas after the official cutoff.
```

Schedule:

```text
09:25 ET
09:40 ET
```

GitHub cron:

```text
25,40 13-14 * * 1-5
```

The workflow has an ET guard, so duplicate/wrong DST UTC slots skip safely.

Safety rules:

```text
Does not create official picks.
Does not write data/picks_log.csv.
Does not create paper trades.
Does not enable live trading.
Does not bypass the 09:20 ET official-picks cutoff.
```

---

## 3. Late Watch-Only No Longer Requires Quote Success

Removed:

```text
--require-quote
```

from late idea generation.

Reason:

```text
If yfinance quote lookup fails or rate-limits,
watch-only ideas should still send with safety text/levels unavailable.
```

This avoids suppressing late watch-only ideas due to a quote-provider failure.

---

## 4. Watchdog Rescue Added/Verified

Workflow:

```text
.github/workflows/watchdog.yml
```

Purpose:

```text
Before 09:20 ET, check whether official picks are already logged.
If missing, automatically dispatch Daily Stock Picks and send Telegram alert.
```

Schedule:

```text
09:10 ET
09:18 ET
```

GitHub cron:

```text
10,18 13-14 * * 1-5
```

Safety:

```text
Does not create picks itself.
Does not bypass Daily Picks timing gate.
Does not enable paper/live trading.
```

Verified watchdog schedule executed successfully after today’s changes.

---

## 5. Zero-Pick Failure Evidence Added

Official Daily Picks now fails loudly if `main.py` runs but no final official picks are produced.

Relevant behavior:

```text
if not top:
    write daily no-pick report
    raise RuntimeError
```

Artifacts:

```text
data/daily_picks_no_pick_report_YYYY-MM-DD.json
data/daily_picks_no_pick_report_YYYY-MM-DD.md
data/daily_picks_run_status_YYYY-MM-DD.jsonl
```

This prevents a zero-pick official run from being treated as normal success.

---

## 6. Market-Data Health Telemetry Added

Added:

```text
src/market_data_health.py
```

Purpose:

```text
Record provider health during Daily Picks so failures are explainable.
```

Tracks:

```text
provider attempts
successes
empty results
errors
rate_limited
unauthorized
not_found
timeout
provider_error
sample failures
```

Persists:

```text
data/market_data_health_YYYY-MM-DD.json
```

Integrated into:

```text
src/data_fetcher.py
src/monster_data.py
main.py
```

No-pick reports now include market-data health when available.

---

## 7. Market-Data Health Artifact Persistence Fixed

Final reliability fix:

```text
cae4b3c ci: persist market data health artifacts
```

The Daily Picks workflow now stages/commits:

```text
data/market_data_health_*.json
```

This ensures provider-health evidence is not lost after the GitHub runner cleans up.

---

## 8. yfinance Pressure Reduced

Changed Daily Picks scoring worker count from hardcoded high concurrency to configurable lower default:

```text
DAILY_SCORER_WORKERS=4
```

Purpose:

```text
Reduce yfinance/rate-limit pressure during scoring.
```

Can be overridden with env var:

```text
DAILY_SCORER_WORKERS
```

---

## Important Commits

Key commits from this reliability work:

```text
7636632 feat: let watchdog rescue missing daily picks schedule
e561fad feat: report zero-pick daily runs as learning evidence
2b8af78 feat: add independent late watch-only fallback
2b3c900 feat: record market data health for daily picks
cae4b3c ci: persist market data health artifacts
```

Latest known head at session close:

```text
cae4b3c ci: persist market data health artifacts
```

CI:

```text
CI #164 green
CI #165 green
CI #166 green
```

---

## Current Reliability Architecture

The system now has these layers:

```text
1. GitHub Daily Picks schedule
2. External Daily Picks scheduler
3. Watchdog rescue before 09:20 ET
4. Daily Picks zero-pick loud failure
5. Daily Picks failure Telegram alert
6. Independent GitHub Late Watch-Only workflow
7. External Late Watch-Only scheduler
8. Late Watch-Only no-quote-required behavior
9. Market-data health telemetry
10. Persisted provider-health artifacts
```

Expected behavior tomorrow:

### Best Case

```text
Official Daily Picks sent before market open.
```

### If GitHub Schedule Misses

```text
External scheduler triggers Daily Picks.
```

### If Daily Picks Are Missing Near Cutoff

```text
Watchdog dispatches Daily Picks before 09:20 ET and alerts.
```

### If Official Picks Are Still Missing After Cutoff

```text
Late Watch-Only Daily Ideas send after 09:20 ET.
```

### If Data Provider Fails

```text
Official run fails loudly.
Telegram failure alert sends.
daily_picks_no_pick_report is written.
market_data_health artifact is written.
Late Watch-Only fallback can still send monitoring-only ideas.
```

---

# What Is NOT Yet Implemented

## 1. True Backup Market-Data Provider

Important: We did NOT add a second market-data provider today.

Current state:

```text
Official Daily Picks still primarily rely on yfinance for OHLCV/price data.
```

What was added today:

```text
observability
lower concurrency
failure evidence
fallback messaging behavior
```

What remains:

```text
real provider fallback chain
```

---

## 2. Provider Fallback Chain

Target architecture:

```text
yfinance → backup provider → cache/watch-only fallback
```

Candidate providers:

```text
1. Stooq
   - no API key
   - useful for historical daily OHLCV fallback
   - ticker format may need conversion, e.g. AAPL.US

2. Alpha Vantage
   - API key required
   - free tier is rate-limited

3. Finnhub
   - existing project already has some Finnhub fundamentals support
   - can potentially be expanded for candles/quotes

4. Polygon
   - stronger data, likely paid

5. Alpaca
   - useful if trading integration is planned later
```

Recommended first step:

```text
Implement Stooq as no-key daily OHLCV fallback.
```

---

## 3. Provider Abstraction Layer

Suggested new package:

```text
src/market_data_providers/
  __init__.py
  base.py
  yfinance_provider.py
  stooq_provider.py
  cache.py
```

Suggested provider interface:

```python
class MarketDataProvider:
    name: str

    def fetch_ohlcv(self, ticker: str, period: str, interval: str) -> MarketDataResult:
        ...
```

Suggested result object:

```python
@dataclass
class MarketDataResult:
    ticker: str
    provider: str
    df: pandas.DataFrame
    success: bool
    stale: bool
    error_type: str | None
    message: str | None
```

Provider chain behavior:

```text
1. Try yfinance.
2. If yfinance returns valid OHLCV, use it.
3. If yfinance empty/errors/rate-limits, record health event.
4. Try Stooq.
5. If Stooq valid, normalize schema and use it.
6. If all fail, return empty and record all provider failures.
```

---

## 4. Cache/Backoff

Still needed:

```text
- last-good OHLCV cache
- provider cooldown after rate-limit
- retry/backoff
- cache freshness metadata
```

Suggested policy:

```text
Official picks:
  require fresh enough daily OHLCV.

Watch-only:
  may use stale/cached data if clearly labeled.

Never:
  fabricate official entries from stale/unknown data.
```

---

## 5. Better No-Pick Watch-Only Candidate Summary

Future enhancement:

If official Daily Picks fails because no candidates pass filters, generate:

```text
No official picks today. Watch-only candidates:
- ticker
- reason not official
- market condition
- provider health
```

This should be clearly monitoring-only and must not write to:

```text
data/picks_log.csv
```

---

## Recommended Next Session Plan

## Phase 1 — Audit Current Provider Usage

Find all yfinance usages:

```text
src/data_fetcher.py
src/monster_data.py
main.py sector benchmark functions
scripts/generate_late_daily_ideas.py
any intraday/news/opening-range scripts
```

Categorize usages:

```text
official daily OHLCV
quote/current price
fundamentals/info
monster float/short data
sector ETF close
late watch-only levels
intraday/opening range
```

## Phase 2 — Implement Provider Abstraction for Official Daily OHLCV

Start only with official daily OHLCV path:

```text
fetch_universe_data()
fetch_ohlcv()
```

Do not refactor every yfinance usage in one patch.

## Phase 3 — Add Stooq Daily OHLCV Fallback

Implement:

```text
src/market_data_providers/stooq_provider.py
```

Normalize to the existing lowercase OHLCV schema:

```text
open
high
low
close
volume
```

Test with mocked HTTP/local sample data.

## Phase 4 — Wire Provider Health Into Fallback

Ensure market-data health records provider-specific events:

```text
provider=yfinance
provider=stooq
stage=ohlcv
result=success/empty/error
error_type=rate_limited/not_found/timeout/provider_error
```

## Phase 5 — Tests

Required tests:

```text
1. yfinance success does not call fallback
2. yfinance rate-limit calls Stooq
3. Stooq success returns normalized dataframe
4. all providers fail returns empty dataframe
5. provider-health records both yfinance failure and Stooq success
6. official picks do not fabricate rows when all providers fail
```

## Phase 6 — CI + Audit

Run:

```bash
python3 -m pytest tests/ -q --tb=short --disable-warnings
python -m compileall -q scripts src tests main.py
git diff --check
```

Then audit workflows and artifact persistence again.

---

## Next Chat Prompt

Use this prompt at the start of the next AI session:

```text
We are continuing work on anjanneogi13/daily-stock-agent.

Read docs/SESSION_HANDOFF_2026-05-07_RELIABILITY.md first.

Current status:
- Reliability hardening for missed Daily Picks is complete.
- External scheduler is configured.
- Watchdog rescue exists.
- Independent late_watch_only fallback exists.
- Market-data health telemetry exists and is persisted.
- CI was green through CI #166.
- Latest reliability commit was cae4b3c.

Important:
We have NOT implemented a real backup market-data provider yet.
Official Daily Picks still primarily depend on yfinance.

Next goal:
Implement a provider fallback chain for official daily OHLCV:
yfinance → Stooq fallback → safe empty/failure with provider-health evidence.

Process:
1. Audit yfinance usages.
2. Implement provider abstraction only for official daily OHLCV first.
3. Add Stooq fallback.
4. Add tests.
5. Verify with pytest, compileall, diff check.
6. Audit again.
7. Document changes.
```

---

## Closing Notes

Today’s work solved the immediate production reliability issue:

```text
Do not miss tomorrow’s window due to scheduler failure or silent zero-pick behavior.
```

Weekend/next-session work should solve the architectural issue:

```text
Do not depend on yfinance as the only official market-data provider.
```