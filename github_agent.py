import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

HERE = Path(__file__).parent

# Your GitHub MCP server, started by the SDK over stdio.
GITHUB_SERVER = {
    "command": str(HERE / ".venv/bin/python"),
    "args": [str(HERE / "github_mcp.py")],
}

# Read tools and issue creation are allowed. merge_pull_request is NOT
# listed, so the agent cannot merge without a human changing this list.
ALLOWED_TOOLS = [
    "mcp__github__list_pull_requests",
    "mcp__github__get_pull_request",
    "mcp__github__get_pull_request_files",
    "mcp__github__list_issues",
    "mcp__github__create_issue",
]

SYSTEM_PROMPT = (
    "You are a GitHub assistant for one repository. Use the GitHub tools "
    "to answer. Never merge pull requests."
)

DEFAULT_TASK = (
    "List the open pull requests. Review the newest one, and if you find "
    "real problems open one issue describing them."
)


async def main(task: str) -> None:
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"github": GITHUB_SERVER},
        allowed_tools=ALLOWED_TOOLS,
        max_turns=15,
    )

    async for message in query(prompt=task, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[tool] {block.name} {block.input}")
                elif isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"\n[done] turns={message.num_turns} cost=${message.total_cost_usd}")


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or DEFAULT_TASK))
