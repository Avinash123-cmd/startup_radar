import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

@router.get("/growth")
def get_growth():

    file_path = BASE_DIR / "database" / "category_history.json"

    with open(file_path, "r", encoding="utf-8") as f:
        history = json.load(f)

    if len(history) < 2:
        return {"message": "Need at least 2 snapshots"}

    old = history[-2]["categories"]
    new = history[-1]["categories"]

    result = []

    for category in new:

        old_value = old.get(category, 0)
        new_value = new.get(category, 0)

        growth = new_value - old_value

        result.append({
            "category": category,
            "previous": old_value,
            "current": new_value,
            "growth": growth
        })

    return result