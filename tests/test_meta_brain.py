"""T50: Meta-brain — recent mutations, stuck detection, hypotheses, digest."""
import csv
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from src import meta_brain as mb


@pytest.fixture
def journal(tmp_path, monkeypatch):
    p = tmp_path / "journal.jsonl"
    monkeypatch.setattr(mb, "JOURNAL", p)
    return p


@pytest.fixture
def picks(tmp_path, monkeypatch):
    p = tmp_path / "picks.csv"
    monkeypatch.setattr(mb, "PICKS", p)
    return p


def _write_journal(p, events):
    with p.open("w") as f:
        for e in events: f.write(json.dumps(e) + "\n")


def _now(): return datetime.now()
def _iso(dt): return dt.isoformat()


# ── Recent mutations ────────────────────────────────────────────
def test_recent_mutations_empty_when_no_journal(journal):
    assert mb.recent_mutations() == []


def test_recent_mutations_filters_by_age(journal):
    _write_journal(journal, [
        {"kind":"weight_applied", "ts": _iso(_now() - timedelta(days=3))},
        {"kind":"weight_applied", "ts": _iso(_now() - timedelta(days=20))},
    ])
    out = mb.recent_mutations(days=7)
    assert len(out) == 1


def test_categorize_groups_by_kind(journal):
    events = [
        {"kind":"weight_applied"},
        {"kind":"weight_applied"},
        {"kind":"pattern_disabled","pattern":"x"},
    ]
    by = mb.categorize_mutations(events)
    assert len(by["weight_applied"]) == 2
    assert len(by["pattern_disabled"]) == 1


# ── Stuck detection ─────────────────────────────────────────────
def test_stuck_when_no_events():
    res = mb.detect_stuck_areas([])
    assert res["stuck"] is True
    assert res["severity"] == "high"


def test_stuck_when_old_events_only():
    events = [{"ts": _iso(_now() - timedelta(days=20))}]
    res = mb.detect_stuck_areas(events, stuck_days=14)
    assert res["stuck"] is True


def test_not_stuck_with_recent_event():
    events = [{"ts": _iso(_now() - timedelta(days=2))}]
    res = mb.detect_stuck_areas(events, stuck_days=14)
    assert res["stuck"] is False


# ── Hypothesis suggestor ────────────────────────────────────────
def test_suggest_hypotheses_empty_picks(picks):
    assert mb.suggest_hypotheses() == []


def test_suggest_hypotheses_finds_outperformer(picks):
    today = _now().date()
    rows = []
    # 25 SEMI picks, all winners (way above baseline)
    for i in range(25):
        rows.append({"pick_date": str(today - timedelta(days=i)),
                     "sector_cat":"SEMI",
                     "trade_type":"swing",
                     "regime":"bull",
                     "r_multiple":"2.0"})
    # 25 OTHER picks, all losers
    for i in range(25):
        rows.append({"pick_date": str(today - timedelta(days=i)),
                     "sector_cat":"OTHER",
                     "trade_type":"swing",
                     "regime":"bull",
                     "r_multiple":"-1.0"})
    with picks.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pick_date","sector_cat","trade_type","regime","r_multiple"])
        w.writeheader()
        for r in rows: w.writerow(r)
    hyps = mb.suggest_hypotheses(min_n=20)
    # At least SEMI flagged outperforming
    assert any(h["label"] == "SEMI" and h["direction"] == "outperforming" for h in hyps)


# ── Digest + Telegram format ────────────────────────────────────
def test_digest_quiet_week(journal, picks):
    digest = mb.build_self_improvement_digest()
    assert digest["n_events"] == 0
    assert digest["stuck"]["stuck"] is True


def test_digest_with_mutations(journal, picks):
    _write_journal(journal, [
        {"kind":"weight_applied","ts": _iso(_now())},
        {"kind":"pattern_disabled","ts": _iso(_now()), "pattern":"rising_wedge"},
        {"kind":"lesson_promoted","ts": _iso(_now())},
    ])
    digest = mb.build_self_improvement_digest()
    assert digest["n_events"] == 3
    assert digest["stuck"]["stuck"] is False
    assert any("Adjusted how it weighs" in line for line in digest["plain_english"])
    assert any("rising_wedge" in line for line in digest["plain_english"])


def test_format_telegram_digest_quiet():
    digest = {
        "days":7, "n_events":0, "by_kind":{},
        "stuck":{"stuck":True,"reason":"No mutations","severity":"high"},
        "hypotheses":[],
        "plain_english":[],
    }
    msg = mb.format_telegram_digest(digest)
    assert "Self-Improvement Report" in msg
    assert "Quiet week" in msg
    assert "Heads up" in msg


def test_format_telegram_digest_active_week():
    digest = {
        "days":7, "n_events":3,
        "by_kind":{"weight_applied":2,"pattern_disabled":1},
        "stuck":{"stuck":False,"age_days":2},
        "hypotheses":[
            {"group":"sector_cat","label":"SEMI","n":25,
             "win_rate":0.72,"baseline":0.50,"delta":0.22,"direction":"outperforming"},
        ],
        "plain_english":[
            "📊 Adjusted how it weighs 2 signal(s) when scoring stocks",
            "🚫 Stopped using 1 chart pattern(s) that were losing money: rising_wedge",
        ],
    }
    msg = mb.format_telegram_digest(digest)
    assert "smarter in these ways" in msg
    assert "investigating next" in msg
    assert "SEMI" in msg
    assert "Heads up" not in msg
