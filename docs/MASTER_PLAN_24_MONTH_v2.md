# 🚀 24-Month Master Plan v2.0 — Daily Stock Agent

> **Version:** 2.0 (replaces April 30 v1.0)
> **Locked:** May 2, 2026 — Singapore
> **Founder:** Anjan Neogi
> **Quit job target:** November 2027 (Month 18)
> **Category leader target:** May 2028 (Month 24)
> **Product launch:** February 2027 (Month 10)

---

## 🎯 NORTH STAR

**The world's only transparent, audited, AI-powered trading agent built for working professionals who want to invest in US stocks but lack time to research.**

Three differentiators no competitor has:
1. **Probability-based decisions** (not arbitrary rules) — see `PROBABILITY_ENGINE_DESIGN.md`
2. **Open source + audited track record** (verifiable, public)
3. **Built BY a working professional FOR working professionals** (lived experience)

---

## 👤 TARGET CUSTOMER (Locked May 2, 2026)

### Primary Persona: "The Time-Starved Professional Investor"

**Who:**
- Working professional, ages 28-50
- Salary $80K-$300K USD/year (or equivalent)
- Has $20K-$500K in investable assets
- Currently invests via: index funds, occasional stock picks, sometimes Robinhood/Webull
- Lives in: Singapore, US, UK, Australia, Hong Kong, India, Canada, EU
- Tech-comfortable but NOT a developer

**Pain points:**
- "I want to beat the market but don't have time to research"
- "I read 20 newsletters and still don't know what to buy"
- "Reddit is noise, Bloomberg is jargon, brokers push their own products"
- "I'm scared of losing money on individual picks"
- "I trust open data more than 'guru' picks"

**What they value:**
- TRANSPARENCY (why this stock?)
- TIME SAVING (5 min decisions, not 5 hours)
- RISK CONTROL (stop losses, position sizing)
- PROVEN TRACK RECORD (not promises)
- COMMUNITY (other smart professionals)

**What they will pay:**
- $30-50/month for Starter (sustainable picks + alerts)
- $80-120/month for Pro (full engine + auto-execute)
- $200-300/month for Elite (multi-asset + custom)

**Channels to reach them:**
- LinkedIn (primary — they live here professionally)
- Twitter/X FinTwit (secondary — finance-curious)
- YouTube long-form (educational content)
- Substack (deep-dive newsletter)
- Singapore tech meetups (founder is here)
- Affiliate via finance YouTubers

---

## 📊 CURRENT STATE (Day 3 — May 2, 2026)

### What's built
- 81 Python files, 10,095 lines of code
- 9 GitHub Actions workflows (automation working)
- 86 PRs merged
- 38 picks logged (9 days of data)
- News pipeline live (266 active signals)
- Backup system live
- Hard enforcement layer live (just shipped)

### What's NOT built (honest)
- Pillar 2 (Trust/Transparency): 0% — no public dashboard, no audit
- Pillar 3 (Community): 0% — no Twitter, no LinkedIn posts, no Substack
- Pillar 4 (Business): 0% — no Alpaca paper trading integration, no domain
- Probability engine: 0% — using rule-based thresholds
- Self-learning: 0% — no learning loop yet
- Test coverage: 15% (need 40%+)

### Honest score by pillar
| Pillar | Plan said by Day 7 | Reality Day 3 | Score |
|---|---|---|---|
| Technical | 25 PRs done | 41 features built | 🟢 Ahead but unmeasured |
| Trust | Public dashboard | Nothing | 🔴 0/10 |
| Community | Twitter live | Not created | 🔴 0/10 |
| Business | Alpaca + domain | Not started | 🔴 0/10 |

**The gap:** All progress is technical. Zero progress on customer-facing pillars.

---

## 🏛️ FOUR PILLARS (Re-Locked)

### Pillar 1: TECHNICAL EXCELLENCE
Be objectively better via probability engine + self-learning + multi-LLM reasoning.

### Pillar 2: TRUST & TRANSPARENCY
Public live dashboard, audited track record, open source core, every decision auditable.

### Pillar 3: COMMUNITY & EDUCATION
Working-professional-focused content. Build in public on LinkedIn (primary) + Twitter (secondary).

### Pillar 4: SUSTAINABLE BUSINESS
$840K+ ARR by Month 24, 800+ paying customers, profitable from Month 12.

---

