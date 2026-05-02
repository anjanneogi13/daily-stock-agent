"""Backtester v2 — Brain Replay Engine.

Replays the live pick pipeline against historical data with
strict point-in-time discipline (no look-ahead bias).

Phase A: price-only, no LLM, no news.
"""
from src.backtester.engine import run_backtest
from src.backtester.metrics import compute_metrics

__all__ = ["run_backtest", "compute_metrics"]
