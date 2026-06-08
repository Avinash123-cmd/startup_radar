from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RawSignal:
    source: str
    external_id: str
    title: str
    description: str = ""
    url: str = ""
    engagement_score: int = 0
    published_at: datetime | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CollectorBatch:
    source: str
    status: str
    records: list[RawSignal] = field(default_factory=list)
    message: str = ""
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass(frozen=True)
class ClassificationResult:
    category_slug: str
    confidence: float
    evidence_terms: list[str]


@dataclass(frozen=True)
class NormalizedSignal:
    source: str
    external_id: str
    title: str
    description: str
    url: str
    engagement_score: int
    published_at: datetime
    normalized_text: str
    category_slug: str
    classification_confidence: float
    classification_evidence: list[str]
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TrendSnapshot:
    category_id: int
    category_slug: str
    star_count: int
    star_growth_30d: int
    growth_rate: float
    news_volume: int
    momentum_score: float
    source_breakdown: dict[str, int]
    score_components: dict[str, float]


@dataclass(frozen=True)
class ForecastResult:
    category_id: int
    category: str
    category_slug: str
    growth_probability: int
    confidence: float
    slope: float
    horizon_days: int = 30


@dataclass(frozen=True)
class MarketGap:
    category_id: int
    category: str
    slug: str
    demand_score: int
    competition_score: int
    opportunity_score: int
    gap_score: float
    confidence: float
    evidence_terms: list[str]
    evidence_titles: list[str]
    pain_terms: list[str]


@dataclass(frozen=True)
class OpportunityCandidate:
    title: str
    description: str
    niche: str
    demand_score: int
    competition_score: int
    opportunity_score: int
    potential_ideas: list[str]
    evidence: dict[str, Any]


@dataclass(frozen=True)
class ReportContext:
    trends: list[dict[str, Any]]
    forecasts: list[ForecastResult]
    opportunities: list[dict[str, Any]]
    top_repositories: list[dict[str, Any]]
    top_signals: list[dict[str, Any]]
