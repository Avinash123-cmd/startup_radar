import json
from datetime import datetime

# Read latest repos

with open("../collectors/repos.json", "r") as f:
    repos = json.load(f)

# Read history

try:
    with open("../database/history.json", "r") as f:
        history = json.load(f)
except:
    history = []

# New snapshot

snapshot = {
    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "repos": repos
}

history.append(snapshot)

# Save history

with open("../database/history.json", "w") as f:
    json.dump(history, f, indent=4)

print("Snapshot saved!")