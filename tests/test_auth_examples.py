"""UpstreamTokenVerifier accepts a key only when your API does, and never raises (a raise is HTTP 500, not 401)."""

import asyncio

import httpx
import pytest

import auth_examples
from auth_examples import UpstreamTokenVerifier

IDENTITY_URL = "https://api.example.com/v1/me"


def verify(monkeypatch, handler, token="key-123"):
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        auth_examples.httpx, "AsyncClient", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw)
    )
    return asyncio.run(UpstreamTokenVerifier(IDENTITY_URL).verify_token(token))


def test_a_key_your_api_accepts_is_accepted(monkeypatch):
    def handler(request):
        assert request.headers["Authorization"] == "Bearer key-123"
        return httpx.Response(200, json={"id": 42})

    access_token = verify(monkeypatch, handler)
    assert access_token.client_id == "42"
    assert access_token.token == "key-123"


@pytest.mark.parametrize(
    "response",
    [httpx.Response(401), httpx.Response(503), httpx.Response(200, json={"name": "no id"})],
    ids=["rejected", "api-down", "no-account-id"],
)
def test_anything_else_is_rejected(monkeypatch, response):
    assert verify(monkeypatch, lambda request: response) is None


def test_a_network_error_is_rejected_not_raised(monkeypatch):
    def handler(request):
        raise httpx.ConnectTimeout("timed out")

    assert verify(monkeypatch, handler) is None
