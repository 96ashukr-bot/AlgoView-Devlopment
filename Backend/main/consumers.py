
# logger = logging.getLogger(__name__)
# API_KEY = 'Xp6znI3s'  
# USERNAME = 'AAAB519761'  
# PASSWORD = '1234' 
# Totp = "RFFORAS7ASFH7KIZWD7FCSVK2Y" 

# Smart API credentials
# API_KEY = 'StvD7EVL'  
# USERNAME = 'AAAB519761'  
# PASSWORD = '1234' 
# TOTP_SECRET = "RFFORAS7ASFH7KIZWD7FCSVK2Y" 

import asyncio
import csv
from datetime import datetime
import json
import logging
import requests
from channels.generic.websocket import AsyncWebsocketConsumer
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
# from SmartApi import SmartConnect
import pyotp
from urllib.parse import parse_qs

logger = logging.getLogger('main')
API_KEY = 'MYRms9xx'  
USERNAME = 'AAAB519761'  
PASSWORD = '1234' 
TOTP_SECRET = "RFFORAS7ASFH7KIZWD7FCSVK2Y" 
# Smart API credentials
#API_KEY = 'FNqcDPCk'
#USERNAME = 'A1420760'
#TOTP_SECRET = "7DFMHZE3BDRCIHMLFT4N3QVCPU"
#PASSWORD = "1986"
# access_token="eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0NkI0VVIiLCJqdGkiOiI2N2Q3ZGMyMmY0MWFkYjFmZDI2ZWQ3YjYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzQyMTk5ODQyLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDIyNDg4MDB9.vkQM6agFoNT-CbdxUB-jTSNpSjASh-pg6X57gls3p2M"
# obj = SmartConnect(api_key=API_KEY)
# totp = pyotp.TOTP(TOTP_SECRET).now()
# data = obj.generateSession(USERNAME, PASSWORD, totp)
# feedToken = obj.getfeedToken()
# FEED_TOKEN = feedToken
# AUTH_TOKEN = data['data']['refreshToken']
correlation_id = "abc123"
mode = 3  # Subscription mode
import json
import ssl
import upstox_client
import websockets
from google.protobuf.json_format import MessageToDict
from main import MarketDataFeed_pb2 as pb
from asgiref.sync import sync_to_async
import os

class UpstoxChainLiveSymbolConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from main.models import WebsocketDetails

        # Auth token from DB
        websocket_details = await sync_to_async(WebsocketDetails.objects.latest)('id')
        access_token = websocket_details.Auth_token
        # Parse query parameters and split by comma.
        query_params = parse_qs(self.scope["query_string"].decode())
        self.symbol_names = query_params.get("name", [None])[0].split(",")
        logger.info(f"Received symbol names: {self.symbol_names}")

        if not self.symbol_names:
            await self.close()
            return

        # Instance variables per connection.
        self.token_to_symbol = {}
        self.token_to_strike_price = {}
        self.token_to_category = {}
        self.reverse_instrument_map = {}
        self.last_prices = {}

        # Load CSV instrument keys using a background thread.
        self.instrument_keys = await asyncio.to_thread(
            
            self.get_instrument_keys_from_csv, self.symbol_names
        )
        if not self.instrument_keys:
            await self.close()
            return

        # Accept the WebSocket connection.
        await self.accept()

        # Upstox configuration.
        self.api_version = '2.0'
        self.configuration = upstox_client.Configuration()
        self.configuration.access_token = access_token

        # Start the market data feed in an asynchronous task.
        asyncio.create_task(self.fetch_market_data())

    async def disconnect(self, close_code):
        logger.info("WebSocket disconnected")

    def get_instrument_keys_from_csv(self, names):
        """
        Reads the CSV file and collects instrument keys that match any of the provided names.
        Adjust the matching logic if you prefer substring matching.
        """
        instrument_keys = []
        # Build an absolute path to ensure robustness.
        csv_path = "main/complete.csv"
        try:
            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # For more flexible matching, you could do:
                    # for name in names:
                    #     if name.upper() in row["name"].upper():
                    #         ... (process and break)
                    if row["name"] in names:
                        token = row["exchange_token"]
                        instrument_key = row["instrument_key"]
                        self.token_to_symbol[token] = row["tradingsymbol"]
                        self.token_to_strike_price[token] = row["strike"]
                        self.token_to_category[token] = row["option_type"]
                        self.reverse_instrument_map[instrument_key] = token
                        instrument_keys.append(instrument_key)
            logger.info(f"Found {len(instrument_keys)} instrument keys: {instrument_keys}")
            return instrument_keys
        except Exception as e:
            logger.error(f"CSV read error: {e}")
            return []

    def get_market_data_feed_authorize_sync(self):
        """
        Blocking call to authorize and retrieve the feed URI.
        """
        api_instance = upstox_client.WebsocketApi(
            upstox_client.ApiClient(self.configuration)
        )
        return api_instance.get_market_data_feed_authorize(self.api_version)

    def decode_protobuf(self, buffer):
        """
        Decodes the binary feed using protobuf.
        """
        try:
            feed_response = pb.FeedResponse()
            feed_response.ParseFromString(buffer)
            return feed_response
        except Exception as e:
            logger.error(f"Protobuf decode error: {e}")
            return None

    async def subscribe_chunks(self, websocket):
        """
        Schedules all subscription messages concurrently.
        """
        tasks = []
        # Loop through instrument_keys in chunks of 100.
        for i in range(0, len(self.instrument_keys), 100):
            chunk = self.instrument_keys[i:i + 100]
            data = {
                "guid": f"guid-{i}",
                "method": "sub",
                "data": {"mode": "full", "instrumentKeys": chunk}
            }
            # Log subscription data for debugging.
            logger.info(f"Subscribing chunk with keys: {chunk}")
            tasks.append(websocket.send(json.dumps(data).encode("utf-8")))
        await asyncio.gather(*tasks)

    async def fetch_market_data(self):
        # Setup SSL context (adjust as needed).
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Authorize and get the Upstox feed URI by running blocking code in the thread.
        response = await sync_to_async(self.get_market_data_feed_authorize_sync)()
        uri = response.data.authorized_redirect_uri
        logger.info(f"Upstox feed URI: {uri}")

        async with websockets.connect(uri, ssl=ssl_context, max_size=4 * 1024 * 1024) as websocket:
            await asyncio.sleep(1)
            # Subscribe to all instrument keys concurrently.
            await self.subscribe_chunks(websocket)

            # Process incoming messages indefinitely.
            while True:
                try:
                    message = await websocket.recv()
                    decoded = self.decode_protobuf(message)
                    if decoded:
                        data_dict = MessageToDict(decoded)
                        await self.process_market_data(data_dict)
                except websockets.exceptions.ConnectionClosedError as e:
                    logger.warning(f"WebSocket closed: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error in receiving: {e}")
                    await asyncio.sleep(0.05)  # yield control if error occurs

    async def process_market_data(self, tick_data):
        feeds = tick_data.get("feeds", {})
        for token_key, data in feeds.items():
            try:
                # Find the token based on instrument key mapping.
                token = self.reverse_instrument_map.get(token_key, token_key)
                ff = data.get("ff", {})
                market_ff = ff.get("marketFF", {})
                index_ff = ff.get("indexFF", {})
                vol_ff = ff.get("marketOHLC", {})

                # Try to determine last traded price (ltp) and close price.
                ltpc = market_ff.get("ltpc", {}) or index_ff.get("ltpc", {})
                efeed = market_ff.get("eFeedDetails", {}) or index_ff.get("ltpc", {})
                ltp = ltpc.get("ltp") or ltpc.get("cp")
                close = efeed.get("cp")
                volume = vol_ff.get("volume", 0)

                # Skip if data is incomplete.
                if ltp is None or close is None:
                    continue

                ltp = float(ltp)
                close = float(close)
                diff = ltp - close
                percent = (diff / close) * 100

                symbol = self.token_to_symbol.get(token, "")
                strike = self.token_to_strike_price.get(token, "")
                cat = self.token_to_category.get(token, "Unknown")

                # Send data to the connected client.
                await self.send(
                    text_data=json.dumps({
                        "symbol": symbol,
                        "strike_price": strike,
                        "ltp": f"{ltp:,.2f}",
                        "volume": volume,
                        "category": cat,
                        "formatted_difference": f"{'+' if diff > 0 else '-'}{abs(diff):,.2f}",
                        "formatted_percentage": f"({'+' if diff > 0 else '-'}{abs(percent):.2f}%)",
                        "close_price": close
                    })
                )
            except Exception as e:
                logger.error(f"Error processing token {token_key}: {e}")

