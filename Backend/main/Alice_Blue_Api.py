# ==============================
# IMPORTS
# ==============================

import os
import logging
import pytz
import pandas as pd
import json
import requests
import hashlib

from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response

from pya3 import Aliceblue, TransactionType, OrderType, ProductType

from main.models import *
from main.tasks import send_trade_email_async
from main.broker_order_utils import extract_ltp_from_quote_payload, normalize_order_type, resolve_limit_price
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

ALICE_VENDOR_SESSION_URL = "https://ant.aliceblueonline.com/rest/AliceBlueAPIService/sso/getUserDetails"


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


def _alice_proxy_cache_key(user_id, proxy_config=None, credential_label="api_key"):
    if not proxy_config:
        return f"{user_id}:{credential_label}:direct"
    proxy_identity = "|".join(str(proxy_config.get(key, "")).split("@", 1)[-1] for key in sorted(proxy_config))
    return f"{user_id}:{credential_label}:proxy:{proxy_identity}"


def _build_alice_session(user_id, api_key, proxy_config=None):
    alice = ProxyAwareAliceblue(user_id=user_id, api_key=api_key, proxy_config=proxy_config)
    session = alice.get_session_id()

    if not session or session.get("stat") != "Ok":
        return None, session

    alice.alice_session_response = session
    alice.alice_session_id = (
        session.get("sessionID")
        or session.get("session_id")
        or session.get("susertoken")
        or session.get("token")
    )
    return alice, session


def _extract_alice_session_id(payload):
    if not isinstance(payload, dict):
        return None

    for key in (
        "sessionID",
        "session_id",
        "susertoken",
        "userSession",
        "user_session",
        "session",
        "token",
    ):
        value = payload.get(key)
        if value:
            return value

    for nested_key in ("data", "result", "response", "user"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict):
            value = _extract_alice_session_id(nested)
            if value:
                return value
        elif isinstance(nested, list):
            for item in nested:
                value = _extract_alice_session_id(item)
                if value:
                    return value
    return None


def _build_alice_vendor_session(user_id, auth_code, api_secret, proxy_config=None):
    if not user_id or not auth_code or not api_secret:
        return None, {"stat": "Not_ok", "emsg": "Missing User ID, Vendor Auth Code, or API Secret."}

    checksum_source = f"{str(user_id).strip()}{str(auth_code).strip()}{str(api_secret).strip()}"
    checksum = hashlib.sha256(checksum_source.encode("utf-8")).hexdigest()

    try:
        response = requests.post(
            ALICE_VENDOR_SESSION_URL,
            json={"checkSum": checksum},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            proxies=proxy_config,
            timeout=10,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"stat": "Not_ok", "emsg": response.text}
    except (requests.ConnectionError, requests.Timeout) as exception:
        return None, {"stat": "Not_ok", "emsg": str(exception)}

    status = str(payload.get("stat") or payload.get("status") or "").strip().lower()
    session_id = _extract_alice_session_id(payload)
    if response.status_code < 400 and status in {"ok", "success"} and session_id:
        alice = ProxyAwareAliceblue(user_id=user_id, api_key=auth_code, session_id=session_id, proxy_config=proxy_config)
        alice.alice_session_response = payload
        alice.alice_session_id = session_id
        return alice, payload

    if response.status_code >= 400 and "emsg" not in payload:
        payload["emsg"] = f"{response.status_code} - {response.reason}"
    return None, payload


