"""
Code-Aware Coach: parses the codebase to extract current parameters,
cross-references with performance data, and suggests specific code changes.
Runs without AI — pure deterministic analysis.
"""
import ast
import re
from pathlib import Path
import pandas as pd


def extract_params(file_path: Path) -> dict:
    """Extract module-level constants and function defaults from a Python file."""
    if not file_path.exists():
        return {}
    src = file_path.read_text()
    params = {}
    
    # 1. Module-level UPPERCASE constants (e.g., MIN_SCORE = 0.7)
    try:
        tree = ast.parse(src)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id.isupper():
                        try:
                            val = ast.literal_eval(node.value)
                            params[tgt.id] = {"value": val, "line": node.lineno, "file": str(file_path)}
                        except Exception:
                            pass
    except Exception as e:
        params["_parse_error"] = str(e)
    
    # 2. Common indicator patterns: rsi(period=14), atr(window=14), ema(span=20), etc.
    for m in re.finditer(r'(\w+)\s*\(\s*(?:period|window|span|n|length)\s*=\s*(\d+)', src):
        key = f"{m.group(1)}_period"
        line_no = src[:m.start()].count("\n") + 1
        params.setdefault(key, {"value": int(m.group(2)), "line": line_no, "file": str(file_path)})
    
    # 3. ATR multipliers / R:R ratios in arithmetic (e.g., entry - 1.5*atr, entry + 2*risk)
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*\*\s*(atr|risk|stop|sl)\b', src, re.IGNORECASE):
        key = f"{m.group(2).lower()}_multiplier"
        line_no = src[:m.start()].count("\n") + 1
        if key not in params:
            params[key] = {"value": float(m.group(1)), "line": line_no, "file": str(file_path)}
    
    return params


def inspect_codebase() -> dict:
    """Walk all scripts/*.py and aggregate parameter inventory."""
    base = Path("scripts")
    inventory = {}
    if not base.exists():
        return inventory
    for p in sorted(base.glob("*.py")):
        if p.name.startswith("_") or p.name in ("send_telegram.py", "send_exec_telegram.py",
            "send_weekend_telegram.py", "send_monthly_telegram.py",
            "send_dashboard_telegram.py", "format_picks_email.py",
            "gemini_helper.py", "code_inspector.py", "local_analyst.py"):
            continue  # skip non-strategy / utility scripts
        params = extract_params(p)
        if params:
            inventory[p.name] = params
    return inventory


