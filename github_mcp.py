
import os

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")

if not all([GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO]):
    raise ValueError("Missing GitHub configuration in .env")

mcp = FastMCP("GitHub MCP Server")

GITHUB_API = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


@mcp.tool()
def list_pull_requests(state: str = "open") -> list[dict]:
    """List pull requests in the configured GitHub repository.

    Args:
        state: Pull request state: open, closed, or all.
    """
    if state not in {"open", "closed", "all"}:
        raise ValueError("state must be open, closed, or all")

    url = (
        f"{GITHUB_API}/repos/{GITHUB_OWNER}/"
        f"{GITHUB_REPO}/pulls"
    )

    response = httpx.get(
        url,
        headers=HEADERS,
        params={"state": state, "per_page": 20},
        timeout=20,
    )
    response.raise_for_status()

    pull_requests = response.json()

    return [
        {
            "number": pr["number"],
            "title": pr["title"],
            "state": pr["state"],
            "author": pr["user"]["login"],
            "url": pr["html_url"],
            "created_at": pr["created_at"],
            "head_branch": pr["head"]["ref"],
            "base_branch": pr["base"]["ref"],
        }
        for pr in pull_requests
    ]

@mcp.tool()
def get_pull_request(pr_number: int) -> dict:
    """Get details for a pull request by its number."""
    url = (
        f"{GITHUB_API}/repos/{GITHUB_OWNER}/"
        f"{GITHUB_REPO}/pulls/{pr_number}"
    )

    response = httpx.get(
        url,
        headers=HEADERS,
        timeout=20,
    )
    
    response.raise_for_status()
    pr = response.json()

    return {
        "number": pr["number"],
        "title": pr["title"],
        "body": pr["body"],
        "state": pr["state"],
        "author": pr["user"]["login"],
        "url": pr["html_url"],
        "head_branch": pr["head"]["ref"],
        "base_branch": pr["base"]["ref"],
        "merged": pr["merged"],
        "additions": pr["additions"],
        "deletions": pr["deletions"],
        "changed_files": pr["changed_files"],
    }


@mcp.tool()
def get_pull_request_files(pr_number: int) -> list[dict]:
    """Get the files changed by a pull request."""
    url = (
        f"{GITHUB_API}/repos/{GITHUB_OWNER}/"
        f"{GITHUB_REPO}/pulls/{pr_number}/files"
    )

    response = httpx.get(
        url,
        headers=HEADERS,
        params={"per_page": 100},
        timeout=20,
    )
    response.raise_for_status()

    return [
        {
            "filename": file["filename"],
            "status": file["status"],
            "additions": file["additions"],
            "deletions": file["deletions"],
            "changes": file["changes"],
            "patch": file.get("patch", ""),
        }
        for file in response.json()
    ]


@mcp.tool()
def list_issues(state: str = "open") -> list[dict]:
    """List GitHub issues. State can be open, closed, or all."""
    if state not in {"open", "closed", "all"}:
        raise ValueError("state must be open, closed, or all")

    url = (
        f"{GITHUB_API}/repos/{GITHUB_OWNER}/"
        f"{GITHUB_REPO}/issues"
    )

    response = httpx.get(
        url,
        headers=HEADERS,
        params={"state": state, "per_page": 20},
        timeout=20,
    )
    response.raise_for_status()

    # GitHub's issues endpoint also returns pull requests.
    return [
        {
            "number": issue["number"],
            "title": issue["title"],
            "state": issue["state"],
            "author": issue["user"]["login"],
            "url": issue["html_url"],
            "created_at": issue["created_at"],
        }
        for issue in response.json()
        if "pull_request" not in issue
    ]


@mcp.tool()
def create_issue(title: str, body: str = "", labels: list[str] | None = None) -> dict:
    """Open a new GitHub issue in the configured repository."""
    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues"

    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels

    response = httpx.post(url, headers=HEADERS, json=payload, timeout=20)
    response.raise_for_status()
    issue = response.json()

    return {
        "number": issue["number"],
        "title": issue["title"],
        "url": issue["html_url"],
    }


@mcp.tool()
def merge_pull_request(
    pr_number: int,
    confirm: bool = False,
    merge_method: str = "squash",
) -> dict:
    """Merge a pull request. Irreversible: only call with confirm=True
    after the user has explicitly approved merging this PR.
    merge_method can be merge, squash, or rebase."""
    if not confirm:
        return {
            "merged": False,
            "message": (
                f"Merge of PR #{pr_number} not done. Ask the user to "
                "approve, then call again with confirm=True."
            ),
        }
    if merge_method not in {"merge", "squash", "rebase"}:
        raise ValueError("merge_method must be merge, squash, or rebase")

    url = (
        f"{GITHUB_API}/repos/{GITHUB_OWNER}/"
        f"{GITHUB_REPO}/pulls/{pr_number}/merge"
    )

    response = httpx.put(
        url,
        headers=HEADERS,
        json={"merge_method": merge_method},
        timeout=20,
    )
    response.raise_for_status()
    result = response.json()

    return {"merged": result["merged"], "message": result["message"]}


@mcp.prompt()
def review_pull_request(pr_number: int) -> str:
    """Prompt template for reviewing a pull request."""
    return (
        f"Review pull request #{pr_number}. Use get_pull_request and "
        "get_pull_request_files, then summarize the changes, point out "
        "bugs or risks, and recommend approve or request changes. "
        "Do not merge it."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
