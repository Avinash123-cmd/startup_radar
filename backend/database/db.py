import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Dynamically construct database folder and absolute SQLite path
BASE_DIR = Path(__file__).resolve().parent.parent # backend directory
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

DB_PATH = BASE_DIR / "database" / "radar.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

# Standard engine configurations
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Dependency to get db session in FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()