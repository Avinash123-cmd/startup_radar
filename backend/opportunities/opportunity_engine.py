from __future__ import annotations

from sqlalchemy.orm import Session

from database.crud import add_opportunity
from database.models import Opportunity
from intelligence.types import MarketGap, OpportunityCandidate
from opportunities.market_gap_engine import detect_market_gaps


def generate_opportunities(db: Session) -> list[OpportunityCandidate]:
    gaps = detect_market_gaps(db)
    db.query(Opportunity).delete()
    db.commit()

    candidates = [_candidate_from_gap(gap) for gap in gaps]
    for candidate in candidates:
        add_opportunity(
            db=db,
            title=candidate.title,
            description=candidate.description,
            niche=candidate.niche,
            demand_score=candidate.demand_score,
            competition_score=candidate.competition_score,
            opportunity_score=candidate.opportunity_score,
            potential_ideas=candidate.potential_ideas,
            evidence=candidate.evidence,
            gap_score=candidate.evidence.get("gap_score", 0.0),
            score_components={
                "demand": candidate.demand_score,
                "competition": candidate.competition_score,
                "confidence": candidate.evidence.get("confidence", 0.0),
            },
        )
    return candidates


def _candidate_from_gap(gap: MarketGap) -> OpportunityCandidate:
    evidence_terms = gap.evidence_terms or [gap.slug.replace("-", " ")]
    primary_term = evidence_terms[0]
    pain = gap.pain_terms[0] if gap.pain_terms else "workflow"
    top_title = gap.evidence_titles[0] if gap.evidence_titles else gap.category
    title = _title(primary_term, pain)
    description = (
        f"Market signals in {gap.category} show demand around {primary_term} while current repository density "
        f"and incumbent maturity leave room for focused products. Recent evidence includes '{_short(top_title, 130)}'."
    )
    ideas = [
        f"Build a focused {primary_term} workflow layer that reduces {pain} for teams already adopting {gap.category}.",
        f"Create an evaluation and monitoring product around recurring {primary_term} deployments surfaced in recent signals.",
        f"Package APIs, integrations, and reliability tooling for buyers comparing fragmented {gap.category} options.",
    ]
    return OpportunityCandidate(
        title=title,
        description=description,
        niche=gap.category,
        demand_score=gap.demand_score,
        competition_score=gap.competition_score,
        opportunity_score=gap.opportunity_score,
        potential_ideas=ideas,
        evidence={
            "gap_score": gap.gap_score,
            "confidence": gap.confidence,
            "evidence_terms": gap.evidence_terms,
            "evidence_titles": gap.evidence_titles,
            "pain_terms": gap.pain_terms,
        },
    )


def _title(primary_term: str, pain: str) -> str:
    clean_term = primary_term.replace("-", " ").title()
    clean_pain = pain.replace("-", " ").title()
    return f"{clean_term} {clean_pain} Platform"


def _short(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."
