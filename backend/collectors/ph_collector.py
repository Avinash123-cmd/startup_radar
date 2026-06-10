from __future__ import annotations

from datetime import datetime

import requests

from collectors.base import batch, guarded_collect
from intelligence.types import CollectorBatch, RawSignal

PRODUCT_HUNT_GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"


def collect_ph(db=None, settings: dict | None = None) -> CollectorBatch:
    settings = settings or {}
    token = settings.get("product_hunt_token", "")
    limit = min(int(settings.get("collectors_limit", 20) or 20), 50)
    started_at = datetime.utcnow()

    if not token:
        return batch("product_hunt", "skipped", [], "PRODUCT_HUNT_TOKEN is not configured.", started_at)

    def _collect() -> list[RawSignal]:
        query = """
        query StartupRadarPosts($first: Int!) {
          posts(first: $first, order: VOTES) {
            edges {
              node {
                id
                name
                tagline
                description
                votesCount
                commentsCount
                website
                url
                createdAt
                topics { edges { node { name } } }
                makers { name }
              }
            }
          }
        }
        """
        import time
        max_retries = 3
        backoff = 2
        response = None
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    PRODUCT_HUNT_GRAPHQL_URL,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"query": query, "variables": {"first": limit}},
                    timeout=25,
                )
                response.raise_for_status()
                break
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Product Hunt API request failed after {max_retries} attempts: {e}")
                time.sleep(backoff)
                backoff *= 2
        payload = response.json()
        if payload.get("errors"):
            raise RuntimeError(str(payload["errors"]))

        records: list[RawSignal] = []
        for edge in payload.get("data", {}).get("posts", {}).get("edges", []):
            node = edge.get("node", {})
            published_at = _parse_datetime(node.get("createdAt"))
            topics = [
                topic_edge.get("node", {}).get("name")
                for topic_edge in node.get("topics", {}).get("edges", [])
                if topic_edge.get("node", {}).get("name")
            ]
            records.append(
                RawSignal(
                    source="product_hunt",
                    external_id=str(node.get("id")),
                    title=f"[Product Hunt] {node.get('name') or ''}",
                    description=f"{node.get('tagline') or ''} {node.get('description') or ''} Topics: {', '.join(topics)}.",
                    url=node.get("url") or node.get("website") or "",
                    engagement_score=int(node.get("votesCount") or 0),
                    published_at=published_at,
                    raw_payload={
                        "website": node.get("website"),
                        "comments": int(node.get("commentsCount") or 0),
                        "topics": topics,
                        "makers": [maker.get("name") for maker in node.get("makers", []) if maker.get("name")],
                    },
                )
            )
        return records

    return guarded_collect("product_hunt", _collect, started_at)


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.utcnow()
