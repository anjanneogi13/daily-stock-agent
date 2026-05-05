"""Bug #8b: dict.get(key, default) returns None when key exists with None
value — the default is ONLY used when the key is missing entirely.
This bit us in main.py:575: _sclose = p.get("_sector_close", "")
When sector ETF fetch failed, the cache stored None, and the dict carried
None forward, which csv.DictWriter then wrote as empty.

Fix: use `p.get("key") or default` to coerce None → default."""


def test_dict_get_with_none_value_returns_None_not_default():
    """Documents the Python gotcha that motivated this fix."""
    d = {"_sector_close": None}
    # The naive pattern silently returns None:
    assert d.get("_sector_close", "") is None
    # The robust pattern coerces None to default:
    assert (d.get("_sector_close") or "") == ""


def test_dict_get_with_missing_key_returns_default():
    """Confirms the gotcha is specific to None values, not missing keys."""
    d = {}
    assert d.get("_sector_close", "") == ""
    assert (d.get("_sector_close") or "") == ""


def test_dict_get_or_pattern_preserves_truthy_values():
    """Regression guard: `or default` must NOT clobber valid floats/strings."""
    assert ({"x": 144.73}.get("x") or "") == 144.73
    assert ({"x": "SPY"}.get("x") or "") == "SPY"
    assert ({"x": 0.5}.get("x") or "") == 0.5


def test_main_py_sclose_assignment_uses_or_idiom():
    """Static check: main.py line for _sclose must use the `or ""` idiom,
    not the unsafe `.get(key, "")` pattern. Guards against regression."""
    from pathlib import Path
    src = Path("main.py").read_text()
    # The fixed line should contain the or-coercion idiom
    assert '_sclose = p.get("_sector_close") or ""' in src, (
        "main.py must use `p.get('_sector_close') or \"\"` to coerce "
        "None (cache miss / fetch failure) to empty string. "
        "The `.get(key, default)` pattern silently passes None through."
    )


def test_main_py_setf_assignment_uses_or_idiom():
    """Same gotcha for sector_etf — _p['_sector_etf'] could theoretically
    be None if resolve_sector_etf returned None (it shouldn't, but defensive)."""
    from pathlib import Path
    src = Path("main.py").read_text()
    assert '_setf = p.get("_sector_etf") or "SPY"' in src, (
        "main.py must use `or 'SPY'` to coerce None to SPY fallback."
    )
