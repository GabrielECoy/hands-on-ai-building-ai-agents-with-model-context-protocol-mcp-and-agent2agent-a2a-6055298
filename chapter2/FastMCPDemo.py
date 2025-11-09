# This is the demo I copy&pasted from the 
# I had to update fastmcp to version 2.12.0 (pip install --upgrade fastmcp==2.12.0) to avoid the below error
# Error:
# "TypeError: cannot specify both default and default_factory"
# It seems like it's a known problem with fastmcp 2.8.0 and pydantic 2.12.0 (this courses uses an old verion of fastmcp 2.3.5)
# More info:
# Fix fastmcp 2.8.0 incompatibility with Pydantic 2.12.0: https://github.com/elastic/mcp-server-elasticsearch/issues/211
# Settings class field has both default and default_factory: https://github.com/jlowin/fastmcp/issues/1377
# Fix: https://github.com/jlowin/fastmcp/blob/c6e3c16b11b7603f78d76c1cef91c4abf23878c8/src/fastmcp/settings.py#L111-L117

from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    mcp.run()