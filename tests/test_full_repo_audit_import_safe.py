"""Bug #18 (2026-05-05): full_repo_audit must be import-safe.

scripts/full_repo_audit.py used to execute the entire audit at import time.
That made tests/test_scripts_import.py spend ~180s importing it because the
script launched a nested full pytest run.

Contract:
  - The script exposes main().
  - The expensive audit body is guarded by if __name__ == "__main__".
  - Importing the module does not print audit sections.
"""
import importlib
import io
import contextlib


def test_full_repo_audit_import_is_side_effect_free():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod = importlib.import_module("scripts.full_repo_audit")

    assert hasattr(mod, "main")
    assert "REPO META" not in buf.getvalue()
    assert "AUDIT COMPLETE" not in buf.getvalue()
