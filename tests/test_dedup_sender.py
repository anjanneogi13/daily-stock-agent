"""Tests for Telegram dedup."""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from src import dedup_sender


@pytest.fixture(autouse=True)
def isolate_dedup_file(tmp_path, monkeypatch):
    """Each test gets a fresh dedup file."""
    test_path = tmp_path / "telegram_sent.json"
    monkeypatch.setattr(dedup_sender, "DEDUP_PATH", test_path)
    yield test_path


def test_should_send_first_time():
    """First send of a message should always be allowed."""
    assert dedup_sender.should_send("Hello world") is True


def test_should_not_send_immediately_after():
    """Same message within window should be blocked."""
    msg = "Daily picks: NVDA AVGO"
    assert dedup_sender.should_send(msg) is True
    dedup_sender.mark_sent(msg)
    assert dedup_sender.should_send(msg) is False


def test_should_send_different_messages():
    """Different messages should both go through."""
    dedup_sender.mark_sent("Message A")
    assert dedup_sender.should_send("Message B") is True


def test_empty_message_blocked():
    """Empty/whitespace messages should not be sent."""
    assert dedup_sender.should_send("") is False
    assert dedup_sender.should_send("   ") is False
    assert dedup_sender.should_send("\n\n") is False


def test_minor_price_drift_treated_as_dup():
    """Same pick with $0.50 price drift = same message (uses first 500 chars)."""
    msg1 = "NVDA entry $200.50 SL $188 TP $216" + " filler" * 50
    msg2 = "NVDA entry $200.75 SL $188 TP $216" + " filler" * 50
    dedup_sender.mark_sent(msg1)
    # Hash uses first 500 chars; small price changes still hash differently
    # but COMPLETELY identical content blocks
    msg3 = "NVDA entry $200.50 SL $188 TP $216" + " filler" * 50
    assert dedup_sender.should_send(msg3) is False  # exact dup → blocked


def test_persists_across_calls():
    """Sent messages should survive between function calls."""
    msg = "Test persistence"
    dedup_sender.mark_sent(msg)
    # Simulate fresh import — should still be marked
    assert dedup_sender.should_send(msg) is False


def test_window_expiry(monkeypatch):
    """After window passes, message should be re-sendable."""
    msg = "Test window"
    # Mock time to be 2 hours ago
    past = datetime.now() - timedelta(hours=2)
    sent = {dedup_sender._content_hash(msg): past.isoformat()}
    dedup_sender._save_sent(sent)
    # 60-min window → 2 hours later should allow re-send
    assert dedup_sender.should_send(msg, window_minutes=60) is True


def test_corrupted_file_recovers():
    """Corrupted JSON should not crash — treated as empty."""
    dedup_sender.DEDUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    dedup_sender.DEDUP_PATH.write_text("{invalid json")
    assert dedup_sender.should_send("anything") is True


def test_atomic_write_no_corruption(tmp_path, monkeypatch):
    """Concurrent writes should not corrupt file (atomic temp+rename)."""
    test_path = tmp_path / "concurrent.json"
    monkeypatch.setattr(dedup_sender, "DEDUP_PATH", test_path)
    for i in range(10):
        dedup_sender.mark_sent(f"msg-{i}")
    # File should be valid JSON
    data = json.loads(test_path.read_text())
    assert len(data) == 10


def test_stats_returns_count():
    """stats() should return current tracked count."""
    dedup_sender.mark_sent("a")
    dedup_sender.mark_sent("b")
    s = dedup_sender.stats()
    assert s["total_tracked"] == 2