"""Weekly hypothesis review runner.

Loads closed picks from the signal journal, runs hypothesis_engine.analyze(),
formats a Telegram report, and (optionally) sends it.

Usage:
    python scripts/run_hypothesis_review.py                 # local print only
    python scripts/run_hypothesis_review.py --send          # send to Telegram
    python scripts/run_hypothesis_review.py --min-n 5       # lower N for early data
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.signal_journal import load_closed
from src import hypothesis_engine as he


REPORT_DIR = Path("data/reports/hypothesis")


def _send_telegram(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    cids  = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"),
                          os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]
    if not token or not cids:
        print("[telegram] Missing creds — skipping send")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    ok_any = False
    # Telegram limit ~4096; truncate safely
    if len(text) > 4000:
        text = text[:3950] + "\n\n_(truncated)_"
    for cid in cids:
        for parse in ("Markdown", None):
            payload = {"chat_id": cid, "text": text, "disable_web_page_preview": "true"}
            if parse:
                payload["parse_mode"] = parse
            data = urllib.parse.urlencode(payload).encode()
            try:
                resp = urllib.request.urlopen(
                    urllib.request.Request(url, data=data), timeout=10)
                if json.loads(resp.read()).get("ok"):
                    print(f"[telegram] ✅ Sent to {cid[:6]}... ({parse or 'plain'})")
                    ok_any = True
                    break
            except Exception as e:
                print(f"[telegram] {parse or 'plain'} failed: {str(e)[:120]}")
    return ok_any


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true", help="Send report to Telegram")
    ap.add_argument("--min-n", type=int, default=None,
                    help="Override MIN_SAMPLE_SIZE for sparse-data weeks")
    ap.add_argument("--save", action="store_true", default=True,
                    help="Save markdown report to data/reports/hypothesis/")
    args = ap.parse_args()

    if args.min_n is not None:
        he.MIN_SAMPLE_SIZE = args.min_n

    closed = load_closed()
    n_closed = len(closed)
    print(f"[hypothesis] Loaded {n_closed} closed picks from journal")

    if n_closed < 5:
        report = (
            f"🧠 *Hypothesis Review — {datetime.now():%Y-%m-%d}*\n"
            f"\n"
            f"Only {n_closed} closed picks in journal. Need ≥5 to run analysis.\n"
            f"Come back next week."
        )
        print(report)
        if args.send:
            _send_telegram(report)
        return 0

    result = he.analyze(closed)
    report_md = he.format_report(result)

    # Wrap with header
    full_report = (
        f"🧠 *Weekly Hypothesis Review — {datetime.now():%Y-%m-%d}*\n"
        f"\n"
        f"{report_md}\n"
        f"\n"
        f"_Observe-mode: insights only, no auto-flipping._"
    )

    print(full_report)

    if args.save:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        out = REPORT_DIR / f"{datetime.now():%Y-%m-%d}.md"
        out.write_text(full_report)
        print(f"\n[hypothesis] 💾 Saved {out}")

    if args.send:
        _send_telegram(full_report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
