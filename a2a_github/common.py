import os
from pathlib import Path

import uvicorn
from a2a.helpers import new_task_from_user_message, new_text_artifact
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    TaskState,
)
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from starlette.applications import Starlette

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

MODEL = "openai:gpt-4o-mini"


async def run_github_agent(task: str, tool_names: set[str], system_prompt: str) -> str:
    """Run a LangChain agent that may only use the listed GitHub MCP tools."""
    client = MultiServerMCPClient(
        {
            "github": {
                "transport": "stdio",
                "command": str(ROOT / ".venv/bin/python"),
                "args": [str(ROOT / "github_mcp.py")],
            }
        }
    )
    tools = [t for t in await client.get_tools() if t.name in tool_names]
    agent = create_agent(MODEL, tools, system_prompt=system_prompt)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": task}]})
    return result["messages"][-1].text


class GitHubAgentExecutor(AgentExecutor):
    """Turns an incoming A2A message into one run of the GitHub agent."""

    def __init__(self, tool_names: set[str], system_prompt: str):
        self.tool_names = tool_names
        self.system_prompt = system_prompt

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # A2A tasks start as a Task object, then report status updates.
        if not context.current_task:
            await event_queue.enqueue_event(new_task_from_user_message(context.message))

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.start_work()
        try:
            answer = await run_github_agent(
                context.get_user_input(), self.tool_names, self.system_prompt
            )
        except Exception as error:
            await updater.failed(updater.new_agent_message([_text_part(str(error))]))
            return

        artifact = new_text_artifact("result", answer)
        await updater.add_artifact(list(artifact.parts), name="result")
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()


def _text_part(text: str):
    from a2a.helpers import new_text_part

    return new_text_part(text)


def build_card(name: str, description: str, port: int, skill: AgentSkill) -> AgentCard:
    return AgentCard(
        name=name,
        description=description,
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(
                url=f"http://localhost:{port}/",
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[skill],
    )


def serve(card: AgentCard, executor: AgentExecutor, port: int) -> None:
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, "/")
    uvicorn.run(Starlette(routes=routes), host="127.0.0.1", port=port)
