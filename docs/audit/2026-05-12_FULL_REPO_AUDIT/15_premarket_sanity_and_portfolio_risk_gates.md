# Batch 9 — src/premarket_sanity_gate.py (301 lines) + src/portfolio_risk_gate.py (279 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** premarket_sanity_gate.py (301 lines, fully read), portfolio_risk_gate.py (279 lines, fully read)
**Phase:** A (safety/gates) — files 4 and 5 of 8

## TOP HEADLINE FINDINGS

1. PSG-X1 RECONSIDERS BATCH 6 M-RUN62: The "300 lines copy-paste across 3 gates" claim was OVERSTATED. The gates share PATTERNS (helper shape, return triple, fail-closed branches) but NOT verbatim code. The real DRY opportunity is ~50 lines (helpers like _safe_float, sector/tag extraction), not 300.
2. PRG-X1: portfolio_risk_gate.py is THE CLEANEST GATE FILE I have audited. 7 fail-CLOSED branches, explicit long-only assertion at line 170, rich audit-trail dict, no bare-except in business logic. Use as template for refactoring other gates.
3. PSG-22: market_snapshot makes 7 sequential yfinance calls (4 for prices + 3 for pct_change). With period=5d each at ~1-2s, that's 7-14s overhead PER RUN before any candidate processing. Then run_premarket_sanity_gate adds 1 more call per candidate = 30+ additional calls. Total: 37+ sequential yfinance calls per gate run.
4. PSG-15 + PRG-7: AI/SEMI tag-split bug confirmed in TWO MORE files. premarket_sanity doesn't tag-check at all, but portfolio_risk_gate line 53 and line 120 both do split(" / ")[0] — only first tag taken. Pattern now confirmed in 4 files.
5. PRG-15: load_open_positions_from_picks_log fails OPEN on read failure (line 104-105 bare except returns []). Same disease as HB-17. picks_log corruption = portfolio risk caps DON'T enforce. Theme T11.
6. PSG-26: _safe_float helper TRIPLICATED across smell_faculty (no), premarket_sanity, portfolio_risk_gate. Should be in src/_utils.py. Theme T8 cross-file copy-paste.

## src/premarket_sanity_gate.py — LINE BY LINE

### Lines 1-13: Module docstring
- PSG-1 GOOD: Explicit safety stance "fail closed to watch-only/skip when fresh price cannot be verified". Sets the contract.
- PSG-2 GOOD (lines 8-12): "no fake picks, no paper trading enablement, no live trading enablement". Strong philosophy.

### Lines 15-25: Imports + action constants
- PSG-3 GOOD (line 15): from __future__ import annotations — modern style, allows | type union.
- PSG-4 GOOD (lines 20-25): Four action constants ACTION_SAFE/HALF_SIZE/SKIP_TODAY/WATCH_ONLY. Named constants instead of magic strings.
- PSG-5 GOOD (line 25): ACTIONABLE_ACTIONS = {ACTION_SAFE, ACTION_HALF_SIZE} — set lookup. Good pattern.

### Lines 28-34: _safe_float helper
- PSG-6 GOOD: Defensive coercion with default.
- PSG-7 SMELL: This is the THIRD copy of this helper across files. Should be in src/_utils.py. Cross-file Theme T8 DRY violation.

### Lines 37-41: _extract_entry_stop
- PSG-8 SMELL (line 38): plan = pick.get("plan") if isinstance(pick.get("plan"), dict) else {} — calls .get("plan") TWICE. Tiny perf, harder to read.
- PSG-9 BUG (lines 39-40): plan.get("entry") or pick.get("entry") — Theme T2 dual-source. Same as smell_faculty SF-15 and hard_blocks HB-32. At least HERE it checks BOTH but the existence of BOTH paths is the symptom: there's no canonical pick-shape contract.
- PSG-10 SMELL: entry or pick.get(...) falsy-or pattern. If plan.get("entry") = 0, falls through. Could mask broken pick state.

