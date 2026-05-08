import json
from pathlib import Path


def test_late_ideas_telegram_dedupes_after_success(tmp_path, monkeypatch):
    import scripts.send_late_daily_ideas_telegram as sender

    data_dir = tmp_path
    msg_path = sender.late_ideas_message_path("2026-05-07", data_dir=data_dir)
    msg_path.write_text("late ideas message", encoding="utf-8")

    monkeypatch.setattr(sender, "today_et", lambda: "2026-05-07")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat1")
    monkeypatch.delenv("TELEGRAM_GROUP_CHAT_ID", raising=False)

    calls = []

    class FakeResp:
        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(req, timeout=10):
        calls.append(req)
        return FakeResp()

    monkeypatch.setattr(sender.urllib.request, "urlopen", fake_urlopen)

    assert sender.main([], data_dir=data_dir) == 0
    assert len(calls) == 1

    ledger = sender.late_ideas_sent_path("2026-05-07", data_dir=data_dir)
    payload = json.loads(ledger.read_text())
    assert payload["date"] == "2026-05-07"
    assert payload["sent_count"] == 1
    assert payload["mode"] == "monitoring_only"
    assert payload["paper_trading_enabled"] is False
    assert payload["live_trading_enabled"] is False

    assert sender.main([], data_dir=data_dir) == 0
    assert len(calls) == 1


def test_late_ideas_telegram_force_resends(tmp_path, monkeypatch):
    import scripts.send_late_daily_ideas_telegram as sender

    data_dir = tmp_path
    sender.late_ideas_message_path("2026-05-07", data_dir=data_dir).write_text(
        "late ideas message",
        encoding="utf-8",
    )
    sender.late_ideas_sent_path("2026-05-07", data_dir=data_dir).write_text(
        json.dumps({"date": "2026-05-07", "sent_count": 1}),
        encoding="utf-8",
    )

    monkeypatch.setattr(sender, "today_et", lambda: "2026-05-07")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat1")
    monkeypatch.delenv("TELEGRAM_GROUP_CHAT_ID", raising=False)

    calls = []

    class FakeResp:
        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(req, timeout=10):
        calls.append(req)
        return FakeResp()

    monkeypatch.setattr(sender.urllib.request, "urlopen", fake_urlopen)

    assert sender.main(["--force"], data_dir=data_dir) == 0
    assert len(calls) == 1
