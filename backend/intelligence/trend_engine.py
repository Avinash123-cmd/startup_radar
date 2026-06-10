from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from database.crud import add_trend_history
from database.models import Category, MarketDataPoint, Repository, RepositorySnapshot, TrendHistory
from intelligence.types import TrendSnapshot
from scoring.market import calculate_momentum
from scoring.signals import calculate_signal_strength


def compute_trends(db: Session) -> list[TrendSnapshot]:
    now = datetime.utcnow()
    window_start = now - timedelta(days=30)
    snapshots: list[TrendSnapshot] = []

    for category in db.query(Category).order_by(Category.name.asc()).all():
        repos = db.query(Repository).filter(Repository.category_id == category.id).all()
        star_count = sum(repo.stars for repo in repos)
        star_growth_30d = _calculate_star_growth(db, repos, window_start)
        growth_rate = _growth_rate(star_count, star_growth_30d)

        signals = (
            db.query(MarketDataPoint)
            .filter(MarketDataPoint.category_id == category.id, MarketDataPoint.published_at >= window_start)
            .all()
        )
        source_counts = Counter(signal.source for signal in signals)
        signal_strength = sum(
            calculate_signal_strength(signal.source, signal.engagement_score, signal.published_at, now)
            for signal in signals
        )
        momentum_score = calculate_momentum(
            star_growth_30d=star_growth_30d,
            growth_rate=growth_rate,
            signal_strength=signal_strength,
            source_count=len(source_counts),
            news_volume=len(signals),
        )
        source_breakdown = dict(source_counts)
        score_components = {
            "signal_strength": round(signal_strength, 3),
            "source_count": float(len(source_counts)),
            "repo_count": float(len(repos)),
        }
        trend = add_trend_history(
            db=db,
            category_id=category.id,
            star_count=star_count,
            star_growth_30d=star_growth_30d,
            growth_rate=growth_rate,
            news_volume=len(signals),
            momentum_score=momentum_score,
            source_breakdown=source_breakdown,
            score_components=score_components,
        )
        snapshots.append(
            TrendSnapshot(
                category_id=category.id,
                category_slug=category.slug,
                star_count=trend.star_count,
                star_growth_30d=trend.star_growth_30d,
                growth_rate=trend.growth_rate,
                news_volume=trend.news_volume,
                momentum_score=trend.momentum_score,
                source_breakdown=source_breakdown,
                score_components=score_components,
            )
        )

    return snapshots


def latest_trends_as_dicts(db: Session) -> list[dict]:
    subquery = (
        db.query(TrendHistory.category_id, func.max(TrendHistory.recorded_at).label("max_recorded"))
        .group_by(TrendHistory.category_id)
        .subquery()
    )
    trends = (
        db.query(TrendHistory)
        .join(subquery, (TrendHistory.category_id == subquery.c.category_id) & (TrendHistory.recorded_at == subquery.c.max_recorded))
        .all()
    )
    return [
        {
            "category_id": trend.category_id,
            "name": trend.category.name,
            "slug": trend.category.slug,
            "description": trend.category.description,
            "star_count": trend.star_count,
            "star_growth_30d": trend.star_growth_30d,
            "growth_rate": trend.growth_rate,
            "news_volume": trend.news_volume,
            "momentum_score": trend.momentum_score,
            "recorded_at": trend.recorded_at,
            "source_breakdown": _loads(trend.source_breakdown, {}),
            "score_components": _loads(trend.score_components, {}),
        }
        for trend in trends
    ]


def _calculate_star_growth(db: Session, repos: list[Repository], window_start: datetime) -> int:
    total = 0
    for repo in repos:
        latest = (
            db.query(RepositorySnapshot)
            .filter(RepositorySnapshot.repository_id == repo.id)
            .order_by(RepositorySnapshot.recorded_at.desc())
            .first()
        )
        baseline = (
            db.query(RepositorySnapshot)
            .filter(RepositorySnapshot.repository_id == repo.id, RepositorySnapshot.recorded_at <= window_start)
            .order_by(RepositorySnapshot.recorded_at.desc())
            .first()
        )
        if not baseline:
            baseline = (
                db.query(RepositorySnapshot)
                .filter(RepositorySnapshot.repository_id == repo.id)
                .order_by(RepositorySnapshot.recorded_at.asc())
                .first()
            )
        if latest and baseline and latest.id != baseline.id:
            total += max(latest.stars - baseline.stars, 0)
    return total


def _growth_rate(star_count: int, star_growth_30d: int) -> float:
    base = star_count - star_growth_30d
    if base <= 0:
        if star_growth_30d > 0:
            return round((star_growth_30d / 1.0) * 100.0, 2)
        return 0.0
    return round((star_growth_30d / base) * 100.0, 2)


def _loads(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback
