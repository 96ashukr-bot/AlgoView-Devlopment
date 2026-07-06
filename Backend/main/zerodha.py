from django.http import JsonResponse
from kiteconnect import KiteConnect
from main.models import ClientBrokerdetails, CompanySmtpDetails
from main.broker_order_utils import extract_ltp_from_quote_payload, is_option_symbol, normalize_order_type, resolve_limit_price, resolve_limit_reference_price, to_float
from main.services.option_ltp_fallback import cache_option_ltp, fetch_nse_option_chain_ltp, get_cached_option_ltp
from main.services.live_price_cache import get_live_price
from main.services.upstox_market_data import UpstoxInstrumentResolver, fetch_central_upstox_option_ltp
from main.trade_history_service import save_trade_order_history
import logging
import requests
import time
from django.db import transaction
logger = logging.getLogger('main')

KITE_LTP_URL = "https://api.kite.trade/quote/ltp"
_central_ltp_resolver = UpstoxInstrumentResolver()
ZERODHA_MAX_LIMIT_BUFFER_PERCENTAGE = 0.5
ZERODHA_ORDER_HISTORY_ATTEMPTS = 3
ZERODHA_ORDER_HISTORY_RETRY_SECONDS = 1
ZERODHA_TERMINAL_ORDER_STATUSES = {"COMPLETE", "REJECTED", "CANCELLED", "CANCELED"}


def _zerodha_buffer_percentage(buffer_percentage=None):
    try:
        buffer = float(buffer_percentage)
    except (TypeError, ValueError):
        buffer = ZERODHA_MAX_LIMIT_BUFFER_PERCENTAGE
    if buffer <= 0:
        return ZERODHA_MAX_LIMIT_BUFFER_PERCENTAGE
    return min(buffer, ZERODHA_MAX_LIMIT_BUFFER_PERCENTAGE)


def _safe_zerodha_limit_input(explicit_price, reference_price, trading_symbol, transaction_type, user=None):
    requested_price = to_float(explicit_price)
    live_reference = to_float(reference_price)
    if not requested_price or not live_reference or not is_option_symbol(trading_symbol):
        return explicit_price

    slippage_percent = abs(requested_price - live_reference) / live_reference * 100
    if slippage_percent <= ZERODHA_MAX_LIMIT_BUFFER_PERCENTAGE:
        return explicit_price

    logger.warning(
        "[%s] Ignoring Zerodha explicit option limit price %s for %s because it is %.2f%% away from LTP %s.",
        user,
        explicit_price,
        trading_symbol,
        slippage_percent,
        reference_price,
    )
    return None

def get_trading_symbol(exchange, symbol, kite, user=None):
    try:
        logger.info(f"[{user}] Fetching instruments from exchange: {exchange}")
        instruments = kite.instruments(exchange)
        logger.info(f"[{user}] Instruments fetched. Searching for {symbol}")

        for instrument in instruments:
            if instrument['tradingsymbol'] == symbol:
                logger.info(f"[{user}] Trading Symbol Found: {instrument['tradingsymbol']}")
                return instrument['tradingsymbol']

        logger.warning(f"[{user}] Trading symbol '{symbol}' not found in exchange '{exchange}'")
        return None

    except Exception as e:
        logger.exception(f"[{user}] Exception occurred while fetching trading symbol '{symbol}' from exchange '{exchange}'")
        return None
    
def get_order_details(order_id, kite, user=None):
    last_error = None
    latest_history = None
    for attempt in range(1, ZERODHA_ORDER_HISTORY_ATTEMPTS + 1):
        try:
            order_history = kite.order_history(order_id)
            if order_history:
                latest_history = order_history
                latest_status = str(order_history[-1].get("status") or "").strip().upper()
                logger.info(f"{user} : order history attempt {attempt}, status {latest_status}: {order_history}")
                if latest_status in ZERODHA_TERMINAL_ORDER_STATUSES:
                    return order_history
                last_error = f"Order remains non-terminal with status {latest_status or 'UNKNOWN'}."
            else:
                last_error = "No order history found for the given order ID."
                logger.info(f"{user}: {last_error}")
        except Exception as e:
            last_error = f"Failed to fetch order history: {str(e)}"
            logger.info(f"{user} : {last_error}")

        if attempt < ZERODHA_ORDER_HISTORY_ATTEMPTS:
            time.sleep(ZERODHA_ORDER_HISTORY_RETRY_SECONDS)

    if latest_history:
        return latest_history
    return {"status": "Failed", "error": last_error or "No order history found for the given order ID."}


def _schedule_zerodha_order_reconciliation(trade_history):
    if not trade_history or not trade_history.pk:
        return

    def enqueue():
        from main.tasks import reconcile_zerodha_order_task

        reconcile_zerodha_order_task.apply_async(
            kwargs={"trade_history_id": trade_history.pk},
            countdown=5,
        )

    transaction.on_commit(enqueue)

def make_serializable(data):
    """Convert non-serializable objects in a data structure to serializable formats"""
    from datetime import datetime  # Import here to ensure it's available
    logger.info("=============================>>>>> make serializable ???")
    
    if isinstance(data, dict):
        return {k: make_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_serializable(v) for v in data]
    elif isinstance(data, datetime):  # Use the directly imported datetime
        return data.isoformat()
    elif isinstance(data, (str, int, float, bool)) or data is None:
        return data
    else:
        return str(data)


def fetch_zerodha_option_ltp(
    kite,
    api_key,
    access_token,
    exchange,
    trading_symbol,
    proxy_config,
    user=None,
    expiry_date=None,
    underlying=None,
):
    quote_key = f"{exchange}:{trading_symbol}"
    instrument = _central_ltp_resolver.resolve(trading_symbol, underlying=underlying)
    if instrument:
        cached_payload = get_live_price(
            instrument_key=instrument.instrument_key,
            max_age_seconds=5,
        )
        if cached_payload and cached_payload.get("is_fresh"):
            ltp = extract_ltp_from_quote_payload(
                cached_payload,
                preferred_keys=(instrument.instrument_key, trading_symbol),
            )
            if ltp is not None:
                logger.info(
                    "[%s] Using central Upstox WebSocket LTP for Zerodha contract %s.",
                    user,
                    trading_symbol,
                )
                return ltp
        central_ltp = fetch_central_upstox_option_ltp(instrument)
        if central_ltp is not None:
            logger.info(
                "[%s] Using central Upstox on-demand LTP for Zerodha contract %s.",
                user,
                trading_symbol,
            )
            return central_ltp

    try:
        ltp_response = kite.ltp(quote_key)
        ltp = extract_ltp_from_quote_payload(ltp_response, preferred_keys=(quote_key, trading_symbol))
        if ltp is not None:
            cache_option_ltp(trading_symbol, ltp, expiry_date=expiry_date, underlying=underlying, source="zerodha-sdk")
            return ltp
        logger.warning(f"[{user}] Zerodha SDK LTP response did not contain option premium for {quote_key}: {ltp_response}")
    except Exception as exc:
        logger.warning(f"[{user}] Zerodha SDK LTP fetch failed for {quote_key}: {str(exc)}")

    cached_ltp = get_cached_option_ltp(trading_symbol, expiry_date=expiry_date, underlying=underlying)
    if cached_ltp is not None:
        return cached_ltp

    try:
        response = requests.get(
            KITE_LTP_URL,
            headers={
                "X-Kite-Version": "3",
                "Authorization": f"token {api_key}:{access_token}",
            },
            params={"i": quote_key},
            timeout=5,
            proxies=proxy_config,
        )
        payload = response.json() if response.content else {}
        if response.status_code != 200:
            logger.warning(f"[{user}] Zerodha REST LTP fetch failed for {quote_key}: {response.status_code} {payload}")
            return fetch_nse_option_chain_ltp(
                trading_symbol,
                expiry_date=expiry_date,
                underlying=underlying,
                proxy_config=proxy_config,
                user=user,
            )
        ltp = extract_ltp_from_quote_payload(payload, preferred_keys=(quote_key, trading_symbol))
        if ltp is None:
            logger.warning(f"[{user}] Zerodha REST LTP response did not contain option premium for {quote_key}: {payload}")
            return fetch_nse_option_chain_ltp(
                trading_symbol,
                expiry_date=expiry_date,
                underlying=underlying,
                proxy_config=proxy_config,
                user=user,
            )
        cache_option_ltp(trading_symbol, ltp, expiry_date=expiry_date, underlying=underlying, source="zerodha-rest")
        return ltp
    except Exception as exc:
        logger.warning(f"[{user}] Zerodha REST LTP fetch failed for {quote_key}: {str(exc)}")
        return fetch_nse_option_chain_ltp(
            trading_symbol,
            expiry_date=expiry_date,
            underlying=underlying,
            proxy_config=proxy_config,
            user=user,
        )

