"""
Startup Generator Engine V2
============================
Converts Opportunity Scoring V2 results into fully-detailed, actionable startup
briefs.  Every field is derived from live engine data — not static templates —
and each brief carries an explicit WHY explanation that traces the recommendation
back to the signals that produced it.

Data flow (no duplicate calculations):
  detect_market_gaps()        → MarketGap per category
       ↓
  generate_forecasts()        → ForecastResult per category      (shared with scoring_v2)
       ↓
  generate_opportunities_v2() → OpportunityV2 with FactorBreakdown + success_probability
       ↓
  founder_engine blueprints   → static category-specific idea profiles
       ↓
  THIS ENGINE                 → StartupBriefV2 per opportunity

Output fields
-------------
  startup_name           — derived from category + strongest factor + top pain term
  problem_statement      — pulled from founder_engine blueprint, refined by evidence
  target_customer        — from blueprint
  mvp_features           — from blueprint (dynamic order by pain term relevance)
  pricing_model          — from blueprint
  revenue_potential      — quantified from V2 revenue_potential factor + star counts
  competitive_advantage  — derived from competition_density + timing factors
  go_to_market           — from blueprint, enriched with top signal sources
  build_difficulty       — from blueprint, optionally adjusted by founder_difficulty
  estimated_time_to_mvp  — from blueprint
  success_probability    — direct from OpportunityV2
  why                    — explicit reasoning trace citing concrete metrics
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from intelligence.types import ForecastResult, MarketGap
from opportunities.founder_engine import (
    FounderIdea,
    _CATEGORY_PROFILES,
    _DEFAULT_BLUEPRINTS,
    _IdeaBlueprint,
    _competition_label,
    _compute_confidence,
    _select_blueprint,
    generate_founder_ideas,
)
from opportunities.market_gap_engine import detect_market_gaps
from opportunities.scoring_v2 import (
    OpportunityV2,
    FactorBreakdown,
    generate_opportunities_v2,
)


# ---------------------------------------------------------------------------
# Output dataclass
# ---------------------------------------------------------------------------

@dataclass
class StartupBriefV2:
    # Identity
    category: str
    category_slug: str
    category_id: int

    # Core brief (11 required fields)
    startup_name: str
    problem_statement: str
    target_customer: str
    mvp_features: list[str]
    pricing_model: str
    revenue_potential: str          # human-readable quantified estimate
    competitive_advantage: str
    go_to_market: str
    build_difficulty: str           # Low | Medium | High
    estimated_time_to_mvp: str
    success_probability: int        # 0–100, from OpportunityV2

    # Scoring context
    factors: FactorBreakdown
    opportunity_score_v1: int
    demand_score: int
    competition_score: int

    # Explainability
    why: str                        # WHY this idea was generated (metric trace)
    strongest_signals: list[str]
    risk_factors: list[str]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_startup_briefs(db: Session) -> list[StartupBriefV2]:
    """
    Generate all startup briefs sorted by success_probability descending.
    Reuses V2 scoring pipeline — detect_market_gaps and generate_forecasts
    are called exactly once inside generate_opportunities_v2.
    """
    opportunities: list[OpportunityV2] = generate_opportunities_v2(db)
    if not opportunities:
        return []

    # Build a MarketGap lookup by category_id for blueprint selection
    gaps: dict[int, MarketGap] = {
        gap.category_id: gap
        for gap in detect_market_gaps(db)
    }

    briefs: list[StartupBriefV2] = []
    for rank, opp in enumerate(opportunities):
        gap = gaps.get(opp.category_id)
        if not gap:
            continue
        brief = _build_brief(opp, gap, rank)
        briefs.append(brief)

    briefs.sort(key=lambda b: b.success_probability, reverse=True)
    return briefs


def generate_startup_brief_for_category(
    db: Session, category_slug: str
) -> Optional[StartupBriefV2]:
    """
    Generate a single startup brief for a specific category slug.
    Returns None if the category has no V2 opportunity or insufficient data.
    """
    briefs = generate_startup_briefs(db)
    for brief in briefs:
        if brief.category_slug == category_slug:
            return brief
    return None


# ---------------------------------------------------------------------------
# Brief builder
# ---------------------------------------------------------------------------

def _build_brief(opp: OpportunityV2, gap: MarketGap, rank: int) -> StartupBriefV2:
    blueprint: _IdeaBlueprint = _select_blueprint(gap.slug, rank)
    factors = opp.factors

    startup_name = _derive_name(opp, gap, blueprint, factors)
    revenue_potential = _quantify_revenue(opp, gap, factors)
    competitive_advantage = _derive_competitive_advantage(opp, gap, factors)
    gtm = _enrich_gtm(blueprint, opp, gap)
    build_difficulty = _adjust_difficulty(blueprint.build_difficulty, factors)
    why = _build_why(opp, gap, factors)
    mvp_features = _prioritise_mvp(blueprint.mvp_features, gap.pain_terms)

    return StartupBriefV2(
        category=opp.category,
        category_slug=opp.category_slug,
        category_id=opp.category_id,
        startup_name=startup_name,
        problem_statement=blueprint.problem_statement,
        target_customer=blueprint.target_customer,
        mvp_features=mvp_features,
        pricing_model=blueprint.pricing_model,
        revenue_potential=revenue_potential,
        competitive_advantage=competitive_advantage,
        go_to_market=gtm,
        build_difficulty=build_difficulty,
        estimated_time_to_mvp=blueprint.estimated_time_to_mvp,
        success_probability=opp.success_probability,
        factors=factors,
        opportunity_score_v1=opp.opportunity_score_v1,
        demand_score=opp.demand_score,
        competition_score=opp.competition_score,
        why=why,
        strongest_signals=opp.strongest_signals,
        risk_factors=opp.risk_factors,
    )


# ---------------------------------------------------------------------------
# Field derivation helpers
# ---------------------------------------------------------------------------

def _derive_name(
    opp: OpportunityV2,
    gap: MarketGap,
    blueprint: _IdeaBlueprint,
    factors: FactorBreakdown,
) -> str:
    """
    Build a startup name from:
      base  = blueprint startup_idea (specific concept noun)
      suffix = strongest factor label or top pain term for differentiation
    """
    base = blueprint.startup_idea

    # Pick a qualifying word from top pain term if it doesn't already appear
    qualifier = ""
    if gap.pain_terms:
        pain = gap.pain_terms[0].replace("-", " ").title()
        if pain.lower() not in base.lower():
            qualifier = f" — {pain} Focus"

    # If timing is the standout factor, note the timing angle
    if factors.market_timing >= 75 and not qualifier:
        qualifier = " — Early Mover Edition"
    elif factors.vc_attractiveness >= 75 and not qualifier:
        qualifier = " — Venture-Scale Play"

    return f"{base}{qualifier}"


def _quantify_revenue(
    opp: OpportunityV2,
    gap: MarketGap,
    factors: FactorBreakdown,
) -> str:
    """
    Translate the revenue_potential factor score into a human-readable
    revenue ceiling estimate with supporting rationale.
    """
    score = factors.revenue_potential

    if score >= 75:
        tier = "$10M–$100M ARR"
        rationale = (
            "large developer community (high star count), strong demand signal, "
            "and broad multi-source market activity"
        )
    elif score >= 55:
        tier = "$1M–$10M ARR"
        rationale = (
            "growing adoption signals, moderate demand, "
            "and emerging community engagement"
        )
    elif score >= 35:
        tier = "$250K–$1M ARR"
        rationale = (
            "early market with limited but consistent signals; "
            "niche product with focused ICP"
        )
    else:
        tier = "Pre-PMF / < $250K ARR"
        rationale = (
            "thin market signal; validate demand before scaling revenue assumptions"
        )

    return (
        f"Estimated ceiling: {tier}. "
        f"Revenue potential score {score:.0f}/100 based on {rationale}."
    )


def _derive_competitive_advantage(
    opp: OpportunityV2,
    gap: MarketGap,
    factors: FactorBreakdown,
) -> str:
    """
    Compose a competitive advantage statement using competition_density,
    market_timing, and founder_difficulty factors.
    """
    parts: list[str] = []

    density = factors.competition_density
    timing = factors.market_timing
    difficulty = factors.founder_difficulty

    if density >= 65:
        parts.append(
            f"Low competitive density ({density:.0f}/100): the market is not yet crowded, "
            "creating room to define the product category."
        )
    elif density >= 40:
        parts.append(
            f"Moderate competition ({density:.0f}/100): clear differentiation on UX, "
            "pricing, or vertical focus will be the key advantage."
        )
    else:
        parts.append(
            f"High competition density ({100 - density:.0f}/100 density): "
            "advantage requires deep technical moat or locked-in distribution channel."
        )

    if timing >= 65:
        parts.append(
            f"Strong timing advantage ({timing:.0f}/100): the market is accelerating "
            "and not yet dominated by a clear winner — first-mover branding is achievable."
        )
    elif timing >= 40:
        parts.append(
            "Market timing is adequate; focus on execution speed to establish positioning "
            "before the consolidation phase."
        )

    if difficulty >= 65:
        parts.append(
            f"Low build difficulty ({difficulty:.0f}/100): a small team can ship an MVP "
            "quickly, enabling rapid iteration before well-funded competitors enter."
        )

    if gap.evidence_terms:
        parts.append(
            f"Evidence-backed differentiation: the market is actively discussing "
            f"{', '.join(gap.evidence_terms[:3])} — building natively around these "
            "pain points creates defensible positioning."
        )

    return " ".join(parts) if parts else (
        "Advantage lies in execution quality and speed; no structural moat identified yet."
    )


def _enrich_gtm(
    blueprint: _IdeaBlueprint,
    opp: OpportunityV2,
    gap: MarketGap,
) -> str:
    """
    Augment the blueprint GTM strategy with signals from the live data:
    active sources and top evidence terms surface specific community channels.
    """
    base = blueprint.go_to_market
    enrichments: list[str] = []

    # Surface specific communities from evidence terms
    if gap.evidence_terms:
        enrichments.append(
            f"Target communities actively discussing: {', '.join(gap.evidence_terms[:3])}."
        )

    # Mention VC signal if attractive
    if opp.factors.vc_attractiveness >= 65:
        enrichments.append(
            "Strong VC attractiveness score — early institutional backing is achievable; "
            "prepare a data-driven pitch citing momentum metrics."
        )

    if not enrichments:
        return base

    return base + " " + " ".join(enrichments)


def _adjust_difficulty(base_difficulty: str, factors: FactorBreakdown) -> str:
    """
    Nudge the blueprint build difficulty using the live founder_difficulty score.
    """
    score = factors.founder_difficulty  # high = easy to enter
    if base_difficulty == "High":
        return "High"
    if base_difficulty == "Low":
        return "Low"
    # Medium: adjust based on live factor
    if score < 35:
        return "High"   # more incumbents than expected — harder
    if score >= 70:
        return "Low"    # market is open — easier than baseline
    return "Medium"


def _prioritise_mvp(features: list[str], pain_terms: list[str]) -> list[str]:
    """
    Re-order MVP features so that those matching live pain terms appear first.
    """
    if not pain_terms:
        return list(features)
    pain_set = {t.lower() for t in pain_terms}
    priority: list[str] = []
    rest: list[str] = []
    for f in features:
        if any(p in f.lower() for p in pain_set):
            priority.append(f)
        else:
            rest.append(f)
    return priority + rest


def _build_why(
    opp: OpportunityV2,
    gap: MarketGap,
    factors: FactorBreakdown,
) -> str:
    """
    Construct an explicit metric-traced explanation for WHY this startup idea
    was generated.  This is the key transparency requirement.
    """
    lines: list[str] = []

    lines.append(
        f"WHY {opp.category}:"
    )

    # 1. Market gap rationale
    lines.append(
        f"• Market gap detected: demand score {gap.demand_score}/100 vs. "
        f"competition score {gap.competition_score}/100 "
        f"(gap score {gap.gap_score:.1f}) — "
        f"{'demand clearly outpaces supply' if gap.demand_score > gap.competition_score else 'early-stage demand signal'}."
    )

    # 2. V2 success probability
    lines.append(
        f"• V2 success probability: {opp.success_probability}/100 across six scored factors."
    )

    # 3. Top factor explanation
    factor_scores = {
        "Revenue Potential": factors.revenue_potential,
        "Growth Velocity": factors.growth_velocity,
        "Market Timing": factors.market_timing,
        "VC Attractiveness": factors.vc_attractiveness,
        "Competition Density (inverted)": factors.competition_density,
        "Founder Difficulty (inverted)": factors.founder_difficulty,
    }
    top_factor = max(factor_scores, key=lambda k: factor_scores[k])
    top_score = factor_scores[top_factor]
    lines.append(
        f"• Strongest factor: {top_factor} = {top_score:.0f}/100."
    )

    # 4. Evidence trace
    if gap.evidence_terms:
        lines.append(
            f"• Evidence terms driving this idea: {', '.join(gap.evidence_terms[:5])}."
        )

    # 5. Pain terms
    if gap.pain_terms:
        lines.append(
            f"• Active pain signals: {', '.join(gap.pain_terms[:4])}."
        )

    # 6. Timing signal
    if factors.market_timing >= 60:
        lines.append(
            f"• Market timing is favourable ({factors.market_timing:.0f}/100): "
            "signal volume is accelerating without heavy incumbent saturation."
        )
    elif factors.market_timing < 35:
        lines.append(
            f"• Market timing is cautious ({factors.market_timing:.0f}/100): "
            "validate timing risk before committing capital."
        )

    # 7. Confidence note
    confidence_pct = int(gap.confidence)
    lines.append(
        f"• Signal confidence: {confidence_pct}/100 "
        f"({'high' if confidence_pct >= 65 else 'moderate' if confidence_pct >= 35 else 'low'})."
    )

    return "\n".join(lines)
