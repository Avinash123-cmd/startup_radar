"""
GET /executive-dashboard
=========================
FastAPI endpoint exposing aggregated startup metrics, predictions, recent alerts,
dynamic founder recommendations, and the AI analyst overview.
"""
from __future__ import annotations

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.db import get_db
from opportunities.executive_dashboard import (
    generate_executive_dashboard,
    ExecutiveDashboardPayload,
    AlertSummaryOut,
    FounderRecommendation,
    AISummaryResult
)

router = APIRouter(tags=["Executive Dashboard"])

# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class FactorScoresOut(BaseModel):
    founder_difficulty: float
    revenue_potential: float
    market_timing: float
    competition_density: float
    growth_velocity: float
    vc_attractiveness: float


class OpportunityDetailOut(BaseModel):
    category: str
    category_slug: str
    category_id: int
    success_probability: int
    demand_score: int
    competition_score: int
    opportunity_score_v1: int
    factors: FactorScoresOut
    reasoning: str
    strongest_signals: List[str]
    risk_factors: List[str]


class StartupBriefDetailOut(BaseModel):
    startup_name: str
    category: str
    category_slug: str
    problem_statement: str
    target_customer: str
    mvp_features: List[str]
    pricing_model: str
    revenue_potential: str
    competitive_advantage: str
    go_to_market: str
    build_difficulty: str
    estimated_time_to_mvp: str
    success_probability: int


class CategoryTrendOut(BaseModel):
    category_id: int
    name: str
    slug: str
    description: str | None = None
    star_count: int
    star_growth_30d: int
    growth_rate: float
    news_volume: int
    momentum_score: float
    recorded_at: str
    source_breakdown: dict[str, int]
    score_components: dict[str, float]


class PredictionDetailOut(BaseModel):
    category: str
    category_slug: str
    category_id: int
    growth_probability: float
    confidence: float
    slope: float
    horizon_days: int


class AlertDetailOut(BaseModel):
    id: int
    watchlist_id: int
    severity: str
    alert_type: str
    title: str
    message: str
    previous_value: float | None = None
    current_value: float | None = None
    change_percent: float | None = None
    is_read: bool
    created_at: str
    category_slug: str | None = None
    repository_name: str | None = None


class AlertSummaryOutModel(BaseModel):
    total: int
    unread: int
    severity_breakdown: dict[str, int]
    recent_alerts: List[AlertDetailOut]


class FounderRecommendationOut(BaseModel):
    category: str
    category_slug: str
    rec_type: str
    text: str
    metric: str


class AISummaryResultOut(BaseModel):
    executive_summary: str
    market_risk_summary: str
    model_used: str
    fallback_mode: bool


class ExecutiveDashboardResponse(BaseModel):
    generated_at: str
    top_opportunities: List[OpportunityDetailOut]
    top_startup_ideas: List[StartupBriefDetailOut]
    fastest_growing_categories: List[CategoryTrendOut]
    highest_confidence_predictions: List[PredictionDetailOut]
    watchlist_alerts_summary: AlertSummaryOutModel
    founder_recommendations: List[FounderRecommendationOut]
    ai_summary: AISummaryResultOut
    platform_status: str
    warnings: List[str]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/executive-dashboard",
    response_model=ExecutiveDashboardResponse,
    summary="Get aggregated executive dashboard metrics",
    description=(
        "Returns a comprehensive overview of the market intelligence platform, including: "
        "1. Top 10 Opportunities (OpportunityV2 with success probability)\n"
        "2. Top 10 Startup Ideas (briefs)\n"
        "3. Fastest Growing Categories\n"
        "4. Highest Confidence Predictions\n"
        "5. Watchlist Alerts Summary\n"
        "6. Dynamic Founder Recommendations\n"
        "7. AI-Generated Executive Summary and Risk Overview.\n\n"
        "Cached for 10 minutes to protect performance. Pass force_refresh=True to bypass cache."
    ),
)
def get_executive_dashboard(
    force_refresh: bool = Query(False, description="Bypass cache and force refresh summaries"),
    db: Session = Depends(get_db)
) -> ExecutiveDashboardResponse:
    try:
        payload = generate_executive_dashboard(db, force_refresh=force_refresh)
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate executive dashboard: {exc}"
        ) from exc
