"""F6 (May 4 2026): Lock workflow persistence invariants.

THE BUG (caught by F6 audit)
news_engine.yml ran every 30 min, computed news_signals.json,
but workflow\'s git add line omitted that file. Result: signals
were silently thrown away after each run. Every pick for 48+
hours got news_boost=0 from a stale May 2 snapshot.

THIS TEST locks the invariant: every data file the news engine
WRITES must be in the git add list. Future regressions break CI.
"""
import re
from pathlib import Path

WORKFLOW = Path(".github/workflows/news_engine.yml")


def _git_add_files() -> set[str]:
    """Extract paths from `git add -f <file1> <file2> ...` lines."""
    text = WORKFLOW.read_text()
    files = set()
    for m in re.finditer(r"git\s+add\s+(?:-\w+\s+)?(.+?)(?:2>|\n|$)", text):
        for tok in m.group(1).split():
            if tok.startswith("data/") or tok.startswith("config/"):
                files.add(tok)
    return files


def test_news_signals_json_in_workflow_git_add():
    """REGRESSION: news_signals.json was missing for 2 days → silent boost=0."""
    files = _git_add_files()
    assert "data/news_signals.json" in files, (
        "data/news_signals.json must be committed by news_engine workflow — "
        "otherwise computed signals are thrown away every run.\n"
        f"Currently committed: {sorted(files)}"
    )


def test_news_log_jsonl_in_workflow_git_add():
    """Lock-in: news_log.jsonl is the historical record."""
    files = _git_add_files()
    assert "data/news_log.jsonl" in files


def test_news_seen_json_in_workflow_git_add():
    """Lock-in: news_seen.json prevents duplicate Claude API calls."""
    files = _git_add_files()
    assert "data/news_seen.json" in files


def test_watchlist_json_in_workflow_git_add():
    """Lock-in: watchlist.json drives morning pick scoring."""
    files = _git_add_files()
    assert "data/watchlist.json" in files


def test_news_signals_json_writer_exists():
    """The fix only matters if news_signals.py actually writes the file."""
    src = Path("src/news_signals.py").read_text()
    assert "SIGNALS_PATH" in src
    assert ".write_text" in src or ".write(" in src or "json.dump" in src or "tmp.replace" in src
