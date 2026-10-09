# Intric MCP Template Server

A template for building Model Context Protocol (MCP) servers that connect seamlessly with Intric's built-in MCP client. This template demonstrates how to create custom tools and resources that extend your AI assistant's capabilities.

## Features

- **Tools**: Functions the AI can call to perform actions
- **Resources**: Static data the AI can access
- **Resource Templates**: Dynamic resources based on parameters
- **Prompts**: Reusable prompt templates for common interactions
- **Server Metadata**: Custom icons, instructions, and versioning displayed in Intric
- **Authentication**: JWT-based API key verification
- **IP Allowlisting**: Restrict server access to specific IP addresses
- **Permissions**: Control whether tools/resources require user confirmation

## Quick start

Requires Python 3.10 or newer (tested on 3.12 on macOS). The commands are for bash or zsh. On Windows, use `python` instead of `python3`, `venv\Scripts\activate` instead of `source venv/bin/activate`, and `copy` instead of `cp`.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and set `MCP_SERVER_JWT_SECRET`. Generate a value with `openssl rand -hex 32` (or `python -c "import secrets; print(secrets.token_hex(32))"`). The server will not start without it.

Generate a token and paste it into the **Api Key** field when you add the server in Intric:

```bash
python generate_token.py
```

Then start the server:

```bash
uvicorn server:app --port 8000
```

The server is now available at `http://localhost:8000/mcp`.

Run the tests with `pip install -r requirements-dev.txt` and then `pytest`.

A token is tied to the secret, issuer and audience in `.env`. If you change any of them, generate a new token and update the Api Key in Intric.

`/health` is public (Intric uses it to check that the server is up). Keep anything sensitive out of it.

## Building with an AI coding agent

`AGENTS.md` has the rules an AI coding agent should follow when it adds or changes a tool. If your agent does not read it automatically, tell it to read `AGENTS.md` first.

## Connecting to Intric

Add your exposed server URL (ending with `/mcp`, no trailing slash) in Intric's MCP connections settings, with the token from the quick start as the Api Key. Intric reads your tools when you add the server and keeps that copy: after you change a tool, click **Refresh capabilities** on the server in Intric. A tenant admin also has to turn the server on and give it a security classification before assistants can use it. Details: [`docs/intric-contract/README.md`](docs/intric-contract/README.md).

Tip: Use a service like ngrok to expose an HTTPS URL bound to a local port, then add that URL (ending with `/mcp`) to Intric.

## Building Your Own MCP Server

### Adding Tools

```python
from typing import Any

@mcp.tool
def your_function_name(param1: str, param2: int) -> dict[str, Any]:
    """
    What this tool does, in one sentence. Name the one mistake to avoid.

    args:
        param1: What it is
        param2: What it is. Must not be negative.

    returns:
        {"result": ...} on success, {"error": <message>} on failure
    """
    if param2 < 0:
        return {"error": "param2 must not be negative."}
    return {"result": f"{param1} - {param2}"}
```

The docstring is what the model reads to decide when and how to call the tool, so write it for the model.

- Return `{"error": ...}` instead of raising. A raised exception reaches the client as a tool error with the text `Error calling tool '<name>': <exception message>`. Annotate tools that can fail `-> dict[str, Any]`: a `-> float` tool that returns an error dict fails the client's output validation.
- When a parameter takes one of a few values, type it as `Literal[...]` and list the values in the docstring (see `convert_temperature` in `tools.py`).
- Keep `get_usage_guide` up to date. `instructions=` tells the model to call it first.
- Return a dict, and add `knowledge_sources` when the answer comes from a document or page the user can open. What Intric does with the result: [`docs/tool-output/README.md`](docs/tool-output/README.md).

### Adding Resources

```python
@mcp.resource("resource://your_resource_name")
def get_your_data() -> str:
    """Description of what data this resource provides."""
    return "Your data here"
```

### Adding Resource Templates

```python
@mcp.resource("data://{category}/{id}")
def get_dynamic_data(category: str, id: str) -> dict:
    """Provide data based on category and id."""
    return {"category": category, "id": id, "data": "..."}
```

### Adding Prompts

Prompts are reusable templates that help standardize common interactions:

```python
@mcp.prompt()
def code_review() -> str:
    """Review code for best practices."""
    return """Please review the following code for:
- Code quality and best practices
- Potential bugs or issues
- Security concerns"""

# Prompts can accept arguments:
@mcp.prompt()
def summarize_text(style: str = "brief") -> str:
    """Summarize text in a specified style."""
    if style == "bullets":
        return "Summarize as a bulleted list of key points."
    return "Provide a brief summary."
```

### Permissions

Control whether Intric asks for user confirmation before executing a tool or accessing a resource:

```python
# Tool that executes without user confirmation
@mcp.tool(meta={"requires_permission": False})
def auto_execute_tool() -> str:
    """This tool runs automatically without asking the user."""
    return "Done"

# Resource that requires user confirmation (resources don't require permission by default)
@mcp.resource(
    uri="resource://sensitive_data",
    meta={"requires_permission": True},
)
def get_sensitive_data() -> str:
    """User must confirm before accessing this resource."""
    return "Sensitive information"
```

## Project Structure

```
intric-mcp-template/
├── AGENTS.md            # Rules for AI coding agents
├── server.py            # Main server file with examples
├── tools.py             # Example tool implementations
├── resources.py         # Example resource implementations
├── generate_token.py    # Prints a token for the Api Key field in Intric
├── .env.example         # Copy to .env and set the secret
├── requirements.txt     # Python dependencies
├── requirements-dev.txt # Adds pytest
├── pytest.ini           # Test configuration
├── tests/               # Smoke tests
└── docs/                # How Intric behaves, one topic per folder
```
