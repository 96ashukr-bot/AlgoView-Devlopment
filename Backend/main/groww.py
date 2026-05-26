from __future__ import annotations

import csv
import hashlib
import logging
import os
import re
import time
from datetime import datetime
from typing import Any, Optional

import requests
from django.conf import settings

from main.broker_order_utils import normalize_order_type, resolve_limit_price, resolve_limit_reference_price, to_float
from main.services.option_ltp_fallback import cache_option_ltp, get_cached_option_ltp
from main.trade_history_service import save_trade_order_history

logger = logging.getLogger("main.groww")

GROWW_API_BASE_URL = "https://api.groww.in/v1"
GROWW_INSTRUMENT_URL = "https://growwapi-assets.groww.in/instruments/instrument.csv"
GROWW_INSTRUMENT_CACHE = os.path.join(os.path.dirname(__file__), "groww_instruments.csv")
GROWW_INSTRUMENT_CACHE_TTL_SECONDS = 12 * 60 * 60

GROWW_SUCCESS_STATUSES = {"SUCCESS"}
GROWW_OPEN_STATUSES = {"NEW", "ACKED", "TRIGGER_PENDING", "APPROVED", "OPEN", "PENDING", "PLACED"}
GROWW_COMPLETE_STATUSES = {"EXECUTED", "COMPLETED", "COMPLETE"}
GROWW_FAILED_STATUSES = {"REJECTED", "FAILED", "CANCELLED", "CANCELED"}


def _failed_response(message, payload=None):
    data = {"status": "Failed", "message": str(message or "Groww order failed.")}
    if payload is not None:
        data["broker_response"] = payload
    return {"data": data}


def _headers(access_token):
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "X-API-VERSION": "1.0",
    }


def generate_groww_checksum(api_secret, timestamp):
    return hashlib.sha256(f"{api_secret}{timestamp}".encode("utf-8")).hexdigest()


def generate_groww_access_token(api_key, api_secret, proxy_config=None):
    if not api_key or not api_secret:
        return {"status": "failed", "message": "Groww API key and API secret are required."}

    timestamp = str(int(time.time()))
    checksum = generate_groww_checksum(api_secret, timestamp)
    try:
        response = requests.post(
            f"{GROWW_API_BASE_URL}/token/api/access",
            json={
                "key_type": "approval",
                "checksum": checksum,
                "timestamp": timestamp,
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-API-VERSION": "1.0",
            },
            timeout=_request_timeout(),
            proxies=proxy_config,
        )
        payload = response.json() if response.content else {}
    except Exception as exc:
        logger.exception("Groww access token generation failed")
        return {"status": "failed", "message": str(exc)}

    token = payload.get("token") or payload.get("access_token") or (payload.get("payload") or {}).get("token")
    if response.status_code >= 400 or not token:
        return {
            "status": "failed",
            "message": payload.get("message") or payload.get("error") or "Groww access token generation failed.",
            "response": payload,
            "status_code": response.status_code,
        }
    return {
        "status": "success",
        "access_token": token,
        "token_ref_id": payload.get("tokenRefId") or payload.get("token_ref_id"),
        "session_name": payload.get("sessionName") or payload.get("session_name"),
        "expiry": payload.get("expiry") or payload.get("expires_at"),
        "response": payload,
    }


def _request_timeout():
    return int(getattr(settings, "GROWW_API_TIMEOUT_SECONDS", 10) or 10)


def _exchange_for_groww(exchange, symbol=None):
    normalized_exchange = str(exchange or "").strip().upper()
    normalized_symbol = str(symbol or "").strip().upper()
    if normalized_exchange.startswith("B") or normalized_symbol in {"SENSEX", "BANKEX", "SENSEX50"}:
        return "BSE"
    return "NSE"


def _segment_for_groww(segment, exchange=None):
    normalized_segment = str(segment or "").strip().upper()
    normalized_exchange = str(exchange or "").strip().upper()
    if normalized_segment in {"CASH", "FNO", "COMMODITY"}:
        return normalized_segment
    if normalized_exchange in {"NFO", "BFO", "BSE_FO", "BSE_FNO", "BSE", "NSE_FO"}:
        return "FNO"
    return "CASH"


def _product_for_groww(product_type):
    normalized = str(product_type or "").strip().upper()
    return {
        "INTRADAY": "MIS",
        "DELIVERY": "CNC",
        "CARRYFORWARD": "NRML",
    }.get(normalized, normalized or "MIS")


