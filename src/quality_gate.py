"""
Evidence-based pick quality gate (2026-10-29 full-repo audit).

Why this exists
---------------
Until this gate, the ONLY thresholds between "scored" and "official pick"
were ``output.min_score`` (0.55) and the top-N trim. A factor analysis of the
110 closed official picks in ``data/picks_log.csv`` (May → Oct 2026) showed
the losses were concentrated in two buckets that are knowable at pick time:

    final composite score <= 0.70 : n=71, total -19.6R  (mean ≈ -0.28R)
    relative volume (rvol) < 0.8  : n=17, mean -0.49R
    ---------------------------------------------------------------
    combined gate  pass (score >= 0.70 AND rvol >= 0.8): n=37, mean -0.02R
                   fail                                : n=73, mean -0.25R

So the gate drops the historically-losing buckets BEFORE the final top-N
trim. Fewer picks on thin days is the intended outcome; the pipeline already
has a valid no-pick path.

Configuration (config.yaml → ``quality_gate``)::

    quality_gate:
      enabled: true
      mode: enforce          # enforce = drop; observe = annotate only
      min_final_score: 0.70  # scores["composite"] after EQ blend + news
      min_rvol: 0.8          # scores["vol_ratio"] (unknown rvol is NOT penalised)

``QUALITY_GATE_MODE`` env var (enforce|observe|off) overrides the config mode
so a workflow can flip behaviour without a code change, matching the other
gates (``BRAIN_ENFORCE_EV``, ``SMELL_ENFORCE``, ``AUTO_PAUSE_ENABLED``).

The gate never mutates scores other than attaching ``scores["quality_gate"]``
(an audit dict) so downstream consumers can see why a pick passed/failed.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

STAGE = "quality_gate"
DEFAULTS = {
    "enabled": True,
    "mode": "enforce",
    "min_final_score": 0.70,
    "min_rvol": 0.8,
}
VALID_MODES = ("enforce", "observe", "off")


def _to_float(value) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out:  # NaN
        return None
    return out


def resolve_config(cfg: Optional[dict], env: Optional[dict] = None) -> Dict:
    """Merge config.yaml block + env override into an effective gate config."""
    env = os.environ if env is None else env
    block = {}
    if isinstance(cfg, dict):
        block = cfg.get("quality_gate") if "quality_gate" in cfg else cfg
        if not isinstance(block, dict):
            block = {}
    eff = dict(DEFAULTS)
    for key in ("min_final_score", "min_rvol"):
        val = _to_float(block.get(key))
        if val is not None:
            eff[key] = val
    if "enabled" in block:
        eff["enabled"] = bool(block.get("enabled"))
    mode = str(block.get("mode", eff["mode"]) or eff["mode"]).strip().lower()
    env_mode = str(env.get("QUALITY_GATE_MODE", "") or "").strip().lower()
    if env_mode in VALID_MODES:
        mode = env_mode
    if mode not in VALID_MODES:
        mode = DEFAULTS["mode"]
    if not eff["enabled"]:
        mode = "off"
    eff["mode"] = mode
    return eff


def evaluate_pick(pick: dict, eff: Dict) -> Tuple[bool, List[str]]:
    """Return (passes, reasons). Unknown rvol is not a failure reason."""
    scores = pick.get("scores") or {}
    reasons: List[str] = []
    score = _to_float(scores.get("composite"))
    if score is None:
        reasons.append("final score missing")
    elif score < eff["min_final_score"]:
        reasons.append(f"final score {score:.3f} < {eff['min_final_score']:.2f}")
    rvol = _to_float(scores.get("vol_ratio"))
    if rvol is None:
        sig = pick.get("signals") or {}
        rvol = _to_float(sig.get("vol_ratio"))
    if rvol is not None and rvol < eff["min_rvol"]:
        reasons.append(f"rvol {rvol:.2f} < {eff['min_rvol']:.2f}")
    return (not reasons), reasons


def apply_quality_gate(picks: List[dict], cfg: Optional[dict] = None,
                       env: Optional[dict] = None) -> Tuple[List[dict], List[dict], Dict]:
    """
    Split ``picks`` into (passed, rejected, effective_config).

    ``rejected`` items are shaped like the other rejection records main.py
    collects (``ticker``/``rejection_stage``/``reason``) so they flow into the
    no-pick diagnostics unchanged; main.py attaches ``candidate`` itself.
    In observe/off mode nothing is dropped; every pick is still annotated.
    """
    eff = resolve_config(cfg, env)
    passed: List[dict] = []
    rejected: List[dict] = []
    for p in picks:
        ok, reasons = evaluate_pick(p, eff)
        scores = p.setdefault("scores", {}) if isinstance(p, dict) else {}
        if isinstance(scores, dict):
            scores["quality_gate"] = {
                "pass": ok,
                "mode": eff["mode"],
                "reasons": list(reasons),
            }
        if ok or eff["mode"] != "enforce":
            passed.append(p)
            continue
        rejected.append({
            "ticker": p.get("ticker", "?"),
            "rejection_stage": STAGE,
            "reason": "; ".join(reasons),
        })
    return passed, rejected, eff
