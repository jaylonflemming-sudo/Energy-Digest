"""Headline collection from RSS feeds."""

import logging
import re
from datetime import datetime, timedelta, timezone
from html import unescape

import feedparser

import config

log = logging.getLogger(__name__)


def _clean(text):
    """Strip tags and collapse whitespace out of a summary blob."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _published(entry):
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
    return None


def fetch_feed(feed):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=config.MAX_AGE_HOURS)
    items = []

    try:
        parsed = feedparser.parse(feed["url"])
    except Exception as exc:
        log.warning("Feed failed: %s (%s)", feed["name"], exc)
        return items

    if parsed.get("bozo") and not parsed.get("entries"):
        log.warning("Feed unreadable: %s", feed["name"])
        return items

    for entry in parsed.entries:
        when = _published(entry)
        if when and when < cutoff:
            continue
        items.append(
            {
                "source": feed["name"],
                "title": _clean(entry.get("title", "")),
                "url": entry.get("link", ""),
                "summary": _clean(entry.get("summary", ""))[:400],
                "published": when.isoformat() if when else None,
            }
        )
        if len(items) >= config.MAX_ITEMS_PER_FEED:
            break

    return items


def fetch_news():
    """All feeds, deduplicated on title."""
    seen = set()
    out = []

    for feed in config.FEEDS:
        for item in fetch_feed(feed):
            fingerprint = item["title"].lower()[:90]
            if not fingerprint or fingerprint in seen:
                continue
            seen.add(fingerprint)
            out.append(item)

    log.info("Collected %d headlines", len(out))
    return out