def place_zerodha_orders(
    LivePrice, group_service, access_token, Api_key, trade_symbol, transaction_type,
    symbol, quantity, strategy, ordertype, product_type, price, user, Lots, Entry_type,
    Exit_type, Entry_price, Exit_price, EntryQty, ExitQty, webhook_signal, Exchange,
    Segment, Index_Symbol, triggerPrice, trade_order_status, history_id, proxy_config=None,
    buffer_percentage=None):
    logger.info(f"[{user}] Starting Zerodha order for symbol: {symbol}, Index: {Index_Symbol}")
    if not proxy_config:
        return {"data": {"status": "Failed", "message": "Proxy/static-IP execution route is required for Zerodha orders."}}

    try:
        EntryQty = quantity
        smtp_details = CompanySmtpDetails.objects.first()
        default_from_email = smtp_details.email_host_user if smtp_details else "no-reply@example.com"

        order_id = 0
        status = "Failed"
        res_data = "Unknown response"

        order_params = {
            "tradingsymbol": trade_symbol,
            "exchange": Exchange,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "order_type": ordertype,
            "product": product_type,
            "price": price if ordertype.upper() == "LIMIT" else 0,
            "trigger_price": triggerPrice if ordertype.upper() == "SL" else None
        }

        try:
            kite = KiteConnect(api_key=Api_key, proxies=proxy_config)
            kite.set_access_token(access_token)
            profile = kite.profile()
            logger.info(f"[{user}] API key and access token validated successfully.")
        except Exception as e:
            logger.exception(f"[{user}] Error validating API key or access token.")
            status = "Unauthorized"
            message = f"Invalid API credentials for {user}"
            res_data = str(e)
            response = {"data": {"status": status, "message": message}}
            save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, symbol, order_id, status, res_data, message,
                                     strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                     webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha", history_id=history_id)
            return response

        logger.info(f"[{user}] Looking up trading symbol: {trade_symbol}")
        trading_symbol = get_trading_symbol(Exchange, trade_symbol, kite, user)

        if not trading_symbol:
            logger.error(f"[{user}] Trading symbol not found for {trade_symbol}")
            message = "Instrument details not found"
            response = {"data": {"status": status, "message": message}}
            save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, symbol, order_id, status, message, message,
                                     strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                     webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha", history_id=history_id)
            return response

        order_params["tradingsymbol"] = trading_symbol
        requested_order_type = normalize_order_type(ordertype)
        ltp = None
        try:
            ltp = fetch_zerodha_option_ltp(
                kite,
                Api_key,
                access_token,
                Exchange,
                trading_symbol,
                proxy_config,
                user=user,
                underlying=Index_Symbol or symbol,
            )
        except Exception as e:
            logger.warning(f"[{user}] Zerodha LTP fetch failed for {trading_symbol}: {str(e)}")

        if requested_order_type == "LIMIT":
            reference_price = resolve_limit_reference_price(trading_symbol, ltp, LivePrice, Entry_price, Exit_price)
            if ltp is None and reference_price:
                logger.info(
                    f"[{user}] Zerodha LTP unavailable for {trading_symbol}; using fallback reference price {reference_price}."
                )
            effective_buffer_percentage = _zerodha_buffer_percentage(buffer_percentage)
            safe_price_input = _safe_zerodha_limit_input(price, reference_price, trading_symbol, transaction_type, user=user)
            price = resolve_limit_price(safe_price_input, reference_price, transaction_type, buffer_percentage=effective_buffer_percentage)
            if not price:
                message = "Unable to calculate Zerodha option limit price because option live price is unavailable. Please retry after quotes are available or provide an explicit option limit price."
                response = {"data": {"status": "Failed", "message": message}}
                save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, symbol, order_id, "Failed", None, message,
                                         strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                         webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha", history_id=history_id)
                return response
            order_params["price"] = price
        elif requested_order_type == "MARKET":
            order_params["price"] = 0
        order_params["order_type"] = requested_order_type
        logger.info(f"[{user}] Placing order with params: {order_params}")

        try:
            history_order_params = (
                {**order_params, "reference_price": reference_price, "buffer_percentage": effective_buffer_percentage}
                if requested_order_type == "LIMIT"
                else order_params
            )
            order_response = kite.place_order(variety=kite.VARIETY_REGULAR, **order_params)
            order_id = order_response  # Assuming it returns an order_id
            logger.info(f"[{user}] Order placed. Order ID: {order_id}")

            if not order_id:
                logger.error(f"[{user}] No order ID returned.")
                response = {"data": {"status": "Failed", "message": "No order ID returned"}}
                save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, symbol, order_id, "Failed", None, "No order ID returned",
                                         strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                         webhook_signal, Exchange, Segment, Index_Symbol, history_order_params, broker="zerodha", history_id=history_id)
                return response

            order_history_response = get_order_details(order_id, kite, user)
            logger.info(f"[{user}] Fetched order history: {order_history_response}")

            if isinstance(order_history_response, dict) and str(order_history_response.get("status", "")).lower() == "failed":
                logger.warning(f"[{user}] Order history is not available yet: {order_history_response}")
                detail = order_history_response.get("error") or "Order details not found"
                message = f"Order was accepted by Zerodha but final status is pending verification. {detail}"
                response = {"data": {"status": "pending", "message": message, "order_id": order_id}}
                history = save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, order_id, "pending", order_history_response, message,
                                                   strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                                   webhook_signal, Exchange, Segment, Index_Symbol, history_order_params, broker="zerodha", history_id=history_id)
                _schedule_zerodha_order_reconciliation(history)
                return response

            if isinstance(order_history_response, list) and order_history_response:
                latest_status = order_history_response[-1]
                status = latest_status.get("status", "").upper()
                res_data = latest_status

                logger.info(f"[{user}] Order status: {status}")

                TERMINAL_STATUSES = ['COMPLETE', 'REJECTED', 'CANCELLED']
                PENDING_STATUSES = [
                    'PUT ORDER REQ RECEIVED', 'VALIDATION PENDING', 'OPEN PENDING',
                    'MODIFY VALIDATION PENDING', 'MODIFY PENDING', 'TRIGGER PENDING',
                    'CANCEL PENDING', 'AMO REQ RECEIVED'
                ]

                transaction_type = res_data.get('transaction_type', '')

                if status in TERMINAL_STATUSES:
                    if status == 'COMPLETE':
                        message = latest_status.get('status_message', "Order completed successfully")
                        trade_order_status = "OPEN" if transaction_type == "BUY" else "CLOSE"
                        if transaction_type == "BUY":
                            Entry_type, Entry_price, EntryQty = "LE", res_data.get('average_price', 0.0), res_data.get('filled_quantity', 0)
                        else:
                            Exit_type, Exit_price, ExitQty = "LX", res_data.get('average_price', 0.0), res_data.get('filled_quantity', 0)

                    elif status == 'REJECTED':
                        message = latest_status.get('status_message', "Order rejected")
                        if transaction_type == "BUY":
                            Entry_type, Entry_price, EntryQty = "LE", res_data.get('average_price', 0.0), res_data.get('filled_quantity', 0)
                        else:
                            Exit_type, Exit_price, ExitQty = "LX", res_data.get('average_price', 0.0), res_data.get('filled_quantity', 0)

                    elif status == 'CANCELLED':
                        message = latest_status.get('status_message', "Order cancelled")
                        if transaction_type == "BUY":
                            Entry_type, Entry_price, EntryQty = "LE", res_data.get('average_price', 0.0), res_data.get('filled_quantity', 0)
                        else:
                            Exit_type, Exit_price, ExitQty = "LX", res_data.get('average_price', 0.0), res_data.get('filled_quantity', 0)

                    logger.info(f"[{user}] Final order status: {status}, Message: {message}")
                    if res_data is not None:
                        res_data = make_serializable(res_data)
                        logger.info(f"[{user}] Make serializable status: {res_data}")

                    save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                             strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                             webhook_signal, Exchange, Segment, Index_Symbol, history_order_params, broker="zerodha", history_id=history_id)
                    return {
                        "data": {
                            "status": status.lower(),
                            "message": message,
                            "order_id": order_id,
                            "order_type": requested_order_type,
                            "price": res_data.get("average_price") or order_params.get("price"),
                            "ltp": ltp,
                            "reference_price": reference_price if requested_order_type == "LIMIT" else ltp,
                        }
                    }

                elif status in PENDING_STATUSES:
                    message = f"{user} : Order is in pending state: {status}"
                    logger.info(f"[{user}] ----------+----------  {message}")
                    if res_data is not None:
                        res_data = make_serializable(res_data)
                        logger.info(f"[{user}] Make serializable status: {res_data}")

                    history = save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, order_id, "pending", res_data, message,
                                                       strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                                       webhook_signal, Exchange, Segment, Index_Symbol, history_order_params, broker="zerodha", history_id=history_id)
                    _schedule_zerodha_order_reconciliation(history)
                    return {"data": {"status": "pending", "message": message}}

                else:
                    message = latest_status.get("status_message") or f"Zerodha order status is {status}."
                    logger.info(f"[{user}] Non-terminal status: {status}")
                    history = save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                                       strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                                       webhook_signal, Exchange, Segment, Index_Symbol, history_order_params, broker="zerodha", history_id=history_id)
                    _schedule_zerodha_order_reconciliation(history)
                    return {
                        "data": {
                            "status": status,
                            "message": message,
                            "order_id": order_id,
                            "order_type": requested_order_type,
                            "price": order_params.get("price"),
                            "ltp": ltp,
                            "reference_price": reference_price if requested_order_type == "LIMIT" else ltp,
                        }
                    }

            else:
                logger.error(f"[{user}] Unknown order response format.")
                message = "Unknown response format from get_order_details"
                save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, order_id, "Failed", None, message,
                                         strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                         webhook_signal, Exchange, Segment, Index_Symbol, history_order_params, broker="zerodha", history_id=history_id)
                return {"data": {"status": "Failed", "message": message}}

        except Exception as e:
            logger.exception(f"[{user}] Exception during order placement")
            response = {"data": {"status": "Failed", "message": str(e)}}
            save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, order_id, "Failed", None, str(e),
                                     strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                     webhook_signal, Exchange, Segment, Index_Symbol, history_order_params if "history_order_params" in locals() else order_params, broker="zerodha", history_id=history_id)
            return response

    except Exception as e:
        logger.exception(f"[{user}] Exception in outer block of place_zerodha_orders")
        response = {"data": {"status": "Failed", "message": str(e)}}
        save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, 0, "Failed", None, str(e),
                                 strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                 webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha", history_id=history_id)
        return response
