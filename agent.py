
import json
import re
from openai import OpenAI

client = OpenAI()


# TOOL 1: Remove special characters
def clean_text(text: str) -> str:
    """Keep letters, numbers, and spaces."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    return cleaned


# TOOL 2: Count characters
def count_characters(text: str) -> int:
    """Count all characters, including spaces."""
    return len(text)


# Tell the AI model which tools are available
tools = [
    {
        "type": "function",
        "name": "clean_text",
        "description": (
            "Remove special characters from text, "
            "keeping letters, numbers, and spaces."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"}
            },
            "required": ["text"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "count_characters",
        "description": (
            "Count all characters in the supplied text, "
            "including spaces. Use the cleaned text when "
            "the user asks for its cleaned length."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"}
            },
            "required": ["text"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

# Map tool names to Python functions
available_functions = {
    "clean_text": clean_text,
    "count_characters": count_characters,
}


def run_agent(user_task: str):
    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=(
            "You are a helpful text-processing agent. "
            "Use tools when appropriate. If the user asks "
            "to clean text and count its length, call "
            "clean_text first, then count_characters using "
            "the exact cleaned result. Explain the result."
        ),
        input=user_task,
        tools=tools,
    )

    # Agent loop: execute tools and return results to the model
    for _ in range(10):
        tool_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        if not tool_calls:
            print("\nAgent:", response.output_text)
            return

        tool_outputs = []

        for call in tool_calls:
            function = available_functions.get(call.name)

            if function is None:
                result = f"Unknown tool: {call.name}"
            else:
                arguments = json.loads(call.arguments)
                result = function(**arguments)

                print(f"\nTool called: {call.name}")
                print("Arguments:", arguments)
                print("Result:", result)

            tool_outputs.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": str(result),
            })

        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=(
                "You are a helpful text-processing agent. "
                "Use the tool results to complete the user's "
                "request. For cleaning and counting, count "
                "the exact cleaned text returned by the tool."
            ),
            previous_response_id=response.id,
            input=tool_outputs,
            tools=tools,
        )

    print("Agent stopped: maximum tool-call rounds reached.")


if __name__ == "__main__":
    task = input("What would you like me to do? ")
    run_agent(task)
