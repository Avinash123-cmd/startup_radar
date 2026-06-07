import requests
import time
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import Category
from database.crud import create_or_update_repository, seed_categories
from config import get_settings

SEARCH_QUERIES = {
    "ai-agents": '"ai agent" OR "autonomous agent" OR "multi-agent"',
    "llm-frameworks": '"llm framework" OR "langchain" OR "llamaindex" OR "rag"',
    "browser-agents": '"browser agent" OR "web agent" OR "browser automation ai"',
    "voice-ai": '"voice ai" OR "text to speech" OR "whisper" OR "speech synthesis"',
    "coding-agents": '"coding agent" OR "ai coding" OR "copilot" OR "developer agent"',
    "multimodal-generation": '"diffusion model" OR "image generation" OR "stable diffusion" OR "text to video"'
}

MOCK_REPOS = {
    "ai-agents": [
        {"name": "crewAI", "full_name": "crewAIInc/crewAI", "url": "https://github.com/crewAIInc/crewAI", "description": "Framework for orchestrating role-playing, autonomous AI agents.", "stars": 19500, "forks": 2400, "language": "Python"},
        {"name": "autogen", "full_name": "microsoft/autogen", "url": "https://github.com/microsoft/autogen", "description": "A programming framework for agentic AI. Autogen enables multiple agents.", "stars": 29800, "forks": 4100, "language": "Python"},
        {"name": "ChatDev", "full_name": "OpenBMB/ChatDev", "url": "https://github.com/OpenBMB/ChatDev", "description": "Create Customized Software using Natural Language Idea through LLM-powered Multi-Agent Collaboration.", "stars": 24200, "forks": 3200, "language": "Python"},
        {"name": "SuperAGI", "full_name": "TransformerOptimus/SuperAGI", "url": "https://github.com/TransformerOptimus/SuperAGI", "description": "A dev-first open source autonomous AI agent framework.", "stars": 14500, "forks": 1900, "language": "Python"},
        {"name": "babyagi", "full_name": "yoheinakajima/babyagi", "url": "https://github.com/yoheinakajima/babyagi", "description": "An AI-powered task management system.", "stars": 18200, "forks": 2600, "language": "Python"}
    ],
    "llm-frameworks": [
        {"name": "langchain", "full_name": "langchain-ai/langchain", "url": "https://github.com/langchain-ai/langchain", "description": "Building applications with LLMs through composability.", "stars": 85000, "forks": 12500, "language": "TypeScript"},
        {"name": "llama_index", "full_name": "run-llama/llama_index", "url": "https://github.com/run-llama/llama_index", "description": "Data framework for your LLM applications.", "stars": 33200, "forks": 4800, "language": "Python"},
        {"name": "ollama", "full_name": "ollama/ollama", "url": "https://github.com/ollama/ollama", "description": "Get up and running with large language models locally.", "stars": 76000, "forks": 5900, "language": "Go"},
        {"name": "vllm", "full_name": "vllm-project/vllm", "url": "https://github.com/vllm-project/vllm", "description": "A high-throughput and memory-efficient LLM serving engine.", "stars": 23400, "forks": 3100, "language": "Python"},
        {"name": "milvus", "full_name": "milvus-io/milvus", "url": "https://github.com/milvus-io/milvus", "description": "A cloud-native vector database written in Go.", "stars": 27800, "forks": 3900, "language": "Go"}
    ],
    "browser-agents": [
        {"name": "browser-use", "full_name": "browser-use/browser-use", "url": "https://github.com/browser-use/browser-use", "description": "Make websites usable by AI agents with a single line of code.", "stars": 12800, "forks": 1100, "language": "Python"},
        {"name": "LaVague", "full_name": "lavague-ai/LaVague", "url": "https://github.com/lavague-ai/LaVague", "description": "Large Action Model framework for Web Automation.", "stars": 6500, "forks": 620, "language": "Python"},
        {"name": "Skyvern", "full_name": "Skyvern-AI/Skyvern", "url": "https://github.com/Skyvern-AI/Skyvern", "description": "Automate browser-based workflows using LLMs and Computer Vision.", "stars": 8900, "forks": 950, "language": "Python"},
        {"name": "multi-on", "full_name": "multion-ai/multion-sdk", "url": "https://github.com/multion-ai/multion-sdk", "description": "SDK for MultiOn API to control a browser agent.", "stars": 1200, "forks": 150, "language": "TypeScript"},
        {"name": "web-arena", "full_name": "web-arena-x/webarena", "url": "https://github.com/web-arena-x/webarena", "description": "A highly realistic environment for evaluating web agents.", "stars": 2100, "forks": 320, "language": "Python"}
    ],
    "voice-ai": [
        {"name": "XTTS", "full_name": "coqui-ai/TTS", "url": "https://github.com/coqui-ai/TTS", "description": "Advanced Deep Learning text-to-speech toolkit.", "stars": 31500, "forks": 4200, "language": "Python"},
        {"name": "whisper", "full_name": "openai/whisper", "url": "https://github.com/openai/whisper", "description": "Robust Speech Recognition via Large-Scale Weak Supervision.", "stars": 112000, "forks": 14200, "language": "Python"},
        {"name": "bark", "full_name": "suno-ai/bark", "url": "https://github.com/suno-ai/bark", "description": "Transformer-based text-to-audio model.", "stars": 32400, "forks": 3800, "language": "Python"},
        {"name": "GPT-SoVITS", "full_name": "RVC-Boss/GPT-SoVITS", "url": "https://github.com/RVC-Boss/GPT-SoVITS", "description": "Few-shot Voice Cloning and Text-to-Speech system.", "stars": 26800, "forks": 3100, "language": "Python"},
        {"name": "F5-TTS", "full_name": "SWHL/F5-TTS", "url": "https://github.com/SWHL/F5-TTS", "description": "A fast, non-autoregressive flow-matching speech generator.", "stars": 8200, "forks": 850, "language": "Python"}
    ],
    "coding-agents": [
        {"name": "aider", "full_name": "paul-gauthier/aider", "url": "https://github.com/paul-gauthier/aider", "description": "aider is AI pair programming in your terminal.", "stars": 18900, "forks": 2100, "language": "Python"},
        {"name": "Cursor", "full_name": "getcursor/cursor", "url": "https://github.com/getcursor/cursor", "description": "Config files and custom tools for the Cursor editor.", "stars": 5400, "forks": 490, "language": "TypeScript"},
        {"name": "OpenDevin", "full_name": "All-Hands-AI/OpenDevin", "url": "https://github.com/All-Hands-AI/OpenDevin", "description": "An open-source autonomous software engineer.", "stars": 28500, "forks": 3400, "language": "Python"},
        {"name": "gpt-engineer", "full_name": "gpt-engineer-org/gpt-engineer", "url": "https://github.com/gpt-engineer-org/gpt-engineer", "description": "Specify what you want it to build, the AI asks clarifying questions.", "stars": 49200, "forks": 8200, "language": "Python"},
        {"name": "Devin-Mocks", "full_name": "devin-community/devin-agent", "url": "https://github.com/devin-community/devin-agent", "description": "An open framework modeling the Devin SWE agent.", "stars": 3400, "forks": 380, "language": "Python"}
    ],
    "multimodal-generation": [
        {"name": "stable-diffusion", "full_name": "CompVis/stable-diffusion", "url": "https://github.com/CompVis/stable-diffusion", "description": "A latent text-to-image diffusion model.", "stars": 64800, "forks": 10500, "language": "Python"},
        {"name": "ComfyUI", "full_name": "comfyanonymous/ComfyUI", "url": "https://github.com/comfyanonymous/ComfyUI", "description": "The most powerful and modular stable diffusion GUI.", "stars": 41200, "forks": 4800, "language": "Python"},
        {"name": "diffusers", "full_name": "huggingface/diffusers", "url": "https://github.com/huggingface/diffusers", "description": "State-of-the-art diffusion models for image and audio generation.", "stars": 24500, "forks": 3600, "language": "Python"},
        {"name": "stable-diffusion-webui", "full_name": "AUTOMATIC1111/stable-diffusion-webui", "url": "https://github.com/AUTOMATIC1111/stable-diffusion-webui", "description": "Stable Diffusion web UI.", "stars": 128000, "forks": 25200, "language": "Python"},
        {"name": "animatediff", "full_name": "guoyww/AnimateDiff", "url": "https://github.com/guoyww/AnimateDiff", "description": "Official implementation of AnimateDiff.", "stars": 9200, "forks": 890, "language": "Python"}
    ]
}

