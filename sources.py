"""Market data: EIA commodity series and ERCOT grid conditions.

Every fetcher is defensive. A dead series or a gridstatus hiccup
degrades the digest, it never kills the run.
"""

import logging

import requests

import config

log = logging.getLogger(__name__)

EIA_BASE = "https://api.eia.gov/v2"


def fetch_eia_series(spec, length=8):
    """Pull the most recent observations for one EIA series.

    Returns a dict with the latest value, the prior value, and the
    change between them — or None if the series can't be read.
    """
    params = {
        "api_key": config.EIA_API_KEY,
        "frequency": spec["frequency"],
        "data[0]": "value",
        "facets[series][]": spec["series"],
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": length,
    }
    url = f"{EIA_BASE}/{spec['route']}/data/"

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        rows = resp.json().get("response", {}).get("data", [])
    except Exception as exc:
        log.warning("EIA fetch failed for %s: %s", spec["key"], exc)
        return None

    points = [r for r in rows if r.get("value") is not None]
    if not points:
        log.warning("EIA returned no values for %s", spec["key"])
        return None

    latest = points[0]
    prior = points[1] if len(points) > 1 else None

    value = float(latest["value"])
    prior_value = float(prior["value"]) if prior else None
    change = value - prior_value if prior_value is not None else None
    pct = (change / prior_value * 100) if change is not None and prior_value else None

    return {
        "key": spec["key"],
        "label": spec["label"],
        "unit": spec["unit"],
        "decimals": spec["decimals"],
        "period": latest.get("period"),
        "value": value,
        "prior_value": prior_value,
        "change": change,
        "pct_change": pct,
        "history": [
            {"period": p.get("period"), "value": float(p["value"])}
            for p in reversed(points)
        ],
    }


def fetch_market_data():
    """All configured EIA series. Skips silently over any that fail."""
    if not config.EIA_API_KEY:
        log.warning("EIA_API_KEY not set — skipping market data")
        return []

    out = []
    for spec in config.EIA_SERIES:
        row = fetch_eia_series(spec)
        if row:
            out.append(row)
    return out


def fetch_ercot():
    """Latest ERCOT fuel mix and load.

    Uses the open-source gridstatus library, which reads ERCOT's public
    files directly — no key needed for these two datasets.
    """
    if not config.INCLUDE_ERCOT:
        return None

    try:
        from gridstatus import Ercot
    except ImportError:
        log.warning("gridstatus not installed — skipping ERCOT")
        return None

    result = {}
    iso = Ercot()

    try:
        mix = iso.get_fuel_mix("latest")
        row = mix.iloc[-1]
        fuels = {
            col: float(row[col])
            for col in mix.columns
            if col not in ("Time", "Interval Start", "Interval End")
            and isinstance(row[col], (int, float))
        }
        total = sum(v for v in fuels.values() if v > 0)
        result["fuel_mix"] = {
            "total_mw": total,
            "breakdown": sorted(
                (
                    {"fuel": k, "mw": v, "share": (v / total * 100) if total else 0}
                    for k, v in fuels.items()
                ),
                key=lambda d: d["mw"],
                reverse=True,
            ),
        }
    except Exception as exc:
        log.warning("ERCOT fuel mix failed: %s", exc)

    try:
        load = iso.get_load("latest")
        result["load_mw"] = float(load.iloc[-1]["Load"])
    except Exception as exc:
        log.warning("ERCOT load failed: %s", exc)

    return result or None
