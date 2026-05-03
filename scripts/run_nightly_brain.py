"""T50 CLI — run the nightly brain maintenance conductor.

Used by .github/workflows/nightly_brain.yml at 23:00 UTC.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nightly_conductor import run_nightly, format_summary_text


def main():
    print("🧠 Starting nightly brain maintenance...")
    summary = run_nightly()
    print(format_summary_text(summary))
    # Always exit 0 — failures are logged in journal, don't break workflow
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
