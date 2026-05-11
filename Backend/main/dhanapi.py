from datetime import datetime
import os
from dhanhq import dhanhq 
import logging
from django.conf import settings
import pandas as pd

from main.broker_instrument_cache import ensure_dhan_instruments_file
from main.models import CompanySmtpDetails
from main.tasks import send_trade_email_async
from main.broker_order_utils import normalize_order_type, resolve_limit_price
from main.trade_history_service import save_trade_order_history
logger = logging.getLogger('main')

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
        
def get_trading_symbol_security_id(symbol, segment, Exch,expiry_date, user=None):
    logger.info(f"{user}: the get_trading_symbol_security_id is calling now !")
    try:
        csv_file_path = ensure_dhan_instruments_file()
        df = pd.read_csv(csv_file_path, low_memory=False)
        normalized_symbol = str(symbol or "").strip().replace(" ", "").replace("-", "").upper()
        
        df['SEM_TRADING_SYMBOL'] = df['SEM_TRADING_SYMBOL'].astype(str).str.strip().str.replace(r"[^\w]", "", regex=True).str.upper()
        df['SEM_EXPIRY_DATE'] = pd.to_datetime(df['SEM_EXPIRY_DATE'], errors="coerce").dt.strftime('%Y-%m-%d')
        df = df[df['SEM_EXPIRY_DATE'].notna()]

        filtered_df = df[
            (df['SEM_TRADING_SYMBOL'] == normalized_symbol) & 
            (df['SEM_EXPIRY_DATE'] == expiry_date)
        ]
        
        if not filtered_df.empty:
            SECURITY_ID = filtered_df.iloc[0]['SEM_SMST_SECURITY_ID']
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
        except Exception as e:
            logger.error(f"{user}: Error validating API key or access token: {str(e)}")
            status = "Failed"
            message = f"{user}: API key and access token are Not valid for. {user}"
            res_data = f"{str(e)}"
            response={"data": {"status": status,"message":message}}
            logger.info(f'{user} : This is exception error in Dhan api {response}')
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,  
                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
            return response

        trading_symbol = get_trading_symbol_security_id(trade_symbol, dhan,Exchange,expiry_date, user)
        if not trading_symbol:
            logger.error(f"{user} : trading_symbol details not found for {trade_symbol}")
            message = "Instrument details not found"
            res_data = "Trading symbol not found."
            response={"data": {"status": status,"message":message}}
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,  
                    strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                    webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
            return response

        logger.info(f"{user} : webhooks Fetched dhan trading_symbol: {trading_symbol}")
        security_id = trading_symbol.get('SECURITY_ID', 0) 
        quantity = int(quantity) 
        if Exchange=="NFO":
            Exchange=dhan.NSE_FNO
        elif Exchange=="NSE":
            Exchange= dhan.NSE
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
            if hasattr(dhan, "get_ltp_data"):
                ltp_response = dhan.get_ltp_data({Exchange: [int(security_id)]})
                exchange_quotes = (ltp_response or {}).get("data", {}).get(Exchange, {})
                quote = exchange_quotes.get(str(int(security_id))) or exchange_quotes.get(int(security_id)) or {}
                ltp = quote.get("last_price") or quote.get("ltp")
        except Exception as e:
            logger.warning(f"{user} : Dhan LTP fetch failed for security_id {security_id}: {str(e)}")

        if requested_order_type == "LIMIT":
            reference_price = ltp or LivePrice or Entry_price or Exit_price
            if ltp is None and reference_price:
                logger.info(
                    f"{user} : Dhan LTP unavailable for security_id {security_id}; using fallback reference price {reference_price}."
                )
            price = resolve_limit_price(price, reference_price, transaction_type)
            if not price:
                message = "Unable to calculate Dhan limit price because no live, signal, or reference price is available."
                response = {"data": {"status": "Failed", "message": message}}
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, "Failed", None, message,
                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response
            order_params["reference_price"] = reference_price
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
            # Validate quantity against lot size using security_id
            try:
                # Load lot size data from CSV
                logger.info(f"{user} : Load lot size data from CSV")
                csv_path = ensure_dhan_instruments_file()
                lot_data = pd.read_csv(csv_path, dtype={'SEM_SMST_SECURITY_ID': str})
                
                # Convert security_id to string for comparison
                security_id_str = str(int(security_id)) if security_id else None
                
                if security_id_str:
                    # Find the instrument in the CSV by security_id
                    instrument_data = lot_data[lot_data['SEM_SMST_SECURITY_ID'].astype(str) == security_id_str]
                    logger.info(f"{user} : instrument_data")
                    if not instrument_data.empty:
                        lot_size = float(instrument_data.iloc[0]['SEM_LOT_UNITS'])
                        if quantity % lot_size != 0:
                            message = f"{user} : Invalid quantity {quantity}. Must be multiple of lot size {lot_size}"
                            logger.error(message)
                            response = {"data": {"status": "Failed", "message": message}}
                            save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, 
                                                user, trade_symbol, order_id, "Failed", None, message,
                                                strategy, Entry_type, Exit_type, Entry_price, Exit_price, 
                                                EntryQty, ExitQty, webhook_signal, Exchange, Segment, 
                                                Index_Symbol, order_params, broker="dhan", history_id=history_id)
                            return response
                    else:
                        logger.warning(f"{user} : No lot size data found for security_id {security_id_str} in CSV")
                else:
                    logger.warning(f"{user} : No security_id available for lot size validation")
            except Exception as e:
                logger.warning(f"{user} : Could not validate lot size: {str(e)}")
            order_response = dhan.place_order(**order_params)
            logger.info(f"{user} : order_response {order_response}")
            # Fetch order ID and validate response
            if order_response.get('status') == 'failure':
                message=order_response.get('remarks', {}).get('error_message', "Unknown error occurred.")
                res_data = order_response
                status='Failed'
                response={"data": {"status": status,"message":message}}
                logger.info(f"{user} : order_response status is failure ??")
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
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
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response

            # Ensure that get_order_details is defined or handled properly
            logger.info(f"{user} : order id {order_id}")
            order_history_response = fetch_order_details(order_id, dhan, user)
            logger.info(f"{user} : Order history response: {order_history_response}")

            # Assuming order_history_response['data'] is a list, we need to access the first element
            res_data = order_history_response['data'][0] if isinstance(order_history_response['data'], list) else order_history_response['data']
            # TRANSIT PENDING REJECTED CANCELLED TRADED EXPIRED
            status = res_data.get('orderStatus', 'UNKNOWN').lower()
            logger.info(f"{user} : status dhan api res _data {status}")
            
            if not status or status==None:
                status = "Failed"
                order_id=0
                message =  'None response from api '
                response = {"data": {"status": status,"message":message}}
                logger.info(f"Order response if None for user {user}. Order ID: {order_id}")

                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response
            
            elif status.lower() == 'complete' or status.lower()=="traded" or status.upper()=="TRADED":
                message = res_data.get('omsErrorDescription', "Order complete")
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
                message = res_data.get('omsErrorDescription', 'not any reason get').lower()
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
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
                return response
            elif status.lower() == "pending":
                message = res_data.get('omsErrorDescription', 'not any reason get').lower()
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
                message = res_data.get('omsErrorDescription', 'not any reason get').lower()
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
                message = res_data.get('omsErrorDescription', 'not any reason get').lower()
                response = {"data": {"status": status,"message":message}}
                if status:
                    status="Failed"
                response= {"data": {"status": "Failed","message": "Order placed but details could not be fetched."}}
                logger.info(f"Order is TRANSIT for user {user}. Order ID: {order_id}")

                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
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
            
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trading_symbol, order_id, "Failed", None, str(e),
                                strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal, Exchange,
                                    Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
            return response

    except Exception as e:
        logger.error(f"{user} : Exception in dhan order placement: {str(e)}")
        error_message = f"Failed to place order: {str(e)}"
        logger.error(error_message)
        order_id = 0
        response={"data": {"status": "error","message": str(e)}}
        save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trading_symbol, order_id, "Failed", None, str(e),
                                    strategy, Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal, Exchange,
                                    Segment, Index_Symbol, order_params, broker="dhan", history_id=history_id)
        return response
