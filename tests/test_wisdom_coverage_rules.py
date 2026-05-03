"""T42: edges/warnings split in wisdom_coverage."""
from __future__ import annotations
import pytest
import src.wisdom_coverage as wc


def test_coverage_empty():
    s = wc.coverage([])
    assert s == {"total":0,"tagged":0,"lessons":0,"patterns":0,"pct":0.0}


def test_coverage_counts_edges_and_warnings(monkeypatch):
    rows = [{"ticker":"A"},{"ticker":"B"},{"ticker":"C"},{"ticker":"D"}]
    # mock: A=edge, B=warning, C=lesson-only, D=nothing
    def fake_wh(t, sector=None):
        return "Livermore: trend is your friend" if t == "C" else ""
    def fake_ph(r):
        if r["ticker"] == "A": return "✨ edge: bull flag"
        if r["ticker"] == "B": return "⚠ drag: rsi overbought"
        return ""
    monkeypatch.setattr(wc, "wisdom_hint", fake_wh)
    monkeypatch.setattr(wc, "pattern_hint", fake_ph)
    s = wc.coverage(rows)
    assert s["total"]    == 4
    assert s["tagged"]   == 3
    assert s["lessons"]  == 1
    assert s["patterns"] == 2
    assert s["edges"]    == 1
    assert s["warnings"] == 1


def test_format_footer_includes_rules_check_when_present():
    stats = {"total":3,"tagged":2,"lessons":1,"patterns":2,
             "edges":1,"warnings":1,"pct":66.7}
    out = wc.format_footer(stats)
    assert "Wisdom:" in out
    assert "Rules check" in out
    assert "✨ 1 matched" in out
    assert "⚠ 1 warnings" in out


def test_format_footer_omits_rules_check_when_zero():
    stats = {"total":3,"tagged":1,"lessons":1,"patterns":0,
             "edges":0,"warnings":0,"pct":33.3}
    out = wc.format_footer(stats)
    assert "Wisdom:" in out
    assert "Rules check" not in out


def test_format_footer_empty_when_no_picks():
    assert wc.format_footer({"total":0}) == ""
