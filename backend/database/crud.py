from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import json
from classification.taxonomy import category_seed_rows
from database.models import (
    Alert,
    Category,
    CollectorRun,
    MarketDataPoint,
    Opportunity,
    PipelineRun,
    Repository,
    RepositorySnapshot,
    TrendHistory,
    WeeklyReport,
    Watchlist,
    WatchlistCategory,
    WatchlistRepository,
)

# ==========================================
# CATEGORIES CRUD
# ==========================================
def get_categories(db: Session):
    return db.query(Category).all()

def get_category_by_slug(db: Session, slug: str):
    return db.query(Category).filter(Category.slug == slug).first()

def create_category(db: Session, name: str, slug: str, description: str = None):
    db_cat = Category(name=name, slug=slug, description=description)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

def seed_categories(db: Session):
    default_categories = category_seed_rows()
    
    seeded = []
    for cat in default_categories:
        existing = db.query(Category).filter(Category.slug == cat["slug"]).first()
        if not existing:
            new_cat = create_category(db, cat["name"], cat["slug"], cat["description"])
            seeded.append(new_cat)
    return seeded

# ==========================================
# REPOSITORIES CRUD
# ==========================================
def get_repositories(db: Session, category_id: int = None, language: str = None, search: str = None, skip: int = 0, limit: int = 50, sort_by: str = "stars", order: str = "desc"):
    query = db.query(Repository)
    
    if category_id:
        query = query.filter(Repository.category_id == category_id)
        
    if language:
        query = query.filter(Repository.language == language)
        
    if search:
        query = query.filter(
            (Repository.name.ilike(f"%{search}%")) | 
            (Repository.full_name.ilike(f"%{search}%")) |
            (Repository.description.ilike(f"%{search}%"))
        )
        
    # Sorting logic
    allowed_sort_columns = {
        "stars": Repository.stars,
        "forks": Repository.forks,
        "name": Repository.name,
        "created_at": Repository.created_at,
        "updated_at": Repository.updated_at,
    }
    sort_column = allowed_sort_columns.get(sort_by, Repository.stars)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
        
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return items, total

def get_repository_languages(db: Session):
    results = db.query(Repository.language).distinct().all()
    return [r[0] for r in results if r[0]]

def get_repository_by_fullname(db: Session, full_name: str):
    return db.query(Repository).filter(Repository.full_name == full_name).first()

def create_or_update_repository(db: Session, name: str, full_name: str, url: str, description: str, stars: int, forks: int, language: str, category_id: int):
    repo = get_repository_by_fullname(db, full_name)
    now = datetime.utcnow()
    
    if repo:
        repo.description = description
        repo.stars = stars
        repo.forks = forks
        repo.language = language
        repo.category_id = category_id
        repo.updated_at = now
    else:
        repo = Repository(
            name=name,
            full_name=full_name,
            url=url,
            description=description,
            stars=stars,
            forks=forks,
            language=language,
            category_id=category_id,
            created_at=now,
            updated_at=now
        )
        db.add(repo)
    
    db.commit()
    db.refresh(repo)
    
    # Insert repository snapshot
    snapshot = RepositorySnapshot(
        repository_id=repo.id,
        stars=stars,
        forks=forks,
        recorded_at=now
    )
    db.add(snapshot)
    db.commit()
    
    return repo

def get_repository_history(db: Session, repo_id: int, limit: int = 30):
    return db.query(RepositorySnapshot).filter(RepositorySnapshot.repository_id == repo_id).order_by(RepositorySnapshot.recorded_at.asc()).limit(limit).all()

# ==========================================
# MARKET DATA POINTS CRUD (HN, Reddit, etc)
# ==========================================
def get_data_points(db: Session, category_id: int = None, source: str = None, limit: int = 50):
    query = db.query(MarketDataPoint)
    if category_id:
        query = query.filter(MarketDataPoint.category_id == category_id)
    if source:
        query = query.filter(MarketDataPoint.source == source)
    return query.order_by(desc(MarketDataPoint.published_at)).limit(limit).all()

