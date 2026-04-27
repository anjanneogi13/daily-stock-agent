"""Curated US-listed semiconductor universe with AI-relevance tagging."""
from typing import Dict, List

SEMI_UNIVERSE: Dict[str, Dict] = {
    "NVDA": {"name": "NVIDIA",            "category": "AI GPU",            "ai_weight": 1.00},
    "AMD":  {"name": "Advanced Micro",    "category": "CPU/GPU",           "ai_weight": 0.90},
    "AVGO": {"name": "Broadcom",          "category": "AI ASIC/Networking","ai_weight": 0.95},
    "MRVL": {"name": "Marvell",           "category": "AI Networking/DPU", "ai_weight": 0.90},
    "INTC": {"name": "Intel",             "category": "CPU/Foundry",       "ai_weight": 0.65},
    "TSM":  {"name": "TSMC (ADR)",        "category": "Foundry",           "ai_weight": 0.95},
    "MU":   {"name": "Micron",            "category": "HBM/DRAM",          "ai_weight": 0.90},
    "WDC":  {"name": "Western Digital",   "category": "Storage",           "ai_weight": 0.55},
    "STX":  {"name": "Seagate",           "category": "Storage",           "ai_weight": 0.50},
    "ASML": {"name": "ASML (ADR)",        "category": "Lithography",       "ai_weight": 0.90},
    "AMAT": {"name": "Applied Materials", "category": "Equipment",         "ai_weight": 0.80},
    "LRCX": {"name": "Lam Research",      "category": "Equipment",         "ai_weight": 0.80},
    "KLAC": {"name": "KLA",               "category": "Metrology",         "ai_weight": 0.75},
    "ACLS": {"name": "Axcelis",           "category": "Ion Implant",       "ai_weight": 0.55},
    "ONTO": {"name": "Onto Innovation",   "category": "Metrology",         "ai_weight": 0.65},
    "UCTT": {"name": "Ultra Clean",       "category": "Equipment Supplier","ai_weight": 0.55},
    "SNPS": {"name": "Synopsys",          "category": "EDA/IP",            "ai_weight": 0.85},
    "CDNS": {"name": "Cadence",           "category": "EDA/IP",            "ai_weight": 0.85},
    "ARM":  {"name": "Arm Holdings",      "category": "IP",                "ai_weight": 0.85},
    "ANET": {"name": "Arista Networks",   "category": "AI Networking",     "ai_weight": 0.85},
    "CRDO": {"name": "Credo Tech",        "category": "AI Connectivity",   "ai_weight": 0.85},
    "ALAB": {"name": "Astera Labs",       "category": "AI Connectivity",   "ai_weight": 0.95},
    "COHR": {"name": "Coherent",          "category": "Optical",           "ai_weight": 0.70},
    "LITE": {"name": "Lumentum",          "category": "Optical",           "ai_weight": 0.65},
    "AAOI": {"name": "Applied Optoelec",  "category": "Optical",           "ai_weight": 0.60},
    "TXN":  {"name": "Texas Instruments", "category": "Analog",            "ai_weight": 0.50},
    "ADI":  {"name": "Analog Devices",    "category": "Analog",            "ai_weight": 0.55},
    "MCHP": {"name": "Microchip",         "category": "MCU/Analog",        "ai_weight": 0.45},
    "ON":   {"name": "ON Semiconductor",  "category": "Power/Auto",        "ai_weight": 0.45},
    "MPWR": {"name": "Monolithic Power",  "category": "Power Mgmt",        "ai_weight": 0.75},
    "POWI": {"name": "Power Integrations","category": "Power",             "ai_weight": 0.40},
    "VICR": {"name": "Vicor",             "category": "AI Power",          "ai_weight": 0.70},
    "QCOM": {"name": "Qualcomm",          "category": "Mobile/AI Edge",    "ai_weight": 0.60},
    "RMBS": {"name": "Rambus",            "category": "Memory IP",         "ai_weight": 0.75},
    "GFS":  {"name": "GlobalFoundries",   "category": "Foundry",           "ai_weight": 0.55},
    "UMC":  {"name": "United Micro",      "category": "Foundry",           "ai_weight": 0.50},
    "SMCI": {"name": "Super Micro",       "category": "AI Servers",        "ai_weight": 0.95},
    "DELL": {"name": "Dell",              "category": "AI Servers",        "ai_weight": 0.70},
    "ENTG": {"name": "Entegris",          "category": "Materials",         "ai_weight": 0.65},
    "MKSI": {"name": "MKS Instruments",   "category": "Equipment/Mat",     "ai_weight": 0.60},
    "TER":  {"name": "Teradyne",          "category": "Test",              "ai_weight": 0.70},
    "AEIS": {"name": "Advanced Energy",   "category": "Power/Test",        "ai_weight": 0.60},
    "FORM": {"name": "FormFactor",        "category": "Test",              "ai_weight": 0.65},
    "SOXX": {"name": "iShares Semi ETF",  "category": "Semi ETF",          "ai_weight": 0.80},
    "SMH":  {"name": "VanEck Semi ETF",   "category": "Semi ETF",          "ai_weight": 0.80},
    "SOXL": {"name": "Direxion Semi 3x",  "category": "Leveraged ETF",     "ai_weight": 0.80},
}

def get_semi_tickers(min_ai_weight: float = 0.0) -> List[str]:
    return [t for t, m in SEMI_UNIVERSE.items() if m["ai_weight"] >= min_ai_weight]

def get_semi_meta(ticker: str) -> Dict:
    return SEMI_UNIVERSE.get(ticker.upper(), {})

def is_semi(ticker: str) -> bool:
    return ticker.upper() in SEMI_UNIVERSE

def semi_categories() -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for tk, meta in SEMI_UNIVERSE.items():
        out.setdefault(meta["category"], []).append(tk)
    return out
