import requests
import time
from decimal import Decimal
import json
import yfinance as yf
from colorama import Fore
from mcp.server.fastmcp import FastMCP
import pandas as pd
from datetime import datetime, timedelta
import time
import requests
from decimal import Decimal
import json
import mcp


def condition_Token_swap(tokenInaddress, tokenOutaddress, minPrice, swapamount, signerAddress, targetChain, tokenInDemical, slippage):
    # Configuration
    AggregatorDomain = "https://aggregator-api.kyberswap.com"
    gettargetPath = f"/{targetChain}/api/v1/routes"
    posttargetPath = f"/{targetChain}/api/v1/route/build"
    
    # Swap parameters
    POLL_INTERVAL = 2  # seconds between checks
    max_attempts = 100  # max attempts before giving up (30 attempts = ~1 minute)
    
    # Calculate amount in smallest units
    amount_in = int(swapamount * (10 ** tokenInDemical))
    
    # Monitoring loop
    for attempt in range(1, max_attempts + 1):
        try:
            # Get current price quote
            response = requests.get(
                f"{AggregatorDomain}{gettargetPath}",
                params={
                    "tokenIn": tokenInaddress,
                    "tokenOut": tokenOutaddress,
                    "amountIn": str(amount_in)
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Check response structure
            if not data.get('data', {}).get('routeSummary'):
                print(f"[Attempt {attempt}] Unexpected response format")
                continue
                
            current_price = int(data['data']['routeSummary']['amountOut'])
            print(f"[Attempt {attempt}] Current output: {current_price}, Target: {minPrice}")
            
            # Check if price meets our condition
            if current_price >= minPrice:
                print("Price condition met! Building swap transaction...")
                
                # Build swap transaction
                swap_response = requests.post(
                    f"{AggregatorDomain}{posttargetPath}",
                    json={
                        "routeSummary": data['data']['routeSummary'],
                        "sender": signerAddress,
                        "recipient": signerAddress,
                        "slippageTolerance": slippage
                    },
                    timeout=10
                )
                swap_response.raise_for_status()
                swap_data = swap_response.json()
                
                print("Swap transaction built successfully!")
                return swap_data['data']
                
        except requests.exceptions.RequestException as error:
            print(f"Attempt {attempt} failed:", str(error))
            if hasattr(error, 'response') and error.response:
                print("Error details:", error.response.text)
        
        time.sleep(POLL_INTERVAL)
    
    print(f"Failed after {max_attempts} attempts. Price condition not met.")
    return None

def token_swap(tokenInaddress, tokenOutaddress, swapamount, signerAddress, targetChain, tokenInDemical, slippage):
    """This tool executes token swaps without regard to price"""

    AggregatorDomain = "https://aggregator-api.kyberswap.com"
    gettargetPath = f"/{targetChain}/api/v1/routes"
    posttargetPath = f"/{targetChain}/api/v1/route/build"
    amount_in = int(swapamount * (10 ** tokenInDemical))

    try:
        response = requests.get(
                f"{AggregatorDomain}{gettargetPath}",
                params={
                    "tokenIn": tokenInaddress,
                    "tokenOut": tokenOutaddress,
                    "amountIn": str(amount_in)
                },
                timeout=10
            )
        response.raise_for_status()
        data = response.json()

        swap_response = requests.post(
                    f"{AggregatorDomain}{posttargetPath}",
                    json={
                        "routeSummary": data['data']['routeSummary'],
                        "sender": signerAddress,
                        "recipient": signerAddress,
                        "slippageTolerance": slippage
                    },
                    timeout=10
                )
        swap_response.raise_for_status()
        swap_data = swap_response.json()
        print("Swap transaction built successfully!")
        return swap_data['data']

    except requests.exceptions.RequestException as error:
            print(str(error))



def limit_order(tokenInaddress, tokenOutaddress, AmountIn, AmountOut, ChainID):
    SignerAddress = "0x42c0682214BF0FdCac4FB29fc509FB636537396E"
    AmountIn = Decimal(AmountIn)
    AmountOut = Decimal(AmountOut)
    makingAmount = str(int(AmountIn * (10 ** 18)))
    takingAmount = str(int(AmountOut * (10 ** 6)))

    try:
        # First request to get signature data
        response = requests.post(
            "https://limit-order.kyberswap.com/write/api/v1/orders/sign-message",
            headers={"Content-Type":"application/json"},
            data=json.dumps({
            "chainId": str(ChainID),
            "makerAsset": tokenInaddress,
            "takerAsset": tokenOutaddress,
            "maker": SignerAddress,
            "makingAmount": makingAmount,
            "takingAmount": takingAmount,
            "expiredAt": int(time.time()) + 3600})  # Expires in 1 hour
        )
        response.raise_for_status()
        signdata = response.json()
        print('Response:', signdata)    

        """
        # SIGN the response with wallet (commented out as in original)
        # This would require web3.py implementation
        from web3 import Web3
        from eth_account.messages import encode_structured_data
        
        w3 = Web3(Web3.HTTPProvider('YOUR_PROVIDER_URL'))
        signed_message = w3.eth.account.sign_typed_data(
            private_key='YOUR_PRIVATE_KEY',
            domain_data=signdata['domain'],
            message_types=signdata['types'],
            message_data=signdata['message']
        )
        
        # Second request to submit the signed order
        order_response = requests.post(
            'https://limit-order.kyberswap.com/write/api/v1/orders',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                **signdata,
                "signature": signed_message.signature.hex()
            })
        )
        print("Order created:", order_response.json())
        """
    

    except requests.exceptions.RequestException as error:
            print('Error:', error.response.text if error.response else str(error))




# Example usage
if __name__ == "__main__":
    tokenInaddress = "0x4200000000000000000000000000000000000006"
    tokenOutaddress = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    TargetChain =8453
    result = limit_order(tokenInaddress,tokenOutaddress, '0.001', '1.7', TargetChain)