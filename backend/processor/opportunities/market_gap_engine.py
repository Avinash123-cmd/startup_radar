from database.db import SessionLocal
from opportunities.market_gap_engine import detect_market_gaps as _detect_market_gaps


def detect_market_gaps():
    db = SessionLocal()
    try:
        return [
            {
                "category": gap.category,
                "slug": gap.slug,
                "gap_score": gap.gap_score,
                "demand": gap.demand_score,
                "competition": gap.competition_score,
            }
            for gap in _detect_market_gaps(db)
        ]
    finally:
        db.close()
