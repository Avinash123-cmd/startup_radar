import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "database" / "settings.json"
PERSISTED_KEYS = {"mock_mode", "ollama_endpoint", "collectors_limit"}

def _masked(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "********"
    return f"{value[:4]}...{value[-4:]}"

def get_settings():
    # Public settings shape consumed by the existing UI. Secrets are env-only and masked.
    config = {
        "mock_mode": False,
        "github_token": _masked(os.getenv("GITHUB_TOKEN", "")),
        "openai_key": _masked(os.getenv("OPENAI_KEY", os.getenv("OPENAI_API_KEY", ""))),
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
                for key in PERSISTED_KEYS:
                    if key in saved:
                        config[key] = saved[key]
        except Exception:
            pass
            
    return config

def get_runtime_settings():
    settings = get_settings()
    settings["github_token"] = os.getenv("GITHUB_TOKEN", "")
    settings["openai_key"] = os.getenv("OPENAI_KEY", os.getenv("OPENAI_API_KEY", ""))
    settings["reddit_client_id"] = os.getenv("REDDIT_CLIENT_ID", "")
    settings["reddit_client_secret"] = os.getenv("REDDIT_CLIENT_SECRET", "")
    settings["reddit_user_agent"] = os.getenv("REDDIT_USER_AGENT", "StartupRadar/1.0")
    settings["product_hunt_token"] = os.getenv("PRODUCT_HUNT_TOKEN", "")
    return settings

def save_settings(new_config: dict):
    current = get_settings()
    for key, value in new_config.items():
        if key in current and key in PERSISTED_KEYS:
            if key == "collectors_limit":
                current[key] = int(value)
            elif key == "mock_mode":
                current[key] = bool(value)
            else:
                current[key] = str(value)
                
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    persisted = {key: current[key] for key in PERSISTED_KEYS}
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(persisted, f, indent=4)
        
    return current


def get_platform_status(db) -> tuple[str, list[str]]:
    import os
    from database.models import CollectorRun, Repository
    
    warnings = []
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        warnings.append("GITHUB_TOKEN is missing. Repository collection runs in Limited Data Mode using the unauthenticated public GitHub API.")
        status = "Limited Data Mode"
    else:
        last_run = (
            db.query(CollectorRun)
            .filter(CollectorRun.source == "github")
            .order_by(CollectorRun.started_at.desc())
            .first()
        )
        if last_run and last_run.status == "failed":
            warnings.append(f"Last GitHub repository collection run failed: {last_run.message}")
            status = "Limited Data Mode"
        elif last_run and last_run.status == "skipped":
            warnings.append(f"Last GitHub repository collection run was skipped: {last_run.message}")
            status = "Limited Data Mode"
        else:
            status = "Live Data Mode"
            
    repo_count = db.query(Repository).count()
    if repo_count == 0:
        warnings.append("No repositories found in database. Run sync to populate.")
        status = "Limited Data Mode"
        
    return status, warnings

