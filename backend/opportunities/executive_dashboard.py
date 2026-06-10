"""
Executive Dashboard Engine
==========================
Aggregates and formats the most critical market intelligence from across all radar
engines for the dashboard layout. Combines top opportunities, startup briefs, forecasts,
recent alert status, dynamic founder recommendations, and platform-level AI summaries.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import requests
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from config import get_settings, get_platform_status
from database.models import Category, Alert, TrendHistory, Repository
from forecasting.forecast_engine import generate_forecasts
from intelligence.trend_engine import latest_trends_as_dicts
from intelligence.types import ForecastResult
from opportunities.startup_generator_v2 import StartupBriefV2, generate_startup_briefs

logger = logging.getLogger(__name__)

# Ollama platform constants
PRIMARY_MODEL = "qwen3:8b"
FALLBACK_MODEL = None
OLLAMA_TIMEOUT = 30  # Keep timeout short for real-time dashboard loading
MAX_RETRIES = 1
CACHE_TTL_SECONDS = 600  # 10 minutes cache for dashboard queries

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AlertSummaryOut:
    total: int
    unread: int
    severity_breakdown: dict[str, int]
    recent_alerts: list[dict[str, Any]]

@dataclass
class FounderRecommendation:
    category: str
    category_slug: str
    rec_type: str  # conviction | entry | venture | timing
    text: str
    metric: str

@dataclass
class AISummaryResult:
    executive_summary: str
    market_risk_summary: str
    model_used: str
    fallback_mode: bool = False

@dataclass
class ExecutiveDashboardPayload:
    generated_at: str
    top_opportunities: list[dict[str, Any]]
    top_startup_ideas: list[dict[str, Any]]
    fastest_growing_categories: list[dict[str, Any]]
    highest_confidence_predictions: list[dict[str, Any]]
    watchlist_alerts_summary: AlertSummaryOut
    founder_recommendations: list[FounderRecommendation]
    ai_summary: AISummaryResult
    platform_status: str
    warnings: list[str]


# ---------------------------------------------------------------------------
# In-process Cache
# ---------------------------------------------------------------------------
_dashboard_cache: Optional[tuple[ExecutiveDashboardPayload, float]] = None

def clear_dashboard_cache() -> None:
    global _dashboard_cache
    _dashboard_cache = None
    logger.info("Dashboard cache cleared")


# ---------------------------------------------------------------------------
# Core Dashboard Aggregation Logic
# ---------------------------------------------------------------------------

def generate_executive_dashboard(db: Session, force_refresh: bool = False) -> ExecutiveDashboardPayload:
    """
    Query all platform metrics, alerts, opportunities, and trends.
    Uses caching to avoid duplicate runs within the Cache TTL period.
    """
    global _dashboard_cache
    now_mono = time.monotonic()
    
    if not force_refresh and _dashboard_cache and now_mono < _dashboard_cache[1]:
        logger.info("Dashboard cache hit")
        return _dashboard_cache[0]

    # 1. Fetch startup briefs (contains OpportunityV2 scoring breakdowns inside)
    # This runs scoring and gap detection once, yielding sorted results.
    briefs = generate_startup_briefs(db)

    # 2. Extract Top 10 Opportunities
    top_opportunities: list[dict[str, Any]] = []
    for b in briefs[:10]:
        top_opportunities.append({
            "category": b.category,
            "category_slug": b.category_slug,
            "category_id": b.category_id,
            "success_probability": b.success_probability,
            "demand_score": b.demand_score,
            "competition_score": b.competition_score,
            "opportunity_score_v1": b.opportunity_score_v1,
            "factors": {
                "founder_difficulty": b.factors.founder_difficulty,
                "revenue_potential": b.factors.revenue_potential,
                "market_timing": b.factors.market_timing,
                "competition_density": b.factors.competition_density,
                "growth_velocity": b.factors.growth_velocity,
                "vc_attractiveness": b.factors.vc_attractiveness,
            },
            "reasoning": b.why,
            "strongest_signals": b.strongest_signals,
            "risk_factors": b.risk_factors
        })

    # 3. Extract Top 10 Startup Ideas
    top_startup_ideas: list[dict[str, Any]] = []
    for b in briefs[:10]:
        top_startup_ideas.append({
            "startup_name": b.startup_name,
            "category": b.category,
            "category_slug": b.category_slug,
            "problem_statement": b.problem_statement,
            "target_customer": b.target_customer,
            "mvp_features": b.mvp_features,
            "pricing_model": b.pricing_model,
            "revenue_potential": b.revenue_potential,
            "competitive_advantage": b.competitive_advantage,
            "go_to_market": b.go_to_market,
            "build_difficulty": b.build_difficulty,
            "estimated_time_to_mvp": b.estimated_time_to_mvp,
            "success_probability": b.success_probability
        })

    # 4. Fetch Fastest Growing Categories
    trends = latest_trends_as_dicts(db)
    trends.sort(key=lambda t: t.get("growth_rate", 0.0), reverse=True)
    fastest_growing = trends[:10]

    # Convert recorded_at to string format for JSON rendering
    for t in fastest_growing:
        if isinstance(t.get("recorded_at"), datetime):
            t["recorded_at"] = t["recorded_at"].isoformat()

    # 5. Fetch Highest Confidence Predictions
    predictions = generate_forecasts(db)
    # Sort by confidence descending
    predictions.sort(key=lambda p: p.confidence, reverse=True)
    highest_confidence = []
    for p in predictions[:10]:
        highest_confidence.append({
            "category": p.category,
            "category_slug": p.category_slug,
            "category_id": p.category_id,
            "growth_probability": p.growth_probability,
            "confidence": p.confidence,
            "slope": p.slope,
            "horizon_days": p.horizon_days
        })

    # 6. Fetch Watchlist Alerts Summary
    alerts_summary = _build_alerts_summary(db)

    # 7. Generate Founder Recommendations
    founder_recs = _build_founder_recommendations(briefs)

    # 8. Synthesize AI Executive Summary & Risk Summary
    ai_summary = _build_ai_summaries(db, top_opportunities, fastest_growing, alerts_summary)

    # 9. Get Platform Status and Warnings
    status, warnings = get_platform_status(db)

    payload = ExecutiveDashboardPayload(
        generated_at=datetime.now(timezone.utc).isoformat(),
        top_opportunities=top_opportunities,
        top_startup_ideas=top_startup_ideas,
        fastest_growing_categories=fastest_growing,
        highest_confidence_predictions=highest_confidence,
        watchlist_alerts_summary=alerts_summary,
        founder_recommendations=founder_recs,
        ai_summary=ai_summary,
        platform_status=status,
        warnings=warnings
    )

    _dashboard_cache = (payload, now_mono + CACHE_TTL_SECONDS)
    return payload


# ---------------------------------------------------------------------------
# Helper Aggregators
# ---------------------------------------------------------------------------

def _build_alerts_summary(db: Session) -> AlertSummaryOut:
    total = db.query(Alert).count()
    unread = db.query(Alert).filter(Alert.is_read == 0).count()

    # Breakdown by severity
    breakdown = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    severity_counts = db.query(Alert.severity, func.count(Alert.id)).group_by(Alert.severity).all()
    for sev, count in severity_counts:
        sev_upper = str(sev).upper()
        if sev_upper in breakdown:
            breakdown[sev_upper] = count

    # Recent alerts
    recent_db = db.query(Alert).order_by(desc(Alert.created_at)).limit(10).all()
    recent_alerts = []
    for a in recent_db:
        recent_alerts.append({
            "id": a.id,
            "watchlist_id": a.watchlist_id,
            "severity": a.severity,
            "alert_type": a.alert_type,
            "title": a.title,
            "message": a.message,
            "previous_value": a.previous_value,
            "current_value": a.current_value,
            "change_percent": a.change_percent,
            "is_read": bool(a.is_read),
            "created_at": a.created_at.isoformat(),
            "category_slug": a.category.slug if a.category else None,
            "repository_name": a.repository.name if a.repository else None
        })

    return AlertSummaryOut(
        total=total,
        unread=unread,
        severity_breakdown=breakdown,
        recent_alerts=recent_alerts
    )


def _build_founder_recommendations(briefs: list[StartupBriefV2]) -> list[FounderRecommendation]:
    """
    Analyze all briefs dynamically to compile actionable launch recommendations.
    """
    recs: list[FounderRecommendation] = []
    if not briefs:
        return recs

    # Recommendation 1: Highest Conviction (Max Success Probability)
    highest_prob = max(briefs, key=lambda b: b.success_probability)
    recs.append(FounderRecommendation(
        category=highest_prob.category,
        category_slug=highest_prob.category_slug,
        rec_type="conviction",
        text=f"High-conviction market: building in {highest_prob.category} offers the platform's highest projected success rate.",
        metric=f"{highest_prob.success_probability}% Success Probability"
    ))

    # Recommendation 2: Easiest Team Entry (Highest Inverted Founder Difficulty)
    # high score in factors.founder_difficulty means easier to enter
    easiest = max(briefs, key=lambda b: b.factors.founder_difficulty)
    recs.append(FounderRecommendation(
        category=easiest.category,
        category_slug=easiest.category_slug,
        rec_type="entry",
        text=f"Lean developer choice: {easiest.category} has the lowest overall complexity and barrier to enter for a small founding team.",
        metric=f"{easiest.factors.founder_difficulty:.0f}/100 Entry Index"
    ))

    # Recommendation 3: Best VC Fundraising Story (Max VC Attractiveness)
    best_vc = max(briefs, key=lambda b: b.factors.vc_attractiveness)
    if best_vc.factors.vc_attractiveness >= 55:
        recs.append(FounderRecommendation(
            category=best_vc.category,
            category_slug=best_vc.category_slug,
            rec_type="venture",
            text=f"Venture-scale play: {best_vc.category} exhibits a large TAM proxy and high developer interest, aligned with VC investment themes.",
            metric=f"{best_vc.factors.vc_attractiveness:.0f}/100 VC Attractiveness"
        ))

    # Recommendation 4: Optimal Timing Window (Max Market Timing)
    best_timing = max(briefs, key=lambda b: b.factors.market_timing)
    if best_timing.factors.market_timing >= 55:
        recs.append(FounderRecommendation(
            category=best_timing.category,
            category_slug=best_timing.category_slug,
            rec_type="timing",
            text=f"Early-mover advantage: {best_timing.category} signal volume is accelerating without heavy incumbent consolidation.",
            metric=f"{best_timing.factors.market_timing:.0f}/100 Timing Score"
        ))

    return recs[:4]


# ---------------------------------------------------------------------------
# AI Summary & Fallback
# ---------------------------------------------------------------------------

def _build_ai_summaries(
    db: Session,
    opps: list[dict[str, Any]],
    trends: list[dict[str, Any]],
    alerts: AlertSummaryOut
) -> AISummaryResult:
    """
    Formulates a platform-wide market summary, requesting JSON from Ollama
    with a deterministic fallback.
    """
    total_categories = db.query(Category).count()
    total_repos = db.query(Repository).count()

    top_growers = [t["name"] for t in trends[:3] if "name" in t]
    top_opp_names = [o["category"] for o in opps[:3]]

    # 1. Build prompt
    prompt = f"""You are a principal AI investment analyst summarizing the state of the AI startup market.
