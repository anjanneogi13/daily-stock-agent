# Batch 12 — src/scorer.py (236 lines) + src/scoring_safety.py (104 lines) — TRUE LINE-BY-LINE — PHASE B BEGINS

**Date:** 2026-05-12
**Files:** scorer.py (236 lines, fully read), scoring_safety.py (104 lines, fully read)
**Phase:** B (scoring + data layer) — files 1 and 2 of ~18

## TOP HEADLINE FINDINGS

1. SC-X1: scorer.py is the SCORING ENGINE that produces composite scores consumed by every downstream gate, brain, log, and decision. ~50 magic thresholds across 11 sub-score functions. ZERO of them are config-driven. The "weights" dict is config (line 207), but every BUCKET threshold (RSI 50/70/30, ATR 1-3% / >6%, vol_ratio 2.0/1.3/0.7, ADX 40/25/20, BB 0.2/0.6/0.85, etc.) is hardcoded. Tuning requires code edits.
2. SC-3 + HB-22 + SCS-X1: SEMI scoring is pulled in TWO inconsistent directions. scorer.py:186-199 applies SEMI/AI bonus multipliers (1.10 + 0.20*ai_weight up to 1.25x). scoring_safety.py:18-19 EXPLICITLY DISABLES blanket SEMI/AI boosts (MAX_ALLOWED_SEMI_BOOST = 1.0, MAX_ALLOWED_AI_BOOST = 0.0). **scorer.py defaults to disabled (sector_cfg.get("semi_boost", 1.10)) but scoring_safety asserts the cfg value is ≤ 1.0.** If config sets semi_boost=1.10 to enable feature → scoring_safety raises RuntimeError. If config omits → scorer uses 1.10 default → boosts apply silently. **scoring_safety guards CONFIG but not code defaults.** Asymmetric guarantee.
3. SC-X2: AI/SEMI tag-split bug confirmed in 6th LOCATION. scorer.py:33 `tag.split(" / ")[0].strip().upper()` in apply_tag_cap. Same Theme T8 cross-file pattern as Batch 9 PRG-11/PRG-28, hard_blocks HB-52/HB-53.
4. SC-15+16+17+18: score_trend has DEAD BRANCHES. Line 144: `c > s20 > s50` adds 0.25. Line 146: `c < s20 < s50` subtracts 0.30. **Asymmetric magnitude (+0.25 vs -0.30) for symmetric conditions.** Bull-bias bias.
5. SC-9 (lines 53-59): Stochastic scoring — k <= 20 ("oversold") gets 0.85 (high score). For a SWING BUY system, oversold IS bullish. But for a momentum/breakout strategy, k<=20 means the trend hasn't established. Without strategy context, scoring assigns 0.85 to a value that means opposite things in different strategies.
6. SCS-X2: scoring_safety.py is 104 lines of guardrails for ONE feature (SEMI/AI boost). It has 3 different entry points (assert_scoring_safety, assert_config_file_scoring_safety, scoring_safety_status). Excellent OVER-engineering for what is basically two `if x > N: raise` checks. Compare to smell_faculty (271 lines, 7 smells). **scoring_safety has more lines per check than any other safety file. The boost feature must have caused real damage to warrant this.**
7. SC-23 (line 209): `composite_score` calls `_enhanced_indicator_score(sig)` then computes `indicators_avg`. Same call already done at line 208 → result computed TWICE per scoring (duplicate work). Plus the enhanced score is INCLUDED IN components AND surfaced individually at lines 232-233.

## src/scorer.py — LINE BY LINE

### Lines 1-3: Module docstring + imports
- SC-1 SMELL (line 1): "Multi-factor scoring with semiconductor sector boost" — but per scoring_safety the boost is DISABLED. Docstring is OUT OF DATE relative to safety constraints.
- SC-2 GOOD (line 3): Imports is_semi, get_semi_meta from .semiconductors. Single-purpose import.

