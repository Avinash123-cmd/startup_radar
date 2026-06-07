from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.db import get_db
from database.crud import get_trends, get_category_trend_history, get_category_by_slug
from database.schemas import TrendSummary, TrendHistoryOut

router = APIRouter(tags=["Trends"])

@router.get("/trends", response_model=List[TrendSummary])
def read_trends(db: Session = Depends(get_db)):
    trends = get_trends(db)
    
    result = []
    for trend in trends:
        result.append({
            "category_id": trend.category_id,
            "name": trend.category.name,
            "slug": trend.category.slug,
            "description": trend.category.description,
            "star_count": trend.star_count,
            "star_growth_30d": trend.star_growth_30d,
            "growth_rate": trend.growth_rate,
            "news_volume": trend.news_volume,
            "momentum_score": trend.momentum_score,
            "recorded_at": trend.recorded_at
        })
        
    return result

@router.get("/trends/{slug}/history", response_model=List[TrendHistoryOut])
def read_trend_history(slug: str, db: Session = Depends(get_db)):
    category = get_category_by_slug(db, slug)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    history = get_category_trend_history(db, category.id)
    return history