## 📅 12-PHASE ROADMAP (Months 1-24)

### PHASE 1 (Months 1-2): STABILIZE + PROBABILITY FOUNDATION
**May-June 2026**

**Tech goals:**
- [ ] Fix all 4 known bugs (penny stock, evals, regime, ticker cooldown)
- [ ] Build Probability Engine Phase 1 (stock_stats per ticker)
- [ ] Build Probability Engine Phase 2 (regime-conditional levels)
- [ ] Integrate Alpaca PAPER TRADING (real fills, slippage)
- [ ] Add SPY/sector benchmark to every pick
- [ ] "No trade today" capability when no edge

**Trust goals:**
- [ ] Public GitHub Pages dashboard (live picks + performance)
- [ ] Open-source the entire repo

**Community goals:**
- [ ] LinkedIn account active, 12 posts (3/week × 4 weeks)
- [ ] Twitter account active, 30 posts (daily auto-pick + 2x/week thoughts)
- [ ] First Substack post: "Why I'm Building This in Public"
- [ ] Domain reserved + landing page (single page)

**Business goals:**
- [ ] Alpaca paper account integrated end-to-end
- [ ] Email waitlist signup (target 50 signups by end M2)

**Deliverable:** Stable, measured, probability-based agent + public presence.

---

### PHASE 2 (Months 3-4): VALIDATION + UNIQUE EDGE
**July-August 2026**

**Tech goals:**
- [ ] Probability Engine Phase 3 (hypothesis testing engine)
- [ ] Probability Engine Phase 4 (algorithm self-awareness)
- [ ] Backtest engine (5+ years walk-forward)
- [ ] Wisdom Base v1 (10 trading books extracted into rules)
- [ ] Moomoo SG L2 + capital flow data integration (unique edge)
- [ ] Multi-LLM ensemble (Claude + GPT-5 + Gemini consensus)

**Trust goals:**
- [ ] 60-day Alpaca paper track record published
- [ ] Backtest results published with methodology
- [ ] Stage 1 Gate review (publish results honestly)

**Community goals:**
- [ ] LinkedIn: 36 posts cumulative (3/week)
- [ ] Twitter: 90 posts cumulative + first viral thread
- [ ] YouTube channel launched (4 videos)
- [ ] Substack: 8 posts cumulative
- [ ] First 200 LinkedIn followers, 100 Twitter, 50 newsletter

**Business goals:**
- [ ] Email waitlist 200+ signups
- [ ] Founder pricing reservation system

**Deliverable:** Probability engine fully operational + audience seeding.

**STAGE 1 GATE (End Month 3):**
- ✅ 60 days Alpaca paper, capture efficiency ≥60%, win rate ≥45%, beats SPY by 2%+
- ❌ If fail → Phase 2 extends to fix engine before Phase 3

---

### PHASE 3 (Months 5-6): REAL MONEY + ALPHA TESTERS
**September-October 2026**

**Tech goals:**
- [ ] Self-learning engine v1 (nightly Claude review + auto-tune weekly)
- [ ] A/B testing harness for strategy variants
- [ ] Adaptive position sizing (Kelly variant, capped at quarter-Kelly)
- [ ] Crypto module (BTC/ETH/SOL — small slice)

**Trust goals:**
- [ ] Open Moomoo real-money account ($5K SGD)
- [ ] Begin live trade journaling publicly
- [ ] Stage 2 begins (real money 60-day clock)

**Community goals:**
- [ ] LinkedIn: 60 posts cumulative
- [ ] First viral LinkedIn post (target 1000+ reactions)
- [ ] YouTube: 10 videos, 200 subscribers
- [ ] Substack: 16 posts, 200 subscribers
- [ ] 10 alpha testers onboarded (free tier, FinTwit + LinkedIn)

**Business goals:**
- [ ] Methodology whitepaper v1 (30+ pages, free PDF)
- [ ] Discord community launched (alpha testers)
- [ ] Begin testing pricing/positioning with alphas

**Deliverable:** Real-money track record begins + alpha tester feedback loop.

---

### PHASE 4 (Months 7-9): SaaS PLATFORM BUILD
**November 2026 - January 2027**

