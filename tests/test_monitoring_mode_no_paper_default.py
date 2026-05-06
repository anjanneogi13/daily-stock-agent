import main


def test_trading_mode_unset_defaults_to_monitoring_not_paper(monkeypatch):
    monkeypatch.delenv("TRADING_MODE", raising=False)

    assert main._should_log_paper_trade() is False


def test_paper_logging_requires_explicit_paper_mode(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "paper")

    assert main._should_log_paper_trade() is True


def test_monitoring_mode_disables_paper_logging(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "monitoring")

    assert main._should_log_paper_trade() is False