def add_market_data_point(
    db: Session,
    source: str,
    external_id: str,
    title: str,
    description: str,
    url: str,
    engagement_score: int,
    published_at: datetime,
    category_id: int = None,
    normalized_text: str | None = None,
    classification_confidence: float = 0.0,
    classification_evidence: list[str] | str | None = None,
    raw_payload: dict | str | None = None,
):
    # Check for duplicates
    existing = db.query(MarketDataPoint).filter(
        MarketDataPoint.source == source,
        MarketDataPoint.external_id == external_id
    ).first()
    
    if existing:
        existing.engagement_score = engagement_score
        existing.title = title
        existing.description = description
        existing.url = url
        existing.published_at = published_at
        existing.category_id = category_id or existing.category_id
        existing.normalized_text = normalized_text or existing.normalized_text
        existing.classification_confidence = classification_confidence or existing.classification_confidence
        existing.classification_evidence = _json_dumps(classification_evidence) or existing.classification_evidence
        existing.raw_payload = _json_dumps(raw_payload) or existing.raw_payload
        existing.updated_at = datetime.utcnow()
        db.commit()
        return existing
        
    new_point = MarketDataPoint(
        source=source,
        external_id=external_id,
        title=title,
        description=description,
        url=url,
        engagement_score=engagement_score,
        published_at=published_at,
        category_id=category_id,
        normalized_text=normalized_text,
        classification_confidence=classification_confidence,
        classification_evidence=_json_dumps(classification_evidence),
        raw_payload=_json_dumps(raw_payload),
    )
    db.add(new_point)
    db.commit()
    db.refresh(new_point)
    return new_point

# ==========================================
# TREND HISTORY CRUD
# ==========================================
def get_trends(db: Session, limit: int = 30):
    # Returns the latest trend history entry for each category
    subquery = db.query(
        TrendHistory.category_id,
        func.max(TrendHistory.recorded_at).label("max_recorded")
    ).group_by(TrendHistory.category_id).subquery()
    
    return db.query(TrendHistory).join(
        subquery,
        (TrendHistory.category_id == subquery.c.category_id) &
        (TrendHistory.recorded_at == subquery.c.max_recorded)
    ).all()

def get_category_trend_history(db: Session, category_id: int, limit: int = 30):
    return db.query(TrendHistory).filter(TrendHistory.category_id == category_id).order_by(TrendHistory.recorded_at.asc()).limit(limit).all()

def add_trend_history(
    db: Session,
    category_id: int,
    star_count: int,
    star_growth_30d: int,
    growth_rate: float,
    news_volume: int,
    momentum_score: float,
    source_breakdown: dict | None = None,
    score_components: dict | None = None,
):
    new_trend = TrendHistory(
        category_id=category_id,
        star_count=star_count,
        star_growth_30d=star_growth_30d,
        growth_rate=growth_rate,
        news_volume=news_volume,
        momentum_score=momentum_score,
        source_breakdown=_json_dumps(source_breakdown),
        score_components=_json_dumps(score_components),
        recorded_at=datetime.utcnow()
    )
    db.add(new_trend)
    db.commit()
    db.refresh(new_trend)
    return new_trend

# ==========================================
# OPPORTUNITIES CRUD
# ==========================================
def get_opportunities(db: Session, limit: int = 20):
    return db.query(Opportunity).order_by(desc(Opportunity.opportunity_score)).limit(limit).all()

