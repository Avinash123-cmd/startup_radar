import json

with open("../database/category_history.json", "r") as f:
    history = json.load(f)

latest = history[-1]["categories"]

print("\n===== OPPORTUNITY RANKING =====\n")

ranked = sorted(
    latest.items(),
    key=lambda x: x[1],
    reverse=True
)

for i, (category, score) in enumerate(ranked, start=1):

    print(
        f"{i}. {category} | Opportunity Score: {score}"
    )