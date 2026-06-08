from database.db import SessionLocal
from reports.report_engine import generate_weekly_report as _generate_weekly_report


def generate_weekly_report():
    db = SessionLocal()
    try:
        return _generate_weekly_report(db)
    finally:
        db.close()


if __name__ == "__main__":
    generate_weekly_report()
