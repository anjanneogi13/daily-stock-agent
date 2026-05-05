"""Telegram daily sender should only mark dedup after confirmed delivery."""

from types import SimpleNamespace
from unittest.mock import Mock
import urllib.error


def test_send_dry_run_without_creds_is_success(monkeypatch, capsys):
    import scripts.send_layman_daily as sld

    monkeypatch.setattr(sld, "TOKEN", None)
    monkeypatch.setattr(sld, "CHATS", [])

    assert sld._send("hello") is True
    assert "dry-run" in capsys.readouterr().out


def test_send_returns_true_when_at_least_one_chat_succeeds(monkeypatch):
    import scripts.send_layman_daily as sld

    monkeypatch.setattr(sld, "TOKEN", "token")
    monkeypatch.setattr(sld, "CHATS", ["chat1", "chat2"])

    calls = []

    class Response:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    def fake_urlopen(url, data=None, timeout=20):
        calls.append(data)
        if len(calls) == 1:
            raise urllib.error.URLError("first chat markdown failed")
        return Response()

    monkeypatch.setattr(sld.urllib.request, "urlopen", fake_urlopen)

    assert sld._send("hello") is True
    assert len(calls) >= 2


def test_send_returns_false_when_all_chats_fail(monkeypatch):
    import scripts.send_layman_daily as sld

    monkeypatch.setattr(sld, "TOKEN", "token")
    monkeypatch.setattr(sld, "CHATS", ["chat1", "chat2"])
    monkeypatch.setattr(
        sld.urllib.request,
        "urlopen",
        Mock(side_effect=urllib.error.URLError("network down")),
    )

    assert sld._send("hello") is False


def test_main_does_not_mark_sent_when_delivery_fails(monkeypatch):
    import scripts.send_layman_daily as sld

    monkeypatch.setattr(sld, "_today_picks", lambda: [{"ticker": "AAPL"}])
    monkeypatch.setattr(sld, "build_message", lambda picks: "message")
    monkeypatch.setattr(sld, "should_send", lambda msg: True)
    monkeypatch.setattr(sld, "_send", lambda msg: False)

    mark_sent = Mock()
    monkeypatch.setattr(sld, "mark_sent", mark_sent)

    assert sld.main() == 1
    mark_sent.assert_not_called()


def test_main_marks_sent_after_delivery_success(monkeypatch):
    import scripts.send_layman_daily as sld

    monkeypatch.setattr(sld, "_today_picks", lambda: [{"ticker": "AAPL"}])
    monkeypatch.setattr(sld, "build_message", lambda picks: "message")
    monkeypatch.setattr(sld, "should_send", lambda msg: True)
    monkeypatch.setattr(sld, "_send", lambda msg: True)

    mark_sent = Mock()
    monkeypatch.setattr(sld, "mark_sent", mark_sent)

    assert sld.main() == 0
    mark_sent.assert_called_once_with("message")


def test_main_dedup_skip_does_not_send_or_mark(monkeypatch):
    import scripts.send_layman_daily as sld

    monkeypatch.setattr(sld, "_today_picks", lambda: [{"ticker": "AAPL"}])
    monkeypatch.setattr(sld, "build_message", lambda picks: "message")
    monkeypatch.setattr(sld, "should_send", lambda msg: False)

    send = Mock()
    mark_sent = Mock()
    monkeypatch.setattr(sld, "_send", send)
    monkeypatch.setattr(sld, "mark_sent", mark_sent)

    assert sld.main() == 0
    send.assert_not_called()
    mark_sent.assert_not_called()
