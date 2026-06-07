import json
import requests
from datetime import datetime
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import Category, Repository, TrendHistory, Opportunity, WeeklyReport
from database.crud import add_weekly_report
from config import get_settings

MOCK_WEEKLY_REPORT = """# Weekly Market Briefing: The Agentic Automation Expansion

## Executive Summary
This week, the market intelligence pipeline registered an unprecedented surge in activity focused on **Browser & Desktop Automation Agents**. Developer mindshare is rapidly shifting from static text-completion wrappers to active execution agents capable of navigating web interfaces, resolving visual prompts, and completing multi-page transactions autonomously. 

## Deep Dive: Fastest Growing Categories
1. **Browser & Desktop Automation Agents** (+24.2% star growth)
   - The release of modular packages like `browser-use` has democratized agentic navigation, enabling developers to build scrapers and transaction flows in single script chains.
2. **AI Coding Assistants** (+18.5% star growth)
   - Git-backed terminal loops (e.g., `aider`) and full-workspace refactoring companions (`OpenDevin`) are growing faster than traditional editor overlays, showing developer preference for end-to-end task completion.
3. **Voice & Audio AI** (+14.0% star growth)
   - Open-weight flow matching speech models like `F5-TTS` are reducing voice clone training to seconds, causing a rise in downstream conversational support applications.

## Emerging Opportunities & Market Gaps
- **Self-Healing Web Operations**: Companies spending significant hours writing Selenium/Playwright scripts are prime targets for visual AI agents that test and scrape without selector dependencies.
- **Micro-ComfyUI APIs**: The complexity of multi-modal generative video workflows (SVD/AnimateDiff) creates an opportunity for platforms that compile node layouts into serverless REST endpoints for designers.

## Repositories to Watch
* **browser-use/browser-use** (+3,400 stars this week): Python library enabling LLMs to navigate and complete forms on web pages.
* **SWHL/F5-TTS** (+1,200 stars this week): Fast, zero-shot voice cloning and speech generation.
* **paul-gauthier/aider** (+980 stars this week): Command-line developer agent implementing git version commits.
"""

def generate_weekly_report():
    print("=== RUNNING WEEKLY REPORT GENERATOR ===")
    db = SessionLocal()
    settings = get_settings()
    
    openai_key = settings.get("openai_key", "")
    ollama_endpoint = settings.get("ollama_endpoint", "http://localhost:11434")
    mock_mode = settings.get("mock_mode", True)
    
    # 1. Fetch current metrics to feed the prompt
    categories = db.query(Category).all()
    trends = db.query(TrendHistory).order_by(TrendHistory.recorded_at.desc()).limit(len(categories)).all()
    opportunities = db.query(Opportunity).order_by(Opportunity.opportunity_score.desc()).all()
    repos = db.query(Repository).order_by(Repository.stars.desc()).limit(5).all()
    
    context_data = {
        "trends": [
            {
                "category": t.category.name,
                "stars": t.star_count,
                "growth_30d": t.star_growth_30d,
                "growth_rate": t.growth_rate,
                "news_mentions": t.news_volume,
                "momentum": t.momentum_score
            } for t in trends
        ],
        "opportunities": [
            {
                "title": o.title,
                "niche": o.niche,
                "score": o.opportunity_score
            } for o in opportunities
        ],
        "top_repos": [
            {
                "name": r.full_name,
                "stars": r.stars,
                "language": r.language
            } for r in repos
        ]
    }
    
    report_content = MOCK_WEEKLY_REPORT
    
    # Check if we should call LLM APIs
    if not mock_mode and openai_key:
        print("Calling OpenAI API for report generation...")
        try:
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            prompt = f"Analyze these AI market intelligence metrics and compile a professional SaaS market research report in markdown detailing trends, opportunities, and top repos to watch. Keep it realistic, precise, and highly actionable:\n\n{json.dumps(context_data, indent=2)}"
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a world-class Startup CTO and AI Research Market Analyst. Write reports in clean Github Markdown with sections like Executive Summary, Category Analysis, and Market Gaps."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
            res.raise_for_status()
            report_content = res.json()["choices"][0]["message"]["content"]
            print("OpenAI report generated successfully.")
        except Exception as e:
            print(f"OpenAI call failed: {e}. Falling back to default briefing...")
            
    elif not mock_mode and ollama_endpoint:
        print("Calling Ollama Endpoint for report generation...")
        try:
            prompt = f"Analyze these AI market intelligence metrics and compile a professional SaaS market research report in markdown:\n\n{json.dumps(context_data, indent=2)}"
            payload = {
                "model": "llama3",
                "prompt": prompt,
                "system": "You are a world-class AI Startup Market Analyst. Write reports in clean Github Markdown.",
                "stream": False,
                "options": {"temperature": 0.7}
            }
            
            res = requests.post(f"{ollama_endpoint}/api/generate", json=payload, timeout=30)
            res.raise_for_status()
            report_content = res.json().get("response", MOCK_WEEKLY_REPORT)
            print("Ollama report generated successfully.")
        except Exception as e:
            print(f"Ollama call failed: {e}. Falling back to default briefing...")
            
    else:
        print("Running in mock mode or API key missing. Compiling pre-configured briefing...")
        
    # Generate quick summary for insights page
    leader_name = "Browser & Desktop Automation Agents"
    leader_score = 98
    quick_insight = "Browser automation agents represent the highest momentum category this week, showing a 24.2% star growth driven by zero-shot visual browser controllers."
    
    if trends:
        # Sort trends by momentum
        sorted_trends = sorted(trends, key=lambda x: x.momentum_score, reverse=True)
        leader_name = sorted_trends[0].category.name
        leader_score = int(sorted_trends[0].momentum_score)
        quick_insight = f"{leader_name} currently leads AI developer momentum with a score of {leader_score}, indicating strong repository growth and social validation."

    # Save to database
    now_str = datetime.utcnow().strftime("%Y-%W")  # Year-WeekNumber e.g., 2026-23
    slug = f"report-{now_str}"
    
    # Remove existing report for the same week to prevent duplicate rows
    db.query(WeeklyReport).filter(WeeklyReport.slug == slug).delete()
    db.commit()
    
    add_weekly_report(
        db=db,
        title=f"AI Startup Radar Briefing - Week {datetime.utcnow().strftime('%U, %Y')}",
        slug=slug,
        summary=quick_insight,
        content=report_content
    )
    print(f"Saved weekly briefing: {slug}")
    db.close()

if __name__ == "__main__":
    generate_weekly_report()
