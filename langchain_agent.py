import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")

# merge_pull_request is left out on purpose, so the agent cannot merge.
BLOCKED_TOOLS = {"merge_pull_request"}

SYSTEM_PROMPT = (
    "You are a GitHub assistant for one repository. Use the GitHub tools "
    "to answer. Never merge pull requests."
)

DEFAULT_TASK = "List the open pull requests and open issues."


def langfuse_config() -> dict:
    """Send traces to Langfuse when its keys are set in .env."""
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        print("Langfuse keys not set: tracing is off")
        return {}

    from langfuse.langchain import CallbackHandler

    return {"callbacks": [CallbackHandler()]}


def pick_model() -> str:
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic:claude-sonnet-5-5"
    if os.getenv("OPENAI_API_KEY"):
        return "openai:gpt-4o-mini"
    raise SystemExit("Add ANTHROPIC_API_KEY or OPENAI_API_KEY to .env")


async def load_github_tools():
    client = MultiServerMCPClient(
        {
            "github": {
                "transport": "stdio",
                "command": str(HERE / ".venv/bin/python"),
                "args": [str(HERE / "github_mcp.py")],
            }
        }
    )
    tools = await client.get_tools()
    return [tool for tool in tools if tool.name not in BLOCKED_TOOLS]


async def main(task: str) -> None:
    tools = await load_github_tools()
    print("Tools loaded:", [tool.name for tool in tools])

    agent = create_agent(pick_model(), tools, system_prompt=SYSTEM_PROMPT)
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": task}]},
        config=langfuse_config(),
    )

    for message in result["messages"]:
        for call in getattr(message, "tool_calls", None) or []:
            print(f"[tool] {call['name']} {call['args']}")
    print(result["messages"][-1].text)

    if os.getenv("LANGFUSE_PUBLIC_KEY"):
        from langfuse import get_client

        get_client().flush()


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or DEFAULT_TASK))
