from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.prompts import load_mcp_prompt
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI # previously was: from langchain_openai import AzureChatOpenAI

import asyncio
import os
from dotenv import load_dotenv

# -----------------------------------------------------------------------
# Setup the LLM for the HR Policy Agent
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

# Fix added by copilot to patch langgraph compatibility issue.
# More info at hr_policy_agend (error fix explanation).md
#
# Workaround: some installed versions of `langgraph` use `input` as the
# add_node kwarg while `create_react_agent` (from another langgraph
# release) passes `input_schema`. Patch StateGraph.add_node to accept
# `input_schema` and map it to `input` so the prebuilt agent works with
# the currently installed langgraph.
#
# Note: This fix may not be required after copilot fixed (as part of running chapter 4 excercises)
# the issue of fastmcp==2.3.5 been incompatible with Pydantic 2.12.4 by updating the
# requirements.txt to use a newer, compatible version of fastmcp: From >= 2.3.5 to fastmcp >= 2.12.0

try:
    from functools import wraps
    from langgraph.graph import StateGraph

    _orig_add_node = StateGraph.add_node

    @wraps(_orig_add_node)
    def _patched_add_node(self, node, action=None, *args, **kwargs):
        # map older/newer kw name to the implemented one
        if 'input_schema' in kwargs and 'input' not in kwargs:
            kwargs['input'] = kwargs.pop('input_schema')
        return _orig_add_node(self, node, action, *args, **kwargs)

    StateGraph.add_node = _patched_add_node
    print('Patched StateGraph.add_node to accept input_schema -> input')
except Exception as _e:
    # If patching fails, continue and let the original error surface later.
    print('Could not patch StateGraph.add_node:', _e)

# -----------------------------------------------------------------------
# Define the HR policy agent that will use the MCP server
# to answer queries about HR policies.
# -----------------------------------------------------------------------


async def run_hr_policy_agent(prompt: str) -> str:

    # Make sure the right path to the server file is passed.
    hr_mcp_server_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__),
                     "hr_policy_server.py"))
    print("HR MCP server path: ", hr_mcp_server_path)

    # Create the server parameters for the MCP server
    server_params = StdioServerParameters(
        command="python",
        args=[hr_mcp_server_path],
    )

    # Create a client session to connect to the MCP server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("initializing session")
            await session.initialize()

            print("\nloading tools & prompt")
            hr_policy_tools = await load_mcp_tools(session)
            hr_policy_prompt = await load_mcp_prompt(session,
                                                     "get_llm_prompt",
                                                     arguments={"query": prompt})

            print("\nTools loaded :", hr_policy_tools[0].name)
            print("\nPrompt loaded :", hr_policy_prompt)

            print("\nCreating agent")
            agent = create_react_agent(model, hr_policy_tools)

            print("\nAnswering prompt : ", prompt)
            agent_response = await agent.ainvoke(
                {"messages": hr_policy_prompt})

            return agent_response["messages"][-1].content

    return "Error"

if __name__ == "__main__":
    # Run the HR policy agent with a sample query
    print("\nRunning HR Policy Agent...")
    response = asyncio.run(
        run_hr_policy_agent("What is the policy on remote work?"))

    print("\nResponse: ", response)