### Lines 44-77: evaluate_premarket_sanity setup
- PSG-11 GOOD (line 49): Keyword-only args after * — protects against arg-order bugs.
- PSG-12 SMELL (line 54): pick.get("ticker", "?") — silent default to "?". Won't crash but propagates "?" through logs.
- PSG-13 BUG (line 57): global_action = market.get("global_action", "normal") — defaults to "normal". If typo, silently defaults to normal. Should validate against {"normal", "skip_all", "half"}.
- PSG-14 GOOD (lines 59-69): base dict with default WATCH_ONLY action. Default fail-CLOSED stance.

### Lines 71-93: Three fail-CLOSED early returns
- PSG-15 GOOD: Three explicit checks (entry, stop_loss, current_price) each setting WATCH_ONLY+actionable=False with reason. Strongest fail-closed pattern in the codebase so far.
- PSG-16 SMELL: Three nearly-identical 5-line blocks. Could be loop. Tradeoff: explicit > clever. Acceptable as-is.

### Lines 95-156: Action ladder
- PSG-17 OK (line 95): gap_pct math correct.
- PSG-18 SMELL (line 96): if entry > 0 guard — but line 71 already returned if entry <= 0. Defensive duplication (dead branch).
- PSG-19 BUG (line 99): global_action == "skip_all" — magic string literal. Define as constant.
- PSG-20 GOOD (lines 107-113): If current_price <= stop_loss, skip with explicit dollar-formatted reason. Excellent operator-friendly logging.
- PSG-21 BUG (line 115): gap_pct <= -sl_buffer_pct * 0.6 — MAGIC 0.6 MULTIPLIER UNDOCUMENTED.
- PSG-22 BUG (line 123): gap_pct >= 3.0 — magic 3.0% gap threshold.
- PSG-23 BUG (line 132): global_action == "half" — magic string again.
- PSG-24 BUG (line 141): gap_pct <= -1.5 — magic -1.5%.
- PSG-25 SMELL (lines 123, 141): Asymmetric gap thresholds (+3 vs -1.5). Probably intentional but undocumented.
- PSG-26 GOOD (lines 124-130): HALF_SIZE on positive gap >= 3% with size_multiplier=0.5 — consistent.
- PSG-27 BUG (lines 132-139): "market caution requires half size" reason at line 137 is masked when gap also >= 3%. Audit trail loses one of two reasons.
- PSG-28 OK (lines 150-155): SAFE branch is fall-through default. size_multiplier=1.0.

### Lines 159-166: _apply_half_size
- PSG-29 SMELL (line 161): _safe_float(plan.get("quantity"), 0.0) or 0.0 — or 0.0 is REDUNDANT.
- PSG-30 BUG (line 163): max(1, int(qty * 0.5)) — minimum quantity 1. Edge case: qty=1 → max(1, 0)=1 → no actual reduction. Should probably SKIP rather than HALF_SIZE if qty=1.
- PSG-31 SMELL (lines 164-165): Mutates plan dict with premarket_size_multiplier and premarket_sanity_reason. Two storage locations for same data.

### Lines 169-205: apply_premarket_sanity_decisions
- PSG-32 GOOD (line 174): Returns (official, blocked) tuple. Type-annotated.
- PSG-33 SMELL (line 180): Empty string fallback.
- PSG-34 BUG (lines 186-189): Writes 4 redundant fields to candidate. Schema bloat. Theme T2: data exists in 2 places.
- PSG-35 SMELL (line 192): Side-effect coupling — _apply_half_size mutates plan; not obvious from this site.
- PSG-36 GOOD (lines 197-203): Blocked entry dict has 5 fields — rich audit trail.

