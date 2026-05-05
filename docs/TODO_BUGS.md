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
| Bug #6 | OPEN | Low | UX / company names | company-name writer falls back to ticker when upstream lookup fails. User sees `NVDA` instead of full company name. | Writer should store empty string when lookup fails, not ticker-as-company. |
| Bug #7 | FIXED | Low | Calendar / trade type | day trades appeared on non-trading days historically. Picker now downgrades would-be day picks to swing on weekends/holidays; evaluator still handles old rows robustly. | Monitor future manual/backfill runs. |
| Bug #8 | PARTIAL | Medium | Sector alpha | sector benchmark fields were historically underfilled. Recent `main.py` path now resolves sector ETF and close with SPY fallback. | Verify new post-fix rows have `sector_etf` and `sector_close`; consider shared helper/backfill. |
| Bug #9 | PARTIAL | Medium | SPY alpha | alpha backfill for pre-May-1 picks appears partially addressed, but older rows should be audited. | Run/extend backfill audit for `spy_close_at_exit`, `spy_return_pct`, `alpha_pct`. |
| Bug #10 | PARTIAL | Medium | Sector ETF fill rate | sector_etf fill should improve after Bug #8 changes, but needs post-fix verification. | Add sector benchmark fill-rate audit. |
| Bug #11 | OPEN | Medium | Earnings data | `days_to_earnings` fill rate was historically low. Earnings proximity is important for filtering and scoring. | Add error logging/retry/fallback; add earnings fill-rate audit. |
| Bug #12 | INFO | Informational | Trailing/adaptive fields | trail/adaptive fields are sparse because the feature shipped partway through the dataset. | No action unless new rows fail to populate. |
| Bug #13 | DEFERRED | Design debt | Tiered exits | Tiered TP system (`tp1`, `tp2`, `qty_t1-3`) is in schema but not actively used. | Decide later: implement tiered exits or mark columns reserved. |
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

1. Bug #11 — earnings fill-rate audit and fallback.
2. Bug #7 — verify no new day trades on non-trading days.
3. Bug #8/#10 — sector benchmark fill-rate audit and optional backfill.
4. Bug #6 — company-name fallback cleanup.
5. Bug #13 — decide tiered TP fate after monitoring window.
