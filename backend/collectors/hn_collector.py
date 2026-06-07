import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import Category
from database.crud import add_market_data_point
from config import get_settings

MOCK_HN_STORIES = [
    # AI Agents
    {"title": "Show HN: CrewAI – orchestrating role-playing autonomous AI agents", "url": "https://github.com/crewAIInc/crewAI", "score": 450, "days_ago": 3, "category_slug": "ai-agents", "id": "hn-101"},
    {"title": "The Rise of Multi-Agent Systems in Production", "url": "https://blog.autogen.microsoft/agents", "score": 280, "days_ago": 8, "category_slug": "ai-agents", "id": "hn-102"},
    {"title": " babyagi: Simple task execution loop with GPT-4", "url": "https://github.com/yoheinakajima/babyagi", "score": 780, "days_ago": 25, "category_slug": "ai-agents", "id": "hn-103"},
    # LLM Frameworks
    {"title": "Ollama: Run Llama 3, Mistral locally", "url": "https://ollama.ai", "score": 1250, "days_ago": 4, "category_slug": "llm-frameworks", "id": "hn-201"},
    {"title": "Why RAG is the future of enterprise document search", "url": "https://arxiv.org/abs/rag-future", "score": 340, "days_ago": 12, "category_slug": "llm-frameworks", "id": "hn-202"},
    {"title": "LangChain v0.1.0 Released", "url": "https://blog.langchain.dev/release-v0.1.0", "score": 620, "days_ago": 19, "category_slug": "llm-frameworks", "id": "hn-203"},
    # Browser Agents
    {"title": "Show HN: Browser-use – Let AI agents browse the web for you", "url": "https://github.com/browser-use/browser-use", "score": 530, "days_ago": 2, "category_slug": "browser-agents", "id": "hn-301"},
    {"title": "Skyvern: Visual browser automation using computer vision and LLMs", "url": "https://skyvern.com", "score": 210, "days_ago": 9, "category_slug": "browser-agents", "id": "hn-302"},
    # Voice AI
    {"title": "Suno Bark: Open-Source Audio Generation Model", "url": "https://github.com/suno-ai/bark", "score": 920, "days_ago": 15, "category_slug": "voice-ai", "id": "hn-401"},
    {"title": "F5-TTS: Non-autoregressive Voice Clone in 5 Seconds", "url": "https://f5-tts.github.io", "score": 310, "days_ago": 5, "category_slug": "voice-ai", "id": "hn-402"},
    # Coding Agents
    {"title": "Aider: Write code with AI in your terminal using git", "url": "https://aider.chat", "score": 670, "days_ago": 7, "category_slug": "coding-agents", "id": "hn-501"},
    {"title": "OpenDevin – An open-source SWE agent alternative", "url": "https://github.com/All-Hands-AI/OpenDevin", "score": 840, "days_ago": 14, "category_slug": "coding-agents", "id": "hn-502"},
    # Multimodal Generation
    {"title": "Stable Diffusion XL Release", "url": "https://stability.ai/stable-diffusion", "score": 1820, "days_ago": 22, "category_slug": "multimodal-generation", "id": "hn-601"},
    {"title": "ComfyUI Node Layouts for Text-to-Video Synthesis", "url": "https://comfy.ui/video", "score": 410, "days_ago": 10, "category_slug": "multimodal-generation", "id": "hn-602"}
]

def collect_hn(db: Session, settings: dict):
    print("Starting Hacker News stories collection...")
    categories = db.query(Category).all()
    cat_map = {c.slug: c.id for c in categories}
    
    mock_mode = settings.get("mock_mode", True)
    limit = settings.get("collectors_limit", 20)
    
    if mock_mode:
        print("Generating mock Hacker News points...")
        for story in MOCK_HN_STORIES:
            cat_id = cat_map.get(story["category_slug"])
            pub_date = datetime.utcnow() - timedelta(days=story["days_ago"])
            
            add_market_data_point(
                db=db,
                source="hacker_news",
                external_id=story["id"],
                title=story["title"],
                description=f"Hacker News story with {story['score']} points.",
                url=story["url"],
                engagement_score=story["score"],
                published_at=pub_date,
                category_id=cat_id
            )
        print("Mock Hacker News stories synchronized successfully.")
        return
        
    # Real HN Algolia API Search
    # We will query Algolia for "AI" stories in the past week
    url = "https://hn.algolia.com/api/v1/search"
    one_week_ago = int((datetime.utcnow() - timedelta(days=7)).timestamp())
    params = {
        "query": "AI",
        "tags": "story",
        "numericFilters": f"created_at_i>{one_week_ago}",
        "hitsPerPage": limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        hits = data.get("hits", [])
        
        for hit in hits:
            title = hit.get("title")
            story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
            score = hit.get("points", 0)
            created_at_str = hit.get("created_at")
            # Parse created_at e.g. "2024-03-24T18:25:00Z"
            try:
                published_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
            except:
                published_at = datetime.utcnow()
                
            external_id = hit.get("objectID")
            
            # Map category from keyword heuristics
            category_id = None
            title_lower = title.lower()
            if any(k in title_lower for k in ["agent", "babyagi", "crewai", "autogen"]):
                category_id = cat_map.get("ai-agents")
            elif any(k in title_lower for k in ["llm", "rag", "langchain", "llama", "vector"]):
                category_id = cat_map.get("llm-frameworks")
            elif any(k in title_lower for k in ["browser", "web automation", "skyvern"]):
                category_id = cat_map.get("browser-agents")
            elif any(k in title_lower for k in ["voice", "audio", "speech", "whisper", "tts"]):
                category_id = cat_map.get("voice-ai")
            elif any(k in title_lower for k in ["code", "coding", "editor", "developer", "aider", "cursor"]):
                category_id = cat_map.get("coding-agents")
            elif any(k in title_lower for k in ["diffusion", "image", "video", "multimodal", "comfyui"]):
                category_id = cat_map.get("multimodal-generation")
                
            add_market_data_point(
                db=db,
                source="hacker_news",
                external_id=external_id,
                title=title,
                description=f"Hacker News story with {score} points.",
                url=story_url,
                engagement_score=score,
                published_at=published_at,
                category_id=category_id
            )
            
        print(f"Hacker News stories successfully queried and synced.")
        
    except Exception as e:
        print(f"Hacker News API search failed: {e}. Falling back to mock generator.")
        settings["mock_mode"] = True
        collect_hn(db, settings)

if __name__ == "__main__":
    db = SessionLocal()
    settings = get_settings()
    collect_hn(db, settings)