def diagnose(inventory: dict, evaluated: pd.DataFrame) -> list[str]:
    """Cross-reference params with performance patterns to produce code-targeted suggestions."""
    suggestions = []
    if evaluated.empty or len(evaluated) < 5:
        return ["📚 Need at least 5 evaluated trades for code-aware diagnosis."]
    
    ev = evaluated.copy()
    for col in ["score", "actual_return_pct", "r_multiple"]:
        if col in ev.columns:
            ev[col] = pd.to_numeric(ev[col], errors="coerce")
    
    # ── Find current params across files ──────────────
    def find(name_substr: str):
        for fname, params in inventory.items():
            for key, meta in params.items():
                if name_substr.lower() in key.lower():
                    return fname, key, meta
        return None, None, None
    
    # ── Diagnosis 1: MIN_SCORE vs score-bucket performance ──
    fname, key, meta = find("min_score")
    if not meta:
        fname, key, meta = find("score_threshold")
    if meta and "score" in ev.columns:
        ev_clean = ev.dropna(subset=["score", "actual_return_pct"])
        if len(ev_clean) >= 5:
            high = ev_clean[ev_clean["score"] >= 0.80]["actual_return_pct"].mean()
            low  = ev_clean[ev_clean["score"] <  0.80]["actual_return_pct"].mean()
            cur = meta["value"]
            if pd.notna(high) and pd.notna(low) and high - low > 1:
                new = max(cur + 0.05, 0.78)
                suggestions.append(
                    f"🎯 **`{key} = {cur}` in `{fname}:{meta['line']}` is too lenient.**\n"
                    f"  - Picks with score ≥0.80 averaged {high:+.2f}% return.\n"
                    f"  - Picks with score <0.80 averaged {low:+.2f}% return.\n"
                    f"  - **Action:** change to `{key} = {new:.2f}` to skip the weak bucket. "
                    f"Estimated impact: +{(high-low):.1f}% avg per trade, fewer total picks."
                )
    
    # ── Diagnosis 2: ATR multiplier vs SL hit rate ──
    fname, key, meta = find("atr_mult")
    if not meta:
        fname, key, meta = find("stop_multiplier")
    if not meta:
        fname, key, meta = find("sl_multiplier")
    sl_hits = (ev["evaluation_status"] == "sl_hit").sum() if "evaluation_status" in ev.columns else 0
    tp_hits = (ev["evaluation_status"] == "tp_hit").sum() if "evaluation_status" in ev.columns else 0
    total_eval = sl_hits + tp_hits
    if meta and total_eval >= 8 and sl_hits > tp_hits * 1.5:
        cur = meta["value"]
        new = round(cur * 1.3, 2)
        suggestions.append(
            f"🛡️ **`{key} = {cur}` in `{fname}:{meta['line']}` may be too tight.**\n"
            f"  - SL hit {sl_hits}× vs TP hit {tp_hits}× — losing setups before they breathe.\n"
            f"  - **Action:** widen to `{key} = {new}` (× 1.3). "
            f"Trade-off: bigger losses on truly bad picks, but more winners survive normal volatility."
        )
    elif meta and total_eval >= 8 and tp_hits > sl_hits * 2:
        cur = meta["value"]
        new = round(cur * 0.85, 2)
        suggestions.append(
            f"🛡️ **`{key} = {cur}` in `{fname}:{meta['line']}` is generous.**\n"
            f"  - TP hit {tp_hits}× vs SL hit {sl_hits}× — you're winning a lot. "
            f"Tighten SL to lock in more profit per losing trade.\n"
            f"  - **Action:** tighten to `{key} = {new}`."
        )
    
    # ── Diagnosis 3: TP ratio (R:R target) ──
    fname, key, meta = find("tp_mult")
    if not meta:
        fname, key, meta = find("risk_reward")
    if not meta:
        fname, key, meta = find("take_profit")
    if meta and total_eval >= 10:
        win_rate = tp_hits / total_eval * 100
        cur = meta["value"]
        if win_rate < 35 and isinstance(cur, (int, float)) and cur >= 2:
            new = round(cur * 0.75, 2)
            suggestions.append(
                f"🎯 **`{key} = {cur}` in `{fname}:{meta['line']}` is too ambitious.**\n"
                f"  - Win rate {win_rate:.0f}% — TP target rarely reached.\n"
                f"  - **Action:** lower to `{key} = {new}`. More wins, smaller wins, but better expectancy."
            )
    
    # ── Diagnosis 4: Indicator periods worth A/B testing ──
    for fname, params in inventory.items():
        for key, meta in params.items():
            if key.endswith("_period") and isinstance(meta.get("value"), int):
                val = meta["value"]
                if "rsi" in key.lower() and val == 14:
                    suggestions.append(
                        f"🔬 **`{key} = {val}` in `{fname}:{meta['line']}` is the default.**\n"
                        f"  - Default RSI(14) is widely arbitraged. Consider A/B testing RSI(7) for faster signals or RSI(21) for less noise.\n"
                        f"  - **Action:** Try `{key} = 21` for one week, compare win rate."
                    )
                if "atr" in key.lower() and val < 10:
                    suggestions.append(
                        f"🔬 **`{key} = {val}` in `{fname}:{meta['line']}` may be noisy.**\n"
                        f"  - Short ATR period reacts to single-day spikes. Consider ATR(14) or ATR(20) for stable stops.\n"
                        f"  - **Action:** Try `{key} = 14`."
                    )
    
    # ── Diagnosis 5: Tag-level filter recommendation with file:line ──
    if "tag" in ev.columns:
        tag_perf = ev.dropna(subset=["actual_return_pct"]).groupby("tag").agg(
            n=("ticker", "count"), avg=("actual_return_pct", "mean")
        ).reset_index()
        bad = tag_perf[(tag_perf["n"] >= 3) & (tag_perf["avg"] < -1.5)]
        for _, r in bad.iterrows():
            target = "pick_stocks.py"
            suggestions.append(
                f"🚫 **Tag `'{r['tag']}'` is consistently losing ({r['avg']:+.1f}% avg over {int(r['n'])} trades).**\n"
                f"  - **Action:** open `scripts/{target}` and add at the top of the scoring loop:\n"
                f"    ```python\n    if tag == \"{r['tag']}\":\n        continue  # filter out underperforming tag\n    ```"
            )
    
    if not suggestions:
        suggestions.append("✅ No code-level red flags detected. Strategy is performing within expected bounds for current parameters.")
    
    return suggestions


def report(period_days: int = 7) -> str:
    """Generate a code-aware diagnostic report."""
    csv = Path("data/picks_log.csv")
    lines = ["## 🔬 Code-Aware Diagnostic"]
    
    inventory = inspect_codebase()
    
    # Inventory summary
    lines.append("\n### 📋 Current parameter inventory")
    if not inventory:
        lines.append("- _No scripts found to inspect._")
    else:
        for fname, params in inventory.items():
            if not params:
                continue
            lines.append(f"\n**`scripts/{fname}`**")
            for k, meta in list(params.items())[:8]:
                if k.startswith("_"):
                    continue
                lines.append(f"- `{k} = {meta['value']}` (line {meta['line']})")
    
    # Diagnoses
    if csv.exists():
        df = pd.read_csv(csv)
        if "pick_date" in df.columns:
            df["pick_date"] = pd.to_datetime(df["pick_date"], errors="coerce")
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(days=period_days)
            recent = df[df["pick_date"] >= cutoff]
        else:
            recent = df
        evaluated = recent[recent.get("evaluation_status", pd.Series()).isin(["tp_hit", "sl_hit", "closed"])]
        
        lines.append(f"\n### 🩺 Code-targeted suggestions (based on last {period_days}d, {len(evaluated)} evaluated trades)")
        for s in diagnose(inventory, evaluated):
            lines.append(f"\n{s}")
    else:
        lines.append("\n_No picks_log.csv yet — code suggestions will appear once trades are evaluated._")
    
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    print(report(days))