### Lines 208-222: fetch_latest_price
- PSG-37 SMELL (line 211): Comment about "legacy premarket_check safety behavior" suggests cross-module duplication.
- PSG-38 GOOD (line 215): Inline import of yfinance — defensive.
- PSG-39 SMELL (line 217): period="5d" hardcoded. Same as hard_blocks._safe_pct_change.
- PSG-40 GOOD (line 219): Returns last available close.
- PSG-41 BUG (lines 220-221): bare except: return None. Theme T1. But here, "None" means "no price" which downstream uses to BLOCK → fail-CLOSED at the GATE LEVEL even though function-level is silent. Net effect OK, design fragile.
- PSG-42 BUG (line 222): Trailing return None after bare-except path. Dead code.

### Lines 225-279: fetch_market_snapshot
- PSG-43 BUG (lines 227-230): FOUR sequential fetch_latest_price calls for SPY, QQQ, SOXX, ^VIX.
- PSG-44 BUG (lines 232-243): Nested _pct_change function REIMPLEMENTS hard_blocks._safe_pct_change almost verbatim. Cross-file DRY violation. Plus nested-function anti-pattern.
- PSG-45 BUG (lines 245-247): THREE more sequential yfinance calls. Combined: 7 sequential yfinance calls per fetch_market_snapshot().
- PSG-46 BUG: SPY and QQQ are fetched TWICE (lines 227-228 for price + 245-246 for pct_change). Same data, no caching.
- PSG-47 BUG (line 252): if spy_chg <= -1.5 — magic threshold.
- PSG-48 BUG (line 255): elif spy_chg <= -0.7 — another magic.
- PSG-49 BUG (lines 252-257): SPY ladder sets global_action; thresholds magic.
- PSG-50 BUG (line 259): VIX >= 25 overrides ANY previous global_action with "skip_all" (overwrite).
- PSG-51 BUG (line 262): VIX 20-25 only sets "half" if SPY didn't escalate. Inconsistent precedence with line 259. Unclear policy.
- PSG-52 BUG (lines 266-267): SOXX < -2% appends warning but does NOT change global_action. Inconsistent. Sector weakness flagged but not enforced.
- PSG-53 SMELL (line 277): warnings list populated but caller may discard them. Dead output channel.

### Lines 282-300: run_premarket_sanity_gate
- PSG-54 GOOD (line 284): market_snapshot fetched ONCE per gate run.
- PSG-55 BUG (lines 285-289): N more sequential yfinance calls for N candidates. For 30 candidates, 30 yfinance calls. Combined with 7 from market_snapshot = 37+ sequential yfinance calls per gate execution.
- PSG-56 BUG (line 288): Silently drops candidates with no ticker. No log, no audit. Silent-drop epidemic.
- PSG-57 SMELL (lines 295-300): summary dict has current_prices — could be huge. Memory bloat.

## src/portfolio_risk_gate.py — LINE BY LINE

### Lines 1-13: Module docstring
- PRG-1 GOOD: Same explicit safety stance as PSG.

### Lines 15-26: Imports + constants
- PRG-2 GOOD (line 17): import csv at module top — better than inline imports elsewhere.
- PRG-3 BUG (line 22): PICKS_LOG_PATH = Path("data/picks_log.csv") — RELATIVE PATH. Same M-CFG1 / HB-10 bug.
- PRG-4 GOOD (lines 24-26): Three named DEFAULT_* constants.

### Lines 29-35: _safe_float
- PRG-5 SMELL: Verbatim copy of premarket_sanity_gate._safe_float. Cross-file DRY violation.

### Lines 38-42: _safe_int
- PRG-6 SMELL (line 40): int(float(value or 0)) — coerces None to 0 implicitly. Defensive but loses precision silently.
- PRG-7 BUG: If value = "abc", silently treats garbage as 0. Should at least log when default returned.

### Lines 45-48: _candidate_sector
- PRG-8 GOOD: Defensive isinstance check. Defaults to "Unknown".
- PRG-9 SMELL (line 47): TWO "Unknown" defaults stacked. Belt-and-suspenders.