**Tech goals:**
- [ ] Multi-tenant Postgres backend (per-user data isolation)
- [ ] FastAPI + JWT authentication + 2FA
- [ ] Per-user broker connections (encrypted)
- [ ] Per-user Telegram bot tokens
- [ ] Background job scheduler (Celery)
- [ ] Next.js frontend (Tailwind + Chart.js)
- [ ] Web dashboard (picks, performance, settings)
- [ ] Stripe billing integration
- [ ] Tiered pricing logic + feature gates

**Trust goals:**
- [ ] 60-day Moomoo real-money track record published
- [ ] Stage 2 Gate review
- [ ] Independent audit hired ($2-5K, 12-month track record verification)

**Community goals:**
- [ ] LinkedIn: 108 posts cumulative
- [ ] YouTube: 20 videos, 500 subscribers
- [ ] Substack: 28 posts, 500 subscribers
- [ ] Twitter: 270 posts, 1,500 followers
- [ ] 25 alpha testers actively using

**Business goals:**
- [ ] Email waitlist 500+ signups
- [ ] Founder pricing locked for first 50 customers
- [ ] Soft launch end of Month 9

**Deliverable:** SaaS platform live + soft launch with first paying customers.

**STAGE 2 GATE (End Month 6):**
- ✅ 60 days Moomoo real $, capture efficiency ≥50%, beats SPY by 1%+
- ❌ If fail → Phase 4 SaaS build delayed, more tuning

---

### PHASE 5 (Months 10-12): PUBLIC LAUNCH
**February-April 2027**

**Tech goals:**
- [ ] Real-time intelligence (WebSocket streaming)
- [ ] News firehose (Alpaca + Yahoo + Benzinga, <30 sec classification)
- [ ] Twitter/X sentiment integration
- [ ] Discord/Reddit retail sentiment
- [ ] Earnings call transcript LLM analysis
- [ ] SEC 8-K filing alerts (<5 min)
- [ ] Mobile PWA (responsive web first, native later)

**Trust goals:**
- [ ] Audit report published
- [ ] Public live dashboard with 12-month track record
- [ ] Transparency report (winners, losers, mistakes)

**Community goals:**
- [ ] LinkedIn: 156 posts cumulative, 1,000+ followers
- [ ] YouTube: 36 videos, 1,500 subscribers
- [ ] Substack: 44 posts, 1,500 subscribers
- [ ] Twitter: 4,000+ followers
- [ ] First press hits (Singapore tech publications)

**Business goals (Month 10 LAUNCH):**
- [ ] Product Hunt launch
- [ ] LinkedIn launch post (target 5K+ impressions)
- [ ] Reddit r/algotrading mega-post (with disclaimers)
- [ ] Email blast to waitlist
- [ ] First 100 paying customers (target by Month 12)
- [ ] $5K MRR by Month 12

**Deliverable:** Public launch + first $5K MRR.

**STAGE 3 GATE (End Month 12):**
- ✅ $5K+ MRR, <10% monthly churn, 100+ paying users, audited record
- ❌ If fail → pivot or pause SaaS, optimize current offering

---

### PHASE 6 (Months 13-15): RETENTION + OPTIMIZATION
**May-July 2027**

**Tech goals:**
- [ ] Risk management 2.0 (correlation matrix, hedging suggestions)
- [ ] Drawdown circuit breakers
- [ ] Tax-loss harvesting helper (US accounts)
- [ ] Multi-broker support (Alpaca + Moomoo + IBKR)
- [ ] Voice query (Telegram + mobile)

**Trust goals:**
- [ ] 18-month track record live
- [ ] Customer testimonials (with permission)

**Community goals:**
- [ ] LinkedIn: 4,000+ followers
- [ ] YouTube: 5,000+ subscribers
- [ ] Substack: 3,000+ subscribers
- [ ] First conference talk (FinTech Singapore meetup)

**Business goals:**
- [ ] $15K MRR by Month 15
- [ ] 200+ paying customers
- [ ] Affiliate program launched (30% recurring)
- [ ] First 5 affiliate partners

**Deliverable:** Sustainable growth, retention >90% monthly.

---

### PHASE 7 (Months 16-18): SCALE + QUIT JOB
**August-November 2027**

**Tech goals:**
- [ ] Native mobile app (React Native iOS + Android)
- [ ] Custom strategy builder (UI for advanced users)
- [ ] B2B Enterprise tier ($999/mo for family offices)
- [ ] White-label dashboard option

**Trust goals:**
- [ ] 24-month track record
- [ ] Industry recognition pursuit (Bloomberg, CNBC pitches)