#live data for trade histoty
class UpstoxMarketDataConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_loop = asyncio.get_event_loop()
    async def connect(self):
        from main.models import WebsocketDetails
        websocket_details = await sync_to_async(WebsocketDetails.objects.latest)('id')
        access_token = websocket_details.Auth_token
        """Connect to WebSocket and accept dynamic instruments"""
        query_params = parse_qs(self.scope["query_string"].decode())
        self.tokens = query_params.get("symbol_tokens", [" "])[0].split(",")
        self.id = query_params.get("id", [" "])[0].split(",")
        self.exchange_type = int(query_params.get("exchange_type", [1])[0])
 
        self.instrument_keys = self.get_instrument_keys_from_csv(self.tokens)
        print(f"Connected with Instruments: {self.instrument_keys}")

        await self.accept()

        self.api_version = '2.0'
        self.configuration = upstox_client.Configuration()
        self.configuration.access_token =access_token
        self.last_prices = {}

        asyncio.create_task(self.fetch_market_data())

    async def disconnect(self, close_code):
        """Handle WebSocket disconnect"""
        print("WebSocket Disconnected")

    def get_market_data_feed_authorize(self):
        """Get authorization for market data feed."""
        api_instance = upstox_client.WebsocketApi(upstox_client.ApiClient(self.configuration))
        return api_instance.get_market_data_feed_authorize(self.api_version)

    def decode_protobuf(self, buffer):
        """Decode Protobuf message"""
        try:
            feed_response = pb.FeedResponse()
            feed_response.ParseFromString(buffer)
            return feed_response
        except Exception as e:
            print(f"Error decoding Protobuf message: {e}")
            return None

    def get_instrument_keys_from_csv(self, tokens):
        """Convert tokens to instrument keys using CSV file"""
        instrument_map = {}
        reverse_map = {} 
        csv_path = "main/complete.csv"
       
        try:
            with open(csv_path, "r") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # print("ttttttttt",row)
                    instrument_map[row["exchange_token"]] = row["instrument_key"]
                    reverse_map[row["instrument_key"]] = row["exchange_token"] 

            self.reverse_instrument_map = reverse_map  

            return [instrument_map[token] for token in tokens if token in instrument_map]
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return []

    async def fetch_market_data(self):
        """Fetch live market data from Upstox WebSocket"""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        response = self.get_market_data_feed_authorize()

        async with websockets.connect(response.data.authorized_redirect_uri, ssl=ssl_context) as websocket:
            print(f'Connected to Upstox WebSocket for Instruments: {self.instrument_keys}')
            
            await asyncio.sleep(1)

            
            data = {
                "guid": "someguid",
                "method": "sub",
                "data": {
                    "mode": "full",
                    "instrumentKeys": self.instrument_keys  
                }
            }

            binary_data = json.dumps(data).encode('utf-8')
            await websocket.send(binary_data)

            while True:
                message = await websocket.recv()
                decoded_data = self.decode_protobuf(message)

                if decoded_data:
                    data_dict = MessageToDict(decoded_data)  
                    await self.process_market_data(data_dict)
                else:
                    print("Failed to decode message, skipping...")

    async def process_market_data(self, tick_data):
        """Process incoming tick data and send structured response"""
        feeds = tick_data.get("feeds", {})

        for token, data in feeds.items():
            try:
                token = self.reverse_instrument_map.get(token, token) 
                ff_data = data.get("ff", {})
                market_ff = ff_data.get("marketFF", {})
                index_ff = ff_data.get("indexFF", {})

                ltpc_data = market_ff.get("ltpc", {}) or index_ff.get("ltpc", {})
                efeed_details = market_ff.get("eFeedDetails", {}) or index_ff.get("ltpc", {})

                current_price = ltpc_data.get("ltp") or ltpc_data.get("cp")
                close_price = efeed_details.get("cp") 

                if current_price is None or close_price is None:
                    print(f"Missing critical data for {token}: {tick_data}")
                    continue

                difference = current_price - close_price
                percentage = (difference / close_price) * 100
                trend_symbol = "+" if difference > 0 else "-"

                formatted_price = f"{current_price:,.2f}"
                formatted_difference = f"{trend_symbol}{abs(difference):,.2f}"
                formatted_percentage = f"({trend_symbol}{abs(percentage):.2f}%)"

                self.last_prices[token] = current_price

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
               

            except Exception as e:
                print(f"Error processing data for {token}: {e}")



class UpstoxChainConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_loop = asyncio.get_event_loop()
        self.token_to_symbol = {}
        self.token_to_strike_price = {}
        self.token_to_category = {}
        self.instrument_keys = []
        self.last_prices = {}
        self.reverse_instrument_map = {}

    async def connect(self):
        from main.models import WebsocketDetails
        websocket_details = await sync_to_async(WebsocketDetails.objects.latest)('id')
        access_token = websocket_details.Auth_token

        """Connect to WebSocket and accept dynamic instruments"""
        query_params = parse_qs(self.scope["query_string"].decode())
        self.symbol_name = query_params.get('name', [None])[0]
        self.expiry_date = query_params.get('expiry_date', [None])[0]

        # Get the instrument keys for the tokens
        self.instrument_keys = self.get_instrument_keys_from_csv(self.symbol_name)

        await self.accept()

       
        self.api_version = '2.0'
        self.configuration = upstox_client.Configuration()
        self.configuration.access_token = access_token
        self.last_prices = {}

        asyncio.create_task(self.fetch_market_data())

    async def disconnect(self, close_code):
        """Handle WebSocket disconnect"""
        logger.info("WebSocket Disconnected from Upstox.")

    def get_market_data_feed_authorize(self):
        """Get authorization for market data feed."""
        api_instance = upstox_client.WebsocketApi(upstox_client.ApiClient(self.configuration))
        return api_instance.get_market_data_feed_authorize(self.api_version)

    def decode_protobuf(self, buffer):
        """Decode Protobuf message"""
        try:
            feed_response = pb.FeedResponse()
            feed_response.ParseFromString(buffer)
            return feed_response
        except Exception as e:
            logger.error(f"Error decoding Protobuf message: {e}")
            return None

    def get_instrument_keys_from_csv(self, name):
        instrument_map = {}
        reverse_map = {}
        strike_price_map = {}
        tradingsymbol_map = {}
        category_map = {}
        #csv_path = "/home/digi2/JYOTIWORKSPACE/AlgoView-Devlopment/Backend/main/complete.csv"
        csv_path = "main/complete.csv"

        try:
            try:
                formatted_expiry_date = datetime.strptime(self.expiry_date, "%d%b%Y").strftime("%Y-%m-%d")
            except ValueError:
                logger.error(f"Invalid expiry date format: {self.expiry_date}")
                return []

            with open(csv_path, "r") as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames

                if "name" not in headers or "tradingsymbol" not in headers or "expiry" not in headers:
                    raise KeyError("Missing required columns ('name', 'tradingsymbol', 'expiry') in CSV file")

                for row in reader:
                    if row["name"] == name and row["expiry"] == formatted_expiry_date:
                        exchange_token = row["exchange_token"]
                        instrument_map[row["exchange_token"]] = row["instrument_key"]
                        reverse_map[row["instrument_key"]] = row["exchange_token"]

                        if "strike" in row:
                            strike_price_map[row["exchange_token"]] = row["strike"]

                        if "tradingsymbol" in row:
                            tradingsymbol_map[row["exchange_token"]] = row["tradingsymbol"]

                        if "option_type" in row:
                            category_map[row["exchange_token"]] = row["option_type"]
                        

            self.reverse_instrument_map = reverse_map
            self.token_to_strike_price = strike_price_map
            self.token_to_symbol = tradingsymbol_map
            self.token_to_category = category_map

            return list(instrument_map.values())
        except KeyError as e:
            logger.error(f"CSV Error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return []

    async def fetch_market_data(self):
            
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        response = self.get_market_data_feed_authorize()

        async with websockets.connect(response.data.authorized_redirect_uri, ssl=ssl_context) as websocket:
           
            
            await asyncio.sleep(1)

            
            data = {
                "guid": "someguid",
                "method": "sub",
                "data": {
                    "mode": "full",
                    "instrumentKeys": self.instrument_keys  
                }
            }

            binary_data = json.dumps(data).encode('utf-8')
            await websocket.send(binary_data)

            while True:
                message = await websocket.recv()
                decoded_data = self.decode_protobuf(message)

                if decoded_data:
                    data_dict = MessageToDict(decoded_data)  
                    await self.process_market_data(data_dict)
                else:
                    print("Failed to decode message, skipping...")

            

    async def process_market_data(self, tick_data):
        feeds = tick_data.get("feeds", {})
      

        for token, data in feeds.items():
            try:
                token = self.reverse_instrument_map.get(token, token)
                ff_data = data.get("ff", {})
                market_ff = ff_data.get("marketFF", {})
                index_ff = ff_data.get("indexFF", {})
                vol_ff=ff_data.get("marketOHLC", {})
                ltpc_data = market_ff.get("ltpc", {}) or index_ff.get("ltpc", {})
                efeed_details = market_ff.get("eFeedDetails", {}) or index_ff.get("ltpc", {})
                current_price = ltpc_data.get("ltp") or ltpc_data.get("cp")
                volume = vol_ff.get("volume", 0)
                close_price = efeed_details.get("cp")

                symbol = self.token_to_symbol.get(token, " ")
                strike_price = self.token_to_strike_price.get(token, " ")
                category = self.token_to_category.get(token, "Unknown")

                if current_price is None or close_price is None:
                    return

                current_price = current_price 
                close_price = close_price

                difference = current_price - close_price
                percentage = (difference / close_price) * 100
                trend_symbol = "+" if difference > 0 else "-"

                formatted_price = f"{current_price:,.2f}"
                formatted_difference = f"{trend_symbol}{abs(difference):,.2f}"
                formatted_percentage = f"({trend_symbol}{abs(percentage):.2f}%)"
                
                self.last_prices[token] = current_price

                asyncio.run_coroutine_threadsafe(
                self.send(text_data=json.dumps({
                    "symbol": symbol,
                    "strike_price": strike_price,
                    "ltp": formatted_price,
                    "volume": volume,
                    "category": category,
                    "formatted_difference": formatted_difference,
                    "formatted_percentage": formatted_percentage,
                    "close_price": close_price
                })),
                self.event_loop
            )
            except Exception as e:
                print(f"Error processing data for {token}: {e}")
class StockTradingConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_prices = {}
        self.sws = None
        self.event_loop = asyncio.get_event_loop()

    async def connect(self):
        query_params = parse_qs(self.scope['query_string'].decode())
        self.exchange_type = int(query_params.get("exchange_type", [1])[0])
        self.symbol_tokens = query_params.get("symbol_tokens", [""])[0].split(",")
        self.token_list = [{"exchangeType": self.exchange_type, "tokens": self.symbol_tokens}]

        await self.accept()

        self.sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, USERNAME, FEED_TOKEN)
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close

        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self.sws.connect)

    def on_open(self, wsapp):
        logger.info("WebSocket connection established for stock live data.")
        self.sws.subscribe(correlation_id, mode, self.token_list)

    def on_data(self, wsapp, message, *args):
        try:
            tick_data = message
            current_price = tick_data.get('last_traded_price')
            close_price = tick_data.get('closed_price')

            if current_price is None or close_price is None:
                logger.error(f"Missing critical data: {tick_data}")
                return

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
            logger.info("live data market********************")
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
        except Exception as e:
            logger.error(f"Error processing data: {e}")

    def on_error(self, wsapp, error, *args):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, wsapp, *args):
        logger.info("WebSocket connection closed for stock live data. Cleaning up resources.")
        if self.sws is not None:
            self.sws.close_connection()
            self.sws = None

    async def disconnect(self, close_code):
        logger.info("WebSocket connection closed.")
        if hasattr(self, "sws") and self.sws is not None:
            logger.info("Closing SmartWebSocketV2 connection...stock live data....")
            self.sws.close_connection()
            self.sws = None

class StockChainConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_prices = {}
        self.token_to_symbol = {}
        self.token_to_strike_price = {}
        self.token_to_category = {}
        self.symbol_name = None
        self.expiry_date = None
        self.sws = None
        self.event_loop = asyncio.get_event_loop()

    async def connect(self):
        query_params = parse_qs(self.scope['query_string'].decode('utf-8'))
        self.symbol_name = query_params.get('name', [None])[0]
        self.expiry_date = query_params.get('expiry_date', [None])[0]

        if not self.symbol_name:
            await self.close(code=4001)
            return

        logger.info(f"Requested symbol: {self.symbol_name}, Expiry Date: {self.expiry_date or 'ALL DATES'}")

        tokens = await self.get_symbol_tokens(self.symbol_name, self.expiry_date)
        if not tokens:
            await self.close(code=4002)
            return

        self.token_list = [{"exchangeType": 2, "tokens": tokens}]
        await self.accept()

        self.sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, USERNAME, FEED_TOKEN)
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close

        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self.sws.connect)

    async def get_symbol_tokens(self, symbol_name, expiry_date):
        try:
            url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            token_to_symbol = {}
            token_to_strike_price = {}
            token_to_category = {}

            for entry in data:
                if entry.get('exch_seg') == 'NFO' and entry.get('name') == symbol_name.upper():
                    if expiry_date and entry.get('expiry').upper() != expiry_date.upper():
                        continue

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

            return list(token_to_symbol.keys())
        except requests.RequestException as e:
            logger.error(f"Error fetching tokens for symbol {symbol_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []

    def on_open(self, wsapp):
        logger.info("WebSocket connection established. for option chain......")
        if not self.token_list:
            logger.error("No tokens to subscribe to!")
            return
        self.sws.subscribe(correlation_id, mode, self.token_list)

    def on_data(self, wsapp, message, *args):
        try:
            tick_data = message if isinstance(message, dict) else json.loads(message)
            token = tick_data.get("token")
            current_price = tick_data.get('last_traded_price', 0) / 100.0
            volume = tick_data.get("volume_trade_for_the_day", 0)
            close_price = tick_data.get("closed_price", 0) / 100.0

            symbol = self.token_to_symbol.get(token, "Unknown Symbol")
            strike_price = self.token_to_strike_price.get(token, "Unknown Strike Price")
            category = self.token_to_category.get(token, "Unknown")

            if current_price is None or close_price is None:
                logger.error(f"Missing critical data: {tick_data}")
                return

            current_price = current_price / 100.0
            close_price = close_price / 100.0

            difference = current_price - close_price
            percentage = (difference / close_price) * 100
            trend_symbol = "+" if difference > 0 else "-"

            formatted_price = f"{current_price:,.2f}"
            formatted_difference = f"{trend_symbol}{abs(difference):,.2f}"
            formatted_percentage = f"({trend_symbol}{abs(percentage):.2f}%)"

            if category not in ["CE", "PE"]:
                return
            logger.info("option chain data::::::::::::")
            asyncio.run_coroutine_threadsafe(
                self.send(text_data=json.dumps({
                    "symbol": symbol,
                    "strike_price": strike_price,
                    "ltp": f"{current_price:.2f}",
                    "volume": volume,
                    "category": category,
                    "formatted_difference": formatted_difference,
                    "formatted_percentage": formatted_percentage,
                    "close_price": close_price
                })),
                self.event_loop
            )
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON data: {e}")
        except Exception as e:
            logger.error(f"Error processing data: {e}")

    def on_error(self, wsapp, error, *args):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, wsapp, close_status_code, close_msg, *args):
        logger.info(f"WebSocket connection closed for option chain... Status code: {close_status_code}, Message: {close_msg}")

    async def disconnect(self, close_code):
        logger.info("WebSocket connection closed.for option chain....")
        if hasattr(self, "sws") and self.sws is not None:
            self.sws.close_connection()
            self.sws = None











