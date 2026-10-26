from a2a.types import AgentSkill

from common import GitHubAgentExecutor, build_card, serve

PORT = 9002

SKILL = AgentSkill(
    id="open-issue",
    name="Open GitHub Issue",
    description="Turns a problem report into a GitHub issue.",
    tags=["github", "issues"],
    examples=["Open an issue for these review findings: ..."],
)

CARD = build_card(
    "GitHub Issue Agent",
    "Opens issues in the configured GitHub repository.",
    PORT,
    SKILL,
)

TOOLS = {"list_issues", "create_issue"}

PROMPT = (
    "You manage GitHub issues. Check list_issues first so you do not open a "
    "duplicate, then create one issue with a clear title and body. If the "
    "request says DRY RUN, do NOT call create_issue: only reply with the "
    "title and body you would use."
)

if __name__ == "__main__":
    serve(CARD, GitHubAgentExecutor(TOOLS, PROMPT), PORT)
