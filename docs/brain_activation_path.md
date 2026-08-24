# Brain Activation Path — Observe-Mode → Bounded Auto-Adjustment

Cluster H deliverable: the documented, guardrailed path by which the
self-improvement loop may move from *observe-mode* ("No weights auto-changed.
You decide what to act on.") to *bounded auto-adjustment*. This is
**evidence-gated improvement of selection quality — not forced mutation, and
not any promise of profitability.**

## Why the brain was right to do nothing in Aug 2026

The Aug 17–23 review said "LOW SAMPLE / no brain mutations" while daily
reports accumulated 52 "losses", the weekly said 0 closed, and the journal
said 14 closed. The learner's inputs were corrupted (missed TP closes, 45
fabricated $0 "losses", flats counted as losses). **No mutation on garbage
data is correct behavior.** The fix order is therefore: inputs first
(§7 single source of truth + Clusters B/C/D/F), activation second.

## Stage 0 — Corrected inputs (prerequisite, now enforced)

- All closed-trade counts project from `data/picks_log.csv` via
  `src/trade_state.py` (states, WIN/LOSS/FLAT/NO_TRADE/UNVERIFIED taxonomy).
- `scripts/run_hypothesis_review.py` prints a **ledger reconciliation block**
  and flags any journal-vs-ledger sample mismatch; the ledger is authoritative.
- Flats are never counted as losses (`FLAT_EPSILON_PCT` in trade_state;
  same epsilon in `src/signal_journal.attach_outcome`).
- Corrupt prints are quarantined before they can settle a trade
  (`src/price_sanity.py`), so no outcome is learned from a bad quote.

## Stage 1 — Observe-mode (current default)

- `src/hypothesis_engine.py` buckets closed picks (regime, days-to-earnings,
  composite score, tag, trade type) and reports edges/drags. Insights only.
- `src/weight_proposer.py` may write **proposals** to
  `data/weight_proposals.jsonl` — never applied automatically.
- Root-cause hypotheses from `docs/root_cause_zero_tp.md` (SL width vs noise,
  R/R feasibility vs observed MFE, delayed-data fill dynamics, bell-exit drag)
  are candidate hypotheses for the engine, not just per-bucket win rates.

## Stage 2 — Activation gates (all must hold before any auto-apply)

| Gate | Threshold | Where enforced |
|---|---|---|
| Corrected sample size | ≥ 30 realized (win/loss) closes per bucket (`min_n`) | `weight_proposer.propose` |
| Ledger reconciliation | journal sample == ledger realized wins+losses (no ⚠️ in the review block) | `run_hypothesis_review.py` |
| Statistical bar | bias_R > +0.10 (boost) / < −0.10 (penalize) / kill only if bias_R < −0.30 **and** WR < 35% | `weight_proposer` decision rule |
| Confidence scaling | √(n/100), caps at 1.0 — small samples get small deltas | `weight_proposer` |
| Bounded deltas | ±5% per factor per ISO week, cumulative cap enforced against applied history | `src/weight_applier.apply_proposals(cap_pct=5.0)` |
| Human-visible record | every proposal journaled (proposed vs applied) in `data/weight_proposals.jsonl` + applier history | both modules |

## Stage 3 — Bounded auto-adjustment

When every Stage-2 gate holds, `weight_applier.apply_proposals()` may run in
the weekly workflow (currently invoked manually / dry-run). It:

1. applies only unapplied proposals within the weekly cap,
2. writes the new multipliers to `config/weights.json`,
3. journals each mutation (timestamp, factor, old→new, proposal id),
4. reports applied vs skipped in the Self-Improvement Report — so Telegram
   output shows *proposed vs applied* explicitly.

## Stage 4 — Rollback on regression

- Every mutation is journaled with its prior value; reverting = applying the
  inverse delta (the applier's history makes this deterministic).
- Regression trigger: if the 4-week rolling realized win-rate or mean R of
  the affected bucket degrades below its pre-mutation baseline, revert the
  mutation and re-enter observe-mode for that factor for 2 weeks.
- All rollbacks are journaled and reported like mutations.

## Explicit non-goals

- No profitability guarantee, no implied expected returns.
- "Insufficient evidence — no change" is a *valid, reportable* weekly outcome.
- Monitoring-only stays monitoring-only; weight changes affect **selection
  and sizing of monitored picks**, never live orders.
