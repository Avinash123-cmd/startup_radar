import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "database" / "settings.json"

def get_settings():
    # Default parameters, starts in mock mode for instant evaluation
    config = {
        "mock_mode": True,
        "github_token": os.getenv("GITHUB_TOKEN", ""),
        "openai_key": os.getenv("OPENAI_KEY", ""),
        "ollama_endpoint": os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434"),
        "collectors_limit": int(os.getenv("COLLECTORS_LIMIT", "20"))
    }
    
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                # Cast integer limits
                if "collectors_limit" in saved:
                    saved["collectors_limit"] = int(saved["collectors_limit"])
                config.update(saved)
        except Exception:
            pass
            
    return config

def save_settings(new_config: dict):
    current = get_settings()
    for key, value in new_config.items():
        if key in current:
            if key == "collectors_limit":
                current[key] = int(value)
            elif key == "mock_mode":
                current[key] = bool(value)
            else:
                current[key] = str(value)
                
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=4)
        
    return current
