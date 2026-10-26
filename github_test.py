
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN")
owner = os.getenv("GITHUB_OWNER")
repo = os.getenv("GITHUB_REPO")

if not all([token, owner, repo]):
    raise ValueError("Check GITHUB_TOKEN, GITHUB_OWNER, and GITHUB_REPO in .env")

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

url = f"https://api.github.com/repos/{owner}/{repo}"

response = httpx.get(url, headers=headers, timeout=20)
response.raise_for_status()

repository = response.json()

print("GitHub connection successful!")
print("Repository:", repository["full_name"])
print("Default branch:", repository["default_branch"])
