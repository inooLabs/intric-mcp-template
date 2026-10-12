# Authentication with Intric

Intric connects to a server in one of two ways, chosen when the server is added in Intric:

- **Api Key:** one string per server entry. Intric sends it on every request as `Authorization: Bearer <key>`. Each tenant adds the server separately, with its own key, and every user in that tenant shares it.
- **OAuth2:** each user connects their own account. Intric runs the login, stores each user's tokens and refreshes them. It sends the user's access token as `Authorization: Bearer <token>`.

Pick one of the three setups below.

| Setup | Use it when | Intric auth |
|---|---|---|
| A. A JWT you mint (the default in `server.py`) | You run the server for one customer, or the server calls your API with one key of its own | Api Key |
| B. Your customers' own API keys | One server for many customers, and each customer already has an API key for your service | Api Key |
| C. Your OAuth server | Each user should act as themselves in your service, with their own permissions | OAuth2 |

## A. A JWT you mint

This is what the template does. `generate_token.py` mints a token from the secret, issuer and audience in `.env`, and you paste it into the Api Key field. The key the server uses to call your API stays in the server's environment and never passes through Intric.

A token stops working when you change the secret, issuer or audience. Mint a new one and update the Api Key in the same step: [the refresh then looks fine but keeps the old tool list](../intric-contract/README.md#intric-keeps-its-own-copy-of-your-tool-list).

## B. Your customers' own API keys

The tenant admin pastes the customer's API key for your service into the Api Key field. The server checks that key against your API on each request, then uses it for the tool's calls. Nothing is minted, and the server stores no keys.

```python
from auth_examples import UpstreamTokenVerifier

mcp = FastMCP(
    ...,
    auth=UpstreamTokenVerifier("https://api.example.com/v1/me"),  # an endpoint that returns the key's account
)
```

In a tool, `upstream_token()` returns the caller's key, and `get_access_token().client_id` (from `fastmcp.server.dependencies`) the account id from that endpoint. `ctx.client_id` is `None` here. Do not use the key itself as an id, in logs or anywhere else.

Use the verifier directly, as above, not inside `RemoteAuthProvider`. That provider advertises an OAuth server, and an admin who picks OAuth2 would then be sent to it.

## C. Your OAuth server

Intric is the OAuth client. Your authorization server issues the tokens, and the MCP server only checks them. Wrap the verifier in `RemoteAuthProvider`, so the server tells Intric where to log users in:

```python
from fastmcp.server.auth import RemoteAuthProvider
from auth_examples import UpstreamTokenVerifier

mcp = FastMCP(
    ...,
    auth=RemoteAuthProvider(
        token_verifier=UpstreamTokenVerifier("https://api.example.com/v1/me"),
        authorization_servers=["https://auth.example.com"],  # your authorization server's issuer, exactly
        base_url="https://mcp.example.com",  # the public origin, plus any path prefix your proxy adds
    ),
)
```

If your access tokens are JWTs, verify them locally with the JWKS `JWTVerifier` shown commented out in `server.py`, and pass that as `token_verifier` instead.

### How Intric finds your OAuth server

When the admin adds the server with OAuth2 and leaves the OAuth URLs empty, Intric discovers them:

1. It calls the server URL. The `401` from `RemoteAuthProvider` points to `/.well-known/oauth-protected-resource/mcp` under `base_url`. Your proxy must route that path to the server, not only `/mcp`.
2. From that document it takes the first entry of `authorization_servers` and fetches that server's `oauth-authorization-server` or `openid-configuration` metadata. The `issuer` in the metadata must equal the entry exactly. Only a trailing slash may differ.
3. The metadata must list `S256` in `code_challenge_methods_supported`. Intric always uses PKCE, and discovery fails without it.
4. Scopes come from the `scope` in the `401`, otherwise from `scopes_supported` in the server's own document from step 1, which you set with `RemoteAuthProvider(..., scopes_supported=[...])`. Your authorization server's list is not used. With neither, Intric requests no scope, which some authorization servers reject.

Every URL involved must be public `https`. Discovery does not work against `localhost`. If your authorization server publishes no metadata, the admin enters the URLs by hand instead: the authorization and token URLs are required, the revocation URL and the scopes are optional.

### The OAuth client

- If your authorization server advertises `client_id_metadata_document_supported`, Intric uses its own client metadata URL as the client id. Nothing needs to be registered.
- Otherwise, register an OAuth client in your system and give the client id and secret to the tenant admin, who enters them in Intric. Its redirect URI is `<Intric base URL>/mcp-servers/oauth/callback/`, trailing slash included. The base URL differs between Intric instances, so register the exact URL for each instance you support.
- Intric sends `resource=<server URL>` on the authorize, token and refresh requests.
- Changing the server URL or the auth type in Intric disconnects every user, and each user has to connect again.

## For B and C: the verifier runs on every request

`verify_token` runs for every MCP request, including tool calls that run in parallel, and FastMCP does not cache the result. Keep the identity endpoint fast. You can cache successful checks for a short time, but a cached key stays accepted for that long after it is revoked. Never cache failures.

`UpstreamTokenVerifier` returns `None` for every failure: a rejected key, a `429` or `5xx` from your API, a timeout. The client then gets `401`. If the verifier raised instead, the client would get `500`. A `401` caused by your API being down looks to Intric like an expired token: with OAuth2 it refreshes the token and tries once more, with an Api Key it does not retry. Either way the user sees a failed call. The verifier logs why a check failed, without the key, so you can tell a bad key from an outage.

If your API expects the key in another header or as a query parameter, send it that way in `verify_token` and in your tool calls. Intric always delivers it as a bearer.
