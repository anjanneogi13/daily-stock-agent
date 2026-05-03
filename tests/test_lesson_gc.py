"""T32: stale-lesson garbage collector."""
import json
from datetime import datetime, timedelta
import pytest

from src import wisdom_base, lesson_gc


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    lessons = tmp_path / "lessons.jsonl"
    monkeypatch.setattr(wisdom_base, "LESSONS", lessons)
    monkeypatch.setattr(lesson_gc, "LESSONS", lessons)
    return lessons


def _write(path, *records):
    with path.open("w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _lesson(text, days_ago, conf=0.7, active=True):
    ts = (datetime.now() - timedelta(days=days_ago)).isoformat(timespec="seconds")
    return {
        "ts": ts, "text": text, "source": "manual",
        "confidence": conf, "tags": [], "author": "test",
        "active": active,
    }


# ═════════════════════════════════════════════════════════════
class TestFindStale:
    def test_no_file_returns_empty(self, isolated):
        assert lesson_gc.find_stale() == []

    def test_old_lesson_flagged(self, isolated):
        _write(isolated, _lesson("ancient", days_ago=120))
        stale = lesson_gc.find_stale()
        assert len(stale) == 1
        assert stale[0]["text"] == "ancient"

    def test_fresh_lesson_kept(self, isolated):
        _write(isolated, _lesson("fresh", days_ago=10))
        assert lesson_gc.find_stale() == []

    def test_boundary_just_under(self, isolated):
        _write(isolated, _lesson("boundary", days_ago=89))
        assert lesson_gc.find_stale(max_age_days=90) == []

    def test_boundary_just_over(self, isolated):
        _write(isolated, _lesson("boundary", days_ago=91))
        assert len(lesson_gc.find_stale(max_age_days=90)) == 1


class TestProtections:
    def test_high_conf_protected(self, isolated):
        _write(isolated, _lesson("trusted", days_ago=200, conf=0.95))
        assert lesson_gc.find_stale() == []

    def test_inactive_skipped(self, isolated):
        _write(isolated, _lesson("dead", days_ago=200, active=False))
        assert lesson_gc.find_stale() == []

    def test_missing_ts_kept(self, isolated):
        bad = _lesson("noTs", days_ago=200)
        bad.pop("ts")
        _write(isolated, bad)
        assert lesson_gc.find_stale() == []

    def test_unparseable_ts_kept(self, isolated):
        bad = _lesson("badTs", days_ago=200)
        bad["ts"] = "not-a-date"
        _write(isolated, bad)
        assert lesson_gc.find_stale() == []


class TestGcStale:
    def test_dry_run_no_write(self, isolated):
        _write(isolated, _lesson("ancient", days_ago=120))
        n, _ = lesson_gc.gc_stale(dry_run=True)
        assert n == 1
        # File untouched — still active
        with isolated.open() as f:
            r = json.loads(f.readline())
        assert r["active"] is True

    def test_real_run_persists(self, isolated):
        _write(isolated, _lesson("ancient", days_ago=120))
        n, _ = lesson_gc.gc_stale()
        assert n == 1
        with isolated.open() as f:
            r = json.loads(f.readline())
        assert r["active"] is False
        assert r["deactivated_reason"] == "stale>90d"
        assert "deactivated_at" in r

    def test_mixed_only_stale_touched(self, isolated):
        _write(isolated,
               _lesson("ancient",  days_ago=200),
               _lesson("fresh",    days_ago=5),
               _lesson("trusted",  days_ago=200, conf=0.95),
               _lesson("dead",     days_ago=200, active=False))
        n, _ = lesson_gc.gc_stale()
        assert n == 1
        recs = [json.loads(l) for l in isolated.read_text().splitlines()]
        active_now = [r for r in recs if r.get("active", True)]
        # fresh + trusted survive, ancient deactivated, dead stays dead
        assert {r["text"] for r in active_now} == {"fresh", "trusted"}

    def test_idempotent(self, isolated):
        _write(isolated, _lesson("ancient", days_ago=200))
        first, _  = lesson_gc.gc_stale()
        second, _ = lesson_gc.gc_stale()
        assert first == 1
        assert second == 0


class TestCLI:
    def test_cli_clean(self, isolated, capsys):
        _write(isolated, _lesson("fresh", days_ago=5))
        rc = lesson_gc._cli([])
        assert rc == 0
        assert "No stale" in capsys.readouterr().out

    def test_cli_deactivates(self, isolated, capsys):
        _write(isolated, _lesson("ancient", days_ago=200))
        rc = lesson_gc._cli([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Deactivated 1" in out

    def test_cli_dry_run(self, isolated, capsys):
        _write(isolated, _lesson("ancient", days_ago=200))
        rc = lesson_gc._cli(["--dry-run"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Would deactivate" in out
        # File still has active record
        r = json.loads(isolated.read_text().strip())
        assert r["active"] is True

    def test_cli_custom_max_age(self, isolated, capsys):
        _write(isolated, _lesson("midlife", days_ago=45))
        rc = lesson_gc._cli(["--max-age", "30"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Deactivated 1" in out

    def test_cli_custom_protect(self, isolated, capsys):
        _write(isolated, _lesson("almost-trusted", days_ago=200, conf=0.85))
        # Default protect=0.90 → would deactivate
        # Raise protect bar to 0.80 → spared
        rc = lesson_gc._cli(["--protect", "0.80"])
        assert rc == 0
        assert "No stale" in capsys.readouterr().out
