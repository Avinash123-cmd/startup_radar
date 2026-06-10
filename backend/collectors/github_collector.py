from __future__ import annotations

from datetime import datetime
import time

import requests

from classification.taxonomy import CATEGORY_TAXONOMY
from collectors.base import batch, guarded_collect
from intelligence.types import CollectorBatch, RawSignal

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"


def _make_github_request(url: str, headers: dict, params: dict, max_retries: int = 3) -> requests.Response:
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=20)
            if response.status_code in (403, 429):
                remaining = response.headers.get("X-RateLimit-Remaining")
                reset = response.headers.get("X-RateLimit-Reset")
                is_rate_limit = (response.status_code == 429) or (remaining == "0") or ("rate limit" in response.text.lower())
                
                if is_rate_limit:
                    if reset:
                        try:
                            wait_time = float(reset) - time.time()
                            wait_time = max(wait_time, 1.0)
                            if wait_time <= 65:
                                time.sleep(wait_time)
                                continue
                        except ValueError:
                            pass
                    wait_time = (2 ** attempt) * 2
                    time.sleep(wait_time)
                    continue
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt == max_retries - 1:
                raise
            time.sleep((2 ** attempt) * 2)
    raise RuntimeError("Max retries exceeded")


def collect_github(db=None, settings: dict | None = None) -> CollectorBatch:
    settings = settings or {}
    token = settings.get("github_token", "")
    limit = min(int(settings.get("collectors_limit", 20) or 20), 100)
    started_at = datetime.utcnow()

    if not token:
        return batch("github", "skipped", [], "GitHub token is not configured.", started_at)

    headers = {"Accept": "application/vnd.github+json"}
    headers["Authorization"] = f"Bearer {token}"

    def _collect() -> list[RawSignal]:
        records: list[RawSignal] = []
        seen: set[str] = set()
        for meta in CATEGORY_TAXONOMY.values():
            query = str(meta.get("github_query", "artificial intelligence"))
            per_page = min(limit, 100)
            page = 1
            category_collected = 0
            
            while category_collected < limit:
                params = {
                    "q": f"{query} stars:>50",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": per_page,
                    "page": page,
                }
                response = _make_github_request(GITHUB_SEARCH_URL, headers=headers, params=params)
                items = response.json().get("items", [])
                if not items:
                    break
                
                new_added = 0
                for item in items:
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
                    category_collected += 1
                    new_added += 1
                    if category_collected >= limit:
                        break
                
                if new_added == 0 and len(items) < per_page:
                    break
                
                page += 1
                if page > 10:
                    break
                    
        return records

    return guarded_collect("github", _collect, started_at)


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.utcnow()
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return datetime.utcnow()

