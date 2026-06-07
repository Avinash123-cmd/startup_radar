import json
from collections import defaultdict

def classify_repo(repo_name):

    name = repo_name.lower()

    if "agent" in name:
        return "AI Agents"

    elif "gpt" in name:
        return "LLM Applications"

    elif "lang" in name:
        return "LLM Frameworks"

    elif "diffusion" in name:
        return "AI Image Generation"

    elif "webui" in name:
        return "AI Interfaces"

    elif "n8n" in name:
        return "Workflow Automation"

    else:
        return "Other"


with open("../collectors/repos.json", "r") as f:
    repos = json.load(f)

category_data = defaultdict(int)

for repo in repos:

    category = classify_repo(repo["name"])

    category_data[category] += repo["stars"]

print("\n===== AI STARTUP RADAR =====\n")

ranked = sorted(
    category_data.items(),
    key=lambda x: x[1],
    reverse=True
)

for i, (category, stars) in enumerate(ranked, start=1):

    print(
        f"{i}. {category} | Total Stars: {stars}"
    )