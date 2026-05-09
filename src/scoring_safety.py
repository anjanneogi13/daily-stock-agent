"""Scoring safety guardrails.

These checks prevent accidental reactivation of legacy blanket boosts or future
theme-aware scoring before validation/approval. They are intentionally separate
from scoring logic so this module does not alter production scores.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .theme_scoring_guardrails import assert_theme_scoring_disabled


MAX_ALLOWED_SEMI_BOOST = 1.0
MAX_ALLOWED_AI_BOOST = 0.0


def _as_float(value: Any, *, field_name: str) -> float:
    try:
        return float(value)
    except Exception as exc:
        raise RuntimeError(f"{field_name} must be numeric; got {value!r}") from exc


def assert_legacy_sector_boosts_disabled(config: dict[str, Any] | None = None) -> None:
    """Raise if config attempts to enable legacy blanket semi/AI boosts.

    Historical backtesting found blanket SEMI/AI boosting unsafe. The current
    permitted neutral values are:

    - sector.semi_boost <= 1.0
    - sector.ai_boost <= 0.0
    """
    cfg = config or {}
    if not isinstance(cfg, dict):
        raise RuntimeError("scoring config must be a dictionary")

    sector_cfg = cfg.get("sector", {})
    if sector_cfg is None:
        sector_cfg = {}
    if not isinstance(sector_cfg, dict):
        raise RuntimeError("sector config must be a dictionary when present")

    semi_boost = _as_float(sector_cfg.get("semi_boost", MAX_ALLOWED_SEMI_BOOST), field_name="sector.semi_boost")
    ai_boost = _as_float(sector_cfg.get("ai_boost", MAX_ALLOWED_AI_BOOST), field_name="sector.ai_boost")

    violations: list[str] = []
    if semi_boost > MAX_ALLOWED_SEMI_BOOST:
        violations.append(
            f"sector.semi_boost={semi_boost} exceeds neutral maximum {MAX_ALLOWED_SEMI_BOOST}"
        )
    if ai_boost > MAX_ALLOWED_AI_BOOST:
        violations.append(
            f"sector.ai_boost={ai_boost} exceeds neutral maximum {MAX_ALLOWED_AI_BOOST}"
        )

    if violations:
        raise RuntimeError(
            "Legacy blanket sector boosts are disabled pending explicit approval; "
            + "; ".join(violations)
        )


def assert_scoring_safety(config: dict[str, Any] | None = None) -> None:
    """Run all scoring safety guardrails."""
    cfg = config or {}
    assert_legacy_sector_boosts_disabled(cfg)
    assert_theme_scoring_disabled(cfg)


def load_yaml_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    """Load a YAML config file as a dictionary."""
    raw = Path(path).read_text()
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} must contain a YAML dictionary")
    return data


def assert_config_file_scoring_safety(path: str | Path = "config.yaml") -> None:
    """Load a config file and enforce scoring safety guardrails."""
    assert_scoring_safety(load_yaml_config(path))


def scoring_safety_status(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a compact status dict after validating scoring safety."""
    assert_scoring_safety(config or {})
    sector_cfg = (config or {}).get("sector", {}) if isinstance(config or {}, dict) else {}
    if not isinstance(sector_cfg, dict):
        sector_cfg = {}
    return {
        "legacy_sector_boosts_disabled": True,
        "theme_aware_official_scoring_enabled": False,
        "production_scoring_effect": False,
        "max_allowed_semi_boost": MAX_ALLOWED_SEMI_BOOST,
        "max_allowed_ai_boost": MAX_ALLOWED_AI_BOOST,
        "configured_semi_boost": float(sector_cfg.get("semi_boost", MAX_ALLOWED_SEMI_BOOST)),
        "configured_ai_boost": float(sector_cfg.get("ai_boost", MAX_ALLOWED_AI_BOOST)),
    }
