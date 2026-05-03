# 📋 Next Session Queue

## Mon May 4
- [ ] Watch first daily run with all new pillars active
- [ ] Verify Telegram includes pause signal + sector_etf
- [ ] Eyeball data/signal_journal.jsonl after run
- [ ] Eyeball data/wisdom/ for unexpected mutations

## Wed May 6
- [ ] Flip auto-pause observe → enforce
- [ ] Add early-return in main.py if score >= 8

## Sun May 10
- [ ] First real weekly self-assessment from full 7d window

## Backlog
- Migrate picks_log.csv → SQLite (1000+ rows incoming)
- Pillar 4: auto-flip wisdom patterns into composite weights
- Pillar 6: equity curve PNG in quarterly report
- CI workflow on push (currently manual pytest)

## Do NOT
- ❌ Re-introduce blanket sector boosts
- ❌ Auto-flip patterns below 30 samples / p<0.05
- ❌ Add universe tickers without backtester validation
