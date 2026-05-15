"""PR-A2.6: official_pick_artifact must fall back to ticker when company name unavailable.

Real-world bug: 2026-05-15 workflow run failed because AMAT pick had empty 'company'
field (yfinance rate-limited, info.name blank). Validator rejected it as
"missing required field: company", workflow crashed, no Telegram, no pick.
Fix: fall back to ticker symbol.
"""
from src.official_pick_artifact import build_official_pick_artifact
from src.premarket_decision_contract import (
    validate_official_pick,
    OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES,
)


def _base_pick(ticker="AMAT"):
    return {
        "ticker": ticker,
        "company": "",  # ← intentionally blank, mirrors the real 2026-05-15 failure
        "info_short": {},  # ← yfinance rate-limited, no info
        "scores": {"composite": 0.947, "day_score": 0.99, "sector_tag": "SEMI / AI"},
        "plan": {"entry": 440.56, "stop_loss": 429.35, "take_profit": 459.24,
                 "risk_reward": 1.67, "quantity": 10},
        "trade_type": "day",
    }


def test_company_falls_back_to_ticker_when_name_missing():
    artifact = build_official_pick_artifact(_base_pick(), date_str="2026-05-15")
    assert artifact["company"] == "AMAT", \
        f"company should fall back to ticker symbol, got {artifact['company']!r}"


def test_artifact_validates_when_company_falls_back_to_ticker():
    artifact = build_official_pick_artifact(_base_pick(), date_str="2026-05-15")
    errors = validate_official_pick(artifact)
    assert errors == [], f"validation should pass with ticker fallback, got: {errors}"


def test_company_uses_real_name_when_available():
    pick = _base_pick()
    pick["info_short"] = {"name": "Applied Materials, Inc."}
    artifact = build_official_pick_artifact(pick, date_str="2026-05-15")
    assert artifact["company"] == "Applied Materials, Inc."


def test_company_uses_pick_company_when_info_short_blank():
    pick = _base_pick()
    pick["company"] = "Applied Materials"
    artifact = build_official_pick_artifact(pick, date_str="2026-05-15")
    assert artifact["company"] == "Applied Materials"


def test_unknown_fallback_when_ticker_also_missing():
    pick = _base_pick(ticker="")
    artifact = build_official_pick_artifact(pick, date_str="2026-05-15")
    assert artifact["company"] == "UNKNOWN"


def test_validation_failed_enum_now_allowed():
    """BUG-B: when artifact validation fails, no-pick writer needs a valid enum."""
    assert "NO_PICK_OFFICIAL_PICK_ARTIFACT_VALIDATION_FAILED" \
        in OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES
