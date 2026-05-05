# TODO / Bugs — Current Status Ledger

**Last updated:** 2026-05-05  
**Purpose:** single operational ledger for known bugs, partial fixes, deferred design debt, and recently fixed launch-readiness issues.

This file is intentionally status-based. Do not leave stale free-form bug notes here after a fix lands.

---

## Status legend

| Status | Meaning |
|---|---|
| OPEN | Real remaining issue; needs fix or investigation |
| PARTIAL | Some code landed, but verification/backfill/follow-up remains |
| FIXED | Fix landed and is protected by tests or audit |
| DEFERRED | Valid design debt, intentionally postponed |
| INFO | Historical/informational; no action unless it regresses |

---

## Current bug ledger

| Bug | Status | Severity | Area | Summary | Next action |
|---|---|---|---|---|---|
| Bug #6 | FIXED | Low | UX / company names | company-name writer no longer falls back to ticker when upstream lookup fails; future unresolved names persist blank; tracked historical ticker-as-company rows were backfilled to known names. | Continue monitoring new rows. |
| Bug #7 | FIXED | Low | Calendar / trade type | day trades appeared on non-trading days historically. Picker now downgrades would-be day picks to swing on weekends/holidays; evaluator still handles old rows robustly. | Monitor future manual/backfill runs. |
| Bug #8 | FIXED | Medium | Sector alpha | sector benchmark fields were historically underfilled. `main.py` now resolves sector ETF and close with SPY fallback; `backfill_sector_alpha.py` repairs post-floor rows; sector audit is green. | Continue monitoring new rows. |
| Bug #9 | FIXED | Medium | SPY alpha | closed rows now have complete `spy_close_at_exit`, `spy_return_pct`, and `alpha_pct`; tracked data is protected by `tests/test_picks_log_spy_alpha_fill_rate.py`. | Continue monitoring new closed rows. |
| Bug #10 | FIXED | Medium | Sector ETF fill rate | sector_etf/sector_close fill is now protected by `audit_sector_fill_rate.py` and regression tests. | Continue monitoring new rows. |
| Bug #11 | FIXED | Medium | Earnings data | `days_to_earnings` now supports historical `as_of` backfills; `backfill_earnings_days.py` repaired post-floor rows; earnings fill-rate audit is green. | Continue monitoring provider reliability. |
| Bug #12 | INFO | Informational | Trailing/adaptive fields | trail/adaptive fields are sparse because the feature shipped partway through the dataset. | No action unless new rows fail to populate. |
| Bug #13 | FIXED | Design debt | Tiered exits | Tiered TP columns (`tp1`, `tp2`, `qty_t1-3`, `tier_status`) are intentionally reserved schema and inactive in current monitoring mode. | Revisit only if/when scale-out execution is implemented. |
| Bug #19 | FIXED | High | GitHub workflow reports | report issue upsert prevents duplicate Daily Picks / Performance / Execution Report issues. | Monitor next reruns; old duplicates can be closed separately if desired. |
| Bug #20 | FIXED | High | Product docs | monitoring-first/no-paper-trading decision encoded in docs and tests. | Keep docs in sync if launch policy changes. |
| Bug #21 | FIXED | High | Monitoring gates | monitoring readiness dashboard calculates day/swing/monster paper-trading gates. | Use during observation windows. |
| Bug #22 | FIXED | Medium | Audit accuracy | `full_repo_audit.py` now reports python lines accurately and includes monitoring readiness. | Continue protecting via audit tests. |

---

## Monitoring-first policy reminder

The agent is approved for monitoring-only operation.

Paper trading remains forbidden until post-floor data clears:

| Trade type | Gate |
|---|---|
| day trades | >60% win rate plus positive expectancy |
| swing trades | >66% win rate plus positive expectancy |
| monster / long holder picks | >90% win rate plus positive expectancy |

Decision record: `docs/decisions/2026-05-05-monitoring-first-no-paper-trading.md`

---

## Recently closed in launch-readiness cleanup

- Bug #19 — workflow report issue upsert.
- Bug #20 — monitoring-first product decision docs.
- Bug #21 — monitoring readiness dashboard.
- Bug #22 — full_repo_audit accuracy.

---

## Next likely fixes

1. Add tests for undercovered modules: `llm_agent`, `market_news`.
2. Continue monitoring until post-floor sample-size gates are ready.
