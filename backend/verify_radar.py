import os
import sys
from datetime import datetime

# Add parent path to import correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import engine, SessionLocal
from database.models import Base, Category, Repository, RepositorySnapshot, MarketDataPoint, TrendHistory, Opportunity, WeeklyReport
from database.crud import seed_categories

# Collectors & Processors imports
from collectors.collector_manager import run_all_collectors
from processor.trend_analyzer import run_trend_analysis
from processor.opportunity_generator import generate_opportunities
from processor.insights_generator import generate_weekly_report

def run_verification():
    print("=== STARTING ARCHITECTURE VERIFICATION ===")
    
    # 1. Test database schema generation
    print("Step 1: Rebuilding database schemas...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("  Database tables generated successfully.")
    
    # 2. Test seeding
    print("Step 2: Seeding standard niche categories...")
    db = SessionLocal()
    try:
        seeded = seed_categories(db)
        print(f"  Successfully seeded {len(seeded)} default niche categories.")
        
        # Verify db insertion
        cat_count = db.query(Category).count()
        assert cat_count == 6, f"Expected 6 categories, got {cat_count}"
        
        # 3. Test collectors sync
        print("Step 3: Running collectors pipeline...")
        run_all_collectors()
        
        repo_count = db.query(Repository).count()
        snap_count = db.query(RepositorySnapshot).count()
        point_count = db.query(MarketDataPoint).count()
        print(f"  Sync Results:")
        print(f"    - Repositories: {repo_count}")
        print(f"    - Snapshots: {snap_count}")
        print(f"    - Market Data Points: {point_count}")
        
        assert repo_count > 0, "No repositories collected"
        assert snap_count > 0, "No repository snapshots collected"
        assert point_count > 0, "No HN/Reddit data points collected"
        
        # 4. Test trend analysis calculation
        print("Step 4: Running trend analyzer matrix...")
        run_trend_analysis()
        
        trend_count = db.query(TrendHistory).count()
        print(f"    - Trend History Entries: {trend_count}")
        assert trend_count == 6, f"Expected 6 trend logs, got {trend_count}"
        
        # 5. Test opportunity generation
        print("Step 5: Running opportunity gap analyzer...")
        generate_opportunities()
        
        opp_count = db.query(Opportunity).count()
        print(f"    - Computed Opportunities: {opp_count}")
        assert opp_count == 6, f"Expected 6 opportunity recommendations, got {opp_count}"
        
        # 6. Test weekly intelligence report generation
        print("Step 6: Running LLM report compiler...")
        generate_weekly_report()
        
        report_count = db.query(WeeklyReport).count()
        print(f"    - Compiled Weekly Reports: {report_count}")
        assert report_count == 1, f"Expected 1 briefing, got {report_count}"
        
        print("\n=== VERIFICATION SUCCESSFUL: Pipeline architecture functions perfectly! ===")
        
    except Exception as e:
        print(f"\nVerification FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_verification()
