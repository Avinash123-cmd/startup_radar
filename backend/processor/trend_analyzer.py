from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.db import SessionLocal
from database.models import Category, Repository, RepositorySnapshot, MarketDataPoint, TrendHistory
from database.crud import add_trend_history

def run_trend_analysis():
    print("=== STARTING TREND ANALYSIS ===")
    db = SessionLocal()
    
    try:
        categories = db.query(Category).all()
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        for category in categories:
            print(f"Analyzing category: {category.name}")
            
            # 1. Get all repositories in this category
            repos = db.query(Repository).filter(Repository.category_id == category.id).all()
            repo_ids = [r.id for r in repos]
            
            total_stars = sum(r.stars for r in repos)
            star_growth_30d = 0
            
            if repo_ids:
                # Calculate star growth by comparing latest snapshot to the one ~30 days ago
                for repo in repos:
                    # Latest snapshot
                    latest_snap = db.query(RepositorySnapshot)\
                        .filter(RepositorySnapshot.repository_id == repo.id)\
                        .order_by(RepositorySnapshot.recorded_at.desc())\
                        .first()
                        
                    # 30-day snapshot (earliest snapshot around 30 days ago)
                    historical_snap = db.query(RepositorySnapshot)\
                        .filter(
                            RepositorySnapshot.repository_id == repo.id,
                            RepositorySnapshot.recorded_at <= thirty_days_ago
                        )\
                        .order_by(RepositorySnapshot.recorded_at.desc())\
                        .first()
                        
                    # If no 30-day snapshot, get the oldest snapshot available
                    if not historical_snap:
                        historical_snap = db.query(RepositorySnapshot)\
                            .filter(RepositorySnapshot.repository_id == repo.id)\
                            .order_by(RepositorySnapshot.recorded_at.asc())\
                            .first()
                            
                    if latest_snap and historical_snap and latest_snap.id != historical_snap.id:
                        growth = latest_snap.stars - historical_snap.stars
                        if growth > 0:
                            star_growth_30d += growth
                            
            # 2. Get news volume (Market Data Points) in the last 30 days
            news_volume = db.query(MarketDataPoint)\
                .filter(
                    MarketDataPoint.category_id == category.id,
                    MarketDataPoint.published_at >= thirty_days_ago
                )\
                .count()
                
            # 3. Calculate growth rate percentage
            base_stars = total_stars - star_growth_30d
            if base_stars > 0:
                growth_rate = (star_growth_30d / base_stars) * 100.0
            else:
                growth_rate = 0.0
                
            # 4. Calculate Momentum Score
            # Formula: (Star growth / 100 * 4) + (News volume * 2) + 10 (base momentum)
            # Cap at 99.0
            momentum = 10.0 + (star_growth_30d / 50.0) + (news_volume * 1.8)
            momentum_score = min(round(momentum, 1), 99.0)
            
            # 5. Save Trend telemetry
            add_trend_history(
                db=db,
                category_id=category.id,
                star_count=total_stars,
                star_growth_30d=star_growth_30d,
                growth_rate=round(growth_rate, 2),
                news_volume=news_volume,
                momentum_score=momentum_score
            )
            print(f"  Category: {category.name} | Total Stars: {total_stars} | 30d Growth: {star_growth_30d} (+{growth_rate:.1f}%) | Mentions: {news_volume} | Momentum: {momentum_score}")
            
        print("=== TREND ANALYSIS COMPLETE ===")
        
    finally:
        db.close()

if __name__ == "__main__":
    run_trend_analysis()