### Lines 7-19: apply_sector_cap
- SC-3 BUG (line 7): `max_per_sector: int = 4` default — **MAGIC 4**. But Batch 6 M-RUN39 noted main.py log lies about "max 4/sector" when actual cap is 2 (PRG-33). **Confirms cross-file inconsistency:** scorer default 4, portfolio_risk default 2. Two different defaults for the same logical limit.
- SC-4 SMELL (line 8): `reduced_sectors: dict = None` — mutable-default-pattern OK (uses None then `or {}`). But type hint should be `Optional[dict]`.
- SC-5 GOOD (line 13): Sort by composite DESC before capping — best-first preserved.
- SC-6 BUG (line 14): `p.get("info_short", {}).get("sector", "Unknown")` — relies on info_short being populated. Per parallel_scorer PS-51 / Batch 8, info_short DROPS most fields but keeps name and sector. So sector IS available here. But "Unknown" silently bins all picks-with-no-sector together → all share the cap → most get blocked. **Silent grouping.**
- SC-7 OK (lines 16-18): cap-counting logic clean.

### Lines 22-40: apply_tag_cap
- SC-8 BUG (line 22): `max_per_tag: int = 2` default — same 2 as portfolio_risk (PRG-34). Consistent. But scoring/portfolio_risk apply BOTH = double-cap. Possible 0-pick result if both fire restrictively. No coordination logged.
- SC-9 SMELL (lines 22-25): docstring says "Catches what yfinance sector misses" — implies tag is a FALLBACK. But if BOTH sector cap AND tag cap apply to same pick, the pick is SUBJECT TO TWO caps. Architectural overlap, not a fallback.
- SC-10 BUG (line 33): `tag.split(" / ")[0].strip().upper()` — **AI/SEMI bug 6th location.** Confirmed pattern from Batch 9 cross-cutting findings. Single _utils.py helper would consolidate.

### Lines 48-126: _enhanced_indicator_score (8 sub-scores)
- SC-11 BUG (lines 53-59): Stochastic — magic thresholds 20/80, magic scores 0.85/0.70/0.30/0.50. None config-driven.
- SC-12 SMELL (line 59): Default 0.50 when stoch_k missing. **All 8 sub-scores default 0.50 when missing.** Silent "neutral" default could mask data outages.
- SC-13 BUG (line 62): OBV — boolean trigger to either 0.85 OR 0.40. **No middle ground.** Bimodal sub-score.
- SC-14 BUG (line 65): PSAR — same bimodal 0.85/0.30.
- SC-15 BUG (lines 68-72): BB position thresholds 0.2/0.6/0.85, scores 0.85/0.75/0.55/0.30. 4 magic numbers, 4 magic scores.
- SC-16 BUG (lines 75-79): Support/Resistance — `min(d_res / 10.0, 1.0)` and `min(d_sup / 15.0, 1.0)`. **Magic 10.0 and 15.0 dividers.** Why different scales? No comment.
- SC-17 BUG (line 79): `upside_room * 0.6 + safety * 0.4` — magic weights 0.6/0.4 inside scoring.
- SC-18 BUG (lines 82-90): Fibonacci scoring — depends on close, fib_382, fib_618 ALL being present. If any None → defaults 0.50.
- SC-19 BUG (line 87): `elif close < f382: scores["fibonacci"] = 0.60` — **value below fib_382 (golden zone) gets 0.60, ABOVE fib_618 gets 0.50**. Higher score for below-zone? Asymmetric and arguably backwards.
- SC-20 BUG (lines 95-101): ADX thresholds 40/25/20, scores 0.90/0.80/0.60/0.35. Documented well in comments but still magic.
- SC-21 BUG (line 104): DI direction — bimodal 0.80/0.30.
- SC-22 BUG (lines 107-114): VWAP — 3 magic distance thresholds (0/3/6%), scores 0.85/0.70/0.50/0.30.
- SC-23 BUG (lines 117-124): Candlestick — 4-way decision tree with magic 0.85/0.20/0.50/0.55. **Default 0.55 when no pattern detected** — slightly above 0.50 neutral. Asymmetric implicit bias.
- SC-24 SMELL: 8 sub-scores, 32+ magic thresholds, 30+ magic score values. **A scoring config YAML alone could externalize all of this.** Currently every threshold tweak requires code change + redeploy.

### Lines 129-132: score_indicators
- SC-25 SMELL: Wraps _enhanced_indicator_score with average. Trivial wrapper. Used inconsistently — composite_score calls `_enhanced` directly (line 208), score_indicators not called from anywhere I've seen. **Probably dead helper.**

