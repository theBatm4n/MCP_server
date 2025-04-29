from smolagents import ToolCallingAgent, ToolCollection, LiteLLMModel
from mcp import StdioServerParameters, ClientSession

model = LiteLLMModel(
    model_id="ollama_chat/llama3.2",
    num_ctx=8192
)

server_parameters= StdioServerParameters(
    command='uv',
    args=['run', 'server.py'],
    env=None,
)

with ToolCollection.from_mcp(server_parameters, trust_remote_code=True) as tool_collection:
    agent = ToolCallingAgent(tools=[*tool_collection.tools], model=model)
    #agent.run("How has ETH-USD price moved in staring from 1st march 2025 to 30th march 2025? ")
    #agent.run("Could you swap 0.001 of 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE to 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 at a minimum price of 1601000 in the base chain with a slippage of 100 and the tokindecimal is 18")
    agent.run("Could you swap 0.001 of 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE to 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 in the base chain with a slippage of 100 and the tokindecimal is 18")
    #agent.run("Could you place a limit order of 0.001 of 0x4200000000000000000000000000000000000006 for 1.8 of 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 at the chain 8453 with a slippage of 100")
    #agent.run("what is the swap rate for 0.01 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE to 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 in the base chain")