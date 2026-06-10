from __future__ import annotations

from collectors.arxiv_collector import collect_arxiv
from collectors.github_collector import collect_github
from collectors.hn_collector import collect_hn
from collectors.ph_collector import collect_ph
from collectors.reddit_collector import collect_reddit
from config import get_runtime_settings
from intelligence.types import CollectorBatch

import concurrent.futures
from datetime import datetime

COLLECTORS = [
    collect_github,
    collect_hn,
    collect_reddit,
    collect_arxiv,
    collect_ph,
]


def collect_all_sources(settings: dict | None = None) -> list[CollectorBatch]:
    settings = settings or get_runtime_settings()
    
    # Run collectors concurrently to avoid sequential blocking on I/O network requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(COLLECTORS)) as executor:
        collector_to_future = {
            collector: executor.submit(collector, settings=settings)
            for collector in COLLECTORS
        }
        
        results: list[CollectorBatch] = []
        for collector in COLLECTORS:
            future = collector_to_future[collector]
            try:
                results.append(future.result())
            except Exception as exc:
                source_name = collector.__name__.replace("collect_", "")
                # Gracefully catch thread crashes and formulate a failed batch report
                results.append(
                    CollectorBatch(
                        source=source_name,
                        status="failed",
                        records=[],
                        message=f"Concurrently raised: {exc}",
                        started_at=datetime.utcnow(),
                        finished_at=datetime.utcnow(),
                    )
                )
        return results


def run_all_collectors():
    from pipeline import collect_and_persist_signals

    return collect_and_persist_signals(get_runtime_settings())


if __name__ == "__main__":
    for result in collect_all_sources():
        print(f"{result.source}: {result.status} ({len(result.records)} records) {result.message}")
