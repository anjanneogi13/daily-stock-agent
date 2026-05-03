# ═══════════════════════════════════════════════════════════════
# daily-stock-agent — developer & ops shortcuts
# ═══════════════════════════════════════════════════════════════
# Usage:  make help
.DEFAULT_GOAL := help

PY := python3

# ─── Help ──────────────────────────────────────────────────────
.PHONY: help
help:  ## Show this help
	@echo ""
	@echo "📋 Available targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
	  awk 'BEGIN{FS=":.*?##"} {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ─── Tests ─────────────────────────────────────────────────────
.PHONY: test test-fast test-cov
test:       ## Run full test suite
	$(PY) -m pytest tests/ -q
test-fast:  ## Run tests, stop on first failure
	$(PY) -m pytest tests/ -x -q
test-cov:   ## Run tests with coverage summary
	$(PY) -m pytest tests/ --cov=src --cov-report=term-missing -q

# ─── Wisdom ops ────────────────────────────────────────────────
.PHONY: wisdom-preview wisdom-promote wisdom-dryrun wisdom-stats wisdom-gc wisdom-gc-dryrun
wisdom-preview:  ## Preview hints that would surface on today's picks
	@echo "🔮 Wisdom hint preview"
	@echo "─────────────────────────────────────────────"
	@$(PY) -m src.wisdom_hint --from-csv data/picks_log.csv 2>/dev/null \
		|| echo "(no picks_log.csv or no hints)"

wisdom-promote:  ## Promote significant patterns → lessons (writes!)
	@echo "🧠 Auto-promoting patterns..."
	@$(PY) -m src.auto_promote

wisdom-dryrun:   ## Preview which patterns WOULD be promoted (read-only)
	@echo "👀 Auto-promote dry-run"
	@$(PY) -m src.auto_promote --dry-run

wisdom-stats:    ## Show wisdom-base counts (lessons, patterns, coverage)
	@$(PY) -c "from src.wisdom_base import stats; \
import json; print(json.dumps(stats(), indent=2))"

wisdom-gc:       ## Deactivate lessons older than 90d (writes!)
	@echo "🗑  GC stale lessons..."
	@$(PY) -m src.lesson_gc

wisdom-gc-dryrun: ## Preview which lessons WOULD be deactivated
	@echo "👀 Lesson GC dry-run"
	@$(PY) -m src.lesson_gc --dry-run

# ─── Daily ops ─────────────────────────────────────────────────
.PHONY: picks evaluate weekly
picks:     ## Generate today's picks
	$(PY) -m scripts.send_telegram

evaluate:  ## Evaluate open picks (closes hits)
	$(PY) -m src.pick_evaluator

weekly:    ## Generate weekly review report
	$(PY) -m src.weekly_review

# ─── Housekeeping ──────────────────────────────────────────────
.PHONY: clean lint
clean:  ## Remove caches and bytecode
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ cleaned"

lint:   ## Quick syntax check on src/ + scripts/
	@$(PY) -m compileall -q src scripts && echo "✅ syntax OK"
