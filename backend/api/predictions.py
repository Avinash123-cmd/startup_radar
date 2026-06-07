from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database.db import get_db
from database.crud import get_trends
from database.schemas import CategoryPrediction

router = APIRouter(tags=["Predictions"])

@router.get("/predictions", response_model=List[CategoryPrediction])
def read_predictions(db: Session = Depends(get_db)):
    trends = get_trends(db)
    
    predictions = []
    for trend in trends:
        # Calculate dynamic prediction probability based on momentum score and growth rates
        # Probability = cap(base_probability + rate_velocity)
        base = int(trend.momentum_score * 0.8)
        rate_modifier = int(trend.growth_rate * 0.5)
        
        prob = base + rate_modifier + 20
        # cap between 45% and 98%
        prob = max(45, min(prob, 98))
        
        predictions.append({
            "category": trend.category.name,
            "growth_probability": prob
        })
        
    # Sort predictions by probability descending
    predictions.sort(key=lambda x: x["growth_probability"], reverse=True)
    return predictions