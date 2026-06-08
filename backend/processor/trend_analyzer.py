from database.db import SessionLocal
from intelligence.trend_engine import compute_trends


def run_trend_analysis():
    db = SessionLocal()
    try:
        return compute_trends(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_trend_analysis()
