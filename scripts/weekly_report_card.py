"""Generate weekly performance report card and post to Telegram + GitHub Issue."""
import os, json, sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.performance_tracker import save_metrics


def format_report(m: dict) -> str:
    overall = m["overall"]
    week = m["last_7_days"]
    day = m["day_trades"]
    swing = m["swing_trades"]

    def emoji(val, target, higher_better=True):
        if higher_better:
            return "✅" if val >= target else "⚠️" if val >= target * 0.7 else "🔴"
        return "✅" if val <= target else "⚠️" if val <= target * 1.3 else "🔴"

    lines = [
        f"📊 *Weekly Performance Report Card — {datetime.now().strftime('%Y-%m-%d')}*",
        "",
        f"*This Week ({week['n_trades']} trades)*",
        f"  Wins: {week['wins']} | Losses: {week['losses']} | Win rate: {week['win_rate']}%",
        f"  Avg R: {week['avg_r']} | Total return: {week['total_return_pct']}%",
        "",
        "*Overall Performance*",
        f"  📈 Win rate: {overall['win_rate']}% {emoji(overall['win_rate'], 55)}",
        f"  💰 Avg R: {overall['avg_r']} {emoji(overall['avg_r'], 0.5)}",
        f"  📊 Sharpe: {overall['sharpe']} {emoji(overall['sharpe'], 1.5)}",
        f"  📉 Max DD: {overall['max_dd_pct']}% {emoji(overall['max_dd_pct'], 15, higher_better=False)}",
        f"  💎 Profit factor: {overall['profit_factor']} {emoji(overall['profit_factor'], 1.5)}",
        f"  🎯 Expectancy: {overall['expectancy_r']}R per trade",
        f"  📦 Total trades: {overall['n_trades']}",
        "",
    ]

    if overall['best_ticker']:
        lines.append(f"🏆 Best trade: *{overall['best_ticker']}* ({overall['best_trade_r']}R)")
    if overall['worst_ticker']:
        lines.append(f"😰 Worst trade: *{overall['worst_ticker']}* ({overall['worst_trade_r']}R)")
    lines.append("")

    if day['n_trades'] > 0 or swing['n_trades'] > 0:
        lines.append("*By trade type:*")
        if day['n_trades']:
            lines.append(f"🔥 DAY ({day['n_trades']}): win {day['win_rate']}%, avg R {day['avg_r']}")
        if swing['n_trades']:
            lines.append(f"⚡ SWING ({swing['n_trades']}): win {swing['win_rate']}%, avg R {swing['avg_r']}")
        lines.append("")

    return "\n".join(lines)


def claude_coach(metrics: dict) -> str:
    """Ask Claude for one piece of actionable coaching advice."""
    try:
        import anthropic
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            return ""
        client = anthropic.Anthropic(api_key=key)
        prompt = f"""You are a senior trading coach reviewing this AI agent's weekly performance:

{json.dumps(metrics, indent=2)}

Give ONE specific, actionable coaching insight in 2-3 sentences. Focus on:
- The biggest pattern you see (winning or losing)
- One concrete change to consider next week

Be direct, no fluff. Start with "💡 Coaching:"."""
        resp = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception as e:
        return f"💡 Coaching: (Claude unavailable: {type(e).__name__})"


def main():
    metrics = save_metrics()
    report = format_report(metrics)

    if metrics["overall"]["n_trades"] >= 5:
        coaching = claude_coach(metrics)
        if coaching:
            report += "\n\n" + coaching

    # Write to file (for GitHub issue)
    Path("data/weekly_reports").mkdir(parents=True, exist_ok=True)
    out = Path(f"data/weekly_reports/report_{datetime.now().strftime('%Y-%m-%d')}.md")
    out.write_text(report)
    print(report)
    print(f"\n✅ Saved to {out}")

    # Telegram
    bot = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")
    if bot and chat:
        import requests
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{bot}/sendMessage",
                json={"chat_id": chat, "text": report, "parse_mode": "Markdown"},
                timeout=15,
            )
            print(f"Telegram: {r.status_code}")
        except Exception as e:
            print(f"Telegram failed: {e}")


if __name__ == "__main__":
    main()
