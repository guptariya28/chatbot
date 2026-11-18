
import asyncio
from mcp import Client


MCP_SERVER_URL = "https://mcp.atlassian.com/v2/mcp"


async def main():

    async with Client(MCP_SERVER_URL) as client:

        # Call an existing Jira MCP tool
        result = await client.call_tool(
            "get_issue",
            {
                "issue_key": "PROJ-123"
            }
        )

        print(result)


asyncio.run(main())
