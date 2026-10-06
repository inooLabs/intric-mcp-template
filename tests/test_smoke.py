"""Smoke tests: the server enforces authentication and its tools keep the contract. Run with `pytest`."""

import asyncio
import datetime
import os

# Set these before importing `server`: load_dotenv() does not override variables that are already set.
SECRET = "test-secret-" + "x" * 32
ISSUER = "test-issuer"
AUDIENCE = "test-audience"
os.environ["MCP_SERVER_JWT_SECRET"] = SECRET
os.environ["MCP_SERVER_JWT_ISSUER"] = ISSUER
os.environ["MCP_SERVER_JWT_AUDIENCE"] = AUDIENCE

import jwt
import pytest
from fastmcp import Client
from starlette.testclient import TestClient

import server

HEADERS = {"Accept": "application/json, text/event-stream"}
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "pytest", "version": "0"},
    },
}


def make_token(secret=SECRET, issuer=ISSUER, audience=AUDIENCE):
    now = datetime.datetime.now(datetime.timezone.utc)
    claims = {"sub": "test-user", "iat": now, "exp": now + datetime.timedelta(hours=1)}
    if issuer:
        claims["iss"] = issuer
    if audience:
        claims["aud"] = audience
    return jwt.encode(claims, secret, algorithm="HS256")


@pytest.fixture(scope="module")
def client():
    # The context manager runs the app lifespan, which the MCP endpoint needs.
    with TestClient(server.app) as c:
        yield c


def initialize(client, token=None):
    headers = dict(HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.post("/mcp", json=INITIALIZE, headers=headers)


def test_health_is_open(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.text == "OK"


def test_missing_token_is_rejected(client):
    assert initialize(client).status_code == 401


@pytest.mark.parametrize(
    "bad_token",
    [
        make_token(secret="wrong-secret-" + "y" * 32),
        make_token(audience="other-audience"),
        make_token(issuer="other-issuer"),
    ],
    ids=["wrong-secret", "wrong-audience", "wrong-issuer"],
)
def test_bad_token_is_rejected(client, bad_token):
    assert initialize(client, bad_token).status_code == 401


def test_valid_token_initializes(client):
    r = initialize(client, make_token())
    assert r.status_code == 200
    assert "serverInfo" in r.text


# Tool contract tests: they talk to the server in memory, like a client would.
# The tests that name divide_two_numbers and convert_temperature pin the example tools:
# when you replace the examples with your own tools, replace those tests too.


def call_tool(name, arguments):
    async def run():
        async with Client(server.mcp) as c:
            return await c.call_tool(name, arguments, raise_on_error=False)

    return asyncio.run(run())


def list_tools():
    async def run():
        async with Client(server.mcp) as c:
            return await c.list_tools()

    return {t.name: t for t in asyncio.run(run())}


def test_literal_values_are_listed_in_the_description():
    checked = 0
    for tool in list_tools().values():
        for prop in tool.inputSchema.get("properties", {}).values():
            for value in prop.get("enum", []):
                assert f'"{value}"' in tool.description, f"{tool.name}: {value!r} is not in the docstring"
                checked += 1
    assert checked > 0  # a check that finds nothing to check must not pass


def test_usage_guide_names_every_tool():
    tools = list_tools()
    guide = call_tool("get_usage_guide", {}).data
    others = [name for name in tools if name != "get_usage_guide"]
    assert others
    for name in others:
        assert name in guide, f"get_usage_guide does not mention {name}"


@pytest.mark.parametrize(
    "name, arguments",
    [
        ("divide_two_numbers", {"a": 1, "b": 0}),
        ("convert_temperature", {"value": -300, "from_unit": "celsius", "to_unit": "fahrenheit"}),
    ],
)
def test_failures_are_error_dicts_not_tool_errors(name, arguments):
    result = call_tool(name, arguments)
    assert result.is_error is False
    assert isinstance(result.data, dict)
    assert set(result.data) == {"error"}


def test_invalid_literal_is_rejected_before_the_tool_runs():
    result = call_tool("convert_temperature", {"value": 1, "from_unit": "kelvin", "to_unit": "celsius"})
    assert result.is_error is True
    # Only the schema check says "validation error" and lists the valid values.
    text = result.content[0].text
    assert "validation error" in text
    assert "celsius" in text
    assert "fahrenheit" in text


def test_tools_return_results():
    assert call_tool("divide_two_numbers", {"a": 6, "b": 3}).data == {"result": 2.0}
    boiling = call_tool("convert_temperature", {"value": 100, "from_unit": "celsius", "to_unit": "fahrenheit"})
    assert boiling.data == {"value": 212.0, "unit": "fahrenheit"}
