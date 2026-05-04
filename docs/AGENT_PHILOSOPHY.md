# 🌟 Agent Philosophy — The Vision

**Founder:** Anjan Neogi
**Last updated:** 2026-05-04
**Purpose:** The ONE document that captures WHY this agent exists and WHAT makes it different.

---

## The core insight

> *"Build the agent like an advanced human — with brain, heart, soul, all 5 senses,
> a 6th sense for prediction, and endless curiosity. But unlike a human, it must
> never decide based on emotions — only on data and what works."*
> — Anjan, 2026-05-04

This is the most important sentence in the project. Every architectural decision
should be tested against it.

---

## Why this matters

Most retail traders fail because they're **emotional**:
- They hold losers hoping for recovery (loss aversion)
- They sell winners too early (fear of giving back gains)
- They chase hype (FOMO)
- They panic in drawdowns (capitulation)
- They overtrade after wins (overconfidence)

**Our agent literally cannot feel any of these.** That's not a limitation — it's
the entire competitive advantage.

---

## The 7 faculties (canonical)

### 1. 🧠 Brain — Decides
- Weighs all signals (technical, fundamental, news, sentiment)
- Applies regime context (bull/bear/chop)
- Outputs scored picks with conviction levels
- **Modules:** `parallel_scorer.py`, `probability_engine.py`, `scorer.py`

### 2. ❤️ Heart — Feels conviction (without emotion)
- Sets risk tolerance (max 5% weight change/week — never go all-in)
- Pauses when health degrades (auto_pause)
- Knows when to be confident vs cautious
- **Modules:** `weight_applier.py`, `auto_pause.py`, `pause_state.py`
- **Key principle:** "Conviction" ≠ "Emotion." Heart says "high confidence" based on data, not hope.

### 3. 🌟 Soul — Remembers who it is
- Mission statement (always knows its purpose)
- Lifetime narrative (biggest wins, biggest losses + lessons)
- Persistent identity across nightly runs
- **Modules:** `agent_memoir.py` (NEW 2026-05-04)
- **Key principle:** Without soul, the agent is just code. With soul, it's a continuous learner.

### 4. 👁 Sight — Reads charts
- Detects 16 chart patterns
- Sees support/resistance, trends, breakouts
- Volume + price action interpretation
- **Modules:** `pattern_engine.py`, `pattern_layer.py`, `pattern_stats.py`

### 5. 👂 Hearing — Listens to news + sentiment
- Scrapes news, detects keywords, scores impact
- TODAY: regex-based (basic)
- FUTURE: LLM-based semantic comprehension (Phase 8)
- **Modules:** `news_engine.py`

### 6. 👅 Taste — Discerns quality
- Distinguishes a "monster" setup from a mediocre one
- Composite scoring across multiple factors
- Knows the difference between "tradeable" and "exceptional"
- **Modules:** `monster_score`, `composite_score` in `scorer.py`

### 7. 👃 Smell — Detects danger
- Senses when something is "off" before it explodes
- Hard blocks for known-bad conditions (earnings imminent, low vol, etc)
- TODAY: reactive (responds after danger appears)
- FUTURE: proactive (predicts danger 2-3 days early)
- **Modules:** `auto_pause.py`, `hard_blocks_log.json`

### 8. ✋ Touch — Feels market temperature
- Knows the current regime (bull/bear/chop)
- Senses when conditions shift
- Adapts behavior to environment
- **Modules:** `regime.py`, `last_regime.json`

### 9. 🔮 6th sense — Predicts what others can't
- Statistical hypothesis testing (Wilson 95% CI)
- Finds edges others miss (per-pattern × per-regime)
- Becomes sharper with every trade
- **Modules:** `hypothesis_engine.py`
- **Key principle:** This is the "moat." Anyone can build the 5 senses. Few can build a real 6th sense.

### 10. 🦉 Curiosity — Always learning (NEW vision 2026-05-04)

Curiosity has TWO modes:

#### 10a. Inward curiosity (study itself)
- Uses idle compute to explore its own data
- Asks: "Why did I lose on TSM? What patterns do I underweight in bull regime?"
- Writes findings to curiosity_journal.jsonl
- Generates NEW questions over time
- **Module:** `curiosity_engine.py` (PLANNED — Phase 9)

