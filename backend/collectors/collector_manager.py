from __future__ import annotations

from collectors.arxiv_collector import collect_arxiv
from collectors.github_collector import collect_github
from collectors.hn_collector import collect_hn
from collectors.ph_collector import collect_ph
from collectors.reddit_collector import collect_reddit
from config import get_runtime_settings
from intelligence.types import CollectorBatch

COLLECTORS = [
    collect_github,
    collect_hn,
    collect_reddit,
    collect_arxiv,
    collect_ph,
]


def collect_all_sources(settings: dict | None = None) -> list[CollectorBatch]:
    settings = settings or get_runtime_settings()
    return [collector(settings=settings) for collector in COLLECTORS]


def run_all_collectors():
    from pipeline import collect_and_persist_signals

    return collect_and_persist_signals(get_runtime_settings())


if __name__ == "__main__":
    for result in collect_all_sources():
        print(f"{result.source}: {result.status} ({len(result.records)} records) {result.message}")
