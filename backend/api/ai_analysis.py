"""
GET /ai-analysis/{slug}
========================
Returns an AI-generated market analysis for a tracked category, powered by a
local Ollama instance (default: qwen3:8b).  Falls back to a deterministic
rule-based analysis when Ollama is unavailable.

Results are cached for 1 hour in-process.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.db import get_db
from reports.ai_analyst import AIAnalysisResult, run_ai_analysis

router = APIRouter(tags=["AI Analysis"])


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class AIAnalysisResponse(BaseModel):
    category: str = Field(..., description="Category name analysed")
    slug: str = Field(..., description="Category slug")
    executive_summary: str = Field(..., description="2-3 sentence executive briefing")
    market_overview: str = Field(..., description="Market dynamics and ecosystem maturity paragraph")
    key_drivers: List[str] = Field(default_factory=list, description="Primary growth drivers")
    risks: List[str] = Field(default_factory=list, description="Key risk factors")
    startup_opportunities: List[str] = Field(
        default_factory=list, description="Actionable startup opportunity descriptions"
    )
    recommended_startup: str = Field(..., description="Single most actionable startup recommendation")
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Model confidence in this analysis (0.0–1.0)"
    )
    model_used: str = Field(..., description="Ollama model that generated this analysis")
    fallback_mode: bool = Field(
        ..., description="True when Ollama was unavailable and deterministic fallback was used"
    )
    generated_at: datetime = Field(..., description="UTC timestamp of when analysis was generated")
    cached: bool = Field(False, description="True if this result was served from cache")


class CacheStatusResponse(BaseModel):
    slug: str
    cached: bool
    message: str


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _to_response(result: AIAnalysisResult, cached: bool = False) -> AIAnalysisResponse:
    return AIAnalysisResponse(
        category=result.category,
        slug=result.slug,
        executive_summary=result.executive_summary,
        market_overview=result.market_overview,
        key_drivers=result.key_drivers,
        risks=result.risks,
        startup_opportunities=result.startup_opportunities,
        recommended_startup=result.recommended_startup,
        confidence=result.confidence,
        model_used=result.model_used,
        fallback_mode=result.fallback_mode,
        generated_at=result.generated_at,
        cached=cached,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ai-analysis/{slug}",
    response_model=AIAnalysisResponse,
    summary="AI-generated market analysis for a category",
    description=(
        "Runs an AI analysis for the given category slug using a local Ollama instance "
        "(qwen3:8b by default). If Ollama is unavailable a deterministic fallback is "
        "returned. Results are cached for 1 hour. Pass `?force_refresh=true` to bypass "
        "the cache and regenerate."
    ),
)
def get_ai_analysis(
    slug: str,
    force_refresh: bool = Query(
        False,
        description="Bypass the 1-hour cache and regenerate the analysis",
    ),
    db: Session = Depends(get_db),
) -> AIAnalysisResponse:

    from reports.ai_analyst import _cache, CACHE_TTL_SECONDS
    import time

    # Force-clear cache entry when requested
    if force_refresh:
        _cache.pop(slug, None)

    # Detect whether a valid unexpired cache entry is present before run_ai_analysis is executed
    cached_flag = False
    if slug in _cache:
        entry = _cache[slug]
        if entry and time.monotonic() < entry[1]:
            cached_flag = True

    try:
        result = run_ai_analysis(slug, db)
    except ValueError as exc:
        # Category not found
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        # No trend data — pipeline not yet run
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis engine error: {exc}",
        ) from exc

    return _to_response(result, cached=cached_flag)


@router.delete(
    "/ai-analysis/{slug}/cache",
    response_model=CacheStatusResponse,
    summary="Invalidate cached AI analysis for a category",
    description="Clears the in-process cache entry for the given slug so the next request regenerates.",
)
def invalidate_cache(slug: str) -> CacheStatusResponse:
    from reports.ai_analyst import _cache
    existed = slug in _cache
    _cache.pop(slug, None)
    return CacheStatusResponse(
        slug=slug,
        cached=False,
        message=(
            f"Cache for '{slug}' cleared successfully."
            if existed
            else f"No cache entry found for '{slug}'."
        ),
    )
