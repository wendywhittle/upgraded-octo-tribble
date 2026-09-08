"""Small, environment-driven configuration boundary."""

import os


def research_feed_urls() -> list[str]:
    raw = os.getenv("ALETHEIA_RESEARCH_FEEDS", "")
    return [url.strip() for url in raw.split(",") if url.strip()]


def live_market_enabled() -> bool:
    return os.getenv("ALETHEIA_LIVE_MARKET_DATA", "").strip().lower() in {"1", "true", "yes"}


def market_symbol_map() -> dict[str, str]:
    raw = os.getenv("ALETHEIA_MARKET_SYMBOL_MAP", "")
    mapping: dict[str, str] = {}
    for item in raw.split(","):
        if "=" not in item:
            continue
        logical, provider = item.split("=", 1)
        logical = logical.strip().upper()
        provider = provider.strip()
        if logical and provider:
            mapping[logical] = provider
    return mapping
