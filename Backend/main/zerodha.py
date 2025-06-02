from django.http import JsonResponse
from kiteconnect import KiteConnect
from main.Alice_Blue_Api import save_trade_order_history
from main.models import ClientBrokerdetails, CompanySmtpDetails
import logging
logger = logging.getLogger('main')

def place_zerodha_orders(
    LivePrice, group_service, access_token, Api_key, trade_symbol, transaction_type,
    symbol, quantity, strategy, ordertype, product_type, price, user, Lots, Entry_type,
    Exit_type, Entry_price, Exit_price, EntryQty, ExitQty, webhook_signal, Exchange,
    Segment, Index_Symbol, triggerPrice, trade_order_status):
    logger.info(f"[{user}] Starting Zerodha order for symbol: {symbol}, Index: {Index_Symbol}")

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
            kite = KiteConnect(api_key=Api_key)
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
                                     webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
            return response

        logger.info(f"[{user}] Looking up trading symbol: {trade_symbol}")
        trading_symbol = get_trading_symbol(Exchange, trade_symbol, kite, user)

        if not trading_symbol:
            logger.error(f"[{user}] Trading symbol not found for {trade_symbol}")
            message = "Instrument details not found"
            response = {"data": {"status": status, "message": message}}
            save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, symbol, order_id, status, message, message,
                                     strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                     webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
            return response

        order_params["tradingsymbol"] = trading_symbol
        logger.info(f"[{user}] Placing order with params: {order_params}")

        try:
            order_response = kite.place_order(variety=kite.VARIETY_REGULAR, **order_params)
            order_id = order_response  # Assuming it returns an order_id
            logger.info(f"[{user}] Order placed. Order ID: {order_id}")

            if not order_id:
                logger.error(f"[{user}] No order ID returned.")
                response = {"data": {"status": "Failed", "message": "No order ID returned"}}
                save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, symbol, order_id, "Failed", None, "No order ID returned",
                                         strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                         webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                return response

            order_history_response = get_order_details(order_id, kite)
            logger.info(f"[{user}] Fetched order history: {order_history_response}")

            if isinstance(order_history_response, dict) and order_history_response.get("error") == "Failed":
                logger.error(f"[{user}] Order history error: {order_history_response}")
                message = "Order details not found"
                response = {"data": {"status": "Failed", "message": message}}
                save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, symbol, order_id, "Failed", order_history_response.get("error"), message,
                                         strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                         webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
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

                    save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                             strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                             webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                    return {"data": {"status": status.lower(), "message": message}}

                elif status in PENDING_STATUSES:
                    message = f"Order is in pending state: {status}"
                    logger.info(f"[{user}] ----------+----------  {message}")
                    if res_data is not None:
                        res_data = make_serializable(res_data)

                    save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, order_id, "pending", res_data, message,
                                             strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                             webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                    return {"data": {"status": "pending", "message": message}}

                else:
                    message = latest_status.get("status_message", "Success")
                    logger.info(f"[{user}] Non-terminal status: {status}")
                    save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                             strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                             webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                    return {"data": {"status": status, "message": message}}

            else:
                logger.error(f"[{user}] Unknown order response format.")
                message = "Unknown response format from get_order_details"
                save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, order_id, "Failed", None, message,
                                         strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                         webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                return {"data": {"status": "Failed", "message": message}}

        except Exception as e:
            logger.exception(f"[{user}] Exception during order placement")
            response = {"data": {"status": "Failed", "message": str(e)}}
            save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, order_id, "Failed", None, str(e),
                                     strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                     webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
            return response

    except Exception as e:
        logger.exception(f"[{user}] Exception in outer block of place_zerodha_orders")
        response = {"data": {"status": "Failed", "message": str(e)}}
        save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, 0, "Failed", None, str(e),
                                 strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                 webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
        return response

def get_trading_symbol(exchange, symbol, kite, user=None):
    try:
        instruments = kite.instruments(exchange)
        for instrument in instruments:
            if instrument['tradingsymbol'] == symbol:
                logger.info(f"[{user}] Trading Symbol Found: {instrument['tradingsymbol']}")
                return instrument['tradingsymbol']
        logger.warning(f"[{user}] Trading symbol '{symbol}' not found in exchange '{exchange}'")
        return None
    except Exception as e:
        logger.exception(f"[{user}] Exception occurred while fetching trading symbol '{symbol}' from exchange '{exchange}'")
        return None

def get_order_details(order_id, kite):
    try:
        # Fetch order history
        # kite = KiteConnect(api_key=api_key)
        # kite.set_access_token(access_token)
        order_history = kite.order_history(order_id)
        # print("order_history>>>",order_history)
        if order_history:
            return order_history
        else:
            return {"status": "Failed", "error": "No order history found for the given order ID."}
    except Exception as e:
        return {"status": "Failed", "error": f"Failed to fetch order history: {str(e)}"}



def make_serializable(data):
    """Convert non-serializable objects in a data structure to serializable formats"""
    from datetime import datetime  # Import here to ensure it's available
    
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