def _order_type_for_groww(order_type):
    normalized = normalize_order_type(order_type)
    return {"SL-M": "SL_M", "SLM": "SL_M"}.get(normalized, normalized)


def _expiry_date(day, month, fullyear, order_params=None):
    if isinstance(order_params, dict):
        explicit = order_params.get("expiry") or order_params.get("expiry_date")
        if explicit:
            return str(explicit)[:10]
    if not (day and month and fullyear):
        return None
    try:
        month_number = datetime.strptime(str(month)[:3], "%b").month
        return f"{int(fullyear):04d}-{month_number:02d}-{int(day):02d}"
    except (TypeError, ValueError):
        return None


def _safe_order_reference_id(history_id):
    base = re.sub(r"[^A-Za-z0-9]", "", str(history_id or ""))
    digest = hashlib.sha1(str(history_id or time.time()).encode()).hexdigest()[:8]
    value = (base[:12] + digest)[:20]
    if len(value) < 8:
        value = f"ALG{digest}"[:20]
    return value


def _cache_symbol(underlying, strike, option_type, day=None, month=None, fullyear=None, fallback=None):
    if underlying and strike and option_type and day and month and fullyear:
        return f"{underlying} {strike} {option_type} {day} {month} {str(fullyear)[-2:]}"
    return fallback or underlying


def _refresh_instrument_cache(proxy_config=None):
    response = requests.get(
        GROWW_INSTRUMENT_URL,
        timeout=_request_timeout(),
        proxies=proxy_config,
    )
    response.raise_for_status()
    with open(GROWW_INSTRUMENT_CACHE, "wb") as instrument_file:
        instrument_file.write(response.content)


def _instrument_cache_is_fresh():
    try:
        return time.time() - os.path.getmtime(GROWW_INSTRUMENT_CACHE) < GROWW_INSTRUMENT_CACHE_TTL_SECONDS
    except OSError:
        return False


def _iter_groww_instruments(proxy_config=None):
    if not _instrument_cache_is_fresh():
        try:
            _refresh_instrument_cache(proxy_config=proxy_config)
        except Exception as exc:
            if not os.path.exists(GROWW_INSTRUMENT_CACHE):
                raise
            logger.warning("Using stale Groww instrument cache after refresh failed: %s", exc)

    with open(GROWW_INSTRUMENT_CACHE, newline="", encoding="utf-8") as instrument_file:
        reader = csv.DictReader(instrument_file)
        for row in reader:
            yield row


def resolve_groww_trading_symbol(
    *,
    exchange,
    segment,
    symbol,
    trade_symbol,
    strike,
    option_type,
    expiry_date,
    proxy_config=None,
):
    groww_exchange = _exchange_for_groww(exchange, symbol=symbol)
    groww_segment = _segment_for_groww(segment, exchange=exchange)
    normalized_symbol = str(symbol or "").strip().upper()
    normalized_option_type = str(option_type or "").strip().upper()
    normalized_strike = to_float(strike)
    explicit_symbol = str(trade_symbol or "").strip().upper()

    if groww_segment != "FNO" or not (normalized_symbol and normalized_option_type and normalized_strike and expiry_date):
        return explicit_symbol or normalized_symbol

    for row in _iter_groww_instruments(proxy_config=proxy_config):
        if str(row.get("exchange") or "").strip().upper() != groww_exchange:
            continue
        if str(row.get("segment") or "").strip().upper() != "FNO":
            continue
        if str(row.get("underlying_symbol") or "").strip().upper() != normalized_symbol:
            continue
        if str(row.get("instrument_type") or "").strip().upper() != normalized_option_type:
            continue
        if str(row.get("expiry_date") or "").strip()[:10] != str(expiry_date)[:10]:
            continue
        if to_float(row.get("strike_price")) != normalized_strike:
            continue
        if str(row.get("buy_allowed") or "1").strip() == "0" and str(row.get("sell_allowed") or "1").strip() == "0":
            continue
        return str(row.get("trading_symbol") or "").strip()

    return explicit_symbol or normalized_symbol