### Lines 50-53: _candidate_tag
- PRG-10 BUG (line 52): candidate.get("tag") or scores.get("sector_tag") — TWO sources for tag. Same dual-source as hard_blocks line 223.
- PRG-11 BUG (line 53): raw.split(" / ")[0].strip().upper() — AI/SEMI bug AGAIN. Only first tag of "AI / SEMI" used. SEMI cap not enforced for AI/SEMI picks.

### Lines 56-58: _candidate_score
- PRG-12 OK: defensive composite extraction with 0.0 default. Malformed candidates sort to bottom — acceptable degradation.

### Lines 61-63: _trade_plan
- PRG-13 GOOD: Defensive isinstance.

### Lines 66-88: _risk_profile
- PRG-14 BUG (lines 68-72): 5 fields each with dual-source (entry, stop_loss, take_profit, quantity, risk_reward). Theme T2 multiplied by 5.
- PRG-15 BUG (line 71): _safe_int defaults to 0. Then line 76 quantity > 0 check filters. Fail-CLOSED chain works.
- PRG-16 GOOD (line 76): All-three-required check before computing risk_dollars.
- PRG-17 GOOD (line 77): max(0.0, ...) defends against negative risk. Defensive duplication with line 170 broken-pick check.
- PRG-18 GOOD (line 78): account_size > 0 guard against div-by-zero.
- PRG-19 GOOD (lines 80-88): Returns 7-field profile dict. Rounding for serialization.

### Lines 91-106: load_open_positions_from_picks_log
- PRG-20 GOOD (line 91): default param uses module constant.
- PRG-21 BUG (line 93): Silently empty if file missing. Same fail-open as HB-11. Missing picks_log = NO existing positions = portfolio caps applied to ZERO existing = caps allow N more picks. First-time run after log rotation: caps don't enforce.
- PRG-22 GOOD (lines 98-103): csv DictReader with status filter on 'pending' AND watch_only false.
- PRG-23 BUG (line 100): status == "pending" — what other valid statuses exist? "open"? "active"? Not documented.
- PRG-24 GOOD (line 101): watch_only handles 3 truthy strings.
- PRG-25 BUG (lines 104-105): except Exception: return []. Theme T1+T11. picks_log corruption silently returns empty → portfolio caps don't enforce.

### Lines 109-114: _existing_sector_counts
- PRG-26 BUG (line 112): row.get("sector") or row.get("info_sector") — DUAL COLUMN NAMES IN PICKS_LOG.CSV ITSELF. Schema drift confirmed in the persistence layer. Suggests historical column rename without migration.
- PRG-27 GOOD: Defensive defaults.

### Lines 117-123: _existing_tag_counts
- PRG-28 BUG (line 120): AI/SEMI bug for the FIFTH location. Existing positions tagged "AI / SEMI" only count toward "AI" cap. SEMI exposure under-counted.

### Lines 126-140: build_portfolio_risk_config
- PRG-29 GOOD: Defensive cfg unpacking.
- PRG-30 BUG (line 130): account_size default 10000.0. Same magic 10000 default in 3 locations now.
- PRG-31 SMELL (line 131): risk_per_trade_pct default 1.0% — magic but defensible.
- PRG-32 SMELL (line 136): max_positions default 5, floor 1.
- PRG-33 BUG (line 137): max_per_sector default 2 — CONFIRMS Batch 6 M-RUN10. Weak-sector tightening logic in main.py is no-op because base cap already 2.
- PRG-34 SMELL (line 138): max_per_tag default 2 — but split-bug means SEMI cap functionally disabled.
- PRG-35 SMELL (line 139): min_risk_reward default 1.0 — quite low. Industry typical is 1.5-2.0.

