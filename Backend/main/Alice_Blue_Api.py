# ==============================
# IMPORTS
# ==============================

import os
import logging
import pytz
import pandas as pd
import json
import requests

from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response

from pya3 import Aliceblue, TransactionType, OrderType, ProductType

from main.models import *
from main.tasks import send_trade_email_async
from main.broker_order_utils import normalize_order_type, resolve_limit_price
from main.trade_history_service import save_trade_order_history


# ==============================
# SAFE ENV
# ==============================

def get_env(key, default=None):
    try:
        return os.getenv(key, default)
    except:
        return default


USER_ID = get_env("USER_ID")
ALICE_API_KEY = get_env("ALICE_API_KEY")

logger = logging.getLogger('main')


# ==============================
# CONSTANTS (FULL SAFE)
# ==============================

BASE_URL = "https://ant.aliceblueonline.com/rest/AliceBlueAPIService/api/"

ORDER_PLACE_API = "placeOrder/executePlaceOrder"
ALICE_ORDER_URL = BASE_URL + ORDER_PLACE_API

GET_ORDER_BOOK_API = "placeOrder/fetchOrderBook"
GET_ORDER_BOOK_URL = BASE_URL + GET_ORDER_BOOK_API

GET_TRADE_BOOK_API = "placeOrder/fetchTradeBook"
GET_TRADE_BOOK_URL = BASE_URL + GET_TRADE_BOOK_API

# Backward compatibility (IMPORTANT)
GET_TREAD_BOOK_API = GET_TRADE_BOOK_API
GET_TREAD_BOOK_URL = GET_TRADE_BOOK_URL


# ==============================
# MULTI-USER SESSION
# ==============================

alice_sessions = {}