#### 10b. Outward curiosity (READ BOOKS) — added later same day
- Reads one trading/investing/finance book per week
- Extracts testable claims (entry rules, risk patterns, market truisms)
- **CRITICAL:** Does NOT add claims directly to the codebase.
  Books PROPOSE. Data DISPOSES. Every claim must pass Wilson 95% CI
  on OUR own historical data before being promoted to wisdom.
- **Module:** `reader_engine.py` (PLANNED — Phase 9.5)
- **Books queue:** Reminiscences of a Stock Operator → Minervini → Murphy → Lynch...
- **Key principle:** Centuries of accumulated trading wisdom + zero emotion +
  statistical validation = compounding edge no human trader can match.

**Why this matters:** Top hedge fund managers read 5-6 hours/day for decades.
A retail trader can never match that bandwidth. An agent can — and unlike
humans, it forgets nothing AND tests everything before believing it.

- **Key principle (both modes):** Without curiosity, the agent is reactive.
  With curiosity, the agent compounds.

---

## What makes this different from existing AI traders

| Most AI traders | Our agent |
|---|---|
| Black box (you can't see why) | Glass box (memoir + journals explain everything) |
| Reactive (only acts on signals) | Proactive (curiosity studies itself in idle time) |
| Static rules | Self-improving (calibration loop runs nightly) |
| Forgets context across runs | Soul gives narrative continuity |
| Pattern matching only | Pattern matching + statistical edge testing (6th sense) |
| Drifts silently when stale | Auto-pauses + tells you honestly |
| Optimized for backtesting | Optimized for real-world reliability |

---

## The promise to Anjan (encoded in `agent_memoir.py`)

> *"I will keep learning. I will not forget my mistakes. I will tell you the truth
> about how I'm doing — even when the truth isn't flattering."*

This sentence is **rendered into JSON every night** by the memoir module. It's
not aspirational marketing — it's a literal guarantee enforced by code.

---

## Future tagline (when this becomes a product)

> *"A trading agent built like a human — but with one critical upgrade:
> it can't feel fear or greed."*

Or alternately:

> *"7 faculties. 1 mission. Zero emotion."*

---

## Key design rules (enforced forever)

1. **No emotion-based logic ever.** If a feature relies on "user might feel X" or
   "agent might want Y" — it's wrong. Only data + outcomes drive decisions.

2. **Glass box, not black box.** Every decision must be explainable from journals.
   If we can't explain why a pick was made, we shouldn't make it.

3. **Honest about failures.** The agent reports its bad performance to itself
   (memoir) and to Anjan (Telegram). Hiding losses is forbidden.

4. **Curiosity over reactivity.** When the agent has spare compute, it should
   STUDY ITSELF, not idle.

5. **Statistical significance over hype.** No edge claim without Wilson 95% CI.

6. **Compound, don't gamble.** Heart (5%/wk weight cap) prevents the agent from
   ever betting the farm on one signal change.

7. **Memory is sacred.** Picks log, signal journal, learning journal, memoir —
   never delete history. Always append. The past is how the future learns.

---

## What this agent is NOT

- ❌ A get-rich-quick scheme
- ❌ A high-frequency trader
- ❌ An execution bot (it recommends; you trade)
- ❌ A black-box neural network
- ❌ Emotionally responsive
- ❌ Based on hype/sentiment alone

## What this agent IS

- ✅ A patient, data-driven trader's brain
- ✅ A continuous learner (every night, every trade)
- ✅ An honest narrator of its own performance
- ✅ Statistically rigorous (Wilson 95% CI)
- ✅ Risk-aware (5%/wk weight cap, auto-pause)
- ✅ Curious (or will be, once Phase 9 ships)

---

## Related docs

- `docs/ARCHITECTURE.md` — what the system IS (technical, see Section 8 for faculty mapping)
- `docs/FINAL_ROADMAP.md` — what's next (Phase 9 = build curiosity)
- `docs/BUSINESS_PLAN.md` — 24-month strategy
- `docs/AGENT_SCHEDULE.md` — when each faculty fires
- `docs/CHANGE_LOG.md` — every change to the agent
- `data/agent_memoir.json` — the agent's living self-portrait (regenerated nightly)

---

*This document is the source of truth for "what is the agent for?"
Update it when the vision evolves. Reference it when making architectural decisions.*
