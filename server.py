import yfinance as yf
from colorama import Fore
from mcp.server.fastmcp import FastMCP
import time
import requests
from decimal import Decimal
import json
import pandas as pd
from datetime import datetime, timedelta

gettargetPath = '/base/api/v1/routes'
posttargetPath = '/base/api/v1/route/build'

mcp = FastMCP('yfinanceserver')

# HELPER FUNCTIONS
def getSignerAddress():
    return "0x42c0682214BF0FdCac4FB29fc509FB636537396E"

def getDecimals(tokenAddress):
    return 18

@mcp.tool()
def get_price_data(ticker, start_date, end_date, interval="1d"):
    """This tool returns historical price data for a given cryptocurrency pair (e.g., ETH-USD) 
    between start_date and end_date. Returns only Date and Close price columns.
    
    Args:
        ticker: The trading pair symbol (e.g., "ETH-USD")
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        interval: Data interval (default: '1d' for daily)
                 Options: 1m, 2m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo
    
    Returns:
        pandas.DataFrame: A dataframe with only two columns: 
                         - 'Date' (datetime) 
                         - 'Close' (price)
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    intraday_intervals = ['1m', '2m', '5m', '15m', '30m', '1h']

    if interval in intraday_intervals:
        batch_sizes = {
            '1m': timedelta(days=7),
            '2m': timedelta(days=60),
            '5m': timedelta(days=60),
            '15m': timedelta(days=60),
            '30m': timedelta(days=60),
            '1h': timedelta(days=730)
        }

        delta = batch_sizes[interval]
        data_frames = []
        current_start = start
        while current_start < end:
            current_end = min(current_start + delta, end)
            try:
                batch = yf.download(
                    tickers=ticker,
                    start=current_start,
                    end=current_end,
                    interval=interval,
                    progress=False,
                    ignore_tz=True
                )
                if not batch.empty:
                    # Keep only Close price and reset index to get Date
                    batch = batch[['Close']].reset_index()
                    data_frames.append(batch)
            except Exception as e:
                print(f"Error fetching {interval} data for {current_start} to {current_end}: {str(e)}")

            current_start = current_end
            time.sleep(0.5)

        if not data_frames:
            raise ValueError("No data was fetched")

        full_data = pd.concat(data_frames)
    else:
        full_data = yf.download(
            tickers=ticker,
            start=start,
            end=end,
            interval=interval,
            progress=False,
            ignore_tz=True
        )
        # Keep only Close price and reset index to get Date
        full_data = full_data[['Close']].reset_index()

    # Remove duplicates and sort
    full_data = full_data[~full_data['Date'].duplicated(keep='first')]
    full_data = full_data.sort_values('Date')
    
    return full_data[['Date', 'Close']]  # Return only these two columns


@mcp.tool()
def get_current_swap_rate(tokenInaddress, tokenOutaddress, swapamount, targetChain):
    """Fetches the current swap rate between two tokens on KyberSwap's aggregator.
    
    Args:
        tokenInaddress (str): Contract address of the input token (0x... format)
        tokenOutaddress (str): Contract address of the output token (0x... format)
        swapamount (str): Amount of input token to swap (in human-readable units)
        targetChain (str): Chain name where the swap will occur (e.g., "ethereum", "bsc")
        
    Returns:
            - outputAmount (str): Expected output amount in wei
    """

    gettargetPath = f"/{targetChain}/api/v1/routes"
    AggregatorDomain = "https://aggregator-api.kyberswap.com"
    swapamount = Decimal(swapamount)
    amount_in = int(swapamount * (10 ** getDecimals(tokenInaddress)))
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
            rate = int(data['data']['routeSummary']['amountOut'])
            # remove the zeros to make to human readable
            rate_decimals = getDecimals(tokenOutaddress)
            human_readable_rate = rate / (10 ** rate_decimals)
            return human_readable_rate
    
    except requests.exceptions.RequestException as error:
        print('Error:', error.response.text if error.response else str(error))


@mcp.tool()
def perform_condition_Token_swap(tokenInaddress, tokenOutaddress, minPrice, swapamount, targetChain, tokenInDemical, slippage):
    """This tool executes token swaps when the desired miniumum price is reached , 
    only used when there is a given price target/ minimum price to be swapped
    
    Args:
        tokenInaddress: Contract address of the token to swap from (use 0xEee...EEeE for native ETH)
        Example: "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
        
        tokenOutaddress: Contract address of the token to receive
        Example: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
        
        minPrice: Minimum acceptable output amount (in token's smallest units)
        Example: 1620000 (for 1.62 USDC)
        
        swapamount: Amount of input token to swap (in human-readable units)
        Example: 0.001 (for 0.001 ETH)
        
        targetChain: Blockchain network ID (lowercase)
        Example: "base" or "arbitrum"
        
        slippage: Slippage tolerance in basis points (100 = 1%)
        Example: 100

    Returns:
        dict: Swap transaction details when successful, None if conditions not met
        Example Response: {
            "routerAddress": "0x...",
            "data": "0x...",
            "amountIn": "1000000"
        }
        Example Error: None
    """
    minPrice = int(minPrice)
    swapamount = Decimal(swapamount)
    tokenInDemical= int(tokenInDemical)
    slippage = int(slippage)

    AggregatorDomain = "https://aggregator-api.kyberswap.com"
    gettargetPath = f"/{targetChain}/api/v1/routes"
    posttargetPath = f"/{targetChain}/api/v1/route/build"
    
    # Swap parameters
    POLL_INTERVAL = 2  
    max_attempts = 100 
    
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
                        "sender": getSignerAddress(),
                        "recipient": getSignerAddress(),
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
        dict: Swap transaction data containing:
            - 'routerAddress' (str): KyberSwap router contract address
            - 'data' (str): Encoded transaction calldata
            - 'amountIn' (str): Input amount in wei
            - 'amountOut' (str): Minimum expected output in wei
            - 'gasPrice' (str): Recommended gas price
            - 'gasLimit' (str): Estimated gas limit
    
    Example:
        >>> perform_token_swap(
        ...     "0xeeee...", 
        ...     "0xusdc...", 
        ...     1.0, 
        ...     "ethereum", 
        ...     18, 
        ...     0.5
        ... )
    """

    AggregatorDomain = "https://aggregator-api.kyberswap.com"
    gettargetPath = f"/{targetChain}/api/v1/routes"
    posttargetPath = f"/{targetChain}/api/v1/route/build"
    amount_in = int(Decimal(swapamount) * (10 ** getDecimals(tokenInaddress)))

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
                        "sender": getSignerAddress(),
                        "recipient": getSignerAddress(),
                        "slippageTolerance": slippage
                    },
                    timeout=10
                )
        swap_response.raise_for_status()
        swap_data = swap_response.json()
        print("Swap transaction built successfully!")
        return swap_data['data']

    except requests.exceptions.RequestException as error:
            return str(error)


