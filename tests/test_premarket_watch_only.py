from pathlib import Path


def test_premarket_unverified_price_is_watch_only_not_half_size():
    text = Path("scripts/premarket_check.py").read_text()

    assert '"👀 WATCH ONLY", "could not verify fresh price' in text
    assert '"⚠️ HALF SIZE", "could not verify price"' not in text
    assert '"actionable": tag not in ("👀 WATCH ONLY", "🚫 SKIP TODAY")' in text
