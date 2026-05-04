"""Find src/ modules NEVER imported by main.py, scripts/, or other live src/ modules.

Found dead modules = potential silent features (the smell faculty
pattern from E4: code exists, no caller, never runs).

Audit fix (May 4 2026): regex now catches THREE import shapes:
  1. from src.X import ...
  2. import src.X
  3. from src import X       ← original audit MISSED this, gave false positives

Usage:
    python scripts/audit_dead_code.py          # report
    python scripts/audit_dead_code.py --strict # exit 1 if any dead found
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
ENTRY = ROOT / "main.py"
SCRIPTS = ROOT / "scripts"


def _imports_from(text: str) -> set[str]:
    """Return set of src/<modname> imported by `text`. Catches all 3 shapes."""
    deps = set()
    # Shape 1: `from src.X import ...`        OR     `from .X import ...`
    for m in re.finditer(r"from\s+src\.(\w+)|from\s+\.(\w+)\s+import", text):
        d = m.group(1) or m.group(2)
        if d: deps.add(d)
    # Shape 2: `import src.X` (possibly aliased)
    for m in re.finditer(r"import\s+src\.(\w+)", text):
        deps.add(m.group(1))
    # Shape 3: `from src import X[, Y, ...]`  ← was missed in v1 audit
    for m in re.finditer(r"from\s+src\s+import\s+([\w\s,]+)", text):
        for name in m.group(1).split(","):
            n = name.strip().split(" as ")[0].strip()
            if n and n.isidentifier():
                deps.add(n)
    return deps


def find_dead() -> dict:
    all_modules = {f.stem for f in SRC.glob("*.py") if f.stem != "__init__"}

    imports_by_mod = {}
    for f in SRC.glob("*.py"):
        if f.stem == "__init__":
            continue
        imports_by_mod[f.stem] = _imports_from(f.read_text())

    seeds = set()
    if ENTRY.exists():
        seeds |= _imports_from(ENTRY.read_text())
    for f in SCRIPTS.glob("*.py"):
        seeds |= _imports_from(f.read_text())
    # app.py too (may be alive Streamlit dashboard)
    app = ROOT / "app.py"
    if app.exists():
        seeds |= _imports_from(app.read_text())

    reached = set()
    queue = [s for s in seeds if s in all_modules]
    while queue:
        n = queue.pop()
        if n in reached:
            continue
        reached.add(n)
        for d in imports_by_mod.get(n, set()):
            if d in all_modules and d not in reached:
                queue.append(d)

    dead = sorted(all_modules - reached)
    return {"all": all_modules, "reached": reached, "dead": dead, "seeds": seeds}


def main(argv=None):
    argv = argv or sys.argv[1:]
    strict = "--strict" in argv

    r = find_dead()
    print(f"  Total src/ modules:  {len(r['all'])}")
    print(f"  Reached (live):      {len(r['reached'])}")
    print(f"  Dead (suspects):     {len(r['dead'])}")
    print()

    if not r["dead"]:
        print("  ✅ No dead modules found.")
        return 0

    print("─── DEAD MODULE CANDIDATES ───")
    for d in r["dead"]:
        f = SRC / f"{d}.py"
        loc = sum(1 for _ in f.read_text().splitlines())
        # Test coverage (informational; tests don\'t count as live)
        tested = any(
            f"src.{d}" in tf.read_text() or f"src import {d}" in tf.read_text()
            for tf in (ROOT / "tests").glob("test_*.py")
            if tf.exists()
        )
        tag = "  (tested)" if tested else "  ⚠ NO TESTS"
        print(f"    {d:30}  {loc:>4} lines{tag}")

    return 1 if strict and r["dead"] else 0


if __name__ == "__main__":
    sys.exit(main())
