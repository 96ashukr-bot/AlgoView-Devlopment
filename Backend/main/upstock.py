
import requests
import json
import re
from django.shortcuts import redirect
from django.http import JsonResponse
from main.models import CompanySmtpDetails
from main.broker_instrument_cache import load_upstox_instruments
from main.broker_order_utils import normalize_order_type, resolve_limit_price, resolve_limit_reference_price
from main.trade_history_service import save_trade_order_history
import logging
logger = logging.getLogger('main')
from datetime import datetime
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLACE__ORDER_URL="https://api-hft.upstox.com/v2/order/place"
MARKET_QUOTE_LTP_URL = "https://api.upstox.com/v2/market-quote/ltp"


def _response_json_or_error(response):
    try:
        return response.json() if getattr(response, "content", b"") else {}
    except ValueError:
        return {
            "status": "error",
            "message": "Broker returned a non-JSON response.",
            "raw_response": getattr(response, "text", ""),
        }

def get_upstox_login_url(request):
    return redirect("/broker_auth_login/?broker=upstox")

def callback_upstox(request):
    from main.dematemodule import BrokerCallbackView

    return BrokerCallbackView.as_view()(request)

def place_upstox_orders(LivePrice,group_service,
    access_token, trade_symbol, transaction_type, symbol, quantity, strategy, ordertype,
    product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price, EntryQty,ExitQty,webhook_signal, Exchange,
    Segment, Index_Symbol, triggerPrice,trade_order_status, history_id, proxy_config=None):
    if not proxy_config:
        return {"data": {"status": "Failed", "message": "Proxy/static-IP execution route is required for Upstox orders."}}
    try:
        EntryQty=quantity
        smtp_details=CompanySmtpDetails.objects.first()
        default_from_email=smtp_details.email_host_user if smtp_details else   "no-reply@example.com" 
        logger.info(f"{user} : exchnage symbole....{trade_symbol}")
        upstox_exchange = {
            "NFO": "NSE",
            "NSE": "NSE",
            "NSE_EQ": "NSE",
            "NSE_FO": "NSE",
            "NSE_COM": "NSE",
            "BSE": "BSE",
            "BSE_EQ": "BSE",
            "BSE_FO": "BSE",
            "MCX": "MCX",
            "MCX_FO": "MCX",
        }.get(str(Exchange or "").upper(), "NSE")
        result = fetch_instrument_details(trade_symbol, upstox_exchange, user)
        
        logger.info(f"{user} : The exchange result is : {result}")
        if result.get("trading_symbol"):
            trade_symbol = result["trading_symbol"]
        status="Failed"
        order_id=0
        message=""
        order_params = {
            "quantity": quantity,
            "price": price if ordertype.upper() == "LIMIT" else 0,
            "order_type": ordertype.upper(),
            "transaction_type": transaction_type.upper(),
            'validity': 'DAY',  
            'trigger_price': 0 }
        instrument_key = result.get("instrument_key")
        if not instrument_key:
            logger.error(f"{user} : Instrument details not found for {trade_symbol}. Response: {result}")
            status="Failed"
            message="Instrument details not found"
            res_data=result
            if not trade_symbol:
                trade_symbol=symbol
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
            webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="upstox", history_id=history_id)
            return {
                "data": {
                    "status": "error", "message": "Instrument details not found.",  "error_details": result,}
                }
        logger.info(f"{user} : Fetched Instrument Key: {instrument_key}")
        requested_order_type = normalize_order_type(ordertype)
        ltp = None
        try:
            quote_response = requests.get(
                MARKET_QUOTE_LTP_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                params={"instrument_key": instrument_key},
                timeout=5,
                proxies=proxy_config,
            )
            quote_data = quote_response.json() if quote_response.content else {}
            if quote_response.status_code == 200:
                quote_values = quote_data.get("data", {})
                first_quote = next(iter(quote_values.values()), {}) if isinstance(quote_values, dict) else {}
                ltp = first_quote.get("last_price") or first_quote.get("ltp")
        except Exception as e:
            logger.warning(f"{user} : Upstox LTP fetch failed for {instrument_key}: {str(e)}")

        if requested_order_type == "LIMIT":
            reference_price = resolve_limit_reference_price(trade_symbol, ltp, LivePrice, Entry_price, Exit_price)
            if ltp is None and reference_price:
                logger.info(
                    f"{user} : Upstox LTP unavailable for {instrument_key}; using fallback reference price {reference_price}."
                )
            price = resolve_limit_price(price, reference_price, transaction_type)
            if not price:
                message = "Unable to calculate Upstox option limit price because option live price is unavailable. Please retry after quotes are available or provide an explicit option limit price."
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, "Failed", result, message,
                strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
                webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="upstox", history_id=history_id)
                return {"data": {"status": "Failed", "message": message}}
        elif requested_order_type == "MARKET":
            price = 0
        # Map product types to API-compatible values
        product_mapping = {"NRML": "N", "MIS": "I", "CNC": "D"}
        product_code = product_mapping.get(product_type.upper(), product_type)
        # Construct the order payload
        order_params = {
            "quantity": quantity,
            "product": product_code,
            "price": price if requested_order_type == "LIMIT" else 0,
            "instrument_token": instrument_key,
            "order_type": requested_order_type,
            "transaction_type": transaction_type.upper(),
            'validity': 'DAY',  # Order validity (DAY)
            # 'disclosed_quantity': 0,  # Not disclosing partial quantity
            'trigger_price': 0,  # Not required for market orders
            # 'is_amo': False  # Not an After Market Order
        }
        
        headers = {"Authorization": f"Bearer {access_token}"}
        # Place the order
        logger.info(f"{user} : Place the order API is calling for the Upstox !!")
        history_order_params = {**order_params, "reference_price": reference_price} if requested_order_type == "LIMIT" else order_params
        response = requests.post(PLACE__ORDER_URL, headers=headers, json=order_params, timeout=10, proxies=proxy_config)
        response_data = _response_json_or_error(response)

        logger.info(f"{user} : Order API response: {response_data} status code ::{response.status_code}")

        # Handle response based on status
        if response.status_code == 200 and response_data.get("status") == "success":
            order_id = response_data["data"]["order_id"]
            logger.info(f"{user} : Order placed successfully get the Order details for Order ID: {order_id}")
            handled_response = handle_successful_order(LivePrice,group_service,transaction_type,
                order_id, user, trade_symbol, strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal,
                Exchange, Segment, Index_Symbol, history_order_params, access_token,trade_order_status, history_id, proxy_config=proxy_config
            )
            handled_response.setdefault("data", {})
            handled_response["data"].update({
                "order_id": order_id,
                "order_type": requested_order_type,
                "price": price if requested_order_type == "LIMIT" else None,
                "ltp": ltp,
                "reference_price": reference_price if requested_order_type == "LIMIT" else ltp,
            })
            return handled_response
        elif response.status_code == 401:
            logger.error(f"{user} : Unauthorized access for user {user}. Reason: {response_data.get('message', 'Unknown')}")
            status= "Unauthorized"
            message="Unauthorized access"
            res_data=response_data
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
            webhook_signal , Exchange, Segment,Index_Symbol ,history_order_params,broker="upstox", history_id=history_id)
            return {
                "data": {  "status": "Unauthorized", "message": "Unauthorized access. Please check your token."}
            }
        elif response.status_code == 404:
            res_data=response_data.get('errors', 'Unknown')
            logger.error(f"{user} : Resource not Found. Reason: {res_data}")
            status= "errors"
            message="Resource not Found 404"
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
            webhook_signal , Exchange, Segment,Index_Symbol ,history_order_params,broker="upstox", history_id=history_id)
            return { "data": {"status": "error","message":res_data}}
        elif response.status_code == 400:
            errors = response_data.get("errors", [])
            
            # Extract the first error message if available, otherwise use a default message
            if errors and isinstance(errors, list):
                message = errors[0].get("message", "Unknown error occurred")
            else:
                message = "Unknown error occurred"

            logger.error(f"{user} : Resource not Found. Reason: {message}")
            
            status = "errors"
            res_data = response_data if response_data else "Unknown error"

            save_trade_order_history(
                LivePrice, group_service,transaction_type, trade_order_status, user, trade_symbol, order_id,
                status, res_data, message, strategy, Entry_type, Exit_type, Entry_price, Exit_price,
                EntryQty, ExitQty, webhook_signal, Exchange, Segment, Index_Symbol, history_order_params, broker="upstox", history_id=history_id
            )

            return {"data": {"status": "error", "message": message}}
       
        else:
            logger.error(f"{user} : Order placement Failed. Response: {response_data}")
            status="error"
            message="Order placement Failed"
            res_data=response_data
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
            webhook_signal , Exchange, Segment,Index_Symbol ,history_order_params,broker="upstox", history_id=history_id)
            return {"data": { "status": "Failed", "message": "Order placement Failed.",  "error_details": response_data}}
    except Exception as e:
        logger.exception(f"{user} : Unexpected error while placing order for {symbol}: {str(e)}")
        return {
            "data": { "status": "error","message": "Unexpected error occurred.","error_details": str(e)}
            }

