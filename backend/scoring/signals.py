from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from scoring.scale import clamp, log_scale, recency_decay

SOURCE_WEIGHTS: dict[str, float] = {
    "github": 1.2,
    "hacker_news": 0.95,
    "reddit": 0.9,
    "arxiv": 0.85,
    "product_hunt": 0.8,
}


def calculate_signal_strength(source: str, engagement_score: int, published_at: datetime, now: datetime | None = None) -> float:
    base = log_scale(max(engagement_score, 0), divisor=10000, maximum=35)
    if source == "arxiv" and engagement_score == 0:
        base = 8.0
    strength = base * SOURCE_WEIGHTS.get(source, 0.7) * recency_decay(published_at, now=now)
    return round(clamp(strength, 0, 45), 3)


def calculate_confidence(source_counts: Mapping[str, int], evidence_terms: int = 0, history_points: int = 0) -> float:
    source_diversity = min(len([v for v in source_counts.values() if v > 0]) / 5.0, 1.0) * 45
    volume = min(sum(source_counts.values()) / 40.0, 1.0) * 25
    evidence = min(evidence_terms / 12.0, 1.0) * 15
    history = min(history_points / 8.0, 1.0) * 15
    return round(clamp(source_diversity + volume + evidence + history), 2)
