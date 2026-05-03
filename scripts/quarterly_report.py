"""
Generate a quarterly performance report.
Usage:
  python scripts/quarterly_report.py [--days N]
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.quarterly_report import generate_report


def main():
    days = 90
    if "--days" in sys.argv:
        i = sys.argv.index("--days")
        try:
            days = int(sys.argv[i + 1])
        except (IndexError, ValueError):
            pass
    out = generate_report(days=days)
    print(f"✅ Report saved: {out}")
    print(f"   Size: {out.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
