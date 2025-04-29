import requests
import json
from typing import Optional, Dict, Any

class SuiRpcClient:
    def __init__(self, network: str = "mainnet", local_port: int = 9000, custom_endpoint: Optional[str] = None):
        """
        Initialize Sui RPC client
        
        :param network: 'mainnet', 'testnet', 'devnet', or 'local'
        :param local_port: Port for local network (default: 9000)
        :param custom_endpoint: Override with custom fullnode URL
        """
        self.endpoint = self._get_endpoint(network, local_port, custom_endpoint)
        self.headers = {"Content-Type": "application/json"}
    
    def _get_endpoint(self, network: str, local_port: int, custom_endpoint: Optional[str]) -> str:
        if custom_endpoint:
            return custom_endpoint
            
        network = network.lower()
        if network == "local":
            return f"http://localhost:{local_port}"
        elif network in ("mainnet", "testnet", "devnet"):
            return f"https://fullnode.{network}.sui.io:443"
        else:
            raise ValueError(f"Unsupported network: {network}")

    def call_rpc(self, method: str, params: list, rpc_id: int = 1) -> Dict[str, Any]:
        """
        Make JSON-RPC 2.0 call to Sui fullnode
        
        :param method: RPC method name (e.g. 'suix_getCoinMetadata')
        :param params: List of parameters
        :param rpc_id: Request ID (default: 1)
        :return: Parsed JSON response
        """
        payload = {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "method": method,
            "params": params
        }
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"RPC call failed: {e}")

# Example Usage
if __name__ == "__main__":
    # Initialize client (choose one)
    client = SuiRpcClient(network="mainnet")  # For mainnet
    # client = SuiRpcClient(network="testnet")  # For testnet
    # client = SuiRpcClient(network="local")    # For localnet
    
    # Get USDC metadata
    usdc_metadata = client.call_rpc(
        method="suix_getCoinMetadata",
        params=["0x168da5bf1f48dafc111b0a488fa454aca95e0b5e::usdc::USDC"]
    )
    
    print(json.dumps(usdc_metadata, indent=2))

