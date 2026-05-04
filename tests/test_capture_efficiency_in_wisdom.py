"""F2: capture_efficiency surfaces in daily wisdom output."""
from pathlib import Path


def test_daily_wisdom_imports_exit_metrics():
    src = Path("src/daily_wisdom.py").read_text()
    assert "from src.exit_metrics import capture_efficiency" in src


def test_daily_wisdom_calls_capture_efficiency():
    src = Path("src/daily_wisdom.py").read_text()
    assert "capture_efficiency(" in src


def test_capture_efficiency_call_is_guarded():
    """Must be try/except — never crash daily message on exit_metrics fail."""
    src = Path("src/daily_wisdom.py").read_text()
    lines = src.splitlines()
    call_lines = [i for i, l in enumerate(lines)
                  if "capture_efficiency(" in l and "import" not in l]
    assert call_lines
    for ci in call_lines:
        before = "\n".join(lines[max(0, ci - 12):ci])
        assert "try:" in before, f"call at line {ci+1} not in try/except"


def test_wisdom_still_produces_output():
    """Smoke: must not crash, must include header."""
    from src.daily_wisdom import generate_daily_wisdom
    out = generate_daily_wisdom()
    assert isinstance(out, str)
    assert "DAILY WISDOM" in out
