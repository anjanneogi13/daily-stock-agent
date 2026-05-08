


def test_stooq_symbol_rejects_exchange_prefixed_and_unsupported_symbols():
    from src.market_data_providers.stooq_provider import stooq_symbol

    assert stooq_symbol("TSX:AQN") == ""
    assert stooq_symbol("TSX:FCR") == ""
    assert stooq_symbol("^GSPC") == ""
    assert stooq_symbol("BRK/B") == ""


def test_stooq_symbol_keeps_simple_us_symbols_conservative():
    from src.market_data_providers.stooq_provider import stooq_symbol

    assert stooq_symbol("AAPL") == "aapl.us"
    assert stooq_symbol("BRK.B") == "brk.b"
