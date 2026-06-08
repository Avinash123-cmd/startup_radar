from __future__ import annotations

from datetime import datetime, timedelta

import requests

from collectors.base import guarded_collect
from intelligence.types import CollectorBatch, RawSignal

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"


def collect_hn(db=None, settings: dict | None = None) -> CollectorBatch:
    settings = settings or {}
    limit = min(int(settings.get("collectors_limit", 20) or 20), 100)
    started_at = datetime.utcnow()

    def _collect() -> list[RawSignal]:
        one_month_ago = int((datetime.utcnow() - timedelta(days=30)).timestamp())
        response = requests.get(
            HN_SEARCH_URL,
            params={
                "query": "AI OR LLM OR agent",
                "tags": "story",
                "numericFilters": f"created_at_i>{one_month_ago}",
                "hitsPerPage": limit,
            },
            timeout=15,
        )
        response.raise_for_status()
        records: list[RawSignal] = []
        for hit in response.json().get("hits", []):
            title = hit.get("title") or hit.get("story_title") or ""
            if not title:
                continue
            created_at = _parse_datetime(hit.get("created_at"))
            object_id = str(hit.get("objectID"))
            records.append(
                RawSignal(
                    source="hacker_news",
                    external_id=object_id,
                    title=title,
                    description=f"Hacker News story with {hit.get('points') or 0} points and {hit.get('num_comments') or 0} comments.",
                    url=hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}",
                    engagement_score=int(hit.get("points") or 0),
                    published_at=created_at,
                    raw_payload={
                        "author": hit.get("author"),
                        "comments": hit.get("num_comments") or 0,
                    },
                )
            )
        return records

    return guarded_collect("hacker_news", _collect, started_at)


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.utcnow()
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return datetime.utcnow()
