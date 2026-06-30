"""Task 7a / vision items #29 (heartbeat) + #14/#4 (channel routing groundwork).

watchdog.yml only alarms ON FAILURE to the same chat -> a silent failure stays
silent. This adds a positive daily "I'm alive + what I logged today" heartbeat.

v1 is honest: it reports liveness + today's pick-artifact/picks status derived
from durable files on disk (NOT a fabricated send-recap; per-report send ledgers
are deleted post-send so a full sent-list is not durably queryable).

Channel resolution prefers HEARTBEAT_CHAT_ID, then the existing
TELEGRAM_CHAT_ID / TELEGRAM_GROUP_CHAT_ID chain -- so it works before the
dedicated secret exists (falls back to main) and self-separates once set.
"""
import importlib

mod = importlib.import_module("scripts.send_heartbeat")


def _clear(monkeypatch):
    for k in ("HEARTBEAT_CHAT_ID", "TELEGRAM_CHAT_ID", "TELEGRAM_GROUP_CHAT_ID",
              "TELEGRAM_BOT_TOKEN"):
        monkeypatch.delenv(k, raising=False)


# ---- chat-id resolution ---------------------------------------------------
def test_prefers_heartbeat_chat_id(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("HEARTBEAT_CHAT_ID", "hb1")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "main1")
    monkeypatch.setenv("TELEGRAM_GROUP_CHAT_ID", "grp1")
    assert mod._chat_ids() == ["hb1", "main1", "grp1"]
    assert mod._chat_ids()[0] == "hb1"  # heartbeat first


def test_falls_back_to_main_when_no_heartbeat(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "main1")
    ids = mod._chat_ids()
    assert "main1" in ids and "hb" not in "".join(ids)


def test_empty_when_none_set(monkeypatch):
    _clear(monkeypatch)
    assert mod._chat_ids() == []


# ---- message composition (durable, honest) --------------------------------
def test_message_has_alive_marker_and_date(monkeypatch, tmp_path):
    _clear(monkeypatch)
    msg = mod._compose_message(data_dir=tmp_path)
    assert isinstance(msg, str) and msg.strip()
    low = msg.lower()
    assert "alive" in low
    # ISO date YYYY-MM-DD present
    import re
    assert re.search(r"\d{4}-\d{2}-\d{2}", msg), msg


def test_message_reports_no_picks_when_absent(monkeypatch, tmp_path):
    _clear(monkeypatch)
    # empty data dir -> should say not-yet / none, never crash
    msg = mod._compose_message(data_dir=tmp_path)
    assert "not" in msg.lower() or "none" in msg.lower() or "0" in msg


def test_message_reports_picks_when_present(monkeypatch, tmp_path):
    _clear(monkeypatch)
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (tmp_path / "picks_log.csv").write_text(
        "date,ticker\n" + f"{today},AAA\n" + f"{today},BBB\n")
    msg = mod._compose_message(data_dir=tmp_path)
    assert "2" in msg  # two rows for today reflected


# ---- graceful no-op -------------------------------------------------------
def test_main_returns_zero_without_creds(monkeypatch):
    _clear(monkeypatch)
    # No token, no chat ids -> must not raise, must return 0.
    assert mod.main() == 0
