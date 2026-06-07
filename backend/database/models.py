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
    product_hunt_products = relationship("ProductHuntProduct", back_populates="category", cascade="all, delete-orphan")

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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Markdown content
    published_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductHuntProduct(Base):
    __tablename__ = "product_hunt_products"

    id = Column(Integer, primary_key=True, index=True)
    ph_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    tagline = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    votes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    website_url = Column(String(1000), nullable=True)
    ph_url = Column(String(1000), nullable=True)
    topics = Column(Text, nullable=True)  # JSON-serialized list of strings
    makers = Column(Text, nullable=True)  # JSON-serialized list of strings
    launch_date = Column(DateTime, nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    trend_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="product_hunt_products")