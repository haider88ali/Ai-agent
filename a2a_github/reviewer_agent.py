from a2a.types import AgentSkill

from common import GitHubAgentExecutor, build_card, serve

PORT = 9001

SKILL = AgentSkill(
    id="review-pull-request",
    name="Review Pull Request",
    description="Reads a GitHub pull request and reports bugs and risks.",
    tags=["github", "review"],
    examples=["Review pull request #1"],
)

CARD = build_card(
    "GitHub Reviewer Agent",
    "Reviews pull requests in the configured GitHub repository. Read-only.",
    PORT,
    SKILL,
)

TOOLS = {"list_pull_requests", "get_pull_request", "get_pull_request_files"}

PROMPT = (
    "You review GitHub pull requests. Read the PR and its changed files with "
    "the tools, then reply with: a short summary, a list of concrete problems "
    "(or 'No problems found'), and a verdict of APPROVE or REQUEST_CHANGES. "
    "Never merge anything."
)

if __name__ == "__main__":
    serve(CARD, GitHubAgentExecutor(TOOLS, PROMPT), PORT)