class StockTradingConsumertttttttt(AsyncWebsocketConsumer):
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
        

class StockChainConsumerwwwwwwwwwwwwww(AsyncWebsocketConsumer):
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

        if not self.symbol_name:
            await self.close(code=4001)  # Close with error code for missing symbol parameter
            return

        logger.info(f"Requested symbol: {self.symbol_name}, Expiry Date: {self.expiry_date or 'ALL DATES'}")

        tokens = await self.get_symbol_tokens(self.symbol_name, self.expiry_date)
        if not tokens:
            await self.close(code=4002)  # Close with error code for no tokens found
            return

        self.token_list = [{
            "exchangeType": 2,  # NFO exchange type
            "tokens": tokens
        }]

        # logger.info(f"Fetched tokens for {self.symbol_name}: {tokens}")
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
                if entry.get('exch_seg') == 'NFO' and entry.get('name') == symbol_name.upper():
                    if expiry_date and entry.get('expiry').upper() != expiry_date.upper():
                        continue

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

            # logger.info(f"Token to Symbol Mapping: {self.token_to_symbol}")
            # logger.info(f"Token to Strike Price Mapping: {self.token_to_strike_price}")
            # logger.info(f"Token to Category Mapping: {self.token_to_category}")

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

            # logger.info(
            #     f"Token {token}: Symbol {symbol}, Strike Price {strike_price}, LTP {current_price:.2f}, Volume {volume}, Category {category}"
            # )
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





