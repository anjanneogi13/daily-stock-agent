"""
Code-Aware Coach: parses config.yaml + src/ + main.py to extract real strategy
parameters, cross-references with picks_log.csv performance data, and produces
specific file:line/key-targeted suggestions. Pure deterministic — no AI required.
"""
import ast
import re
from pathlib import Path
import pandas as pd

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ════════════════════════════════════════════════════
# Config + code scanning
# ════════════════════════════════════════════════════
def load_config_params() -> dict:
    """Flatten config.yaml into a dict of dotted-path → value, with file ref."""
    p = Path("config.yaml")
    if not (HAS_YAML and p.exists()):
        return {}
    try:
        cfg = yaml.safe_load(p.read_text())
    except Exception:
        return {}

    flat = {}

    def walk(node, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, (int, float, bool, str)):
            flat[path] = {"value": node, "file": "config.yaml", "type": "yaml"}

    walk(cfg)
    return flat


def extract_code_params(file_path: Path) -> dict:
    """Extract module-level constants and indicator default args from a Python file."""
    if not file_path.exists():
        return {}
    src = file_path.read_text()
    params = {}

    # 1. Module-level constants (UPPERCASE or lowercase) of numeric type
    try:
        tree = ast.parse(src)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        try:
                            val = ast.literal_eval(node.value)
                            if isinstance(val, (int, float, bool)):
                                params[tgt.id] = {
                                    "value": val,
                                    "line": node.lineno,
                                    "file": str(file_path),
                                    "type": "const",
                                }
                        except Exception:
                            pass
            # 2. Function default args (e.g., def rsi(period: int = 14))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = node.args
                defaults = args.defaults
                if defaults:
                    arg_names = [a.arg for a in args.args[-len(defaults):]]
                    for arg_name, dval in zip(arg_names, defaults):
                        try:
                            v = ast.literal_eval(dval)
                            if isinstance(v, (int, float)):
                                key = f"{node.name}({arg_name})"
                                params[key] = {
                                    "value": v,
                                    "line": node.lineno,
                                    "file": str(file_path),
                                    "type": "default",
                                }
                        except Exception:
                            pass
    except Exception:
        pass

    return params


def inspect_codebase() -> dict:
    """Aggregate inventory: config.yaml + src/*.py + main.py."""
    inventory = {"config.yaml": load_config_params()}
    for p in [Path("main.py")] + sorted(Path("src").glob("*.py")) if Path("src").exists() else [Path("main.py")]:
        if not p.exists() or p.name == "__init__.py":
            continue
        params = extract_code_params(p)
        if params:
            inventory[str(p)] = params
    return {k: v for k, v in inventory.items() if v}


