from pathlib import Path

import pytest
import yaml

from src.scoring_safety import (
    assert_config_file_scoring_safety,
    assert_legacy_sector_boosts_disabled,
    assert_scoring_safety,
    scoring_safety_status,
)


def test_current_config_yaml_passes_scoring_safety():
    assert_config_file_scoring_safety("config.yaml")


@pytest.mark.parametrize(
    "config",
    [
        {"sector": {"semi_boost": 1.01, "ai_boost": 0.0}},
        {"sector": {"semi_boost": 1.10, "ai_boost": 0.0}},
        {"sector": {"semi_boost": 1.0, "ai_boost": 0.01}},
        {"sector": {"semi_boost": 1.0, "ai_boost": 0.20}},
        {"sector": {"semi_boost": 1.10, "ai_boost": 0.20}},
    ],
)
def test_legacy_sector_boost_guard_rejects_unsafe_boosts(config):
    with pytest.raises(RuntimeError, match="Legacy blanket sector boosts are disabled"):
        assert_legacy_sector_boosts_disabled(config)


@pytest.mark.parametrize(
    "config",
    [
        {},
        {"sector": {}},
        {"sector": {"semi_boost": 1.0, "ai_boost": 0.0}},
        {"sector": {"semi_boost": 0.95, "ai_boost": 0.0}},
        {"sector": {"semi_boost": 1.0, "ai_boost": -0.1}},
    ],
)
def test_legacy_sector_boost_guard_accepts_neutral_or_defensive_config(config):
    assert_legacy_sector_boosts_disabled(config)


@pytest.mark.parametrize(
    "config",
    [
        {"sector": "bad"},
        {"sector": {"semi_boost": "not-a-number", "ai_boost": 0.0}},
        {"sector": {"semi_boost": 1.0, "ai_boost": "not-a-number"}},
    ],
)
def test_legacy_sector_boost_guard_rejects_invalid_config(config):
    with pytest.raises(RuntimeError):
        assert_legacy_sector_boosts_disabled(config)


def test_combined_scoring_safety_rejects_theme_scoring_enablement():
    with pytest.raises(RuntimeError, match="Theme-aware official scoring is disabled"):
        assert_scoring_safety({
            "sector": {"semi_boost": 1.0, "ai_boost": 0.0},
            "theme_scoring": {"enabled": True},
        })


def test_combined_scoring_safety_rejects_sector_boost_before_theme_config():
    with pytest.raises(RuntimeError, match="Legacy blanket sector boosts are disabled"):
        assert_scoring_safety({
            "sector": {"semi_boost": 1.1, "ai_boost": 0.2},
            "theme_scoring": {"enabled": True},
        })


def test_config_file_guard_rejects_unsafe_temp_config(tmp_path):
    p = tmp_path / "unsafe.yaml"
    p.write_text(yaml.safe_dump({
        "sector": {"semi_boost": 1.10, "ai_boost": 0.20}
    }))

    with pytest.raises(RuntimeError, match="Legacy blanket sector boosts are disabled"):
        assert_config_file_scoring_safety(p)


def test_scoring_safety_status_reports_disabled_state():
    status = scoring_safety_status({
        "sector": {"semi_boost": 1.0, "ai_boost": 0.0}
    })

    assert status["legacy_sector_boosts_disabled"] is True
    assert status["theme_aware_official_scoring_enabled"] is False
    assert status["production_scoring_effect"] is False
    assert status["configured_semi_boost"] == 1.0
    assert status["configured_ai_boost"] == 0.0


def test_config_yaml_documents_legacy_boost_disablement():
    text = Path("config.yaml").read_text()

    assert "DISABLED" in text
    assert "semi_boost: 1.0" in text
    assert "ai_boost: 0.0" in text
    assert "Original: semi_boost 1.1, ai_boost 0.2" in text
