"""Authentication for a server that checks keys or tokens against your own API.

Not used by default: server.py uses a JWT you mint yourself. See docs/auth/README.md for when to use this
and how to wire it.
"""

import logging

import httpx
from fastmcp.server.auth import AccessToken, TokenVerifier
from fastmcp.server.dependencies import get_access_token

logger = logging.getLogger(__name__)


class UpstreamTokenVerifier(TokenVerifier):
    """Accepts a bearer only if your API accepts it, by calling an endpoint that returns the caller's account."""

    def __init__(self, identity_url: str, id_field: str = "id", timeout: float = 10.0):
        super().__init__()
        self.identity_url = identity_url  # e.g. https://api.example.com/v1/me
        self.id_field = id_field  # the field in that response that identifies the account
        self.timeout = timeout

    async def verify_token(self, token: str) -> AccessToken | None:
        # Return None for every failure. A raised exception here reaches the client as HTTP 500, not 401.
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # If your API expects the key in another header or a query parameter, send it that way here
                # and in your tool calls. Intric always delivers it as a bearer.
                response = await client.get(self.identity_url, headers={"Authorization": f"Bearer {token}"})
            if response.status_code != 200:
                # Log the status, never the key: 401 is a bad key, 429 or 5xx is your API.
                logger.warning("Identity check returned %s", response.status_code)
                return None
            account_id = response.json().get(self.id_field)
        except Exception as exc:
            logger.warning("Identity check failed: %s", type(exc).__name__)
            return None
        if account_id in (None, ""):
            logger.warning("Identity response has no %r field", self.id_field)
            return None
        return AccessToken(token=token, client_id=str(account_id), scopes=[])


def upstream_token() -> str | None:
    """The caller's key or token, for your tool's calls to your API. None outside an authenticated request."""
    access_token = get_access_token()
    return access_token.token if access_token is not None else None
