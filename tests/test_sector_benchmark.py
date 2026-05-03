"""Tests for sector benchmark resolution (T3 May 3 2026)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sector_benchmark import resolve_sector_etf


def test_semi_tag_resolves_to_soxx():
    assert resolve_sector_etf(sector="Technology", tag="SEMI") == "SOXX"


def test_semi_ai_compound_tag_resolves_to_soxx():
    """Tag 'SEMI / AI' → primary='SEMI' → SOXX."""
    assert resolve_sector_etf(sector="Technology", tag="SEMI / AI") == "SOXX"


def test_tech_sector_no_tag_resolves_to_xlk():
    assert resolve_sector_etf(sector="Technology", tag=None) == "XLK"


def test_healthcare_resolves_to_xlv():
    assert resolve_sector_etf(sector="Healthcare", tag="") == "XLV"


def test_financial_services_resolves_to_xlf():
    assert resolve_sector_etf(sector="Financial Services") == "XLF"


def test_unknown_falls_back_to_spy():
    assert resolve_sector_etf(sector="Astrology", tag="MEMECOIN") == "SPY"


def test_no_inputs_falls_back_to_spy():
    assert resolve_sector_etf() == "SPY"


def test_tag_overrides_sector():
    """Tag should win — more specific than generic sector."""
    assert resolve_sector_etf(sector="Healthcare", tag="BIOTECH") == "XBI"
