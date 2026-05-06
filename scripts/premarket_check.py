"""
Premarket Sanity Check — runs BEFORE notifications.
Reads today's picks from data/picks_log.csv, checks market conditions, 
and writes a tagged version to data/picks_today_tagged.json for the formatters.

Tags each pick:
  ✅ SAFE          — proceed normally
  ⚠️ HALF SIZE     — reduce position by 50%
  🚫 SKIP TODAY    — don't enter, gap too risky
  👀 WATCH ONLY    — no actionable entry until fresh quote is verified
"""
import csv, json, sys
from datetime import datetime
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("[premarket] yfinance missing — skipping check"); sys.exit(0)

today = datetime.now().strftime("%Y-%m-%d")

# ---- Load today's picks ----
p = Path("data/picks_log.csv")
if not p.exists():
    print("[premarket] No picks_log.csv"); sys.exit(0)

picks = [r for r in csv.DictReader(p.open()) if r.get("pick_date") == today]
if not picks:
    print("[premarket] No picks today"); sys.exit(0)

print(f"[premarket] Checking {len(picks)} picks...")

# ---- Market-wide signals ----
def safe_last(ticker):
    try:
        h = yf.Ticker(ticker).history(period="5d", auto_adjust=False)
        if len(h) >= 2:
            prev = float(h["Close"].iloc[-2])
            curr = float(h["Close"].iloc[-1])
            return prev, curr, (curr - prev) / prev * 100
    except Exception as e:
        print(f"[premarket] {ticker} fetch failed: {e}")
    return None, None, 0.0

spy_prev, spy_curr, spy_chg = safe_last("SPY")
qqq_prev, qqq_curr, qqq_chg = safe_last("QQQ")
soxx_prev, soxx_curr, soxx_chg = safe_last("SOXX")  # semiconductor ETF
vix_prev, vix_curr, vix_chg = safe_last("^VIX")

vix_disp = f"{vix_curr:.1f}" if vix_curr else "n/a"
print(f"[premarket] SPY: {spy_chg:+.2f}%  QQQ: {qqq_chg:+.2f}%  SOXX: {soxx_chg:+.2f}%  VIX: {vix_disp}")

# ---- Market regime ----
market_warnings = []
global_action = "normal"  # normal | half | skip_all

if spy_chg <= -1.5:
    market_warnings.append(f"🚫 SPY down {spy_chg:.1f}% — broad market selloff")
    global_action = "skip_all"
elif spy_chg <= -0.7:
    market_warnings.append(f"⚠️ SPY down {spy_chg:.1f}% — caution")
    global_action = "half"

if vix_curr and vix_curr >= 25:
    market_warnings.append(f"🚫 VIX at {vix_curr:.1f} — high fear regime")
    global_action = "skip_all"
elif vix_curr and vix_curr >= 20:
    market_warnings.append(f"⚠️ VIX at {vix_curr:.1f} — elevated volatility")
    if global_action == "normal":
        global_action = "half"

if soxx_chg <= -2.0:
    market_warnings.append(f"⚠️ Semiconductor sector (SOXX) down {soxx_chg:.1f}% — semis at risk")

# ---- Per-pick check ----
tagged = []
for p_ in picks:
    ticker = p_["ticker"]
    try:
        entry = float(p_["entry"]); sl = float(p_["stop_loss"])
    except Exception:
        continue

    _, last_close, _ = safe_last(ticker)
    if last_close is None:
        tag, reason = "👀 WATCH ONLY", "could not verify fresh price — require fresh quote before entry"
    else:
        gap_pct = (last_close - entry) / entry * 100
        sl_buffer = (entry - sl) / entry * 100  # how much room before SL

        # Decision logic
        if global_action == "skip_all":
            tag, reason = "🚫 SKIP TODAY", "broad market risk"
        elif last_close <= sl:
            tag, reason = "🚫 SKIP TODAY", f"price ${last_close:.2f} already at/below SL ${sl:.2f}"
        elif gap_pct <= -sl_buffer * 0.6:
            tag, reason = "🚫 SKIP TODAY", f"gapped {gap_pct:+.1f}%, only {sl_buffer-abs(gap_pct):.1f}% to SL"
        elif gap_pct >= 3.0:
            tag, reason = "⚠️ HALF SIZE", f"gapped UP {gap_pct:+.1f}% — chasing risk"
        elif global_action == "half":
            tag, reason = "⚠️ HALF SIZE", "market caution — reduce size"
        elif gap_pct <= -1.5:
            tag, reason = "⚠️ HALF SIZE", f"gapped {gap_pct:+.1f}% — wait for limit fill"
        else:
            tag, reason = "✅ SAFE", "normal entry"

    tagged.append({
        "ticker": ticker,
        "tag": tag,
        "reason": reason,
        "current_price": round(last_close, 2) if last_close else None,
        "gap_pct": round((last_close - entry) / entry * 100, 2) if last_close else None,
        "actionable": tag not in ("👀 WATCH ONLY", "🚫 SKIP TODAY"),
    })
    print(f"  {tag}  {ticker:6s}  {reason}")

# ---- Save result ----
out = {
    "date": today,
    "market": {
        "spy_change_pct": round(spy_chg, 2),
        "qqq_change_pct": round(qqq_chg, 2),
        "soxx_change_pct": round(soxx_chg, 2),
        "vix": round(vix_curr, 2) if vix_curr else None,
        "warnings": market_warnings,
        "global_action": global_action,
    },
    "picks": tagged,
}
Path("data").mkdir(exist_ok=True)
Path("data/premarket_check.json").write_text(json.dumps(out, indent=2))
print(f"[premarket] ✅ Saved data/premarket_check.json (action: {global_action})")
