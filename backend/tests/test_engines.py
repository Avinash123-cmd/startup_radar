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


def test_growth_rate_for_new_viral_repo():
    from intelligence.trend_engine import _growth_rate
    rate = _growth_rate(100, 100)
    assert rate == 10000.0
    
    rate = _growth_rate(0, 0)
    assert rate == 0.0


def test_prune_repository_snapshots(db):
    from database.crud import prune_repository_snapshots
    category = db.query(Category).first()
    repo = create_or_update_repository(
        db=db,
        name="test-repo",
        full_name="example/test-repo",
        url="https://github.com/example/test-repo",
        description="test description",
        stars=100,
        forks=10,
        language="Python",
        category_id=category.id
    )
    # Add 35 snapshots
    for i in range(35):
        db.add(
            RepositorySnapshot(
                repository_id=repo.id,
                stars=i,
                forks=0,
                recorded_at=datetime.utcnow() - timedelta(minutes=i)
            )
        )
    db.commit()
    
    # Prune
    prune_repository_snapshots(db, keep_limit=30)
    
    # Check count
    count = db.query(RepositorySnapshot).filter(RepositorySnapshot.repository_id == repo.id).count()
    assert count == 30
    
    # Check that kept snapshots are the latest 30 (stars 100 from repo creation, and stars 0 to 28 from the loop)
    remaining_stars = [s.stars for s in db.query(RepositorySnapshot).filter(RepositorySnapshot.repository_id == repo.id).all()]
    assert 100 in remaining_stars
    for star in range(29):
        assert star in remaining_stars
    for star in range(29, 35):
        assert star not in remaining_stars


def test_verify_data_integrity(db):
    from database.crud import verify_data_integrity
    
    # Assert integrity passes for seeded database
    result = verify_data_integrity(db)
    assert result["success"] is True
    
    # Corrupt category mapping by adding a repository pointing to invalid category ID 9999
    create_or_update_repository(
        db=db,
        name="corrupt-repo",
        full_name="example/corrupt-repo",
        url="https://github.com/example/corrupt-repo",
        description="corrupt description",
        stars=100,
        forks=10,
        language="Python",
        category_id=9999
    )
    
    result = verify_data_integrity(db)
    assert result["success"] is False
    assert any("points to non-existent Category ID 9999" in w for w in result["warnings"])
