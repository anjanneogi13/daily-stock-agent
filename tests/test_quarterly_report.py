"""Tests for quarterly report generator."""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

import src.quarterly_report as qr


def test_quarter_label():
    assert qr._quarter_label(datetime(2026, 1, 15)) == "2026_Q1"
    assert qr._quarter_label(datetime(2026, 5, 3))  == "2026_Q2"
    assert qr._quarter_label(datetime(2026, 8, 1))  == "2026_Q3"
    assert qr._quarter_label(datetime(2026, 12, 31)) == "2026_Q4"


def test_summary_metrics_empty():
    m = qr._summary_metrics([])
    assert m["total_picks"] == 0
    assert m["closed_picks"] == 0
    assert m["win_rate"] is None


def test_summary_metrics_with_data():
    picks = [
        {"evaluation_status": "tp_hit",  "r_multiple": "2.0",
         "actual_return_pct": "8.0", "alpha_pct": "3.0",
         "sector_alpha_pct": "1.5"},
        {"evaluation_status": "sl_hit",  "r_multiple": "-1.0",
         "actual_return_pct": "-3.0", "alpha_pct": "-2.0",
         "sector_alpha_pct": "-1.0"},
        {"evaluation_status": "open"},  # ignored
    ]
    m = qr._summary_metrics(picks)
    assert m["total_picks"] == 3
    assert m["closed_picks"] == 2
    assert m["wins"] == 1
    assert m["losses"] == 1
    assert m["win_rate"] == 0.5
    assert m["total_r"] == 1.0
    assert m["avg_alpha_spy"] == 0.5
    assert m["avg_alpha_sec"] == 0.25


def test_top_movers_handles_few_rows():
    picks = [
        {"ticker": "A", "r_multiple": "2.0"},
        {"ticker": "B", "r_multiple": "-3.0"},
    ]
    w, L = qr._top_movers(picks, k=5)
    assert w[0]["ticker"] == "A"
    assert L[0]["ticker"] == "B"


def test_generate_report_smoke(tmp_path, monkeypatch):
    """Run end-to-end against real data — just ensure no crash and file appears."""
    monkeypatch.setattr(qr, "REPORTS", tmp_path)
    out = qr.generate_report(days=30)
    assert out.exists()
    text = out.read_text()
    assert "Quarterly Report" in text
    assert "Headline" in text
    assert "Hypothesis Engine" in text
    assert "Wisdom Base" in text
    assert "System Changes" in text
