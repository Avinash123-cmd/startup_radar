from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from database.db import get_db
from database.crud import clear_all_data, seed_categories
from database.schemas import SettingsConfig, SettingsConfigUpdate
from config import get_settings, save_settings

# Pipeliners import
from collectors.collector_manager import run_all_collectors
from processor.trend_analyzer import run_trend_analysis
from processor.opportunity_generator import generate_opportunities
from processor.insights_generator import generate_weekly_report

router = APIRouter(tags=["Settings"])

@router.get("/settings", response_model=SettingsConfig)
def read_settings():
    return get_settings()

@router.post("/settings", response_model=SettingsConfig)
def update_settings(payload: SettingsConfigUpdate):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    return save_settings(updates)

@router.post("/settings/sync")
def trigger_manual_sync(background_tasks: BackgroundTasks):
    # Trigger all pipelines sequentially
    # We run it synchronously or in background tasks so the client doesn't time out
    # Running it synchronously for immediate sync in MVP makes sense, but background task is safer.
    # Let's do it in background tasks, and return immediate message.
    def execute_pipeline():
        run_all_collectors()
        run_trend_analysis()
        generate_opportunities()
        generate_weekly_report()
        
    background_tasks.add_task(execute_pipeline)
    return {"message": "Data ingestion and intelligence pipeline successfully queued!"}

@router.post("/settings/reset")
def trigger_reset(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    clear_all_data(db)
    seed_categories(db)
    
    # Re-run collection and analysis in background
    def execute_pipeline():
        run_all_collectors()
        run_trend_analysis()
        generate_opportunities()
        generate_weekly_report()
        
    background_tasks.add_task(execute_pipeline)
    return {"message": "Database successfully reset and analysis queued!"}