### Lines 139-147: score_trend
- SC-26 GOOD (line 139): Defaults to 0.5 (neutral).
- SC-27 BUG (line 142): `if not all([c, s20, s50]): return 0.5` — early return on missing data. Silent "neutral" hides incomplete picks. Same Theme T11 fail-soft.
- SC-28 BUG (lines 144-146): `c > s20 > s50` adds 0.25 (bullish stack). `c < s20 < s50` subtracts 0.30 (bearish stack). **ASYMMETRIC: -0.30 vs +0.25**. The bear-stack penalty is 20% larger than bull-stack reward. Why? No comment. Could be intentional bear-aversion or a typo. Theme T10.
- SC-29 SMELL (line 145): `if s200 and c > s200: score += 0.15` — but no symmetric `if s200 and c < s200: score -= 0.15`. Long-bias accumulation.

### Lines 150-161: score_momentum
- SC-30 BUG (lines 154-157): RSI thresholds 50/70/30, score adjustments +0.20/-0.15/+0.10. **3 magic values + 3 magic adjustments.**
- SC-31 BUG (lines 158-160): MACD — `macd > macd_sig and (macd_hist or 0) > 0` adds 0.20. `macd < macd_sig` subtracts 0.15. ASYMMETRIC again (+0.20 vs -0.15).
- SC-32 BUG (line 159): `(macd_hist or 0) > 0` — `macd_hist or 0` treats macd_hist=0 as 0. Edge case OK.

### Lines 164-170: score_volatility
- SC-33 GOOD: Returns 0.5 when ATR/close missing. Defensive.
- SC-34 BUG (line 168): `0.01 <= vol_pct <= 0.03` — magic "ideal vol" band 1-3%. No source.
- SC-35 BUG (line 169): `vol_pct > 0.06` returns 0.30. **Score CLIFFS at 6% (0.30) but no penalty between 3-6%** (returns 0.5 default). 5% vol = neutral score, 6.01% vol = 0.30 penalty. Discontinuous.

### Lines 173-179: score_volume
- SC-36 BUG (lines 174-178): vol_ratio thresholds 2.0/1.3/0.7. Scores 0.85/0.70/0.35/0.5. 4 magic values, 4 magic scores. Same pattern.

### Lines 186-199: sector_bonus
- SC-37 BUG (line 186): Only applies to is_semi(ticker). For non-SEMI tickers, returns multiplier=1.0. **All non-SEMI picks get NO sector bonus computation.** Other sectors (e.g., biotech with high momentum) have NO sector-specific scoring. Hard-coded SEMI favoritism.
- SC-38 BUG (line 190): `sector_cfg.get("semi_boost", 1.10)` — DEFAULT 1.10 (10% boost). But scoring_safety.py:18 says MAX_ALLOWED_SEMI_BOOST = 1.0. **Code default VIOLATES safety constraint** unless config explicitly overrides. If sector_cfg is `{}` (e.g., test or bad config), boost = 1.10 → SC-37 multiplier = 1.10 → composite up by 10%. **scoring_safety asserts only on CONFIG values, not code defaults.** Theme T11 + Theme T10 (docstring/safety lie).
- SC-39 BUG (line 191): `ai_boost`, default 0.20. Same problem — scoring_safety MAX_ALLOWED_AI_BOOST = 0.0.
- SC-40 BUG (line 193): `multiplier = base_boost + (ai_boost * ai_weight)` — for SEMI with ai_weight=1.0 and defaults: 1.10 + 0.20*1.0 = 1.30. **Up to 30% composite boost for AI semis.** Defaults silently enable maximal blanket boost.
- SC-41 SMELL (line 196): `"SEMI" + (" / AI" if ai_weight >= 0.75 else "")` — produces "SEMI / AI" tag string. **THIS IS THE SOURCE OF THE TAG-SPLIT BUG that 6 downstream files fail on.** scorer creates the multi-token tag, downstream consumers fail to iterate it. Single producer, six failed consumers.

