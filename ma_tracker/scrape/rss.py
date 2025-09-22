from __future__ import annotations
from typing import List, Dict
import feedparser
import dateparser

def fetch_rss(url: str, limit: int = 50) -> List[Dict]:
    """
    Fetch an RSS/Atom feed and return a list of items with normalized fields:
      - published (datetime or None)
      - title (str)
      - link (str)
      - summary (str)
    """
    parsed = feedparser.parse(url)
    items = []
    for entry in parsed.entries[:limit]:
        published_raw = (
            getattr(entry, "published", None)
            or getattr(entry, "updated", None)
            or getattr(entry, "pubDate", None)
        )
        published = dateparser.parse(published_raw) if published_raw else None

        items.append({
            "published": published,
            "title": getattr(entry, "title", "") or "",
            "link": getattr(entry, "link", "") or "",
            "summary": getattr(entry, "summary", "") or getattr(entry, "description", "") or "",
        })
    return items
