"""BUG-M97: monster treatment must be re-validated against the portfolio
risk gate BEFORE its SL/TP/qty overwrite the gate-approved plan.

Background
---------
In main.py the order is: portfolio risk gate -> write official artifact ->
apply_monster_treatment (overwrites plan SL/TP/qty). The monster mutation is
NEVER re-checked by the gate, so a pick approved at <=1.05% risk can ship at
~1.5% risk (monster position_pct), and the artifact (pre-mutation) disagrees
with the CSV (post-mutation).

Fix under test
--------------
src.monster_hunt.revalidate_and_apply_monster(pick, monster_score, cfg,
    sector_counts, tag_counts) must:
  * compute monster treatment,
  * re-validate the treated SL/TP/qty against evaluate_candidate_portfolio_risk
    (risk/structural limits only; diversity caps unchanged),
  * apply to pick["plan"] ONLY if it still passes,
  * otherwise leave pick["plan"] at its gate-approved (pre-monster) values
    (fail-closed = B1 revert),
  * return {"applied": bool, "reason": str}.
"""
import importlib

import pytest

monster_hunt = importlib.import_module("src.monster_hunt")


# config whose per-trade cap (1.0% * 1.05 = 1.05%) is BELOW monster's 1.5%
CFG = {
    "risk": {
        "account_size": 10000.0,
        "risk_per_trade_pct": 1.0,        # gate cap becomes 1.05%
        "min_risk_reward": 1.0,
        "max_per_sector": 99,
        "max_per_tag": 99,
    },
    "monster": {"enabled": True, "threshold": 0.60, "position_pct": 1.5},
}


def _gate_approved_pick():
    """A pick whose plan PASSES the gate at <=1.05% risk pre-monster.

    entry=100, SL=99 (1pt risk), qty=10 -> risk_dollars=10 -> 0.10% of 10k. OK.
    RR: TP=102 -> (102-100)/(100-99)=2.0 >= 1.0. OK.
    """
    return {
        "ticker": "TEST",
        "plan": {
            "entry": 100.0,
            "stop_loss": 99.0,
            "take_profit": 102.0,
            "quantity": 10,
            "risk_reward": 2.0,
        },
        "scores": {"composite": 0.90, "monster_score": 0.80},
        "info_short": {"sector": "Tech"},
    }


def test_function_exists():
    """The fix must expose revalidate_and_apply_monster."""
    assert hasattr(monster_hunt, "revalidate_and_apply_monster"), (
        "BUG-M97 fix missing: src.monster_hunt.revalidate_and_apply_monster "
        "is not defined."
    )


def test_monster_exceeding_cap_is_not_applied():
    """A monster whose treated risk (~1.5%) exceeds the gate cap (1.05%) must
    NOT overwrite the gate-approved plan (fail-closed to pre-monster values)."""
    pick = _gate_approved_pick()
    pre_sl = pick["plan"]["stop_loss"]
    pre_tp = pick["plan"]["take_profit"]
    pre_qty = pick["plan"]["quantity"]

    res = monster_hunt.revalidate_and_apply_monster(
        pick, pick["scores"]["monster_score"], CFG,
        sector_counts={}, tag_counts={},
    )

    # Monster treatment widens SL to entry*0.95=95 and sizes qty to 1.5% risk,
    # which exceeds the 1.05% cap -> must be rejected.
    assert res["applied"] is False, (
        f"monster exceeding risk cap was applied anyway: {res}"
    )
    # plan must be untouched (still gate-approved values)
    assert pick["plan"]["stop_loss"] == pre_sl, "plan SL was mutated despite failing re-validation"
    assert pick["plan"]["take_profit"] == pre_tp, "plan TP was mutated despite failing re-validation"
    assert pick["plan"]["quantity"] == pre_qty, "plan qty was mutated despite failing re-validation"


def test_monster_within_cap_is_applied():
    """If the cap is wide enough to accommodate monster sizing, the treatment
    SHOULD apply and overwrite the plan."""
    cfg = {**CFG, "risk": {**CFG["risk"], "risk_per_trade_pct": 2.0}}  # cap=2.1% > 1.5%
    pick = _gate_approved_pick()

    res = monster_hunt.revalidate_and_apply_monster(
        pick, pick["scores"]["monster_score"], cfg,
        sector_counts={}, tag_counts={},
    )

    assert res["applied"] is True, f"monster within cap was not applied: {res}"
    # SL should now be the monster 5% stop (entry*0.95 = 95.0)
    assert pick["plan"]["stop_loss"] == 95.0, "monster SL not applied when within cap"
    assert pick["plan"]["take_profit"] == 125.0, "monster TP not applied when within cap"
