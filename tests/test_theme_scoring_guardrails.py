from pathlib import Path

import pytest

from src.theme_scoring_guardrails import (
    FUTURE_THEME_SCORING_FIELDS,
    REQUIRED_PREREQUISITES,
    assert_theme_scoring_disabled,
    explain_theme_scoring_guardrail,
    theme_scoring_status,
)


def test_theme_scoring_status_is_disabled_by_default():
    status = theme_scoring_status()

    assert status["theme_aware_official_scoring_enabled"] is False
    assert status["production_scoring_effect"] is False
    assert status["official_score_boost_enabled"] is False
    assert status["paper_trading_enabled"] is False
    assert status["live_trading_enabled"] is False
    assert status["buy_instructions_enabled"] is False
    assert tuple(status["required_prerequisites"]) == REQUIRED_PREREQUISITES
    assert tuple(status["future_fields"]) == FUTURE_THEME_SCORING_FIELDS


@pytest.mark.parametrize(
    "config",
    [
        {"theme_scoring": {"enabled": True}},
        {"theme_scoring": {"production_scoring_effect": True}},
        {"theme_scoring": {"official_score_boost_enabled": True}},
        {"theme_scoring": {"theme_aware_official_scoring_enabled": True}},
    ],
)
def test_theme_scoring_guardrail_rejects_enabled_config(config):
    with pytest.raises(RuntimeError, match="Theme-aware official scoring is disabled"):
        assert_theme_scoring_disabled(config)


def test_theme_scoring_guardrail_accepts_missing_or_disabled_config():
    assert_theme_scoring_disabled({})
    assert_theme_scoring_disabled({"theme_scoring": {"enabled": False}})
    assert_theme_scoring_disabled({"theme_scoring": {"production_scoring_effect": False}})


def test_theme_scoring_explanation_names_required_validation():
    text = explain_theme_scoring_guardrail()

    assert "inactive" in text
    assert "observe-only" in text
    assert "historical validation" in text
    assert "founder approval" in text
    assert "readiness-gate" in text


def test_production_scorers_do_not_import_theme_artifacts():
    production_files = [
        Path("src/scorer.py"),
        Path("src/parallel_scorer.py"),
        Path("src/probability_engine.py"),
        Path("src/news_signals.py"),
    ]
    forbidden = [
        "theme_discovery_",
        "theme_pick_bridge_",
        "build_theme_discovery",
        "build_theme_pick_bridge",
        "theme_strength_score",
        "theme_breadth_score",
        "theme_quality_score",
        "theme_overextension_penalty",
        "theme_confirmation_count",
    ]

    for path in production_files:
        text = path.read_text()
        for token in forbidden:
            assert token not in text, f"{path} unexpectedly references {token}"


def test_config_does_not_enable_theme_scoring():
    text = Path("config.yaml").read_text()
    assert "theme_scoring:" not in text
    assert "theme_aware_official_scoring_enabled: true" not in text
    assert "official_score_boost_enabled: true" not in text
