from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database.db import engine, SessionLocal
from database.models import Base, Category
from database.migrations import run_migrations
from database.crud import seed_categories, get_categories

# Import Routers
from api.trends import router as trends_router
from api.opportunities import router as opportunities_router
from api.predictions import router as predictions_router
from api.insights import router as insights_router
from api.repositories import router as repositories_router
from api.reports import router as reports_router
from api.settings import router as settings_router

from scheduler import start_scheduler
from pipeline import run_pipeline

def run_initial_sync():
    print("Initiating initial synchronization run...")
    run_pipeline()
    print("Initial synchronization run complete.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing Database migrations...")
    run_migrations(engine)
    
    # 2. Seed Default Categories
    db = SessionLocal()
    try:
        seed_categories(db)
        
        # Check if database is empty (no repositories)
        # If so, run an initial sync immediately in the background
        from database.models import Repository
        repo_count = db.query(Repository).count()
        if repo_count == 0:
            print("Database is empty. Queueing first-time sync pipeline...")
            from threading import Thread
            Thread(target=run_initial_sync).start()
    finally:
        db.close()
        
    # 3. Start APScheduler Background Daemon
    scheduler = start_scheduler()
    
    yield
    
    print("Stopping scheduler...")
    if scheduler:
        scheduler.shutdown()

app = FastAPI(
    title="AI Startup Radar API",
    description="Market intelligence platform for emerging AI trends and startup opportunities.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Endpoint Routers
app.include_router(trends_router)
app.include_router(opportunities_router)
app.include_router(predictions_router)
app.include_router(insights_router)
app.include_router(repositories_router)
app.include_router(reports_router)
app.include_router(settings_router)

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "AI Startup Radar API Running 🚀",
        "version": "1.0.0"
    }
