from web3 import Web3
from web3.contract import Contract
from web3.exceptions import BadFunctionCallOutput

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

def getDecimals(tokenAddress: str, web3: Web3) -> int:
    """
    Get the decimals of an ERC20 token
    
    Args:
        tokenAddress: The contract address of the token
        web3: Web3 instance connected to a provider
        
    Returns:
        int: Number of decimals (typically 18 for ETH, 6 for USDC, etc.)
        
    Raises:
        ValueError: If the address is invalid or contract doesn't support decimals
    """
    try:
        # Validate address 
        if not web3.is_address(tokenAddress):
            raise ValueError(f"Invalid token address: {tokenAddress}")
            
        if tokenAddress.lower() == "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee":
            return 18
            
        # Create contract instance
        contract: Contract = web3.eth.contract(
            address=web3.to_checksum_address(tokenAddress),
            abi=ERC20_ABI
        )
        
        # Call decimals function
        decimals: int = contract.functions.decimals().call()
        return decimals
        
    except BadFunctionCallOutput:
        raise ValueError("Contract doesn't support decimals function")
    except Exception as e:
        raise ValueError(f"Error getting decimals: {str(e)}")
    
if __name__ == "__main__":
    print(getDecimals('0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', Web3))