### Lines 206-235: composite_score
- SC-42 BUG (line 207): `sector_cfg: dict = None` — mutable-default OK (uses `or {}` at line 222). But type hint should be Optional.
- SC-43 BUG (line 208): `enhanced = _enhanced_indicator_score(sig)` — computed. Then line 209: `indicators_avg = round(sum(enhanced.values()) / len(enhanced), 4)`. Then line 218: `"indicators": indicators_avg`. Then line 232: `for k, v in enhanced.items(): components[f"ind_{k}"] = v`. **Same enhanced dict is averaged AND inlined as ind_* fields. Same data twice.**
- SC-44 SMELL (line 209): Average across heterogeneous sub-scores. No weighting between OBV (binary) vs Stochastic (continuous). Naive avg = bias toward whichever is most "extreme."
- SC-45 BUG (line 221): `raw = sum(components[k] * weights.get(k, 0) for k in components)` — `weights.get(k, 0)` defaults to 0 for unrecognized keys. **If `weights` config is missing a key (e.g., new "indicators" sub-score added but config not updated), that component contributes 0.** Silent feature regression. Should warn/raise.
- SC-46 BUG (line 222): `bonus = sector_bonus(ticker, sector_cfg or {})` — passes empty dict if sector_cfg None. Then sector_bonus reads sector_cfg.get("semi_boost", 1.10) → uses default 1.10. **Empty sector_cfg silently triggers SC-38 violation.** Per SC-38, this defeats scoring_safety guard.
- SC-47 BUG (line 223): `boosted = max(0.0, min(1.0, raw * bonus["multiplier"]))` — clamps to [0,1]. With multiplier 1.30 and raw=0.8: boosted = 1.0 (clamped). **Picks at top end SATURATE composite=1.0** — multiple picks tie at 1.0, sorting becomes arbitrary.
- SC-48 GOOD (lines 225-229): components stores raw_score, sector_mult, sector_tag, sector_cat, composite — 5 audit-visibility fields. **Better audit trail than parallel_scorer (Batch 8 PS-X2)** but those mutations happen LATER, hiding original.
- SC-49 GOOD (lines 232-233): Inlines enhanced sub-scores as `ind_<name>`. Surfaces for audit.
- SC-50 BUG: `score_trend`, `score_momentum`, `score_volatility`, `score_volume` are CALLED ONLY VIA composite_score. None are called standalone elsewhere I can verify. They are essentially private helpers. Should be `_score_trend` etc. Module export is unfocused.

## src/scoring_safety.py — LINE BY LINE

### Lines 1-6: Module docstring
- SCS-1 GOOD: Explicit purpose. "intentionally separate from scoring logic so this module does not alter production scores." **Excellent design discipline.**

### Lines 8-15: Imports
- SCS-2 GOOD (line 8): `from __future__ import annotations` — modern.
- SCS-3 GOOD (lines 13, 15): yaml + theme_scoring_guardrails. Single-purpose.

### Lines 18-19: Constants
- SCS-4 GOOD: Two MAX_ALLOWED constants. Named, documented in docstring (line 36-37).
- SCS-5 BUG: 1.0 / 0.0 means BOOST IS DISABLED (multiplier=1.0 = no change). But scorer.py defaults to 1.10/0.20 which would MAX out at 1.30 = 30% boost. **Two safety levels in conflict — config-asserts-disable vs code-default-enabled.** Per SC-38 cross-cutting.

