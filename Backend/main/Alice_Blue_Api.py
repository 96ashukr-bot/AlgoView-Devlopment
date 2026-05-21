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
import ssl

from datetime import datetime
from time import sleep
from urllib.parse import urlparse

from rest_framework.views import APIView
from rest_framework.response import Response

from pya3 import Aliceblue
from pya3.alicebluepy import encrypt_string

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

A3_BASE_URL = "https://a3.aliceblueonline.com/"
A3_OPEN_API_BASE_URL = A3_BASE_URL + "open-api/od/v1/"
A3_CONTRACT_BASE_URL = "https://v2api.aliceblueonline.com/restpy/static/contract_master/"

A3_VENDOR_SESSION_URL = A3_OPEN_API_BASE_URL + "vendor/getUserDetails"
A3_ORDER_PLACE_URL = A3_OPEN_API_BASE_URL + "orders/placeorder"
A3_ORDER_BOOK_URL = A3_OPEN_API_BASE_URL + "orders/book"
A3_TRADE_BOOK_URL = A3_OPEN_API_BASE_URL + "orders/trades"
A3_ORDER_HISTORY_URL = A3_OPEN_API_BASE_URL + "orders/history"
A3_WS_INVALIDATE_URL = A3_OPEN_API_BASE_URL + "profile/invalidateWsSess"
A3_WS_CREATE_URL = A3_OPEN_API_BASE_URL + "profile/createWsSess"

BASE_URL = A3_BASE_URL

ORDER_PLACE_API = "open-api/od/v1/orders/placeorder"
ALICE_ORDER_URL = A3_ORDER_PLACE_URL

GET_ORDER_BOOK_API = "open-api/od/v1/orders/book"
GET_ORDER_BOOK_URL = A3_ORDER_BOOK_URL

GET_TRADE_BOOK_API = "open-api/od/v1/orders/trades"
GET_TRADE_BOOK_URL = A3_TRADE_BOOK_URL

# Backward compatibility (IMPORTANT)
GET_TREAD_BOOK_API = GET_TRADE_BOOK_API
GET_TREAD_BOOK_URL = GET_TRADE_BOOK_URL

ALICE_VENDOR_SESSION_URL = A3_VENDOR_SESSION_URL


# ==============================
# MULTI-USER SESSION
# ==============================

alice_sessions = {}


