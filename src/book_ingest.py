"""T35: Books-into-Brain loader.

Reads data/books/seed.yaml and inserts each rule into wisdom_base.LESSONS
with source="book:<slug>" so wisdom_hint can attribute lines like:
    🧠 _Livermore: Never average down a losing position._

Idempotent — won't double-insert if a rule's text already exists with
source=book:<same-slug>.

CLI:
    python -m src.book_ingest load-seed [--path data/books/seed.yaml] [--dry-run]
    python -m src.book_ingest list-books
    python -m src.book_ingest stats
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import yaml

from src.wisdom_base import add_lesson, LESSONS

DEFAULT_SEED = Path("data/books/seed.yaml")


def load_seed_file(path: Path | str = DEFAULT_SEED) -> Dict:
    """Parse a books seed YAML file. Raises if malformed."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"seed file not found: {p}")
    with p.open() as f:
        data = yaml.safe_load(f) or {}
    if "books" not in data:
        raise ValueError(f"seed file missing 'books' key: {p}")
    return data


def _existing_book_lessons() -> set[Tuple[str, str]]:
    """Return set of (source, text) already in LESSONS for dedup."""
    out: set[Tuple[str, str]] = set()
    if not LESSONS.exists():
        return out
    with LESSONS.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            src = rec.get("source", "")
            if src.startswith("book:"):
                out.add((src, rec.get("text", "")))
    return out


def load_seed(path: Path | str = DEFAULT_SEED,
              dry_run: bool = False) -> Dict[str, int]:
    """Insert all rules from the seed YAML into wisdom_base.LESSONS.

    Returns counts: {"inserted": N, "skipped": M, "books": K, "rules": R}
    """
    data = load_seed_file(path)
    existing = _existing_book_lessons()

    inserted = 0
    skipped = 0
    total_rules = 0

    for book in data.get("books", []):
        slug = book.get("slug", "unknown")
        author = book.get("author", "unknown")
        source = f"book:{slug}"
        for rule in book.get("rules", []):
            total_rules += 1
            text = rule.get("text", "").strip()
            if not text:
                skipped += 1
                continue
            if (source, text) in existing:
                skipped += 1
                continue
            tags = list(rule.get("tags", []))
            # tag the book id for traceability
            rid = rule.get("id")
            if rid:
                tags = tags + [f"rule:{rid}"]
            conf = float(rule.get("confidence", 0.85))
            if not dry_run:
                add_lesson(
                    text=text,
                    source=source,
                    confidence=conf,
                    tags=tags,
                    author=author,
                )
            inserted += 1

    return {
        "inserted": inserted,
        "skipped": skipped,
        "books":    len(data.get("books", [])),
        "rules":    total_rules,
        "dry_run":  dry_run,
    }


def list_books(path: Path | str = DEFAULT_SEED) -> List[Dict]:
    data = load_seed_file(path)
    return [
        {
            "slug":   b.get("slug"),
            "title":  b.get("title"),
            "author": b.get("author"),
            "year":   b.get("year"),
            "rules":  len(b.get("rules", [])),
        }
        for b in data.get("books", [])
    ]


def book_stats() -> Dict[str, int]:
    """Count active book-sourced lessons by book slug."""
    out: Dict[str, int] = {}
    if not LESSONS.exists():
        return out
    with LESSONS.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not rec.get("active", True):
                continue
            src = rec.get("source", "")
            if src.startswith("book:"):
                slug = src.split(":", 1)[1]
                out[slug] = out.get(slug, 0) + 1
    return out


# ───────────────────────── CLI ─────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="book_ingest",
                                 description="Books-into-Brain loader (T35)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_load = sub.add_parser("load-seed", help="insert seed rules into wisdom_base")
    p_load.add_argument("--path", default=str(DEFAULT_SEED))
    p_load.add_argument("--dry-run", action="store_true")

    sub.add_parser("list-books", help="show books in seed file")
    sub.add_parser("stats", help="active book-sourced lesson counts")

    args = ap.parse_args(argv)

    if args.cmd == "load-seed":
        res = load_seed(args.path, dry_run=args.dry_run)
        prefix = "[DRY-RUN] " if res["dry_run"] else ""
        print(f"{prefix}📚 Books: {res['books']}  Rules: {res['rules']}")
        print(f"{prefix}✅ Inserted: {res['inserted']}  ⏭  Skipped (dup/empty): {res['skipped']}")
        return 0

    if args.cmd == "list-books":
        for b in list_books(DEFAULT_SEED):
            print(f"  • [{b['slug']:10}] {b['title']:42} — {b['author']} ({b['year']})  · {b['rules']} rules")
        return 0

    if args.cmd == "stats":
        s = book_stats()
        if not s:
            print("(no book-sourced lessons loaded yet — run `load-seed`)")
            return 0
        total = sum(s.values())
        for slug, n in sorted(s.items(), key=lambda x: -x[1]):
            print(f"  {slug:12} {n:3} active lessons")
        print(f"  {'TOTAL':12} {total:3}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
