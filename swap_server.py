import mcp
import time
import requests
from decimal import Decimal
import json

AggregatorDomain = "https://aggregator-api.kyberswap.com"

#### Helper functions
def getSignerAddress():
    return "0x42c0682214BF0FdCac4FB29fc509FB636537396E"

def getDecimals(tokenAddress):
    # number of decimcals for the given ERC20 token and native token
    pass

def get_swap_quote(tokenInaddress,tokenOutaddress, amount_in, targetChain):
    gettargetPath = f"/{targetChain}/api/v1/routes"
    amount_in = int(amount_in * (10 ** getDecimals(tokenInaddress)))
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
            return data
    except requests.exceptions.RequestException as error:
        return None
    
def post_swap_quote(data, slippage, targetChain):
    posttargetPath = f"/{targetChain}/api/v1/route/build"
    try:
        swap_response = requests.post(
                        f"{AggregatorDomain}{posttargetPath}",
                        json={
                            "routeSummary": data['data']['routeSummary'],
                            "sender": getSignerAddress(),
                            "recipient": getSignerAddress(),
                            "slippageTolerance": slippage
                        },
                        timeout=10
                    )
        swap_response.raise_for_status()
        swap_data = swap_response.json()
        print("Swap transaction built successfully!")
        return swap_data
    except requests.exceptions.RequestException as error:
        return None

def excute_transcation(data):
    # based on framework, ethers.js?
    pass


### TOOLS
@mcp.tool()
def get_current_swap_rate(tokenInaddress, tokenOutaddress, swapamount, targetChain):

    quote_data = get_swap_quote(tokenInaddress, tokenOutaddress, swapamount, targetChain)
    if not quote_data:
        return {"error": "Failed to get swap quote"}
    return 


@mcp.tool()
def perform_conditional_token_swap(tokenInaddress, tokenOutaddress, minPrice, swapamount, targetChain, slippage):
    """This tool executes token swaps when the desired miniumum price is reached , 
    only used when there is a given price target/ minimum price to be swapped
    
    Args:
        tokenInaddress: Contract address of the token to swap from (use 0xEee...EEeE for native ETH)      
        tokenOutaddress: Contract address of the token to receive       
        minPrice: Minimum acceptable output amount (in token's smallest units) 
        swapamount: Amount of input token to swap (in human-readable units)       
        targetChain: Blockchain network ID (lowercase), like "base" or "arbitrum"
        Example: "base" or "arbitrum"
        slippage: Slippage tolerance in basis points (100 = 1%)

    Returns:
        dict: Swap transaction details when successful, None if conditions not met
    """
    POLL_INTERVAL = 2  
    max_attempts = 100 

    for attempt in range(max_attempts):
        quote_data = get_swap_quote(tokenInaddress, tokenOutaddress, swapamount, targetChain)
        if not quote_data:
            return {"error": "Failed to get swap quote"}
        current_price = int(quote_data['data']['routeSummary']['amountOut'])
        print(f"[Attempt {attempt}] Current output: {current_price}, Target: {minPrice}")
        if current_price >= minPrice:
            swap_data = post_swap_quote(quote_data, slippage, targetChain)
            if not swap_data:
                return {"error": "Failed to build swap transaction"}
            # tx_hash = execute_transaction(swap_data)
            # if not tx_hash:
            #     return {"error": "Transaction execution failed"}
            # return tx_hash
        time.sleep(POLL_INTERVAL)
    return {"failed to swap at target price"}


 
@mcp.tool()
def perform_token_swap(tokenInaddress, tokenOutaddress, swapamount, targetChain, slippage):
    """This tool executes a token swap without price targets or minimum price.

    Args:
        tokenInaddress (str): Contract address of the input token.
        tokenOutaddress (str): Contract address of the output token.
        swapamount (float): Amount of input token to swap (in human-readable units, e.g., 1.5 ETH).
        targetChain (str): Blockchain network ID (e.g., "ethereum", "polygon").
        tokenInDemical (int): Decimal places of the input token (e.g., 18 for ETH).
        slippage (float): Maximum acceptable slippage (e.g., 0.5 for 0.5%).
    
    Returns:
        Swap transaction data tx hash
    """
    # Step 1: Get the swap quote
    quote_data = get_swap_quote(tokenInaddress, tokenOutaddress, swapamount, targetChain)
    if not quote_data:
        return {"error": "Failed to get swap quote"}
    
    # Step 2: Build the swap transaction with slippage tolerance
    swap_data = post_swap_quote(quote_data, slippage, targetChain)
    if not swap_data:
        return {"error": "Failed to build swap transaction"}
    
    # tx_hash = execute_transaction(swap_data)
    # if not tx_hash:
    #     return {"error": "Transaction execution failed"}
    # return tx_hash