Analyze the aggregate market indicators below and respond with a valid JSON object containing an executive summary and a risk overview.

=== PLATFORM INDICATORS ===
Total Categories Tracked: {total_categories}
Total Open Source Repositories Tracked: {total_repos}

Top Fastest-Growing Segments:
{', '.join(top_growers) if top_growers else 'None recorded'}

Top Startup Opportunity Areas (Scored by Success Probability):
{', '.join(top_opp_names) if top_opp_names else 'None recorded'}

Watchlist Alert Status:
  Total Triggered Alerts: {alerts.total}
  Critical / High Severity Alerts: {alerts.severity_breakdown.get('CRITICAL', 0) + alerts.severity_breakdown.get('HIGH', 0)}

=== INSTRUCTIONS ===
Produce a JSON object with this exact schema:
{{
  "executive_summary": "<2-3 sentence overview of overall market health, developer interest, and which AI categories present the highest conviction plays>",
  "market_risk_summary": "<2-3 sentence overview of critical headwinds, competition risks, and macro risks identified across the sectors>"
}}

Rules:
- Output ONLY the JSON block. No markdown formatting, no preamble, no wrapper other than the JSON itself.
- Do not make up any numbers or metrics outside of those provided above.
"""

    # 2. Call Ollama
    settings = get_settings()
    base_endpoint = settings.get("ollama_endpoint", "http://localhost:11434").rstrip("/")
    url = f"{base_endpoint}/api/generate"

    payload = {
        "model": PRIMARY_MODEL,
        "prompt": prompt.strip(),
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 250,
        }
    }

    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            raw_response = response.json()
            resp_text = raw_response.get("response", "").strip()
            
            # Clean up thinking or code fences
            if "<think>" in resp_text and "</think>" in resp_text:
                start = resp_text.find("<think>")
                end = resp_text.find("</think>") + len("</think>")
                resp_text = resp_text[:start] + resp_text[end:]
                resp_text = resp_text.strip()
            
            if resp_text.startswith("```"):
                lines = resp_text.splitlines()
                inner = [line for line in lines if not line.startswith("```")]
                resp_text = "\n".join(inner).strip()

            start_idx = resp_text.find("{")
            end_idx = resp_text.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                resp_text = resp_text[start_idx:end_idx]

            parsed = json.loads(resp_text)
            
            logger.info("Executive summary successfully generated by Ollama in %s seconds", round(elapsed, 2))
            return AISummaryResult(
                executive_summary=parsed.get("executive_summary", "").strip(),
                market_risk_summary=parsed.get("market_risk_summary", "").strip(),
                model_used=PRIMARY_MODEL,
                fallback_mode=False
            )
    except Exception as exc:
        logger.warning("Ollama dashboard summary generation failed or timed out: %s. Using deterministic fallback.", exc)

    # 3. Deterministic Fallback Mode
    top_grow_str = ", ".join(top_growers) if top_growers else "emerging sectors"
    top_opp_str = ", and ".join(top_opp_names[:2]) if top_opp_names else "AI integration frameworks"
    
    exec_fallback = (
        f"The AI market radar is active across {total_categories} tracked categories. "
        f"We see rapid open-source acceleration in {top_grow_str}, which anchors developer interest. "
        f"The highest conviction startup opportunities reside in {top_opp_str}, reflecting strong underlying demand."
    )

    risk_fallback = (
        f"Ecosystem risks remain concentrated around early-stage builder fatigue and high incumbent saturation. "
        f"The system has triggered {alerts.total} total alerts, including "
        f"{alerts.severity_breakdown.get('CRITICAL', 0) + alerts.severity_breakdown.get('HIGH', 0)} high-severity warnings, "
        f"indicating high competition and potential cooling trends in select developer markets."
    )

    return AISummaryResult(
        executive_summary=exec_fallback,
        market_risk_summary=risk_fallback,
        model_used="deterministic-fallback",
        fallback_mode=True
    )
