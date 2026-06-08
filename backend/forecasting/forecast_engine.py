from __future__ import annotations

from statistics import mean

from sqlalchemy.orm import Session

from database.models import Category, TrendHistory
from intelligence.types import ForecastResult
from scoring.market import calculate_growth_probability
from scoring.signals import calculate_confidence


def generate_forecasts(db: Session, horizon_days: int = 30) -> list[ForecastResult]:
    results: list[ForecastResult] = []
    for category in db.query(Category).order_by(Category.name.asc()).all():
        history = (
            db.query(TrendHistory)
            .filter(TrendHistory.category_id == category.id)
            .order_by(TrendHistory.recorded_at.asc())
            .limit(60)
            .all()
        )
        if not history:
            continue
        slope = _momentum_slope(history)
        current = history[-1].momentum_score
        source_counts = _latest_source_counts(history[-1])
        confidence = calculate_confidence(source_counts, history_points=len(history))
        probability = calculate_growth_probability(slope=slope, current_momentum=current, confidence=confidence)
        results.append(
            ForecastResult(
                category_id=category.id,
                category=category.name,
                category_slug=category.slug,
                growth_probability=probability,
                confidence=confidence,
                slope=round(slope, 4),
                horizon_days=horizon_days,
            )
        )
    results.sort(key=lambda item: item.growth_probability, reverse=True)
    return results


def _momentum_slope(history: list[TrendHistory]) -> float:
    if len(history) < 2:
        return 0.0
    xs = [(item.recorded_at - history[0].recorded_at).total_seconds() / 86400.0 for item in history]
    ys = [item.momentum_score for item in history]
    x_mean = mean(xs)
    y_mean = mean(ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return 0.0
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator


def _latest_source_counts(trend: TrendHistory) -> dict[str, int]:
    import json

    if not trend.source_breakdown:
        return {}
    try:
        return json.loads(trend.source_breakdown)
    except json.JSONDecodeError:
        return {}
