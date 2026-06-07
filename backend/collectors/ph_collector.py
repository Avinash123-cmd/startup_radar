import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import Category
from database.crud import add_market_data_point
from config import get_settings

MOCK_PH_PRODUCTS = [
    # AI Agents
    {"name": "CrewAI Studio", "tagline": "Build and visualize multi-agent networks in a no-code canvas.", "votes": 780, "days_ago": 3, "category_slug": "ai-agents", "id": "ph-101"},
    {"name": "MultiAgent.xyz", "tagline": "Deploy self-hosted AI agent swarms in one click.", "votes": 410, "days_ago": 9, "category_slug": "ai-agents", "id": "ph-102"},
    # LLM Frameworks
    {"name": "Ollama Desktop", "tagline": "One-click local LLM runs with an interactive desktop interface.", "votes": 1250, "days_ago": 2, "category_slug": "llm-frameworks", "id": "ph-201"},
    {"name": "RAG-in-a-Box", "tagline": "Zero-config document ingest and Q&A engine using local embeddings.", "votes": 530, "days_ago": 11, "category_slug": "llm-frameworks", "id": "ph-202"},
    # Browser Agents
    {"name": "BrowserAgent.ai", "tagline": "An API that lets your applications click, type, and read web pages.", "votes": 890, "days_ago": 1, "category_slug": "browser-agents", "id": "ph-301"},
    # Voice AI
    {"name": "VoiceMimic", "tagline": "Clone voice models from a 3-second recording with high expressive range.", "votes": 680, "days_ago": 7, "category_slug": "voice-ai", "id": "ph-401"},
    # Coding Agents
    {"name": "Copilot.nvim", "tagline": "A lightweight agentic plugin supporting full-project refactors in Vim.", "votes": 340, "days_ago": 10, "category_slug": "coding-agents", "id": "ph-501"},
    {"name": "Devin Studio", "tagline": "Collaborative cloud editor featuring autonomous coding companion agents.", "votes": 950, "days_ago": 5, "category_slug": "coding-agents", "id": "ph-502"},
    # Multimodal Generation
    {"name": "ComfyUI Cloud", "tagline": "Run heavy ComfyUI workflow pipelines instantly on serverless GPUs.", "votes": 840, "days_ago": 6, "category_slug": "multimodal-generation", "id": "ph-601"}
]

def collect_ph(db: Session, settings: dict):
    print("Starting Product Hunt products collection...")
    categories = db.query(Category).all()
    cat_map = {c.slug: c.id for c in categories}
    
    # Product Hunt is always mock-supported in MVP due to heavy OAuth flow, but can be scaled in production
    print("Generating Product Hunt updates...")
    for prod in MOCK_PH_PRODUCTS:
        cat_id = cat_map.get(prod["category_slug"])
        pub_date = datetime.utcnow() - timedelta(days=prod["days_ago"])
        
        add_market_data_point(
            db=db,
            source="product_hunt",
            external_id=prod["id"],
            title=f"[Product Hunt] {prod['name']}",
            description=f"Tagline: {prod['tagline']} Upvotes: {prod['votes']}",
            url="https://www.producthunt.com",
            engagement_score=prod["votes"],
            published_at=pub_date,
            category_id=cat_id
        )
    print("Product Hunt launches successfully synchronized.")

if __name__ == "__main__":
    db = SessionLocal()
    settings = get_settings()
    collect_ph(db, settings)
