import os
import time
import logging
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from requests.auth import HTTPBasicAuth

from database.db import SessionLocal
from database.models import Category
from database.crud import add_market_data_point
from config import get_settings

# Configure logging
logger = logging.getLogger("reddit_collector")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

MOCK_REDDIT_POSTS = [
    {"title": "Is anyone using autonomous AI agents for real business tasks yet?", "subreddit": "r/Artificial", "ups": 320, "comments": 45, "author": "agent_master", "days_ago": 2, "category_slug": "ai-agents", "id": "red-101"},
    {"title": "AutoGen vs CrewAI: A deep dive comparison of agent frameworks", "subreddit": "r/MachineLearning", "ups": 480, "comments": 89, "author": "ml_researcher", "days_ago": 5, "category_slug": "ai-agents", "id": "red-102"},
    {"title": "Llama 3 runs incredibly fast on consumer hardware with Ollama + llama.cpp", "subreddit": "r/LocalLLaMA", "ups": 1120, "comments": 230, "author": "local_hacker", "days_ago": 1, "category_slug": "llm-frameworks", "id": "red-201"},
    {"title": "Comparing Vector DBs: Qdrant vs Milvus vs pgvector for RAG applications", "subreddit": "r/LocalLLaMA", "ups": 520, "comments": 112, "author": "rag_dev", "days_ago": 6, "category_slug": "llm-frameworks", "id": "red-202"},
    {"title": "AI Browser automation is getting scary good. WebArena scores are rising", "subreddit": "r/Artificial", "ups": 260, "comments": 34, "author": "web_surfer", "days_ago": 4, "category_slug": "browser-agents", "id": "red-301"},
    {"title": "F5-TTS is the best open voice cloning model I have tried. Truly matching ElevenLabs", "subreddit": "r/LocalLLaMA", "ups": 980, "comments": 156, "author": "audio_wave", "days_ago": 3, "category_slug": "voice-ai", "id": "red-401"},
    {"title": "Has anyone completely migrated their workflow to Cursor or Aider?", "subreddit": "r/LocalLLaMA", "ups": 650, "comments": 180, "author": "vim_coding", "days_ago": 8, "category_slug": "coding-agents", "id": "red-501"},
    {"title": "OpenDevin just hit v0.5 – SWE agents are maturing rapidly", "subreddit": "r/Artificial", "ups": 390, "comments": 78, "author": "devin_fan", "days_ago": 11, "category_slug": "coding-agents", "id": "red-502"},
    {"title": "ComfyUI workflow for creating hyper-realistic text-to-video using Stable Video Diffusion", "subreddit": "r/StableDiffusion", "ups": 1420, "comments": 310, "author": "artist_ai", "days_ago": 9, "category_slug": "multimodal-generation", "id": "red-601"}
]

def get_reddit_access_token(client_id: str, client_secret: str, user_agent: str) -> str:
    """
    Obtains a Reddit OAuth access token using the Client Credentials grant.
    """
    url = "https://www.reddit.com/api/v1/access_token"
    headers = {"User-Agent": user_agent}
    data = {"grant_type": "client_credentials"}
    auth = HTTPBasicAuth(client_id, client_secret)
    
    for attempt in range(3):
        try:
            logger.info(f"Authenticating with Reddit API (attempt {attempt + 1})...")
            response = requests.post(url, headers=headers, data=data, auth=auth, timeout=10)
            if response.status_code == 200:
                token_data = response.json()
                logger.info("Successfully authenticated with Reddit API.")
                return token_data.get("access_token")
            else:
                logger.warning(f"Reddit API credentials rejected. Status: {response.status_code}. Response: {response.text}")
        except Exception as e:
            logger.error(f"Error communicating with Reddit auth endpoint: {e}")
        time.sleep(2 ** attempt)
        
    return None

def classify_reddit_title(title: str) -> str:
    """
    Categorizes the post title into one of the core category slugs.
    """
    text = title.lower()
    
    # 1. AI Coding Assistants
    if any(k in text for k in ["aider", "cursor editor", "coding assistant", "swe agent", "developer agent", "devin", "programmer ai", "git agent", "autopilot"]):
        return "coding-agents"
        
    # 2. Browser & Desktop Automation Agents
    if any(k in text for k in ["browser agent", "web agent", "browser automation", "skyvern", "lavague", "playwright agent", "webarena"]):
        return "browser-agents"
        
    # 3. Voice & Audio AI
    if any(k in text for k in ["voice cloning", "text to speech", "speech synthesis", "whisper", "tts", "cloning voice", "audio model", "suno", "bark", "elevenlabs"]):
        return "voice-ai"
        
    # 4. AI Agents (General Orchestration)
    if any(k in text for k in ["autonomous agent", "multi-agent", "agentic", "crewai", "autogen", "task loop", "babyagi", "swarm"]):
        return "ai-agents"
        
    # 5. AI Image & Video Generation
    if any(k in text for k in ["diffusion", "text to image", "text to video", "comfyui", "midjourney", "sora", "generative video", "stable diffusion", "flux"]):
        return "multimodal-generation"
        
    # 6. LLM Applications & Frameworks
    if any(k in text for k in ["llm", "rag", "langchain", "llamaindex", "vector db", "embedding", "llama 3", "local model", "milvus", "qdrant", "chromadb", "ollama", "gpt-4", "claude", "gemini", "finetune", "inference"]):
        return "llm-frameworks"
        
    return "llm-frameworks"  # Fallback

