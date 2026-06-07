import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.db import SessionLocal
from database.models import Category, Repository, TrendHistory, Opportunity
from database.crud import add_opportunity

MOCK_OPPORTUNITY_DETAILS = {
    "browser-agents": {
        "title": "Self-Healing Browser Scraping APIs",
        "description": "Traditional web scrapers break when website layouts or selectors change. AI-driven browser agents can navigate, interact, and extract structured data using visual computer vision and natural language targets, making scraping self-healing and robust.",
        "ideas": [
            "Visual API generation from raw interactive screen recordings",
            "Auto-adapting checkout agents for complex e-commerce platforms",
            "Continuous UI testing agents that adapt to layout shifts without script changes"
        ]
    },
    "coding-agents": {
        "title": "Legacy Code Modernization Agents",
        "description": "Migrating large codebases between frameworks or languages (e.g., jQuery to React, Python 2 to 3, COBOL to Go) is a massive manual task. Collaborative developer agents can map codebases, write unit tests, and perform refactoring loops autonomously.",
        "ideas": [
            "Automatic framework migration tools (e.g., Vue 2 to Vue 3, Next.js Pages to App Router)",
            "Automated patch generators for libraries with CVE vulnerabilities",
            "Natural language documentation and diagram builders for legacy systems"
        ]
    },
    "voice-ai": {
        "title": "Ultra-Low Latency Voice Agent SaaS",
        "description": "Voice assistants struggle with latency and natural interruptions. Combining fast speech-to-text, low-latency LLMs, and real-time audio streams enables lifelike voice interactions for phone support, gaming, and local business tasks.",
        "ideas": [
            "Autonomous front-desk assistants for dental and medical clinics",
            "Real-time local language translation voice bridges for international calls",
            "Interactive voice NPC scripts for gaming engines"
        ]
    },
    "ai-agents": {
        "title": "Natural Language Agentic RPA",
        "description": "Robotic Process Automation is traditionally rigid. Agentic RPA platforms let operational staff describe workflow processes in plain English, and agents dynamically construct and execute integration tasks across fragmented internal platforms.",
        "ideas": [
            "Automated invoice verification and vendor payouts manager",
            "Multilingual email support triage and draft responding agent",
            "Real-time market tracking and automated competitor intelligence alerts"
        ]
    },
    "multimodal-generation": {
        "title": "Modular Visual Asset Generators",
        "description": "Game studios and marketing agencies require highly specific visual consistency. Creating workflows that build ComfyUI layouts as serverless microservices allows developers to easily embed generative media in existing applications.",
        "ideas": [
            "Serverless ComfyUI workflow runners for e-commerce product placement",
            "Consistent character generation APIs for storyboard creators",
            "Vector format illustration generators for web designers"
        ]
    },
    "llm-frameworks": {
        "title": "Private RAG Databases for Compliance",
        "description": "Enterprises are reluctant to send proprietary data to public APIs. Standardized local-first RAG frameworks bundled with small open-weight LLMs (like Llama 3) allow secure, offline document search and query systems.",
        "ideas": [
            "Offline legal compliance checking databases",
            "Secure internal documentation query systems for defense and medical organizations",
            "Local code repository analysis engines for high-security environments"
        ]
    }
}

def generate_opportunities():
    print("=== RUNNING OPPORTUNITY GENERATION ENGINE ===")
    db = SessionLocal()
    
    try:
        # Clear previous opportunities to avoid duplicates
        db.query(Opportunity).delete()
        db.commit()
        
        categories = db.query(Category).all()
        
        for category in categories:
            # 1. Compute Demand Score (based on star growth and social mention volume)
            latest_trend = db.query(TrendHistory)\
                .filter(TrendHistory.category_id == category.id)\
                .order_by(TrendHistory.recorded_at.desc())\
                .first()
                
            if not latest_trend:
                continue
                
            # Demand: momentum score is a good proxy for demand
            demand_score = int(latest_trend.momentum_score)
            demand_score = max(30, min(demand_score, 99))
            
            # 2. Compute Competition Score (based on number of starred repos in category)
            # High star count and high repository count = higher competition
            repo_count = db.query(Repository).filter(Repository.category_id == category.id).count()
            avg_stars = db.query(func.avg(Repository.stars)).filter(Repository.category_id == category.id).scalar() or 0
            
            if repo_count > 0:
                competition_score = int((repo_count * 5) + (avg_stars / 4000.0))
            else:
                competition_score = 10
                
            competition_score = max(15, min(competition_score, 95))
            
            # 3. Compute Opportunity Score (High demand, Low competition = Sweet spot)
            # Opportunity = Demand * 0.7 + (100 - Competition) * 0.3
            opportunity_score = int((demand_score * 0.75) + ((100 - competition_score) * 0.25))
            opportunity_score = max(10, min(opportunity_score, 99))
            
            # 4. Create Opportunity details
            meta = MOCK_OPPORTUNITY_DETAILS.get(category.slug, {
                "title": f"Emerging SaaS in {category.name}",
                "description": f"An emerging market opportunity focused on leveraging novel trends inside the {category.name} niche, driven by recent repository activity and discussions.",
                "ideas": [
                    f"Automated SaaS toolkit resolving core developer pain points in {category.name}",
                    f"B2B integration middleware specializing in {category.name} workflows",
                    f"Custom model training pipelines optimized for {category.name} applications"
                ]
            })
            
            add_opportunity(
                db=db,
                title=meta["title"],
                description=meta["description"],
                niche=category.name,
                demand_score=demand_score,
                competition_score=competition_score,
                opportunity_score=opportunity_score,
                potential_ideas=meta["ideas"]
            )
            print(f"  Opportunity created for {category.name} | Title: {meta['title']} | Score: {opportunity_score} (D: {demand_score}, C: {competition_score})")
            
        print("=== OPPORTUNITY GENERATION COMPLETE ===")
        
    finally:
        db.close()

if __name__ == "__main__":
    generate_opportunities()
