"""full_repo_audit docs drift classification should avoid noisy false positives."""

from pathlib import Path

from scripts.full_repo_audit import classify_docs_drift


def test_scripts_and_root_python_refs_are_not_ghosts(tmp_path):
    doc = tmp_path / "ARCHITECTURE.md"
    doc.write_text(
        "`scripts/backup_data.py`\n"
        "`evaluate_picks.py`\n"
        "`src/real_module.py`\n"
    )

    scripts_file = tmp_path / "backup_data.py"
    root_file = tmp_path / "evaluate_picks.py"
    src_file = tmp_path / "real_module.py"
    for path in [scripts_file, root_file, src_file]:
        path.write_text("# exists\n")

    drift = classify_docs_drift(
        doc_paths=[doc],
        python_paths=[scripts_file, root_file, src_file],
        src_paths=[src_file],
    )

    assert drift["missing_refs"] == []
    assert drift["planned_missing"] == []


def test_not_yet_built_refs_are_classified_as_planned(tmp_path):
    doc = tmp_path / "ARCHITECTURE.md"
    doc.write_text("| Future | `curiosity_engine.py` | NOT YET BUILT |\n")

    drift = classify_docs_drift(
        doc_paths=[doc],
        python_paths=[],
        src_paths=[],
    )

    assert drift["missing_refs"] == []
    assert drift["planned_missing"] == ["curiosity_engine"]


def test_real_missing_refs_remain_broken_drift(tmp_path):
    doc = tmp_path / "ARCHITECTURE.md"
    doc.write_text("Runtime file: `missing_runtime.py`\n")

    drift = classify_docs_drift(
        doc_paths=[doc],
        python_paths=[],
        src_paths=[],
    )

    assert drift["missing_refs"] == ["missing_runtime"]
    assert drift["planned_missing"] == []


def test_architecture_no_longer_mentions_watchlist_py():
    text = Path("docs/ARCHITECTURE.md").read_text(errors="ignore")
    assert "`watchlist.py`" not in text
    assert "`watchlist_manager.py`" in text
    assert "`data/watchlist.json`" in text
