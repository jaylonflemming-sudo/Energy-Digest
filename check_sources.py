"""Verify every configured source. Run this first, and any time the
digest looks thin.

    python check_sources.py

Feed URLs and EIA series IDs do change. This tells you exactly which
ones need fixing instead of leaving you to guess.
"""

import feedparser
import requests

import config
import sources

OK = "\033[32m  ok \033[0m"
BAD = "\033[31m FAIL\033[0m"


def check_eia():
    print("\nEIA series")
    print("-" * 60)

    if not config.EIA_API_KEY:
        print(f"{BAD}  EIA_API_KEY is not set")
        return

    for spec in config.EIA_SERIES:
        row = sources.fetch_eia_series(spec, length=2)
        if row:
            print(f"{OK}  {spec['label']}: {row['value']} {spec['unit']} ({row['period']})")
        else:
            print(f"{BAD}  {spec['label']}  [{spec['route']} / {spec['series']}]")
            print("        look up a replacement at eia.gov/opendata/browser/")


def check_feeds():
    print("\nRSS feeds")
    print("-" * 60)

    for feed in config.FEEDS:
        try:
            parsed = feedparser.parse(feed["url"])
            count = len(parsed.entries)
        except Exception as exc:
            print(f"{BAD}  {feed['name']}: {exc}")
            continue

        if count:
            print(f"{OK}  {feed['name']}: {count} entries")
        else:
            print(f"{BAD}  {feed['name']}: no entries — {feed['url']}")


def check_ercot():
    print("\nERCOT")
    print("-" * 60)
    data = sources.fetch_ercot()
    if data and data.get("fuel_mix"):
        total = data["fuel_mix"]["total_mw"]
        print(f"{OK}  fuel mix reachable, {total:,.0f} MW total")
    else:
        print(f"{BAD}  ERCOT unreachable (set INCLUDE_ERCOT = False to skip)")


def check_anthropic():
    print("\nClaude API")
    print("-" * 60)
    if not config.ANTHROPIC_API_KEY:
        print(f"{BAD}  ANTHROPIC_API_KEY is not set — digest will ship without a summary")
        return
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=8,
            messages=[{"role": "user", "content": "Reply with the word ok."}],
        )
        print(f"{OK}  {config.ANTHROPIC_MODEL} responding")
    except Exception as exc:
        print(f"{BAD}  {exc}")


if __name__ == "__main__":
    check_eia()
    check_feeds()
    check_ercot()
    check_anthropic()
    print()
