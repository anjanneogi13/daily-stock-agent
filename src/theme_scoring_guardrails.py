"""Guardrails for future theme-aware scoring.

Priority 8 intentionally does NOT enable theme-aware production scoring.
This module documents and tests the disabled/default state so future work must
make an explicit, reviewed change before theme intelligence can affect official
scores.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


FUTURE_THEME_SCORING_FIELDS = (
    "theme_strength_score",
    "theme_breadth_score",
    "theme_quality_score",
    "theme_overextension_penalty",
    "theme_confirmation_count",
)

REQUIRED_PREREQUISITES = (
    "historical_validation",
    "forward_observation",
    "train_test_discipline",
    "overfitting_review",
    "clear_tests",
    "founder_approval",
    "readiness_gate_preserved",
)

THEME_SCORING_SAFETY_FLAGS = {
    "theme_aware_official_scoring_enabled": False,
    "production_scoring_effect": False,
    "official_score_boost_enabled": False,
    "paper_trading_enabled": False,
    "live_trading_enabled": False,
    "buy_instructions_enabled": False,
}


@dataclass(frozen=True)
class ThemeScoringStatus:
    """Current production status for theme-aware official scoring."""

    theme_aware_official_scoring_enabled: bool = False
    production_scoring_effect: bool = False
    official_score_boost_enabled: bool = False
    paper_trading_enabled: bool = False
    live_trading_enabled: bool = False
    buy_instructions_enabled: bool = False
    required_prerequisites: tuple[str, ...] = REQUIRED_PREREQUISITES
    future_fields: tuple[str, ...] = FUTURE_THEME_SCORING_FIELDS


def theme_scoring_status() -> dict[str, Any]:
    """Return the current disabled theme-scoring status."""
    return asdict(ThemeScoringStatus())


def assert_theme_scoring_disabled(config: dict[str, Any] | None = None) -> None:
    """Raise if a config attempts to enable theme-aware production scoring.

    This is a guardrail helper for tests and future orchestration. It does not
    wire theme artifacts into production scoring.
    """
    cfg = config or {}
    theme_cfg = cfg.get("theme_scoring", {}) if isinstance(cfg, dict) else {}
    if not isinstance(theme_cfg, dict):
        raise RuntimeError("theme_scoring config must be a dictionary when present")

    enabled_keys = {
        "enabled",
        "production_scoring_effect",
        "official_score_boost_enabled",
        "theme_aware_official_scoring_enabled",
    }
    enabled = [key for key in enabled_keys if bool(theme_cfg.get(key))]
    if enabled:
        raise RuntimeError(
            "Theme-aware official scoring is disabled pending validation and approval; "
            f"attempted enabled key(s): {', '.join(sorted(enabled))}"
        )


def explain_theme_scoring_guardrail() -> str:
    """Human-readable explanation for docs/reports."""
    return (
        "Theme-aware official scoring is inactive. Theme discovery and bridge "
        "artifacts are observe-only until historical validation, forward "
        "observation, train/test discipline, overfitting review, clear tests, "
        "founder approval, and readiness-gate preservation are complete."
    )
