from __future__ import annotations

from datetime import datetime

import requests

from classification.taxonomy import CATEGORY_TAXONOMY
from collectors.base import batch, guarded_collect
from intelligence.types import CollectorBatch, RawSignal

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"


def collect_github(db=None, settings: dict | None = None) -> CollectorBatch:
    settings = settings or {}
    token = settings.get("github_token", "")
    limit = min(int(settings.get("collectors_limit", 20) or 20), 100)
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    started_at = datetime.utcnow()

    def _collect() -> list[RawSignal]:
        records: list[RawSignal] = []
        seen: set[str] = set()
        for meta in CATEGORY_TAXONOMY.values():
            query = str(meta.get("github_query", "artificial intelligence"))
            params = {
                "q": f"{query} stars:>50",
                "sort": "updated",
                "order": "desc",
                "per_page": limit,
            }
            response = requests.get(GITHUB_SEARCH_URL, headers=headers, params=params, timeout=20)
            if response.status_code == 403:
                raise RuntimeError("GitHub API rate limit or authorization failure.")
            response.raise_for_status()
            for item in response.json().get("items", []):
                full_name = item.get("full_name")
                if not full_name or full_name in seen:
                    continue
                seen.add(full_name)
                published_at = _parse_datetime(item.get("pushed_at") or item.get("updated_at"))
                records.append(
                    RawSignal(
                        source="github",
                        external_id=full_name,
                        title=full_name,
                        description=item.get("description") or "",
                        url=item.get("html_url") or "",
                        engagement_score=int(item.get("stargazers_count") or 0),
                        published_at=published_at,
                        raw_payload={
                            "name": item.get("name") or full_name.split("/")[-1],
                            "full_name": full_name,
                            "forks": int(item.get("forks_count") or 0),
                            "language": item.get("language") or "Other",
                            "created_at": item.get("created_at"),
                            "updated_at": item.get("updated_at"),
                        },
                    )
                )
        return records

    if not token:
        return batch("github", "skipped", [], "GITHUB_TOKEN is not configured.", started_at)
    return guarded_collect("github", _collect, started_at)


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.utcnow()
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return datetime.utcnow()