### Lines 143-192: evaluate_candidate_portfolio_risk — THE GOLD STANDARD
- PRG-36 GOOD (line 149): Returns (allowed, reason, detail) — three fields. Rich.
- PRG-37 GOOD (lines 156-162): detail dict captures everything for audit.
- PRG-38 GOOD (lines 164-165): missing entry → fail-CLOSED with explicit reason.
- PRG-39 GOOD (lines 167-168): missing SL → fail-CLOSED.
- PRG-40 GOOD (lines 170-171): EXPLICIT LONG-ONLY ASSERTION — "stop loss is not below entry" → reject. Compare to HB-40 where this assumption was IMPLICIT.
- PRG-41 GOOD (lines 173-174): TP must be above entry. Long-only consistent.
- PRG-42 GOOD (lines 176-177): quantity > 0.
- PRG-43 GOOD (lines 179-180): risk_reward >= min.
- PRG-44 BUG (line 182): max_risk_pct = risk_config["risk_per_trade_pct"] * 1.05 — MAGIC 1.05 MULTIPLIER UNDOCUMENTED. 5% slack above declared limit. Why? No comment.
- PRG-45 GOOD (lines 183-184): per-trade risk vs limit with 5% slack.
- PRG-46 GOOD (lines 186-187): sector cap enforcement.
- PRG-47 GOOD (lines 189-190): tag cap enforcement (modulo PRG-28 split-bug).
- PRG-48 GOOD: 8 sequential checks — clear ladder, all fail-closed, all return early. Cleanest gate function in the codebase.

### Lines 195-278: apply_portfolio_risk_gate
- PRG-49 GOOD (line 200): Returns (allowed, blocked, summary) — same triple shape as premarket_sanity. Pattern consistency.
- PRG-50 GOOD (lines 209-210): open_position_count + available_slots derivation explicit.
- PRG-51 GOOD (lines 212-213): sector and tag counts pre-computed once.
- PRG-52 GOOD (line 218): Sort by composite score DESC — best-first allocation of slots.
- PRG-53 GOOD (lines 221-234): max_positions check FIRST — cheapest possible block.
- PRG-54 SMELL (line 234): continue iterates ALL remaining candidates. For 100 candidates with 5 slots, 95 entries logged. Could short-circuit.
- PRG-55 GOOD (lines 236-241): kwargs-only call to evaluate_candidate_portfolio_risk.
- PRG-56 GOOD (lines 243-252): blocked entry has 6 fields including block_type distinguishing "max_positions" from "risk_limit".
- PRG-57 GOOD (lines 254-258): MUTATES sector_counts/tag_counts during iteration — correct for progressive cap enforcement.
- PRG-58 GOOD (lines 260-264): Writes candidate["portfolio_risk"] sub-dict — namespaced key, no collision with premarket_sanity. Compare to PSG-34 which flattened 3 redundant copies.
- PRG-59 GOOD (lines 267-276): Comprehensive summary dict — 7 fields.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### PSG-X1 + PRG-X1: M-RUN62 from Batch 6 was OVERSTATED
The "300 lines copy-paste across 3 gates" claim is wrong. Real situation:
- Both gates share PATTERNS (helper shape, return triple, fail-closed branches)
- Both gates have unique business logic
- Real DRY opportunity: ~50 lines (helpers like _safe_float, sector/tag extraction)
- Refactoring effort: 1 hour, not 1 week
This corrects a Batch 6 overestimate.

### Cross-cutting: _safe_float helper now in 2 files (likely 3+ when missing_data_gate audited)
Recommend src/_utils.py with _safe_float, _safe_int, _candidate_tag.

### Cross-cutting: AI/SEMI tag-split bug now in 5 LOCATIONS
1. hard_blocks line 225 (HB-53)
2. hard_blocks line 234 (HB-52)
3. portfolio_risk_gate line 53 (PRG-11)
4. portfolio_risk_gate line 120 (PRG-28)
5. (Likely) wherever else split(" / ")[0] appears
Single fix needed at the helper level.

### Cross-cutting: 7+ files now reference picks_log.csv with bare-except fail-open
1. hard_blocks._get_recent_pick_dates (HB-11/HB-17)
2. portfolio_risk_gate.load_open_positions_from_picks_log (PRG-21/PRG-25)
3. (Likely) main.py loads it for dedup
4. (Likely) tests load it for assertion
5. (Likely) pick_logger writes it
picks_log.csv is the lynchpin. Single missing file or corrupt row breaks 5 safety subsystems silently.