**Community goals:**
- [ ] LinkedIn: 8,000+ followers
- [ ] YouTube: 10,000+ subscribers
- [ ] Substack: 5,000+ subscribers
- [ ] Speaking at AlgoTraderConf

**Business goals:**
- [ ] $25K MRR by Month 18
- [ ] 350+ paying customers
- [ ] **🎯 QUIT JOB MILESTONE (Month 18)**
  - $20K+ MRR for 3 consecutive months
  - 6-month emergency fund saved (S$60K-100K)
  - Spouse/family aligned
  - Singapore visa/legal sorted
- [ ] Hire first part-time contractor (VA or junior dev)

**Deliverable:** Quit job, become full-time founder.

---

### PHASE 8 (Months 19-21): TEAM + INTERNATIONAL
**December 2027 - February 2028**

**Tech goals:**
- [ ] Asia-Pacific stock support expanded (HK, JP, AU)
- [ ] Localization (Chinese, Japanese landing pages)
- [ ] API tier for power users / B2B

**Business goals:**
- [ ] First hire: Customer Success ($3-5K SGD/mo, remote)
- [ ] Second hire: Content Creator (YouTube/podcast)
- [ ] Paid acquisition testing ($1K Twitter, $500 Reddit, $1K YouTube)
- [ ] Singapore office space (co-working initially)
- [ ] $40K MRR by Month 21

**Community:**
- [ ] LinkedIn: 12,000+ followers
- [ ] Daily YouTube Shorts launched
- [ ] Podcast launched

**Deliverable:** First hires, international expansion, $40K MRR.

---

### PHASE 9 (Months 22-24): CATEGORY LEADERSHIP
**March-May 2028**

**Tech goals:**
- [ ] Options scoring module
- [ ] Forex module (for international users)
- [ ] Advanced backtesting UI for users

**Business goals:**
- [ ] $70K+ MRR by Month 24 (= $840K ARR)
- [ ] 800+ paying customers
- [ ] Press features (Bloomberg, CNBC, TechCrunch pitches)
- [ ] Conference sponsorships
- [ ] **STRATEGIC OPTIONS DECISION:**
  - Option A: Acquisition discussions ($5-15M target)
  - Option B: Series A consideration ($3-5M at $30-50M val)
  - Option C: Stay independent, optimize for profit

**Community:**
- [ ] LinkedIn: 20,000+ followers
- [ ] YouTube: 25,000+ subscribers
- [ ] Substack: 10,000+ subscribers
- [ ] Industry recognition (Bloomberg/CNBC mention)

**Deliverable:** Best-in-market product, optionality on next chapter.

---

## 💰 REVENUE TRAJECTORY

| Month | Phase | Customers | MRR | ARR | Cumulative Cash |
|---|---|---|---|---|---|
| 1-2 | Stabilize | 0 | $0 | $0 | -$200 (domain, tools) |
| 3-4 | Validate | 0 | $0 | $0 | -$500 |
| 5-6 | Real $ | 10 free | $0 | $0 | -$1.5K (audit) |
| 7-9 | SaaS build | 25 | $725 | $8.7K | $0 net |
| 10-12 | Launch | 100 | $5K | $60K | +$15K |
| 13-15 | Optimize | 200 | $15K | $180K | +$80K |
| 16-18 | **Quit job** | 350 | $25K | $300K | +$200K |
| 19-21 | Hire/scale | 500 | $40K | $480K | +$400K |
| 22-24 | **Category leader** | 800 | $70K | $840K | +$700K |

**Year 3 projection:** 2,500 customers, $200K MRR, $2.4M ARR.

---

## 🎯 PRICING TIERS (Locked)

### FREE — "The Honest Demo"
- 1 daily pick (24-hour delayed)
- Public track record access
- Open source self-host
- Community Discord access

### STARTER — $39/mo
- Real-time picks (5/day)
- Telegram alerts
- Daily/weekly/monthly reports
- Watchlist + news scoring
- Basic exits (TP1/SL only)

### PRO — $99/mo ⭐ MOST POPULAR
- Everything in Starter
- Full 5-layer adaptive exits
- Auto-execute (Alpaca, Moomoo, IBKR)
- Backtest engine access
- LLM reasoning per pick
- Capital flow + UOA signals
- Self-tuning suggestions

