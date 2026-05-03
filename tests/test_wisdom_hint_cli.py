"""T25: CLI dry-run preview for wisdom_hint."""
import csv
import pytest
from src import wisdom_base, wisdom_hint as wh_mod


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(wisdom_base, "LESSONS",  tmp_path / "lessons.jsonl")
    monkeypatch.setattr(wisdom_base, "PATTERNS", tmp_path / "patterns.jsonl")
    monkeypatch.setattr(wisdom_base, "KILL",     tmp_path / "kill.json")
    return tmp_path


class TestCLI:
    def test_no_args_returns_zero(self, isolated, capsys):
        assert wh_mod._cli([]) == 0
        assert "No tickers" in capsys.readouterr().out

    def test_inline_tickers_no_lessons(self, isolated, capsys):
        rc = wh_mod._cli(["AAPL", "NVDA"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "AAPL" in out and "NVDA" in out
        assert "0/2" in out

    def test_inline_tickers_with_hits(self, isolated, capsys):
        wisdom_base.add_lesson(text="AAPL chops in low VIX",
                                source="t", confidence=0.85,
                                tags=["AAPL"], author="t")
        rc = wh_mod._cli(["AAPL", "NVDA"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "1/2" in out
        assert "AAPL chops" in out

    def test_from_csv(self, isolated, capsys):
        csv_path = isolated / "picks.csv"
        with csv_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["ticker", "pick_date"])
            w.writeheader()
            w.writerow({"ticker": "TSLA", "pick_date": "2026-05-03"})
            w.writerow({"ticker": "OLD",  "pick_date": "2020-01-01"})
        wisdom_base.add_lesson(text="TSLA wisdom", source="t",
                                confidence=0.9, tags=["TSLA"], author="t")
        rc = wh_mod._cli(["--from-csv", str(csv_path), "--date", "2026-05-03"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "TSLA wisdom" in out
        assert "OLD" not in out

    def test_csv_missing_returns_2(self, isolated):
        assert wh_mod._cli(["--from-csv", "/no/such/file.csv"]) == 2

    def test_min_confidence_flag(self, isolated, capsys):
        wisdom_base.add_lesson(text="weak", source="t",
                                confidence=0.65, tags=["X"], author="t")
        # Default 0.7 -> miss
        wh_mod._cli(["X"])
        out1 = capsys.readouterr().out
        assert "0/1" in out1
        # Lower threshold -> hit
        wh_mod._cli(["--min-confidence", "0.6", "X"])
        out2 = capsys.readouterr().out
        assert "1/1" in out2
