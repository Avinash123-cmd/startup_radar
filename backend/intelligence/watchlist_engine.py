"""
Watchlist Intelligence Engine
Analyzes active watchlists and generates alerts for detected anomalies.

Fixes applied:
  - Signal activity detection now queries MarketDataPoint (real market signals),
    not RepositorySnapshot (collector artefacts).
  - Momentum spike detection uses absolute score delta, not percentage change,
    eliminating false positives on small low-end values.
  - Alert deduplication: identical (watchlist_id, alert_type, category_id,
    repository_id) tuples are suppressed if a matching alert was created within
    the last 24 hours.
  - analyze_single_watchlist_alerts exposes per-watchlist scanning so the API
    scan endpoint can call it without touching all watchlists.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from database.crud import create_alert, get_watchlists
from database.models import (
    Alert,
    Category,
    MarketDataPoint,
    Repository,
    RepositorySnapshot,
    TrendHistory,
    Watchlist,
)


AlertType = Literal["momentum_spike", "star_growth", "signal_activity"]
Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# Absolute momentum-score delta (0–99 scale) required to raise an alert.
# Previous implementation used *percentage* change which caused false positives
# (e.g. 1→3 = 200% yet only 2 points gained) and false negatives
# (e.g. 80→90 = 12.5% yet 10 points gained).
MOMENTUM_DELTA_THRESHOLDS: dict[str, float] = {
    "LOW": 5.0,
    "MEDIUM": 12.0,
    "HIGH": 25.0,
    "CRITICAL": 40.0,
}

STAR_GROWTH_THRESHOLDS: dict[str, float] = {
    "LOW": 0.10,     # 10 % growth
    "MEDIUM": 0.25,  # 25 %
    "HIGH": 0.50,    # 50 %
    "CRITICAL": 1.00,  # 100 %
}

# Ratio of current-week signal volume vs prior-week signal volume.
SIGNAL_ACTIVITY_THRESHOLDS: dict[str, float] = {
    "LOW": 2.0,
    "MEDIUM": 3.5,
    "HIGH": 5.0,
    "CRITICAL": 10.0,
}

# Deduplication cooldown — suppress identical alerts raised within this window.
ALERT_DEDUP_HOURS = 24


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def analyze_watchlist_alerts(db: Session) -> list[Alert]:
    """Analyse every active watchlist and generate alerts for anomalies."""
    alerts: list[Alert] = []
    for watchlist in get_watchlists(db, is_active=True):
        alerts.extend(analyze_single_watchlist_alerts(db, watchlist))
    return alerts


def analyze_single_watchlist_alerts(db: Session, watchlist: Watchlist) -> list[Alert]:
    """Analyse one watchlist and return newly created Alert objects."""
    alerts: list[Alert] = []

    for wc in watchlist.category_items:
        alerts.extend(_analyze_category_for_alerts(db, wc.category_id, watchlist.id))

    for wr in watchlist.repository_items:
        alerts.extend(_analyze_repository_for_alerts(db, wr.repository_id, watchlist.id))

    return alerts


def clear_alerts_for_watchlist(db: Session, watchlist_id: int) -> int:
    """Clear all alerts for a watchlist. Returns count of cleared alerts."""
    result = db.query(Alert).filter(Alert.watchlist_id == watchlist_id).delete()
    db.commit()
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _determine_severity(value: float, thresholds: dict[str, float]) -> Severity | None:
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if value >= thresholds[severity]:
            return severity
    return None


def _is_alert_duplicate(
    db: Session,
    watchlist_id: int,
    alert_type: str,
    category_id: int | None,
    repository_id: int | None,
) -> bool:
    """Return True if an identical alert was already created within the cooldown window."""
    cutoff = datetime.utcnow() - timedelta(hours=ALERT_DEDUP_HOURS)
    query = db.query(Alert).filter(
        Alert.watchlist_id == watchlist_id,
        Alert.alert_type == alert_type,
        Alert.created_at >= cutoff,
    )
    if category_id is not None:
        query = query.filter(Alert.category_id == category_id)
    if repository_id is not None:
        query = query.filter(Alert.repository_id == repository_id)
    return query.first() is not None


def _maybe_create_alert(db: Session, **kwargs) -> Alert | None:
    """Create an alert only when no duplicate exists within the cooldown window."""
    if _is_alert_duplicate(
        db,
        watchlist_id=kwargs["watchlist_id"],
        alert_type=kwargs["alert_type"],
        category_id=kwargs.get("category_id"),
        repository_id=kwargs.get("repository_id"),
    ):
        return None
    return create_alert(db, **kwargs)


# ---------------------------------------------------------------------------
# Category-level analysis
# ---------------------------------------------------------------------------

def _analyze_category_for_alerts(
    db: Session, category_id: int, watchlist_id: int
) -> list[Alert]:
    alerts: list[Alert] = []

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        return alerts

    now = datetime.utcnow()

    # ------------------------------------------------------------------
    # 1. Momentum spike — absolute delta on the 0–99 score scale.
    # ------------------------------------------------------------------
    trends = (
        db.query(TrendHistory)
        .filter(TrendHistory.category_id == category_id)
        .order_by(desc(TrendHistory.recorded_at))
        .limit(2)
        .all()
    )

    if len(trends) >= 2:
        current_momentum = trends[0].momentum_score
        previous_momentum = trends[1].momentum_score
        delta = current_momentum - previous_momentum

        if delta >= MOMENTUM_DELTA_THRESHOLDS["LOW"]:
            severity = _determine_severity(delta, MOMENTUM_DELTA_THRESHOLDS)
            if severity:
                alert = _maybe_create_alert(
                    db=db,
                    watchlist_id=watchlist_id,
                    severity=severity,
                    alert_type="momentum_spike",
                    category_id=category_id,
                    title=f"Momentum spike detected: {category.name}",
                    message=(
                        f"Momentum score jumped +{delta:.1f} points "
                        f"(from {previous_momentum:.1f} to {current_momentum:.1f})"
                    ),
                    previous_value=previous_momentum,
                    current_value=current_momentum,
                    change_percent=delta,
                )
                if alert:
                    alerts.append(alert)

    # ------------------------------------------------------------------
    # 2. Category star growth — compare current stars vs 7-day baseline.
    # ------------------------------------------------------------------
    repos = db.query(Repository).filter(Repository.category_id == category_id).all()
    if repos:
        current_star_count = sum(repo.stars for repo in repos)
        window_start = now - timedelta(days=7)

        prev_total = 0
        counted_repos = 0
        for repo in repos:
            baseline = (
                db.query(RepositorySnapshot)
                .filter(
                    RepositorySnapshot.repository_id == repo.id,
                    RepositorySnapshot.recorded_at <= window_start,
                )
                .order_by(desc(RepositorySnapshot.recorded_at))
                .first()
            )
            if baseline:
                prev_total += baseline.stars
                counted_repos += 1

        # Only evaluate growth when every repository has a baseline so the
        # denominator is not artificially deflated by newly-added repos.
        if prev_total > 0 and counted_repos == len(repos):
            growth_rate = (current_star_count - prev_total) / prev_total
            if growth_rate >= STAR_GROWTH_THRESHOLDS["LOW"]:
                severity = _determine_severity(growth_rate, STAR_GROWTH_THRESHOLDS)
                if severity:
                    alert = _maybe_create_alert(
                        db=db,
                        watchlist_id=watchlist_id,
                        severity=severity,
                        alert_type="star_growth",
                        category_id=category_id,
                        title=f"Star growth spike: {category.name}",
                        message=(
                            f"Total stars grew {growth_rate * 100:.1f}% in 7 days "
                            f"(from {prev_total:,} to {current_star_count:,})"
                        ),
                        previous_value=float(prev_total),
                        current_value=float(current_star_count),
                        change_percent=growth_rate * 100,
                    )
                    if alert:
                        alerts.append(alert)

    # ------------------------------------------------------------------
    # 3. Signal activity — real market signals from MarketDataPoint.
    #    (Replaces the previous RepositorySnapshot-based query which was
    #    counting collector runs, not market events.)
    # ------------------------------------------------------------------
    window_7d_start = now - timedelta(days=7)
    window_14d_start = now - timedelta(days=14)

    current_signals: int = (
        db.query(func.count(MarketDataPoint.id))
        .filter(
            MarketDataPoint.category_id == category_id,
            MarketDataPoint.published_at >= window_7d_start,
        )
        .scalar()
        or 0
    )

    previous_signals: int = (
        db.query(func.count(MarketDataPoint.id))
        .filter(
            MarketDataPoint.category_id == category_id,
            MarketDataPoint.published_at >= window_14d_start,
            MarketDataPoint.published_at < window_7d_start,
        )
        .scalar()
        or 0
    )

    if previous_signals > 0:
        signal_ratio = current_signals / previous_signals
        if signal_ratio >= SIGNAL_ACTIVITY_THRESHOLDS["LOW"]:
            severity = _determine_severity(signal_ratio, SIGNAL_ACTIVITY_THRESHOLDS)
            if severity:
                alert = _maybe_create_alert(
                    db=db,
                    watchlist_id=watchlist_id,
                    severity=severity,
                    alert_type="signal_activity",
                    category_id=category_id,
                    title=f"Unusual signal activity: {category.name}",
                    message=(
                        f"Market signal volume increased {signal_ratio:.1f}x "
                        f"vs prior week ({previous_signals} → {current_signals} posts)"
                    ),
                    previous_value=float(previous_signals),
                    current_value=float(current_signals),
                    change_percent=(signal_ratio - 1) * 100,
                )
                if alert:
                    alerts.append(alert)

    return alerts


# ---------------------------------------------------------------------------
# Repository-level analysis
# ---------------------------------------------------------------------------

def _analyze_repository_for_alerts(
    db: Session, repository_id: int, watchlist_id: int
) -> list[Alert]:
    alerts: list[Alert] = []

    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repo:
        return alerts

    now = datetime.utcnow()
    window_start = now - timedelta(days=7)

    # Compare latest snapshot against the snapshot closest to 7 days ago,
    # not just the two most recent snapshots (which may be hours apart).
    latest_snapshot = (
        db.query(RepositorySnapshot)
        .filter(RepositorySnapshot.repository_id == repository_id)
        .order_by(desc(RepositorySnapshot.recorded_at))
        .first()
    )

    baseline_snapshot = (
        db.query(RepositorySnapshot)
        .filter(
            RepositorySnapshot.repository_id == repository_id,
            RepositorySnapshot.recorded_at <= window_start,
        )
        .order_by(desc(RepositorySnapshot.recorded_at))
        .first()
    )

    if latest_snapshot and baseline_snapshot and latest_snapshot.id != baseline_snapshot.id:
        current_stars = latest_snapshot.stars
        previous_stars = baseline_snapshot.stars

        if previous_stars > 0:
            growth_rate = (current_stars - previous_stars) / previous_stars
            if growth_rate >= STAR_GROWTH_THRESHOLDS["LOW"]:
                severity = _determine_severity(growth_rate, STAR_GROWTH_THRESHOLDS)
                if severity:
                    alert = _maybe_create_alert(
                        db=db,
                        watchlist_id=watchlist_id,
                        severity=severity,
                        alert_type="star_growth",
                        repository_id=repository_id,
                        title=f"Star growth spike: {repo.full_name}",
                        message=(
                            f"Stars increased {growth_rate * 100:.1f}% over 7 days "
                            f"(from {previous_stars:,} to {current_stars:,})"
                        ),
                        previous_value=float(previous_stars),
                        current_value=float(current_stars),
                        change_percent=growth_rate * 100,
                    )
                    if alert:
                        alerts.append(alert)

    return alerts