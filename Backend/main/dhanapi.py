from datetime import datetime
import os
import re
from time import sleep
from dhanhq import dhanhq 
import logging
import time
from django.conf import settings
import requests

from main.broker_instrument_cache import (
    ensure_dhan_instruments_file,
    get_dhan_instrument,
    get_dhan_lot_size,
)
from main.brokers.exchange_mapping import normalize_broker_exchange
from main.models import CompanySmtpDetails
from main.tasks import send_trade_email_async
from main.broker_order_utils import extract_ltp_from_quote_payload, normalize_order_type, resolve_limit_price, resolve_limit_reference_price, to_float
from main.services.live_price_cache import get_live_price
from main.services.option_ltp_fallback import fetch_nse_option_chain_ltp
from main.services.upstox_market_data import (
    fetch_central_upstox_option_ltp,
    get_upstox_instrument_resolver,
)
from main.trade_history_service import save_trade_order_history
logger = logging.getLogger('main')
DHAN_LTP_URL = "https://api.dhan.co/v2/marketfeed/ltp"
DHAN_NON_FINAL_STATUSES = {"", "unknown", "transit", "pending", "open", "validation pending"}
DHAN_TERMINAL_FAILURE_STATUSES = {"rejected", "cancelled", "canceled", "expired"}


def _dhan_option_contract_parts(trading_symbol, expiry_date=None, underlying=None):
    raw_symbol = re.sub(r"[^A-Z0-9]", "", str(trading_symbol or "").upper())
    under = re.sub(r"[^A-Z0-9]", "", str(underlying or "").upper())
    if not raw_symbol:
        return None
    if not under:
        match = re.match(r"^(?P<under>[A-Z]+)", raw_symbol)
        under = match.group("under") if match else ""
    if not under or not raw_symbol.startswith(under):
        return None
    match = re.match(
        r"^(?P<mon>JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
        r"(?P<year>20\d{2})(?P<strike>\d+(?:\.\d+)?)(?P<opt>CE|PE)$",
        raw_symbol[len(under):],
    )
    if not match:
        return None
    expiry = str(expiry_date or "").strip()
    if not expiry:
        month = datetime.strptime(match.group("mon").title(), "%b").month
        expiry = f"{match.group('year')}-{month:02d}-01"
    return {
        "underlying": under,
        "expiry_date": expiry,
        "strike": float(match.group("strike")),
        "option_type": match.group("opt"),
    }


def _fetch_central_dhan_option_ltp(trading_symbol, *, expiry_date=None, underlying=None, user=None):
    payload = get_live_price(
        trading_symbol=trading_symbol,
        max_age_seconds=3,
    )
    if payload and payload.get("is_fresh"):
        ltp = to_float(payload.get("ltp"))
        if ltp and ltp > 0:
            logger.info("%s : Using central websocket option premium for Dhan %s.", user, trading_symbol)
            return float(ltp)

    contract = _dhan_option_contract_parts(trading_symbol, expiry_date=expiry_date, underlying=underlying)
    if not contract:
        return None
    payload = get_live_price(max_age_seconds=3, **contract)
    if payload and payload.get("is_fresh"):
        ltp = to_float(payload.get("ltp"))
        if ltp and ltp > 0:
            logger.info("%s : Using central websocket option premium for Dhan %s.", user, trading_symbol)
            return float(ltp)
    return None


