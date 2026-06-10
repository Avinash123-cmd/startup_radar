import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from database.db import get_db
from database.schemas import OpportunityOut
from opportunities.scoring_v2 import generate_opportunities_v2
from opportunities.startup_generator_v2 import generate_startup_briefs

router = APIRouter(tags=["Opportunities"])

@router.get("/opportunities", response_model=List[OpportunityOut])
def read_opportunities(db: Session = Depends(get_db)):
    # Fetch V2 opportunities
    opps = generate_opportunities_v2(db)
    
    # Fetch V2 startup briefs for potential_ideas mapping
    try:
        briefs = generate_startup_briefs(db)
    except Exception:
        briefs = []
        
    result = []
    for opp in opps:
        # Match startup brief for ideas
        brief = next((b for b in briefs if b.category_id == opp.category_id), None)
        if brief:
            ideas = [
                f"Build '{brief.startup_name}': {brief.problem_statement}",
                f"MVP Features: {', '.join(brief.mvp_features[:3])}",
                f"GTM Strategy: {brief.go_to_market}"
            ]
        else:
            ideas = [
                f"Build a focused SaaS product leveraging V2 growth signals in {opp.category}.",
                f"Address pain points surfaced in telemetry (VC Attractiveness: {opp.factors.vc_attractiveness:.0f}/100).",
                f"Launch a competitive entry using YC Decision Vectors (Success Prob: {opp.success_probability}%)."
            ]
            
        result.append({
            "id": opp.category_id,
            "title": f"{opp.category} V2 Growth Niche",
            "description": opp.reasoning,
            "niche": opp.category,
            "demand_score": opp.demand_score,
            "competition_score": opp.competition_score,
            "opportunity_score": opp.success_probability,  # Map success_probability to V1 opportunity_score
            "potential_ideas": json.dumps(ideas),
            "created_at": datetime.now(timezone.utc),
            "parsed_ideas": ideas
        })
        
    return result