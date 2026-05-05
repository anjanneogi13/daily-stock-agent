"""Smoke-import every script in scripts/ — catches missing functions, bad refactors.

This test would have caught:
  - 2026-05-04: scripts/evaluate_picks.py importing nonexistent format_paused_summary
  - Any future rename/move that breaks a script's imports
"""
import importlib
import sys
from pathlib import Path
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

def _all_script_modules():
    if not SCRIPTS_DIR.exists():
        return []
    out = []
    for p in sorted(SCRIPTS_DIR.glob("*.py")):
        if p.name.startswith("_"):
            continue
        out.append(f"scripts.{p.stem}")
    return out

@pytest.mark.parametrize("modname", _all_script_modules())
def test_script_imports_cleanly(modname):
    """Each script must be importable without ImportError/NameError."""
    # Add repo root to sys.path so imports work
    repo_root = str(SCRIPTS_DIR.parent)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    try:
        # Use spec_from_file_location to import without executing __main__ body
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            modname, SCRIPTS_DIR / f"{modname.split('.')[-1]}.py"
        )
        mod = importlib.util.module_from_spec(spec)
        # Set __name__ to non-__main__ so top-level guards skip
        mod.__name__ = modname
        spec.loader.exec_module(mod)
    except (ImportError, AttributeError, NameError) as e:
        pytest.fail(f"{modname} failed to import: {type(e).__name__}: {e}")
    except SystemExit:
        # Some scripts call sys.exit at import — acceptable
        pass
