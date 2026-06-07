from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import json
from database.models import Category, Repository, RepositorySnapshot, MarketDataPoint, TrendHistory, Opportunity, WeeklyReport, ProductHuntProduct

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
    default_categories = [
        {"name": "AI Agents", "slug": "ai-agents", "description": "Autonomous agents capable of executing complex workflows and reasoning tasks."},
        {"name": "LLM Applications & Frameworks", "slug": "llm-frameworks", "description": "Frameworks for building applications powered by large language models, including prompt managers, RAG pipelines, and orchestration libraries."},
        {"name": "Browser & Desktop Automation Agents", "slug": "browser-agents", "description": "AI systems designed to control browsers, desktops, and interact with graphical user interfaces."},
        {"name": "Voice & Audio AI", "slug": "voice-ai", "description": "Synthesized voice generator models, real-time translations, speech-to-text converters, and audio intelligence tools."},
        {"name": "AI Coding Assistants", "slug": "coding-agents", "description": "AI models and agents designed to write, refactor, search, and explain codebase systems."},
        {"name": "AI Image & Video Generation", "slug": "multimodal-generation", "description": "Generative diffusion models, text-to-image/video synthesizers, and media editing pipelines."}
    ]
    
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
    sort_column = getattr(Repository, sort_by, Repository.stars)
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

def add_market_data_point(db: Session, source: str, external_id: str, title: str, description: str, url: str, engagement_score: int, published_at: datetime, category_id: int = None):
    # Check for duplicates
    existing = db.query(MarketDataPoint).filter(
        MarketDataPoint.source == source,
        MarketDataPoint.external_id == external_id
    ).first()
    
    if existing:
        existing.engagement_score = engagement_score
        existing.title = title
        existing.description = description
        existing.category_id = category_id or existing.category_id
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
        category_id=category_id
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

def add_trend_history(db: Session, category_id: int, star_count: int, star_growth_30d: int, growth_rate: float, news_volume: int, momentum_score: float):
    new_trend = TrendHistory(
        category_id=category_id,
        star_count=star_count,
        star_growth_30d=star_growth_30d,
        growth_rate=growth_rate,
        news_volume=news_volume,
        momentum_score=momentum_score,
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

def add_opportunity(db: Session, title: str, description: str, niche: str, demand_score: int, competition_score: int, opportunity_score: int, potential_ideas: list):
    opp = Opportunity(
        title=title,
        description=description,
        niche=niche,
        demand_score=demand_score,
        competition_score=competition_score,
        opportunity_score=opportunity_score,
        potential_ideas=json.dumps(potential_ideas)
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

def add_weekly_report(db: Session, title: str, slug: str, summary: str, content: str, published_at: datetime = None):
    if not published_at:
        published_at = datetime.utcnow()
        
    report = WeeklyReport(
        title=title,
        slug=slug,
        summary=summary,
        content=content,
        published_at=published_at
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

# ==========================================
# RESET DATABASE
# ==========================================
def clear_all_data(db: Session):
    db.query(WeeklyReport).delete()
    db.query(Opportunity).delete()
    db.query(TrendHistory).delete()
    db.query(MarketDataPoint).delete()
    db.query(RepositorySnapshot).delete()
    db.query(Repository).delete()
    db.query(ProductHuntProduct).delete()
    db.query(Category).delete()
    db.commit()

# ==========================================
# PRODUCT HUNT CRUD
# ==========================================
def create_or_update_ph_product(
    db: Session,
    ph_id: str,
    name: str,
    tagline: str,
    description: str,
    votes_count: int,
    comments_count: int,
    website_url: str,
    ph_url: str,
    topics: list,
    makers: list,
    launch_date: datetime,
    category_id: int = None
):
    # Calculate scores
    trend_score = votes_count * 0.7 + comments_count * 0.3
    
    # Calculate age decay factor
    age_in_hours = (datetime.utcnow() - launch_date).total_seconds() / 3600.0
    age_decay_factor = 1.0 / ((age_in_hours + 2) ** 1.5)
    final_score = trend_score * age_decay_factor
    
    existing = db.query(ProductHuntProduct).filter(ProductHuntProduct.ph_id == ph_id).first()
    
    if existing:
        existing.name = name
        existing.tagline = tagline
        existing.description = description
        existing.votes_count = votes_count
        existing.comments_count = comments_count
        existing.website_url = website_url
        existing.ph_url = ph_url
        existing.topics = json.dumps(topics)
        existing.makers = json.dumps(makers)
        existing.category_id = category_id or existing.category_id
        existing.trend_score = trend_score
        existing.final_score = final_score
        existing.updated_at = datetime.utcnow()
        db.commit()
        return existing
        
    new_product = ProductHuntProduct(
        ph_id=ph_id,
        name=name,
        tagline=tagline,
        description=description,
        votes_count=votes_count,
        comments_count=comments_count,
        website_url=website_url,
        ph_url=ph_url,
        topics=json.dumps(topics),
        makers=json.dumps(makers),
        launch_date=launch_date,
        category_id=category_id,
        trend_score=trend_score,
        final_score=final_score
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

def get_ph_products(db: Session, trending: bool = False, top: bool = False, limit: int = 20):
    query = db.query(ProductHuntProduct)
    if trending:
        query = query.order_by(desc(ProductHuntProduct.final_score))
    elif top:
        query = query.order_by(desc(ProductHuntProduct.votes_count))
    else:
        query = query.order_by(desc(ProductHuntProduct.launch_date))
    return query.limit(limit).all()
