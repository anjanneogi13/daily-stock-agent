"""Learned-weights consumer — closes the Pillar 4 learning loop.

The nightly brain (calibration → weight_proposer → weight_applier) writes
per-factor-bucket multipliers to config/weights.json and mirrors them to
data/weights_runtime.json. Until this module existed NOTHING read those
files, so months of learning never changed a single pick.

At scoring time we compute the candidate's calibration buckets (same
bucketing functions the brain learns on) and multiply the matching learned
multipliers together. The total is clamped to [0.85, 1.15] so learning can
tilt scores but never dominate them, and any failure returns a neutral 1.0
(fail-safe: a broken brain must never block picking).

Factors applied at pick time: rsi, score, atrpct. Outcome-only factors
(exit_status) and post-score factors (trade_type) are skipped — they are
unknowable when the composite is computed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

from src.calibration import _rsi_bucket, _score_bucket, _atr_bucket

RUNTIME_WEIGHTS = Path("data/weights_runtime.json")
CONFIG_WEIGHTS = Path("config/weights.json")

# Total learned influence is bounded — same envelope as the pattern layer.
MULT_FLOOR = 0.85
MULT_CEIL = 1.15

_cache: Dict[str, object] = {"key": None, "factors": None}


def _load_factors() -> Dict[str, Dict[str, float]]:
    """Load factor→bucket→multiplier map, preferring the runtime snapshot.

    data/weights_runtime.json is committed by nightly_brain.yml so a fresh
    CI checkout always sees the latest applied weights; config/weights.json
    is the applier's working copy and acts as fallback.
    """
    for path in (RUNTIME_WEIGHTS, CONFIG_WEIGHTS):
        try:
            if not path.exists():
                continue
            key = (str(path), path.stat().st_mtime_ns)
            if _cache["key"] == key and _cache["factors"] is not None:
                return _cache["factors"]  # type: ignore[return-value]
            data = json.loads(path.read_text())
            factors = data.get("factors") or {}
            if isinstance(factors, dict):
                _cache["key"] = key
                _cache["factors"] = factors
                return factors
        except Exception:
            continue
    return {}


def learned_multiplier(sig: Dict, composite: float) -> Tuple[float, Dict[str, float]]:
    """Return (bounded multiplier, {factor=bucket: applied multiplier}).

    sig is the latest_signals() dict (rsi_14, atr_14, close). composite is
    the score before this multiplier. Neutral (1.0, {}) on any problem.
    """
    try:
        factors = _load_factors()
        if not factors:
            return 1.0, {}

        buckets = {
            "rsi": _rsi_bucket(_f(sig.get("rsi_14"))),
            "score": _score_bucket(_f(composite)),
            "atrpct": _atr_bucket(_f(sig.get("atr_14")), _f(sig.get("close"))),
        }

        total = 1.0
        applied: Dict[str, float] = {}
        for factor, bucket in buckets.items():
            if bucket.endswith("_na"):
                continue
            mult = factors.get(factor, {}).get(bucket)
            if mult is None:
                continue
            m = float(mult)
            # A killed bucket (0.0) must dampen, not zero-out — the floor
            # clamp below keeps the worst case at MULT_FLOOR.
            total *= max(0.0, m)
            applied[f"{factor}={bucket}"] = m

        total = max(MULT_FLOOR, min(MULT_CEIL, round(total, 4)))
        return total, applied
    except Exception:
        return 1.0, {}


def _f(v) -> Optional[float]:
    try:
        return float(v) if v is not None and v != "" else None
    except (TypeError, ValueError):
        return None
