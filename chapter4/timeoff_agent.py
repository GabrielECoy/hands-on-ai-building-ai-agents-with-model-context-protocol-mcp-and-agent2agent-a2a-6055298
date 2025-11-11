from mcp import ClientSession, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.prompts import load_mcp_prompt

# -- See note at the bottom of the file for more info on this fix by copilot --
# Workaround shim: some versions of langgraph.prebuilt.create_react_agent
# call StateGraph.add_node(...) with keyword `input_schema=` while older
# installed `StateGraph.add_node` implementations expect `input=`. That
# mismatch raises a TypeError at runtime. Instead of forcing a dependency
# upgrade (which conflicts with other pinned langchain packages), we
# monkey-patch StateGraph.add_node at runtime to accept `input_schema`
# and forward it to `input`.
try:
    from langgraph.graph import StateGraph

    _orig_add_node = StateGraph.add_node

    def _add_node_accept_input_schema(self, *args, **kwargs):
        if "input_schema" in kwargs and "input" not in kwargs:
            kwargs["input"] = kwargs.pop("input_schema")
        return _orig_add_node(self, *args, **kwargs)

    StateGraph.add_node = _add_node_accept_input_schema
except Exception:
    # If langgraph isn't installed or the patch can't be applied, continue
    # and let the original import/call produce the normal error for visibility.
    pass

from langgraph.prebuilt import create_react_agent
# previously was: from langchain_openai import AzureChatOpenAI
from langchain_openai import ChatOpenAI

import asyncio
import os
from dotenv import load_dotenv

# -----------------------------------------------------------------------
# Setup the LLM for the HR Timeoff Agent
# This uses the Azure OpenAI service with a specific deployment
# Please replace the environment variables with your own values
# -----------------------------------------------------------------------
# *** Changes to the above comment, this is now going to use navite OpenAI model ***
# More info and similar changes in: code_of_conduct_client.py in chapter2
# -----------------------------------------------------------------------

load_dotenv()

model = ChatOpenAI(
    model="gpt-4.1",
    # temperature=0.7,
    # max_tokens=512,
)

# -----------------------------------------------------------------------
# Define the HR timeoff agent that will use the MCP server
# to manage timeoff requests.
# -----------------------------------------------------------------------


