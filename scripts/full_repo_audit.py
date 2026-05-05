"""Full repo audit — produces structured text for REPO_HEALTH.md generation.

Run: python scripts/full_repo_audit.py > /tmp/audit.txt 2>&1
Then paste /tmp/audit.txt contents back into Claude chat.
"""
from __future__ import annotations
import ast
import csv
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

def section(title):
    print()
    print("═" * 72)
    print(f"  {title}")
    print("═" * 72)

def sh(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return f"<error: {e}>"


def recent_regime_counts(path="data/picks_log.csv", limit=10) -> dict:
    """Count regimes in recent picks using real CSV parsing.

    Shell parsing with awk -F, breaks when company names contain quoted commas,
    e.g. "Agilent Technologies, Inc.", which shifts field numbers.
    """
    try:
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        return {}

    out = defaultdict(int)
    for row in rows[-limit:]:
        regime = (row.get("regime") or "EMPTY").strip() or "EMPTY"
        out[regime] += 1
    return dict(sorted(out.items()))


def format_regime_counts(counts: dict) -> str:
    if not counts:
        return "no picks_log rows"
    return "\n".join(f"{count:6d} {regime}" for regime, count in counts.items())



def documented_python_refs(doc_paths) -> tuple[set[str], set[str]]:
    """Return documented Python module/file references and planned references.

    planned_refs are docs lines explicitly marked NOT YET BUILT, so they should
    not be treated as broken drift.
    """
    refs = set()
    planned_refs = set()
    for doc in doc_paths:
        try:
            lines = doc.read_text(errors="ignore").splitlines()
        except FileNotFoundError:
            continue
        for line in lines:
            line_refs = set()
            for match in re.finditer(r"`?(?:(?:src|scripts)/)?(\w+)\.py`?", line):
                name = match.group(1)
                line_refs.add(name)
                refs.add(name)
            if "NOT YET BUILT" in line.upper():
                planned_refs.update(line_refs)
    return refs, planned_refs


def repo_python_stems(paths=None) -> set[str]:
    """Return Python file stems that actually exist in root/src/scripts."""
    if paths is None:
        paths = (
            list(ROOT.glob("*.py"))
            + list((ROOT / "src").glob("*.py"))
            + list((ROOT / "scripts").glob("*.py"))
        )
    return {Path(path).stem for path in paths if Path(path).stem != "__init__"}


def classify_docs_drift(doc_paths=None, python_paths=None, src_paths=None) -> dict:
    """Classify docs/code drift without treating scripts/root files as src ghosts."""
    if doc_paths is None:
        doc_paths = list((ROOT / "docs").glob("ARCHITECTURE*.md")) + list(
            (ROOT / "docs").glob("CONTEXT*.md")
        )
    if src_paths is None:
        src_paths = list((ROOT / "src").glob("*.py"))

    refs, planned_refs = documented_python_refs(doc_paths)
    real_py = repo_python_stems(python_paths)
    src_names = {Path(path).stem for path in src_paths if Path(path).stem != "__init__"}

    missing_refs = sorted(
        name for name in refs
        if name not in real_py and name not in planned_refs and name not in {"main", "app", "__init__"}
    )
    planned_missing = sorted(name for name in planned_refs if name not in real_py)
    existing_refs = sorted(name for name in refs if name in real_py)
    src_not_explicitly_documented = sorted(src_names - refs)

    return {
        "existing_refs": existing_refs,
        "missing_refs": missing_refs,
        "planned_missing": planned_missing,
        "src_not_explicitly_documented": src_not_explicitly_documented,
    }


def main() -> int:
    # ════════════════════════════════════════════════════════════════
    section("1. REPO META")
    # ════════════════════════════════════════════════════════════════
    print(f"  generated_at:  {datetime.now().isoformat()}")
    print(f"  cwd:           {ROOT}")
    print(f"  current_branch: {sh('git rev-parse --abbrev-ref HEAD').strip()}")
    print(f"  head_commit:   {sh('git log -1 --oneline').strip()}")
    print(f"  total_commits: {sh('git rev-list --count HEAD').strip()}")
    print(f"  remote:        {sh('git remote -v | head -1').strip()}")

    # ════════════════════════════════════════════════════════════════
    section("2. FILE INVENTORY")
    # ════════════════════════════════════════════════════════════════
    def count(pattern):
        return len(list(ROOT.glob(pattern)))

    print(f"  src/*.py:                {count('src/*.py')}")
    print(f"  scripts/*.py:            {count('scripts/*.py')}")
    print(f"  tests/*.py:              {count('tests/test_*.py')}")
    print(f"  .github/workflows/*.yml: {count('.github/workflows/*.yml')}")
    print(f"  docs/*.md:               {count('docs/*.md')}")
    print(f"  data/* (top-level):      {len([p for p in (ROOT/'data').glob('*') if p.is_file()])}")
    print(f"  TOTAL python lines:      {sh("find src scripts tests -name '*.py' -exec cat {} + 2>/dev/null | wc -l").strip()}")

    # ════════════════════════════════════════════════════════════════
    section("3. SRC MODULE MAP — imports + lines + test coverage")
    # ════════════════════════════════════════════════════════════════
    src_files = sorted((ROOT / "src").glob("*.py"))
    test_files = list((ROOT / "tests").glob("test_*.py"))
    test_blob = "\n".join(f.read_text(errors='ignore') for f in test_files)

    # Build import graph
    imports_into = defaultdict(set)  # module -> set of importers
    for py in [ROOT/"main.py", ROOT/"app.py"] + list((ROOT/"src").glob("*.py")) + list((ROOT/"scripts").glob("*.py")):
        if not py.exists(): continue
        try:
            text = py.read_text(errors='ignore')
            for m in re.finditer(r'from\s+(?:src\.|\.)?(\w+)\s+import|from\s+src\s+import\s+([\w,\s]+)|import\s+src\.(\w+)', text):
                for g in m.groups():
                    if not g: continue
                    for tok in g.split(","):
                        tok = tok.strip().split(" as ")[0].strip()
                        if tok: imports_into[tok].add(py.relative_to(ROOT).as_posix())
        except: pass

    print(f"  {'MODULE':28} {'LINES':>6}  {'IMPORTERS':>9}  TESTED")
    for f in src_files:
        name = f.stem
        if name == "__init__": continue
        lines = sum(1 for _ in f.open(errors='ignore'))
        importers = len(imports_into.get(name, set()))
        tested = "✅" if name in test_blob else "❌"
        flag = " 🚨DEAD" if importers == 0 and name not in ("__init__",) else ""
        print(f"  {name:28} {lines:>6}  {importers:>9}  {tested}{flag}")

    # ════════════════════════════════════════════════════════════════
    section("4. WORKFLOWS — schedule + what they commit")
    # ════════════════════════════════════════════════════════════════
    for wf in sorted((ROOT/".github/workflows").glob("*.yml")):
        txt = wf.read_text(errors='ignore')
        crons = re.findall(r"cron:\s*['\"]([^'\"]+)['\"]", txt)
        git_adds = re.findall(r"git\s+add\s+(?:-\w+\s+)?([^\n|&;]+)", txt)
        name_m = re.search(r"^name:\s*(.+)$", txt, re.M)
        print(f"\n  📋 {wf.name}  ({name_m.group(1) if name_m else '?'})")
        print(f"     schedule: {crons or 'manual only'}")
        if git_adds:
            for ga in git_adds[:3]:
                files = [t for t in ga.split() if t.startswith(('data/','config/','docs/'))]
                if files:
                    print(f"     commits: {' '.join(files)}")

    # ════════════════════════════════════════════════════════════════
    section("5. DATA FILES — size + age + git activity")
    # ════════════════════════════════════════════════════════════════
    for f in sorted((ROOT/"data").glob("*")):
        if not f.is_file(): continue
        if f.suffix not in ('.csv','.json','.jsonl','.parquet'): continue
        size_kb = f.stat().st_size // 1024
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        commits = sh(f'git log --oneline -- {f} 2>/dev/null | wc -l').strip()
        last_git = sh(f'git log -1 --format="%ar" -- {f} 2>/dev/null').strip() or "never"
        flag = ""
        age_days = (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).days
        if age_days > 5: flag = " 🟡STALE"
        print(f"  {f.name:32} {size_kb:>6}KB  mtime={mtime}  commits={commits:>4}  last_git={last_git}{flag}")

    # ════════════════════════════════════════════════════════════════
    section("6. TEST SUITE")
    # ════════════════════════════════════════════════════════════════
    out = sh("python -m pytest tests/ -q --tb=no 2>&1 | tail -5", timeout=180)
    print(out)

    # ════════════════════════════════════════════════════════════════
    section("7. AUDIT DASHBOARDS")
    # ════════════════════════════════════════════════════════════════
    print("\n--- DEAD CODE ---")
    print(sh("python scripts/audit_dead_code.py 2>&1 | head -25"))
    print("\n--- JOURNAL CONSISTENCY ---")
    print(sh("python scripts/audit_journal_consistency.py 2>&1 | head -10"))
    print("\n--- ENFORCEMENT READINESS ---")
    print(sh("python scripts/check_enforcement_readiness.py 2>&1 | head -25"))
    print("\n--- MONITORING READINESS ---")
    print(sh("python scripts/monitoring_readiness.py 2>&1 | head -35"))
    print("\n--- EARNINGS FILL-RATE ---")
    print(sh("python scripts/audit_earnings_fill_rate.py 2>&1 | head -30"))
    print("\n--- SECTOR BENCHMARK FILL-RATE ---")
    print(sh("python scripts/audit_sector_fill_rate.py 2>&1 | head -35"))

    # ════════════════════════════════════════════════════════════════
    section("8. KNOWN PENDING ISSUES (from session notes)")
    # ════════════════════════════════════════════════════════════════
    issues = [
        ("report issue upsert helper wired?",
         "grep -R 'upsert_issue.js' .github/workflows/*.yml | wc -l"),
        ("monitoring readiness dashboard present?",
         "test -f scripts/monitoring_readiness.py && echo 'present' || echo 'MISSING'"),
        ("agent_memoir reads learning_journal?",
         "grep -n 'learning_journal' src/agent_memoir.py 2>/dev/null | head -3 || echo 'NO REFERENCE'"),
        ("regime counts in recent picks",
         None),
        ("tracker.py legacy module exists?",
         "ls -la src/tracker.py 2>/dev/null || echo 'absent'"),
    ]
    for label, cmd in issues:
        print(f"\n  🔍 {label}")
        if cmd is None and label == "regime counts in recent picks":
            print("     " + format_regime_counts(recent_regime_counts()).replace("\n", "\n     "))
        else:
            print("     " + sh(cmd).replace("\n", "\n     ").strip())

    # ════════════════════════════════════════════════════════════════
    section("9. PICKS_LOG STATE")
    # ════════════════════════════════════════════════════════════════
    try:
        rows = list(csv.DictReader(open("data/picks_log.csv")))
        print(f"  total rows: {len(rows)}")
        statuses = defaultdict(int)
        for r in rows: statuses[r.get("evaluation_status","?")] += 1
        print(f"  status breakdown: {dict(statuses)}")
        dates = sorted(set(r.get("pick_date") for r in rows if r.get("pick_date")))
        print(f"  date range: {dates[0]} → {dates[-1]} ({len(dates)} unique days)")
        floor = "2026-05-02"
        post_floor_closed = [r for r in rows if r.get("pick_date","") >= floor and r.get("evaluation_status") in ("tp_hit","sl_hit","expired")]
        print(f"  post-floor ({floor}) closed: {len(post_floor_closed)}")
    except Exception as e:
        print(f"  error: {e}")

    # ════════════════════════════════════════════════════════════════
    section("10. RECENT COMMITS (last 30)")
    # ════════════════════════════════════════════════════════════════
    print(sh("git log --oneline -30"))

    # ════════════════════════════════════════════════════════════════
    section("11. DOCS INVENTORY")
    # ════════════════════════════════════════════════════════════════
    for d in sorted((ROOT/"docs").glob("*.md")):
        lines = sum(1 for _ in d.open(errors='ignore'))
        mtime = datetime.fromtimestamp(d.stat().st_mtime).strftime("%Y-%m-%d")
        print(f"  {d.name:42} {lines:>5} lines  modified={mtime}")

    # ════════════════════════════════════════════════════════════════
    section("12. POTENTIAL DRIFT — modules in docs but not in code")
    # ════════════════════════════════════════════════════════════════
    drift = classify_docs_drift()

    if drift["missing_refs"]:
        print("  📛 documented Python refs with no matching root/src/scripts file:")
        for g in drift["missing_refs"][:20]:
            print(f"     - {g}")
    else:
        print("  ✅ no broken Python file references")

    if drift["planned_missing"]:
        print("\n  📝 planned/future Python refs explicitly marked NOT YET BUILT:")
        for g in drift["planned_missing"][:20]:
            print(f"     - {g}")

    undocumented = drift["src_not_explicitly_documented"]
    if undocumented:
        print(
            f"\n  ℹ️ src modules not explicitly documented by filename "
            f"({len(undocumented)} total; informational sample):"
        )
        for o in undocumented[:15]:
            print(f"     - {o}")
    else:
        print("\n  ✅ every src module is explicitly documented by filename")

    print()
    print("═" * 72)
    print("  ✅ AUDIT COMPLETE — copy everything above and paste into Claude chat")
    print("═" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