# ════════════════════════════════════════════════════
# Diagnostic engine
# ════════════════════════════════════════════════════
def diagnose(inventory: dict, evaluated: pd.DataFrame) -> list[str]:
    suggestions = []

    if evaluated.empty or len(evaluated) < 5:
        return ["📚 Need at least 5 evaluated trades for code-aware diagnosis."]

    ev = evaluated.copy()
    for col in ["score", "actual_return_pct", "r_multiple"]:
        if col in ev.columns:
            ev[col] = pd.to_numeric(ev[col], errors="coerce")

    # Helper: lookup a param across all sources
    def find_param(*key_substrings):
        for src_name, params in inventory.items():
            for k, meta in params.items():
                kl = k.lower()
                if any(sub.lower() in kl for sub in key_substrings):
                    return src_name, k, meta
        return None, None, None

    cfg_params = inventory.get("config.yaml", {})

    sl_hits = (ev["evaluation_status"] == "sl_hit").sum() if "evaluation_status" in ev.columns else 0
    tp_hits = (ev["evaluation_status"] == "tp_hit").sum() if "evaluation_status" in ev.columns else 0
    total_eval = sl_hits + tp_hits
    win_rate = tp_hits / total_eval * 100 if total_eval else 0

    # ── 1. output.min_score vs score-bucket performance ──
    min_score = cfg_params.get("output.min_score")
    if min_score and "score" in ev.columns and "actual_return_pct" in ev.columns:
        ev_clean = ev.dropna(subset=["score", "actual_return_pct"])
        if len(ev_clean) >= 5:
            high = ev_clean[ev_clean["score"] >= 0.80]["actual_return_pct"].mean()
            low = ev_clean[ev_clean["score"] < 0.80]["actual_return_pct"].mean()
            if pd.notna(high) and pd.notna(low) and high - low > 1:
                cur = min_score["value"]
                new = round(max(cur + 0.05, 0.78), 2)
                suggestions.append(
                    f"🎯 **`config.yaml: output.min_score = {cur}` is too lenient.**\n"
                    f"  - Score ≥0.80 averaged {high:+.2f}% return.\n"
                    f"  - Score <0.80 averaged {low:+.2f}% return.\n"
                    f"  - **Action:** edit `config.yaml` → `output.min_score: {new}`. "
                    f"Estimated impact: +{(high-low):.1f}% avg per trade."
                )

    # ── 2. risk.stop_loss_atr_mult vs SL/TP ratio ──
    sl_mult = cfg_params.get("risk.stop_loss_atr_mult")
    if sl_mult and total_eval >= 8:
        cur = sl_mult["value"]
        if sl_hits > tp_hits * 1.5:
            new = round(cur * 1.3, 2)
            suggestions.append(
                f"🛡️ **`config.yaml: risk.stop_loss_atr_mult = {cur}` is too tight.**\n"
                f"  - SL hit {sl_hits}× vs TP hit {tp_hits}× — losing setups before they breathe.\n"
                f"  - **Action:** edit `config.yaml` → `stop_loss_atr_mult: {new}`."
            )
        elif tp_hits > sl_hits * 2:
            new = round(cur * 0.85, 2)
            suggestions.append(
                f"🛡️ **`config.yaml: risk.stop_loss_atr_mult = {cur}` is generous.**\n"
                f"  - TP {tp_hits}× vs SL {sl_hits}× — tighten to lock more profit.\n"
                f"  - **Action:** edit `config.yaml` → `stop_loss_atr_mult: {new}`."
            )

    # ── 3. risk.take_profit_atr_mult vs win rate ──
    tp_mult = cfg_params.get("risk.take_profit_atr_mult")
    if tp_mult and total_eval >= 10:
        cur = tp_mult["value"]
        if win_rate < 35 and cur >= 2:
            new = round(cur * 0.75, 2)
            suggestions.append(
                f"🎯 **`config.yaml: risk.take_profit_atr_mult = {cur}` is ambitious.**\n"
                f"  - Win rate {win_rate:.0f}% — TP rarely reached.\n"
                f"  - **Action:** edit `config.yaml` → `take_profit_atr_mult: {new}`. "
                f"More wins, smaller wins, better expectancy."
            )
        elif win_rate > 60 and cur <= 2:
            new = round(cur * 1.25, 2)
            suggestions.append(
                f"🎯 **`config.yaml: risk.take_profit_atr_mult = {cur}` is conservative.**\n"
                f"  - Win rate {win_rate:.0f}% — could ride winners further.\n"
                f"  - **Action:** edit `config.yaml` → `take_profit_atr_mult: {new}`."
            )

    # ── 4. risk_per_trade_pct sanity ──
    risk_pct = cfg_params.get("risk.risk_per_trade_pct")
    if risk_pct and total_eval >= 10:
        cur = risk_pct["value"]
        cum = pd.to_numeric(ev.get("actual_return_pct"), errors="coerce").sum()
        if cum < -5 and cur > 0.5:
            new = round(cur * 0.5, 2)
            suggestions.append(
                f"💰 **`config.yaml: risk.risk_per_trade_pct = {cur}` × negative cumulative {cum:+.1f}% = bleeding.**\n"
                f"  - **Action:** edit `config.yaml` → `risk_per_trade_pct: {new}` until win rate stabilizes."
            )

    # ── 5. Weight rebalance suggestions based on tag/feature performance ──
    weights = {k.split(".")[1]: v["value"] for k, v in cfg_params.items() if k.startswith("weights.")}
    if weights and "tag" in ev.columns:
        tag_perf = ev.dropna(subset=["actual_return_pct"]).groupby("tag").agg(
            n=("ticker", "count"), avg=("actual_return_pct", "mean")
        ).reset_index()
        bad_tags = tag_perf[(tag_perf["n"] >= 3) & (tag_perf["avg"] < -1.5)]
        for _, r in bad_tags.iterrows():
            suggestions.append(
                f"🚫 **Tag `'{r['tag']}'` lost {r['avg']:+.1f}% avg ({int(r['n'])} trades).**\n"
                f"  - **Action:** in `src/scorer.py` add early `return None` for this tag, "
                f"OR adjust `config.yaml: sector.semi_boost / ai_boost` if applicable."
            )

    # ── 6. Score-vs-return correlation → which weights to tune ──
    if "score" in ev.columns and "actual_return_pct" in ev.columns:
        ev_clean = ev.dropna(subset=["score", "actual_return_pct"])
        if len(ev_clean) >= 8:
            corr = ev_clean["score"].corr(ev_clean["actual_return_pct"])
            if pd.notna(corr):
                if corr < -0.1:
                    suggestions.append(
                        f"🚨 **Score INVERSELY correlates with returns ({corr:.2f}).**\n"
                        f"  - **Action:** scoring formula is broken. Open `src/scorer.py` and review "
                        f"`composite_score()` weights — one component likely has the wrong sign."
                    )
                elif corr < 0.15:
                    top_w = sorted(weights.items(), key=lambda x: -x[1])[:3] if weights else []
                    top_str = ", ".join(f"{k}={v}" for k, v in top_w)
                    suggestions.append(
                        f"⚠️ **Score-return correlation weak ({corr:.2f}).** Heaviest weights: {top_str}.\n"
                        f"  - **Action:** experiment in `config.yaml` `weights:` — try halving the largest "
                        f"weight and doubling `sentiment` or `fundamentals`. Compare next week."
                    )
                elif corr > 0.4:
                    suggestions.append(
                        f"✅ **Score predicts returns well (corr={corr:.2f}).** Don't change weights — system is calibrated."
                    )

    # ── 7. Indicator period defaults — suggest A/B ──
    for src_name, params in inventory.items():
        for key, meta in params.items():
            if not isinstance(meta.get("value"), (int, float)):
                continue
            kl = key.lower()
            if "rsi(period)" in kl and meta["value"] == 14:
                suggestions.append(
                    f"🔬 **`{src_name}:{meta['line']}` `rsi(period=14)` is the textbook default.**\n"
                    f"  - **Action:** A/B test by overriding to 7 (faster) or 21 (smoother) in `add_indicators()`."
                )
            if "atr(period)" in kl and meta["value"] < 10:
                suggestions.append(
                    f"🔬 **`{src_name}:{meta['line']}` `atr(period={meta['value']})` may be noisy.**\n"
                    f"  - **Action:** try period=14."
                )

    if not suggestions:
        suggestions.append(
            "✅ No code-level red flags. Strategy operating within expected bounds for current params. Keep accumulating data."
        )
    return suggestions


