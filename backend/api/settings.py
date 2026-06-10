from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from database.db import get_db
from database.crud import clear_all_data, seed_categories
from database.schemas import SettingsConfig, SettingsConfigUpdate
from config import get_runtime_settings, get_settings, save_settings, get_platform_status
from pipeline import run_pipeline

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
    background_tasks.add_task(run_pipeline, get_runtime_settings())
    return {"message": "Data ingestion and intelligence pipeline successfully queued!"}

@router.post("/settings/reset")
def trigger_reset(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    clear_all_data(db)
    seed_categories(db)

    background_tasks.add_task(run_pipeline, get_runtime_settings())
    return {"message": "Database successfully reset and analysis queued!"}

@router.get("/platform-status")
def get_platform_status_endpoint(db: Session = Depends(get_db)):
    status, warnings = get_platform_status(db)
    return {
        "status": status,
        "warnings": warnings
    }