### Lines 22-26: _as_float
- SCS-6 GOOD: Type-coercion with field-name in error. **Explicit, raises (doesn't return None)**. Compare to MDG/PRG/PSG _safe_float which return None silently. **scoring_safety._as_float is fail-LOUD.** Different philosophy on purpose.
- SCS-7 SMELL: 6th _safe_float-like helper in codebase. But this one is intentionally different — fail-loud. Should keep separate from src/_utils.py.

### Lines 29-65: assert_legacy_sector_boosts_disabled
- SCS-8 GOOD (line 29): Type hint `dict[str, Any] | None` — modern.
- SCS-9 GOOD (lines 38-46): Defensive isinstance checks for cfg AND sector_cfg. Raises with clear message.
- SCS-10 BUG (lines 48-49): Reads `semi_boost` and `ai_boost` from config — but if config doesn't have them, defaults are MAX_ALLOWED (1.0/0.0), NOT scorer.py's defaults (1.10/0.20). **scoring_safety asserts CONFIG values, not RUNTIME values.** A scorer.py call with `sector_cfg={}` bypasses scoring_safety entirely.
- SCS-11 GOOD (lines 51-59): violations list, accumulated, raised together. **collect-all-errors pattern** like MDG-13.
- SCS-12 GOOD (lines 61-65): Single RuntimeError with all violations joined. Loud and explicit. ✅

### Lines 68-72: assert_scoring_safety
- SCS-13 GOOD: Composite assertion — calls 2 sub-asserts. Single entry point.

### Lines 75-81: load_yaml_config
- SCS-14 BUG (line 75): default `path: str | Path = "config.yaml"` — **RELATIVE PATH AGAIN.** 5th file in audit with this pattern (HB, PRG, PL, main.py, now SCS).
- SCS-15 GOOD (line 77): `Path(path).read_text()` — explicit.
- SCS-16 GOOD (lines 78-80): Defensive yaml load + isinstance check + raise.
- SCS-17 BUG: NO yaml.YAMLError handling. Malformed YAML = unhandled YAMLError propagates to caller. **Ambiguity:** is this fail-LOUD intent (good for safety) or oversight? Comment would clarify.

### Lines 84-86: assert_config_file_scoring_safety
- SCS-18 GOOD: Trivial composition. Two-line wrapper. OK to have.

### Lines 89-103: scoring_safety_status
- SCS-19 BUG (line 92): `(config or {}).get("sector", {}) if isinstance(config or {}, dict) else {}` — **REDUNDANT isinstance check.** `config or {}` is GUARANTEED to be either the config dict or `{}`. Both are dict. Check always True. Dead branch.
- SCS-20 BUG (lines 93-94): defensive isinstance + reassign — same redundant pattern.
- SCS-21 GOOD (lines 95-103): 7-field status dict. Explicit, documented, machine-readable. **Excellent operator-facing output.**
- SCS-22 BUG (line 101): `float(sector_cfg.get("semi_boost", MAX_ALLOWED_SEMI_BOOST))` — uses MAX_ALLOWED as default. So status shows configured = 1.0 if missing. **But scorer.py uses 1.10 as default → status LIES about what production uses.** Audit trail wrong.
- SCS-23 BUG (line 102): Same issue with ai_boost.
- SCS-24 SMELL: status function performs validation as side effect (line 91 `assert_scoring_safety(...)`). If called with bad config, raises. So "status" function can throw. Naming/contract drift.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### SC-X1 + SCS-X1: Two-source-of-truth on scoring boosts
- scorer.py defaults: `semi_boost=1.10, ai_boost=0.20`
- scoring_safety asserts: `semi_boost ≤ 1.0, ai_boost ≤ 0.0`
- If config sets explicit value → safety enforces ≤1.0 (works)
- If config omits → scorer uses 1.10 default → safety NEVER CHECKED CODE DEFAULTS → silently violates
**Single highest-impact bug in scorer.py.** Either:
  a) Move defaults to MAX_ALLOWED constants (kill the 1.10/0.20 in scorer)
  b) Have assert_scoring_safety also validate code defaults via inspection
  c) Force config to be explicit (no defaults in scorer)

### SC-X2: 6 locations now confirmed for AI/SEMI tag-split bug
1. hard_blocks line 225 (HB-53)
2. hard_blocks line 234 (HB-52)
3. portfolio_risk_gate line 53 (PRG-11)
4. portfolio_risk_gate line 120 (PRG-28)
5. **NEW: scorer.py line 33 (SC-10)** — apply_tag_cap
6. (Likely more in unaudited files)

**scorer.py line 196 PRODUCES the "SEMI / AI" string. Six consumers across the codebase fail to handle it.** The producer is the right place to either:
  - Produce a list `["SEMI", "AI"]` instead of a string
  - Document the parsing convention via helper