### Cross-cutting: account_size = 10000 default in 3 locations
- parallel_scorer line 94
- parallel_scorer line 95
- portfolio_risk_gate line 130
Should be ONE constant in config.yaml or src/_constants.py.

### Cross-cutting: yfinance call counts
- hard_blocks: 17 sequential calls per get_weak_sectors
- premarket_sanity: 7 sequential per fetch_market_snapshot + N per run_gate
- For 30 candidates: hard_blocks(17) + premarket_sanity(37) = 54 sequential yfinance calls per pipeline run
- At ~1-2s each = 54-108 seconds of yfinance latency per run, sequential
yfinance is the dominant runtime cost. ThreadPoolExecutor or simple lru_cache(maxsize=128) would cut this to ~5-10s.

### Cross-cutting: schema drift confirmed AT THE PERSISTENCE LAYER
PRG-26 reveals picks_log.csv has BOTH sector AND info_sector columns at different historical points. Theme T2 isn't just in-memory — it's persistent.

### Cross-cutting: portfolio_risk_gate IS THE GOLD STANDARD
8 fail-CLOSED checks, named constants, rich audit-trail dicts, explicit long-only assertion, namespaced output, comprehensive summary. Use as template for refactoring smell_faculty, hard_blocks, premarket_sanity_gate.

## SUMMARY (Batch 9)

| Severity | premarket_sanity | portfolio_risk | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 14 | 6 | 5 | 25 |
| Data/safety | 9 | 7 | 0 | 16 |
| Code smell | 14 | 6 | 0 | 20 |
| Good code | 20 | 28 | 1 | 49 |
| Total findings | 57 | 47 | 6 | 110 |

## TOP 10 CRITICAL FIXES from Batch 9

1. PSG-43+45+46+55: Replace 54 sequential yfinance calls with parallel batch + lru_cache (1 hour, biggest perf win in audit so far)
2. PRG-25+21: Replace bare-except in load_open_positions with LOUD-error pattern (15 min)
3. PRG-11+28 + cross-file AI/SEMI bug: Add _utils._tags_in() generator, replace 5 split-call sites (30 min)
4. PSG-29: Extract _safe_float to src/_utils.py, replace 3+ duplicates (10 min)
5. PRG-26: Pick canonical column name (sector OR info_sector), migrate picks_log, single-source the read (1 hr)
6. PSG-21+22+24+47+48: Define MARKET_GAP_CHASE_THRESHOLD, MARKET_GAP_DROP_THRESHOLD, SPY_HALF_THRESHOLD, SPY_SKIP_THRESHOLD, VIX_HALF, VIX_SKIP — all magic numbers as named constants (15 min)
7. PSG-30: Skip-rather-than-half-size when qty=1 (5 min)
8. PRG-44: Document or remove the 1.05 max_risk slack (5 min)
9. PSG-13: Validate global_action against {"normal","skip_all","half"} (5 min)
10. PSG-19+23: Define MARKET_ACTION_* constants (5 min)

## NEW THEMES UPDATED

- Theme T2 (schema drift): confirmed at the PERSISTENCE LAYER (PRG-26 sector vs info_sector in picks_log.csv).
- Theme T8 (DRY violation): cross-file _safe_float duplication (3+ files), AI/SEMI bug repeated in 5 sites.
- Theme T11 (fail-open by accident): 2 more confirmed sites (PRG-21 missing log, PRG-25 corrupt log).
- Audit revision M-RUN62: previous "300 lines copy-paste" estimate corrected to ~50 lines.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 5/8 done | premarket_sanity_gate, portfolio_risk_gate | 5/8 |
| Total true line-by-line | | +2 files | 20 of 382 |
| Remaining | | | 362 files |

## NEXT BATCH

Batch 10: src/missing_data_gate.py + src/premarket_readiness_gate.py — the LAST 2 gate files in Phase A.

End of Batch 9.
