from fastmcp import FastMCP

from resources import get_past_weather, tell_a_joke
from tools import devide_two_numbers

# The FastMCP server class is the main object that represents the server.
# The most simple way to create a server is to use the FastMCP class and pass the name of the server.
mcp = FastMCP(
    name="Intric MCP Template Server",
)


####### SIMPLE TOOLS IMPLEMENTATION #######


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
    Internal functiuon description which will be ignored.
    """
    return a + b


# If you are working with multiple modules, you can import the functions directly into the server module and add them to the server via:
mcp.tool()(devide_two_numbers)


####### SIMPLE RESOURCES IMPLEMENTATION #######


# Resources can be defined the same way as tools, but using the @mcp.resource decorator.
@mcp.resource("resource://hello_world")
def get_hello_world() -> str:
    """
    Provides a message
    """
    return "Hello, from Intric MCP Template Server!"


# Just like with tools, you can use decorator arguments to override the ones FastMCP infer (as the example above):
@mcp.resource(
    uri="resource://hello_world_v2",
    name="Greetings Resource",
    description="Provides a message",
)
def get_hello_world_v2() -> str:
    """
    Internal functiuon description which will be ignored.
    """
    return "Hello, from Intric MCP Template Server! (v2)"


# If you are working with multiple modules, you can import the functions directly into the server module and add them to the server via:
mcp.resource("resource://tell_a_joke")(tell_a_joke)


####### SIMPLE RESOURCE TEMPLATES IMPLEMENTATION #######


# Unlike resources, resource templates allow clients to request resourcces where the content depends on the request.
# You can then make a resource that returnes the response based on the request.
# For example:
@mcp.resource("weather://{city}/current")
def get_current_weather(city: str) -> dict:
    """Provide the current weather for a given city."""
    return {"city": city, "temperature": 20, "description": "Sunny", "units": "C"}


# If you are working with multiple modules, you can import the functions directly into the server module and add them to the server via:
mcp.resource("weather://{city}/{date}/past_weather")(get_past_weather)

####### RUNNING THE SERVER #######

# Since Intric connects to the server via HTTP, we can use the FastAPI run method to start the server vitht the streamable HTTP transport.
if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8001)
