from fastapi import APIRouter
from processor.reports.investor_report import generate_investor_report

router = APIRouter(tags=["Investor"])

@router.get("/investor-report")
def investor_report():

    return generate_investor_report()