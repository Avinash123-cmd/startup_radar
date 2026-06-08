from __future__ import annotations

import time
from datetime import datetime, timezone

import requests
from requests.auth import HTTPBasicAuth

from collectors.base import batch, guarded_collect
from intelligence.types import CollectorBatch, RawSignal

SUBREDDITS = ["LocalLLaMA", "MachineLearning", "Artificial", "ChatGPT", "OpenAI"]


def collect_reddit(db=None, settings: dict | None = None) -> CollectorBatch:
    settings = settings or {}
    client_id = settings.get("reddit_client_id", "")
    client_secret = settings.get("reddit_client_secret", "")
    user_agent = settings.get("reddit_user_agent", "StartupRadar/1.0")
    limit = min(int(settings.get("collectors_limit", 20) or 20), 100)
    started_at = datetime.utcnow()

    if not client_id or not client_secret:
        return batch("reddit", "skipped", [], "Reddit credentials are not configured.", started_at)

    def _collect() -> list[RawSignal]:
        token = _get_reddit_access_token(client_id, client_secret, user_agent)
        headers = {"Authorization": f"Bearer {token}", "User-Agent": user_agent}
        records: list[RawSignal] = []
        for subreddit in SUBREDDITS:
            response = _get_with_retry(
                f"https://oauth.reddit.com/r/{subreddit}/hot",
                headers=headers,
                params={"limit": limit},
            )
            for child in response.get("data", {}).get("children", []):
                post = child.get("data", {})
                title = post.get("title") or ""
                external_id = post.get("id") or ""
                if not title or not external_id:
                    continue
                created_utc = post.get("created_utc") or datetime.utcnow().timestamp()
                published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc).replace(tzinfo=None)
                permalink = post.get("permalink") or ""
                selftext = post.get("selftext") or ""
                records.append(
                    RawSignal(
                        source="reddit",
                        external_id=external_id,
                        title=f"[r/{subreddit}] {title}",
                        description=f"{selftext[:800]} Reddit score: {post.get('score') or 0}; comments: {post.get('num_comments') or 0}.",
                        url=f"https://reddit.com{permalink}" if permalink else "",
                        engagement_score=int(post.get("score") or 0),
                        published_at=published_at,
                        raw_payload={
                            "subreddit": subreddit,
                            "author": post.get("author"),
                            "comments": int(post.get("num_comments") or 0),
                        },
                    )
                )
        return records

    return guarded_collect("reddit", _collect, started_at)


def _get_reddit_access_token(client_id: str, client_secret: str, user_agent: str) -> str:
    response = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        headers={"User-Agent": user_agent},
        data={"grant_type": "client_credentials"},
        auth=HTTPBasicAuth(client_id, client_secret),
        timeout=15,
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("Reddit did not return an access token.")
    return token


def _get_with_retry(url: str, headers: dict, params: dict) -> dict:
    backoff = 2
    for attempt in range(4):
        response = requests.get(url, headers=headers, params=params, timeout=20)
        if response.status_code == 429:
            reset = response.headers.get("x-ratelimit-reset")
            sleep_time = max(float(reset or 30), 1.0)
            time.sleep(sleep_time)
            continue
        if response.status_code >= 500 and attempt < 3:
            time.sleep(backoff)
            backoff *= 2
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"Reddit request failed after retries: {url}")
