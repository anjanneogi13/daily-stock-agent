"""Task 9c / vision item #19: structured explainability in the official pick.

The artifact had a single prose `selection_reason` string. #19 wants STRUCTURED
top reasons, an explicit data-missing list, and the model version, so a pick can
be audited: why was it chosen, what data was absent, which model decided.

All three are ADDITIVE optional fields -- they must NOT break the existing
contract validator (which uses a required-field allowlist + type checks and
tolerates extra keys).
"""
from src.official_pick_artifact import (
    _top_reasons,
    _data_missing,
    _model_version,
    build_official_pick_artifact,
)
from src.premarket_decision_contract import validate_official_pick


def _pick(**over):
    base = {
        "ticker": "AAA",
        "company": "Alpha Inc",
        "trade_type": "swing",
        "scores": {"composite": 8.4, "sector_tag": "tech", "trade_type": "swing"},
        "premarket_sanity": {"reason": "gap within range"},
        "plan": {"entry": 100.0, "stop_loss": 98.0, "take_profit": 104.0,
                 "risk_reward": 2.0, "quantity": 10, "risk_dollars": 20.0},
    }
    base.update(over)
    return base


# ---- _top_reasons --------------------------------------------------------
def test_top_reasons_is_list_max_three():
    r = _top_reasons(_pick())
    assert isinstance(r, list), r
    assert len(r) <= 3, r


def test_top_reasons_includes_composite_score():
    r = _top_reasons(_pick())
    joined = " ".join(r).lower()
    assert "score" in joined or "8.4" in joined, r


def test_top_reasons_handles_missing_scores_no_crash():
    r = _top_reasons(_pick(scores={}))
    assert isinstance(r, list)  # must not raise, may be short/empty


# ---- _data_missing -------------------------------------------------------
def test_data_missing_empty_when_complete():
    assert _data_missing(_pick()) == []


def test_data_missing_lists_absent_company():
    miss = _data_missing(_pick(company=""))
    assert "company" in miss, miss


# ---- _model_version ------------------------------------------------------
def test_model_version_nonempty_default(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    mv = _model_version()
    assert isinstance(mv, str) and mv, mv  # falls back to a real default


def test_model_version_env_override(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "claude-test-9")
    assert _model_version() == "claude-test-9"


# ---- contract safety (the critical one) ----------------------------------
def test_artifact_with_explainability_still_validates():
    art = build_official_pick_artifact(
        _pick(),
        regime={"label": "risk_on"},
        data_readiness_status="ready",
        provider_status="healthy",
        market_session_status="premarket",
    )
    # New fields present...
    assert isinstance(art.get("top_reasons"), list), art.get("top_reasons")
    assert isinstance(art.get("data_missing"), list)
    assert art.get("model_version")
    # ...and the artifact STILL passes the contract validator (additive, no break).
    errors = validate_official_pick(art)
    assert errors == [], f"explainability fields broke contract validation: {errors}"