@mcp.tool()
def place_limit_order(tokenInaddress, tokenOutaddress, AmountIn, AmountOut, ChainID, expiry_time):
    """Creates a limit order.
    
    Args:
        tokenInaddress (str): Maker token contract address.
        tokenOutaddress (str): Taker token contract address.
        AmountIn (float): Maker token amount (human-readable units).
        AmountOut (float): Minimum taker token amount to receive (human-readable units).
        ChainID (int): Blockchain network ID (e.g., 1 for Ethereum).
         expiry_time (int): Time in seconds until the order expires (e.g., 3600 for 1 hour).
    
    Returns:
        Swap transaction data tx hash
    """

    AmountIn = Decimal(AmountIn)
    AmountOut = Decimal(AmountOut)
    makingAmount = str(int(AmountIn * (10 ** getDecimals(tokenInaddress))))
    takingAmount = str(int(AmountOut * (10 ** getDecimals(tokenOutaddress))))

    try:
        # First request to get signature data
        response = requests.post(
            'https://limit-order.kyberswap.com/write/api/v1/orders/sign-message',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                "chainId": ChainID,
                "makerAsset": tokenInaddress,
                "takerAsset": tokenOutaddress,
                "maker": getSignerAddress(),
                "makingAmount": makingAmount,
                "takingAmount": takingAmount,
                "expiredAt": int(time.time()) + expiry_time  # Expires in 1 hour
            })
        )
        response.raise_for_status()
        signdata = response.json() 
        # # tx_hash = execute_transaction(signdata)
        # if not tx_hash:
        #     return {"error": "Transaction execution failed"}
        # return tx_hash
        
    except requests.exceptions.RequestException as error:
            return error.response.text if error.response else str(error) 
    

@mcp.tool()
def get_limit_orders(chainId):
    """Fetches active limit orders for a specific maker address.
    
    Args:
        chainId (string): Blockchain network ID (e.g., 1 for Ethereum, 56 for BSC).
        
    Returns:
        List[Dict]: List of active limit orders with details including:
            - orderHash
            - makerAsset
            - takerAsset
            - makerAmount
            - takerAmount
            - expiry
            - status
    """
    makeraddress = getSignerAddress()
    try:
        response = requests.get(
            f"https://limit-order.kyberswap.com/read-ks/api/v1/orders?chainId={chainId}&maker={makeraddress}&status=active",
            headers={"Accept":"*/*"},
        )

        data = response.json()
        return data
    except requests.exceptions.RequestException as error:
        return error.response.text if error.response else str(error) 


@mcp.tool()
def cancel_limit_order(chainId, orderIds):
    """Cancels one or more limit orders on KyberSwap.
    
    Args:
        chainId (str): Blockchain network ID as a string (e.g., "1" for Ethereum, "56" for BSC).
        orderIds (List[int]): List of order IDs to cancel.
        
    Returns:
        Dict: Response from KyberSwap API containing cancellation status.
        
    """
    response = requests.post(
        "https://limit-order.kyberswap.com/write/api/v1/orders/cancel-sign",
        headers={"Content-Type":"application/json"},
        data=json.dumps({
            "chainId":chainId,
            "maker":getSignerAddress(),
            "orderIds":orderIds})
    )
    data = response.json()

    # logic for signing transaction

    confirm_response = requests.post(
    "https://limit-order.kyberswap.com/write/api/v1/orders/cancel",
    headers={"Origin":"text","Content-Type":"application/json"},
    data=json.dumps({"chainId":"137",
                     "maker":"0x2bfc3A4Ef52Fe6cD2c5236dA08005C59EaFB43a7",
                     "orderIds":[22405],
                     "signature":"signed-data"})
    )

    confirm_data = confirm_response.json()
    return confirm_data

if __name__ == "__main__":
    mcp.run(transport='stdio')
    