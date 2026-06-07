import json
from collections import defaultdict
from datetime import datetime

with open("../collectors/repos.json", "r", encoding="utf-8") as f:
    repos = json.load(f)

category_scores = defaultdict(int)

for repo in repos:

    category = repo["category"]

    category_scores[category] += repo["stars"]

snapshot = {
    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "categories": dict(category_scores)
}

try:
    with open("../database/category_history.json", "r") as f:
        history = json.load(f)
except:
    history = []

history.append(snapshot)

with open("../database/category_history.json", "w") as f:
    json.dump(history, f, indent=4)

print("Category score snapshot saved!")