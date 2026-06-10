from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta
import json

from database.db import get_db
from database.models import TrendHistory, MarketDataPoint, Repository, Category
from database.crud import get_category_by_slug
from pydantic import BaseModel, Field, ConfigDict

router = APIRouter(tags=["Analysis"])

# ==========================================
# RESPONSE SCHEMAS (local to this module)
# ==========================================

class RepositorySummary(BaseModel):
    name: str
    full_name: str
    url: str
    description: Optional[str] = None
    stars: int
    forks: int
    language: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisResponse(BaseModel):
    category: str
    momentum_score: float = Field(..., description="Latest momentum score (0–100)")
    growth_rate: float = Field(..., description="Latest growth rate percentage")
    star_growth_30d: int = Field(..., description="Star growth over the last 30 days")
    top_repositories: List[RepositorySummary] = Field(default_factory=list)
    top_signals: List[str] = Field(default_factory=list, description="Top market signal titles")
    analysis: str = Field(..., description="Human-readable analysis narrative")
    risks: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    confidence: float = Field(..., description="Confidence score (0.0–1.0) based on data availability")


# ==========================================
# HELPERS
# ==========================================

def _parse_json_field(raw: Optional[str]) -> dict:
    """Safely parse a JSON text column; returns empty dict on failure."""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def _build_narrative(
    category_name: str,
    trend: TrendHistory,
    signal_count: int,
    top_repo_names: List[str],
) -> str:
    """Compose a concise analysis paragraph from available metrics."""
    momentum = trend.momentum_score
    growth = trend.growth_rate
    star_growth = trend.star_growth_30d

    strength = (
        "strong upward momentum"
        if momentum >= 70
        else "moderate growth"
        if momentum >= 40
        else "early-stage activity"
    )

    repo_clause = (
        f"Notable repositories include {', '.join(top_repo_names[:3])}."
        if top_repo_names
        else "No dominant repositories have emerged yet."
    )

    signal_clause = (
        f"Market signals are robust with {signal_count} recent data points across news, "
        "community discussions, and research publications."
        if signal_count >= 10
        else f"Market signal coverage is thin ({signal_count} recent data points); "
        "confidence will improve as more data is collected."
    )

    return (
        f"{category_name} is showing {strength} with a momentum score of "
        f"{momentum:.1f}/100 and a 30-day star growth of {star_growth:,}. "
        f"The category's growth rate stands at {growth:.1f}%. "
        f"{repo_clause} {signal_clause}"
    )


def _derive_risks(trend: TrendHistory, signal_count: int, score_components: dict) -> List[str]:
    risks: List[str] = []

    if trend.growth_rate < 5:
        risks.append("Growth rate is below 5%, suggesting the category may be plateauing.")

    if signal_count < 5:
        risks.append(
            "Low market signal volume makes it difficult to validate trend direction with confidence."
        )

    if trend.momentum_score < 30:
        risks.append(
            "Momentum score is in the low tier; the category has not yet reached critical adoption mass."
        )

    news_vol = trend.news_volume or 0
    if news_vol == 0:
        risks.append("No recent news coverage detected; community awareness may be limited.")

    if not risks:
        risks.append("No significant risk factors identified based on current data.")

    return risks


def _derive_opportunities(trend: TrendHistory, signal_count: int, repo_count: int) -> List[str]:
    opps: List[str] = []

    if trend.star_growth_30d > 500:
        opps.append(
            f"High 30-day star growth ({trend.star_growth_30d:,}) signals strong developer interest — "
            "an early entry point for tooling or infrastructure products."
        )

    if trend.momentum_score >= 60:
        opps.append(
            "Momentum is accelerating; SaaS wrappers, managed services, and developer tooling "
            "around leading repositories may find product-market fit quickly."
        )

    if signal_count >= 20:
        opps.append(
            "High signal volume indicates active community discourse — content, education, "
            "and community-led products have strong organic distribution potential."
        )

    if repo_count < 20:
        opps.append(
            "Relatively low repository count suggests the category is not yet saturated; "
            "first-mover advantage is still available."
        )

    if trend.growth_rate >= 10:
        opps.append(
            f"A growth rate of {trend.growth_rate:.1f}% is attractive for venture-scale bets "
            "and warranted for inclusion in an emerging technology portfolio."
        )

    if not opps:
        opps.append(
            "Monitor this category closely — early signals may develop into material opportunities "
            "as the ecosystem matures."
        )

    return opps


