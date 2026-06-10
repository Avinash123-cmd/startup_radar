"""
GET /startup-generator
GET /startup-generator/{category_slug}

Returns fully-detailed, actionable startup briefs generated from the
Opportunity Scoring V2 pipeline.  Each brief includes all 11 required fields
plus an explicit WHY explanation that traces the recommendation to live metrics.

Existing endpoints are not modified.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from database.db import get_db
from opportunities.startup_generator_v2 import (
    StartupBriefV2,
    generate_startup_briefs,
    generate_startup_brief_for_category,
)
from opportunities.scoring_v2 import _WEIGHTS

router = APIRouter(tags=["Startup Generator"])


# ---------------------------------------------------------------------------
# Pydantic response schemas
# ---------------------------------------------------------------------------

class FactorScoresOut(BaseModel):
    founder_difficulty: float = Field(..., ge=0, le=100)
    revenue_potential: float = Field(..., ge=0, le=100)
    market_timing: float = Field(..., ge=0, le=100)
    competition_density: float = Field(..., ge=0, le=100)
    growth_velocity: float = Field(..., ge=0, le=100)
    vc_attractiveness: float = Field(..., ge=0, le=100)

    model_config = ConfigDict(from_attributes=True)


class StartupBriefOut(BaseModel):
    # Identity
    category: str = Field(..., description="Market category name")
    category_slug: str = Field(..., description="URL-safe category slug")
    category_id: int

    # 11 required startup fields
    startup_name: str = Field(
        ..., description="Generated startup name derived from blueprint + strongest signal"
    )
    problem_statement: str = Field(
        ..., description="Core problem this startup solves"
    )
    target_customer: str = Field(
        ..., description="Ideal customer profile"
    )
    mvp_features: List[str] = Field(
        default_factory=list,
        description="MVP features ordered by pain-term relevance",
    )
    pricing_model: str = Field(..., description="Recommended pricing structure")
    revenue_potential: str = Field(
        ..., description="Quantified revenue ceiling estimate with rationale"
    )
    competitive_advantage: str = Field(
        ..., description="Derived competitive advantage based on density, timing, and difficulty factors"
    )
    go_to_market: str = Field(
        ..., description="GTM strategy enriched with live signal channel data"
    )
    build_difficulty: str = Field(
        ..., description="Engineering complexity adjusted by live founder_difficulty score: Low | Medium | High"
    )
    estimated_time_to_mvp: str = Field(
        ..., description="Calendar time estimate to working MVP"
    )
    success_probability: int = Field(
        ..., ge=0, le=100,
        description="Weighted composite Startup Success Probability from Opportunity Scoring V2",
    )

    # Scoring detail
    factors: FactorScoresOut = Field(
        ..., description="Six-factor breakdown from Opportunity Scoring V2"
    )
    opportunity_score_v1: int = Field(..., ge=0, le=100, description="V1 baseline opportunity score")
    demand_score: int = Field(..., ge=0, le=100)
    competition_score: int = Field(..., ge=0, le=100)

    # Explainability — the WHY
    why: str = Field(
        ..., description=(
            "Explicit metric-traced explanation of why this startup idea was generated. "
            "Cites gap score, V2 factor scores, evidence terms, and pain signals."
        ),
    )
    strongest_signals: List[str] = Field(
        default_factory=list, description="Top positive signals from Opportunity V2"
    )
    risk_factors: List[str] = Field(
        default_factory=list, description="Key risks and headwinds"
    )

    model_config = ConfigDict(from_attributes=True)


class StartupGeneratorResponse(BaseModel):
    total: int
    generated_at: str
    scoring_weights: dict = Field(
        ..., description="Factor weights used in success_probability calculation"
    )
    briefs: List[StartupBriefOut]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _to_out(brief: StartupBriefV2) -> StartupBriefOut:
    return StartupBriefOut(
        category=brief.category,
        category_slug=brief.category_slug,
        category_id=brief.category_id,
        startup_name=brief.startup_name,
        problem_statement=brief.problem_statement,
        target_customer=brief.target_customer,
        mvp_features=brief.mvp_features,
        pricing_model=brief.pricing_model,
        revenue_potential=brief.revenue_potential,
        competitive_advantage=brief.competitive_advantage,
        go_to_market=brief.go_to_market,
        build_difficulty=brief.build_difficulty,
        estimated_time_to_mvp=brief.estimated_time_to_mvp,
        success_probability=brief.success_probability,
        factors=FactorScoresOut(
            founder_difficulty=brief.factors.founder_difficulty,
            revenue_potential=brief.factors.revenue_potential,
            market_timing=brief.factors.market_timing,
            competition_density=brief.factors.competition_density,
            growth_velocity=brief.factors.growth_velocity,
            vc_attractiveness=brief.factors.vc_attractiveness,
        ),
        opportunity_score_v1=brief.opportunity_score_v1,
        demand_score=brief.demand_score,
        competition_score=brief.competition_score,
        why=brief.why,
        strongest_signals=brief.strongest_signals,
        risk_factors=brief.risk_factors,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/startup-generator",
    response_model=StartupGeneratorResponse,
    summary="Generate all startup briefs (V2)",
    description=(
        "Generates fully-detailed startup opportunity briefs from the Opportunity "
        "Scoring V2 pipeline. Each brief covers all 11 fields (name, problem, customer, "
        "MVP, pricing, revenue, advantage, GTM, difficulty, time-to-MVP, probability) "
        "plus an explicit WHY explanation tracing the recommendation to live metrics. "
        "Results are sorted by success_probability descending."
    ),
)
def get_startup_briefs(
    min_probability: int = Query(
        0, ge=0, le=100,
        description="Minimum success_probability threshold",
    ),
    limit: int = Query(
        20, ge=1, le=50,
        description="Maximum number of briefs to return",
    ),
    db: Session = Depends(get_db),
) -> StartupGeneratorResponse:
    try:
        briefs = generate_startup_briefs(db)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Startup Generator V2 failed: {exc}. "
                "Ensure the pipeline has been run at least once."
            ),
        ) from exc

    if min_probability > 0:
        briefs = [b for b in briefs if b.success_probability >= min_probability]

    briefs = briefs[:limit]

    return StartupGeneratorResponse(
        total=len(briefs),
        generated_at=datetime.now(timezone.utc).isoformat(),
        scoring_weights=_WEIGHTS,
        briefs=[_to_out(b) for b in briefs],
    )


@router.get(
    "/startup-generator/{category_slug}",
    response_model=StartupBriefOut,
    summary="Generate a startup brief for a specific category",
    description=(
        "Returns a single fully-detailed startup brief for the given category slug. "
        "Returns 404 if no V2 opportunity is detected for that category, or if "
        "insufficient market data is available."
    ),
)
def get_startup_brief_by_category(
    category_slug: str,
    db: Session = Depends(get_db),
) -> StartupBriefOut:
    try:
        brief = generate_startup_brief_for_category(db, category_slug)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Startup Generator V2 failed for '{category_slug}': {exc}",
        ) from exc

    if not brief:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No startup brief generated for category '{category_slug}'. "
                "The category may not have a detected market gap, or the pipeline "
                "has not been run yet."
            ),
        )

    return _to_out(brief)
