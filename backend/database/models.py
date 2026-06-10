from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    repositories = relationship("Repository", back_populates="category", cascade="all, delete-orphan")
    data_points = relationship("MarketDataPoint", back_populates="category", cascade="all, delete-orphan")
    trends = relationship("TrendHistory", back_populates="category", cascade="all, delete-orphan")

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(255), unique=True, index=True, nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    stars = Column(Integer, index=True, default=0)
    forks = Column(Integer, default=0)
    language = Column(String(50), index=True, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="repositories")
    snapshots = relationship("RepositorySnapshot", back_populates="repository", cascade="all, delete-orphan")

class RepositorySnapshot(Base):
    __tablename__ = "repository_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    stars = Column(Integer, nullable=False)
    forks = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    repository = relationship("Repository", back_populates="snapshots")

class MarketDataPoint(Base):
    __tablename__ = "market_data_points"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), index=True, nullable=False)  # 'github', 'hacker_news', 'reddit', 'arxiv', 'product_hunt'
    external_id = Column(String(255), index=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(1000), nullable=True)
    engagement_score = Column(Integer, default=0, index=True)
    published_at = Column(DateTime, index=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    normalized_text = Column(Text, nullable=True)
    classification_confidence = Column(Float, default=0.0)
    classification_evidence = Column(Text, nullable=True)
    raw_payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="data_points")

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uix_source_external_id"),
    )

class TrendHistory(Base):
    __tablename__ = "trend_history"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    star_count = Column(Integer, default=0)
    star_growth_30d = Column(Integer, default=0)
    growth_rate = Column(Float, default=0.0)
    news_volume = Column(Integer, default=0)
    momentum_score = Column(Float, default=0.0)
    source_breakdown = Column(Text, nullable=True)
    score_components = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    category = relationship("Category", back_populates="trends")

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    niche = Column(String(100), nullable=False)
    demand_score = Column(Integer, default=0)       # 1-100
    competition_score = Column(Integer, default=0)  # 1-100
    opportunity_score = Column(Integer, default=0)  # 1-100
    potential_ideas = Column(Text, nullable=True)   # JSON string list of potential ideas
    evidence = Column(Text, nullable=True)
    gap_score = Column(Float, default=0.0)
    score_components = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Markdown content
    context_snapshot = Column(Text, nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(30), index=True, nullable=False, default="running")
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    finished_at = Column(DateTime, nullable=True)
    records_collected = Column(Integer, default=0)
    records_saved = Column(Integer, default=0)
    message = Column(Text, nullable=True)
    errors = Column(Text, nullable=True)

    collector_runs = relationship("CollectorRun", back_populates="pipeline_run", cascade="all, delete-orphan")

class CollectorRun(Base):
    __tablename__ = "collector_runs"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_run_id = Column(Integer, ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=True)
    source = Column(String(50), index=True, nullable=False)
    status = Column(String(30), index=True, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    finished_at = Column(DateTime, nullable=True)
    records_collected = Column(Integer, default=0)
    records_saved = Column(Integer, default=0)
    message = Column(Text, nullable=True)

    pipeline_run = relationship("PipelineRun", back_populates="collector_runs")


# ==========================================
# WATCHLIST MODELS
# ==========================================
class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Integer, default=1, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category_items = relationship("WatchlistCategory", back_populates="watchlist", cascade="all, delete-orphan")
    repository_items = relationship("WatchlistRepository", back_populates="watchlist", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistCategory(Base):
    __tablename__ = "watchlist_categories"

    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    watchlist = relationship("Watchlist", back_populates="category_items")
    category = relationship("Category")


class WatchlistRepository(Base):
    __tablename__ = "watchlist_repositories"

    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    watchlist = relationship("Watchlist", back_populates="repository_items")
    repository = relationship("Repository")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False)
    severity = Column(String(20), index=True, nullable=False)
    alert_type = Column(String(50), index=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    previous_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    change_percent = Column(Float, nullable=True)
    is_read = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    watchlist = relationship("Watchlist", back_populates="alerts")
    category = relationship("Category")
    repository = relationship("Repository")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