def _describe_alice_login_failure(response):
    if not response:
        return "Alice Blue did not return a session response."
    message = str(response.get("emsg") or response)
    if "Tunnel connection failed: 401 Unauthorized" in message:
        return (
            "The assigned proxy authenticated for public-IP verification but rejected HTTPS broker traffic "
            "with 401 Unauthorized. Re-save the proxy username/password/port or ask the proxy vendor to enable "
            "HTTPS CONNECT tunneling to Alice Blue broker domains."
        )
    if "ProxyError" in message or "Unable to connect to proxy" in message:
        return f"The assigned proxy route failed before reaching Alice Blue: {message}"
    if "Invalid auth code" in message:
        return (
            "Alice Blue rejected the Vendor Auth Code. For Developer Portal apps, API Key and API Secret are not enough; "
            "generate a fresh authCode from Alice Blue's SSO/app authorization flow, save it in Vendor Auth Code, and try again."
        )
    if "Invalid Input" in message:
        return (
            "Alice Blue rejected the saved User ID/API credentials as Invalid Input. If these credentials are from the "
            "Alice Blue Developer Portal, also save the fresh Vendor Auth Code from Alice's SSO/app authorization flow; "
            "the old ANT API-key login cannot use Developer Portal API Key + Secret alone."
        )
    return f"Alice Blue rejected the saved User ID/API credentials: {message}"


def get_alice_session(user_id, api_key=None, proxy_config=None, api_secret=None, auth_code=None, return_error=False):
    try:
        api_key = str(api_key or "").strip()
        api_secret = str(api_secret or "").strip()
        auth_code = str(auth_code or "").strip()

        if not user_id:
            logger.error("Missing Alice Blue USER_ID")
            return (None, "Missing Alice Blue User ID.") if return_error else None
        if not api_key and not (api_secret and auth_code):
            logger.error("Missing Alice Blue login credentials")
            return (
                None,
                "Missing Alice Blue login credentials. Save either ANT API Key, or Developer Portal API Secret plus Vendor Auth Code.",
            ) if return_error else None

        candidates = []
        if api_key:
            candidates.append(("api_key", api_key))
        if api_secret and api_secret != api_key:
            candidates.append(("api_secret", api_secret))

        last_response = None
        for credential_label, credential_value in candidates:
            cache_key = _alice_proxy_cache_key(user_id, proxy_config, credential_label=credential_label)
            if cache_key in alice_sessions:
                session_data = alice_sessions[cache_key]
                if datetime.now().date() == session_data["time"].date():
                    return (session_data["client"], None) if return_error else session_data["client"]

            try:
                alice, session = _build_alice_session(user_id, credential_value, proxy_config=proxy_config)
            except Exception as e:
                logger.error(f"Alice Blue login exception using {credential_label}: {str(e)}")
                continue

            last_response = session
            if alice:
                alice.alice_credential_label = credential_label
                alice_sessions[cache_key] = {
                    "client": alice,
                    "session": session,
                    "time": datetime.now()
                }
                return (alice, None) if return_error else alice

            logger.error(f"Alice Blue login failed using {credential_label}: {session}")

        if auth_code and api_secret:
            cache_key = _alice_proxy_cache_key(user_id, proxy_config, credential_label="vendor_auth_code")
            if cache_key in alice_sessions:
                session_data = alice_sessions[cache_key]
                if datetime.now().date() == session_data["time"].date():
                    return (session_data["client"], None) if return_error else session_data["client"]

            try:
                alice, session = _build_alice_vendor_session(
                    user_id,
                    auth_code,
                    api_secret,
                    proxy_config=proxy_config,
                )
            except Exception as e:
                logger.error(f"Alice Blue vendor auth-code login exception: {str(e)}")
                alice, session = None, {"stat": "Not_ok", "emsg": str(e)}

            last_response = session
            if alice:
                alice.alice_credential_label = "vendor_auth_code"
                alice_sessions[cache_key] = {
                    "client": alice,
                    "session": session,
                    "time": datetime.now()
                }
                return (alice, None) if return_error else alice

            logger.error(f"Alice Blue vendor auth-code login failed: {session}")

        logger.error(f"Alice Blue login failed for all configured credentials. Last response: {last_response}")
        error_message = _describe_alice_login_failure(last_response)
        return (None, error_message) if return_error else None

    except Exception as e:
        logger.error(f"Login Error: {str(e)}")
        return (None, str(e)) if return_error else None


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
            ltp_payload = alice.get_scrip_info(instrument)
            ltp = float(extract_ltp_from_quote_payload(ltp_payload) or 0)
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
