from datetime import datetime
from mcp.server.fastmcp import FastMCP
from pathlib import Path

import re
mcp = FastMCP("Python AI Agent Tools")

PROJECT_ROOT = Path("/Users/4star/python-learn/mcp-tool").resolve()

# Directories that should not be searched or exposed.
IGNORED_DIRS = {
    ".git", ".venv", "venv", "__pycache__",
    "node_modules", ".idea", ".pytest_cache",
}


def safe_project_path(relative_path: str) -> Path:
    """Resolve a path and ensure it remains inside the project."""
    path = (PROJECT_ROOT / relative_path).resolve()

    if not path.is_relative_to(PROJECT_ROOT):
        raise ValueError("Path must remain inside the project.")

    return path


@mcp.tool()
def search_project_files(query: str) -> dict:
    """Find project files whose names contain the query."""
    query = query.strip().lower()

    if not query:
        return {"success": False, "error": "Query cannot be empty."}

    matches = []

    for path in PROJECT_ROOT.rglob("*"):
        # Exclude generated and hidden directories.
        if any(part.startswith(".") or part in IGNORED_DIRS
               for part in path.relative_to(PROJECT_ROOT).parts):
            continue

        if path.is_file() and query in path.name.lower():
            matches.append(str(path.relative_to(PROJECT_ROOT)))

            if len(matches) >= 100:
                break

    return {
        "success": True,
        "query": query,
        "files": matches,
        "count": len(matches),
    }


@mcp.tool()
def read_project_file(relative_path: str) -> dict:
    """Read a UTF-8 text file inside the project, up to 20,000 characters."""
    try:
        path = safe_project_path(relative_path)

        if not path.is_file():
            return {"success": False, "error": "File not found."}

        if any(
            part.startswith(".") or part in IGNORED_DIRS
            for part in path.relative_to(PROJECT_ROOT).parts
        ):
            return {"success": False, "error": "Access to this path is restricted."}

        if path.stat().st_size > 1_000_000:
            return {"success": False, "error": "File exceeds the 1 MB limit."}

        content = path.read_text(encoding="utf-8")
        return {
            "success": True,
            "path": str(path.relative_to(PROJECT_ROOT)),
            "content": content[:20_000],
            "truncated": len(content) > 20_000,
        }

    except (ValueError, OSError, UnicodeDecodeError) as exc:
        return {"success": False, "error": str(exc)}


@mcp.tool()
def list_project_tests() -> dict:
    """Find common Python test files without executing them."""
    tests = []

    for path in PROJECT_ROOT.rglob("*.py"):
        relative = path.relative_to(PROJECT_ROOT)

        if any(
            part.startswith(".") or part in IGNORED_DIRS
            for part in relative.parts
        ):
            continue

        if (
            path.name.startswith("test_")
            or path.name.endswith("_test.py")
            or "tests" in relative.parts
        ):
            tests.append(str(relative))

            if len(tests) >= 200:
                break

    return {"success": True, "tests": tests, "count": len(tests)}


# Demo task storage: resets when the server restarts.
tasks = []
next_task_id = 1


@mcp.tool()
def add_number(a: float,b: float) -> dict:
    """Add two numbers and return the calculation."""

    return{
        "a" : a,
        "b" : b,
        "result" : a+b
    }

@mcp.tool()
def get_current_time() -> dict:
    """Get the current date and time on the Mac running this server."""
    return {
        "current_time": datetime.now().astimezone().isoformat(),
        "timezone": str(datetime.now().astimezone().tzinfo),
    }

@mcp.tool()
def show_name(name:str) -> dict:
    """Refine Name with remove any special charafter"""

    clean_text = re.sub(r'[^a-zA-Z0-9]', '', name)

    return {
        "pure name" : clean_text
    }



@mcp.tool()
def add_task(title:str) -> dict:
    global next_task_id
    title=title.strip()
    if not title:
        return {"success" : False,"error": "Task Title cannot be empty"}

    task={
        "id":next_task_id,
        "title" : title,
        "completed" : False
    } 

    tasks.append(task)
    next_task_id+=1

    return {"sucess" : True,"task" : task}

@mcp.tool()
def show_tasks()->dict:
    """List all tasks current stored in MCP server"""
    return {"tasks" : tasks,"count" : len(tasks)}
if __name__ == "__main__":
    mcp.run()