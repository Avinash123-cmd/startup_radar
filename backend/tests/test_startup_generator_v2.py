from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.crud import add_market_data_point, create_or_update_repository, seed_categories
from database.models import Base, Category, RepositorySnapshot, TrendHistory
from opportunities.scoring_v2 import generate_opportunities_v2
from opportunities.startup_generator_v2 import (
    generate_startup_briefs,
    generate_startup_brief_for_category,
)


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
    # Keep reference to SessionLocal to spawn new sessions sharing same DB connection
    session._session_local = SessionLocal
    try:
        yield session
    finally:
        session.close()


def test_scoring_v2_and_startup_generator(db):
    # Setup mock data for coding-agents
    category = db.query(Category).filter(Category.slug == "coding-agents").one()
    
    # 1. Create a repository
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
    
    # 2. Add some repository snapshots for trend engine to have data points
    db.add(
        RepositorySnapshot(
            repository_id=repo.id,
            stars=800,
            forks=50,
            recorded_at=datetime.utcnow() - timedelta(days=31),
        )
    )
    db.commit()

    # 3. Add TrendHistory
    db.add(
        TrendHistory(
            category_id=category.id,
            recorded_at=datetime.utcnow(),
            star_count=1200,
            star_growth_30d=400,
            growth_rate=50.0,
            momentum_score=75.0,
        )
    )
    # Add older trend history to test slope calculation
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

    # 4. Add some MarketDataPoints (signals)
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
    add_market_data_point(
        db=db,
        source="reddit",
        external_id="reddit-test-1",
        title="Who is using coding agents in production?",
        description="Looking for feedback on coding agents like Cursor or Devin.",
        url="https://reddit.com/r/developer",
        engagement_score=150,
        published_at=datetime.utcnow() - timedelta(days=5),
        category_id=category.id,
        normalized_text="coding agents production feedback cursor devin",
        classification_confidence=0.9,
        classification_evidence=["coding agents"],
    )
    db.commit()

    # Let's run generate_opportunities_v2
    opps = generate_opportunities_v2(db)
    assert len(opps) > 0
    
    # Check fields in OpportunityV2
    coding_agent_opp = next(o for o in opps if o.category_slug == "coding-agents")
    assert coding_agent_opp.success_probability > 0
    assert coding_agent_opp.factors.founder_difficulty >= 0
    assert coding_agent_opp.factors.revenue_potential >= 0
    assert coding_agent_opp.factors.market_timing >= 0
    assert coding_agent_opp.factors.competition_density >= 0
    assert coding_agent_opp.factors.growth_velocity >= 0
    assert coding_agent_opp.factors.vc_attractiveness >= 0
    assert len(coding_agent_opp.strongest_signals) > 0
    assert len(coding_agent_opp.risk_factors) > 0
    assert coding_agent_opp.reasoning != ""

    # Let's generate briefs
    briefs = generate_startup_briefs(db)
    assert len(briefs) > 0
    
    coding_agent_brief = next(b for b in briefs if b.category_slug == "coding-agents")
    
    # Verify the 11 required startup brief fields
    assert coding_agent_brief.startup_name != ""
    assert coding_agent_brief.problem_statement != ""
    assert coding_agent_brief.target_customer != ""
    assert len(coding_agent_brief.mvp_features) > 0
    assert coding_agent_brief.pricing_model != ""
    assert coding_agent_brief.revenue_potential != ""
    assert coding_agent_brief.competitive_advantage != ""
    assert coding_agent_brief.go_to_market != ""
    assert coding_agent_brief.build_difficulty in ["Low", "Medium", "High"]
    assert coding_agent_brief.estimated_time_to_mvp != ""
    assert 0 <= coding_agent_brief.success_probability <= 100
    
    # Verify explainability why
    assert "WHY" in coding_agent_brief.why
    assert "gap score" in coding_agent_brief.why.lower() or "market gap" in coding_agent_brief.why.lower()

    # Test single category generator
    single_brief = generate_startup_brief_for_category(db, "coding-agents")
    assert single_brief is not None
    assert single_brief.startup_name == coding_agent_brief.startup_name

    non_existent = generate_startup_brief_for_category(db, "non-existent")
    assert non_existent is None


def test_startup_generator_api(db):
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
        
        # Test main endpoint
        response = client.get("/startup-generator")
        assert response.status_code == 200
        data = response.json()
        assert "briefs" in data
        assert len(data["briefs"]) > 0
        
        brief = data["briefs"][0]
        assert brief["category_slug"] == "coding-agents"
        assert brief["startup_name"] != ""
        assert "success_probability" in brief
        
        # Test category-specific endpoint
        resp_cat = client.get("/startup-generator/coding-agents")
        assert resp_cat.status_code == 200
        brief_cat = resp_cat.json()
        assert brief_cat["category_slug"] == "coding-agents"
        assert brief_cat["startup_name"] == brief["startup_name"]
        
        # Test 404 for non-existent category
        resp_404 = client.get("/startup-generator/non-existent-category")
        assert resp_404.status_code == 404
        
    finally:
        app.dependency_overrides.clear()


