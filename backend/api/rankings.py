import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

@router.get("/rankings")
def rankings():

    file_path = BASE_DIR / "database" / "category_history.json"

    with open(file_path, "r") as f:
        history = json.load(f)

    latest = history[-1]["categories"]

    results = []

    for category, score in latest.items():

        opportunity_score = round(score / 100000, 2)

        results.append({
            "category": category,
            "opportunity_score": opportunity_score
        })

    results.sort(
        key=lambda x: x["opportunity_score"],
        reverse=True
    )

    return results