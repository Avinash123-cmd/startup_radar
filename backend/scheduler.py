from apscheduler.schedulers.background import BackgroundScheduler
from collectors.collector_manager import run_all_collectors
from processor.trend_analyzer import run_trend_analysis
from processor.opportunity_generator import generate_opportunities
from processor.insights_generator import generate_weekly_report

def run_sync_pipeline():
    print("Scheduler: Triggering automated synchronization run...")
    try:
        run_all_collectors()
        run_trend_analysis()
        generate_opportunities()
        generate_weekly_report()
        print("Scheduler: Synchronization cycle successfully completed.")
    except Exception as e:
        print(f"Scheduler: Automated run encountered errors: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Runs the analytics sync process once every 6 hours
    scheduler.add_job(run_sync_pipeline, "interval", hours=6)
    scheduler.start()
    print("APScheduler Background Daemon started successfully. Active intervals: 6 Hours.")
    return scheduler