@mcp.tool()
def place_limit_order(tokenInaddress, tokenOutaddress, AmountIn, AmountOut, ChainID):
    """Creates a limit order.
    
    Args:
        tokenInaddress (str): Maker token contract address.
        tokenOutaddress (str): Taker token contract address.
        AmountIn (float): Maker token amount (human-readable units).
        AmountOut (float): Minimum taker token amount to receive (human-readable units).
        ChainID (int): Blockchain network ID (e.g., 1 for Ethereum).
    
    Returns:
        dict: EIP-712 signature data containing:
            - 'domain' (dict): EIP-712 domain separator
            - 'types' (dict): Type definitions for signing
            - 'message' (dict): Order parameters including:
                * 'makerAsset' (str)
                * 'takerAsset' (str)
                * 'makingAmount' (str)
                * 'takingAmount' (str)
                * 'expiredAt' (int)
    Note:
        The actual order submission requires:
        1. Signing the returned data with a wallet
        2. POSTing to KyberSwap's order endpoint
    
    Example:
        >>> limit_order(
        ...     "0xeth...", 
        ...     "0xusdt...", 
        ...     1.0, 
        ...     1800.0, 
        ...     1
        ... )
    """

    AmountIn = Decimal(AmountIn)
    AmountOut = Decimal(AmountOut)
    makingAmount = str(int(AmountIn * (10 ** 18)))
    takingAmount = str(int(AmountOut * (10 ** 6)))

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
                "expiredAt": int(time.time()) + 3600  # Expires in 1 hour
            })
        )
        response.raise_for_status()
        signdata = response.json()
        print('Response:', signdata)    
        return signdata
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


if __name__ == "__main__":
    mcp.run(transport='stdio')