class ProxyAwareAliceblue(Aliceblue):
    def __init__(self, *args, proxy_config=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxy_config = proxy_config

    def _request(self, method, req_type, data=None):
        if not self.proxy_config:
            return super()._request(method, req_type, data=data)

        headers = {
            "X-SAS-Version": "2.0",
            "User-Agent": self._user_agent(),
            "Authorization": self._user_authorization(),
        }
        try:
            if req_type == "POST":
                response = requests.post(method, json=data, headers=headers, proxies=self.proxy_config)
            elif req_type == "GET":
                response = requests.get(method, json=data, headers=headers, proxies=self.proxy_config)
            else:
                return {"stat": "Not_ok", "emsg": f"Unsupported request type: {req_type}", "encKey": None}
        except (requests.ConnectionError, requests.Timeout) as exception:
            return {"stat": "Not_ok", "emsg": exception, "encKey": None}

        if response.status_code == 200:
            return json.loads(response.text)
        emsg = str(response.status_code) + " - " + response.reason
        return {"stat": "Not_ok", "emsg": emsg, "encKey": None}


def _alice_proxy_cache_key(user_id, proxy_config=None):
    if not proxy_config:
        return f"{user_id}:direct"
    proxy_identity = "|".join(str(proxy_config.get(key, "")).split("@", 1)[-1] for key in sorted(proxy_config))
    return f"{user_id}:proxy:{proxy_identity}"


def get_alice_session(user_id, api_key, proxy_config=None):
    try:
        if not user_id or not api_key:
            logger.error("Missing USER_ID or API_KEY")
            return None

        cache_key = _alice_proxy_cache_key(user_id, proxy_config)
        if cache_key in alice_sessions:
            session_data = alice_sessions[cache_key]
            if datetime.now().date() == session_data["time"].date():
                return session_data["client"]

        alice = ProxyAwareAliceblue(user_id=user_id, api_key=api_key, proxy_config=proxy_config)

        try:
            session = alice.get_session_id()
        except Exception as e:
            logger.error(f"Login Exception: {str(e)}")
            return None

        if not session or session.get("stat") != "Ok":
            logger.error(f"Login Failed: {session}")
            return None

        alice_sessions[cache_key] = {
            "client": alice,
            "time": datetime.now()
        }

        return alice

    except Exception as e:
        logger.error(f"Login Error: {str(e)}")
        return None


# ==============================
# FETCH CONTRACT MASTER
# ==============================

def fetch_instrument_data(alice, exchange="NFO"):
    try:
        file_path = f"{exchange}.csv"
        now = datetime.now()

        if os.path.exists(file_path):
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mod_time.date() == now.date():
                return

        if now.hour >= 8:
            alice.get_contract_master(exchange)

    except Exception as e:
        logger.error(f"Contract fetch error: {str(e)}")


# ==============================
# PRICE LOGIC
# ==============================

def get_limit_price(ltp, side):
    return resolve_limit_price(None, ltp, side)


# ==============================
# MARKET CHECK (FIXED)
# ==============================

def is_market_open():
    try:
        market_open_time = datetime.strptime("09:15", "%H:%M").time()
        market_close_time = datetime.strptime("15:30", "%H:%M").time()

        market_timezone = pytz.timezone("Asia/Kolkata")
        now = datetime.now(market_timezone)

        if 0 <= now.weekday() <= 4:
            if market_open_time <= now.time() <= market_close_time:
                return True

        return False

    except Exception as e:
        logger.error(f"Market check error: {str(e)}")
        return False


# ==============================
# ORDER FUNCTION
# ==============================

def place_alice_orders(
    LivePrice, group_service, api_skey, api_uid,
    trading_symbol_aliceblue, transaction_type, symbol, quantity,
    strategy, order_type, product_type, price, user,
    Lots, trade_order_status, Entry_type, Exit_type,
    Entry_price, Exit_price, EntryQty, ExitQty,
    webhook_signal, Exchange, Segment, Index_Symbol, history_id=None,
    trigger_price=None, proxy_config=None
):
    if not proxy_config:
        return {"data": {"status": "Failed", "message": "Proxy/static-IP execution route is required for Alice Blue orders."}}
    try:
        alice = get_alice_session(api_uid, api_skey, proxy_config=proxy_config)

        if not alice:
            return {"data": {"status": "Login Failed or API Disabled"}}

        txn = TransactionType.Buy if transaction_type.upper() == "BUY" else TransactionType.Sell

        product_type = ProductType.Intraday if str(product_type).upper() in ["MIS", "INTRADAY"] else ProductType.Normal

        # Instrument
        try:
            if Exchange == "NFO":
                fetch_instrument_data(alice, "NFO")
                instrument = alice.get_instrument_by_symbol("NFO", trading_symbol_aliceblue)
            else:
                instrument = alice.get_instrument_by_symbol("BSE", trading_symbol_aliceblue)
        except Exception as e:
            return {"data": {"status": "error", "message": str(e)}}

        if not instrument:
            return {"data": {"status": "error", "message": "Instrument not found"}}

        try:
            ltp = float(alice.get_scrip_info(instrument).get("Ltp", 0))
        except Exception as e:
            logger.error(f"{user}: Alice Blue LTP fetch failed: {str(e)}")
            ltp = 0

        if ltp == 0:
            return {"data": {"status": "error", "message": "Invalid LTP"}}

        requested_order_type = normalize_order_type(order_type)
        if requested_order_type == "LIMIT":
            price = resolve_limit_price(price, ltp, transaction_type)
            if not price:
                return {"data": {"status": "error", "message": "Unable to calculate Alice Blue limit price."}}
            alice_order_type = OrderType.Limit
        elif requested_order_type == "MARKET":
            price = 0
            alice_order_type = OrderType.Market
        else:
            return {"data": {"status": "error", "message": f"Unsupported Alice Blue order type: {requested_order_type}"}}

        # Place order
        try:
            response = alice.place_order(
                transaction_type=txn,
                instrument=instrument,
                quantity=quantity,
                order_type=alice_order_type,
                product_type=product_type,
                price=price
            )
        except Exception as e:
            return {"data": {"status": "order_failed", "message": str(e)}}

        if response and response.get("stat") == "Ok":
            return {
                "data": {
                    "status": "completed",
                    "order_id": response.get("NOrdNo"),
                    "order_type": requested_order_type,
                    "price": price if price else None,
                    "ltp": ltp,
                    "reference_price": ltp,
                }
            }

        return {"data": {"status": "Failed", "response": response}}

    except Exception as e:
        logger.error(str(e))
        return {"data": {"status": "error", "message": str(e)}}


# ==============================
# AUTO EXPIRY API
# ==============================

class SymbolExpirDateListView(APIView):

    def get(self, request):
        symbol = request.query_params.get('symbol')

        if not symbol:
            return Response({"error": "Symbol required"}, status=400)

        try:
            file_path = "NFO.csv"

            if not os.path.exists(file_path):
                return Response({
                    "symbol": symbol,
                    "expiry_dates": [],
                    "message": "Contract file not ready yet"
                })

            df = pd.read_csv(file_path)

            if 'Symbol' not in df.columns or 'Expiry Date' not in df.columns:
                return Response({
                    "symbol": symbol,
                    "expiry_dates": [],
                    "message": "Invalid contract format"
                })

            df = df[df['Symbol'] == symbol]

            expiries = sorted(df['Expiry Date'].dropna().unique())

            return Response({
                "symbol": symbol,
                "expiry_dates": expiries[:10]
            })

        except Exception as e:
            return Response({
                "symbol": symbol,
                "expiry_dates": [],
                "error": str(e)
            })