def fetch_groww_option_ltp(access_token, exchange, segment, trading_symbol, proxy_config=None, user=None):
    groww_exchange = _exchange_for_groww(exchange)
    groww_segment = _segment_for_groww(segment, exchange=exchange)
    exchange_symbol = f"{groww_exchange}_{trading_symbol}"
    try:
        response = requests.get(
            f"{GROWW_API_BASE_URL}/live-data/ltp",
            params={"segment": groww_segment, "exchange_symbols": exchange_symbol},
            headers=_headers(access_token),
            timeout=_request_timeout(),
            proxies=proxy_config,
        )
        payload = response.json() if response.content else {}
        if response.status_code >= 400:
            logger.warning("[%s] Groww LTP fetch failed for %s: %s %s", user, exchange_symbol, response.status_code, payload)
            return None
        ltp = to_float((payload.get("payload") or {}).get(exchange_symbol))
        if ltp and ltp > 0:
            return ltp
        logger.warning("[%s] Groww LTP response did not contain option premium for %s: %s", user, exchange_symbol, payload)
    except Exception as exc:
        logger.warning("[%s] Groww LTP fetch failed for %s: %s", user, exchange_symbol, exc)
    return None


def _extract_payload(response_payload):
    if not isinstance(response_payload, dict):
        return {}
    payload = response_payload.get("payload")
    return payload if isinstance(payload, dict) else {}


def _groww_status_to_history_status(order_status, api_status=None):
    normalized_order_status = str(order_status or "").strip().upper()
    normalized_api_status = str(api_status or "").strip().upper()
    if normalized_api_status and normalized_api_status not in GROWW_SUCCESS_STATUSES:
        return "Failed"
    if normalized_order_status in GROWW_COMPLETE_STATUSES:
        return "complete"
    if normalized_order_status in GROWW_OPEN_STATUSES:
        return "open"
    if normalized_order_status in GROWW_FAILED_STATUSES:
        return "Failed"
    return "open" if normalized_api_status in GROWW_SUCCESS_STATUSES else "Failed"


def _groww_message(payload, fallback=None):
    return payload.get("remark") or payload.get("message") or payload.get("error") or fallback or "Groww order response received."


def get_groww_order_status(access_token, order_id, segment, proxy_config=None):
    response = requests.get(
        f"{GROWW_API_BASE_URL}/order/status/{order_id}",
        params={"segment": segment},
        headers=_headers(access_token),
        timeout=_request_timeout(),
        proxies=proxy_config,
    )
    return response.json() if response.content else {}


