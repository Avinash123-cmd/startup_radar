import json

with open("../database/category_history.json", "r") as f:
    history = json.load(f)

if len(history) < 2:
    print("Need at least 2 snapshots.")
    exit()

old = history[-2]["categories"]
new = history[-1]["categories"]

print("\n===== TREND GROWTH REPORT =====\n")

for category in new:

    old_value = old.get(category, 0)
    new_value = new.get(category, 0)

    growth = new_value - old_value

    print(
        f"{category}: {old_value} -> {new_value} | Growth: {growth}"
    )