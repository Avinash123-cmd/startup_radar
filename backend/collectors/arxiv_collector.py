import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import Category
from database.crud import add_market_data_point
from config import get_settings

MOCK_ARXIV_PAPERS = [
    # AI Agents
    {"title": "Agentic Orchestration: Collaborative Planning in Multi-Agent Ecosystems", "authors": "A. Chen et al.", "id": "arxiv-101", "days_ago": 4, "category_slug": "ai-agents"},
    {"title": "Evaluating Reasoning Loops in Autonomous Web Interaction Agents", "authors": "J. Doe et al.", "id": "arxiv-102", "days_ago": 11, "category_slug": "ai-agents"},
    # LLM Frameworks
    {"title": "Retrieval-Augmented Generation at Scale: Optimization and Quantization Methods", "authors": "R. Smith et al.", "id": "arxiv-201", "days_ago": 6, "category_slug": "llm-frameworks"},
    {"title": "Context Compression for Large Language Model Embeddings", "authors": "K. Lee et al.", "id": "arxiv-202", "days_ago": 15, "category_slug": "llm-frameworks"},
    # Browser Agents
    {"title": "Visual Web Agents: Zero-Shot Browser Navigation via Multimodal Vision Models", "authors": "Y. Wang et al.", "id": "arxiv-301", "days_ago": 2, "category_slug": "browser-agents"},
    # Voice AI
    {"title": "High-Fidelity Neural Speech Synthesis with Flow-Matching Models", "authors": "M. Brown et al.", "id": "arxiv-401", "days_ago": 8, "category_slug": "voice-ai"},
    # Coding Agents
    {"title": "SWE-Bench-X: Benchmarking Autonomous Software Development Agents", "authors": "H. Patel et al.", "id": "arxiv-501", "days_ago": 10, "category_slug": "coding-agents"},
    # Multimodal Generation
    {"title": "Stable Diffusion in Latent Space: Accelerating Text-to-Image Generation Rates", "authors": "G. Davis et al.", "id": "arxiv-601", "days_ago": 14, "category_slug": "multimodal-generation"}
]

def collect_arxiv(db: Session, settings: dict):
    print("Starting arXiv academic papers collection...")
    categories = db.query(Category).all()
    cat_map = {c.slug: c.id for c in categories}
    
    mock_mode = settings.get("mock_mode", True)
    limit = settings.get("collectors_limit", 20)
    
    if mock_mode:
        print("Generating mock arXiv papers...")
        for paper in MOCK_ARXIV_PAPERS:
            cat_id = cat_map.get(paper["category_slug"])
            pub_date = datetime.utcnow() - timedelta(days=paper["days_ago"])
            
            add_market_data_point(
                db=db,
                source="arxiv",
                external_id=paper["id"],
                title=f"[arXiv] {paper['title']}",
                description=f"Authors: {paper['authors']}. Academic paper published on arXiv.",
                url=f"https://arxiv.org/abs/{paper['id']}",
                engagement_score=random_citations(),
                published_at=pub_date,
                category_id=cat_id
            )
        print("Mock arXiv papers synchronized successfully.")
        return
        
    # Real arXiv query API
    # Query for "artificial intelligence" or specific categories
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": "cat:cs.AI OR cat:cs.CL OR cat:cs.LG",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.content)
        # XML namespace maps
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            paper_url = entry.find("atom:id", ns).text.strip()
            published_str = entry.find("atom:published", ns).text.strip()
            # Parse published e.g. "2024-03-24T18:25:00Z"
            try:
                published_at = datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%SZ")
            except:
                published_at = datetime.utcnow()
                
            external_id = paper_url.split("/abs/")[-1]
            
            # Extract summary/authors
            summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
            authors = [author.find("atom:name", ns).text for author in entry.findall("atom:author", ns)]
            authors_str = ", ".join(authors)
            
            # Map category from keyword heuristics
            category_id = None
            text_lower = f"{title} {summary}".lower()
            if any(k in text_lower for k in ["agent", "babyagi", "crewai", "autogen"]):
                category_id = cat_map.get("ai-agents")
            elif any(k in text_lower for k in ["llm", "rag", "langchain", "llama", "vector", "embedding"]):
                category_id = cat_map.get("llm-frameworks")
            elif any(k in text_lower for k in ["browser", "web automation", "skyvern"]):
                category_id = cat_map.get("browser-agents")
            elif any(k in text_lower for k in ["voice", "audio", "speech", "whisper", "tts"]):
                category_id = cat_map.get("voice-ai")
            elif any(k in text_lower for k in ["code", "coding", "editor", "developer", "aider", "cursor"]):
                category_id = cat_map.get("coding-agents")
            elif any(k in text_lower for k in ["diffusion", "image", "video", "multimodal", "comfyui"]):
                category_id = cat_map.get("multimodal-generation")
                
            add_market_data_point(
                db=db,
                source="arxiv",
                external_id=external_id,
                title=f"[arXiv] {title}",
                description=f"Authors: {authors_str}. Abstract: {summary[:250]}...",
                url=paper_url,
                engagement_score=random_citations(),
                published_at=published_at,
                category_id=category_id
            )
            
        print(f"arXiv preprints successfully queried and synced.")
        
    except Exception as e:
        print(f"arXiv API query failed: {e}. Falling back to mock generator.")
        settings["mock_mode"] = True
        collect_arxiv(db, settings)

def random_citations():
    import random
    # Return random realistic citations or reads score
    return random.randint(10, 150)

if __name__ == "__main__":
    db = SessionLocal()
    settings = get_settings()
    collect_arxiv(db, settings)