class StockChainConsumerold(AsyncWebsocketConsumer):
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
        logger.info(f"self.symbol_name{self.symbol_name}")
        if not self.symbol_name or not self.expiry_date:
            await self.close(code=4001)  # Close with error code for missing parameters
            return

        # logger.info(f"Requested symbol: {self.symbol_name}, Expiry Date: {self.expiry_date}")

        tokens = await self.get_symbol_tokens(self.symbol_name, self.expiry_date)
        if not tokens:
            await self.close(code=4002)  # Close with error code for no tokens found
            return

        self.token_list = [{
            "exchangeType": 2,  # NFO exchange type
            "tokens": tokens
        }]
        # logger.info(f"Fetched tokens for {self.symbol_name}")
        # logger.info(f"Fetched tokens for {self.symbol_name}: {tokens}")
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
            # logger.info(f"{data}...dataaaaa--------")
            #         # Save the data to the specified directory
            # self.save_data_to_file(data, "symbol_data.json", target_directory)

            token_to_symbol = {}
            token_to_strike_price = {}
            token_to_category = {}

            for entry in data:
                # logger.info(f"Processing entry: {entry}")
                if (entry.get('exch_seg') == 'NFO' and entry.get('name') == symbol_name.upper() and entry.get('expiry').upper() == expiry_date.upper()):
                    # logger.info(f"tttttttttttttttttttt>>{entry}")
                        # Log matched entries
                    # logger.info(f"Matched Entry: {entry}")

                    token = entry['token']
                    symbol = entry['symbol']
                    strike_price = entry['strike']
                    
                    category = 'CE' if 'CE' in symbol else 'PE' if 'PE' in symbol else 'Unknown'
             
                    token_to_symbol[token] = symbol
                    token_to_strike_price[token] = strike_price
                    token_to_category[token] = category
                else:
                    logger.info(f"NOT  Matched Entry: {entry}")

            self.token_to_symbol = token_to_symbol
            self.token_to_strike_price = token_to_strike_price
            self.token_to_category = token_to_category

            # logger.info(f"Token to Symbol Mapping: {self.token_to_symbol}")
            # logger.info(f"Token to Strike Price Mapping: {self.token_to_strike_price}")
            # logger.info(f"Token to Category Mapping: {self.token_to_category}")

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




