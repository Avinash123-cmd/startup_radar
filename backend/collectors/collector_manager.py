import traceback
from database.db import SessionLocal
from config import get_settings, save_settings

# Import collectors
from collectors.github_collector import collect_github
from collectors.hn_collector import collect_hn
from collectors.reddit_collector import collect_reddit
from collectors.arxiv_collector import collect_arxiv
from collectors.ph_collector import collect_ph

def run_all_collectors():
    print("=== STARTING DATA COLLECTION JOB ===")
    db = SessionLocal()
    settings = get_settings()
    
    try:
        # 1. Sync GitHub Repositories (and snapshots)
        try:
            collect_github(db, settings)
        except Exception as e:
            print(f"Error running GitHub collector: {e}")
            traceback.print_exc()
            
        # 2. Sync Hacker News discussion points
        try:
            collect_hn(db, settings)
        except Exception as e:
            print(f"Error running Hacker News collector: {e}")
            traceback.print_exc()
            
        # 3. Sync Reddit threads
        try:
            collect_reddit(db, settings)
        except Exception as e:
            print(f"Error running Reddit collector: {e}")
            traceback.print_exc()
            
        # 4. Sync arXiv academic preprints
        try:
            collect_arxiv(db, settings)
        except Exception as e:
            print(f"Error running arXiv collector: {e}")
            traceback.print_exc()
            
        # 5. Sync Product Hunt launches
        try:
            collect_ph(db, settings)
        except Exception as e:
            print(f"Error running Product Hunt collector: {e}")
            traceback.print_exc()
            
        print("=== DATA COLLECTION JOB COMPLETE ===")
        
    finally:
        db.close()

if __name__ == "__main__":
    run_all_collectors()
