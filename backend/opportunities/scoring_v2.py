"""
Opportunity Scoring Engine V2
==============================
Upgrades opportunity evaluation beyond V1's two-dimension (demand vs. competition)
model with six orthogonal factor scores plus a composite Startup Success Probability.

Six Factors
-----------
1. Founder Difficulty Score     (0–100, lower = easier for a small team to enter)
2. Revenue Potential Score      (0–100)
3. Market Timing Score          (0–100, early-mover vs. late-mover sweet spot)
4. Competition Density Score    (0–100, lower = less crowded)
5. Growth Velocity Score        (0–100)
6. VC Attractiveness Score      (0–100)

Startup Success Probability     (0–100, composite)

Design Constraints
------------------
- All data sourced from objects already computed by the existing pipeline:
  MarketGap (from detect_market_gaps), ForecastResult (from generate_forecasts),
  TrendHistory, Repository aggregates.  No new collectors, no new DB tables.
- No breaking changes to existing /opportunities endpoint.
- Pure Python — no external dependencies beyond what requirements.txt already lists.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import mean
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import Category, MarketDataPoint, Repository, RepositorySnapshot, TrendHistory
from forecasting.forecast_engine import generate_forecasts
from intelligence.types import ForecastResult, MarketGap
from opportunities.market_gap_engine import detect_market_gaps
from scoring.scale import clamp, log_scale


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FactorBreakdown:
    """Individual factor scores with their weights used in the final composite."""
    founder_difficulty: float        # 0–100  (lower = easier)
    revenue_potential: float         # 0–100
    market_timing: float             # 0–100
    competition_density: float       # 0–100  (lower = less crowded)
    growth_velocity: float           # 0–100
    vc_attractiveness: float         # 0–100


@dataclass
class OpportunityV2:
    """Full V2 opportunity record returned by the endpoint."""
    category: str
    category_slug: str
    category_id: int

    # V1 carry-over for comparison
    demand_score: int
    competition_score: int
    opportunity_score_v1: int

    # V2 factors
    factors: FactorBreakdown
    success_probability: int         # 0–100

    # Narrative
    reasoning: str
    strongest_signals: list[str]
    risk_factors: list[str]


# ---------------------------------------------------------------------------
# Factor weight configuration
# Each factor weight = its contribution to the success probability (0–100).
# Weights must sum to 1.0.
# ---------------------------------------------------------------------------

_WEIGHTS: dict[str, float] = {
    "revenue_potential":  0.25,
    "growth_velocity":    0.22,
    "market_timing":      0.18,
    "vc_attractiveness":  0.15,
    "competition_density": 0.12,   # inverted — less density → higher score
    "founder_difficulty": 0.08,    # inverted — lower difficulty → higher score
}

assert abs(sum(_WEIGHTS.values()) - 1.0) < 1e-9, "Factor weights must sum to 1.0"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_opportunities_v2(db: Session) -> list[OpportunityV2]:
    """
    Entry point.  Reuses detect_market_gaps and generate_forecasts exactly as
    the V1 pipeline does; adds six new scoring dimensions on top.
    """
    gaps: list[MarketGap] = detect_market_gaps(db)
    forecasts: dict[int, ForecastResult] = {
        f.category_id: f for f in generate_forecasts(db)
    }

    results: list[OpportunityV2] = []
    for gap in gaps:
        ctx = _build_context(db, gap, forecasts)
        factors = _score_factors(gap, ctx)
        prob = _success_probability(factors)
        reasoning = _build_reasoning(gap, factors, ctx)
        signals = _strongest_signals(gap, factors, ctx)
        risks = _risk_factors(gap, factors, ctx)

        results.append(
            OpportunityV2(
                category=gap.category,
                category_slug=gap.slug,
                category_id=gap.category_id,
                demand_score=gap.demand_score,
                competition_score=gap.competition_score,
                opportunity_score_v1=gap.opportunity_score,
                factors=factors,
                success_probability=prob,
                reasoning=reasoning,
                strongest_signals=signals,
                risk_factors=risks,
            )
        )

    results.sort(key=lambda r: r.success_probability, reverse=True)
    return results


# ---------------------------------------------------------------------------
# Context builder — collects all raw metrics once per gap so factor
# functions stay pure and readable.
# ---------------------------------------------------------------------------

@dataclass
class _GapContext:
    """Pre-computed raw metrics for a single category gap."""
    repo_count: int                  # total repos in category
    avg_stars: float                 # mean stars across repos
    total_stars: int                 # sum stars
    mature_repo_count: int           # repos >= 10k stars
    star_growth_30d: int             # aggregate 30-day star delta
    growth_rate: float               # percentage growth (from TrendHistory)
    momentum_score: float            # latest momentum (0–99)
    momentum_slope: float            # day-over-day trend (positive = accelerating)
    news_volume_30d: int             # MarketDataPoint count last 30d
    news_volume_prev: int            # MarketDataPoint count prior 30d (31–60d)
    source_diversity: int            # distinct sources in last 30d
    forecast: ForecastResult | None
    history_count: int               # number of TrendHistory records


def _build_context(
    db: Session,
    gap: MarketGap,
    forecasts: dict[int, ForecastResult],
) -> _GapContext:
    cat_id = gap.category_id
    now = datetime.utcnow()
    w30 = now - timedelta(days=30)
    w60 = now - timedelta(days=60)

    repo_count: int = db.query(Repository).filter(Repository.category_id == cat_id).count()
    avg_stars: float = (
        db.query(func.avg(Repository.stars)).filter(Repository.category_id == cat_id).scalar() or 0.0
    )
    total_stars: int = int(
        db.query(func.sum(Repository.stars)).filter(Repository.category_id == cat_id).scalar() or 0
    )
    mature_repo_count: int = (
        db.query(Repository)
        .filter(Repository.category_id == cat_id, Repository.stars >= 10_000)
        .count()
    )

    # Use latest TrendHistory for momentum / growth data
    latest_trend: TrendHistory | None = (
        db.query(TrendHistory)
        .filter(TrendHistory.category_id == cat_id)
        .order_by(TrendHistory.recorded_at.desc())
        .first()
    )
    star_growth_30d = latest_trend.star_growth_30d if latest_trend else 0
    growth_rate = latest_trend.growth_rate if latest_trend else 0.0
    momentum_score = latest_trend.momentum_score if latest_trend else 0.0

    # Momentum slope — compare last 10 trend points
    history = (
        db.query(TrendHistory)
        .filter(TrendHistory.category_id == cat_id)
        .order_by(TrendHistory.recorded_at.asc())
        .limit(10)
        .all()
    )
    momentum_slope = _compute_slope([h.momentum_score for h in history])
    history_count = db.query(TrendHistory).filter(TrendHistory.category_id == cat_id).count()

    # Signal volume windows
    news_volume_30d: int = (
        db.query(func.count(MarketDataPoint.id))
        .filter(MarketDataPoint.category_id == cat_id, MarketDataPoint.published_at >= w30)
        .scalar() or 0
    )
    news_volume_prev: int = (
        db.query(func.count(MarketDataPoint.id))
        .filter(
            MarketDataPoint.category_id == cat_id,
            MarketDataPoint.published_at >= w60,
            MarketDataPoint.published_at < w30,
        )
        .scalar() or 0
    )
    source_diversity: int = (
        db.query(func.count(func.distinct(MarketDataPoint.source)))
        .filter(MarketDataPoint.category_id == cat_id, MarketDataPoint.published_at >= w30)
        .scalar() or 0
    )

    return _GapContext(
        repo_count=repo_count,
        avg_stars=avg_stars,
        total_stars=total_stars,
        mature_repo_count=mature_repo_count,
        star_growth_30d=star_growth_30d,
        growth_rate=growth_rate,
        momentum_score=momentum_score,
        momentum_slope=momentum_slope,
        news_volume_30d=news_volume_30d,
        news_volume_prev=news_volume_prev,
        source_diversity=source_diversity,
        forecast=forecasts.get(gap.category_id),
        history_count=history_count,
    )


# ---------------------------------------------------------------------------
# Individual factor scorers (all return float 0–100)
# ---------------------------------------------------------------------------

def _score_founder_difficulty(gap: MarketGap, ctx: _GapContext) -> float:
    """
    Lower difficulty = higher score for founders.
    Factors: repo_count (few = less to navigate), avg_stars (high incumbents =
    harder), build_evidence (more terms = better documented problem),
    mature repos (hard to compete with OSS giants).

    Inverted at composite stage — high score here means easy.
    """
    # Repo density penalty: more repos = harder to stand out
    density_penalty = log_scale(ctx.repo_count, divisor=300, maximum=35)
    # Incumbent penalty: high avg_stars = entrenched competition
    incumbent_penalty = log_scale(ctx.avg_stars, divisor=50_000, maximum=30)
    # Mature repo penalty
    mature_penalty = log_scale(ctx.mature_repo_count, divisor=20, maximum=20)
    # Evidence bonus: many known pain terms = problem is well understood → easier
    evidence_bonus = min(len(gap.evidence_terms) / 8.0, 1.0) * 15.0

    raw_difficulty = clamp(density_penalty + incumbent_penalty + mature_penalty - evidence_bonus, 0, 100)
    # Invert: easy = high score
    return round(100.0 - raw_difficulty, 1)


def _score_revenue_potential(gap: MarketGap, ctx: _GapContext) -> float:
    """
    Proxy revenue ceiling using:
    - total star count (proxy for developer interest → market size)
    - engagement score sum from signals (buying intent)
    - demand score from gap engine
    - source diversity (multi-channel signal = broad market)
    """
    star_component = log_scale(ctx.total_stars, divisor=1_000_000, maximum=35)
    demand_component = clamp(gap.demand_score, 0, 100) / 100.0 * 30
    signal_volume = log_scale(ctx.news_volume_30d, divisor=200, maximum=20)
    diversity_component = min(ctx.source_diversity / 5.0, 1.0) * 15

    return round(clamp(star_component + demand_component + signal_volume + diversity_component, 0, 100), 1)


def _score_market_timing(gap: MarketGap, ctx: _GapContext) -> float:
    """
    Market timing sweet spot: not too early (no signal), not too late (saturated).
    - news_volume_30d > news_volume_prev → market is accelerating (good)
    - momentum_slope > 0 → trend is rising (good)
    - mature_repo_count: too many = late; zero = too early
    - forecast growth_probability → market belief in future growth
    """
    # Signal acceleration ratio
    if ctx.news_volume_prev > 0:
        signal_ratio = min(ctx.news_volume_30d / ctx.news_volume_prev, 5.0)
    else:
        signal_ratio = 1.5 if ctx.news_volume_30d > 0 else 0.5

    accel_score = clamp((signal_ratio - 1.0) / 4.0, 0, 1) * 30  # 0–30

    # Momentum slope (normalised; slope range typically -5 to +5)
    slope_score = clamp((ctx.momentum_slope + 3.0) / 6.0, 0, 1) * 25  # 0–25

    # Maturity sweet spot: 1–5 mature repos = perfect; 0 = too early; >10 = too late
    if ctx.mature_repo_count == 0:
        maturity_score = 10.0  # very early, some risk
    elif ctx.mature_repo_count <= 5:
        maturity_score = 25.0  # ideal window
    elif ctx.mature_repo_count <= 10:
        maturity_score = 15.0  # getting competitive
    else:
        maturity_score = 5.0   # late mover penalty

    # Forecast growth probability
    forecast_score = 0.0
    if ctx.forecast:
        forecast_score = clamp(ctx.forecast.growth_probability, 0, 100) / 100.0 * 20

    return round(clamp(accel_score + slope_score + maturity_score + forecast_score, 0, 100), 1)


def _score_competition_density(gap: MarketGap, ctx: _GapContext) -> float:
    """
    Lower density = higher score (less crowded = better for new entrant).
    Inverted at composite stage.
    Uses: repo_count, avg_stars, mature_repo_count, competition_score from V1.
    """
    # Start from V1 competition score, refine with additional signals
    v1_component = clamp(gap.competition_score, 0, 100) / 100.0 * 50

    # Repo count density
    density = log_scale(ctx.repo_count, divisor=200, maximum=30)

    # Maturity density
    mature_density = log_scale(ctx.mature_repo_count, divisor=15, maximum=20)

    raw_density = clamp(v1_component + density + mature_density, 0, 100)
    # Invert: low density → high score
    return round(100.0 - raw_density, 1)


def _score_growth_velocity(gap: MarketGap, ctx: _GapContext) -> float:
    """
    How fast the market is growing right now.
    - star_growth_30d (absolute momentum)
    - growth_rate (percentage growth)
    - news_volume delta (signal acceleration)
    - momentum_score current level
    """
    star_velocity = log_scale(ctx.star_growth_30d, divisor=50_000, maximum=30)
    rate_component = clamp(ctx.growth_rate, 0, 100) / 100.0 * 25

    # Signal volume growth
    if ctx.news_volume_prev > 0:
        signal_growth = clamp(
            (ctx.news_volume_30d - ctx.news_volume_prev) / max(ctx.news_volume_prev, 1) * 100,
            -20, 100
        ) / 100.0 * 25
    else:
        signal_growth = 0.0

    momentum_component = clamp(ctx.momentum_score, 0, 99) / 99.0 * 20

    return round(clamp(star_velocity + rate_component + signal_growth + momentum_component, 0, 100), 1)


def _score_vc_attractiveness(gap: MarketGap, ctx: _GapContext) -> float:
    """
    Proxy for VC investment thesis alignment:
    - Large TAM signals (total stars, signal volume)
    - High growth velocity
    - Platform / infrastructure potential (repo + evidence diversity)
    - Forecast confidence and growth probability
    - Pain term count (evidence of real user pain)
    """
    # TAM proxy
    tam_signal = log_scale(ctx.total_stars, divisor=500_000, maximum=25)
    volume_signal = log_scale(ctx.news_volume_30d, divisor=150, maximum=20)

    # Growth story
    growth_signal = clamp(ctx.growth_rate, 0, 80) / 80.0 * 20

    # Infrastructure / platform signal: mature repos signal standardisation demand
    platform_signal = min(ctx.mature_repo_count / 5.0, 1.0) * 15

    # Confidence from forecast
    confidence_signal = 0.0
    if ctx.forecast:
        confidence_signal = clamp(ctx.forecast.confidence, 0, 100) / 100.0 * 10
    else:
        confidence_signal = gap.confidence / 100.0 * 10

    # Pain term coverage (VCs want validated problems)
    pain_signal = min(len(gap.pain_terms) / 5.0, 1.0) * 10

    return round(clamp(
        tam_signal + volume_signal + growth_signal + platform_signal + confidence_signal + pain_signal,
        0, 100
    ), 1)


# ---------------------------------------------------------------------------
# Composite success probability
# ---------------------------------------------------------------------------

def _success_probability(factors: FactorBreakdown) -> int:
    """
    Weighted composite of the six factors.
    Difficulty and density are positively coded already (inverted during scoring).
    """
    raw = (
        factors.revenue_potential  * _WEIGHTS["revenue_potential"]
        + factors.growth_velocity  * _WEIGHTS["growth_velocity"]
        + factors.market_timing    * _WEIGHTS["market_timing"]
        + factors.vc_attractiveness * _WEIGHTS["vc_attractiveness"]
        + factors.competition_density * _WEIGHTS["competition_density"]
        + factors.founder_difficulty  * _WEIGHTS["founder_difficulty"]
    )
    return int(round(clamp(raw, 0, 100)))


def _score_factors(gap: MarketGap, ctx: _GapContext) -> FactorBreakdown:
    return FactorBreakdown(
        founder_difficulty=_score_founder_difficulty(gap, ctx),
        revenue_potential=_score_revenue_potential(gap, ctx),
        market_timing=_score_market_timing(gap, ctx),
        competition_density=_score_competition_density(gap, ctx),
        growth_velocity=_score_growth_velocity(gap, ctx),
        vc_attractiveness=_score_vc_attractiveness(gap, ctx),
    )


# ---------------------------------------------------------------------------
# Narrative generation
# ---------------------------------------------------------------------------

def _build_reasoning(gap: MarketGap, factors: FactorBreakdown, ctx: _GapContext) -> str:
    parts: list[str] = []

    prob = _success_probability(factors)
    if prob >= 70:
        verdict = "a high-conviction opportunity"
    elif prob >= 50:
        verdict = "a promising opportunity with manageable risk"
    else:
        verdict = "an emerging opportunity with meaningful execution risk"

    parts.append(
        f"{gap.category} represents {verdict} "
        f"(success probability: {prob}/100)."
    )

    # Best factors
    factor_map = {
        "Revenue Potential": factors.revenue_potential,
        "Growth Velocity": factors.growth_velocity,
        "Market Timing": factors.market_timing,
        "VC Attractiveness": factors.vc_attractiveness,
        "Competition Density": factors.competition_density,
        "Founder Difficulty": factors.founder_difficulty,
    }
    best = max(factor_map, key=lambda k: factor_map[k])
    parts.append(f"Strongest dimension: {best} ({factor_map[best]:.0f}/100).")

    if ctx.momentum_slope > 0.5:
        parts.append(
            f"Momentum is accelerating (slope +{ctx.momentum_slope:.2f}/day), "
            "suggesting growing developer and market interest."
        )
    elif ctx.momentum_slope < -0.5:
        parts.append(
            "Momentum slope is negative — this may be a cooling trend or "
            "a consolidation phase ahead of a breakout."
        )

    if ctx.forecast:
        parts.append(
            f"30-day growth forecast: {ctx.forecast.growth_probability}% probability "
            f"(model confidence: {ctx.forecast.confidence:.0f}/100)."
        )

    if gap.pain_terms:
        parts.append(
            f"Active pain signals detected: {', '.join(gap.pain_terms[:3])}."
        )

    return " ".join(parts)


def _strongest_signals(gap: MarketGap, factors: FactorBreakdown, ctx: _GapContext) -> list[str]:
    signals: list[str] = []

    if factors.growth_velocity >= 60:
        signals.append(
            f"High growth velocity ({factors.growth_velocity:.0f}/100): "
            f"{ctx.star_growth_30d:,} stars gained in 30 days, {ctx.growth_rate:.1f}% repo growth rate."
        )
    if factors.market_timing >= 60:
        signals.append(
            f"Ideal market timing ({factors.market_timing:.0f}/100): "
            "market is accelerating without heavy incumbent saturation."
        )
    if factors.revenue_potential >= 60:
        signals.append(
            f"Strong revenue potential ({factors.revenue_potential:.0f}/100): "
            f"{ctx.total_stars:,} total stars signal broad developer adoption."
        )
    if factors.vc_attractiveness >= 60:
        signals.append(
            f"VC-attractive profile ({factors.vc_attractiveness:.0f}/100): "
            f"large TAM proxy, {ctx.source_diversity} active signal sources."
        )
    if ctx.news_volume_30d > ctx.news_volume_prev * 1.5:
        signals.append(
            f"Signal acceleration: {ctx.news_volume_30d} market mentions in last 30 days "
            f"vs {ctx.news_volume_prev} in prior period."
        )
    if gap.evidence_terms:
        signals.append(
            f"Top market evidence terms: {', '.join(gap.evidence_terms[:4])}."
        )

    return signals[:5] or ["Insufficient historical data — run the pipeline to accumulate signals."]


def _risk_factors(gap: MarketGap, factors: FactorBreakdown, ctx: _GapContext) -> list[str]:
    risks: list[str] = []

    if factors.founder_difficulty < 40:
        risks.append(
            f"High founder difficulty ({100 - factors.founder_difficulty:.0f}/100 difficulty): "
            f"{ctx.mature_repo_count} mature OSS incumbents with avg {ctx.avg_stars:,.0f} stars."
        )
    if factors.competition_density < 35:
        risks.append(
            f"Dense competitive landscape ({100 - factors.competition_density:.0f}/100 density): "
            f"{ctx.repo_count} repositories tracked in this category."
        )
    if factors.market_timing < 35:
        risks.append(
            "Poor market timing: either too early (thin signal) or too late "
            "(heavily saturated with incumbents)."
        )
    if factors.growth_velocity < 30:
        risks.append(
            f"Low growth velocity ({factors.growth_velocity:.0f}/100): "
            "market may be stagnating; validate demand before committing."
        )
    if ctx.history_count < 5:
        risks.append(
            "Limited trend history — less than 5 trend snapshots available; "
            "score confidence is lower than average."
        )
    if ctx.momentum_slope < -1.0:
        risks.append(
            f"Declining momentum slope ({ctx.momentum_slope:.2f}/day): "
            "recent data suggests the market may be cooling."
        )
    if gap.confidence < 40:
        risks.append(
            f"Low signal confidence ({gap.confidence:.0f}/100): "
            "limited cross-source corroboration — run another pipeline cycle."
        )

    return risks[:5] or ["No critical risk factors detected — standard execution risks apply."]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_slope(values: list[float]) -> float:
    """Linear regression slope over an equally-spaced series."""
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    x_mean = mean(xs)
    y_mean = mean(values)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values)) / denom