# ════════════════════════════════════════════════════
# Top-level report
# ════════════════════════════════════════════════════
def report(period_days: int = 7) -> str:
    inventory = inspect_codebase()
    lines = ["## 🔬 Code-Aware Diagnostic"]

    lines.append("\n### 📋 Current strategy parameters")
    if not inventory:
        lines.append("- _No params discovered._")
    else:
        for src_name, params in inventory.items():
            if not params:
                continue
            lines.append(f"\n**`{src_name}`**")
            shown = 0
            for k, meta in params.items():
                if shown >= 12:
                    lines.append(f"- _… +{len(params)-shown} more_")
                    break
                line_ref = f" (line {meta['line']})" if "line" in meta else ""
                lines.append(f"- `{k} = {meta['value']}`{line_ref}")
                shown += 1

    csv = Path("data/picks_log.csv")
    lines.append(f"\n### 🩺 Code-targeted suggestions")
    if not csv.exists():
        lines.append("\n_No picks_log.csv yet._")
        return "\n".join(lines)

    df = pd.read_csv(csv)
    if "pick_date" in df.columns:
        df["pick_date"] = pd.to_datetime(df["pick_date"], errors="coerce")
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=period_days)
        recent = df[df["pick_date"] >= cutoff]
    else:
        recent = df

    evaluated = recent[recent.get("evaluation_status", pd.Series()).isin(["tp_hit", "sl_hit", "closed"])]
    lines.append(f"_(based on last {period_days}d, {len(evaluated)} evaluated trades)_\n")
    for s in diagnose(inventory, evaluated):
        lines.append(f"\n{s}")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    print(report(days))
