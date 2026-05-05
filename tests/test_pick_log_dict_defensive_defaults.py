"""Bug #14 (2026-05-05): defensive None-coercion in main.py picks_for_log.

Same root cause as Bug #8b: `dict.get(key, default)` returns None (not
default) when the key exists with None. For fields that have a SEMANTIC
default (e.g., trade_type='swing', qty=0, multiplier=1.0), None passing
through corrupts CSV columns and downstream math (e.g., round(None, 3)
would TypeError; arithmetic on '' would TypeError).

Fields WITHOUT a semantic default (entry, stop_loss, brain_*, etc.) are
left alone — None there genuinely means 'no data' and writing empty
string to CSV is correct."""
from pathlib import Path
import re

SRC = Path("main.py").read_text()


def _block():
    """Return the picks_for_log.append({...}) block in main.py."""
    m = re.search(r'picks_for_log\.append\(\{(.+?)^\s*\}\)', SRC, re.DOTALL | re.MULTILINE)
    assert m, "picks_for_log.append block not found"
    return m.group(1)


def test_trade_type_uses_or_default():
    assert 'p.get("trade_type") or "swing"' in _block()


def test_score_uses_or_default():
    assert '"composite") or 0' in _block()


def test_multiplier_uses_or_default():
    assert '"sector_mult") or 1.0' in _block()


def test_risk_reward_uses_or_default():
    assert '"risk_reward") or 2.0' in _block()


def test_qty_uses_or_default():
    assert '"quantity") or 0' in _block()


def test_monster_score_uses_or_default():
    assert '"monster_score") or 0' in _block()


def test_is_monster_uses_explicit_bool_coercion():
    """is_monster is special: falsy default is False but `or False` is fine
    because False/None/0 all coerce to False semantically."""
    assert '"is_monster") or False' in _block()


def test_no_data_fields_left_alone():
    """Regression guard: fields where None is valid 'no data' must NOT
    be coerced (would mask missing data as 0)."""
    blk = _block()
    # entry/stop_loss/take_profit have no default — None means no plan
    assert 'p["plan"].get("entry")' in blk
    assert 'p["plan"].get("stop_loss")' in blk
    # brain fields — None means brain didn't evaluate, must show as empty
    assert 'brain.get("p_win")' in blk
    assert 'brain.get("ev_pct")' in blk
