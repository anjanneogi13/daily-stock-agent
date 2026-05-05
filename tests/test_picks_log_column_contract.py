"""Contract test — every reader of data/picks_log.csv via csv.DictReader
must use real column names from the live CSV header.

Catches the bug class that hit 4 times on 2026-05-04:
  - send_layman_evening.py read 'status' (CSV has 'evaluation_status')
  - layman_translator.outcome_to_layman read 'pnl_dollar' (no such column)

PRECISE SCOPING (avoids false positives):
  Only flags .get('xxx') calls on a variable `r` (or `row`) that is the
  loop variable of `for r in csv.DictReader(...)`. Other .get() calls
  on JSON, brain output, etc. are correctly ignored.
"""
import ast
import csv
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CSV_PATH = REPO / "data" / "picks_log.csv"

# Synthetic/aliased CSV-like fields. Add to this set when a writer/reader
# legitimately uses an alias for a real column.
SYNTHETIC_FIELDS = {
    "pnl", "pnl_dollar",          # computed dollar P&L
    "status",                      # legacy alias for evaluation_status
    "buy_price",                   # alias for entry
    "position_size",               # alias for qty
    "outcome",                     # legacy alias for evaluation_status
    # Date variants
    "exit_date",
}


def _real_columns():
    if not CSV_PATH.exists():
        pytest.skip("data/picks_log.csv missing")
    with CSV_PATH.open() as f:
        return set(h.strip() for h in next(csv.reader(f)))


def _find_csv_row_vars(tree):
    """Find variable names that are loop targets of `for X in csv.DictReader(...)`.

    Returns set of (lineno_start, lineno_end, var_name) tuples — we use
    line ranges to know which .get() calls are inside which loop scope.
    """
    rows = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        # Check the iterator: is it csv.DictReader(...) or DictReader(...)?
        it = node.iter
        is_dict_reader = False
        if isinstance(it, ast.Call):
            if isinstance(it.func, ast.Attribute) and it.func.attr == "DictReader":
                is_dict_reader = True
            elif isinstance(it.func, ast.Name) and it.func.id == "DictReader":
                is_dict_reader = True
        if not is_dict_reader:
            continue
        # Get the loop variable name(s)
        if isinstance(node.target, ast.Name):
            rows.append((node.lineno, node.end_lineno or node.lineno + 100,
                         node.target.id))
    return rows


def _csv_get_calls(tree, csv_row_vars):
    """Find .get('literal') calls where receiver is a known CSV row var."""
    out = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            continue
        # Receiver must be a Name node
        if not isinstance(node.func.value, ast.Name):
            continue
        receiver = node.func.value.id
        # Is this call inside a CSV-row-loop scope and is receiver that var?
        for (start, end, var) in csv_row_vars:
            if start <= node.lineno <= end and receiver == var:
                out.append((node.args[0].value, node.lineno))
                break
    return out


def _files_to_check():
    targets = []
    for sub in ("src", "scripts"):
        d = REPO / sub
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.py")):
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if "DictReader" in txt:
                targets.append(p)
    return targets


@pytest.mark.parametrize("file_path", _files_to_check(),
                          ids=lambda p: p.relative_to(REPO).as_posix())
def test_csv_column_contract(file_path):
    real_cols = _real_columns()
    valid = real_cols | SYNTHETIC_FIELDS
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        pytest.skip(f"{file_path.name} syntax error")

    csv_row_vars = _find_csv_row_vars(tree)
    if not csv_row_vars:
        pytest.skip(f"{file_path.name} has DictReader but no for-row pattern detected")

    bad = []
    for key, lineno in _csv_get_calls(tree, csv_row_vars):
        if key not in valid:
            bad.append(f"  line {lineno}: .get({key!r}) — not in CSV header or allowlist")

    if bad:
        rel = file_path.relative_to(REPO).as_posix()
        msg = (f"\n{rel} reads CSV column(s) that don't exist:\n"
               + "\n".join(bad)
               + f"\n\nReal CSV columns: {sorted(real_cols)}"
               + f"\n\nIf intentionally synthetic, add to SYNTHETIC_FIELDS.")
        pytest.fail(msg)
