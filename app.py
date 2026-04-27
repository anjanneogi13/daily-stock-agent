"""Streamlit dashboard."""
import streamlit as st
import pandas as pd
import yaml
import plotly.graph_objects as go
from dotenv import load_dotenv

from src.universe import get_universe
from src.data_fetcher import fetch_universe_data, fetch_info
from src.indicators import add_indicators, latest_signals
from src.fundamentals import score_fundamentals, passes_filters
from src.news_sentiment import fetch_news, score_sentiment
from src.scorer import composite_score
from src.risk_manager import trade_plan
from src.llm_agent import explain_pick
from src.tracker import performance_summary
from src.semiconductors import is_semi, get_semi_tickers

load_dotenv()
st.set_page_config(page_title="Daily Stock Picker", layout="wide")
st.title("Daily Stock Picker Agent")
st.caption("Educational only. Not financial advice. Paper-trade first.")

@st.cache_data(ttl=600)
def load_cfg():
    with open("config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)

cfg = load_cfg()

with st.sidebar:
    st.header("Settings")
    top_n = st.slider("Top picks", 3, 20, cfg["output"]["top_n_picks"])
    min_score = st.slider("Min score", 0.0, 1.0, cfg["output"]["min_score"], 0.05)
    semis_only = st.checkbox("Semiconductors only", value=False)
    ai_focus = st.checkbox("AI-relevant semis only (>=0.75)", value=False)
    run_btn = st.button("Run Agent", type="primary")
    st.divider()
    st.subheader("Performance")
    for k, v in performance_summary().items():
        st.write(f"**{k}:** {v}")

if run_btn:
    if semis_only:
        tickers = get_semi_tickers(min_ai_weight=0.75 if ai_focus else 0.0)
    else:
        tickers = get_universe(cfg)
    with st.spinner(f"Fetching {len(tickers)} tickers..."):
        data = fetch_universe_data(tickers, period=f"{cfg['strategy']['lookback_days']}d")
    progress = st.progress(0)
    candidates = []
    for i, (tk, df) in enumerate(data.items()):
        progress.progress((i + 1) / len(data))
        d = add_indicators(df); sig = latest_signals(d)
        if not sig.get("close"): continue
        info = fetch_info(tk)
        if not passes_filters(info, cfg): continue
        fund = score_fundamentals(info)
        news = fetch_news(tk, limit=5); sent = score_sentiment(news)
        scores = composite_score(sig, fund, sent, cfg["weights"],
                                 ticker=tk, sector_cfg=cfg.get("sector", {}))
        if scores["composite"] < min_score: continue
        plan = trade_plan(sig, cfg)
        candidates.append({"ticker": tk, "scores": scores, "plan": plan,
                           "news": news, "df": d,
                           "name": info.get("shortName", tk),
                           "sector": info.get("sector", "N/A")})
    candidates.sort(key=lambda x: x["scores"]["composite"], reverse=True)
    top = candidates[:top_n]
    st.success(f"{len(candidates)} candidates -> top {len(top)}")
    st.metric("Semi picks in top list",
              f"{sum(1 for p in top if is_semi(p['ticker']))} / {len(top)}")
    rows = [{"Ticker": p["ticker"], "Tag": p["scores"].get("sector_tag") or "",
             "Name": p["name"], "Sector": p["sector"],
             "Score": p["scores"]["composite"],
             "Entry": p["plan"].get("entry"), "SL": p["plan"].get("stop_loss"),
             "TP": p["plan"].get("take_profit"),
             "R:R": p["plan"].get("risk_reward"),
             "Qty": p["plan"].get("quantity")} for p in top]
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    for p in top:
        with st.expander(f"{p['ticker']} - {p['name']} (Score: {p['scores']['composite']:.2f})"):
            c1, c2 = st.columns([2, 1])
            with c1:
                df = p["df"].tail(90)
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index, open=df["open"], high=df["high"],
                    low=df["low"], close=df["close"], name=p["ticker"])])
                if "sma_20" in df: fig.add_trace(go.Scatter(x=df.index, y=df["sma_20"], name="SMA20"))
                if "sma_50" in df: fig.add_trace(go.Scatter(x=df.index, y=df["sma_50"], name="SMA50"))
                fig.update_layout(height=400, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.write("**Score Breakdown**")
                for k, v in p["scores"].items():
                    if isinstance(v, (int, float)) and k not in ("composite","raw_score","sector_mult"):
                        st.progress(min(float(v), 1.0), text=f"{k}: {v:.2f}")
                st.write("**Trade Plan**"); st.json(p["plan"])
            st.write("**Rationale**")
            st.write(explain_pick(p["ticker"], p["scores"], p["plan"], p["news"], cfg["llm"]["model"]))
            st.write("**Recent News**")
            for n in p["news"][:3]:
                st.markdown(f"- [{n['title']}]({n['link']})")
else:
    st.info("Click Run Agent in the sidebar to start.")
