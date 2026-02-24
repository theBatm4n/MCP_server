from mcp import ClientSession , StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
import asyncio  

async def main():
    model = ChatAnthropic(model="claude-3-5-sonnet-latest")

    server_parameters= StdioServerParameters(
        command='uv',
        args=['run', 'server.py'],
        env=None,
    )

    async with stdio_client(server_parameters) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(model,tools)
            agent_response = await agent.ainvoke({"messages":"How has ETH-USD price moved in staring from 1st march 2025 to 30th march 2025?"})
    
    for m in agent_response["messages"]:
        m.pretty_print()

if __name__ == "__main__":
    asyncio.run(main())
