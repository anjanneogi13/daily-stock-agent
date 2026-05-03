"""
Run hypothesis review — analyze closed picks in signal journal.
Usage: python scripts/run_hypothesis_review.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.signal_journal import load_closed
from src.hypothesis_engine import analyze, format_report


def main():
    closed = load_closed()
    result = analyze(closed)
    print(format_report(result))


if __name__ == "__main__":
    main()
