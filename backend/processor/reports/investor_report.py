from database.db import SessionLocal
from opportunities.market_gap_engine import detect_market_gaps


def generate_investor_report():
    db = SessionLocal()
    try:
        gaps = detect_market_gaps(db)
        if not gaps:
            return {"status": "No data"}
        leader = gaps[0]
        return {
            "best_market": leader.category,
            "market_gap": leader.gap_score,
            "demand": leader.demand_score,
            "competition": leader.competition_score,
            "recommendation": "WATCH" if leader.opportunity_score < 50 else "INVESTIGATE",
        }
    finally:
        db.close()
