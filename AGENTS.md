# AGENTS.md

Rules for AI coding agents in this repo: an MCP server template for Intric. Read this before you add or change a tool.

## Commands

- Install: `pip install -r requirements-dev.txt`
- Test: `pytest`
- Run: `uvicorn server:app --port 8000` (needs a `.env`, see README)

## Layout

- `server.py`: server setup, authentication, registration of tools, resources and prompts.
- `tools.py`: tool functions. `divide_two_numbers` can fail, `convert_temperature` takes a fixed set of values, `get_usage_guide` explains the server.
- `tests/test_smoke.py`: when you replace the example tools, replace the tests that name them.

## Rules

1. **Return `{"error": ...}` instead of raising.** A raised exception reaches the model as the framed text `Error calling tool '<name>': <exception message>`, not as an `{"error": ...}` you wrote. Wrap the upstream call and the code that processes its result. Annotate such a tool `-> dict[str, Any]`: with `-> float` the client rejects the error dict. Example: `divide_two_numbers`.
2. **Open `instructions=` with the domain, then point to the guide.** The first sentence says what this server covers, not only that it is an MCP server. Then "ALWAYS call get_usage_guide first". The guide says which tool to call for what and how they combine: update it when you add a tool. Example: `server.py`, `get_usage_guide`.
3. **Write each docstring for the model.** It is the one text you can count on the model seeing for that tool: `instructions=` is optional and not every client shows it. On a tool that can be misused, say what it does and the one mistake to avoid in the first two sentences, name parameters exactly, and list valid values verbatim. Example: `convert_temperature`.
4. **Use `Literal[...]` for a fixed set of values**, and list the values in the docstring. A wrong value is rejected by the schema before your code runs, with a message that lists the valid values. It is not returned as an error dict. If the values are configured in an external system and can change, do not hard-code them: add a tool that looks them up. Example: `convert_temperature`.
5. **Keep internal notes out of registered docstrings.** Commit hashes, dates, file paths and changelog notes ("used to return X") are part of the description the model reads for every registered tool. Put them in a comment, or in a private helper you do not register.
6. **Never block inside an `async def` tool.** A sync HTTP client or `time.sleep` makes concurrent calls wait for each other: two concurrent 1-second `time.sleep` calls took 2 seconds, against 1 second with `await asyncio.sleep`. Use `httpx.AsyncClient` (installed with `fastmcp`) and `await`.
7. **Keep authentication on.** Set `MCP_SERVER_JWT_SECRET`, `MCP_SERVER_JWT_ISSUER` and `MCP_SERVER_JWT_AUDIENCE` together: an empty issuer or audience silently turns that check off. Never commit `.env`. `/health` is public, so return nothing sensitive from it. Example: the verifier and `/health` in `server.py`.
8. **Set permissions per tool.** `meta={"requires_permission": False}` for tools that only read or compute. `True` for a tool that changes something in another system, so Intric asks the user first. Example: the `meta=` registrations in `server.py` (all read-only, so `False`).
9. **Import `Context` from `fastmcp`.** If a tool needs the request context, use `from fastmcp import Context`. The `Context` from `mcp.server.fastmcp` shows up as a required argument in the tool's input schema.
