"""E5-A: backfill_regime must be idempotent and use 4-state logic."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.backfill_regime import _classify


def test_classify_bull():
    # SPY 7.5% above 200d SMA
    assert _classify(spy_close=107.5, sma200=100.0) == "bull"


def test_classify_transition():
    assert _classify(spy_close=102.0, sma200=100.0) == "transition"


def test_classify_chop():
    assert _classify(spy_close=98.0, sma200=100.0) == "chop"


def test_classify_bear():
    assert _classify(spy_close=92.0, sma200=100.0) == "bear"


def test_classify_unknown_on_missing_data():
    assert _classify(spy_close=None, sma200=100) == "unknown"
    assert _classify(spy_close=100, sma200=None) == "unknown"
    assert _classify(spy_close=0, sma200=100) == "unknown"


def test_classify_at_boundaries():
    """Boundary values: 5% → bull, 0% → transition, -5% → chop."""
    assert _classify(105.0, 100.0) == "bull"          # exactly +5%
    assert _classify(100.0, 100.0) == "transition"    # exactly 0%
    assert _classify(95.0, 100.0) == "chop"           # exactly -5%
