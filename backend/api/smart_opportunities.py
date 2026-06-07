import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

@router.get("/smart-opportunities")
def smart_opportunities():

    file_path = BASE_DIR / "database" / "category_history.json"

    with open(file_path, "r") as f:
        history = json.load(f)

    if len(history) < 2:
        return {"message": "Need more history"}

    old = history[-2]["categories"]
    new = history[-1]["categories"]

    rankings = []

    for category in new:

        old_value = old.get(category, 1)
        new_value = new.get(category, 1)

        growth_percent = (
            (new_value - old_value) / old_value
        ) * 100

        score = (
            new_value * 0.7
            +
            growth_percent * 0.3
        )

        rankings.append({
            "category": category,
            "growth_percent": round(growth_percent, 2),
            "score": round(score, 2)
        })

    rankings.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return rankings