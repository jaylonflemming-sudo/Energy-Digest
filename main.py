"""Build today's energy digest.

    python main.py              # fetch, render, publish, email
    python main.py --no-email   # skip delivery, just write the files
"""

import argparse
import json
import logging
import os
from datetime import datetime

import config
import brief as brief_module
import mailer
import news
import render
import sources

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("digest")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-email", action="store_true")
    args = parser.parse_args()

    log.info("Fetching market data")
    market_data = sources.fetch_market_data()

    log.info("Fetching ERCOT")
    ercot = sources.fetch_ercot()

    log.info("Fetching headlines")
    headlines = news.fetch_news()

    if not market_data and not headlines:
        log.error("Nothing collected — aborting without overwriting the last digest")
        return 1

    log.info("Writing brief")
    written = brief_module.write_brief(market_data, ercot, headlines)

    now = datetime.now()
    html = render.render(written, market_data, ercot, headlines, now=now)

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    # index.html is what GitHub Pages serves; the dated copy is the archive.
    index_path = os.path.join(config.OUTPUT_DIR, "index.html")
    archive_path = os.path.join(
        config.OUTPUT_DIR, "archive", f"{now:%Y-%m-%d}.html"
    )
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)

    for path in (index_path, archive_path):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(html)

    # Raw payload, handy if you ever want to chart the history.
    with open(os.path.join(config.OUTPUT_DIR, "latest.json"), "w") as handle:
        json.dump(
            {
                "generated": now.isoformat(),
                "brief": written,
                "market": market_data,
                "ercot": ercot,
                "headlines": headlines,
            },
            handle,
            indent=2,
            default=str,
        )

    log.info("Wrote %s", index_path)

    if not args.no_email:
        subject = f"Energy digest — {written.get('headline', now.strftime('%b %d'))}"
        mailer.send(subject[:120], html)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
