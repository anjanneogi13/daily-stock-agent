"""F1: daily_wisdom must be surfaced in Telegram message build."""
from pathlib import Path


def test_send_telegram_imports_daily_wisdom():
    """Locks the wiring — no silent revert to dead-code state."""
    src = Path("scripts/send_telegram.py").read_text()
    assert "from src.daily_wisdom import generate_daily_wisdom" in src


def test_send_telegram_calls_generate_daily_wisdom():
    src = Path("scripts/send_telegram.py").read_text()
    assert "generate_daily_wisdom()" in src


def test_wisdom_call_is_inside_try_except():
    """Wisdom is observability; must never crash the daily message."""
    src = Path("scripts/send_telegram.py").read_text()
    lines = src.splitlines()
    call_lines = [i for i, l in enumerate(lines)
                  if "generate_daily_wisdom" in l and "import" not in l]
    assert call_lines, "no call site found"
    for ci in call_lines:
        before = "\n".join(lines[max(0, ci - 10):ci])
        assert "try:" in before, (
            f"call at line {ci+1} not wrapped in try (would crash daily msg)"
        )


def test_wisdom_appears_before_disclaimer():
    """Wisdom should appear before the 'Educational only' disclaimer."""
    src = Path("scripts/send_telegram.py").read_text()
    # Find the CALL site (not import)
    lines = src.splitlines()
    call_line = next(
        (i for i, l in enumerate(lines)
         if "generate_daily_wisdom()" in l), -1
    )
    disc_line = next(
        (i for i, l in enumerate(lines)
         if "Educational only" in l), -1
    )
    assert call_line > 0 and disc_line > 0
    assert call_line < disc_line, "wisdom must come BEFORE disclaimer"


def test_wisdom_call_followed_by_except():
    """Source-level guard: an `except` follows the call within 30 lines.

    Equivalent to ensuring the call is inside try/except — but checks
    the FORWARD direction (try precedes call already proven above).
    """
    src = Path("scripts/send_telegram.py").read_text()
    lines = src.splitlines()
    call_idx = next(
        (i for i, l in enumerate(lines)
         if "generate_daily_wisdom()" in l), -1
    )
    assert call_idx > 0, "call site not found"
    after = lines[call_idx:call_idx + 30]
    assert any("except" in l for l in after), (
        "no `except` within 30 lines after wisdom call"
    )
