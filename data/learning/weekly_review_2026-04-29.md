# 🧠 Weekend Review — 2026-04-29

_⚠️ Gemini free quota exhausted — using local analysis._

---

# 📊 Weekly Local Analysis (7d)

**Period:** 7d  •  **Picks:** 26  •  **Evaluated:** 0  •  **Pending:** 26

_Not enough evaluated trades yet for stats._


## 🏷️ Picks by tag
- SEMI / AI: 20
- SEMI: 6


## 🔬 Code-Aware Diagnostic

### 📋 Current strategy parameters

**`config.yaml`**
- `universe.source = sp500`
- `universe.semiconductors.always_include = True`
- `universe.semiconductors.min_ai_weight = 0.0`
- `universe.min_price = 5.0`
- `universe.max_price = 1500.0`
- `universe.min_avg_volume = 500000`
- `strategy.style = swing`
- `strategy.lookback_days = 180`
- `weights.trend = 0.18`
- `weights.momentum = 0.2`
- `weights.volatility = 0.08`
- `weights.volume = 0.05`
- _… +18 more_

**`src/backtester.py`**
- `backtest_simple(rsi_buy) = 35` (line 8)
- `backtest_simple(rsi_sell) = 70` (line 8)

**`src/cape_ratio.py`**
- `_CAPE_VALUE = 38.5` (line 6)

**`src/data_fetcher.py`**
- `fetch_universe_data(max_workers) = 5` (line 44)

**`src/earnings.py`**
- `earnings_safe(min_days) = 5` (line 37)

**`src/indicators.py`**
- `rsi(period) = 14` (line 18)
- `macd(fast) = 12` (line 26)
- `macd(slow) = 26` (line 26)
- `macd(signal) = 9` (line 26)
- `bollinger(period) = 20` (line 35)
- `bollinger(std) = 2.0` (line 35)
- `atr(period) = 14` (line 41)
- `stochastic(k_period) = 14` (line 55)
- `stochastic(d_period) = 3` (line 55)
- `parabolic_sar(af_start) = 0.02` (line 68)
- `parabolic_sar(af_step) = 0.02` (line 68)
- `parabolic_sar(af_max) = 0.2` (line 68)
- _… +5 more_

**`src/llm_agent.py`**
- `_MIN_INTERVAL = 5.0` (line 38)
- `_gemini_with_retry(max_retries) = 1` (line 111)

**`src/market_news.py`**
- `fetch_market_news(limit) = 40` (line 25)

**`src/news_sentiment.py`**
- `fetch_news(limit) = 5` (line 19)

**`src/parallel_scorer.py`**
- `score_all(max_workers) = 10` (line 38)

**`src/pick_evaluator.py`**
- `MAX_DAYS_OPEN = 20` (line 15)
- `EVAL_LOOKBACK_DAYS = 30` (line 16)

**`src/semiconductors.py`**
- `get_semi_tickers(min_ai_weight) = 0.0` (line 53)

### 🩺 Code-targeted suggestions
_(based on last 7d, 0 evaluated trades)_


📚 Need at least 5 evaluated trades for code-aware diagnosis.

---

Raw observations: 55 this week.