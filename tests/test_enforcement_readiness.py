"""F5: enforcement-readiness scorer tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.check_enforcement_readiness import (
    check_smell_enforce, check_brain_enforce_ev, check_auto_pause,
    run_all, format_report,
)


def _row(status="tp_hit", tag="none", brain_ev=None, r_mult=None,
         pick_date="2026-05-03"):
    return {
        "pick_date": pick_date,
        "ticker": "TEST",
        "tag": tag,
        "evaluation_status": status,
        "brain_ev_pct": str(brain_ev) if brain_ev is not None else "",
        "r_multiple": str(r_mult) if r_mult is not None else "",
    }


# ════════════════════════════════════════════════════════════════
# Smell enforce
# ════════════════════════════════════════════════════════════════
def test_smell_enforce_not_ready_when_no_data():
    r = check_smell_enforce([])
    assert r["ready"] is False
    assert "smell_verdicts_not_persisted" in r["blockers"]


# ════════════════════════════════════════════════════════════════
# Brain EV enforce
# ════════════════════════════════════════════════════════════════
def test_brain_ev_blocked_when_low_n():
    r = check_brain_enforce_ev([_row()])
    assert r["ready"] is False
    assert any("n=" in b for b in r["blockers"])


def test_brain_ev_ready_when_n_and_correlation():
    """30 closed picks, EV positively correlates with r_multiple."""
    rows = []
    for i in range(35):
        # Synthesize: high EV → win, low EV → loss
        ev = 1.0 if i < 20 else -1.0
        rm = 2.0 if i < 20 else -1.0
        rows.append(_row(status="tp_hit" if rm > 0 else "sl_hit",
                         brain_ev=ev, r_mult=rm))
    r = check_brain_enforce_ev(rows)
    assert r["n_observed"] == 35
    assert r["ev_correlation"] is not None and r["ev_correlation"] > 0
    assert r["ready"] is True


def test_brain_ev_blocked_when_correlation_negative():
    """If EV negatively correlates with outcome, do NOT flip."""
    rows = []
    for i in range(35):
        ev = 1.0 if i < 20 else -1.0
        rm = -1.0 if i < 20 else 2.0  # INVERTED — high EV → loss
        rows.append(_row(status="sl_hit" if rm < 0 else "tp_hit",
                         brain_ev=ev, r_mult=rm))
    r = check_brain_enforce_ev(rows)
    assert r["ready"] is False
    assert any("correlation" in b for b in r["blockers"])


# ════════════════════════════════════════════════════════════════
# Auto-pause
# ════════════════════════════════════════════════════════════════
def test_auto_pause_blocked_when_low_n():
    rows = [_row() for _ in range(10)]
    r = check_auto_pause(rows)
    assert r["ready"] is False


def test_auto_pause_ready_when_bad_group_exists():
    """50+ closed; SEMI tag has 6/8 losses → bad group → ready."""
    rows = [_row(status="tp_hit", tag="HEALTHCARE") for _ in range(50)]
    rows += [_row(status="sl_hit", tag="SEMI") for _ in range(6)]
    rows += [_row(status="tp_hit", tag="SEMI") for _ in range(2)]
    r = check_auto_pause(rows)
    assert r["n_observed"] == 58
    assert r["ready"] is True
    assert r["bad_groups"], "SEMI should be flagged as bad"
    assert any(g["tag"] == "SEMI" for g in r["bad_groups"])


def test_auto_pause_blocked_when_no_bad_group():
    """50+ closed but everyone is winning → nothing to pause."""
    rows = [_row(status="tp_hit", tag="HEALTHCARE") for _ in range(50)]
    r = check_auto_pause(rows)
    assert r["ready"] is False


# ════════════════════════════════════════════════════════════════
# Orchestration
# ════════════════════════════════════════════════════════════════
def test_run_all_returns_three_gates():
    results = run_all()
    assert len(results) == 3
    gates = {r["gate"] for r in results}
    assert gates == {"SMELL_ENFORCE", "BRAIN_ENFORCE_EV", "AUTO_PAUSE_ENABLED"}


def test_format_report_includes_all_gates():
    text = format_report(run_all())
    assert "SMELL_ENFORCE" in text
    assert "BRAIN_ENFORCE_EV" in text
    assert "AUTO_PAUSE_ENABLED" in text
    assert "DASHBOARD" in text


def test_no_gate_is_falsely_ready_today():
    """Sanity: with current real data (n=0 post-floor), nothing should be ready."""
    results = run_all()
    ready = [r for r in results if r["ready"]]
    assert not ready, (
        f"Gate marked ready prematurely with current data: "
        f"{[r['gate'] for r in ready]}"
    )