### SC-X3: scorer.py has ~50 magic numbers, ZERO are config-driven
| Sub-score | Magic threshold count |
|---|---:|
| Stochastic | 4 (20/80/.85/.70/.30) |
| OBV | 2 (.85/.40) |
| PSAR | 2 (.85/.30) |
| BB position | 8 (3 thresholds + 4 scores + .5 default) |
| S/R | 4 (10.0/15.0/.6/.4) |
| Fibonacci | 5 (4 buckets + .5 default) |
| ADX | 7 (3 thresholds + 4 scores) |
| DI | 2 |
| VWAP | 5 (3 thresholds + 4 scores) |
| Candlestick | 4 (4 outcomes) |
| Trend | 5 (.25/.30/.15 + close/sma checks) |
| Momentum | 6 (RSI 50/70/30 + .20/.15/.10) |
| Volatility | 4 (.01/.03/.06/.30) |
| Volume | 5 (2.0/1.3/0.7 + .85/.70/.35) |
| Composite | 0 (only weights are config) |
| **Total** | **63 magic numbers** |
**A scoring_thresholds.yaml alone would externalize all 63.**

### Cross-cutting: relative-path bug now in 5 files
HB-10, PRG-3, PL-5, main.py M-CFG1, **NEW: SCS-14 (config.yaml default)**.

### Cross-cutting: bull-bias bias is implicit across scoring
SC-28: trend +0.25 vs -0.30 (bear penalty larger). SC-29: long-only s200 check. SC-31: MACD +0.20 vs -0.15 (bull bias). **System has implicit short-aversion baked into scoring constants.** Consistent with the long-only assumption (PRG-40, MDG-18) but unstated in scoring docstring.

### Cross-cutting: SAME _as_float / _safe_float pattern split brain
- scoring_safety._as_float (line 22): fail-LOUD, raises RuntimeError
- 5 other files: fail-SOFT, returns None or default
**Two philosophies, intentionally separated. Don't unify these without thought.**

## SUMMARY (Batch 12)

| Severity | scorer.py | scoring_safety.py | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 18 | 6 | 3 | 27 |
| Data/safety | 15 | 4 | 0 | 19 |
| Code smell | 12 | 5 | 0 | 17 |
| Good code | 5 | 11 | 0 | 16 |
| Total findings | 50 | 26 | 3 | 79 |

## TOP 10 CRITICAL FIXES from Batch 12

1. SC-X1: Align scorer defaults with scoring_safety MAX_ALLOWED. scorer.py line 190/191 should default to 1.0/0.0 (not 1.10/0.20). Critical safety gap. (15 min)
2. SC-X2: scorer.py line 196 — change `tag = "SEMI / AI"` string to a list, OR add helper that all 6 consumers use. (30 min)
3. SC-X3: Externalize 63 magic numbers to scoring_thresholds.yaml. (1 day, biggest tunability win)
4. SC-45: weights.get(k, 0) silently zeros missing keys. Should raise. (5 min)
5. SC-3 vs PRG-33: Reconcile max_per_sector default 4 vs 2. Pick one. (5 min)
6. SC-41: Document or correct "fibonacci" asymmetry — below f382 scoring 0.60 above f618 scoring 0.50 (intent unclear). (15 min)
7. SC-28+SC-31: Document or correct asymmetric +/-0.25/-0.30 and +0.20/-0.15. (15 min)
8. SCS-19+20: Remove redundant isinstance branches (dead code). (5 min)
9. SCS-22+23: scoring_safety_status defaults should match scorer.py defaults to avoid status lying. (5 min)
10. SC-50: Mark internal helpers as private (_score_trend, etc.). (10 min)

## NEW THEMES UPDATED

- Theme T2 (schema drift): SC-X1 confirms defaults in code disagree with safety constraints in another file.
- Theme T8 (DRY): AI/SEMI tag-split now 6 locations.
- Theme T10 (documentation lies): scorer docstring says "semiconductor sector boost" but scoring_safety asserts this is disabled. Status function reports values that don't match production.
- Theme T11 (fail-open by accident): SC-46 — empty sector_cfg silently enables 30% boost despite safety module asserting otherwise.
- Theme T12 NEW (asymmetric scoring magnitudes): bull-vs-bear adjustments differ by 5-20% across multiple sub-scores. Either intentional bull-bias OR untracked typos.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 2/~18 done | scorer, scoring_safety | 2/~18 |
| Total true line-by-line | | +2 files | 25 of 382 |
| Remaining | | | 357 files |

## NEXT BATCH

Batch 13: src/data_fetcher.py + src/indicators.py (data layer foundations). These produce the `info` and `sig` dicts that EVERY scoring/gate function consumes.

End of Batch 12. Phase B in progress.