def handle_successful_order(LivePrice,group_service,transaction_type,
    order_id, user, trade_symbol, strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal, Exchange,
    Segment, Index_Symbol, order_params, access_token,trade_order_status, history_id, proxy_config=None):
    try:
        EntryQty=order_params['quantity']
        order_details = get_order_details(order_id, access_token, proxy_config=proxy_config)
        logger.info(f"after order deatis are fetched resp::{order_details}")
        if not isinstance(order_details, dict):
            order_details = {"data": {}, "raw": order_details}

        order_data = order_details.get("data")
        if isinstance(order_data, list):
            order_data = order_data[0] if order_data and isinstance(order_data[0], dict) else {}
        elif not isinstance(order_data, dict):
            order_data = {}

        if order_data:
            order_status = str(order_data.get('status', '') or '').lower()
            order_id = order_data.get('order_id', '') or order_id
        else:
            print("Error: 'data' key missing in API response")
            order_status = "Failed"
            rejection_message="error while fetching order due to network issue"
            status="success"
            res_data=order_details
            if transaction_type=="BUY":
                Entry_type="LE"
                Entry_price=LivePrice
                EntryQty=order_params['quantity']
            elif transaction_type=="SELL":
                Exit_type="LX"
                Exit_price=LivePrice
                ExitQty=order_params['quantity']    
            logger.exception(f"Error while fetching order details for Order ID {order_id}:")
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
            Segment,Index_Symbol ,order_params , broker="Upstox", history_id=history_id)
            return {
                "data": {
                    "status": "error",
                    "message": "Error while fetching order details.but order is placed successfully.",
                    # "error_details": str(e),
                }
            }

        print(f"Order Status: {order_status}, Order ID: {order_id}")

        res_data=order_details
        logger.info(f"order_status:::{order_status}")
        if order_status in {"complete", "completed", "success"}:
            transaction_type=order_data.get('transaction_type', '')
            if transaction_type == "BUY":
                trade_order_status="OPEN"
                Entry_type="LE"
                Entry_price=order_data.get('average_price', 0.0)
                EntryQty=order_data.get('quantity', 0)
            elif transaction_type == "SELL": 
                trade_order_status="CLOSE"
                Exit_type="LX"
                Exit_price=order_data.get('average_price', 0.0) 
                ExitQty= order_data.get('quantity', 0)#disclosedquantity
            logger.info(f"Order Placed Successfully, Order ID:{order_id}")
            message = order_data.get('status_message', 'completed successfully ')
            res_data=order_details
            
            status=order_data.get('status', 'completed')
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  
                                     strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
                                     webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="upstox", history_id=history_id)
            response={"data": {"status": "completed","message": "Order placed and details saved successfully."}}
            return response
        elif order_status == "rejected":
            rejection_message= order_data.get('status_message', 'Unknown rejection reason')
            status=order_data.get('status', 'rejected')
            transaction_type=order_data.get('transaction_type', '')
            print("transaction_type.........",transaction_type)
            if transaction_type == "BUY":
                Entry_type="LE"
                Entry_price=order_data.get('average_price', 0.0)
                print("Entry_price>>>",Entry_price)
                EntryQty=order_data.get('quantity', 0)
            elif transaction_type == "SELL": 
                Exit_type="LX"
                Exit_price=order_data.get('average_price', 0.0) 
                ExitQty= order_data.get('quantity', 0)#disclosedquantity

            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
            Segment,Index_Symbol ,order_params , broker="Upstox", history_id=history_id)
            logger.info(f"Order Rejected reason!!!::{rejection_message} Order ID: {order_id}")
            response = {"data": {"status": status,"message": "Order is rejected "}}
            return response
        elif order_status == "open":
            logger.info(f"Upstox order is active and open in the market. for order ID: {order_id}")
            rejection_message= order_data.get('status_message', 'Unknown Open reason')
            status=order_data.get('status', 'open')
            transaction_type=order_data.get('transaction_type', '')
            if transaction_type == "BUY":
                Entry_type="LE"
                Entry_price=order_data.get('average_price', 0.0)
                print("Entry_price>>>",Entry_price)
                EntryQty=order_data.get('quantity', 0)
            elif transaction_type == "SELL": 
                Exit_type="LX"
                Exit_price=order_data.get('average_price', 0.0) 
                ExitQty= order_data.get('quantity', 0)#disclosedquantity
            status="complete"
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
            Segment,Index_Symbol ,order_params , broker="Upstox", history_id=history_id)
            logger.info(f"Order  active and open in the market reason!!!::{rejection_message} Order ID: {order_id}")
            response = {"data": {"status": status,"message": "Order is Open "}}
            return response
        elif order_status == "put order req received":
            logger.info(f"Upstox order is active and open in the market. for order ID: {order_id}")
            rejection_message= order_data.get('status_message', 'Unknown Open reason')
            status=order_data.get('status', 'put order req received')
            transaction_type=order_data.get('transaction_type', '')
            if transaction_type == "BUY":
                Entry_type="LE"
                Entry_price=order_data.get('average_price', 0.0)
                print("Entry_price>>>",Entry_price)
                EntryQty=order_data.get('quantity', 0)
            elif transaction_type == "SELL": 
                Exit_type="LX"
                Exit_price=order_data.get('average_price', 0.0) 
                ExitQty= order_data.get('quantity', 0)#disclosedquantity

            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
            Segment,Index_Symbol ,order_params , broker="Upstox", history_id=history_id)
            logger.info(f"Order  active and open in the market reason!!!::{rejection_message} Order ID: {order_id}")
            response = {"data": {"status": status,"message": "Order is Open "}}
            return response
        else:
            
            status=order_data.get('status', 'Failed')
            rejection_message= order_data.get('status_message', 'Unknown rejection reason')
            logger.warning(f"Failed to fetch order details for Order ID {order_id} with status {status} broker is :upstox")
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
            Segment,Index_Symbol ,order_params , broker="Upstox", history_id=history_id)
            return {"data": {"status": "Failed","message": "Order placed but details could not be fetched."}}
                           
    except Exception as e:
        rejection_message="error while fetching order"
        status="Failed"
        res_data=str(e)
        print("trade_symbolfff>>>",trade_symbol)
        logger.exception(f"Error while fetching order details for Order ID {order_id}: {str(e)}")
        save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
        strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
        Segment,Index_Symbol ,order_params , broker="Upstox", history_id=history_id)
        return {
            "data": {
                "status": "error",
                "message": "Error while fetching order details.",
                "error_details": str(e),
            }
        }

