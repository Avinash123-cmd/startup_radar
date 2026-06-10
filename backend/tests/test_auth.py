import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.models import Base
from main import app
from database.db import get_db

@pytest.fixture()
def db():
    # Setup in-memory SQLite for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    session._session_local = SessionLocal
    try:
        yield session
    finally:
        session.close()

@pytest.fixture()
def client(db):
    def override_get_db():
        session = db._session_local()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_signup_success(client):
    response = client.post(
        "/api/auth/signup",
        json={"username": "testuser", "password": "securepassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["username"] == "testuser"
    assert "created_at" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_signup_duplicate_username(client):
    # Register first time
    response1 = client.post(
        "/api/auth/signup",
        json={"username": "testuser", "password": "securepassword"}
    )
    assert response1.status_code == 200

    # Register duplicate
    response2 = client.post(
        "/api/auth/signup",
        json={"username": "testuser", "password": "anotherpassword"}
    )
    assert response2.status_code == 400
    assert response2.json()["detail"] == "Username already registered"


def test_signin_success(client):
    # Register user first
    signup_resp = client.post(
        "/api/auth/signup",
        json={"username": "loginuser", "password": "mypassword"}
    )
    assert signup_resp.status_code == 200

    # Sign in
    signin_resp = client.post(
        "/api/auth/signin",
        json={"username": "loginuser", "password": "mypassword"}
    )
    assert signin_resp.status_code == 200
    data = signin_resp.json()
    assert data["success"] is True
    assert "token" in data
    assert data["username"] == "loginuser"


def test_signin_wrong_password(client):
    # Register user first
    signup_resp = client.post(
        "/api/auth/signup",
        json={"username": "loginuser", "password": "mypassword"}
    )
    assert signup_resp.status_code == 200

    # Sign in with wrong password
    signin_resp = client.post(
        "/api/auth/signin",
        json={"username": "loginuser", "password": "wrongpassword"}
    )
    assert signin_resp.status_code == 401
    assert signin_resp.json()["detail"] == "Incorrect username or password"


def test_signin_nonexistent_user(client):
    # Sign in with non-existent user
    signin_resp = client.post(
        "/api/auth/signin",
        json={"username": "nobody", "password": "password"}
    )
    assert signin_resp.status_code == 401
    assert signin_resp.json()["detail"] == "Incorrect username or password"
