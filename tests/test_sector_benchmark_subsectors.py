"""Bug #8a: yfinance returns specific subsector strings (e.g. 'Semiconductors',
'Biotechnology') that weren't in SECTOR_TO_ETF, falling through to SPY and
killing sector-relative alpha for ~70% of picks. These tests guard the
mappings we added."""
import pytest
from src.sector_benchmark import resolve_sector_etf


@pytest.mark.parametrize("yfinance_sector,expected_etf", [
    ("Semiconductors",                    "SOXX"),  # NVDA, AVGO, ARM, etc. — most common
    ("Biotechnology",                     "XBI"),   # ARWR, etc.
    ("Life Sciences Tools & Services",    "XLV"),   # Agilent (A)
    ("Software",                          "IGV"),
    ("Software—Application",              "IGV"),
    ("Software—Infrastructure",           "IGV"),
    ("Internet Content & Information",    "FDN"),
    ("Drug Manufacturers—General",        "XPH"),
    ("Drug Manufacturers—Specialty",      "XPH"),
    ("Medical Devices",                   "IHI"),
])
def test_yfinance_subsector_resolves_correctly(yfinance_sector, expected_etf):
    """The exact subsector strings yfinance actually returns must map to the
    most-specific ETF, not fall through to SPY."""
    got = resolve_sector_etf(sector=yfinance_sector, tag=None)
    assert got == expected_etf, (
        f"yfinance sector {yfinance_sector!r} mapped to {got!r}, "
        f"expected {expected_etf!r}. SPY fallback corrupts sector-alpha learning."
    )


def test_truly_unknown_sector_still_falls_back_to_SPY():
    """Regression guard: don't break the SPY fallback for genuinely unknown
    sectors. SPY is a valid 'we don't know' signal."""
    assert resolve_sector_etf(sector="Made-Up Sector XYZ", tag=None) == "SPY"


def test_empty_sector_falls_back_to_SPY():
    """Regression guard: empty/None sector still falls back."""
    assert resolve_sector_etf(sector="", tag=None) == "SPY"
    assert resolve_sector_etf(sector=None, tag=None) == "SPY"


def test_tag_still_wins_over_sector_after_subsector_additions():
    """Regression guard: existing tag-priority logic must still work.
    A 'SEMI' tag should still win → SOXX, even if sector is also Semiconductors."""
    assert resolve_sector_etf(sector="Semiconductors", tag="SEMI / AI") == "SOXX"


def test_existing_top_level_sectors_still_work():
    """Regression guard: don't break existing mappings."""
    assert resolve_sector_etf(sector="Technology", tag=None) == "XLK"
    assert resolve_sector_etf(sector="Healthcare", tag=None) == "XLV"
    assert resolve_sector_etf(sector="Financial Services", tag=None) == "XLF"
