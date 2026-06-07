def classify_text(text: str) -> str:
    """
    Classifies text content into one of the core AI Startup Radar category slugs.
    """
    text = text.lower()
    
    # 1. AI Coding Assistants
    if any(k in text for k in ["aider", "cursor editor", "coding assistant", "swe agent", "developer agent", "devin", "programmer ai", "git agent"]):
        return "coding-agents"
        
    # 2. Browser & Desktop Automation Agents
    if any(k in text for k in ["browser agent", "web agent", "browser automation", "skyvern", "lavague", "playwright agent", "webarena"]):
        return "browser-agents"
        
    # 3. Voice & Audio AI
    if any(k in text for k in ["voice cloning", "text to speech", "speech synthesis", "whisper", "tts", "cloning voice", "audio model", "suno", "bark"]):
        return "voice-ai"
        
    # 4. AI Agents (General Orchestration)
    if any(k in text for k in ["autonomous agent", "multi-agent", "agentic", "crewai", "autogen", "task loop", "babyagi"]):
        return "ai-agents"
        
    # 5. AI Image & Video Generation
    if any(k in text for k in ["diffusion", "text to image", "text to video", "comfyui", "midjourney", "sora", "generative video", "stable diffusion"]):
        return "multimodal-generation"
        
    # 6. LLM Applications & Frameworks
    if any(k in text for k in ["llm", "rag", "langchain", "llamaindex", "vector db", "embedding", "llama 3", "local model", "milvus", "qdrant", "chromadb", "ollama"]):
        return "llm-frameworks"
        
    # Catch-all simple heuristics
    if "agent" in text:
        return "ai-agents"
    if "speech" in text or "audio" in text or "voice" in text:
        return "voice-ai"
    if "code" in text or "developer" in text or "coding" in text:
        return "coding-agents"
    if "image" in text or "video" in text or "draw" in text or "generation" in text:
        return "multimodal-generation"
    if "database" in text or "search" in text or "rag" in text or "model" in text or "prompt" in text:
        return "llm-frameworks"
        
    return "llm-frameworks"  # Default fallback