"""Shiller CAPE Ratio — manually maintained (updates monthly).
Source: https://www.multpl.com/shiller-pe (check monthly)."""
from datetime import datetime

# Update this monthly from multpl.com
_CAPE_VALUE = 38.5    # As of late April 2025
_CAPE_UPDATED = "2025-04-01"


def get_cape() -> dict:
    c = _CAPE_VALUE
    if c < 15:    verdict, pct = "Cheap",                      "<25th percentile"
    elif c < 20:  verdict, pct = "Fair",                       "25-50th"
    elif c < 25:  verdict, pct = "Elevated",                   "50-75th"
    elif c < 32:  verdict, pct = "Expensive",                  "75-90th"
    else:         verdict, pct = "Very Expensive (caution)",   ">90th"
    return {
        "cape": c,
        "verdict": verdict,
        "percentile": pct,
        "as_of": _CAPE_UPDATED,
        "source": "multpl.com (manual)",
    }


if __name__ == "__main__":
    print(get_cape())
