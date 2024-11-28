import json
import logging
from logzero import logger
from channels.generic.websocket import AsyncWebsocketConsumer
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from SmartApi import SmartConnect
import uuid
import pyotp
import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from SmartApi.smartWebSocketV2 import SmartWebSocketV2


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


correlation_id="abc123"
mode = 1  

class StockTradingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = "stocks"
        self.room_group_name = f"stock_{self.room_name}"
        self.exchange_type = int(self.scope["url_route"]["kwargs"].get("exchange_type", 1))  # Default to 1
        self.symbol_token = self.scope["url_route"]["kwargs"].get("symbol_token", "default_token")

        self.token_list = [{
                "exchangeType": self.exchange_type,
                "tokens": [self.symbol_token]
            }]

        # Accept the WebSocket connection
        await self.accept()

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

    def on_data(self, wsapp, message):
        logger.info(f"Live stock data received: {message}")
        
        # Add logging to verify data reception
        print(f"Received data: {message}")  # Debugging line

        # Forward the data received from the external WebSocket to the client
        self.send(text_data=json.dumps({
            'message': message  # Send the live data as it is
        }))

    def on_error(self, wsapp, error):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, wsapp):
        logger.info("WebSocket connection closed.")

    async def disconnect(self, close_code):
        logger.info("WebSocket connection closed.")
        self.sws.close_connection()
