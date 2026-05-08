"""Daily Picks workflow must be reliable enough for unattended operation."""

from pathlib import Path
import re


WF = Path(".github/workflows/daily-picks.yml")
WATCHDOG = Path(".github/workflows/watchdog.yml")


def _text() -> str:
    return WF.read_text()


def _watchdog_text() -> str:
    return WATCHDOG.read_text()


def test_daily_picks_has_frequent_guarded_cron_chances():
    text = _text()
    crons = re.findall(r"cron:\s*'([^']+)'", text)

    assert "5,20,35,50 12-14 * * 1-5" in crons
    assert "frequent guarded premarket attempts" in text
    assert "picks_log.csv dedup guard" in text
    assert "OFFICIAL_CUTOFF=$((9 * 60 + 20))" in text


def test_daily_picks_keeps_hard_safety_cutoff():
    text = _text()

    assert "OFFICIAL_CUTOFF=$((9 * 60 + 20))" in text
    assert "Official premarket window missed after 09:20 ET" in text
    assert "Manual dispatch must not bypass this freshness/timing gate" in text
    assert "Manual run — bypassing time guard" not in text
    assert "WINDOW_END=$((11 * 60))" not in text


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


def test_daily_picks_uses_single_combined_missed_window_late_ideas_message():
    text = _text()

    assert "missed_window=true" in text
    assert "Send missed-window Telegram alert" not in text
    assert "scripts/send_missed_premarket_alert.py" not in text
    assert "Send late watch-only daily ideas to Telegram" in text
    assert "combined missed-window and late watch-only ideas Telegram sender completed" in text


def test_watchdog_runs_before_market_open_and_cutoff():
    text = _watchdog_text()
    crons = re.findall(r"cron:\s*'([^']+)'", text)

    assert "10,18 13-14 * * 1-5" in crons
    assert "09:10 and 09:18 ET" in text
    assert "09:20 ET cutoff" in text
    assert "9:35" not in text


def test_watchdog_checks_picks_log_not_stale_premarket_check():
    text = _watchdog_text()

    assert "grep -c \"^$ET_DATE\" data/picks_log.csv" in text
    assert "TODAY_ROWS" in text
    assert "premarket_check.json" not in text


def test_watchdog_does_not_create_picks_or_bypass_safety():
    text = _watchdog_text()

    assert "does not create picks itself" in text
    assert "does not bypass the daily-picks timing gate" in text
    assert "does not enable paper/live trading" in text
    assert "Watchdog is attempting to trigger Daily Stock Picks automatically now" in text
    assert "Manual run: Actions → Daily Stock Picks → Run workflow" in text


def test_daily_picks_records_run_status_events():
    text = _text()

    assert "scripts/record_daily_picks_run_status.py --event guard_started" in text
    assert "--event before_window_skip" in text
    assert "--event missed_window_skip" in text
    assert "--event already_logged_skip" in text
    assert "--event guard_passed" in text
    assert "--event verify_csv_success" in text
    assert "--event telegram_daily_success" in text
    assert "data/daily_picks_run_status_*.jsonl" in text


def test_skipped_daily_picks_attempts_commit_status_artifact():
    text = _text()

    assert "Commit run-status artifacts for skipped daily-picks attempt" in text
    assert "steps.guard.outputs.should_run != 'true'" in text
    assert "status: daily picks attempt" in text


def test_watchdog_records_and_commits_run_status():
    text = _watchdog_text()

    assert "contents: write" in text
    assert "--workflow watchdog --event watchdog_started" in text
    assert "--event watchdog_checked --result missing_picks" in text
    assert "--event watchdog_alert --result success" in text
    assert "Commit watchdog run-status artifact" in text
    assert "data/daily_picks_run_status_*.jsonl" in text


def test_missed_window_generates_late_watch_only_ideas():
    text = _text()

    assert "Generate late watch-only daily ideas" in text
    assert "steps.guard.outputs.missed_window == 'true'" in text
    assert "scripts/generate_late_daily_ideas.py" in text
    assert "scripts/send_late_daily_ideas_telegram.py" in text
    assert "--event late_ideas_generated" in text
    assert "--event late_ideas_telegram" in text
    assert "data/late_daily_ideas_*.jsonl" in text
    assert "data/late_daily_ideas_*.md" in text


def test_late_watch_only_ideas_install_quote_dependency():
    text = _text()

    assert "Set up Python for late watch-only ideas" in text
    assert "Install late watch-only idea dependencies" in text
    assert "pip install yfinance==0.2.65 curl_cffi==0.7.4" in text
    assert "scripts/generate_late_daily_ideas.py --max-results 5 --min-score 0.40" in text
    assert "--require-quote" not in text


def test_late_watch_only_message_is_single_combined_notice():
    text = _text()

    assert text.count("Send late watch-only daily ideas to Telegram") == 1
    assert "Send missed-window Telegram alert" not in text
    assert "--event missed_window_alert" not in text
    assert "--event late_ideas_telegram" in text

def test_watchdog_can_trigger_daily_picks_before_cutoff():
    text = _watchdog_text()

    assert "actions: write" in text
    assert "watchdog_rescue_dispatch" in text
    assert "actions/workflows/daily-picks.yml/dispatches" in text
    assert '"ref":"main"' in text
    assert "Rescue triggered: $RESCUE_TRIGGERED" in text
    assert "does not create picks itself" in text

def test_daily_picks_sends_failure_alert_and_commits_no_pick_report():
    text = _text()

    assert "Send daily picks failure alert" in text
    assert "Daily picks failed for $ET_DATE" in text
    assert "telegram_daily_failed" in text
    assert "data/daily_picks_no_pick_report_*.json" in text
    assert "data/daily_picks_no_pick_report_*.md" in text

def test_independent_late_watch_only_workflow_exists_and_is_safe():
    path = Path(".github/workflows/late_watch_only.yml")
    assert path.exists()
    text = path.read_text()

    crons = re.findall(r"cron:\s*'([^']+)'", text)
    assert "25,40 13-14 * * 1-5" in crons
    assert "OFFICIAL_CUTOFF=$((9 * 60 + 20))" in text
    assert "Does not create official picks" in text
    assert "Does not write data/picks_log.csv" in text
    assert "Does not enable live trading" in text
    assert "late_watch_only_guard_passed" in text
    assert "scripts/generate_late_daily_ideas.py --max-results 5 --min-score 0.40" in text
    assert "--require-quote" not in text
    assert "scripts/send_late_daily_ideas_telegram.py" in text
    assert "data/late_daily_ideas_*.jsonl" in text
    assert "data/late_daily_ideas_*.md" in text


def test_skipped_daily_picks_attempt_self_heals_missing_run_status_marker():
    text = Path(".github/workflows/daily-picks.yml").read_text()

    skipped_block = text.split("- name: Commit run-status artifacts for skipped daily-picks attempt", 1)[1]
    skipped_block = skipped_block.split("- name: Set up Python", 1)[0]

    assert "skipped_run_persistence_marker" in skipped_block
    assert "GITHUB_RUN_ID" in skipped_block
    assert "grep -Fq" in skipped_block
    assert "'\"run_id\": \"'" in skipped_block
    assert '"${GITHUB_RUN_ID}"' in skipped_block
    assert 'grep -q ""run_id": "${GITHUB_RUN_ID}""' not in skipped_block
    assert r"\\\\run_id" not in skipped_block
    assert "daily_picks_run_status_${ET_DATE}.jsonl" in skipped_block
    assert "tail -8" in skipped_block
    assert "git status --short" in skipped_block
