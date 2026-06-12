"""Women in Tech Inspiration Feed — Apify Actor.

Collects recent posts about women in tech and turns them into one stream:

  Level 1 (API):  Dev.to publishes a clean JSON API        -> source "devto"
  Level 3 (RSS):  Medium blocks scrapers, so we use its RSS -> source "medium"

Each post is normalized to the same shape and pushed to the dataset.
"""

from __future__ import annotations

import asyncio
import html
import re
from datetime import datetime, timedelta, timezone

import feedparser
import httpx

from apify import Actor

DEVTO_API = "https://dev.to/api/articles"
MEDIUM_FEED = "https://medium.com/feed/tag/{tag}"

# Common shape every source maps to:
#   name, excerpt, link, tags, source, published_at (ISO), reactions, cover_image


def _clean(text: str | None) -> str:
    """Strip HTML tags and collapse whitespace (Medium summaries are HTML)."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(" ".join(text.split())).strip()


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Dev.to returns e.g. "2026-06-02T12:03:30Z"
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


async def fetch_devto(client: httpx.AsyncClient, tag: str, per_page: int = 30) -> list[dict]:
    """Level 1 — the easy win. Data already comes as clean JSON."""
    resp = await client.get(DEVTO_API, params={"tag": tag, "per_page": per_page})
    resp.raise_for_status()
    posts = []
    for a in resp.json():
        posts.append(
            {
                "name": a.get("user", {}).get("name"),
                "excerpt": a.get("description") or "",
                "link": a.get("url"),
                "tags": a.get("tag_list", []),
                "source": "dev.to",
                "published_at": a.get("published_at"),
                "reactions": a.get("public_reactions_count", 0),
                "cover_image": a.get("cover_image"),
            }
        )
    return posts


def _parse_medium(feed_bytes: bytes) -> list[dict]:
    """Level 3 — Medium blocks scrapers, so we read its RSS feed."""
    feed = feedparser.parse(feed_bytes)
    posts = []
    for e in feed.entries:
        published = None
        if getattr(e, "published_parsed", None):
            published = datetime(*e.published_parsed[:6], tzinfo=timezone.utc).isoformat()
        posts.append(
            {
                "name": getattr(e, "author", None),
                "excerpt": _clean(getattr(e, "summary", ""))[:280],
                "link": getattr(e, "link", None),
                "tags": [t["term"] for t in getattr(e, "tags", [])],
                "source": "medium",
                "published_at": published,
                "reactions": None,
                "cover_image": None,
            }
        )
    return posts


async def fetch_medium(client: httpx.AsyncClient, tag: str) -> list[dict]:
    # Fetch with our own (non-bot) user agent — Medium blocks feedparser's default.
    resp = await client.get(MEDIUM_FEED.format(tag=tag))
    resp.raise_for_status()
    # feedparser is synchronous — run the parse off the event loop.
    return await asyncio.to_thread(_parse_medium, resp.content)


async def main() -> None:
    # `async with Actor:` is the Apify lifecycle: it reads the run's input,
    # wires up logging, and finalizes the run on exit. All Actor work goes inside.
    async with Actor:
        # Input comes from the platform UI (or, when run locally, from
        # storage/key_value_stores/default/INPUT.json). The `or [...]` are fallbacks.
        actor_input = await Actor.get_input() or {}
        tags = actor_input.get("tags") or ["womenintech"]
        sources = actor_input.get("sources") or ["devto"]
        max_age_days = actor_input.get("maxAgeDays", 30)
        min_reactions = actor_input.get("minReactions", 0)
        limit = actor_input.get("limit", 50)

        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        Actor.log.info(f"Tags={tags} sources={sources} since={cutoff.date()}")

        # Step 1 — COLLECT. We query each tag from each source and pile everything
        # into one list. Note: multiple tags are a UNION (OR), not an intersection —
        # asking for ["womenintech", "python"] returns women-in-tech posts AND all
        # Python posts, not their overlap. (A busy tag like #python will flood the feed.)
        collected: list[dict] = []
        async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "women-in-tech-feed"}) as client:
            for tag in tags:
                if "devto" in sources:
                    try:
                        collected += await fetch_devto(client, tag)
                    except httpx.HTTPError as exc:
                        Actor.log.warning(f"Dev.to failed for #{tag}: {exc}")
                if "medium" in sources:
                    try:
                        collected += await fetch_medium(client, tag)
                    except Exception as exc:  # feedparser is forgiving; be defensive anyway
                        Actor.log.warning(f"Medium failed for #{tag}: {exc}")

        # Step 2 — FILTER: keep only recent posts, and (for Dev.to) popular enough ones.
        # Medium has no reaction count -> p["reactions"] is None -> always kept.
        filtered = []
        for p in collected:
            published = _parse_dt(p["published_at"])
            if published and published < cutoff:
                continue
            if p["reactions"] is not None and p["reactions"] < min_reactions:
                continue
            filtered.append(p)

        # Step 3 — DEDUPE by link (the same post can appear under two tags), then
        # sort newest-first so the freshest inspiration is at the top of the feed.
        seen: set[str] = set()
        unique = []
        for p in filtered:
            if p["link"] and p["link"] not in seen:
                seen.add(p["link"])
                unique.append(p)
        unique.sort(key=lambda p: p["published_at"] or "", reverse=True)

        result = unique[:limit]
        Actor.log.info(f"Collected {len(collected)} -> {len(result)} after filtering/dedupe")
        # Step 4 — OUTPUT. push_data writes each item to the run's dataset, which you
        # can browse/export (JSON, CSV, Excel) on the platform or in ./storage locally.
        await Actor.push_data(result)
