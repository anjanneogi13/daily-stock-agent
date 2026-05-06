"""Daily Picks workflow must be reliable enough for unattended operation."""

from pathlib import Path
import re


WF = Path(".github/workflows/daily-picks.yml")


def _text() -> str:
    return WF.read_text()


def test_daily_picks_has_multiple_guarded_cron_chances():
    text = _text()
    crons = re.findall(r"cron:\s*'([^']+)'", text)

    assert len(crons) >= 5
    assert "30 12 * * 1-5" in crons
    assert "30 13 * * 1-5" in crons
    assert "30 14 * * 1-5" in crons
    assert "picks_log.csv dedup guard" in text


def test_post_send_commit_can_recover_picks_log():
    text = _text()
    post_send = text.split("- name: Commit post-send artifacts", 1)[1]

    assert "data/picks_log.csv" in post_send
    assert "recovery path" in post_send


def test_post_send_push_stashes_unstaged_changes_before_rebase():
    text = _text()
    post_send = text.split("- name: Commit post-send artifacts", 1)[1]

    assert "git stash push --include-untracked" in post_send
    assert "auto-stash-post-send" in post_send
    assert "git pull --rebase origin main && git push" in post_send


def test_post_send_push_failure_is_not_hidden():
    text = _text()
    post_send = text.split("- name: Commit post-send artifacts", 1)[1]

    assert "POST_PUSH_OK=0" in post_send
    assert "CRITICAL: post-send artifacts were committed locally but not pushed" in post_send
    assert "done || true" not in post_send
    assert "exit 1" in post_send

def test_daily_picks_hard_blocks_normal_picks_after_0920_et():
    text = _text()

    assert "OFFICIAL_CUTOFF=$((9 * 60 + 20))" in text
    assert "Official premarket window missed after 09:20 ET" in text
    assert "Manual dispatch must not bypass this freshness/timing gate" in text
    assert "Manual run — bypassing time guard" not in text
    assert "WINDOW_END=$((11 * 60))" not in text


def test_daily_picks_sends_missed_window_alert_instead_of_normal_picks():
    text = _text()

    assert "missed_window=true" in text
    assert "Send missed-window Telegram alert" in text
    assert "steps.guard.outputs.missed_window == 'true'" in text
    assert "scripts/send_missed_premarket_alert.py" in text
