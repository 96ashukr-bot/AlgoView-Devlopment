import asyncio
import json
import logging
# from logzero import logger
import logging

import requests
logger = logging.getLogger('main')
from channels.generic.websocket import AsyncWebsocketConsumer
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from SmartApi import SmartConnect
import pyotp
from urllib.parse import parse_qs

# Smart API credentials
# API_KEY = 'FNqcDPCk'#'Xp6znI3s'
# USERNAME = 'A1420760'
# TOTP_SECRET= "7DFMHZE3BDRCIHMLFT4N3QVCPU"
# PASSWORD="1986"
API_KEY = 'StvD7EVL'  
USERNAME = 'AAAB519761'  
PASSWORD = '1234' 
TOTP_SECRET = "RFFORAS7ASFH7KIZWD7FCSVK2Y" 
obj = SmartConnect(api_key=API_KEY)
totp = pyotp.TOTP(TOTP_SECRET).now()
data = obj.generateSession(USERNAME, PASSWORD, totp)
feedToken = obj.getfeedToken()
FEED_TOKEN = feedToken
AUTH_TOKEN = data['data']['refreshToken']

correlation_id = "abc123"
mode = 3#1  # Subscription mode

class StockTradingConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_prices = {}  # Dictionary to store last known prices for tokens

    async def connect(self):
        # Handle default values for query parameters
        query_params = parse_qs(self.scope['query_string'].decode())
        
        self.exchange_type = int(query_params.get("exchange_type", [1])[0])  # Default to 1 if not provided
        self.symbol_tokens = query_params.get("symbol_tokens", [""])[0].split(",")  # Expecting a comma-separated list
        
        # Prepare token list for subscription
        self.token_list = [{
            "exchangeType": self.exchange_type,
            "tokens": self.symbol_tokens
        }]

        # Log the received parameters (optional but useful for debugging)
        print(f"Exchange Type: {self.exchange_type}")
        print(f"Symbol Tokens: {self.symbol_tokens}")

        # Accept the WebSocket connection
        await self.accept()

        # Store the current event loop
        self.event_loop = asyncio.get_event_loop()

        # Initialize WebSocket and subscribe
        self.sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, USERNAME, FEED_TOKEN)
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close

        # Start the WebSocket connection in a separate thread
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self.sws.connect)

    def on_open(self, wsapp):
        logger.info("WebSocket connection established.")
        self.sws.subscribe(correlation_id, mode, self.token_list)
    def on_data(self, wsapp, message, *args):
        """
        Called when data is received from the external WebSocket.
        """
        try:
            tick_data = message
            print("tick_data>>>>>>>>>>>>", tick_data)

            # Extract and validate data
            current_price = tick_data.get('last_traded_price')
            close_price = tick_data.get('closed_price')  # Use the correct key for "close"

            # Check if any critical data is missing
            if current_price is None or close_price is None:
                logger.error(f"Missing critical data: {tick_data}")
                return

            # Convert prices to float
            current_price = current_price / 100.0
            close_price = close_price / 100.0

            # Calculate difference and percentage
            difference = current_price - close_price
            percentage = (difference / close_price) * 100

            # Determine trend symbol
            trend_symbol = "+" if difference > 0 else "-"

            # Format the result
            formatted_price = f"{current_price:,.2f}"
            formatted_difference = f"{trend_symbol}{abs(difference):,.2f}"
            formatted_percentage = f"({trend_symbol}{abs(percentage):.2f}%)"

            # Combined formatted string
            output = f"{formatted_price} {formatted_difference} {formatted_percentage}"

            # Update last known price for trend tracking
            token = tick_data.get("token", "unknown")
            self.last_prices[token] = current_price

            # Schedule the coroutine to send data to the WebSocket client
            asyncio.run_coroutine_threadsafe(
                self.send(text_data=json.dumps({
                    "token": token,
                    "price": formatted_price,
                    "trend": trend_symbol,
                    "difference": formatted_difference,
                    "percentage": formatted_percentage,
                    "close": close_price,
                })),
                self.event_loop
            )
            # logger.info(f"Token {token}: {output} sent to client.")
        except Exception as e:
            logger.error(f"Error processing data: {e}")

    def on_error(self, wsapp, error, *args):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, wsapp, close_status_code, close_msg, *args):
        logger.info(f"WebSocket connection closed. Status code: {close_status_code}, Message: {close_msg}")

    async def disconnect(self, close_code):
        logger.info("WebSocket connection closed.")
        self.sws.close_connection()

from urllib.parse import parse_qs  # For parsing the query string

class StockChainConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_prices = {}  # Dictionary to store last known prices for tokens
        self.token_to_symbol = {}  # Dictionary to store token to symbol mapping
        self.token_to_strike_price = {}
        self.symbol_name = None  # Variable to store the symbol name from query params

    async def connect(self):
        # Parse query string to get the 'name' parameter
        query_params = parse_qs(self.scope['query_string'].decode('utf-8'))
        self.symbol_name = query_params.get('name', [None])[0]  # Extract the 'name' parameter
        
        if not self.symbol_name:
            # Close the connection if 'name' parameter is missing
            await self.close(code=4001)
            return

        logger.info(f"Requested symbol: {self.symbol_name}")

        # Fetch tokens for the requested symbol
        tokens = await self.get_symbol_tokens(self.symbol_name)
        if not tokens:
            # Close the connection if no tokens are found
            await self.close(code=4002)
            return

        # Prepare token list for subscription
        self.token_list = [{
            "exchangeType": 2,  # NFO exchange type
            "tokens": tokens  # Tokens for the requested symbol
        }]
        logger.info(f"Fetched tokens for {self.symbol_name}: {tokens}")

        # Accept the WebSocket connection
        await self.accept()

        # Store the current event loop
        self.event_loop = asyncio.get_event_loop()

        # Initialize WebSocket and subscribe
        self.sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, USERNAME, FEED_TOKEN)
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close

        # Start the WebSocket connection in a separate thread
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self.sws.connect)

    async def get_symbol_tokens(self, symbol_name):
        """Fetch and filter tokens for the requested symbol from the Master API."""
        try:
            url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
            response = requests.get(url)
            data = response.json()

            # Filter tokens for the requested symbol
            token_to_symbol = {}
            token_to_strike_price = {}

            for entry in data:
                if entry.get('exch_seg') == 'NFO' and entry.get('name') == symbol_name.upper():
                    token = entry['token']
                    symbol = entry['symbol']
                    strike_price = entry['strike']

                    token_to_symbol[token] = symbol
                    token_to_strike_price[token] = strike_price

            # Store the dictionaries in instance variables
            self.token_to_symbol = token_to_symbol
            self.token_to_strike_price = token_to_strike_price

            logger.info(f"Token to Symbol Mapping: {self.token_to_symbol}")
            logger.info(f"Token to Strike Price Mapping: {self.token_to_strike_price}")

            return list(token_to_symbol.keys())  # Return just the tokens for subscription
        except Exception as e:
            logger.error(f"Error fetching tokens for symbol {symbol_name}: {e}")
            return []

    def on_open(self, wsapp):
        logger.info("WebSocket connection established.")
        # Subscribe to tokens for the requested symbol
        self.sws.subscribe(correlation_id, mode, self.token_list)

    def on_data(self, wsapp, message, *args):
        """Process incoming data and filter by token."""
        try:
            tick_data = message
            # print("data of option chain----", tick_data)  # Log the tick data to inspect its structure

            if 'subscription_mode' in tick_data:
                current_price = tick_data['last_traded_price'] / 100.0
                token = tick_data.get("token")
                volume = tick_data.get("volume_trade_for_the_day")
                closeprice = tick_data.get("closed_price") / 100.0
                point = closeprice - current_price
                price_trend = "+" if current_price > closeprice else "-"
                self.last_prices[token] = current_price  # Update last known price

                # Retrieve symbol and strike price using token mappings
                symbol = self.token_to_symbol.get(token, "Unknown Symbol")
                strike_price = self.token_to_strike_price.get(token, "Unknown Strike Price")

                # Determine option category (CE or PE)
                category = "CE" if "CE" in symbol else "PE" if "PE" in symbol else "Unknown"

                # Send data to the WebSocket client
                asyncio.run_coroutine_threadsafe(
                    self.send(text_data=json.dumps({
                        "token": token,
                        "Ltp": f"{current_price:.4f}",
                        "_": price_trend,
                        "close": closeprice,
                        "strike_price": strike_price,
                        "volume": volume,
                        "symbol": symbol,
                        "category": category,
                        "points": point,
                        "tick_data":tick_data
                    })),
                    self.event_loop
                )

                logger.info(
                    f"Token {token}: Price {current_price:.4f} ({price_trend}), Symbol: {symbol}, Volume: {volume}, Strike Price: {strike_price}"
                )
        except Exception as e:
            logger.error(f"Error processing data: {e}")

    def on_error(self, wsapp, error, *args):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, wsapp, close_status_code, close_msg, *args):
        logger.info(f"WebSocket connection closed. Status code: {close_status_code}, Message: {close_msg}")

    async def disconnect(self, close_code):
        logger.info("WebSocket connection closed.")
        self.sws.close_connection()




