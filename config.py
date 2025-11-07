"""
Configuration for ZERA Historical Price Tracker
"""

# GeckoTerminal API Configuration
BASE_URL = "https://api.geckoterminal.com/api/v2"
NETWORK = "solana"
TIMEFRAME = "day"  # Daily OHLCV data (options: minute, hour, day)

# Pool Addresses (in chronological order)
POOLS = {
    "mon3y": {
        "address": "95AT5r4i85gfqeew2yR6BYFG8RLrY1d9ztPs7qrSKDVc",
        "name": "M0N3Y (Original)",
        "token_symbol": "M0N3Y",
        "active_until": "2025-10-02"  # Migration date
    },
    "zera_pool2": {
        "address": "Nn9VMHJTqgG9L9F8SP3GEuFWC5zVuHrADCwehh7N7Di",
        "name": "ZERA Raydium",
        "token_symbol": "ZERA",
        "active_from": "2025-10-02",
        "active_until": "2025-11-05"  # Second migration date
    },
    "zera_pool3": {
        "address": "6oUJD1EHNVBNMeTpytmY2NxKWicz5C2JUbByUrHEsjhc",
        "name": "ZERA Meteora",
        "token_symbol": "ZERA",
        "active_from": "2025-11-05"
    }
}

# Migration Dates (Unix timestamps)
MIGRATION_DATES = {
    "mon3y_to_zera": 1759363200,  # October 2, 2025 08:00:00 UTC
    "zera_pool2_to_pool3": 1762300800  # November 5, 2025 08:00:00 UTC (Raydium to Meteora)
}

# Output Configuration
OUTPUT_DIR = "output"
CSV_FILENAME = "zera_unified_price_history.csv"
CHART_FILENAME = "zera_price_chart.png"
