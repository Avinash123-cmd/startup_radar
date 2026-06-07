from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database.db import engine, SessionLocal
from database.models import Base, Category
from database.crud import seed_categories, get_categories

# Import Routers
from api.trends import router as trends_router
from api.opportunities import router as opportunities_router
from api.predictions import router as predictions_router
from api.insights import router as insights_router
from api.repositories import router as repositories_router
from api.reports import router as reports_router
from api.settings import router as settings_router

# Import Scheduler and Pipeliners
from scheduler import start_scheduler
from collectors.collector_manager import run_all_collectors
from processor.trend_analyzer import run_trend_analysis
from processor.opportunity_generator import generate_opportunities
from processor.insights_generator import generate_weekly_report

# Background job to run initial sync
def run_initial_sync():
    print("Initiating initial synchronization run...")
    run_all_collectors()
    run_trend_analysis()
    generate_opportunities()
    generate_weekly_report()
    print("Initial synchronization run complete.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize Database & Create Tables
    print("Initializing Database tables...")
    Base.metadata.create_all(bind=engine)
    
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
    
    # Shutdown scheduler on exit
    print("Stopping scheduler...")
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