def fetch_dhan_option_ltp(
    dhan_client,
    client_id,
    access_token,
    exchange,
    security_id,
    proxy_config,
    user=None,
    trading_symbol=None,
    expiry_date=None,
    underlying=None,
):
    security_id_int = int(security_id)
    security_id_key = str(security_id_int)
    central_ltp = _fetch_central_dhan_option_ltp(
        trading_symbol,
        expiry_date=expiry_date,
        underlying=underlying,
        user=user,
    )
    if central_ltp is not None:
        return central_ltp

    contract = _dhan_option_contract_parts(
        trading_symbol,
        expiry_date=expiry_date,
        underlying=underlying,
    )
    if contract:
        instrument = get_upstox_instrument_resolver().resolve_contract(**contract)
        if instrument:
            upstox_ltp = fetch_central_upstox_option_ltp(instrument)
            if upstox_ltp is not None:
                logger.info(
                    "%s : Using central Upstox on-demand option premium for Dhan %s.",
                    user,
                    trading_symbol,
                )
                return float(upstox_ltp)

    try:
        response = requests.post(
            DHAN_LTP_URL,
            headers={
                "Content-Type": "application/json",
                "access-token": access_token,
                "client-id": str(client_id),
            },
            json={exchange: [security_id_int]},
            timeout=5,
            proxies=proxy_config,
        )
        payload = response.json() if response.content else {}
        if response.status_code == 200:
            ltp = extract_ltp_from_quote_payload(payload, preferred_keys=(exchange, security_id_key, security_id_int))
            if ltp is not None:
                return ltp
            logger.warning(
                f"{user} : Dhan REST LTP response did not contain option premium for "
                f"exchange {exchange}, security_id {security_id_key}: {payload}"
            )
        else:
            logger.warning(f"{user} : Dhan REST LTP fetch failed for security_id {security_id_key}: {response.status_code} {payload}")
    except Exception as exc:
        logger.warning(f"{user} : Dhan REST LTP fetch failed for security_id {security_id_key}: {str(exc)}")

    try:
        if hasattr(dhan_client, "get_ltp_data"):
            ltp_response = dhan_client.get_ltp_data({exchange: [security_id_int]})
            ltp = extract_ltp_from_quote_payload(
                ltp_response,
                preferred_keys=(exchange, security_id_key, security_id_int),
            )
            if ltp is not None:
                return ltp
            logger.warning(
                f"{user} : Dhan SDK LTP response did not contain option premium for "
                f"exchange {exchange}, security_id {security_id_key}: {ltp_response}"
            )
    except Exception as exc:
        logger.warning(f"{user} : Dhan SDK LTP fetch failed for security_id {security_id_key}: {str(exc)}")

    if trading_symbol:
        return fetch_nse_option_chain_ltp(
            trading_symbol,
            expiry_date=expiry_date,
            underlying=underlying,
            proxy_config=proxy_config,
            user=user,
        )
    return None

def fetch_order_details(order_id,dhan, user=None):
    try:
        response = dhan.get_order_by_id(order_id)
        if response['status'] == 'success':
            return response
            # print(f"Order details fetched successfully: {response}")
        else:
            logger.info(f"{user} : Failed to fetch order details: {response['remarks']['error_message']}")
    except Exception as e:
        logger.info(f"{user} : Error while fetching order details: {str(e)}")


def _dhan_order_record(order_history_response):
    if not isinstance(order_history_response, dict):
        return None
    data = order_history_response.get("data")
    if isinstance(data, list):
        return data[0] if data else None
    if isinstance(data, dict):
        return data
    return None


def _dhan_order_status(order_record):
    if not isinstance(order_record, dict):
        return ""
    return str(order_record.get("orderStatus") or order_record.get("status") or "").strip().lower()


def _dhan_order_message(order_record, default_message=""):
    if not isinstance(order_record, dict):
        return default_message
    for key in (
        "omsErrorDescription",
        "errorDescription",
        "errorMessage",
        "error_message",
        "message",
        "remarks",
        "reason",
    ):
        value = order_record.get(key)
        if isinstance(value, dict):
            nested = value.get("error_message") or value.get("message")
            if nested:
                return str(nested)
        elif value not in (None, "", [], {}):
            return str(value)
    return default_message


def _fetch_dhan_order_details_with_poll(order_id, dhan, user=None, attempts=4, delay_seconds=1):
    latest_response = None
    latest_record = None
    for attempt in range(attempts):
        latest_response = fetch_order_details(order_id, dhan, user)
        latest_record = _dhan_order_record(latest_response)
        status = _dhan_order_status(latest_record)
        if status and status not in DHAN_NON_FINAL_STATUSES:
            return latest_response, latest_record
        if attempt < attempts - 1:
            sleep(delay_seconds)
    return latest_response, latest_record


def _is_dhan_invalid_token_message(message):
    return "invalid token" in str(message or "").lower()


def _mark_dhan_token_expired_if_needed(user, message):
    if not _is_dhan_invalid_token_message(message) or not user:
        return
    try:
        from main.models import ClientBrokerdetails

        broker_details = ClientBrokerdetails.objects.filter(
            client=user,
            broker_name__broker_name__iexact="Dhan",
        ).first()
        if broker_details and not broker_details.isTokenExpired:
            broker_details.isTokenExpired = True
            broker_details.save(update_fields=["isTokenExpired"])
            logger.warning(f"{user} : Dhan token marked expired after broker returned Invalid Token.")
    except Exception as exc:
        logger.exception(f"{user} : Failed to mark Dhan token expired: {exc}")