def _alice_a3_headers(session_id=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if session_id:
        headers["Authorization"] = f"Bearer {session_id}"
    return headers


def _alice_a3_request(method, url, *, session_id=None, json_payload=None, proxy_config=None, timeout=10):
    try:
        response = requests.request(
            method,
            url,
            headers=_alice_a3_headers(session_id),
            json=json_payload,
            proxies=proxy_config,
            timeout=timeout,
        )
    except (requests.ConnectionError, requests.Timeout) as exception:
        return {"status": "Not_ok", "message": str(exception)}

    try:
        content = getattr(response, "content", None)
        payload = response.json() if content is None or content != b"" else {}
    except ValueError:
        payload = {"status": "Not_ok", "message": response.text}

    if isinstance(payload, dict):
        payload.setdefault("http_status_code", response.status_code)
        if response.status_code >= 400 and not _extract_alice_response_message(payload):
            payload["message"] = f"{response.status_code} - {response.reason}"
    return payload


class ProxyAwareAliceblue(Aliceblue):
    def __init__(self, *args, proxy_config=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxy_config = proxy_config

    def _proxy_url(self):
        if not self.proxy_config:
            return None
        return self.proxy_config.get("https") or self.proxy_config.get("http")

    def _websocket_proxy_kwargs(self):
        proxy_url = self._proxy_url()
        if not proxy_url:
            return {}
        parsed = urlparse(proxy_url)
        proxy_type = "socks5" if parsed.scheme.startswith("socks5") else "http"
        kwargs = {
            "proxy_type": proxy_type,
            "http_proxy_host": parsed.hostname,
            "http_proxy_port": parsed.port,
        }
        if parsed.username:
            kwargs["http_proxy_auth"] = (parsed.username, parsed.password or "")
        return kwargs

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
                response = requests.post(method, json=data, headers=headers, proxies=self.proxy_config, timeout=10)
            elif req_type == "GET":
                response = requests.get(method, json=data, headers=headers, proxies=self.proxy_config, timeout=10)
            else:
                return {"stat": "Not_ok", "emsg": f"Unsupported request type: {req_type}", "encKey": None}
        except (requests.ConnectionError, requests.Timeout) as exception:
            return {"stat": "Not_ok", "emsg": exception, "encKey": None}

        if response.status_code == 200:
            return json.loads(response.text)
        emsg = str(response.status_code) + " - " + response.reason
        return {"stat": "Not_ok", "emsg": emsg, "encKey": None}

    def get_contract_master(self, exchange):
        if not exchange or not (len(exchange) == 3 or exchange == "INDICES"):
            return self._error_response("Invalid Exchange parameter")

        print("NOTE: Today's contract master file will be updated after 08:00 AM. Before 08:00 AM previous day contract file be downloaded.")
        url = A3_CONTRACT_BASE_URL + f"{exchange.upper()}.csv"
        response = requests.get(url, proxies=self.proxy_config, timeout=20)
        response.raise_for_status()
        with open("%s.csv" % exchange.upper(), "w") as file_obj:
            file_obj.write(response.text)
        return self._error_response("Today contract File Downloaded")

    def invalid_sess(self, session_ID):
        return _alice_a3_request(
            "POST",
            A3_WS_INVALIDATE_URL,
            session_id=session_ID,
            json_payload={"source": "API", "userId": self.user_id},
            proxy_config=self.proxy_config,
        )

    def createSession(self, session_ID):
        return _alice_a3_request(
            "POST",
            A3_WS_CREATE_URL,
            session_id=session_ID,
            json_payload={"source": "API", "userId": self.user_id},
            proxy_config=self.proxy_config,
        )

    def _Aliceblue__ws_run_forever(self):
        while self._Aliceblue__stop_event.is_set() is False:
            try:
                self.ws.run_forever(
                    ping_interval=3,
                    ping_payload='{"t":"h"}',
                    sslopt={"cert_reqs": ssl.CERT_NONE},
                    **self._websocket_proxy_kwargs(),
                )
            except Exception as e:
                logger.warning(f"websocket run forever ended in exception, {e}")
            sleep(0.1)


def _alice_proxy_cache_key(user_id, proxy_config=None, credential_label="api_key"):
    if not proxy_config:
        return f"{user_id}:{credential_label}:direct"
    proxy_identity = "|".join(str(proxy_config.get(key, "")).split("@", 1)[-1] for key in sorted(proxy_config))
    return f"{user_id}:{credential_label}:proxy:{proxy_identity}"


def _build_alice_session(user_id, api_key, proxy_config=None):
    alice = ProxyAwareAliceblue(user_id=user_id, api_key=api_key, proxy_config=proxy_config)
    normalized_user_id = str(user_id or "").strip().upper()
    encryption_response = alice._post("encryption_key", {"userId": normalized_user_id})
    if not encryption_response or encryption_response.get("encKey") is None:
        if isinstance(encryption_response, dict):
            encryption_response = {
                **encryption_response,
                "alice_step": "encryption_key",
            }
        return None, encryption_response

    encrypted_payload = encrypt_string(normalized_user_id + str(api_key or "") + encryption_response["encKey"])
    session = alice._post("getsessiondata", {"userId": normalized_user_id, "userData": encrypted_payload})
    if isinstance(session, dict):
        session = {**session, "alice_step": "get_session_data"}

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
    if isinstance(payload, list):
        for item in payload:
            value = _extract_alice_session_id(item)
            if value:
                return value
        return None
    if not isinstance(payload, dict):
        return None

    for key in (
        "accessToken",
        "access_token",
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

    payload = _alice_a3_request(
        "POST",
        ALICE_VENDOR_SESSION_URL,
        json_payload={"checkSum": checksum},
        proxy_config=proxy_config,
    )

    status = str(payload.get("stat") or payload.get("status") or "").strip().lower()
    session_id = _extract_alice_session_id(payload)
    if int(payload.get("http_status_code") or 200) < 400 and status in {"ok", "success"} and session_id:
        alice = ProxyAwareAliceblue(user_id=user_id, api_key=auth_code, session_id=session_id, proxy_config=proxy_config)
        alice.alice_session_response = payload
        alice.alice_session_id = session_id
        return alice, payload

    return None, payload


def get_alice_vendor_session(user_id, auth_code, api_secret, proxy_config=None, return_error=False):
    cache_key = _alice_proxy_cache_key(user_id, proxy_config, credential_label=f"vendor_auth_code:{str(auth_code or '').strip()}")
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

    if alice:
        alice.alice_credential_label = "vendor_auth_code"
        alice_sessions[cache_key] = {
            "client": alice,
            "session": session,
            "time": datetime.now()
        }
        return (alice, None) if return_error else alice

    logger.error(f"Alice Blue vendor auth-code login failed: {session}")
    error_message = _describe_alice_login_failure(session)
    return (None, error_message) if return_error else None


def _build_alice_saved_session(user_id, api_key, session_id, proxy_config=None):
    if not user_id or not session_id:
        return None
    alice = ProxyAwareAliceblue(
        user_id=user_id,
        api_key=str(api_key or "").strip(),
        session_id=str(session_id or "").strip(),
        proxy_config=proxy_config,
    )
    alice.alice_session_id = str(session_id or "").strip()
    alice.alice_session_response = {"stat": "Ok", "sessionID": alice.alice_session_id, "source": "saved_access_token"}
    alice.alice_credential_label = "saved_access_token"
    return alice


def get_alice_saved_session(user_id, api_key, session_id, proxy_config=None, return_error=False):
    session_id = str(session_id or "").strip()
    if not session_id:
        message = "Alice Blue session token is missing. Connect to Alice Blue again before placing orders."
        return (None, message) if return_error else None

    cache_key = _alice_proxy_cache_key(
        user_id,
        proxy_config,
        credential_label=f"saved_session:{session_id[-12:]}",
    )
    if cache_key in alice_sessions:
        session_data = alice_sessions[cache_key]
        if datetime.now().date() == session_data["time"].date():
            return (session_data["client"], None) if return_error else session_data["client"]

    alice = _build_alice_saved_session(user_id, api_key, session_id, proxy_config=proxy_config)
    if not alice:
        message = "Alice Blue saved session could not be prepared. Connect to Alice Blue again."
        return (None, message) if return_error else None

    alice_sessions[cache_key] = {
        "client": alice,
        "session": alice.alice_session_response,
        "time": datetime.now(),
    }
    return (alice, None) if return_error else alice


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
        step = response.get("alice_step")
        if step == "encryption_key":
            return (
                "Alice Blue rejected the saved User ID before session generation. Verify the Alice User ID/Login ID, "
                "log in to Alice Blue web/mobile once today, and confirm this account is allowed for API login."
            )
        if step == "get_session_data":
            return (
                "Alice Blue accepted the User ID but rejected the saved ANT API_KEY. For individual trader login, "
                "the API Key field must contain the API_KEY generated inside ANT Web Trading Platform, not the "
                "Developer Portal app key/secret. Leave App Secret blank unless Alice specifically gives an alternate "
                "individual API key, and confirm the assigned proxy/static IP is whitelisted for this Alice app."
            )
        return (
            "Alice Blue rejected the saved User ID/App credentials as Invalid Input. For individual trader login, "
            "verify the User ID and ANT API_KEY, log in to Alice Blue web/mobile once today, and confirm the assigned "
            "proxy/static IP is whitelisted for this Alice app. Developer Portal app key/secret requires Alice's "
            "vendor SSO authCode flow and is not enough for pya3 individual login."
        )
    return f"Alice Blue rejected the saved User ID/App credentials: {message}"


def _extract_alice_response_message(payload):
    if payload in (None, ""):
        return None
    if isinstance(payload, str):
        return payload
    if isinstance(payload, list):
        for item in payload:
            message = _extract_alice_response_message(item)
            if message:
                return message
        return None
    if not isinstance(payload, dict):
        return str(payload)

    for key in ("emsg", "message", "Message", "error", "Error", "remarks", "rejectreason", "rejReason"):
        value = payload.get(key)
        if value:
            return str(value)

    for key in ("data", "response", "result", "body"):
        message = _extract_alice_response_message(payload.get(key))
        if message:
            return message

    stat = payload.get("stat") or payload.get("status")
    if stat and str(stat).lower() not in {"ok", "success", "completed", "complete"}:
        return str(stat)
    return None


def _alice_nested_values(payload):
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from _alice_nested_values(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _alice_nested_values(item)


def _extract_alice_order_id(payload):
    for item in _alice_nested_values(payload):
        for key in (
            "brokerOrderId",
            "broker_order_id",
            "orderId",
            "order_id",
            "NOrdNo",
            "nestOrderNumber",
            "exchangeOrderNo",
        ):
            value = item.get(key)
            if value:
                return str(value)
    return None


def _extract_alice_order_status(payload):
    for item in _alice_nested_values(payload):
        for key in ("orderStatus", "order_status", "status", "stat"):
            value = item.get(key)
            if value:
                return str(value).strip()
    return None


def _alice_order_statuses(payload):
    statuses = []
    for item in _alice_nested_values(payload):
        for key in ("orderStatus", "order_status", "status", "stat"):
            value = item.get(key)
            if value:
                statuses.append(str(value).strip())
    return statuses


def _alice_a3_order_succeeded(payload):
    order_id = _extract_alice_order_id(payload)
    if order_id:
        return True
    statuses = [status.lower() for status in _alice_order_statuses(payload)]
    if any(status in {"not_ok", "failed", "failure", "rejected", "cancelled", "error"} for status in statuses):
        return False
    if any(status in {"open", "complete", "completed", "pending", "put order req received"} for status in statuses):
        return True
    message = str(_extract_alice_response_message(payload) or "").lower()
    if "routed to execution" in message or "order placed" in message:
        return True
    return False


def _alice_order_display_status(payload):
    statuses = _alice_order_statuses(payload)
    for status in statuses:
        normalized = status.lower()
        if normalized in {"failed", "failure", "rejected", "cancelled", "error"}:
            return "Failed"
        if normalized not in {"ok", "success"}:
            return status
    if any(status.lower() == "success" for status in statuses):
        return "Success"
    return "open"


def _alice_a3_product(product_type):
    value = str(product_type or "").strip().upper()
    if value in {"MIS", "INTRADAY", "I"}:
        return "INTRADAY"
    if value in {"NRML", "NORMAL", "CARRYFORWARD", "MARGIN"}:
        return "NORMAL"
    if value in {"CNC", "DELIVERY", "LONGTERM"}:
        return "DELIVERY"
    return "INTRADAY"


def _alice_a3_order_type(order_type):
    value = normalize_order_type(order_type)
    if value == "LIMIT":
        return "LIMIT"
    if value == "MARKET":
        return "MARKET"
    if value in {"SL", "STOPLOSS_LIMIT"}:
        return "SL"
    if value in {"SLM", "STOPLOSS_MARKET"}:
        return "SLM"
    return value


def get_alice_a3_orderbook(session_id, proxy_config=None):
    if not session_id:
        return {"status": "Not_ok", "message": "Alice Blue session token is missing."}
    return _alice_a3_request("GET", A3_ORDER_BOOK_URL, session_id=session_id, proxy_config=proxy_config)


def get_alice_session(user_id, api_key=None, proxy_config=None, api_secret=None, auth_code=None, return_error=False):
    message = (
        "Legacy Alice Blue API-key session generation is disabled. Use Connect to Alice Blue "
        "so ANT returns authCode, then exchange it through A3 vendor/getUserDetails and save "
        "the returned A3 session token before trading."
    )
    logger.error(message)
    return (None, message) if return_error else None


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


def _alice_failed_response(message, **extra):
    data = {"status": "Failed", "message": str(message or "Alice Blue order failed.")}
    data.update({key: value for key, value in extra.items() if value not in (None, "")})
    return {"data": data}


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
    trigger_price=None, proxy_config=None, session_id=None,
    allow_direct_node_execution=False,
):
    if not proxy_config and not allow_direct_node_execution:
        return _alice_failed_response("Proxy/static-IP execution route is required for Alice Blue orders.")
    try:
        if session_id:
            alice, session_error = get_alice_saved_session(
                api_uid,
                api_skey,
                session_id,
                proxy_config=proxy_config,
                return_error=True,
            )
        else:
            alice = None
            session_error = (
                "Alice Blue A3 session token is missing. Connect to Alice Blue through ANT "
                "authCode login before placing orders."
            )

        if not alice:
            return _alice_failed_response(session_error or "Alice Blue login failed or API is disabled.")

        # Instrument
        exchange = str(Exchange or "NFO").strip().upper()
        try:
            fetch_exchange = exchange if exchange in {"NFO", "NSE", "BSE", "MCX"} else "NFO"
            fetch_instrument_data(alice, fetch_exchange)
            instrument = alice.get_instrument_by_symbol(fetch_exchange, trading_symbol_aliceblue)
        except Exception as e:
            return _alice_failed_response(str(e))

        if not instrument:
            return _alice_failed_response("Instrument not found")

        requested_order_type = normalize_order_type(order_type)
        ltp = 0
        if requested_order_type == "LIMIT":
            explicit_price = price
            if not explicit_price:
                try:
                    ltp_payload = alice.get_scrip_info(instrument)
                    ltp = float(extract_ltp_from_quote_payload(ltp_payload) or 0)
                except Exception as e:
                    logger.error(f"{user}: Alice Blue LTP fetch failed: {str(e)}")
                    ltp = 0

                if ltp == 0:
                    return _alice_failed_response("Invalid LTP")

            price = resolve_limit_price(explicit_price, ltp, transaction_type)
            if not price:
                return _alice_failed_response("Unable to calculate Alice Blue limit price.")
        elif requested_order_type == "MARKET":
            price = 0
        else:
            return _alice_failed_response(f"Unsupported Alice Blue order type: {requested_order_type}")

        instrument_id = str(
            getattr(instrument, "token", "")
            or getattr(instrument, "instrument_token", "")
            or getattr(instrument, "instrumentId", "")
            or ""
        ).strip()
        if not instrument_id:
            return _alice_failed_response("Alice Blue instrument token was not found for the selected symbol.")

        broker_session_id = getattr(alice, "alice_session_id", None) or session_id
        order_payload = [{
            "exchange": fetch_exchange,
            "instrumentId": instrument_id,
            "transactionType": str(transaction_type or "").strip().upper(),
            "quantity": int(quantity or 0),
            "product": _alice_a3_product(product_type),
            "orderComplexity": "REGULAR",
            "orderType": _alice_a3_order_type(requested_order_type),
            "validity": "DAY",
            "price": price if requested_order_type == "LIMIT" else 0,
            "slTriggerPrice": trigger_price or "",
            "slLegPrice": "",
            "targetLegPrice": "",
            "disclosedQuantity": "",
            "marketProtectionPercent": "",
            "trailingSlAmount": "",
            "apiOrderSource": "",
            "algoId": "",
            "orderTag": str(history_id or ""),
        }]

        response = _alice_a3_request(
            "POST",
            A3_ORDER_PLACE_URL,
            session_id=broker_session_id,
            json_payload=order_payload,
            proxy_config=proxy_config,
        )

        if _alice_a3_order_succeeded(response):
            return {
                "data": {
                    "status": _alice_order_display_status(response),
                    "order_id": _extract_alice_order_id(response),
                    "message": _extract_alice_response_message(response) or _alice_order_display_status(response),
                    "order_type": requested_order_type,
                    "price": price if price else None,
                    "ltp": ltp or None,
                    "reference_price": ltp or None,
                    "response": response,
                    "broker_order": response,
                }
            }

        message = _extract_alice_response_message(response) or "Broker rejected Alice Blue order."
        return _alice_failed_response(message, response=response)

    except Exception as e:
        logger.error(str(e))
        return _alice_failed_response(str(e))


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