### ELITE — $249/mo
- Everything in Pro
- Multi-asset (stocks + options + crypto)
- Custom strategy builder
- Priority Discord (founder access)
- Monthly 1-on-1 review call
- Early feature access

### ENTERPRISE — $999/mo (Month 17+)
- White-label dashboard
- Custom strategies
- Dedicated support + SLA
- For hedge funds, family offices

**Discounts:**
- Annual: 2 months free (16% off)
- Lifetime: $1,499 (first 100 users only)
- Affiliate: 30% recurring commission
- Founder pricing: $29/mo locked for first 25 users

---

## 📅 WEEKLY OPERATING RHYTHM (Locked)

### Daily (10 min)
- 9 AM SGT: Read overnight Telegram (premarket intel)
- 9:05 AM SGT: Auto-tweet morning picks
- 6 PM SGT: Read evening exec X-ray
- 6:05 PM SGT: Auto-tweet evening results
- 6:30-7:30 PM: Build session (1 hour, 5 days/week)

### Weekly (Sunday, 90 min)
- 8 AM: Read weekly digest (auto-generated)
- 9 AM: Apply 0-2 small tunings (high confidence only)
- 10 AM: LinkedIn long-form post
- 11 AM: Plan next week's PRs
- 12 PM: REST — rest of Sunday off

### Monthly (1st Saturday, 3 hr)
- Read monthly review
- Strategic decisions (1-3 PRs queued)
- Substack monthly results post
- YouTube monthly recap video
- Update public dashboard
- Personal review: am I burning out?

### Quarterly (1 day off, full review)
- Tech, trust, community, business pillar review
- Adjust 24-month plan if needed
- Plan 2-week vacation (mandatory)

---

## 🚨 STAGE GATES (Mandatory, Cannot Skip)

### Gate 1 (End Month 3): Engine Validation
**Pass criteria:**
- 60 days Alpaca paper trading complete
- Capture efficiency ≥60%
- Win rate ≥45%
- R-multiple ≥1.3
- Beats SPY by 2%+
- Max drawdown <15%

**If pass:** Proceed to Stage 2 (real money $5K Moomoo)
**If fail:** Spend Month 4 on engine tuning, retry

### Gate 2 (End Month 6): Real-Money Validation
**Pass criteria:**
- 60 days Moomoo real $5K
- Capture efficiency ≥50% (real fills harder)
- Win rate ≥45%
- R-multiple ≥1.2
- Beats SPY by 1%+
- No catastrophic loss (>20% drawdown)

**If pass:** Proceed to Phase 4 (SaaS build)
**If fail:** More tuning, no SaaS yet

### Gate 3 (End Month 12): Market Validation
**Pass criteria:**
- $5K+ MRR
- <10% monthly churn
- 50+ paying customers
- Audited 12-month track record
- NPS ≥40

**If pass:** Year 2 scale plan
**If fail:** Pivot positioning OR optimize current cohort

### Gate 4 (Month 18): Quit Job Decision
**Pass criteria:**
- $20K+ MRR for 3 consecutive months
- 6-month emergency fund (S$60K-100K)
- <5% monthly churn
- Spouse/family aligned
- Singapore tax/visa sorted

**If pass:** **QUIT JOB**, full-time founder
**If fail:** Wait until Month 24 or adjust plan

---

## ⚠️ RISK REGISTER + MITIGATIONS

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| 🔴 Burnout | HIGH | KILL | Weekly REST day. Quarterly vacation. Therapist by Month 6. |
| 🔴 Bad market period | MEDIUM | HARM | Show drawdowns honestly. Hedging features. Educate users. |
| 🔴 Regulatory issues | LOW | KILL | Frame as "research tool". MAS-friendly. Lawyer at Month 9. |
| 🟡 Big competitor copies | MEDIUM | HARM | Move faster. Open source = commoditize their copy. |
| 🟡 Can't sustain content | MEDIUM | HARM | Daily auto-tweets. VA hire at Month 12. Schedule it. |
| 🟡 Probability engine overfits | MEDIUM | HARM | Strict train/test discipline. Walk-forward only. 95% CIs. |
| 🟡 Working professional don't pay $99 | MEDIUM | HARM | Test pricing in Phase 3 alphas. Adjust if needed. |
| 🟡 Singapore base limits US customer trust | LOW | HARM | Independent audit. US testimonials. |

---

## 🏆 PRODUCT FEATURE MATRIX (Month 24 Target)

