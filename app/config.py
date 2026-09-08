"""Small, environment-driven configuration boundary."""

import os


def research_feed_urls() -> list[str]:
    raw = os.getenv("ALETHEIA_RESEARCH_FEEDS", "")
    return [url.strip() for url in raw.split(",") if url.strip()]
