# # I had to update fastmcp to version 2.12.0 (pip install --upgrade fastmcp==2.12.0) to avoid the error:
# "TypeError: cannot specify both default and default_factory"
# More info at FastMCPDemo.py

from langchain_openai import AzureChatOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.resources import load_mcp_resources
from langchain_openai import ChatOpenAI # previously was: from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage

import asyncio
import os
from dotenv import load_dotenv

#-----------------------------------------------------------------------
#Configure the MCP Server Connection
#-----------------------------------------------------------------------
#Make sure the right path to the MCP server file is passed.
server_params = StdioServerParameters(
    command="python",
    args=[os.getcwd() + "/chapter2/code_of_conduct_server.py"],
)

#-----------------------------------------------------------------------
#Setup the OpenAI model (before it was Azure OpenAI model)
#-----------------------------------------------------------------------
load_dotenv()  # Loading OPENAI_API_KEY value (and old ones for Azure OpenAI)
# .env was tracked in git, so I had to add it to .gitignore and remove it from git tracking
## git status --short
## check if tracked
#git ls-files - -error-unmatch .env & & echo ".env is tracked" | | echo ".env is not tracked"
## show which ignore rule (if any) would match:
#git check-ignore - v .env | | true
#
# git rm --cached .env
# git commit - m "Stop tracking .env (now in .gitignore)"


# old parameters for Azure OpenAI
#endpoint = os.getenv("ENDPOINT_URL")
#deployment = os.getenv("DEPLOYMENT_NAME")
#subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
#api_version=os.getenv("API_VERSION")

model = ChatOpenAI(
    model="gpt-4.1",
    #temperature=0.7,
    #max_tokens=512,
)
# old code for Azure OpenAI
#model=AzureChatOpenAI(
#    azure_endpoint=endpoint,
#    api_key=subscription_key,
#    api_version=api_version,
#    deployment_name=deployment,
#)

# Common Mistake: Using AzureChatOpenAI with OpenAI Key
# WRONG — This is for AZURE only
# llm = AzureChatOpenAI(
#    azure_endpoint="https://api.openai.com",  # This will fail!
#    api_key="sk-..."
#)

#-----------------------------------------------------------------------
#Asynchronous function to fetch content from MCP resource
#Boilerplate code to run MCP and fetch resources
#-----------------------------------------------------------------------
async def fetch_resource_content():
    print("Running the MCP server...")
    async with stdio_client(server_params) as (read,write):
        #Initialize a session with the MCP server
        async with ClientSession(read,write) as session:
            print("initializing session")
            await session.initialize()

            #Load list of resources available & print
            print("\nloading resources")
            resources=await load_mcp_resources(session)
            print("Resources loaded :")
            for resource in resources:
                print(resource.metadata)  

            #Return the body of the first resource
            #This contains the content of the code of conduct PDF
            return resources[0].data

    return "done"

#-----------------------------------------------------------------------
#Run the MCP Client, fetch resource and generate response
#-----------------------------------------------------------------------

if __name__ == "__main__":
    print("\n-------------------------------------------------------")
    print("Running the code-of-client application")
    # Get content from the MCP resource
    retrieved_content = asyncio.run(fetch_resource_content())
    print("\nContent retrieved: ", retrieved_content)

    #Simulated User query
    user_query = "What are the data privacy policies of the company?"
    print("\nUser query: ", user_query)

    #Use the retrieved content to answer the user query
    prompt = f"""Answer the query based on the following context provided.\n
                Context: {retrieved_content} \n
                query: {user_query}
                """
    #Invoke the model with the prompt
    model_response = model.invoke(prompt)
    print("\nAnswer: ", model_response.content)