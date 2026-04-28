"""Display performance dashboard."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.performance_stats import print_dashboard
print_dashboard()
