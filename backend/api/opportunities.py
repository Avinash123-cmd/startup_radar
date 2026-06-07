import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database.db import get_db
from database.crud import get_opportunities
from database.schemas import OpportunityOut

router = APIRouter(tags=["Opportunities"])

@router.get("/opportunities", response_model=List[OpportunityOut])
def read_opportunities(db: Session = Depends(get_db)):
    opps = get_opportunities(db)
    
    result = []
    for opp in opps:
        ideas = []
        if opp.potential_ideas:
            try:
                ideas = json.loads(opp.potential_ideas)
            except:
                ideas = [opp.potential_ideas]
                
        result.append({
            "id": opp.id,
            "title": opp.title,
            "description": opp.description,
            "niche": opp.niche,
            "demand_score": opp.demand_score,
            "competition_score": opp.competition_score,
            "opportunity_score": opp.opportunity_score,
            "potential_ideas": opp.potential_ideas,
            "created_at": opp.created_at,
            "parsed_ideas": ideas
        })
        
    return result