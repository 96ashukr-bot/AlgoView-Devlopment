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
API_KEY = 'FNqcDPCk'#'Xp6znI3s'
USERNAME = 'A1420760'
TOTP_SECRET= "7DFMHZE3BDRCIHMLFT4N3QVCPU"
PASSWORD="1986"
# API_KEY = 'StvD7EVL'  
# USERNAME = 'AAAB519761'  
# PASSWORD = '1234' 
# TOTP_SECRET = "RFFORAS7ASFH7KIZWD7FCSVK2Y" 
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
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import requests
import json
import logging

logger = logging.getLogger(__name__)

class StockChainConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_prices = {}
        self.token_to_symbol = {}
        self.token_to_strike_price = {}
        self.token_to_category = {}
        self.symbol_name = None
        self.expiry_date = None
        self.sws = None  # Initialize WebSocket handler to None
        self.event_loop = asyncio.get_event_loop()

    async def connect(self):
        # Parse query string to get the 'name' and 'expiry_date' parameters
        query_params = parse_qs(self.scope['query_string'].decode('utf-8'))
        self.symbol_name = query_params.get('name', [None])[0]
        self.expiry_date = query_params.get('expiry_date', [None])[0]

        if not self.symbol_name or not self.expiry_date:
            await self.close(code=4001)  # Close with error code for missing parameters
            return

        logger.info(f"Requested symbol: {self.symbol_name}, Expiry Date: {self.expiry_date}")

        tokens = await self.get_symbol_tokens(self.symbol_name, self.expiry_date)
        if not tokens:
            await self.close(code=4002)  # Close with error code for no tokens found
            return

        self.token_list = [{
            "exchangeType": 2,  # NFO exchange type
            "tokens": tokens
        }]

        logger.info(f"Fetched tokens for {self.symbol_name}: {tokens}")
        await self.accept()

        # Initialize and connect the SmartWebSocket
        self.sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, USERNAME, FEED_TOKEN)
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close

        # Run the WebSocket connection in a separate thread
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self.sws.connect)

    async def get_symbol_tokens(self, symbol_name, expiry_date):
        try:
            url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()

            token_to_symbol = {}
            token_to_strike_price = {}
            token_to_category = {}

            for entry in data:
                # logger.info(f"Processing entry: {entry}")
               if (entry.get('exch_seg') == 'NFO' and entry.get('name') == symbol_name.upper() and entry.get('expiry').upper() == expiry_date.upper()):
                    print("dataaaa>>")
                    token = entry['token']
                    symbol = entry['symbol']
                    strike_price = entry['strike']
                    category = 'CE' if 'CE' in symbol else 'PE' if 'PE' in symbol else 'Unknown'
             
                    token_to_symbol[token] = symbol
                    token_to_strike_price[token] = strike_price
                    token_to_category[token] = category

            self.token_to_symbol = token_to_symbol
            self.token_to_strike_price = token_to_strike_price
            self.token_to_category = token_to_category

            logger.info(f"Token to Symbol Mapping: {self.token_to_symbol}")
            logger.info(f"Token to Strike Price Mapping: {self.token_to_strike_price}")
            logger.info(f"Token to Category Mapping: {self.token_to_category}")

            return list(token_to_symbol.keys())
        except requests.RequestException as e:
            logger.error(f"Error fetching tokens for symbol {symbol_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    def on_open(self, wsapp):
        logger.info("WebSocket connection established.")
        if not self.token_list:
            logger.error("No tokens to subscribe to!")
            return
        self.sws.subscribe(correlation_id, mode, self.token_list)


    def on_data(self, wsapp, message, *args):
        try:
            # Check if the message is already a dictionary
            if isinstance(message, dict):
                tick_data = message  # If it's already a dict, no need to parse
            else:
                tick_data = json.loads(message)  # Parse it as JSON if it's not a dict

            token = tick_data.get("token")
            current_price = tick_data.get('last_traded_price', 0) / 100.0
            volume = tick_data.get("volume_trade_for_the_day", 0)
            close_price = tick_data.get("closed_price", 0) / 100.0

            symbol = self.token_to_symbol.get(token, "Unknown Symbol")
            strike_price = self.token_to_strike_price.get(token, "Unknown Strike Price")
            category = self.token_to_category.get(token, "Unknown")
            
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

            if category not in ["CE", "PE"]:
                return

            asyncio.run_coroutine_threadsafe(
                self.send(text_data=json.dumps({
                    "symbol": symbol,
                    "strike_price": strike_price,
                    "ltp": f"{current_price:.2f}",
                    "volume": volume,
                    "category": category,
                    "formatted_difference":formatted_difference,
                    "formatted_percentage":formatted_percentage,
                    "close_price":close_price
                    
                })),
                self.event_loop
            )

            logger.info(
                f"Token {token}: Symbol {symbol}, Strike Price {strike_price}, LTP {current_price:.2f}, Volume {volume}, Category {category}"
            )
            # await asyncio.sleep(4)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON data: {e}")
        except Exception as e:
            logger.error(f"Error processing data: {e}")

    def on_error(self, wsapp, error, *args):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, wsapp, close_status_code, close_msg, *args):
        logger.info(f"WebSocket connection closed. Status code: {close_status_code}, Message: {close_msg}")

    async def disconnect(self, close_code):
        logger.info("WebSocket connection closed.")
        self.sws.close_connection()




