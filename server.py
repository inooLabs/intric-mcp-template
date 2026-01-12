import os

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier
from mcp.server.fastmcp import Icon
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

load_dotenv()

from resources import get_past_weather, tell_a_joke
from tools import divide_two_numbers

####### API KEY #######

# Option 1: HMAC symmetric key verification
verifier = JWTVerifier(
    public_key=os.getenv("MCP_SERVER_JWT_SECRET"),  # Shared secret (min 32 chars)
    issuer=os.getenv("MCP_SERVER_JWT_ISSUER", ""),
    audience=os.getenv("MCP_SERVER_JWT_AUDIENCE", ""),
    algorithm="HS256",
)

# Option 2: JWKS endpoint (for external auth providers like Auth0, Keycloak, etc.)
# verifier = JWTVerifier(
#     jwks_uri="https://your-auth-provider.com/.well-known/jwks.json",
#     issuer="https://your-auth-provider.com/",
#     audience="your-mcp-server",
#     algorithm="RS256",
# )


####### CUSTOM MIDDLEWARE #######


# IP Allowlist Middleware restricts server access to specific IP addresses.
# If your server is behind a reverse proxy (e.g., nginx, Cloudflare),
# you may need to check headers like X-Forwarded-For instead of request.client.host
class IPAllowlistMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_ips: list[str]):
        super().__init__(app)
        self.allowed_ips = set(allowed_ips)
        self.allow_all = "*" in self.allowed_ips

    async def dispatch(self, request, call_next):
        if self.allow_all:
            return await call_next(request)

        client_ip = request.client.host if request.client else None

        if client_ip not in self.allowed_ips:
            return JSONResponse(
                status_code=403,
                content={"error": "Forbidden", "your_ip": client_ip},
            )
        return await call_next(request)


ALLOWED_IPS = ["*"]  # For development purposes, allow all IPs

middleware = [Middleware(IPAllowlistMiddleware, allowed_ips=ALLOWED_IPS)]


####### SERVER METADATA #######


# FastMCP metadata is used to describe the server and its capabilities.
# The Intric client will use this metadata to display the server in the Intric UI.
icon = Icon(
    src="https://portal.intric.ai/intric_pwa_logo.png",
)

INSTRUCTION_STRING = "This is a template server for the Intric MCP client. It is used to demonstrate the capabilities of the Intric MCP client."
VERSION = "1.0.0"
WEBSITE_URL = "https://www.intric.ai"


####### SERVER CONFIGURATION #######


# The FastMCP server class is the main object that represents the server.
# The most simple way to create a server is to use the FastMCP class and pass the name of the server.
# Additional metadata (from the above variables) can be passed to the FastMCP class.
# The auth parameter is used to set authentication for the server.
mcp = FastMCP(
    name="Intric MCP Template Server",
    instructions=INSTRUCTION_STRING,
    version=VERSION,
    website_url=WEBSITE_URL,
    icons=[icon],
    auth=verifier,
)


####### TOOLS #######


# If you are working with a single module, you can use the @mcp.tool decorator.
# In this example, FastMCP will automatically use the function name (add_two_numbers) as the tool name.
# The provided docstring will be used as the tool description.
# An input schema will be generated from the function parameters as well as handle parameter validation and error reporting.
# The description along with the input schema will be used by the Intric client to represent the tool for the LLM.
@mcp.tool
def add_two_numbers(a: int, b: int) -> int:
    """
    Add two numbers together.

    args:
        a: The first number
        b: The second number

    returns:
        The sum of the two numbers
    """
    return a + b


# When using the @mcp.tool decorator, you can use decorator arguments to override the ones FastMCP infer (as the example above):
@mcp.tool(
    name="add_two_numbers_v2",
    description="Add two numbers together.",
)
def addition_implementation(a: int, b: int) -> int:
    """
    Internal function description which will be ignored.
    """
    return a + b


# Permissions:
# In its standard configuration, Intric will ask the user for permission to execute a tool.
# However, you can configure tools to be executed without user permission by adding "requires_permission" in the meta field of the tool decorator.
@mcp.tool(
    meta={"requires_permission": False},
)
def tool_without_permission() -> str:
    """This tool will be executed without user permission."""
    return "Hello, from Intric MCP Template Server! (without permission)"


# Import tools from other modules:
mcp.tool()(divide_two_numbers)


####### RESOURCES #######


# Resources provide static or computed data that can be accessed by clients.
@mcp.resource("resource://hello_world")
def get_hello_world() -> str:
    """Provides a greeting message."""
    return "Hello, from Intric MCP Template Server!"


# Override URI, name, and description with decorator arguments:
@mcp.resource(
    uri="resource://hello_world_v2",
    name="Greetings Resource",
    description="Provides a message",
)
def get_hello_world_v2() -> str:
    """
    Internal function description which will be ignored.
    """
    return "Hello, from Intric MCP Template Server! (v2)"


# Permissions:
# In its standard configuration, Intric will NOT ask the user for permission to access a resource.
# However, you can configure resources to be executed with user permission by adding "requires_permission" in the meta field of the resource decorator.
# The same goes for resource templates.
@mcp.resource(
    uri="resource://hello_world_v2_with_permission",
    name="Greetings Resource with Permission",
    description="Provides a message with permission",
    meta={"requires_permission": True},
)
def get_hello_world_v2_with_permission() -> str:
    """
    This resource will be executed with user permission.
    """
    return "Hello, from Intric MCP Template Server! (v2 with permission)"


# Import resources from other modules:
mcp.resource("resource://tell_a_joke")(tell_a_joke)


####### RESOURCE TEMPLATES #######


# Resource templates allow dynamic content based on URI parameters.
@mcp.resource("weather://{city}/current")
def get_current_weather(city: str) -> dict:
    """Provide the current weather for a given city."""
    return {"city": city, "temperature": 20, "description": "Sunny", "units": "C"}


# Import resource templates from other modules:
mcp.resource("weather://{city}/{date}/past_weather")(get_past_weather)


####### PROMPTS #######


# Prompts are reusable prompt templates that clients can discover and use.
# They help standardize common interactions and can include dynamic arguments.
@mcp.prompt()
def code_review() -> str:
    """Review code for best practices and potential issues."""
    return """Please review the following code for:
- Code quality and best practices
- Potential bugs or issues
- Performance considerations
- Security concerns

Provide specific suggestions for improvement."""


# Prompts can accept arguments to customize the output:
@mcp.prompt()
def summarize_text(style: str = "brief") -> str:
    """Summarize text in a specified style."""
    styles = {
        "brief": "Provide a 1-2 sentence summary.",
        "detailed": "Provide a comprehensive summary covering all key points.",
        "bullets": "Summarize as a bulleted list of key points.",
    }
    return f"""Summarize the following text.
{styles.get(style, styles["brief"])}"""


# Override the prompt name and description with decorator arguments:
@mcp.prompt(
    name="debug_error",
    description="Help debug an error message",
)
def debug_helper(error_message: str) -> str:
    return f"""I encountered the following error:

{error_message}

Please help me understand:
1. What this error means
2. Common causes
3. How to fix it"""


####### CUSTOM ROUTES #######


# Custom routes are used to add additional routes to the server.
# Intric will use this route to check if the server is running (falling back to ping if not found).
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


####### RUNNING THE SERVER #######
# The most simple way to run the server is to use the mcp.run() method.
# But for more control, you can use the http_app() method to create an ASGI application and then run it with uvicorn.
# Run with: uvicorn server:app --host 0.0.0.0 --port 8000
app = mcp.http_app(middleware=middleware)
