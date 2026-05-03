"""Tests for src/book_ingest (T35)."""
from __future__ import annotations
import json
from pathlib import Path

import pytest
import yaml

from src import book_ingest


# ───────────────── fixtures ─────────────────

@pytest.fixture
def tiny_seed(tmp_path: Path) -> Path:
    data = {
        "meta": {"version": 1, "total_rules": 3},
        "books": [
            {
                "slug": "testlib",
                "title": "Test Library",
                "author": "Test Author",
                "year": 2026,
                "rules": [
                    {"id": "t-01", "text": "Rule one.", "tags": ["risk"], "confidence": 0.9},
                    {"id": "t-02", "text": "Rule two.", "tags": ["psychology"], "confidence": 0.85},
                ],
            },
            {
                "slug": "tinybook",
                "title": "Tiny",
                "author": "Solo",
                "year": 2025,
                "rules": [
                    {"id": "x-01", "text": "Solo wisdom.", "confidence": 0.8},
                ],
            },
        ],
    }
    p = tmp_path / "seed.yaml"
    p.write_text(yaml.safe_dump(data))
    return p


@pytest.fixture
def isolated_lessons(tmp_path: Path, monkeypatch):
    """Point wisdom_base.LESSONS at a temp file so tests don't touch real data."""
    fake = tmp_path / "lessons.jsonl"
    import src.wisdom_base as wb
    monkeypatch.setattr(wb, "LESSONS", fake)
    monkeypatch.setattr(book_ingest, "LESSONS", fake)
    return fake


# ───────────────── tests ─────────────────

def test_load_seed_file_parses(tiny_seed: Path):
    data = book_ingest.load_seed_file(tiny_seed)
    assert "books" in data
    assert len(data["books"]) == 2

def test_load_seed_file_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        book_ingest.load_seed_file(tmp_path / "nope.yaml")

def test_load_seed_file_bad_schema_raises(tmp_path: Path):
    p = tmp_path / "bad.yaml"
    p.write_text("foo: bar\n")
    with pytest.raises(ValueError):
        book_ingest.load_seed_file(p)

def test_load_seed_inserts_rules(tiny_seed, isolated_lessons):
    res = book_ingest.load_seed(tiny_seed)
    assert res["inserted"] == 3
    assert res["skipped"] == 0
    assert res["books"] == 2
    assert res["rules"] == 3

    # verify they landed
    lines = isolated_lessons.read_text().strip().splitlines()
    assert len(lines) == 3
    recs = [json.loads(ln) for ln in lines]
    sources = {r["source"] for r in recs}
    assert sources == {"book:testlib", "book:tinybook"}

def test_load_seed_is_idempotent(tiny_seed, isolated_lessons):
    book_ingest.load_seed(tiny_seed)
    res2 = book_ingest.load_seed(tiny_seed)
    assert res2["inserted"] == 0
    assert res2["skipped"] == 3

def test_load_seed_dry_run(tiny_seed, isolated_lessons):
    res = book_ingest.load_seed(tiny_seed, dry_run=True)
    assert res["inserted"] == 3
    assert res["dry_run"] is True
    assert not isolated_lessons.exists() or isolated_lessons.read_text() == ""

def test_load_seed_attaches_rule_id_tag(tiny_seed, isolated_lessons):
    book_ingest.load_seed(tiny_seed)
    recs = [json.loads(ln) for ln in isolated_lessons.read_text().strip().splitlines()]
    rule_one = next(r for r in recs if r["text"] == "Rule one.")
    assert "rule:t-01" in rule_one["tags"]
    assert "risk" in rule_one["tags"]

def test_load_seed_uses_author_field(tiny_seed, isolated_lessons):
    book_ingest.load_seed(tiny_seed)
    recs = [json.loads(ln) for ln in isolated_lessons.read_text().strip().splitlines()]
    assert any(r["author"] == "Test Author" for r in recs)
    assert any(r["author"] == "Solo" for r in recs)

def test_load_seed_skips_empty_text(tmp_path, isolated_lessons):
    p = tmp_path / "s.yaml"
    p.write_text(yaml.safe_dump({
        "books": [{"slug": "x", "rules": [
            {"id": "a", "text": "", "confidence": 0.9},
            {"id": "b", "text": "valid", "confidence": 0.9},
        ]}]
    }))
    res = book_ingest.load_seed(p)
    assert res["inserted"] == 1
    assert res["skipped"] == 1

def test_list_books(tiny_seed):
    books = book_ingest.list_books(tiny_seed)
    assert len(books) == 2
    assert books[0]["slug"] == "testlib"
    assert books[0]["rules"] == 2

def test_book_stats(tiny_seed, isolated_lessons):
    book_ingest.load_seed(tiny_seed)
    s = book_ingest.book_stats()
    assert s == {"testlib": 2, "tinybook": 1}

def test_book_stats_empty(isolated_lessons):
    assert book_ingest.book_stats() == {}

def test_book_stats_ignores_inactive(tiny_seed, isolated_lessons):
    book_ingest.load_seed(tiny_seed)
    # mark one inactive
    lines = isolated_lessons.read_text().strip().splitlines()
    recs = [json.loads(ln) for ln in lines]
    recs[0]["active"] = False
    isolated_lessons.write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    s = book_ingest.book_stats()
    assert sum(s.values()) == 2  # one deactivated

def test_real_seed_file_loads_50_rules():
    """Smoke test: the actual data/books/seed.yaml has 50 rules across 10 books."""
    real = Path("data/books/seed.yaml")
    if not real.exists():
        pytest.skip("real seed file not present")
    data = book_ingest.load_seed_file(real)
    total = sum(len(b.get("rules", [])) for b in data["books"])
    assert len(data["books"]) == 10
    assert total == 50

def test_cli_list_books_runs(tiny_seed, capsys, monkeypatch):
    monkeypatch.setattr(book_ingest, "DEFAULT_SEED", tiny_seed)
    rc = book_ingest.main(["list-books"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "testlib" in out and "tinybook" in out

def test_cli_load_seed_dry_run(tiny_seed, isolated_lessons, capsys):
    rc = book_ingest.main(["load-seed", "--path", str(tiny_seed), "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY-RUN" in out
    assert "Inserted: 3" in out

def test_cli_stats_empty(isolated_lessons, capsys):
    rc = book_ingest.main(["stats"])
    assert rc == 0
    assert "no book-sourced" in capsys.readouterr().out