def _schedule_dhan_order_reconciliation(history, order_id, user=None):
    if not history or not getattr(history, "id", None):
        return
    try:
        from main.tasks import reconcile_broker_order_task

        reconcile_broker_order_task.apply_async(
            kwargs={"trade_history_id": history.id},
            countdown=5,
        )
    except Exception as exc:
        logger.warning(
            "%s : Could not queue Dhan broker reconciliation for order %s: %s",
            user,
            order_id,
            exc,
        )


def get_trading_symbol_security_id(symbol, segment, Exch,expiry_date, user=None):
    logger.info(f"{user}: the get_trading_symbol_security_id is calling now !")
    try:
        instrument = get_dhan_instrument(symbol, expiry_date)
        if instrument:
            SECURITY_ID = instrument["security_id"]
            logger.info(f"{user}: SECURITY_ID is not empty : {SECURITY_ID}")
            return {"status": "success", "SECURITY_ID": SECURITY_ID}
        else:
            status={"status": "error", "message": f"{user} : No records found matching the given symbol and exchange."}
            logger.info(f"{status}")
            return  None
    
    except Exception as e:
        msg= f"{user} : status is :error An error occurred.details: {str(e)}"
        logger.info(f"{msg}")
        return  None

def place_dhan_orders(expiry_date,LivePrice,group_service,access_token, client_id, trade_symbol, transaction_type, symbol, quantity,
    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, 
    EntryQty, ExitQty, webhook_signal, Exchange, Segment,Index_Symbol, triggerPrice, trade_order_status, history_id,
    proxy_config=None):
    timing_started = time.perf_counter()
    timing_checkpoint = timing_started

    def log_timing(stage):
        nonlocal timing_checkpoint
        now_value = time.perf_counter()
        logger.info(
            "%s : Dhan execution timing stage=%s stage_ms=%.1f total_ms=%.1f",
            user,
            stage,
            (now_value - timing_checkpoint) * 1000,
            (now_value - timing_started) * 1000,
        )
        timing_checkpoint = now_value

    logger.info(f'{user} : dhan api  Exchange is:: {Exchange} product typweeee {product_type}')
    if not proxy_config:
        return {"data": {"status": "Failed", "message": "Proxy/static-IP execution route is required for Dhan orders."}}
    
    try:
        EntryQty=quantity
        Index_Symbol = symbol
        smtp_details=CompanySmtpDetails.objects.first()
        default_from_email=smtp_details.email_host_user if smtp_details else   "no-reply@example.com" 
        order_id = 0
        status = "Failed"
        res_data = "Unknown response"
        # Prepare order parameters
        order_params = {
            "tradingsymbol": trade_symbol,
            "exchange_segment": Exchange,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "order_type": ordertype,
            "security_id":0,
            "product": product_type,
            "price": price if ordertype.upper() == "LIMIT" else 0,
            "trigger_price": triggerPrice if ordertype.upper() == "SL" else None
        }
        try:
            dhan = dhanhq(client_id, access_token)
            if proxy_config and hasattr(dhan, "session"):
                dhan.session.proxies.update(proxy_config)
            logger.info(f"{user}: API key and access token are valid.")
            log_timing("authentication")
        except Exception as e:
            logger.error(f"{user}: Error validating API key or access token: {str(e)}")
            status = "Failed"
            message = f"{user}: API key and access token are Not valid for. {user}"
            res_data = f"{str(e)}"
            response={"data": {"status": status,"message":message}}
            logger.info(f'{user} : This is exception error in Dhan api {response}')
            _mark_dhan_token_expired_if_needed(user, message)
            save_trade_order_history(LivePrice,group_service,transaction_type,"Failed", user, trade_symbol, order_id, status, res_data, message,  
                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
            return response

        trading_symbol = get_trading_symbol_security_id(trade_symbol, dhan,Exchange,expiry_date, user)
        log_timing("instrument_lookup")
        if not trading_symbol:
            logger.error(f"{user} : trading_symbol details not found for {trade_symbol}")
            message = "Instrument details not found"
            res_data = "Trading symbol not found."
            response={"data": {"status": status,"message":message}}
            save_trade_order_history(LivePrice,group_service,transaction_type,"Failed", user, trade_symbol, order_id, status, res_data, message,  
                    strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                    webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
            return response

        logger.info(f"{user} : webhooks Fetched dhan trading_symbol: {trading_symbol}")
        security_id = trading_symbol.get('SECURITY_ID', 0) 
        quantity = int(quantity) 
        Exchange = normalize_broker_exchange("dhan", exchange=Exchange, underlying=symbol)
        if Exchange=="NFO":
            Exchange=dhan.NSE_FNO
        elif Exchange=="NSE":
            Exchange= dhan.NSE
        elif Exchange in {"BSE", "BFO", "BSE_FO", "BSE_FNO"}:
            Exchange = getattr(dhan, "BSE_FNO", "BSE_FNO")
        if product_type.upper() in ["NRML", "NORMAL"]:
            product_type = dhan.NORMAL
        elif product_type.upper() in ["MIS", "INTRADAY"]:
            product_type = dhan.INTRA
        elif product_type.upper() in ["CNC", "DELIVERY"]:
            product_type = dhan.CNC
        else:
            logger.info(f"{user} : Invalid product type: {product_type}")
            return {"status": "error", "message": "Invalid product type"}

        # Validate transaction_type
        if transaction_type.upper() == "BUY":
            transaction_type = dhan.BUY
        elif transaction_type.upper() == "SELL":
            transaction_type = dhan.SELL
        else:
            logger.info(f"{user} : Invalid transaction type: {transaction_type}")
            return {"status": "error", "message": "Invalid transaction type"}

        requested_order_type = normalize_order_type(ordertype)
        ltp = None
        try:
            ltp = fetch_dhan_option_ltp(
                dhan,
                client_id,
                access_token,
                Exchange,
                security_id,
                proxy_config,
                user=user,
                trading_symbol=trade_symbol,
                expiry_date=expiry_date,
                underlying=symbol,
            )
        except Exception as e:
            logger.warning(f"{user} : Dhan LTP fetch failed for security_id {security_id}: {str(e)}")
        log_timing("ltp_resolution")

        if requested_order_type == "LIMIT":
            reference_price = resolve_limit_reference_price(trade_symbol, ltp, LivePrice, Entry_price, Exit_price)
            if ltp is None and reference_price:
                logger.info(
                    f"{user} : Dhan LTP unavailable for security_id {security_id}; using fallback reference price {reference_price}."
                )
            price = resolve_limit_price(price, reference_price, transaction_type)
            if not price:
                message = "Unable to calculate Dhan option limit price because option live price is unavailable. Please retry after quotes are available or provide an explicit option limit price."
                response = {"data": {"status": "Failed", "message": message}}
                save_trade_order_history(LivePrice,group_service,transaction_type,"Failed", user, trade_symbol, order_id, "Failed", None, message,
                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response
        elif requested_order_type == "MARKET":
            price = 0

        # Validate order_type
        if requested_order_type == "MARKET":
            ordertype = dhan.MARKET
        elif requested_order_type == "LIMIT":
            ordertype = dhan.LIMIT
        elif requested_order_type == "SL":
            ordertype = dhan.SL
        else:
            print("Invalid order type:", ordertype)
            logger.info(f"{user} : Invalid order type: {ordertype}")
            return {"status": "error", "message": "Invalid order type"}

        # Reconstruct order_params with valid values
        order_params = {
            "transaction_type": transaction_type,
            "exchange_segment": Exchange,
            "product_type": product_type,
            "order_type": ordertype,
            "validity": "DAY",
            "security_id": int(security_id),
            "quantity": int(quantity),
            "price": float(price) if ordertype == dhan.LIMIT else 0,
            "trigger_price": float(triggerPrice) if ordertype == dhan.SL else 0,
        }
        logger.info(f"{user} : Final order_params dhan order:{order_params}")
        try:    
            # Validate quantity against the prebuilt security-id index.
            try:
                lot_size = get_dhan_lot_size(security_id, symbol=trade_symbol, expiry_date=expiry_date)
                if lot_size and quantity % lot_size != 0:
                    message = f"{user} : Invalid quantity {quantity}. Must be multiple of lot size {lot_size}"
                    logger.error(message)
                    response = {"data": {"status": "Failed", "message": message}}
                    save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status,
                                        user, trade_symbol, order_id, "Failed", None, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price,
                                        EntryQty, ExitQty, webhook_signal, Exchange, Segment,
                                        Index_Symbol, order_params, broker="dhan", history_id=history_id)
                    return response
                if lot_size is None:
                    logger.warning(f"{user} : No lot size data found for security_id {security_id}")
            except Exception as e:
                logger.warning(f"{user} : Could not validate lot size: {str(e)}")
            log_timing("lot_validation")
            order_response = dhan.place_order(**order_params)
            log_timing("broker_submission")
            logger.info(f"{user} : order_response {order_response}")
            # Fetch order ID and validate response
            if order_response.get('status') == 'failure':
                message=order_response.get('remarks', {}).get('error_message', "Unknown error occurred.")
                res_data = order_response
                status='Failed'
                response={"data": {"status": status,"message":message}}
                logger.info(f"{user} : order_response status is failure ??")
                _mark_dhan_token_expired_if_needed(user, message)
                save_trade_order_history(LivePrice,group_service,transaction_type,"Failed", user, trade_symbol, order_id, status, res_data, message,
                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response
            order_id = order_response.get('data', {}).get('orderId')
            if not order_id:
                logger.error(f"{user} : Order ID is not returned")
                status = "Failed"
                message = order_response.get('error_message',"")
                res_data = order_response.get(order_response,"No order ID returned")
                response={"data": {"status": status,"message":message}}
                _mark_dhan_token_expired_if_needed(user, message)
                save_trade_order_history(LivePrice,group_service,transaction_type,"Failed", user, trade_symbol, order_id, status, res_data, message,
                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response

            logger.info(f"{user} : order id {order_id}")
            if str(transaction_type).upper() == "BUY":
                status = "open"
                message = "Dhan accepted the order. Confirmation is continuing in the background."
                history = save_trade_order_history(
                    LivePrice, group_service, transaction_type, trade_order_status,
                    user, trade_symbol, order_id, status, order_response, message,
                    strategy, Entry_type, Exit_type, Entry_price, Exit_price,
                    EntryQty, ExitQty, webhook_signal, Exchange, Segment,
                    Index_Symbol, order_params, broker="dhan", history_id=history_id,
                )
                _schedule_dhan_order_reconciliation(history, order_id, user)
                return {
                    "data": {
                        "status": "open",
                        "broker_status": "accepted",
                        "reconciliation_scheduled": True,
                        "message": message,
                        "order_id": order_id,
                        "order_type": requested_order_type,
                        "price": price if requested_order_type == "LIMIT" else None,
                        "ltp": ltp,
                        "reference_price": ltp,
                    }
                }
            order_history_response, res_data = _fetch_dhan_order_details_with_poll(order_id, dhan, user)
            log_timing("broker_confirmation")
            logger.info(f"{user} : Order history response: {order_history_response}")

            if not res_data:
                status = "Failed"
                message = "Dhan order was placed, but broker order details could not be fetched. Please check Dhan order book before retrying."
                response = {"data": {"status": status, "message": message, "order_id": order_id}}
                save_trade_order_history(LivePrice,group_service,transaction_type,"Failed", user, trade_symbol, order_id, status, order_history_response, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response

            # TRANSIT PENDING REJECTED CANCELLED TRADED EXPIRED
            status = _dhan_order_status(res_data) or "unknown"
            logger.info(f"{user} : status dhan api res _data {status}")
            
            if not status or status==None:
                status = "Failed"
                order_id=0
                message =  'None response from api '
                response = {"data": {"status": status,"message":message}}
                logger.info(f"Order response if None for user {user}. Order ID: {order_id}")

                save_trade_order_history(LivePrice,group_service,transaction_type,"Failed", user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response
            
            elif status.lower() == 'complete' or status.lower()=="traded" or status.upper()=="TRADED":
                message = _dhan_order_message(res_data, "Order complete")
                logger.info(f"{user} : Order placed successfully. Order ID: {order_id}")
                transaction_type = res_data.get('transactionType', '')
                status=status.lower()
                
                if transaction_type == "BUY":
                    trade_order_status="OPEN"
                    Entry_type = "LE"
                    Entry_price = res_data.get('averageTradedPrice', 0.0)
                    EntryQty = res_data.get('quantity', 0)
                elif transaction_type == "SELL":
                    trade_order_status="CLOSE"
                    Exit_type = "LX"
                    Exit_price = res_data.get('averageTradedPrice', 0.0)
                    ExitQty = res_data.get('quantity', 0)
                
                response = {
                    "data": {
                        "status": "completed",
                        "message": "Order placed and details saved successfully.",
                        "order_id": order_id,
                        "order_type": requested_order_type,
                        "price": res_data.get("averageTradedPrice") or order_params.get("price"),
                        "ltp": ltp,
                        "reference_price": ltp,
                    }
                }
                logger.info(f"{user} : Order placed and details saved successfully for the Dhan.")
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response
            elif status.lower() == "rejected":
                message = _dhan_order_message(res_data, "Dhan rejected the order.")
                transaction_type = res_data.get('transactionType', '')
                if transaction_type == "BUY":
                    Entry_type = "LE"
                    Entry_price = res_data.get('averageTradedPrice', 0.0)
                    EntryQty = res_data.get('quantity', 0)
                elif transaction_type == "SELL":
                    Exit_type = "LX"
                    Exit_price = res_data.get('averageTradedPrice', 0.0)
                    ExitQty = res_data.get('quantity', 0)
                send_trade_email_async.delay(user.email, default_from_email, user.firstName, status, message)
                response = {"data": {"status": status,"message":message}}
                logger.info(f"Order is rejected for user {user}. Order ID: {order_id}")
                _mark_dhan_token_expired_if_needed(user, message)
                save_trade_order_history(LivePrice,group_service,transaction_type,"Failed", user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response
            elif status.lower() == "pending":
                message = _dhan_order_message(res_data, "Dhan order is pending.")
                transaction_type = res_data.get('transactionType', '')
                
                if transaction_type == "BUY":
                    Entry_type = "LE"
                    Entry_price = res_data.get('averageTradedPrice', 0.0)
                    EntryQty = res_data.get('quantity', 0)
                elif transaction_type == "SELL":
                    Exit_type = "LX"
                    Exit_price = res_data.get('averageTradedPrice', 0.0)
                    ExitQty = res_data.get('quantity', 0)
                response = {"data": {"status": status,"message":message}}
                logger.info(f"Order is pending for user {user}. Order ID: {order_id}")
                
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response
            elif status.lower() == "transit" or status == "TRANSIT":
                message = _dhan_order_message(res_data, "Dhan accepted the order and it is in transit.")
                transaction_type = res_data.get('transactionType', '')
                if transaction_type == "BUY":
                    Entry_type = "LE"
                    Entry_price = res_data.get('averageTradedPrice', 0.0)
                    EntryQty = res_data.get('quantity', 0)
                elif transaction_type == "SELL":
                    Exit_type = "LX"
                    Exit_price = res_data.get('averageTradedPrice', 0.0)
                    ExitQty = res_data.get('quantity', 0)
                response = {"data": {"status": status,"message":message}}
                logger.info(f"Order is TRANSIT for user {user}. Order ID: {order_id}")
                
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response
            else:
                message = _dhan_order_message(res_data, "Dhan order status could not be resolved.")
                response = {"data": {"status": status,"message":message}}
                if status:
                    status="Failed"
                response= {"data": {"status": "Failed","message": "Order placed but details could not be fetched."}}
                logger.info(f"Order is TRANSIT for user {user}. Order ID: {order_id}")

                _mark_dhan_token_expired_if_needed(user, message)
                save_trade_order_history(LivePrice,group_service,transaction_type,"Failed", user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response     
        except Exception as e:
            error_message = f"{user} : Failed to place order: {str(e)}"
            logger.error(error_message)
            order_id = 0
            response = {"data": {"status": "Failed", "message": str(e)}}
            print("error in dhan api :::::",{str(e)})
            Index_Symbol = symbol
            
            _mark_dhan_token_expired_if_needed(user, str(e))
            save_trade_order_history(LivePrice,group_service,transaction_type,"Failed", user, trade_symbol, order_id, "Failed", None, str(e),
                                strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal, Exchange,
                                    Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
            return response

    except Exception as e:
        logger.error(f"{user} : Exception in dhan order placement: {str(e)}")
        error_message = f"Failed to place order: {str(e)}"
        logger.error(error_message)
        order_id = 0
        response={"data": {"status": "error","message": str(e)}}
        _mark_dhan_token_expired_if_needed(user, str(e))
        save_trade_order_history(LivePrice,group_service,transaction_type,"Failed", user, trade_symbol, order_id, "Failed", None, str(e),
                                    strategy, Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal, Exchange,
                                    Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
        return response
