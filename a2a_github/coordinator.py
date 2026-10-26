import asyncio
import sys

import httpx
from a2a.client import ClientConfig, create_client
from a2a.helpers import get_stream_response_text, new_text_message
from a2a.types import Role, SendMessageRequest

REVIEWER_URL = "http://localhost:9001"
ISSUE_URL = "http://localhost:9002"


async def ask_agent(url: str, text: str) -> str:
    """Discover an agent from its card, send it a message, return its text."""
    # The agent calls an LLM and GitHub, so allow far more than the default timeout.
    http = httpx.AsyncClient(timeout=180)
    client = await create_client(url, ClientConfig(httpx_client=http))
    print(f"Connected to: {client._card.name}")

    request = SendMessageRequest(message=new_text_message(text, role=Role.ROLE_USER))
    answer = ""
    async for response in client.send_message(request):
        answer = get_stream_response_text(response) or answer
    return answer


async def main(pr_number: str, open_issue: bool) -> None:
    review = await ask_agent(REVIEWER_URL, f"Review pull request #{pr_number}")
    print("\n--- Review ---\n" + review)

    mode = "" if open_issue else "DRY RUN. "
    issue = await ask_agent(
        ISSUE_URL,
        f"{mode}Open one issue for the problems in this review. "
        f"If there are none, say so.\n\n{review}",
    )
    print("\n--- Issue agent ---\n" + issue)


if __name__ == "__main__":
    pr = sys.argv[1] if len(sys.argv) > 1 else "1"
    asyncio.run(main(pr, open_issue="--open-issue" in sys.argv))
