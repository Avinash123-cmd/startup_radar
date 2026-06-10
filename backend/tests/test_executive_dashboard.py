from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.crud import add_market_data_point, create_or_update_repository, seed_categories
from database.models import Base, Category, RepositorySnapshot, TrendHistory, Alert, Watchlist
from opportunities.executive_dashboard import generate_executive_dashboard


@pytest.fixture()
def db(monkeypatch):
    monkeypatch.delenv("OPENAI_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    seed_categories(session)
    session._session_local = SessionLocal
    try:
        yield session
    finally:
        session.close()


def test_generate_executive_dashboard_logic(db):
    # Setup mock data for coding-agents
    category = db.query(Category).filter(Category.slug == "coding-agents").one()
    
    # Create a repository
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

    # Create TrendHistory
    db.add(
        TrendHistory(
            category_id=category.id,
            recorded_at=datetime.utcnow(),
            star_count=1200,
            star_growth_30d=400,
            growth_rate=50.0,
            momentum_score=75.0,
            source_breakdown='{"github": 2, "hacker_news": 5}',
            score_components='{"signal_strength": 10.0, "source_count": 2, "repo_count": 1}'
        )
    )
    db.add(
        TrendHistory(
            category_id=category.id,
            recorded_at=datetime.utcnow() - timedelta(days=1),
            star_count=1100,
            star_growth_30d=300,
            growth_rate=40.0,
            momentum_score=70.0,
        )
    )
    db.commit()

    # Add MarketDataPoints
    add_market_data_point(
        db=db,
        source="hacker_news",
        external_id="hn-test-1",
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
    db.commit()

    # Create Alert & Watchlist
    wl = Watchlist(name="Test Watchlist", description="Test desc", is_active=1)
    db.add(wl)
    db.commit()

    alert = Alert(
        watchlist_id=wl.id,
        severity="CRITICAL",
        alert_type="star_growth_spike",
        category_id=category.id,
        title="Significant growth spike",
        message="Coding Agents is growing very fast",
        is_read=0
    )
    db.add(alert)
    db.commit()

    # Generate dashboard
    payload = generate_executive_dashboard(db, force_refresh=True)

    assert payload.generated_at != ""
    assert len(payload.top_opportunities) > 0
    assert len(payload.top_startup_ideas) > 0
    assert len(payload.fastest_growing_categories) > 0
    assert len(payload.highest_confidence_predictions) > 0
    
    # Watchlist alert summary check
    assert payload.watchlist_alerts_summary.total == 1
    assert payload.watchlist_alerts_summary.unread == 1
    assert payload.watchlist_alerts_summary.severity_breakdown["CRITICAL"] == 1
    assert len(payload.watchlist_alerts_summary.recent_alerts) == 1
    assert payload.watchlist_alerts_summary.recent_alerts[0]["title"] == "Significant growth spike"

    # Founder recommendations check
    assert len(payload.founder_recommendations) > 0
    assert any(r.rec_type == "conviction" for r in payload.founder_recommendations)

    # AI summaries check (fallback check)
    assert payload.ai_summary.executive_summary != ""
    assert payload.ai_summary.market_risk_summary != ""
    assert payload.ai_summary.fallback_mode is True
    assert payload.ai_summary.model_used == "deterministic-fallback"


def test_executive_dashboard_api(db):
    # Setup mock data for coding-agents
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
    db.add(
        TrendHistory(
            category_id=category.id,
            recorded_at=datetime.utcnow(),
            star_count=1200,
            star_growth_30d=400,
            growth_rate=50.0,
            momentum_score=75.0,
            source_breakdown='{"github": 2}',
            score_components='{"signal_strength": 1.0, "source_count": 1, "repo_count": 1}'
        )
    )
    add_market_data_point(
        db=db,
        source="hacker_news",
        external_id="hn-test-1",
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
    db.commit()

    from fastapi.testclient import TestClient
    from main import app
    from database.db import get_db

    # Override database dependency with in-memory test db session generator
    def override_get_db():
        session = db._session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        
        response = client.get("/executive-dashboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "generated_at" in data
        assert "top_opportunities" in data
        assert "top_startup_ideas" in data
        assert "fastest_growing_categories" in data
        assert "highest_confidence_predictions" in data
        assert "watchlist_alerts_summary" in data
        assert "founder_recommendations" in data
        assert "ai_summary" in data

        # check content schemas
        assert len(data["top_opportunities"]) > 0
        assert data["top_opportunities"][0]["category_slug"] == "coding-agents"
        assert len(data["top_startup_ideas"]) > 0
        assert len(data["fastest_growing_categories"]) > 0
        assert len(data["highest_confidence_predictions"]) > 0
        assert data["watchlist_alerts_summary"]["total"] >= 0
        assert len(data["founder_recommendations"]) > 0
        assert data["ai_summary"]["fallback_mode"] is True

    finally:
        app.dependency_overrides.clear()
