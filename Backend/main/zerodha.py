from django.http import JsonResponse
from kiteconnect import KiteConnect
from main.Alice_Blue_Api import save_trade_order_history
from main.models import ClientBrokerdetails, CompanySmtpDetails
import logging
logger = logging.getLogger('main')

def place_zerodha_orders(LivePrice,group_service,access_token, Api_key, trade_symbol, transaction_type, symbol, quantity,
    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, 
    EntryQty, ExitQty, webhook_signal, Exchange, Segment,Index_Symbol, triggerPrice, trade_order_status):
    print("index symbolllllll",Index_Symbol)
    try:
        EntryQty=quantity
        smtp_details=CompanySmtpDetails.objects.first()
        default_from_email=smtp_details.email_host_user if smtp_details else   "no-reply@example.com"
        order_id = 0
        status = "Failed"
        res_data = "Unknown response"
        # Prepare order parameters
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
            # This part of the code is attempting to authenticate with the Zerodha Kite API using the provided
            # API key and access token. Here's a breakdown of what each step does:
            kite = KiteConnect(api_key=Api_key)
            kite.set_access_token(access_token)
            profile = kite.profile()
            print("API key and access token are valid.")
        except Exception as e:
            logger.error(f"Error validating API key or access token: {str(e)}")
            status = "Unauthorized"
            message = f"API key and access token are Not valid for. {user}"
            res_data = f"{str(e)}"
            response={"data": {"status": status,"message":message}}
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, symbol, order_id, status, res_data, message,  
                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
            
            return response

        trading_symbol = get_trading_symbol(Exchange, trade_symbol, kite)

        if not trading_symbol:
            logger.error(f"trading_symbol details not found for {trade_symbol}")
            message = "Instrument details not found"
            res_data = "Trading symbol not found."
            response={"data": {"status": status,"message":message}}
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, symbol, order_id, status, res_data, message,  
                    strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                    webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
            return response

        logger.info(f"Fetched Zerodha trading_symbol: {trading_symbol}")

        # Prepare order parameters
        order_params = {
            "tradingsymbol": trading_symbol,
            "exchange": Exchange,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "order_type": ordertype,
            "product": product_type,
            "price": price if ordertype.upper() == "LIMIT" else 0,
            "trigger_price": triggerPrice if ordertype.upper() == "SL" else None
        }

        try:
            order_response = kite.place_order(variety=kite.VARIETY_REGULAR, **order_params)
            print("order_response-------------",order_response)
            print("order_params*******************",order_params)
            order_id =order_response#order_response.get('order_id')
            if not order_id:
                logger.error("Order ID is not returned")
                status = "Failed"
                message = "No order ID returned"
                res_data = "No order ID returned"
                response={"data": {"status": status,"message":message}}
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, symbol, order_id, status, res_data, message,
                                         strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                         webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                return response

            # Ensure that get_order_details is defined or handled properly
            order_history_response = get_order_details(order_id, kite)
            
            logger.info(f"Order history response: {order_history_response}")
            if isinstance(order_history_response, dict):
                if order_history_response.get("error") == "Failed":
                    logger.error("Order details not found")
                    status = "Failed"
                    message = "Order details not found"
                    res_data = order_history_response.get("error")
                    response = {"data": {"status": status, "message": message}}
                    save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, symbol, order_id, status, res_data, message,
                                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                    return response

            # latest_status = order_history_response[-1]  # Assuming the last item is the most recent
            # status = latest_status.get("status", "").lower()
            # res_data=latest_status
            # Inside your place_zerodha_orders function, modify the status handling part:

            elif isinstance(order_history_response, list) and order_history_response:
                latest_status = order_history_response[-1]
                status = latest_status.get("status", "").upper()  # Convert to uppercase for consistent comparison
                res_data = latest_status
                print("status>>>>>>>>>>>>>>>", status)
                print("Entry_price, Exit_price, >>",Entry_price, Exit_price, )
                # Define terminal statuses (final states that won't change)
                TERMINAL_STATUSES = ['COMPLETE', 'REJECTED', 'CANCELLED','complete','rejected','cancelled']
                
                # Define pending statuses (temporary states that will eventually change)
                PENDING_STATUSES = [
                    'PUT ORDER REQ RECEIVED',
                    'VALIDATION PENDING',
                    'OPEN PENDING',
                    'MODIFY VALIDATION PENDING',
                    'MODIFY PENDING',
                    'TRIGGER PENDING',
                    'CANCEL PENDING',
                    'AMO REQ RECEIVED'
                ]
                print("status>>>>",status)
                if status in TERMINAL_STATUSES:
                    print("::::::::::::::::")
                    # Handle terminal statuses
                    if status == 'COMPLETE' or status =='complete':
                        message = latest_status.get('status_message', "Order completed successfully")
                        logger.info(f"Order completed successfully. Order ID: {order_id}")
                        status='complete'
                        # Update transaction details
                        trasaction_type = res_data.get('transaction_type','')
                        if trasaction_type == "BUY":
                            trade_order_status="OPEN"
                            Entry_type = "LE"
                            Entry_price = res_data.get('average_price', 0.0)
                            EntryQty = res_data.get('filled_quantity', 0)
                        elif trasaction_type == "SELL": 
                            trade_order_status="CLOSE"
                            Exit_type = "LX"
                            Exit_price = res_data.get('average_price', 0.0)  
                            ExitQty = res_data.get('filled_quantity', 0)
                            
                        response = {"data": {"status": "completed", "message": message}}
                        
                    elif status == 'REJECTED' or status=='rejected':
                        status='rejected'
                        message = latest_status.get('status_message', "Order rejected")
                        logger.error(f"Order rejected. Reason: {message}")
                        trasaction_type = res_data.get('transaction_type','')
                        if trasaction_type == "BUY":
                            Entry_type = "LE"
                            Entry_price = res_data.get('average_price', 0.0)
                            EntryQty = res_data.get('filled_quantity', 0)
                        elif trasaction_type == "SELL": 
                            Exit_type = "LX"
                            Exit_price = res_data.get('average_price', 0.0)  
                            ExitQty = res_data.get('filled_quantity', 0)
                        response = {"data": {"status": "rejected", "message": message}}
                        
                    elif status == 'CANCELLED' or status =='cancelled':
                        status='cancelled'
                        trasaction_type = res_data.get('transaction_type','')
                        if trasaction_type == "BUY":
                            Entry_type = "LE"
                            Entry_price = res_data.get('average_price', 0.0)
                            EntryQty = res_data.get('filled_quantity', 0)
                        elif trasaction_type == "SELL": 
                            Exit_type = "LX"
                            Exit_price = res_data.get('average_price', 0.0)  
                            ExitQty = res_data.get('filled_quantity', 0)
                        message = latest_status.get('status_message', "Order cancelled")
                        logger.warning(f"Order cancelled. Reason: {message}")
                        response = {"data": {"status": "cancelled", "message": message}}
                        
                    # Save trade history for terminal statuses
                    print("order_params>>>>",order_params)
                    if res_data is not None:
                        res_data = make_serializable(res_data)
                    save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, 
                                        user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, 
                                        EntryQty, ExitQty, webhook_signal, Exchange, Segment, 
                                        Index_Symbol, order_params, broker="zerodha")
                    return response
                    
                elif status in PENDING_STATUSES:
                    status='pending'
                    # Handle pending statuses - you might want to poll again later
                    message = f"Order is in pending state: {status}"
                    logger.info(message)
                    response = {"data": {"status": "pending", "message": message}}
                    if res_data is not None:
                        res_data = make_serializable(res_data)
                    # You might want to save this as a pending status or wait for terminal status
                    save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, 
                                        user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, 
                                        EntryQty, ExitQty, webhook_signal, Exchange, Segment, 
                                        Index_Symbol, order_params, broker="zerodha")
                    return response
        

                else:
                    message = latest_status.get('status_message', "Success")
                    response = {"data": {"status": status, "message": message}}
                    save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                    return response
            else:
                logger.error("Unknown order response format")
                status = "Failed"
                message = "Unknown response format from get_order_details"
                response = {"data": {"status": status, "message": message}}
                save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, order_id, status, None, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                return response
        except Exception as e:
            error_message = f"Failed to place order: {str(e)}"
            logger.error(error_message)
            order_id = 0
            response={"data": {"status": status,"message": str(e)}}
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, "Failed", None, str(e),
                                     strategy, Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal, Exchange,
                                     Segment, Index_Symbol, order_params, broker="zerodha")
            return response

    except Exception as e:
        logger.error(f"Exception in Zerodha order placement: {str(e)}")
        error_message = f"Failed to place order: {str(e)}"
        logger.error(error_message)
        order_id = 0
        response={"data": {"status": status,"message": str(e)}}
        save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, "Failed", None, str(e),
                        strategy, Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal, Exchange,
                                    Segment, Index_Symbol, order_params, broker="zerodha")
        return response

    
def get_trading_symbol(exchange, symbol, kite):
    try:
        # Fetch the list of instruments for the specified exchange
        instruments = kite.instruments(exchange)
        for instrument in instruments:
            if instrument['tradingsymbol'] == symbol:
                print("Trading Symbol Found:", instrument['tradingsymbol'])
                return instrument['tradingsymbol']
        
        return None  # Return None if the symbol is not found

    except Exception as e:
        print(f"Error: {str(e)}")
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