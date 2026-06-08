from database.db import SessionLocal
from opportunities.opportunity_engine import generate_opportunities


def generate_startup_ideas():
    db = SessionLocal()
    try:
        return [
            {
                "title": candidate.title,
                "category": candidate.niche,
                "score": candidate.opportunity_score,
                "market_gap": candidate.evidence.get("gap_score", 0.0),
            }
            for candidate in generate_opportunities(db)
        ]
    finally:
        db.close()