def _normalize_upstox_symbol(value):
    normalized = str(value or "").replace(" ", "").replace("-", "").upper()
    return re.sub(r"(\d+)\.0(?=(CE|PE|FUT|CALL|PUT|[A-Z]))", r"\1", normalized)


def fetch_instrument_details(symbol_name, exchange="NSE", user = None):
    try:
        logger.info(f"{user} : instrument details fetching for the upstox api calling !!")
        normalized_symbol_name = _normalize_upstox_symbol(symbol_name)
        instruments_data = load_upstox_instruments(exchange)
        for instrument in instruments_data:
            instrument_symbol = _normalize_upstox_symbol(instrument.get("trading_symbol", ""))
            if instrument_symbol == normalized_symbol_name:
                logger.info(f"{user} : instrument_key is get it ?????????????========>>>>>>>")
                return {
                    "instrument_key": instrument.get("instrument_key"),
                    "trading_symbol": instrument.get("trading_symbol"),
                }

        logger.info(f"{user} : No instruments found for symbol {symbol_name} on exchange {exchange}.")
        return {"error": f"No instruments found for symbol {symbol_name} on exchange {exchange}."}
    except Exception as e:
        logger.info(f"{user} : Exception occurred: {str(e)}")
        return {"error": f"Exception occurred: {str(e)}"}

def get_order_details(order_id, access_token, proxy_config=None):
    try:
        if not order_id:
            return {"error": "Invalid order ID"}

        url = f"https://api.upstox.com/v2/order/details?order_id={order_id}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        print(f"Making API request to: {url}")
        response = requests.get(url, headers=headers, proxies=proxy_config)

        logger.info(f"API Response Status Code: {response.status_code}")

        try:
            response_dict = response.json()  # Corrected JSON parsing
        except json.JSONDecodeError:
            print("Error: Failed to parse JSON response")
            return {
                "error": f"Failed to parse response. Status code: {response.status_code}",
                "details": response.text
            }

        # print("Full API Response:", json.dumps(response_dict, indent=4))  # Pretty-print JSON

        return response_dict

    except requests.RequestException as e:
        print(f"Network error: {e}")
        return {"error": "Network issue occurred", "details": str(e)}

    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"error": "Unexpected error occurred", "details": str(e)}

def get_order_details2222(order_id, access_token):
    return {"error": "Direct Upstox order details lookup is disabled. Use proxy-bound get_order_details()."}