| Category | Us | Best Competitor | Status |
|---|---|---|---|
| Probability-based decisions | ✅ | ❌ | UNIQUE 🏆 |
| Per-decision audit trail | ✅ | ❌ | UNIQUE 🏆 |
| Multi-LLM ensemble | ✅ | ⚠ partial | LEADER 🏆 |
| Self-learning engine | ✅ | ⚠ basic | LEADER 🏆 |
| Open source core | ✅ | ❌ | UNIQUE 🏆 |
| Capital flow data (SG L2) | ✅ | ❌ | UNIQUE 🏆 |
| Multi-asset breadth | ✅ | ⚠ stocks | LEADER 🏆 |
| Multi-broker support | ✅ | ⚠ 1-2 | LEADER 🏆 |
| Backtest engine | ✅ | ✅ | TIE |
| Auto-execute | ✅ | ✅ | TIE |
| Mobile app | ✅ | ✅ | TIE |
| Charts | ⚠ | 🏆 TradingView | BEHIND (don't compete) |
| Brand recognition | 🟡 | 🏆 | BEHIND (Year 3+) |
| Customer count | 🟡 | 🏆 | BEHIND (catching up) |

**Goal: Best in market on 8 dimensions, tie on 3, behind on 3 (acceptable).**

---

## 🤝 WORKING AGREEMENT

### Founder commits to:
- Daily build session (1 hr, 5 days/week)
- Weekly LinkedIn post (Sunday morning)
- Daily Twitter auto-post (5 min)
- Stage gate discipline (don't skip)
- Sunday afternoon + Saturday evening = REST
- Quarterly 2-week vacation (mandatory)
- Therapist starting Month 6 (mental health)

### AI co-pilot commits to:
- Read `docs/CONTEXT.md` first every session
- Push back on bad ideas (honest co-founder voice)
- Document everything in repo (memory > chat)
- Reference architecture decisions before coding
- Help draft LinkedIn/Twitter content
- Anti-overfitting discipline enforcement

---

## 🎯 IMMEDIATE NEXT 7 DAYS (May 2-8)

### This weekend (May 2-3) — Sprint
- [x] Save all docs to repo (CONTEXT, ROADMAP, ADR, this plan)
- [ ] Fix BUG-4 (ticker cooldown, no TSM 3× in week)
- [ ] Add SPY benchmark column to picks_log
- [ ] Build Probability Engine Phase 1 (stock_stats foundation)
- [ ] Open Twitter/X account (reserve handle)
- [ ] Open Substack account
- [ ] Reserve domain name

### Next week (May 4-8) — Daily build (1 hr/day)
- Mon: Bug investigation + commit (after work)
- Tue: Probability Engine Phase 2 start
- Wed: Probability Engine Phase 2 finish + tests
- Thu: First LinkedIn post draft + publish
- Fri: First Substack post + plan weekend

### Next weekend (May 9-10) — Probability Engine Phase 2
- Sat: Regime-conditional levels integration
- Sun: First public picks tweet + LinkedIn post

---

## 📞 QUICK REFERENCE

| Item | Value |
|---|---|
| Customer | Working professionals, $80-300K salary, want to invest US stocks but no time |
| Pricing | $39 / $99 / $249 / $999 |
| Quit job | Month 18 ($20K MRR consistent for 3 months) |
| Category leader | Month 24 ($70K MRR, 800 customers) |
| Total PRs target | #87-187 (100 over 24 months, ~4/month) |
| Tests target | 12 → 1,000+ by Month 24 |
| LinkedIn target | 0 → 20,000 followers by Month 24 |
| Open source | Yes — entire core, from Day 1 |

---

## 🔄 REVISION HISTORY

- **v1.0 (April 30, 2026):** Original plan, 100 features over 24 months
- **v2.0 (May 2, 2026):** Reset based on Day 3 honest audit
  - Probability engine added as architectural core
  - Customer persona locked: working professionals
  - Trust/Community/Business pillars properly weighted
  - LinkedIn elevated to primary channel (was Twitter)
  - Wisdom Base feature added (unique differentiator)
  - Realistic capacity: 1 hr/day weekday + weekends

---

*Living document. Update after every major decision or quarterly review.*
*Next revision: End of Month 3 (Stage 1 Gate review, August 2026).*

— Anjan Neogi, Singapore, May 2, 2026