def place_groww_orders(
    LivePrice, group_service, access_token, trade_symbol, transaction_type, symbol, quantity,
    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price,
    Exit_price, EntryQty, ExitQty, webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice,
    trade_order_status, history_id, day=None, month=None, fullyear=None, strike=None, option_type=None,
    order_params=None, proxy_config=None,
):
    if not proxy_config:
        return _failed_response("Proxy/static-IP execution route is required for Groww orders.")
    if not access_token:
        return _failed_response("Groww API auth token is missing.")

    expiry_date = _expiry_date(day, month, fullyear, order_params=order_params)
    groww_exchange = _exchange_for_groww(Exchange, symbol=Index_Symbol or symbol)
    groww_segment = _segment_for_groww(Segment, exchange=Exchange)
    resolved_symbol = resolve_groww_trading_symbol(
        exchange=groww_exchange,
        segment=groww_segment,
        symbol=Index_Symbol or symbol,
        trade_symbol=trade_symbol,
        strike=strike,
        option_type=option_type,
        expiry_date=expiry_date,
        proxy_config=proxy_config,
    )
    if not resolved_symbol:
        message = "Groww trading symbol could not be resolved for the selected contract."
        save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, 0, "Failed", None, message,
                                 strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                 webhook_signal, Exchange, Segment, Index_Symbol, order_params or {}, broker="Groww", history_id=history_id)
        return _failed_response(message)

    requested_order_type = _order_type_for_groww(ordertype)
    ltp = fetch_groww_option_ltp(access_token, groww_exchange, groww_segment, resolved_symbol, proxy_config=proxy_config, user=user)
    if ltp:
        cache_option_ltp(
            _cache_symbol(Index_Symbol or symbol, strike, option_type, day, month, fullyear, fallback=resolved_symbol),
            ltp,
            expiry_date=expiry_date,
            underlying=Index_Symbol or symbol,
            source="groww",
        )
    elif groww_segment == "FNO":
        ltp = get_cached_option_ltp(
            _cache_symbol(Index_Symbol or symbol, strike, option_type, day, month, fullyear, fallback=resolved_symbol),
            expiry_date=expiry_date,
            underlying=Index_Symbol or symbol,
        )

    reference_price = resolve_limit_reference_price(resolved_symbol, ltp, LivePrice, Entry_price, Exit_price)
    if requested_order_type == "LIMIT":
        price = resolve_limit_price(price, reference_price, transaction_type)
        if not price:
            message = "Unable to calculate Groww option limit price because option live price is unavailable. Please retry after quotes are available or provide an explicit option limit price."
            save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, resolved_symbol, 0, "Failed", None, message,
                                     strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                     webhook_signal, groww_exchange, groww_segment, Index_Symbol, order_params or {}, broker="Groww", history_id=history_id)
            return _failed_response(message)
    elif requested_order_type == "MARKET":
        price = 0

    payload = {
        "trading_symbol": resolved_symbol,
        "quantity": int(quantity or 0),
        "validity": "DAY",
        "exchange": groww_exchange,
        "segment": groww_segment,
        "product": _product_for_groww(product_type),
        "order_type": requested_order_type,
        "transaction_type": str(transaction_type or "").upper(),
        "order_reference_id": _safe_order_reference_id(history_id),
    }
    if requested_order_type in {"LIMIT", "SL"}:
        payload["price"] = price
    if requested_order_type in {"SL", "SL_M"} and triggerPrice not in (None, ""):
        payload["trigger_price"] = to_float(triggerPrice)

    try:
        response = requests.post(
            f"{GROWW_API_BASE_URL}/order/create",
            json=payload,
            headers=_headers(access_token),
            timeout=_request_timeout(),
            proxies=proxy_config,
        )
        response_payload = response.json() if response.content else {}
    except requests.Timeout:
        message = "Groww order placement timed out before broker confirmation. Please check Groww order book before retrying."
        save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, resolved_symbol, 0, "Failed", None, message,
                                 strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                 webhook_signal, groww_exchange, groww_segment, Index_Symbol, payload, broker="Groww", history_id=history_id)
        return _failed_response(message)
    except Exception as exc:
        message = f"Groww order placement failed: {exc}"
        save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, resolved_symbol, 0, "Failed", None, message,
                                 strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                 webhook_signal, groww_exchange, groww_segment, Index_Symbol, payload, broker="Groww", history_id=history_id)
        return _failed_response(message)

    place_payload = _extract_payload(response_payload)
    order_id = place_payload.get("groww_order_id")
    if response.status_code >= 400 or str(response_payload.get("status") or "").upper() not in GROWW_SUCCESS_STATUSES:
        message = _groww_message(place_payload, response_payload.get("message") or "Groww rejected the order.")
        save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, resolved_symbol, order_id or 0, "Failed", response_payload, message,
                                 strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                 webhook_signal, groww_exchange, groww_segment, Index_Symbol, payload, broker="Groww", history_id=history_id)
        return _failed_response(message, response_payload)

    status_payload = response_payload
    if order_id:
        try:
            status_payload = get_groww_order_status(access_token, order_id, groww_segment, proxy_config=proxy_config)
        except Exception as exc:
            logger.warning("[%s] Groww order status lookup failed for %s: %s", user, order_id, exc)

    final_payload = _extract_payload(status_payload) or place_payload
    final_status = _groww_status_to_history_status(final_payload.get("order_status"), status_payload.get("status"))
    message = _groww_message(final_payload, place_payload.get("remark") or "Groww order placed successfully.")
    broker_response = status_payload if status_payload is not response_payload else response_payload
    history_trade_status = "OPEN" if final_status in {"open", "complete", "completed"} and str(transaction_type).upper() == "BUY" else trade_order_status
    if final_status in {"open", "complete", "completed"} and str(transaction_type).upper() == "SELL":
        history_trade_status = "CLOSE"

    filled_quantity = final_payload.get("filled_quantity")
    average_price = final_payload.get("average_fill_price") or final_payload.get("price")
    if str(transaction_type).upper() == "BUY":
        Entry_type = Entry_type or "LE"
        Entry_price = average_price or Entry_price
        EntryQty = filled_quantity or EntryQty
    else:
        Exit_type = Exit_type or "LX"
        Exit_price = average_price or Exit_price
        ExitQty = filled_quantity or ExitQty

    save_trade_order_history(LivePrice, group_service, transaction_type, history_trade_status, user, resolved_symbol, order_id, final_status, broker_response, message,
                             strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                             webhook_signal, groww_exchange, groww_segment, Index_Symbol, payload, broker="Groww", history_id=history_id)
    return {
        "data": {
            "status": final_status,
            "message": message,
            "order_id": order_id,
            "order_type": requested_order_type,
            "price": average_price or price,
            "ltp": ltp,
            "reference_price": reference_price,
        }
    }
