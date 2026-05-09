
import asyncio
import csv
from datetime import datetime
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from urllib.parse import parse_qs

logger = logging.getLogger('main')
import ssl
import upstox_client
import websockets
from google.protobuf.json_format import MessageToDict
from main import MarketDataFeed_pb2 as pb
from asgiref.sync import sync_to_async
from main.models import ClientBrokerdetails
from main.services.proxy_utils import build_requests_proxy_config


async def _upstox_context_for_scope(scope):
    user = scope.get("user")
    if not user or not getattr(user, "is_authenticated", False):
        return None, None

    def load_details():
        return (
            ClientBrokerdetails.objects.filter(client=user, broker_name__broker_name__icontains="upstox")
            .select_related("execution_node", "broker_name")
            .order_by("-id")
            .first()
        )

    broker_details = await sync_to_async(load_details)()
    node = getattr(broker_details, "execution_node", None)
    if not broker_details or not node:
        return None, None
    if not node.is_active or not node.is_verified_with_broker:
        return None, None
    if node.execution_type == node.EXECUTION_TYPE_PROXY and not node.proxy_public_ip_verified:
        return None, None
    token_getter = getattr(broker_details, "get_access_token_secure", None)
    access_token = await sync_to_async(token_getter)() if callable(token_getter) else None
    access_token = access_token or broker_details.access_token
    proxy_config = build_requests_proxy_config(node)
    proxy_url = proxy_config.get("https") or proxy_config.get("http")
    return access_token, proxy_url

class UpstoxChainLiveSymbolConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        access_token, proxy_url = await _upstox_context_for_scope(self.scope)
        if not access_token or not proxy_url:
            await self.close()
            return
        self._broker_ws_proxy_url = proxy_url
        # Parse query parameters and split by comma.
        query_params = parse_qs(self.scope["query_string"].decode())
        self.symbol_names = query_params.get("name", [None])[0].split(",")
        #logger.info(f"Received symbol names: {self.symbol_names}")

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
            # logger.info(f"Found {len(instrument_keys)} instrument keys: {instrument_keys}")
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
            # logger.info(f"Subscribing chunk with keys: {chunk}")
            tasks.append(websocket.send(json.dumps(data).encode("utf-8")))
        await asyncio.gather(*tasks)

    async def fetch_market_data(self):
        # Setup SSL context (adjust as needed).
        ssl_context = ssl.create_default_context()

        # Authorize and get the Upstox feed URI by running blocking code in the thread.
        response = await sync_to_async(self.get_market_data_feed_authorize_sync)()
        uri = response.data.authorized_redirect_uri
        logger.info(f"Upstox feed URI: {uri}")

        async with websockets.connect(uri, ssl=ssl_context, proxy=self._broker_ws_proxy_url, max_size=4 * 1024 * 1024) as websocket:
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
                pass
                #logger.error(f"Error processing token {token_key}: {e}")

class UpstoxMarketDataConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_loop = asyncio.get_event_loop()
    async def connect(self):
        access_token, proxy_url = await _upstox_context_for_scope(self.scope)
        if not access_token or not proxy_url:
            await self.close()
            return
        self._broker_ws_proxy_url = proxy_url
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

        response = self.get_market_data_feed_authorize()

        async with websockets.connect(response.data.authorized_redirect_uri, ssl=ssl_context, proxy=self._broker_ws_proxy_url) as websocket:
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
        access_token, proxy_url = await _upstox_context_for_scope(self.scope)
        if not access_token or not proxy_url:
            await self.close()
            return
        self._broker_ws_proxy_url = proxy_url

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

        response = self.get_market_data_feed_authorize()

        async with websockets.connect(response.data.authorized_redirect_uri, ssl=ssl_context, proxy=self._broker_ws_proxy_url) as websocket:
           
            
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
