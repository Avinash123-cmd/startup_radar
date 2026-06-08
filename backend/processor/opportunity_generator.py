from database.db import SessionLocal
from opportunities.opportunity_engine import generate_opportunities as _generate_opportunities


def generate_opportunities():
    db = SessionLocal()
    try:
        return _generate_opportunities(db)
    finally:
        db.close()


if __name__ == "__main__":
    generate_opportunities()
