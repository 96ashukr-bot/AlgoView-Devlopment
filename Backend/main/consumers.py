import asyncio
import json
import logging
from logzero import logger
from channels.generic.websocket import AsyncWebsocketConsumer
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from SmartApi import SmartConnect
import pyotp


# Smart API credentials
API_KEY = 'Xp6znI3s'
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
mode = 1  # Subscription mode


class StockTradingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = "stocks"
        self.room_group_name = f"stock_{self.room_name}"
        self.exchange_type = int(self.scope["url_route"]["kwargs"].get("exchange_type", 1))  # Default to 1
        self.symbol_tokens = self.scope["url_route"]["kwargs"].get("symbol_tokens", "").split(",")  # Token list

        # Prepare the token list for subscription
        self.token_list = [{
            "exchangeType": self.exchange_type,
            "tokens": self.symbol_tokens
        }]

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

            if 'subscription_mode' in tick_data:
                price = tick_data['last_traded_price'] / 100.0
                token = tick_data.get("token")

                # Schedule the coroutine to send data to the WebSocket client
                asyncio.run_coroutine_threadsafe(
                    self.send(text_data=json.dumps({
                        "token": token,
                        "price": f"{price:.4f}",
                        "exchange_type": tick_data['exchange_type'],
                        "subscription_mode": tick_data['subscription_mode']
                    })),
                    self.event_loop  # Use the stored event loop
                )
                logger.info(f"Token {token}: Price {price:.4f} sent to client.")
        except Exception as e:
            logger.error(f"Error processing data: {e}")

    def on_error(self, wsapp, error, *args):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, wsapp, close_status_code, close_msg, *args):
        logger.info(f"WebSocket connection closed. Status code: {close_status_code}, Message: {close_msg}")

    async def disconnect(self, close_code):
        logger.info("WebSocket connection closed.")
        self.sws.close_connection()
