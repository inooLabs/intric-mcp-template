# AGENTS.md

Rules for AI coding agents in this repo: an MCP server template for Intric. Read this before you add or change a tool.

## Commands

- Install: `pip install -r requirements-dev.txt`
- Test: `pytest`
- Run: `uvicorn server:app --port 8000` (needs a `.env`, see README)

## Layout

- `server.py`: server setup, authentication, registration of tools, resources and prompts.
- `tools.py`: tool functions. `divide_two_numbers` can fail, `convert_temperature` takes a fixed set of values, `define_temperature_unit` returns a citation, `get_usage_guide` explains the server.
- `tests/test_smoke.py`: when you replace the example tools, replace the tests that name them.
- `auth_examples.py`: a verifier that checks keys or tokens against your own API. Not used by default.
- `docs/`: how Intric behaves, one topic per folder. The rules below link to them.

## Rules

1. **Return `{"error": ...}` instead of raising.** A raised exception reaches the client as the framed text `Error calling tool '<name>': <exception message>`, not as an `{"error": ...}` you wrote. Wrap the upstream call and the code that processes its result. Annotate such a tool `-> dict[str, Any]`: with `-> float` the client rejects the error dict. Example: `divide_two_numbers`.
2. **Open `instructions=` with the domain, then point to the guide.** The first sentence says what this server covers, not only that it is an MCP server. Then "ALWAYS call get_usage_guide first". The guide says which tool to call for what and how they combine: update it when you add a tool. Example: `server.py`, `get_usage_guide`.
3. **Write each docstring for the model.** It is the one text you can count on the model seeing for that tool: `instructions=` is optional and not every client shows it. On a tool that can be misused, say what it does and the one mistake to avoid in the first two sentences, name parameters exactly, and list valid values verbatim. Example: `convert_temperature`.
4. **Use `Literal[...]` for a fixed set of values**, and list the values in the docstring. A wrong value is rejected by the schema before your code runs, with a message that lists the valid values. It is not returned as an error dict. If the values are configured in an external system and can change, do not hard-code them: add a tool that looks them up. Example: `convert_temperature`.
5. **Keep internal notes out of registered docstrings.** Commit hashes, dates, file paths and changelog notes ("used to return X") are part of the description the model reads for every registered tool. Put them in a comment, or in a private helper you do not register.
6. **Never block inside an `async def` tool.** A sync HTTP client or `time.sleep` makes concurrent calls wait for each other: two concurrent 1-second `time.sleep` calls took 2 seconds, against 1 second with `await asyncio.sleep`. Use `httpx.AsyncClient` and `await`. It is installed with `fastmcp`; add `httpx` to `requirements.txt` when you import it. Open the client inside the call (`async with httpx.AsyncClient() as client:`) so nothing stays open after the call returns.
7. **Keep authentication on.** Set `MCP_SERVER_JWT_SECRET`, `MCP_SERVER_JWT_ISSUER` and `MCP_SERVER_JWT_AUDIENCE` together: an empty issuer or audience silently turns that check off. Never commit `.env`. `/health` is public, so return nothing sensitive from it. Example: the verifier and `/health` in `server.py`.
8. **Set permissions per tool.** `meta={"requires_permission": False}` for tools that only read or compute. `True` for a tool that changes something in another system, so Intric asks the user first. Example: the `meta=` registrations in `server.py` (all read-only, so `False`).
9. **Import `Context` from `fastmcp`.** If a tool needs the request context, use `from fastmcp import Context`. The `Context` from `mcp.server.fastmcp` shows up as a required argument in the tool's input schema.
10. **Intric keeps its own copy of the tool list.** Adding or removing a tool, or changing a tool's name, parameters or docstring, reaches Intric only after someone clicks **Refresh capabilities** on the server there. After such a change, tell the user to refresh. Details: [`docs/intric-contract/README.md`](docs/intric-contract/README.md).
11. **Return one dict, and cite with `knowledge_sources`.** Intric reads citations only from a dict result, drops an entry without a `title`, and hides the entry's `text` from the model, so put the facts in the rest of the dict. Keep results small and say when a list is capped (`total`, `returned`, `truncated`). Of a result that is too large, the model first sees only the top. Add each tool that cites to `CITING_TOOLS` in the tests. Example: `define_temperature_unit`. Details: [`docs/tool-output/README.md`](docs/tool-output/README.md).
12. **Choose the authentication setup on purpose.** The default is a JWT you mint. If each customer brings its own API key for your service, pass `UpstreamTokenVerifier` from `auth_examples.py` as `auth=`. For OAuth, wrap a verifier in `RemoteAuthProvider`: `UpstreamTokenVerifier` for opaque access tokens, the JWKS `JWTVerifier` in `server.py` for JWT access tokens. A verifier must return `None` on every failure and never raise: a raise reaches the client as HTTP 500. Details: [`docs/auth/README.md`](docs/auth/README.md).
