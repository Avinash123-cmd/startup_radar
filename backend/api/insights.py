from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from database.crud import get_weekly_reports, get_trends
from database.schemas import QuickInsight

router = APIRouter(tags=["Insights"])

@router.get("/insights", response_model=QuickInsight)
def read_insights(db: Session = Depends(get_db)):
    reports = get_weekly_reports(db, limit=1)
    trends = get_trends(db)
    sorted_trends = sorted(trends, key=lambda x: x.momentum_score, reverse=True)

    if reports:
        report = reports[0]
        leader_name = sorted_trends[0].category.name if sorted_trends else "No data"
        leader_score = int(sorted_trends[0].momentum_score) if sorted_trends else 0
            
        return {
            "leader": leader_name,
            "score": leader_score,
            "insight": report.summary or "Insight brief compiled successfully."
        }
        
    if sorted_trends:
        leader = sorted_trends[0]
        return {
            "leader": leader.category.name,
            "score": int(leader.momentum_score),
            "insight": f"{leader.category.name} currently leads with momentum {leader.momentum_score}, based on repository growth and recent market signals."
        }

    return {
        "leader": "No data",
        "score": 0,
        "insight": "No market signals are available yet. Configure source credentials and run the pipeline."
    }
