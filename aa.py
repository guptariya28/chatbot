
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Official Atlassian MCP endpoint
MCP_SERVER_URL = "https://mcp.atlassian.com/v2/mcp"


async def main():

    # Launch the OAuth-enabled remote MCP proxy
    server_params = StdioServerParameters(
        command="npx",
        args=[
            "-y",
            "mcp-remote",
            MCP_SERVER_URL
        ]
    )

    print("Starting Atlassian MCP connection...")

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            # Initialize MCP connection
            await session.initialize()

            print("\nSuccessfully connected to Jira MCP!")

            # Discover Jira tools
            response = await session.list_tools()

            print("\nAvailable Jira tools:\n")

            for tool in response.tools:
                print(f"Name: {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Input: {tool.inputSchema}")
                print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())

python -c "import certifi; print(certifi.where())"


2. Check Atlassian authentication connectivity
python -c "import httpx; print(httpx.get('https://auth.atlassian.com').status_code)"


3. Check SSL-related environment variables
Get-ChildItem Env: | Where-Object {$_.Name -match 'proxy|cert|ssl'}
