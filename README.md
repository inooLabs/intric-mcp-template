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

## Running the Server

Start the MCP server with uvicorn:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000/mcp`.

## Connecting to Intric

Add your exposed server URL in Intric's MCP connections settings. Intric will automatically discover all available tools and resources.

Tip: Use a service like ngrok to expose an HTTPS URL bound to a local port, then add that URL (ending with `/mcp`) to Intric.

## Building Your Own MCP Server

### Adding Tools

```python
@mcp.tool
def your_function_name(param1: str, param2: int) -> str:
    """Description of what this tool does."""
    return f"Result: {param1} - {param2}"
```

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
├── server.py         # Main server file with examples
├── tools.py          # Example tool implementations
├── resources.py      # Example resource implementations
├── requirements.txt  # Python dependencies
```
