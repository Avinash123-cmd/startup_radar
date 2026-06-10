"""
GET /opportunities/v2
=====================
Returns a ranked list of opportunities scored across six factors with a
Startup Success Probability composite.

Response is fully additive — the existing /opportunities endpoint is unchanged.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from database.db import get_db
from opportunities.scoring_v2 import (
    FactorBreakdown,
    OpportunityV2,
    generate_opportunities_v2,
)

router = APIRouter(tags=["Opportunities V2"])


# ---------------------------------------------------------------------------
# Pydantic response schemas
# ---------------------------------------------------------------------------

class FactorBreakdownOut(BaseModel):
    founder_difficulty: float = Field(
        ..., ge=0, le=100,
        description=(
            "Ease-of-entry for a small founding team (100 = easy). "
            "Derived from repo density, incumbent star counts, and evidence term richness."
        ),
    )
    revenue_potential: float = Field(
        ..., ge=0, le=100,
        description=(
            "Proxy revenue ceiling based on market size signals: total star count, "
            "signal volume, demand score, and source diversity."
        ),
    )
    market_timing: float = Field(
        ..., ge=0, le=100,
        description=(
            "Timing sweet-spot score. Penalises categories that are too early "
            "(no signal) or too late (heavy incumbents). "
            "Rewards accelerating signal velocity and positive momentum slope."
        ),
    )
    competition_density: float = Field(
        ..., ge=0, le=100,
        description=(
            "Inverse competition score (100 = low density). "
            "Higher means less crowded — better for a new entrant."
        ),
    )
    growth_velocity: float = Field(
        ..., ge=0, le=100,
        description=(
            "Current market acceleration: 30-day star growth, growth rate percentage, "
            "signal volume delta, and momentum score."
        ),
    )
    vc_attractiveness: float = Field(
        ..., ge=0, le=100,
        description=(
            "Proxy for investor thesis alignment: large TAM, high growth, "
            "platform/infra potential, and validated pain evidence."
        ),
    )

    model_config = ConfigDict(from_attributes=True)


class OpportunityV2Out(BaseModel):
    category: str
    category_slug: str
    category_id: int

    # V1 baseline scores for comparison
    demand_score: int = Field(..., ge=0, le=100, description="V1 demand score")
    competition_score: int = Field(..., ge=0, le=100, description="V1 competition score")
    opportunity_score_v1: int = Field(..., ge=0, le=100, description="V1 opportunity score")

    # V2 six-factor breakdown
    factors: FactorBreakdownOut

    # Composite
    success_probability: int = Field(
        ..., ge=0, le=100,
        description=(
            "Weighted composite Startup Success Probability (0–100). "
            "Combines all six factors with validated empirical weights."
        ),
    )

    # Narrative
    reasoning: str = Field(..., description="Plain-English explanation of the score")
    strongest_signals: List[str] = Field(
        default_factory=list,
        description="Top positive signals driving this opportunity",
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        description="Key risks and headwinds to watch",
    )

    model_config = ConfigDict(from_attributes=True)


class OpportunitiesV2Response(BaseModel):
    total: int
    generated_at: str = Field(..., description="UTC timestamp of this response")
    weight_config: dict = Field(
        ...,
        description="Factor weights used in success_probability calculation",
    )
    opportunities: List[OpportunityV2Out]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_out(opp: OpportunityV2) -> OpportunityV2Out:
    return OpportunityV2Out(
        category=opp.category,
        category_slug=opp.category_slug,
        category_id=opp.category_id,
        demand_score=opp.demand_score,
        competition_score=opp.competition_score,
        opportunity_score_v1=opp.opportunity_score_v1,
        factors=FactorBreakdownOut(
            founder_difficulty=opp.factors.founder_difficulty,
            revenue_potential=opp.factors.revenue_potential,
            market_timing=opp.factors.market_timing,
            competition_density=opp.factors.competition_density,
            growth_velocity=opp.factors.growth_velocity,
            vc_attractiveness=opp.factors.vc_attractiveness,
        ),
        success_probability=opp.success_probability,
        reasoning=opp.reasoning,
        strongest_signals=opp.strongest_signals,
        risk_factors=opp.risk_factors,
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

from datetime import datetime, timezone
from opportunities.scoring_v2 import _WEIGHTS


@router.get(
    "/opportunities/v2",
    response_model=OpportunitiesV2Response,
    summary="Opportunity Scoring Engine V2",
    description=(
        "Evaluates every detected market gap across six orthogonal scoring dimensions "
        "and returns a Startup Success Probability (0–100) composite. "
        "Reuses the same trend, forecast, and gap data as /opportunities — no new "
        "data collection required. Results are sorted by success_probability descending."
    ),
)
def get_opportunities_v2(
    min_probability: int = Query(
        0,
        ge=0,
        le=100,
        description="Minimum success_probability to include in results (0–100)",
    ),
    category: Optional[str] = Query(
        None,
        description="Filter by category slug (e.g. 'ai-agents')",
    ),
    limit: int = Query(
        25,
        ge=1,
        le=100,
        description="Maximum results to return",
    ),
    db: Session = Depends(get_db),
) -> OpportunitiesV2Response:
    try:
        opportunities = generate_opportunities_v2(db)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Opportunity V2 scoring failed: {exc}. "
                "Ensure the pipeline has been run at least once."
            ),
        ) from exc

    if not opportunities:
        return OpportunitiesV2Response(
            total=0,
            generated_at=datetime.now(timezone.utc).isoformat(),
            weight_config=_WEIGHTS,
            opportunities=[],
        )

    # Apply filters
    if category:
        slug = category.lower().replace(" ", "-")
        opportunities = [
            o for o in opportunities
            if o.category_slug == slug or o.category.lower().replace(" ", "-") == slug
        ]
        if not opportunities:
            raise HTTPException(
                status_code=404,
                detail=f"No V2 opportunities found for category '{category}'.",
            )

    if min_probability > 0:
        opportunities = [o for o in opportunities if o.success_probability >= min_probability]

    opportunities = opportunities[:limit]

    return OpportunitiesV2Response(
        total=len(opportunities),
        generated_at=datetime.now(timezone.utc).isoformat(),
        weight_config=_WEIGHTS,
        opportunities=[_to_out(o) for o in opportunities],
    )