def add_opportunity(
    db: Session,
    title: str,
    description: str,
    niche: str,
    demand_score: int,
    competition_score: int,
    opportunity_score: int,
    potential_ideas: list,
    evidence: dict | None = None,
    gap_score: float = 0.0,
    score_components: dict | None = None,
):
    opp = Opportunity(
        title=title,
        description=description,
        niche=niche,
        demand_score=demand_score,
        competition_score=competition_score,
        opportunity_score=opportunity_score,
        potential_ideas=json.dumps(potential_ideas),
        evidence=_json_dumps(evidence),
        gap_score=gap_score,
        score_components=_json_dumps(score_components),
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp

# ==========================================
# WEEKLY REPORTS CRUD
# ==========================================
def get_weekly_reports(db: Session, limit: int = 10):
    return db.query(WeeklyReport).order_by(desc(WeeklyReport.published_at)).limit(limit).all()

def get_weekly_report_by_slug(db: Session, slug: str):
    return db.query(WeeklyReport).filter(WeeklyReport.slug == slug).first()

def add_weekly_report(db: Session, title: str, slug: str, summary: str, content: str, published_at: datetime = None, context_snapshot: dict | None = None):
    if not published_at:
        published_at = datetime.utcnow()
        
    report = WeeklyReport(
        title=title,
        slug=slug,
        summary=summary,
        content=content,
        published_at=published_at,
        context_snapshot=_json_dumps(context_snapshot),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

# ==========================================
# RESET DATABASE
# ==========================================
def clear_all_data(db: Session):
    db.query(CollectorRun).delete()
    db.query(PipelineRun).delete()
    db.query(WeeklyReport).delete()
    db.query(Opportunity).delete()
    db.query(TrendHistory).delete()
    db.query(MarketDataPoint).delete()
    db.query(RepositorySnapshot).delete()
    db.query(Repository).delete()
    db.query(Category).delete()
    db.commit()

# ==========================================
# PIPELINE STATUS
# ==========================================
def create_pipeline_run(db: Session) -> PipelineRun:
    run = PipelineRun(status="running", started_at=datetime.utcnow())
    db.add(run)
    db.commit()
    db.refresh(run)
    return run

def finish_pipeline_run(db: Session, run: PipelineRun, status: str, records_collected: int = 0, records_saved: int = 0, message: str = "", errors: list[str] | None = None) -> PipelineRun:
    run.status = status
    run.finished_at = datetime.utcnow()
    run.records_collected = records_collected
    run.records_saved = records_saved
    run.message = message
    run.errors = _json_dumps(errors or [])
    db.commit()
    db.refresh(run)
    return run

def add_collector_run(
    db: Session,
    source: str,
    status: str,
    records_collected: int = 0,
    records_saved: int = 0,
    message: str = "",
    pipeline_run_id: int | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> CollectorRun:
    run = CollectorRun(
        pipeline_run_id=pipeline_run_id,
        source=source,
        status=status,
        started_at=started_at or datetime.utcnow(),
        finished_at=finished_at or datetime.utcnow(),
        records_collected=records_collected,
        records_saved=records_saved,
        message=message,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run

def get_latest_pipeline_runs(db: Session, limit: int = 10):
    return db.query(PipelineRun).order_by(desc(PipelineRun.started_at)).limit(limit).all()


def _json_dumps(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


# ==========================================
# WATCHLIST CRUD
# ==========================================
def get_watchlists(db: Session, is_active: bool = True):
    query = db.query(Watchlist)
    if is_active is not None:
        query = query.filter(Watchlist.is_active == (1 if is_active else 0))
    return query.order_by(desc(Watchlist.created_at)).all()


def get_watchlist_by_id(db: Session, watchlist_id: int):
    return db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()


def create_watchlist(db: Session, name: str, description: str = None) -> Watchlist:
    watchlist = Watchlist(name=name, description=description)
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)
    return watchlist


def add_category_to_watchlist(db: Session, watchlist_id: int, category_id: int):
    existing = db.query(WatchlistCategory).filter(
        WatchlistCategory.watchlist_id == watchlist_id,
        WatchlistCategory.category_id == category_id
    ).first()
    if existing:
        return existing
    item = WatchlistCategory(watchlist_id=watchlist_id, category_id=category_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def add_repository_to_watchlist(db: Session, watchlist_id: int, repository_id: int):
    existing = db.query(WatchlistRepository).filter(
        WatchlistRepository.watchlist_id == watchlist_id,
        WatchlistRepository.repository_id == repository_id
    ).first()
    if existing:
        return existing
    item = WatchlistRepository(watchlist_id=watchlist_id, repository_id=repository_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_category_from_watchlist(db: Session, watchlist_id: int, category_id: int):
    db.query(WatchlistCategory).filter(
        WatchlistCategory.watchlist_id == watchlist_id,
        WatchlistCategory.category_id == category_id
    ).delete()
    db.commit()


def remove_repository_from_watchlist(db: Session, watchlist_id: int, repository_id: int):
    db.query(WatchlistRepository).filter(
        WatchlistRepository.watchlist_id == watchlist_id,
        WatchlistRepository.repository_id == repository_id
    ).delete()
    db.commit()


# ==========================================
# ALERT CRUD
# ==========================================
def create_alert(
    db: Session,
    watchlist_id: int,
    severity: str,
    alert_type: str,
    title: str,
    message: str,
    category_id: int = None,
    repository_id: int = None,
    previous_value: float = None,
    current_value: float = None,
    change_percent: float = None,
):
    alert = Alert(
        watchlist_id=watchlist_id,
        severity=severity,
        alert_type=alert_type,
        category_id=category_id,
        repository_id=repository_id,
        title=title,
        message=message,
        previous_value=previous_value,
        current_value=current_value,
        change_percent=change_percent,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_alerts(
    db: Session,
    watchlist_id: int = None,
    severity: str = None,
    is_read: bool = False,
    limit: int = 50
):
    query = db.query(Alert)
    if watchlist_id:
        query = query.filter(Alert.watchlist_id == watchlist_id)
    if severity:
        query = query.filter(Alert.severity == severity)
    if is_read is not None:
        query = query.filter(Alert.is_read == (1 if is_read else 0))
    return query.order_by(desc(Alert.created_at)).limit(limit).all()


def mark_alert_read(db: Session, alert_id: int):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.is_read = 1
        db.commit()
        db.refresh(alert)
    return alert


def get_alert_by_id(db: Session, alert_id: int):
    return db.query(Alert).filter(Alert.id == alert_id).first()


# ==========================================
# PRODUCTION HARDENING / INTEGRITY CRUD
# ==========================================
def prune_repository_snapshots(db: Session, keep_limit: int = 30):
    """
    Keep only the latest `keep_limit` snapshots per repository (ordered by recorded_at desc)
    and delete any older snapshots.
    """
    # Get all repository IDs that have snapshots
    repo_ids = [r[0] for r in db.query(RepositorySnapshot.repository_id).distinct().all()]
    
    for repo_id in repo_ids:
        # Find all snapshots for this repository, ordered by recorded_at descending
        snapshots = (
            db.query(RepositorySnapshot)
            .filter(RepositorySnapshot.repository_id == repo_id)
            .order_by(RepositorySnapshot.recorded_at.desc())
            .all()
        )
        if len(snapshots) > keep_limit:
            to_delete = snapshots[keep_limit:]
            for snap in to_delete:
                db.delete(snap)
    db.commit()


def verify_data_integrity(db: Session):
    warnings = []
    
    # 1. Categories checks
    categories = db.query(Category).all()
    cat_ids = {c.id for c in categories}
    
    # 2. Repository checks
    repos = db.query(Repository).all()
    for repo in repos:
        if repo.category_id not in cat_ids:
            warnings.append(f"Repository {repo.full_name} (ID: {repo.id}) points to non-existent Category ID {repo.category_id}")
            
    # 3. RepositorySnapshot checks
    repo_ids = {r.id for r in repos}
    snapshots = db.query(RepositorySnapshot).all()
    for snap in snapshots:
        if snap.repository_id not in repo_ids:
            warnings.append(f"RepositorySnapshot ID {snap.id} points to non-existent Repository ID {snap.repository_id}")
            
    # 4. TrendHistory checks
    trends = db.query(TrendHistory).all()
    for trend in trends:
        if trend.category_id not in cat_ids:
            warnings.append(f"TrendHistory ID {trend.id} points to non-existent Category ID {trend.category_id}")
            
    # 5. Opportunity checks
    opps = db.query(Opportunity).all()
    for opp in opps:
        matched_cat = [c for c in categories if c.name == opp.niche]
        if not matched_cat:
            warnings.append(f"Opportunity ID {opp.id} (niche: '{opp.niche}') does not match any valid Category name")
            
    # 6. TrendHistory star totals check
    for cat in categories:
        cat_repos = [r for r in repos if r.category_id == cat.id]
        expected_stars = sum(r.stars for r in cat_repos)
        
        latest_trend = (
            db.query(TrendHistory)
            .filter(TrendHistory.category_id == cat.id)
            .order_by(TrendHistory.recorded_at.desc())
            .first()
        )
        if latest_trend and latest_trend.star_count != expected_stars:
            warnings.append(
                f"Category '{cat.name}' star consistency error: "
                f"Repository sum stars = {expected_stars}, TrendHistory star_count = {latest_trend.star_count}"
            )
            
    success = len(warnings) == 0
    return {
        "success": success,
        "warnings": warnings,
        "checked_categories": len(categories),
        "checked_repositories": len(repos),
        "checked_snapshots": len(snapshots),
        "checked_opportunities": len(opps)
    }
