from __future__ import annotations

from datetime import datetime
from typing import Callable

from intelligence.types import CollectorBatch


def batch(source: str, status: str, records=None, message: str = "", started_at: datetime | None = None) -> CollectorBatch:
    return CollectorBatch(
        source=source,
        status=status,
        records=list(records or []),
        message=message,
        started_at=started_at or datetime.utcnow(),
        finished_at=datetime.utcnow(),
    )


def guarded_collect(source: str, collector: Callable[[], list], started_at: datetime | None = None) -> CollectorBatch:
    started_at = started_at or datetime.utcnow()
    try:
        records = collector()
        return batch(source, "success", records, f"{len(records)} records collected.", started_at)
    except Exception as exc:
        return batch(source, "failed", [], str(exc), started_at)
