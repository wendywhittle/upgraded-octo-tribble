"""Read-only RSS/Atom acquisition adapter.

The adapter only performs HTTP GET requests against explicitly configured feeds.
It does not execute actions, infer point-in-time timestamps, or make decisions.
"""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Callable, Iterable, List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from app.evidence_sources import SourceDocument

FetchBytes = Callable[[str], bytes]
Clock = Callable[[], datetime]
ATOM = "{http://www.w3.org/2005/Atom}"


def _default_fetch(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("RSS acquisition requires HTTPS URLs.")
    request = Request(url, headers={"User-Agent": "AletheiaTelos/1.0"}, method="GET")
    with urlopen(request, timeout=10) as response:  # nosec B310 - scheme is checked above
        return response.read()


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _parse_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _text(element: Optional[ET.Element], *tags: str) -> str:
    if element is None:
        return ""
    for tag in tags:
        child = element.find(tag)
        if child is not None:
            value = "".join(child.itertext()).strip()
            if value:
                return value
    return ""


class RSSFeedEvidenceSource:
    """Acquire searchable RSS/Atom entries as normalized source documents."""

    name = "rss_feed"

    def __init__(
        self,
        feed_urls: Iterable[str],
        fetcher: FetchBytes = _default_fetch,
        clock: Clock = _default_clock,
    ):
        urls = list(feed_urls)
        if not urls:
            raise ValueError("At least one feed URL is required.")
        for url in urls:
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError("All RSS feed URLs must be valid HTTPS URLs.")
        self._feed_urls = urls
        self._fetcher = fetcher
        self._clock = clock

    def acquire(self, query: str, limit: int = 10) -> List[SourceDocument]:
        if limit < 1:
            return []
        terms = [term.lower() for term in query.split() if term.strip()]
        documents: List[SourceDocument] = []
        retrieved_at = self._clock().astimezone(timezone.utc).isoformat()

        for feed_url in self._feed_urls:
            root = ET.fromstring(self._fetcher(feed_url))
            channel_title = _text(root, "./channel/title", f"{ATOM}title") or feed_url

            entries = list(root.findall("./channel/item"))
            if not entries:
                entries = list(root.findall(f"{ATOM}entry"))

            for entry in entries:
                title = _text(entry, "title", f"{ATOM}title") or "Untitled"
                description = _text(
                    entry,
                    "description",
                    "summary",
                    "content",
                    f"{ATOM}summary",
                    f"{ATOM}content",
                )
                link = _text(entry, "link")
                if not link:
                    atom_link = entry.find(f"{ATOM}link")
                    if atom_link is not None:
                        link = atom_link.attrib.get("href", "")
                observed_raw = _text(
                    entry,
                    "pubDate",
                    f"{ATOM}published",
                    f"{ATOM}updated",
                )
                observed_at = _parse_date(observed_raw)
                haystack = f"{title} {description}".lower()
                if terms and not any(term in haystack for term in terms):
                    continue

                source_id = link or f"{feed_url}#{len(documents) + 1}"
                documents.append(SourceDocument(
                    source=channel_title,
                    title=title,
                    content=description,
                    retrieved_at=retrieved_at,
                    observed_at=observed_at,
                    url=link or feed_url,
                    source_id=source_id,
                    provenance_type="rss",
                    point_in_time=observed_at is not None,
                ))
                if len(documents) >= limit:
                    return documents
        return documents
