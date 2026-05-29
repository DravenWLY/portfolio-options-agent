"""Offline symbol fixtures for symbol lookup fallback tests.

These records are deliberately small. They are not a broad directory, user
recents, recommendations, broker tradability, or quote data.
"""

from __future__ import annotations

OFFLINE_SYMBOL_FIXTURES = (
    {
        "symbol": "AMRX",
        "name": "RAM Research Corporation",
        "asset_class": "stock",
        "exchange": "NASDAQ",
    },
    {
        "symbol": "DRAM",
        "name": "Global X Synthetic DRAM Memory ETF",
        "asset_class": "etf",
        "exchange": "NYSEARCA",
    },
    {
        "symbol": "LNOK",
        "name": "Synthetic Long Nokia Exposure ETF",
        "asset_class": "etf",
        "exchange": "NASDAQ",
    },
    {
        "symbol": "NKRKF",
        "name": "Nokia Synthetic Foreign Ordinary",
        "asset_class": "stock",
        "exchange": "OTC",
    },
    {
        "symbol": "NKRKY",
        "name": "Nokia Synthetic ADR",
        "asset_class": "adr",
        "exchange": "OTC",
    },
    {
        "symbol": "NOK",
        "name": "Nokia Corporation ADR",
        "asset_class": "adr",
        "exchange": "NYSE",
    },
    {
        "symbol": "NOKBF",
        "name": "Nokia Synthetic Foreign Ordinary",
        "asset_class": "stock",
        "exchange": "OTC",
    },
    {
        "symbol": "NOKPF",
        "name": "Nokia Synthetic Preferred",
        "asset_class": "stock",
        "exchange": "OTC",
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "asset_class": "stock",
        "exchange": "NASDAQ",
    },
    {
        "symbol": "NVDL",
        "name": "GraniteShares 2x Long NVDA Daily ETF",
        "asset_class": "etf",
        "exchange": "NASDAQ",
    },
    {
        "symbol": "SPY",
        "name": "SPDR S&P 500 ETF Trust",
        "asset_class": "etf",
        "exchange": "NYSEARCA",
    },
    {
        "symbol": "SPX",
        "name": "S&P 500 Index",
        "asset_class": "index",
        "exchange": "CBOE",
        "is_supported": False,
    },
    {
        "symbol": "TESTU",
        "name": "Unsupported Synthetic Test Issue",
        "asset_class": "stock",
        "exchange": "NASDAQ",
        "is_test_issue": True,
    },
)
