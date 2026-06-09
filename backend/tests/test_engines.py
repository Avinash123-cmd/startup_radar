from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.crud import add_market_data_point, create_or_update_repository, seed_categories
from database.models import Base, Category, RepositorySnapshot
from forecasting.forecast_engine import generate_forecasts
from intelligence.trend_engine import compute_trends
from opportunities.opportunity_engine import generate_opportunities
from reports.report_engine import generate_weekly_report


@pytest.fixture()
def db(monkeypatch):
    monkeypatch.delenv("OPENAI_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    seed_categories(session)
    try:
        yield session
    finally:
        session.close()


def test_database_backed_engines_generate_intelligence(db):
    category = db.query(Category).filter(Category.slug == "coding-agents").one()
    repo = create_or_update_repository(
        db=db,
        name="agent-debugger",
        full_name="example/agent-debugger",
        url="https://github.com/example/agent-debugger",
        description="Coding agent for debugging and test generation",
        stars=1200,
        forks=80,
        language="Python",
        category_id=category.id,
    )
    db.add(
        RepositorySnapshot(
            repository_id=repo.id,
            stars=800,
            forks=50,
            recorded_at=datetime.utcnow() - timedelta(days=31),
        )
    )
    db.commit()
    add_market_data_point(
        db=db,
        source="hacker_news",
        external_id="hn-test",
        title="SWE agent for debugging legacy code",
        description="Developer agent workflow for testing and migration.",
        url="https://news.ycombinator.com/item?id=1",
        engagement_score=300,
        published_at=datetime.utcnow() - timedelta(days=2),
        category_id=category.id,
        normalized_text="swe agent debugging legacy code testing migration",
        classification_confidence=0.8,
        classification_evidence=["swe agent", "debugging"],
    )

    trends = compute_trends(db)
    forecasts = generate_forecasts(db)
    opportunities = generate_opportunities(db)
    report = generate_weekly_report(db)

    assert trends
    assert forecasts
    assert opportunities
    assert report.slug.startswith("report-")
    assert "Weekly Market Briefing" in report.content