def collect_reddit(db: Session, settings: dict) -> dict:
    """
    Ingests hot posts from subreddits using the Reddit OAuth API.
    Returns sync metrics dictionary.
    """
    logger.info("Initializing Reddit collection run...")
    categories = db.query(Category).all()
    cat_map = {c.slug: c.id for c in categories}
    cat_name_map = {c.id: c.name for c in categories}
    
    mock_mode = settings.get("mock_mode", True)
    limit = settings.get("collectors_limit", 20)
    
    stats = {
        "posts_collected": 0,
        "categories_detected": set(),
        "failed_requests": 0
    }
    
    # 1. Run in Mock/Sandbox Mode
    if mock_mode:
        logger.info("Running in Mock Mode. Injecting simulated Reddit post metrics...")
        for post in MOCK_REDDIT_POSTS:
            cat_id = cat_map.get(post["category_slug"])
            pub_date = datetime.utcnow() - timedelta(days=post["days_ago"])
            
            add_market_data_point(
                db=db,
                source="reddit",
                external_id=post["id"],
                title=f"[{post['subreddit']}] {post['title']}",
                description=f"Reddit post by u/{post['author']} with {post['ups']} upvotes and {post['comments']} comments.",
                url=f"https://reddit.com/{post['subreddit']}",
                engagement_score=post["ups"],
                published_at=pub_date,
                category_id=cat_id
            )
            stats["posts_collected"] += 1
            if cat_id:
                stats["categories_detected"].add(cat_name_map[cat_id])
                
        logger.info("Mock Reddit collection run complete.")
        stats["categories_detected"] = list(stats["categories_detected"])
        return stats

    # 2. Run in Production OAuth Mode
    client_id = os.getenv("REDDIT_CLIENT_ID", "")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    user_agent = os.getenv("REDDIT_USER_AGENT", "StartupRadar/1.0")
    
    if not client_id or not client_secret:
        logger.warning("Reddit API keys missing in environment variables. Falling back to Mock Mode...")
        settings["mock_mode"] = True
        return collect_reddit(db, settings)
        
    access_token = get_reddit_access_token(client_id, client_secret, user_agent)
    if not access_token:
        logger.error("Failed to retrieve Reddit access token. Run aborted.")
        stats["failed_requests"] = 1
        stats["categories_detected"] = []
        return stats
        
    subreddits = ["LocalLLaMA", "MachineLearning", "Artificial", "ChatGPT", "OpenAI"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": user_agent
    }
    
    for sub in subreddits:
        url = f"https://oauth.reddit.com/r/{sub}/hot"
        params = {"limit": limit}
        
        logger.info(f"Querying hot posts from sub: r/{sub}")
        
        success = False
        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=15)
                
                # Check remaining rate limits
                remaining = response.headers.get("x-ratelimit-remaining")
                reset = response.headers.get("x-ratelimit-reset")
                if remaining and float(remaining) < 10:
                    sleep_time = float(reset) if reset else 10
                    logger.warning(f"Reddit API rate limits low. Pausing for {sleep_time}s...")
                    time.sleep(sleep_time)
                
                if response.status_code == 429:
                    sleep_time = float(reset) if reset else 30
                    logger.warning(f"Too Many Requests (429). Sleeping for {sleep_time}s...")
                    time.sleep(sleep_time)
                    continue
                    
                response.raise_for_status()
                data = response.json()
                posts = data.get("data", {}).get("children", [])
                
                for child in posts:
                    post_data = child.get("data", {})
                    title = post_data.get("title")
                    ups = post_data.get("score", 0)
                    comments_count = post_data.get("num_comments", 0)
                    author = post_data.get("author", "unknown")
                    permalink = post_data.get("permalink")
                    external_id = post_data.get("id")
                    created_utc = post_data.get("created_utc", datetime.utcnow().timestamp())
                    
                    published_at = datetime.utcfromtimestamp(created_utc)
                    post_url = f"https://reddit.com{permalink}"
                    
                    # Compute category mapping dynamically
                    slug = classify_reddit_title(title)
                    cat_id = cat_map.get(slug)
                    
                    add_market_data_point(
                        db=db,
                        source="reddit",
                        external_id=external_id,
                        title=f"[r/{sub}] {title}",
                        description=f"Reddit post by u/{author} with {ups} score and {comments_count} comments.",
                        url=post_url,
                        engagement_score=ups,
                        published_at=published_at,
                        category_id=cat_id
                    )
                    stats["posts_collected"] += 1
                    if cat_id:
                        stats["categories_detected"].add(cat_name_map[cat_id])
                        
                success = True
                break
                
            except Exception as e:
                logger.error(f"Failed to query sub r/{sub} on attempt {attempt + 1}: {e}")
                time.sleep(2 ** attempt)
                
        if not success:
            logger.error(f"Aborting queries for r/{sub} after repeated attempts.")
            stats["failed_requests"] += 1
            
    stats["categories_detected"] = list(stats["categories_detected"])
    logger.info(f"Reddit collection finished. Results: {stats['posts_collected']} posts collected, {stats['failed_requests']} failed subreddits.")
    return stats

if __name__ == "__main__":
    db = SessionLocal()
    settings = get_settings()
    # Force OAuth test check locally if tokens configured
    stats = collect_reddit(db, settings)
    print("Execution statistics:", stats)
