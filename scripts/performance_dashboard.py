"""Performance dashboard from picks_log.csv. Run anytime: python scripts/performance_dashboard.py"""
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

p = Path("data/picks_log.csv")
if not p.exists():
    print("No picks_log.csv yet."); raise SystemExit

rows = list(csv.DictReader(p.open()))
total = len(rows)
evaluated = [r for r in rows if r.get("evaluation_status") and r["evaluation_status"] != "pending"]
pending = [r for r in rows if r.get("evaluation_status") == "pending" or not r.get("evaluation_status")]

def f(x, d=0.0):
    try: return float(x)
    except: return d

print("\n" + "="*70)
print(f"📊 DAILY STOCK AGENT — PERFORMANCE DASHBOARD")
print("="*70)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

print(f"📈 Total picks logged:    {total}")
print(f"✅ Evaluated (closed):    {len(evaluated)}")
print(f"⏳ Pending (still open):  {len(pending)}")

if not evaluated:
    print("\n⚠ No closed trades yet. Wait for evaluator to mark TP/SL hits.")
    raise SystemExit

# Outcomes
tp = [r for r in evaluated if r["evaluation_status"] == "tp_hit"]
sl = [r for r in evaluated if r["evaluation_status"] == "sl_hit"]
exp = [r for r in evaluated if r["evaluation_status"] == "expired"]

win_rate = len(tp) / len(evaluated) * 100 if evaluated else 0
returns = [f(r["actual_return_pct"]) for r in evaluated if r.get("actual_return_pct")]
r_mults = [f(r["r_multiple"]) for r in evaluated if r.get("r_multiple")]
avg_ret = sum(returns)/len(returns) if returns else 0
avg_r = sum(r_mults)/len(r_mults) if r_mults else 0
total_r = sum(r_mults) if r_mults else 0

print(f"\n🎯 OUTCOMES")
print(f"   🟢 TP hit:    {len(tp):3d}  ({len(tp)/len(evaluated)*100:5.1f}%)")
print(f"   🔴 SL hit:    {len(sl):3d}  ({len(sl)/len(evaluated)*100:5.1f}%)")
print(f"   ⚪ Expired:   {len(exp):3d}  ({len(exp)/len(evaluated)*100:5.1f}%)")

print(f"\n💰 PERFORMANCE")
print(f"   Win rate:        {win_rate:.1f}%")
print(f"   Avg return:      {avg_ret:+.2f}%")
print(f"   Avg R-multiple:  {avg_r:+.2f}R")
print(f"   Total R earned:  {total_r:+.2f}R")
expectancy = (win_rate/100) * 2.0 - (1 - win_rate/100) * 1.0
print(f"   Expectancy/trade: {expectancy:+.2f}R  (>0 = profitable system)")

# Best/worst
ranked = sorted([r for r in evaluated if r.get("r_multiple")], key=lambda x: f(x["r_multiple"]), reverse=True)
print(f"\n🏆 TOP 5 PICKS")
for r in ranked[:5]:
    print(f"   {r['pick_date']} {r['ticker']:6s}  {f(r['r_multiple']):+.2f}R  ({f(r['actual_return_pct']):+.2f}%)  [{r['evaluation_status']}]")

print(f"\n💀 WORST 5 PICKS")
for r in ranked[-5:][::-1]:
    print(f"   {r['pick_date']} {r['ticker']:6s}  {f(r['r_multiple']):+.2f}R  ({f(r['actual_return_pct']):+.2f}%)  [{r['evaluation_status']}]")

# By regime
by_reg = defaultdict(list)
for r in evaluated:
    by_reg[r.get("regime","?")].append(f(r.get("r_multiple",0)))
print(f"\n🌐 BY MARKET REGIME")
for reg, vals in by_reg.items():
    if vals:
        print(f"   {reg:10s} {len(vals):3d} trades  •  avg {sum(vals)/len(vals):+.2f}R")

# By score bucket
buckets = defaultdict(list)
for r in evaluated:
    s = f(r.get("score",0))
    b = "0.85+" if s>=0.85 else "0.80-0.85" if s>=0.80 else "0.75-0.80" if s>=0.75 else "<0.75"
    buckets[b].append(f(r.get("r_multiple",0)))
print(f"\n📊 BY COMPOSITE SCORE")
for b in ["0.85+","0.80-0.85","0.75-0.80","<0.75"]:
    if buckets[b]:
        v = buckets[b]
        print(f"   {b:12s} {len(v):3d} trades  •  avg {sum(v)/len(v):+.2f}R  •  win {sum(1 for x in v if x>0)/len(v)*100:.0f}%")

print("\n" + "="*70)
print("💡 Rule of thumb: positive expectancy + 100+ trades = trustworthy edge")
print("="*70 + "\n")
