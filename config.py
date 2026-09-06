"""Configuration for the energy digest.

Everything you'd want to tune lives here: which numbers to pull,
which feeds to read, and how many stories to keep.
"""

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- Secrets (set in .env locally, GitHub Secrets in CI) ---
EIA_API_KEY = os.getenv("EIA_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

# --- Market data -----------------------------------------------------------
# EIA API v2. Each entry maps to https://api.eia.gov/v2/{route}/data/
# filtered by facets[series][]={series}.
#
# If a series stops returning data, run `python check_sources.py` — it will
# tell you which ones are broken, and you can look up replacements at
# https://www.eia.gov/opendata/browser/
EIA_SERIES = [
    {
        "key": "wti",
        "label": "WTI crude, Cushing",
        "route": "petroleum/pri/spt",
        "series": "RWTC",
        "frequency": "daily",
        "unit": "$/bbl",
        "decimals": 2,
    },
    {
        "key": "brent",
        "label": "Brent crude",
        "route": "petroleum/pri/spt",
        "series": "RBRTE",
        "frequency": "daily",
        "unit": "$/bbl",
        "decimals": 2,
    },
    {
        "key": "henry_hub",
        "label": "Henry Hub natural gas",
        "route": "natural-gas/pri/fut",
        "series": "RNGWHHD",
        "frequency": "daily",
        "unit": "$/MMBtu",
        "decimals": 2,
    },
    {
        "key": "crude_stocks",
        "label": "US crude stocks, ex-SPR",
        "route": "petroleum/stoc/wstk",
        "series": "WCESTUS1",
        "frequency": "weekly",
        "unit": "kbbl",
        "decimals": 0,
    },
    {
        "key": "gas_storage",
        "label": "Lower 48 gas in storage",
        "route": "natural-gas/stor/wkly",
        "series": "NW2_EPG0_SWO_R48_BCF",
        "frequency": "weekly",
        "unit": "Bcf",
        "decimals": 0,
    },
]

# --- News feeds ------------------------------------------------------------
# Direct publisher feeds first. Google News queries are the safety net:
# they always resolve, so the digest is never empty even if a
# publisher changes their feed URL.
FEEDS = [
    # Direct publisher feeds
    {"name": "EIA Today in Energy", "url": "https://www.eia.gov/rss/todayinenergy.xml"},
    {"name": "RBN Energy", "url": "https://rbnenergy.com/rss.xml"},
    {"name": "Oil & Gas Journal", "url": "https://news.google.com/rss/search?q=site:ogj.com+when:7d&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Canary Media", "url": "https://www.canarymedia.com/feed"},
    {"name": "Houston Business Journal", "url": "https://news.google.com/rss/search?q=Houston+energy+business+when:3d&hl=en-US&gl=US&ceid=US:en"},

    # Google News fallbacks — reliable, and easy to retarget
    {
        "name": "Gulf Coast LNG",
        "url": "https://news.google.com/rss/search?q=%22Gulf+Coast%22+LNG+when:2d&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "ERCOT & Texas grid",
        "url": "https://news.google.com/rss/search?q=ERCOT+OR+%22Texas+grid%22+when:2d&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "Houston energy hiring",
        "url": "https://news.google.com/rss/search?q=Houston+energy+company+expansion+OR+hiring+when:3d&hl=en-US&gl=US&ceid=US:en",
    },
]

# --- Behaviour -------------------------------------------------------------
MAX_ITEMS_PER_FEED = 5
MAX_AGE_HOURS = 48          # ignore anything staler than this
INCLUDE_ERCOT = True        # set False to skip the gridstatus call
TIMEZONE = "America/Chicago"

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "docs")
