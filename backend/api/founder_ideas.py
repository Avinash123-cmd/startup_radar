"""
GET /founder-ideas
==================
Returns a ranked list of founder-ready startup opportunity briefs derived from
live market gap analysis. Each brief includes category-specific startup ideas,
target customer profiles, MVP features, pricing models, GTM strategies, and a
data-driven confidence score.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.db import get_db
from opportunities.founder_engine import FounderIdea, generate_founder_ideas

router = APIRouter(tags=["Founder Ideas"])


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class FounderIdeaOut(BaseModel):
    title: str = Field(..., description="Opportunity title with primary pain-point focus")
    category: str = Field(..., description="Market category this idea targets")
    opportunity_score: int = Field(..., ge=0, le=100, description="Composite opportunity score (0–100)")
    startup_idea: str = Field(..., description="Specific startup concept to build")
    target_customer: str = Field(..., description="Ideal customer profile description")
    problem_statement: str = Field(..., description="Core problem this startup solves")
    mvp_features: List[str] = Field(default_factory=list, description="Prioritised MVP feature list")
    pricing_model: str = Field(..., description="Recommended pricing structure")
    revenue_model: str = Field(..., description="Revenue model and monetisation approach")
    go_to_market: str = Field(..., description="Go-to-market and distribution strategy")
    competition_level: str = Field(..., description="Assessed competition level: Low | Medium | High")
    build_difficulty: str = Field(..., description="Engineering complexity: Low | Medium | High")
    estimated_time_to_mvp: str = Field(..., description="Estimated calendar time to working MVP")
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "Composite confidence (0.0–1.0) derived from momentum, demand score, "
            "inverse competition, and forecast signal quality"
        ),
    )


class FounderIdeasResponse(BaseModel):
    total: int = Field(..., description="Total number of founder ideas returned")
    ideas: List[FounderIdeaOut]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _to_out(idea: FounderIdea) -> FounderIdeaOut:
    return FounderIdeaOut(
        title=idea.title,
        category=idea.category,
        opportunity_score=idea.opportunity_score,
        startup_idea=idea.startup_idea,
        target_customer=idea.target_customer,
        problem_statement=idea.problem_statement,
        mvp_features=idea.mvp_features,
        pricing_model=idea.pricing_model,
        revenue_model=idea.revenue_model,
        go_to_market=idea.go_to_market,
        competition_level=idea.competition_level,
        build_difficulty=idea.build_difficulty,
        estimated_time_to_mvp=idea.estimated_time_to_mvp,
        confidence=idea.confidence,
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/founder-ideas",
    response_model=FounderIdeasResponse,
    summary="Get founder-ready startup opportunity briefs",
    description=(
        "Analyses live market gaps across tracked AI categories and returns structured "
        "startup opportunity briefs sorted by opportunity score (descending). "
        "Optionally filter by category slug or cap the number of results."
    ),
)
def get_founder_ideas(
    category: str = Query(
        None,
        description=(
            "Optional category slug to filter results "
            "(e.g. 'ai-agents', 'voice-ai', 'coding-agents')"
        ),
    ),
    limit: int = Query(
        20,
        ge=1,
        le=50,
        description="Maximum number of ideas to return (1–50)",
    ),
    min_score: int = Query(
        0,
        ge=0,
        le=100,
        description="Minimum opportunity score threshold (0–100)",
    ),
    db: Session = Depends(get_db),
) -> FounderIdeasResponse:

    # ── Generate ideas from live market gap data ─────────────────────────────
    try:
        ideas = generate_founder_ideas(db)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to generate founder ideas: {exc}. "
                "Ensure the pipeline has been run and market data is available."
            ),
        ) from exc

    # ── Apply optional filters ────────────────────────────────────────────────
    if not ideas:
        return FounderIdeasResponse(total=0, ideas=[])

    if category:
        # Normalise slug comparison (handle spaces vs hyphens, case)
        slug_query = category.lower().replace(" ", "-")
        ideas = [
            i for i in ideas
            # Match on category name (display) or derived slug
            if i.category.lower().replace(" ", "-") == slug_query
            or i.category.lower() == category.lower()
        ]
        if not ideas:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No founder ideas found for category '{category}'. "
                    "Check the slug (e.g. 'ai-agents', 'voice-ai', 'coding-agents', "
                    "'llm-frameworks', 'browser-agents', 'multimodal-generation')."
                ),
            )

    if min_score > 0:
        ideas = [i for i in ideas if i.opportunity_score >= min_score]

    # ── Sort descending by opportunity_score (already sorted; defensive) ─────
    ideas.sort(key=lambda i: i.opportunity_score, reverse=True)

    # ── Apply limit ───────────────────────────────────────────────────────────
    ideas = ideas[:limit]

    return FounderIdeasResponse(
        total=len(ideas),
        ideas=[_to_out(i) for i in ideas],
    )