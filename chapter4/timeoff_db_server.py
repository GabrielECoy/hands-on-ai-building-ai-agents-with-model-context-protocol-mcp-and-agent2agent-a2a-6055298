import os
import re
from dotenv import load_dotenv
from fastmcp import FastMCP

from timeoff_datastore import TimeOffDatastore

# -----------------------------------------------------------------------
# Setup the MCP Server
# -----------------------------------------------------------------------
load_dotenv()
timeoff_mcp = FastMCP("Timeoff-MCP-Server")

# -----------------------------------------------------------------------
# Initialize the Timeoff Datastore
# -----------------------------------------------------------------------
timeoff_db = TimeOffDatastore()

# Tool to get time off balance for an employee

# Copilot added sanitization and additional error messages, as I was getting 
# I added "Remove any comma or punctuation from the user name." in the above prompt because I was
# getting the error the following error when trying the agent examples:
#
# Answering prompt :  What is my time off balance?
# Response:  There was an error when trying to fetch your time off balance. Could you verify if your
# name is correctly spelled as "Alice," or provide your full name if necessary? This will help me
# retrieve your information more accurately.

@timeoff_mcp.tool()
def get_timeoff_balance(employee_name: str) -> str:
    """Get the timeoff balance for the employee, given their name.

    Input is sanitized (strip punctuation/trailing commas commonly inserted by LLMs)
    and the function returns a string result suitable for the MCP tool surface.
    """
    # Sanitize the incoming name: remove punctuation (commas, quotes, etc.) and trim
    print("Getting timeoff balance for employee: ", employee_name)
    if not employee_name:
        return "Invalid employee name"

    # remove punctuation characters that often get introduced by the LLM (e.g. 'Alice,')
    clean_name = re.sub(r"[^\w\s-]", "", employee_name).strip()
    if not clean_name:
        return "Invalid employee name"

    balance = timeoff_db.get_timeoff_balance(clean_name)
    if balance is None:
        # Return a clear string response the tool/agent can consume
        return f"Employee '{clean_name}' not found"

    # Ensure we return a string (tools often expect serializable simple types)
    return str(balance)

# Tool to add a time off request for an employee


@timeoff_mcp.tool()
def request_timeoff(employee_name: str, start_day: str, days: int) -> str:
    """File a  timeoff request for the employee, 
        given their name, start day and number of days"""

    print("Requesting timeoff for employee: ", employee_name)
    return timeoff_db.add_timeoff_request(
        employee_name, start_day, days)

# Get prompt for the LLM to use to answer the query


@timeoff_mcp.prompt()
def get_llm_prompt(user: str, prompt: str) -> str:
    """Generates a a prompt for the LLM to use to answer the query
    give a user and a query"""
    print("Generating prompt for user: ", user)
    return f"""
    You are a helpful timeoff assistant. 
    Execute the action requested in the query using the tools provided to you.
    Action: {prompt}
    The tasks need to be executed in terms of the user {user}.    
    """

# -----------------------------------------------------------------------
# Run the Timeoff Server
# -----------------------------------------------------------------------

# Test code
# print("Time off balance for Alice: ", get_timeoff_balance("Alice"))
# print("Add time off request for Alice: ", request_timeoff("Alice", "2025-05-05",5))
# print("New Time off balance for Alice: ", get_timeoff_balance("Alice"))

if __name__ == "__main__":
    timeoff_mcp.run(transport="streamable-http",
                    host="localhost",
                    port=8000,
                    path="/",
                    log_level="debug")

# --- CoPilot changes to fix this error I was getting when running the server ---
# /home/vscode/.local/lib/python3.13/site-packages/websockets/legacy/init.py: 6:
# DeprecationWarning: websockets.legacy is deprecated; see
# # https: // websockets.readthedocs.io/en/stable/howto/upgrade.html for upgrade instructions
# warnings.warn(  # deprecated in 14.0 - 2024-11-09
# / home/vscode/.local/lib/python3.13/site-packages/uvicorn/protocols/websockets/websockets_impl.py: 17: DeprecationWarning: websockets.server.WebSocke
#
# --- Warning Explanation ---
# This is a Python dependency issue, not a VS Code configuration issue. The deprecation warnings are coming from your project's dependencies (uvicorn and websockets), not from VS Code itself.
# To fix these warnings, you need to update your Python packages:
# Update the websockets package to a version that no longer uses the legacy API:
# Update uvicorn to a version compatible with the latest websockets:
# Or update all dependencies in your project:
# (if you have a requirements.txt file)
# Verify the updates by running your server again:
# Why this is happening:
# Your uvicorn version is using the deprecated websockets.legacy API
# Newer versions of websockets(14.0+) have removed the legacy API
# You need compatible versions of both packages
# If you want to suppress these warnings temporarily while working on updates, you can add this to the top of your timeoff_db_server.py:
# , it's better to update the packages to resolve the underlying issue properly.
#
#
# --- Agent Fix ---
# I'll analyze the current requirements and propose a fix. Let me first check what's currently in the requirements.txt file.
#
# Perfect! I can see the issue now. The problem is:
# websockets 15.0.1 has removed the legacy API(deprecated in 14.0+)
# uvicorn 0.38.0 still depends on the old legacy API
# The fix is to update uvicorn to a newer version that's compatible with websockets 15.0.1.
# Proposed Fix
# Add explicit package version constraints to requirements.txt to ensure compatibility:
#
# uvicorn>=0.32.0
# websockets >= 14.0, < 15.0
#
# requirements.txt+2-0
# Code to install the updated packages:
# cd /workspaces/hands-on-ai-building-ai-agents-with-model-context-protocol-mcp-and-agent2agent-a2a-6055298
# && pip install -r requirements.txt --upgrade
#
# --- Final update because I was still getting the deprecation warnings ---:
# The issue is that uvicorn 0.38.0 still uses the deprecated websockets legacy API, even though
# we downgraded websockets to 14.2. We need to upgrade uvicorn to a newer version that supports
# the current websockets API. Note: Tried upgrading uvicorn to 0.40 and failed
# I see - uvicorn's latest version is 0.38.0. The issue is that the old uvicorn/websockets
# compatibility is baked in. Let me try a different approach - use websockets 13.x instead,
# which should be compatible with uvicorn 0.38.0:
# So it changed: websockets >= 14.0, < 15.0 to websockets >= 13.0, < 14.0
#
# Also see hr_policy_agent.py in chapter 2 for additional fixes on fastmcp to avoid the
# TypeError('cannot specify both default and default_factory')
