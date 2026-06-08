from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import Category, MarketDataPoint, Repository, TrendHistory
from forecasting.forecast_engine import generate_forecasts
from intelligence.types import MarketGap
from scoring.market import calculate_competition, calculate_demand, calculate_opportunity
from scoring.signals import calculate_confidence

PAIN_TERMS = [
    "latency",
    "cost",
    "security",
    "compliance",
    "workflow",
    "automation",
    "migration",
    "testing",
    "monitoring",
    "evaluation",
    "deployment",
    "reliability",
    "privacy",
    "integration",
]


def detect_market_gaps(db: Session) -> list[MarketGap]:
    forecasts = {forecast.category_id: forecast for forecast in generate_forecasts(db)}
    gaps: list[MarketGap] = []
    window_start = datetime.utcnow() - timedelta(days=30)

    for category in db.query(Category).order_by(Category.name.asc()).all():
        trend = (
            db.query(TrendHistory)
            .filter(TrendHistory.category_id == category.id)
            .order_by(TrendHistory.recorded_at.desc())
            .first()
        )
        if not trend:
            continue

        repo_count = db.query(Repository).filter(Repository.category_id == category.id).count()
        avg_stars = db.query(func.avg(Repository.stars)).filter(Repository.category_id == category.id).scalar() or 0
        mature_repo_count = (
            db.query(Repository)
            .filter(Repository.category_id == category.id, Repository.stars >= 10000)
            .count()
        )
        competition = calculate_competition(repo_count, avg_stars, mature_repo_count)
        source_counts = _source_breakdown(trend)
        evidence_terms = _evidence_terms(db, category.id, window_start)
        confidence = calculate_confidence(source_counts, evidence_terms=len(evidence_terms), history_points=_history_points(db, category.id))
        forecast = forecasts.get(category.id)
        forecast_probability = forecast.growth_probability if forecast else int(trend.momentum_score)
        demand = calculate_demand(trend.momentum_score, forecast_probability, confidence)
        opportunity = calculate_opportunity(demand, competition, confidence)
        evidence_titles = _evidence_titles(db, category.id, window_start)
        pain_terms = _pain_terms(db, category.id, window_start)
        gap_score = round(demand - competition + confidence * 0.15, 2)

        if demand >= 20 or opportunity >= 35:
            gaps.append(
                MarketGap(
                    category_id=category.id,
                    category=category.name,
                    slug=category.slug,
                    demand_score=demand,
                    competition_score=competition,
                    opportunity_score=opportunity,
                    gap_score=gap_score,
                    confidence=confidence,
                    evidence_terms=evidence_terms,
                    evidence_titles=evidence_titles,
                    pain_terms=pain_terms,
                )
            )

    gaps.sort(key=lambda gap: gap.opportunity_score, reverse=True)
    return gaps


def _source_breakdown(trend: TrendHistory) -> dict[str, int]:
    if not trend.source_breakdown:
        return {}
    try:
        return json.loads(trend.source_breakdown)
    except json.JSONDecodeError:
        return {}


def _evidence_terms(db: Session, category_id: int, window_start: datetime) -> list[str]:
    counter: Counter[str] = Counter()
    rows = (
        db.query(MarketDataPoint.classification_evidence)
        .filter(MarketDataPoint.category_id == category_id, MarketDataPoint.published_at >= window_start)
        .all()
    )
    for (value,) in rows:
        if not value:
            continue
        try:
            terms = json.loads(value)
        except json.JSONDecodeError:
            terms = []
        counter.update(term for term in terms if term)
    return [term for term, _ in counter.most_common(8)]


def _evidence_titles(db: Session, category_id: int, window_start: datetime) -> list[str]:
    rows = (
        db.query(MarketDataPoint)
        .filter(MarketDataPoint.category_id == category_id, MarketDataPoint.published_at >= window_start)
        .order_by(MarketDataPoint.engagement_score.desc(), MarketDataPoint.published_at.desc())
        .limit(5)
        .all()
    )
    return [row.title for row in rows]


def _pain_terms(db: Session, category_id: int, window_start: datetime) -> list[str]:
    text = " ".join(
        row[0] or ""
        for row in db.query(MarketDataPoint.normalized_text)
        .filter(MarketDataPoint.category_id == category_id, MarketDataPoint.published_at >= window_start)
        .limit(100)
        .all()
    ).lower()
    found = [term for term in PAIN_TERMS if term in text]
    return found[:5] or ["integration", "workflow", "reliability"]


def _history_points(db: Session, category_id: int) -> int:
    return db.query(TrendHistory).filter(TrendHistory.category_id == category_id).count()