async def run_timeoff_agent(user: str, prompt: str,) -> str:

    # Make sure the right URL to the MCP Server is passed.
    # and MCP server is running and accessible
    #
    # The url originally ended in "/mcp", but copilot changes to avoid the following error I was getting:
    # Response: Error initializing session - Error: unhandled errors in a TaskGroup(1 sub-exception)
    # It was probably due to the version updates in the packages
    mcp_server_url = "http://localhost:8000/"

    try:
        async with streamablehttp_client(mcp_server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                print("initializing session")
                await session.initialize()

                timeoff_tools = await load_mcp_tools(session)
                print("\nTools loaded :")
                for tool in timeoff_tools:
                    print("Tool : ", tool.name, " - ", tool.description)

                timeoff_prompt = await load_mcp_prompt(session,
                                                       "get_llm_prompt",
                                                       arguments={"user": user, "prompt": prompt})
                print("\nPrompt loaded :", timeoff_prompt)

                print("\nCreating agent instance")
                agent = create_react_agent(model, timeoff_tools)

                print("\nAnswering prompt : ", prompt)
                agent_response = await agent.ainvoke(
                    {"messages": timeoff_prompt})

                return agent_response["messages"][-1].content
    except Exception as e:
        # Print full traceback to help diagnose TaskGroup sub-exceptions
        import traceback
        traceback.print_exc()

        print(f"Error: {e}")
        return "Error"


if __name__ == "__main__":
    #
    response = asyncio.run(
        run_timeoff_agent("Alice",
                          "What is my time off balance?"))
    print("\nResponse: ", response)
    response = asyncio.run(
        run_timeoff_agent("Alice",
                          "File a time off request for 5 days starting from 2025-05-05"))
    print("\nResponse: ", response)

    response = asyncio.run(
        run_timeoff_agent("Alice",
                          "What is my time off balance now?"))
    print("\nResponse: ", response)

# I got "Error: unhandled errors in a TaskGroup (1 sub-exception)" error when creating the agent instance
# The sub exception shown by the traceback was:  TypeError: StateGraph.add_node() got an unexpected keyword argument 'input_schema'
#
# What Copilot did:
# Summary — what I did
# Root cause: the agent creation failed because installed langgraph code expected StateGraph.add_node(input=...)
#  while create_react_agent was calling add_node(input_schema=...). Upgrading langgraph to fix that conflicts
#  with the current pinned langchain/core versions.
# Fix applied: added a small runtime shim to translate input_schema -> input on StateGraph.add_node so 
#  create_react_agent works with the currently installed packages.
# Verified: ran the agent in the project's .venv; session initialized, tools loaded, agent created and 
#  returned a reply (no TaskGroup ExceptionGroup / TypeError anymore).
#
# Files changed
# timeoff_agent.py
# Added a safe monkey-patch at runtime that maps keyword input_schema to input on
# langgraph.graph.StateGraph.add_node.
# Kept original behavior if langgraph isn't present or the patch can't be applied.

#
# Why I chose this approach
# Upgrading langgraph to >=1.0.3 is a correct long-term fix, but pip resolution failed in this environment
#  because langgraph-prebuilt >=1.0.2 requires langchain-core>=1.0.0 which conflicts with many pinned
#  langchain packages (0.3.x) in your requirements.
# The runtime shim is a low-risk, minimally invasive fix that resolves the immediate TypeError without
#  changing dependency pins or requiring a breaking upgrade of the langchain stack.
# What I ran to test it
# Reinstalled requirements in the project's venv (attempted; pip showed a dependency conflict if we try
#  to upgrade langgraph).
# Ran the agent script with the venv Python:
# /workspaces/.../.venv/bin/python timeoff_agent.py
# Observed output:
# Session initialized
# Tools loaded
# Agent created
# Agent returned a reply (so no TaskGroup ExceptionGroup / TypeError)
# Result (quality gates)
# Build / runtime: PASS — agent runs, no TaskGroup ExceptionGroup observed.
# Lint/typecheck: the editor reported unresolved imports (these are environment/static-analysis warnings
#  because some packages live in the venv); runtime execution succeeded.
# Tests: none added. If you'd like, I can add a small unit test to exercise agent creation.
#
# Recommendations / next steps
# Short-term (keep as-is)
# Keep the monkey-patch shim in timeoff_agent.py. It's a safe stopgap and documented in the file with
# comments.
# Long-term (preferred if you want to clean dependencies)
# Decide whether to upgrade the langchain ecosystem to versions compatible with langgraph >=1.0.3
# (this means upgrading langchain-core to >=1.0.0 and likely many other langchain packages). If you want
#  to do that, I can:
# Propose a minimal new set of constraints for requirements.txt that are compatible, or
# Create a branch and do the upgrade+test, fixing any API changes.
# Alternatively, vendor a small compatibility shim module in the project (instead of patching in-place)
#  or add the shim to a central bootstrap module if multiple scripts need it.
# Cleanup suggestions
# Recreate the venv and run pip install -r requirements.txt after deciding whether to upgrade or not.
#  Right now pip fails when trying to upgrade langgraph because of the langchain-core mismatch; that's
#  expected.
# If you want I can prepare a lockfile or a tighter requirements set that will allow you to upgrade safely.
# If you'd like, I can:
# Remove the shim and upgrade the langchain/langgraph stack end-to-end (I will first propose a compatible
#  set of pins and run & test).
# Or add a tiny unit test verifying agent creation (happy path + one edge case) and run it in the venv.
#
# Note: There was a changes in requirements.txt to upgrade langgraph from == 0.4.5 to >=1.0.3, but
# I removed since as per the explanation above, it would cause conflicts with other langchain packages.
# and the shim approach was chosen instead.
# I ren pip install -r requirements.txt to confirm the final environment requirements work