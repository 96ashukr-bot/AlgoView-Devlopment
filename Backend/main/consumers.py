import asyncio
import json
import logging
from logzero import logger
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

    def on_data111(self, wsapp, message, *args):
        """
        Called when data is received from the external WebSocket.
        """
        try:
            tick_data = message
            print("tick_data>>>>>>>>>>>>",tick_data)
            
            if 'subscription_mode' in tick_data:
                current_price = tick_data['last_traded_price'] / 100.0
                token = tick_data.get("token")
                exchange_type = tick_data.get("exchange_type")
                subscription_mode = tick_data.get("subscription_mode")
                closeprice=tick_data.get("closed_price")/100.0
                last_price = self.last_prices.get(token, None)
                price_trend = "+" if last_price is None or current_price > last_price else "-"
                self.last_prices[token] = current_price  # Update last known price
                
                # Schedule the coroutine to send data to the WebSocket client
                asyncio.run_coroutine_threadsafe(
                    self.send(text_data=json.dumps({
                        "token": token,
                        "price": f"{current_price:.4f}",
                        "_": price_trend,
                        "close":closeprice,
                        "exchange_type": exchange_type,
                        "subscription_mode": subscription_mode,
                        "indices_diffrence":current_price-closeprice,
                        "percentage":((current_price -closeprice) /closeprice) * 100
                    })),
                    self.event_loop  # Use the stored event loop
                )
                logger.info(f"Token {token}: Price {current_price:.4f} ({price_trend}) sent to client.  closeprice:{closeprice},    difference:{current_price-closeprice}")

        except Exception as e:
            logger.error(f"Error processing data: {e}")
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
            logger.info(f"Token {token}: {output} sent to client.")
        except Exception as e:
            logger.error(f"Error processing data: {e}")

    def on_error(self, wsapp, error, *args):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, wsapp, close_status_code, close_msg, *args):
        logger.info(f"WebSocket connection closed. Status code: {close_status_code}, Message: {close_msg}")

    async def disconnect(self, close_code):
        logger.info("WebSocket connection closed.")
        self.sws.close_connection()



class OptionChainConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_prices = {}  # Dictionary to store last known prices for tokens

    async def connect(self):
        # Extract query parameters from the WebSocket connection URL
        query_params = parse_qs(self.scope['query_string'].decode())
        
        # Extract 'symbol' parameter, defaulting to 'NIFTY' if not provided
        self.symbol = query_params.get("symbol", ["NIFTY"])[0]  # Default symbol is 'NIFTY'
        
        # Initialize WebSocket and subscribe to the symbol
        self.token_list = [{
            "exchangeType": 1,  # Assuming exchange type is 1 for NIFTY
            "tokens": [self.symbol]  # Use the symbol from query parameter
        }]
        
        # Log the symbol (optional for debugging)
        print(f"Subscribing to symbol: {self.symbol}")
        
        # Accept the WebSocket connection
        await self.accept()

        # Store the current event loop
        self.event_loop = asyncio.get_event_loop()

        # Initialize the SmartWebSocketV2 object and subscribe
        self.sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, USERNAME, FEED_TOKEN)
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close

        # Start WebSocket connection in a separate thread
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self.sws.connect)

    def on_open(self, wsapp):
        logger.info("WebSocket connection established.")
        self.sws.subscribe(correlation_id, mode, self.token_list)

    def on_data(self, wsapp, message, *args):
        try:
            tick_data = message
            print("tick_data >>>>>>>>>>>>>", tick_data)

            current_price = tick_data.get('last_traded_price')
            close_price = tick_data.get('closed_price')

            if current_price is None or close_price is None:
                logger.error(f"Missing critical data: {tick_data}")
                return

            # Process price data
            current_price = current_price / 100.0
            close_price = close_price / 100.0
            difference = current_price - close_price
            percentage = (difference / close_price) * 100
            trend_symbol = "+" if difference > 0 else "-"

            formatted_price = f"{current_price:,.2f}"
            formatted_difference = f"{trend_symbol}{abs(difference):,.2f}"
            formatted_percentage = f"({trend_symbol}{abs(percentage):.2f}%)"

            token = tick_data.get("token", "unknown")
            self.last_prices[token] = current_price

            # Send the data to the WebSocket client
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
            logger.info(f"Token {token}: {formatted_price} {formatted_difference} {formatted_percentage} sent to client.")
        except Exception as e:
            logger.error(f"Error processing data: {e}")

    def on_error(self, wsapp, error, *args):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, wsapp, close_status_code, close_msg, *args):
        logger.info(f"WebSocket connection closed. Status code: {close_status_code}, Message: {close_msg}")

    async def disconnect(self, close_code):
        logger.info("WebSocket connection closed.")
        self.sws.close_connection()