def collect_github(db: Session, settings: dict):
    print("Starting GitHub Repository collection...")
    
    # 1. Seed categories
    seed_categories(db)
    categories = db.query(Category).all()
    cat_map = {c.slug: c.id for c in categories}
    
    limit = settings.get("collectors_limit", 20)
    mock_mode = settings.get("mock_mode", True)
    token = settings.get("github_token", "")
    
    if mock_mode:
        print("Running in MOCK mode. Generating realistic repository histories...")
        # Populate repositories and snapshots over time (history simulation)
        for slug, repos in MOCK_REPOS.items():
            cat_id = cat_map.get(slug)
            if not cat_id:
                continue
                
            for repo_data in repos:
                # Add historical star snapshots
                # To simulate growth, we backdate snapshots
                final_stars = repo_data["stars"]
                final_forks = repo_data["forks"]
                
                # Base repository creation
                repo = create_or_update_repository(
                    db=db,
                    name=repo_data["name"],
                    full_name=repo_data["full_name"],
                    url=repo_data["url"],
                    description=repo_data["description"],
                    stars=final_stars,
                    forks=final_forks,
                    language=repo_data["language"],
                    category_id=cat_id
                )
                
                # Insert historical snapshots (30 days ago, 15 days ago, 7 days ago)
                from database.models import RepositorySnapshot
                db.query(RepositorySnapshot).filter(RepositorySnapshot.repository_id == repo.id).delete()
                
                # Generate random historical rates (growth over month)
                growth_rate = random.uniform(0.05, 0.25)  # 5% to 25% monthly growth
                
                snapshots = [
                    (30, int(final_stars * (1 - growth_rate)), int(final_forks * (1 - growth_rate))),
                    (15, int(final_stars * (1 - growth_rate * 0.5)), int(final_forks * (1 - growth_rate * 0.5))),
                    (7, int(final_stars * (1 - growth_rate * 0.2)), int(final_forks * (1 - growth_rate * 0.2))),
                    (0, final_stars, final_forks)
                ]
                
                for days_ago, st, fk in snapshots:
                    snap_date = datetime.utcnow() - timedelta(days=days_ago)
                    db_snap = RepositorySnapshot(
                        repository_id=repo.id,
                        stars=st,
                        forks=fk,
                        recorded_at=snap_date
                    )
                    db.add(db_snap)
                
                # Update current repository status to match the latest snapshot
                repo.stars = final_stars
                repo.forks = final_forks
                db.commit()
                
        print(f"Mock GitHub repositories successfully synchronized.")
        return
        
    # Real GitHub API collection
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
        
    for slug, query in SEARCH_QUERIES.items():
        cat_id = cat_map.get(slug)
        if not cat_id:
            continue
            
        print(f"Querying GitHub for: {slug} (query: {query})")
        url = "https://api.github.com/search/repositories"
        params = {
            "q": f"{query} stars:>100",
            "sort": "stars",
            "order": "desc",
            "per_page": min(limit, 100)
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 403:
                print("GitHub API rate limit hit! Falling back to mock generator for safety...")
                # Rate limit fallback
                settings["mock_mode"] = True
                collect_github(db, settings)
                return
                
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            
            for item in items:
                create_or_update_repository(
                    db=db,
                    name=item["name"],
                    full_name=item["full_name"],
                    url=item["html_url"],
                    description=item["description"],
                    stars=item["stargazers_count"],
                    forks=item["forks_count"],
                    language=item["language"] or "Other",
                    category_id=cat_id
                )
            # Standard delay to avoid API throttling
            time.sleep(1)
            
        except Exception as e:
            print(f"Failed to fetch {slug} from GitHub API: {e}. Running mock sync as fallback.")
            settings["mock_mode"] = True
            collect_github(db, settings)
            return

if __name__ == "__main__":
    db = SessionLocal()
    settings = get_settings()
    collect_github(db, settings)