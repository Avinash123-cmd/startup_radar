from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database.db import get_db
from database.schemas import CategoryPrediction
from forecasting.forecast_engine import generate_forecasts

router = APIRouter(tags=["Predictions"])

@router.get("/predictions", response_model=List[CategoryPrediction])
def read_predictions(db: Session = Depends(get_db)):
    return [
        {
            "category": forecast.category,
            "growth_probability": forecast.growth_probability,
        }
        for forecast in generate_forecasts(db)
    ]
