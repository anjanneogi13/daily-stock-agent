# Root Cause — "Zero Take-Profits for a Week" (Aug 17–23, 2026)

§6 deliverable: split the week's "only losses" outcome into **accounting-caused**
(bugs that lost or fabricated outcomes) vs **strategy-caused** (real market
results), with a corrected scoreboard and testable strategy hypotheses.
No profitability claims are made — the deliverable is correct measurement.

## 1. Verdict up front

The week was **not** "zero take-profits". At least one TP demonstrably
occurred (`MRNA`, Aug 19, TP $66.72 touched at 09:35, entry $62.96, +5.97%)
and was never booked. The headline "0 wins · 52 losses" was dominated by
fabricated outcomes: of the 52 counted "losses", **45 were $0 stale flats
from a legacy block re-dumped every day** and never that day's trades. The
real week: a handful of genuine SL/bell-exit losses, one genuine watch-only
TP win, and several positions that should simply have stayed open.

## 2. Accounting-side failures (fixed in this overhaul)

| # | Failure | Mechanism (code-verified) | Effect on the week | Fix |
|---|---|---|---|---|
| 1 | Intraday closes never persisted | `.github/workflows/intraday_monitor.yml` committed alert state but **not `data/picks_log.csv`** — every close the monitor wrote was discarded at run end | `MRNA` TP booked in-memory then lost; positions re-printed all day; `OKTA` printed 5+ times | workflow now commits the ledger + quarantine logs |
| 2 | Carryover closes silently no-op'd | `_close_pick_in_csv` keyed `update_pick_row` on **today's date**, but carryover rows have `pick_date` < today → no row matched | `TTMI`/`SOFI`/`ZIM` carryovers could never close in the CSV | close keyed to the pick's own `pick_date`; write-once terminal guard in `src/picks_csv.py` |
| 3 | Stale block dumped daily as losses | evening report used a 3-day `evaluated_on` lookback while a mass-expiry stamped `evaluated_on=today` on ~68 legacy `pending` rows each run; `losses = len(trades) − wins` counted $0 flats as losses | the recurring `CDNS…BZH` "45 losses · $0" block; counts inflating 45→52 | strict `evaluated_on == today` scoping; WIN/LOSS/FLAT/NO_TRADE/UNVERIFIED taxonomy (`src/trade_state.py`); one-time `scripts/reconcile_ledger.py` settlement (68 orphans incl. `ANL`, closed once, deterministic dates) |
| 4 | Weekly report structurally dead | `send_layman_weekly.py` read a nonexistent `status` column → always "No closed trades"; also scoped by pick-date not close-date | "0 closed" contradiction | reads `evaluation_status`, scopes by `evaluated_on`, same buckets as daily |
| 5 | Corrupt quotes drove bookkeeping | no plausibility gate on monitoring quotes: `MRNA` printed $117–$174 (+86%…+176%) intraday against a $62.96 entry | trailing-SL math consumed absurd prints; win could have been mis-sized | `src/price_sanity.py` gates entry, monitoring, and closes; implausible prints quarantined to `data/quote_quarantine_*.jsonl`, state held |
| 6 | Journal/ledger divergence | hypothesis review counted `signal_journal.jsonl` win/loss rows (all-time, flats counted as losses); daily/weekly counted differently | "14 closed" vs "0" vs "52" for one week | ledger is authoritative; review prints a reconciliation block and flags mismatches; journal flats no longer classed as losses |

### Quantified: what the broken week reported vs what actually closed

Reported by the broken pipeline (accumulating dump):

| Day | Reported |
|---|---|
| Aug 17 | 0 wins · 45 losses · $0 |
| Aug 18 | 0 wins · 46 losses · −$100 |
| Aug 19 | 0 wins · 48 losses |
| Aug 20 | 0 wins · 51 losses |
| Aug 21 | 0 wins · 52 losses |
| Weekly | "No closed trades this week" |
| Hypothesis review | "14 closed picks, WR 14.3%" |

Corrected daily scoreboard (terminal events actually evidenced that day;
official headline separates watch-only reference outcomes, which carry no
position):

| Day | Official closes | Watch-only reference outcomes |
|---|---|---|
| Aug 17 | none | `OKTA` SL $143.42 (−2.7%) |
| Aug 18 | `SOFI` SL loss (≈−$100) | `TTMI` SL reference loss |
| Aug 19 | none | **`MRNA` TP WIN $66.72 (+5.97%)** — the missed win |
| Aug 20 | `WEAV`, `ZIM` day-trade bell exits (small losses) | none |
| Aug 21 | `WEAV` day-trade bell exit | none |
| Still open (correctly) | `SGHT`, `GDS`, `JKHY`, `ADI`/`AZ` pending fill-confirmation | `FTH` (+9% unrealized, TP never touched), `RKLB`, `ZIM` carryover, `NVDA`, `DOO`, `CLPBY` |

Every number that differs is accounting, not strategy: **45 of 52 "losses"
were fabricated $0 flats; the one real win was dropped; 3 views used 3
different stores.** After the fixes, all three views project from
`data/picks_log.csv` via `src/trade_state.py` and must reconcile
(`reconcile_counts`), and the remaining open Aug rows settle deterministically
on the next evaluator run with real bar data.

## 3. Strategy-side diagnostics (real, once accounting is corrected)

Genuine (non-fabricated) losing mechanisms observed in the week's execution
reports — these are **testable hypotheses for the learning loop
(docs/brain_activation_path.md), not conclusions**:

1. **SL width vs realized noise.** SLs ≈ −2% to −5% against avg MAE ≈ −0.7%
   to −3.7% and avg MFE often < +1%: stops sit *inside* normal intraday
   noise while TPs sit *beyond* typical favorable excursion. Hypothesis:
   volatility-scaled (ATR-style) SL/TP would cut noise stop-outs. Test:
   recompute the week's outcomes under ATR-scaled levels from the same bars.
2. **R/R feasibility.** ~1.7–2.0 R/R targets require MFE the week rarely
   delivered (`OKTA` TP +4.5% vs MFE <1%; `FTH` TP +9.5% vs peak +9%).
   Hypothesis: TP distance should be bounded by observed per-name MFE
   distribution for the hold horizon.
3. **Entry/fill dynamics on ~15-min delayed data.** Execution reports show
   limits "missed by +0.35%…+1.40%" and fills that immediately stop out —
   consistent with entering on stale prints. Hypothesis: delayed-data limit
   placement is adverse; verified-fresh entries (now enforced by the §F gate)
   should change the fill/stop-out mix. Measurable from fill-vs-first-print
   deltas now that entries are gated.
4. **Day-trade bell-exit drag.** Repeated small-negative forced bell exits
   (`WEAV`, `ZIM`) are a consistent loss engine when TP is unreachable
   intraday. Hypothesis: day-trade TPs must be reachable within one session's
   typical range or the pick should be a swing/no-trade.
5. **Signal predictiveness** can only be judged now that wins are recorded,
   flats are not losses, and the sample excludes fabricated outcomes — the
   corrected ledger feeds the hypothesis engine (Cluster H).

## 4. Why "LOW SAMPLE / no mutation" was the right output of a broken input

The brain was fed 52 mostly-fabricated losses in one view, 0 closes in
another, and 14 flats-as-losses in a third. Observe-mode correctly refused to
mutate on garbage. With the reconciled ledger, the review recomputes from real
closes and either proposes bounded, journaled weight deltas or reports an
explicit "insufficient evidence" — see `docs/brain_activation_path.md`.

*Educational project; monitoring-only; nothing here is financial advice or a
claim of future returns.*
