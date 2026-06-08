from __future__ import annotations

CATEGORY_TAXONOMY: dict[str, dict[str, object]] = {
    "ai-agents": {
        "name": "AI Agents",
        "description": "Autonomous agents capable of executing complex workflows and reasoning tasks.",
        "keywords": {
            "autonomous agent": 6,
            "multi-agent": 6,
            "agentic": 5,
            "agent framework": 5,
            "agent workflow": 5,
            "crewai": 5,
            "autogen": 5,
            "babyagi": 5,
            "swarm": 4,
            "task loop": 4,
            "reasoning agent": 4,
        },
        "github_query": '"ai agent" OR "autonomous agent" OR "multi-agent" OR agentic',
    },
    "llm-frameworks": {
        "name": "LLM Applications & Frameworks",
        "description": "Frameworks for building applications powered by large language models, RAG, and orchestration libraries.",
        "keywords": {
            "llm": 4,
            "large language model": 5,
            "rag": 5,
            "retrieval augmented": 5,
            "langchain": 5,
            "llamaindex": 5,
            "vector database": 5,
            "vector db": 5,
            "embedding": 3,
            "ollama": 5,
            "vllm": 5,
            "inference": 3,
            "fine-tuning": 3,
            "transformers": 3,
        },
        "github_query": '"llm framework" OR langchain OR llamaindex OR rag OR "vector database"',
    },
    "browser-agents": {
        "name": "Browser & Desktop Automation Agents",
        "description": "AI systems designed to control browsers, desktops, and graphical interfaces.",
        "keywords": {
            "browser agent": 6,
            "web agent": 5,
            "browser automation": 6,
            "desktop agent": 5,
            "computer use": 5,
            "web navigation": 5,
            "gui agent": 5,
            "skyvern": 5,
            "lavague": 5,
            "webarena": 5,
            "browser-use": 5,
            "playwright agent": 4,
        },
        "github_query": '"browser agent" OR "web agent" OR "browser automation" OR "computer use"',
    },
    "voice-ai": {
        "name": "Voice & Audio AI",
        "description": "Synthesized voice, speech-to-text, audio intelligence, and real-time voice systems.",
        "keywords": {
            "voice cloning": 6,
            "text to speech": 6,
            "speech synthesis": 6,
            "speech recognition": 5,
            "speech-to-text": 5,
            "voice agent": 5,
            "audio model": 4,
            "tts": 5,
            "whisper": 5,
            "bark": 4,
            "elevenlabs": 4,
            "f5-tts": 5,
            "suno": 4,
        },
        "github_query": '"voice ai" OR "text to speech" OR whisper OR tts OR "speech synthesis"',
    },
    "coding-agents": {
        "name": "AI Coding Assistants",
        "description": "AI models and agents that write, refactor, test, search, and explain software systems.",
        "keywords": {
            "coding agent": 6,
            "developer agent": 6,
            "swe agent": 6,
            "software engineer agent": 6,
            "code generation": 4,
            "program synthesis": 4,
            "refactor": 3,
            "debugging": 3,
            "aider": 5,
            "cursor": 5,
            "copilot": 4,
            "devin": 5,
            "codex": 4,
        },
        "github_query": '"coding agent" OR "ai coding" OR "developer agent" OR "SWE agent"',
    },
    "multimodal-generation": {
        "name": "AI Image & Video Generation",
        "description": "Generative diffusion, image, video, and media editing model ecosystems.",
        "keywords": {
            "diffusion": 5,
            "diffusion model": 6,
            "text to image": 6,
            "text to video": 6,
            "image generation": 5,
            "video generation": 5,
            "generative video": 5,
            "stable diffusion": 6,
            "comfyui": 5,
            "controlnet": 4,
            "flux": 4,
            "sdxl": 4,
            "midjourney": 4,
        },
        "github_query": '"diffusion model" OR "image generation" OR "stable diffusion" OR "text to video"',
    },
}


DEFAULT_CATEGORY_SLUG = "llm-frameworks"


def category_seed_rows() -> list[dict[str, str]]:
    return [
        {
            "slug": slug,
            "name": str(meta["name"]),
            "description": str(meta["description"]),
        }
        for slug, meta in CATEGORY_TAXONOMY.items()
    ]
