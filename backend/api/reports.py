from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.db import get_db
from database.crud import get_weekly_reports, get_weekly_report_by_slug
from database.schemas import WeeklyReportOut

router = APIRouter(tags=["Reports"])

@router.get("/reports", response_model=List[WeeklyReportOut])
def read_reports(db: Session = Depends(get_db)):
    reports = get_weekly_reports(db)
    return reports

@router.get("/reports/{slug}", response_model=WeeklyReportOut)
def read_report(slug: str, db: Session = Depends(get_db)):
    report = get_weekly_report_by_slug(db, slug)
    if not report:
        raise HTTPException(status_code=404, detail="Weekly report not found")
    return report
