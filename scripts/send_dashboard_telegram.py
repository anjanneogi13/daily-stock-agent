"""Sends performance dashboard to Telegram after market close."""
import os, sys, json, subprocess, urllib.request, urllib.parse

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_IDS = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"), os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]
if not TOKEN or not CHAT_IDS:
    print("[telegram] Missing creds — skipping"); sys.exit(0)

# Capture dashboard output
result = subprocess.run(["python", "scripts/performance_dashboard.py"],
                        capture_output=True, text=True)
output = result.stdout.strip() or "_(empty dashboard)_"

# Telegram needs <4096 chars; wrap in code block for monospace alignment
msg = "📊 *Daily Performance Update*\n```\n" + output + "\n```"
if len(msg) > 4000:
    msg = msg[:3950] + "\n```\n_(truncated)_"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
for _cid in CHAT_IDS:
    data = urllib.parse.urlencode({
        "chat_id": _cid, "text": msg,
        "parse_mode": "Markdown", "disable_web_page_preview": "true",
    }).encode()
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
        res = json.loads(resp.read())
        print(f"[telegram] {'✅ Dashboard sent' if res.get('ok') else '❌ '+str(res)}")
    except Exception as e:
        print(f"[telegram] ❌ {e}"); sys.exit(1)
