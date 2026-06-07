from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# ==========================================
# CATEGORY SCHEMAS
# ==========================================
class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ==========================================
# REPOSITORY SCHEMAS
# ==========================================
class RepositoryBase(BaseModel):
    name: str
    full_name: str
    url: str
    description: Optional[str] = None
    stars: int
    forks: int
    language: Optional[str] = None
    category_id: int

class RepositoryCreate(RepositoryBase):
    pass

class RepositoryOut(RepositoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RepositoryHistoryOut(BaseModel):
    id: int
    repository_id: int
    stars: int
    forks: int
    recorded_at: datetime

    class Config:
        from_attributes = True

class PaginatedRepositories(BaseModel):
    items: List[RepositoryOut]
    total: int
    page: int
    pages: int

# ==========================================
# TREND HISTORY SCHEMAS
# ==========================================
class TrendHistoryBase(BaseModel):
    category_id: int
    star_count: int
    star_growth_30d: int
    growth_rate: float
    news_volume: int
    momentum_score: float

class TrendHistoryOut(TrendHistoryBase):
    id: int
    recorded_at: datetime

    class Config:
        from_attributes = True

class TrendSummary(BaseModel):
    category_id: int
    name: str
    slug: str
    description: Optional[str]
    star_count: int
    star_growth_30d: int
    growth_rate: float
    news_volume: int
    momentum_score: float
    recorded_at: datetime

# ==========================================
# OPPORTUNITY SCHEMAS
# ==========================================
class OpportunityBase(BaseModel):
    title: str
    description: str
    niche: str
    demand_score: int
    competition_score: int
    opportunity_score: int
    potential_ideas: Optional[str] = None  # JSON string representation

class OpportunityOut(OpportunityBase):
    id: int
    created_at: datetime
    parsed_ideas: List[str] = []

    class Config:
        from_attributes = True

# ==========================================
# WEEKLY REPORT SCHEMAS
# ==========================================
class WeeklyReportBase(BaseModel):
    title: str
    slug: str
    summary: Optional[str] = None
    content: str

class WeeklyReportOut(WeeklyReportBase):
    id: int
    published_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# ==========================================
# INSIGHTS & PREDICTIONS
# ==========================================
class QuickInsight(BaseModel):
    leader: str
    score: int
    insight: str

class CategoryPrediction(BaseModel):
    category: str
    growth_probability: int

# ==========================================
# SETTINGS & CONFIG SCHEMAS
# ==========================================
class SettingsConfig(BaseModel):
    mock_mode: bool
    github_token: str
    openai_key: str
    ollama_endpoint: str
    collectors_limit: int

class SettingsConfigUpdate(BaseModel):
    mock_mode: Optional[bool] = None
    github_token: Optional[str] = None
    openai_key: Optional[str] = None
    ollama_endpoint: Optional[str] = None
    collectors_limit: Optional[int] = None