def _compute_confidence(trend: TrendHistory, signal_count: int, repo_count: int) -> float:
    """
    Confidence is a weighted score [0.0, 1.0] based on data richness:
      - 40%  : signal (market data points) coverage
      - 30%  : repository coverage
      - 30%  : trend history availability (always 1.0 if we have a trend record)
    """
    MAX_SIGNALS = 50
    MAX_REPOS = 30

    signal_score = min(signal_count / MAX_SIGNALS, 1.0)
    repo_score = min(repo_count / MAX_REPOS, 1.0)
    trend_score = 1.0  # We only reach this point when a TrendHistory row exists

    confidence = (signal_score * 0.40) + (repo_score * 0.30) + (trend_score * 0.30)
    return round(confidence, 3)


# ==========================================
# ENDPOINT
# ==========================================

@router.get(
    "/analysis/{slug}",
    response_model=AnalysisResponse,
    summary="Get structured trend analysis for a category",
    description=(
        "Returns a structured analysis for the given category slug, including momentum score, "
        "growth metrics, top repositories, market signals, risks, opportunities, and a "
        "confidence rating based on available data."
    ),
)
def get_analysis(slug: str, db: Session = Depends(get_db)) -> AnalysisResponse:
    # ── 1. Resolve category ──────────────────────────────────────────────────
    category: Optional[Category] = get_category_by_slug(db, slug)
    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Category with slug '{slug}' not found.",
        )

    # ── 2. Latest TrendHistory record ────────────────────────────────────────
    trend: Optional[TrendHistory] = (
        db.query(TrendHistory)
        .filter(TrendHistory.category_id == category.id)
        .order_by(desc(TrendHistory.recorded_at))
        .first()
    )
    if not trend:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No trend data available for '{category.name}'. "
                "Run the pipeline to collect market data first."
            ),
        )

    # ── 3. Recent MarketDataPoints (last 30 days) ────────────────────────────
    since_30d = datetime.utcnow() - timedelta(days=30)
    market_data_points: List[MarketDataPoint] = (
        db.query(MarketDataPoint)
        .filter(
            MarketDataPoint.category_id == category.id,
            MarketDataPoint.published_at >= since_30d,
        )
        .order_by(desc(MarketDataPoint.engagement_score))
        .limit(50)
        .all()
    )

    # ── 4. Top repositories by star count ────────────────────────────────────
    top_repos: List[Repository] = (
        db.query(Repository)
        .filter(Repository.category_id == category.id)
        .order_by(desc(Repository.stars))
        .limit(10)
        .all()
    )

    # ── 5. Derive computed fields ────────────────────────────────────────────
    signal_count = len(market_data_points)
    repo_count_total: int = (
        db.query(func.count(Repository.id))
        .filter(Repository.category_id == category.id)
        .scalar()
        or 0
    )
    score_components = _parse_json_field(trend.score_components)

    top_signals: List[str] = [mdp.title for mdp in market_data_points[:10]]
    top_repo_names: List[str] = [r.full_name for r in top_repos]

    narrative = _build_narrative(category.name, trend, signal_count, top_repo_names)
    risks = _derive_risks(trend, signal_count, score_components)
    opportunities = _derive_opportunities(trend, signal_count, repo_count_total)
    confidence = _compute_confidence(trend, signal_count, repo_count_total)

    # ── 6. Build and return response ─────────────────────────────────────────
    return AnalysisResponse(
        category=category.name,
        momentum_score=round(trend.momentum_score, 2),
        growth_rate=round(trend.growth_rate, 2),
        star_growth_30d=trend.star_growth_30d,
        top_repositories=[
            RepositorySummary(
                name=r.name,
                full_name=r.full_name,
                url=r.url,
                description=r.description,
                stars=r.stars,
                forks=r.forks,
                language=r.language,
            )
            for r in top_repos
        ],
        top_signals=top_signals,
        analysis=narrative,
        risks=risks,
        opportunities=opportunities,
        confidence=confidence,
    )
