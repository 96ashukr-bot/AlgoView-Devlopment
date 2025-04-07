from django.http import JsonResponse
import requests

from main.Alice_Blue_Api import save_trade_order_history
from main.models import ClientBrokerdetails, CompanySmtpDetails
import logging
logger = logging.getLogger('main')

def place_fyers_orders(LivePrice,group_service,access_token, Api_key, trade_symbol, transaction_type, symbol, quantity,
    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, 
    EntryQty, ExitQty, webhook_signal, Exchange, Segment,Index_Symbol, triggerPrice, trade_order_status):
    print("index symbolllllll",Index_Symbol)
    try:
        EntryQty=quantity
        order_id = 0
        status = "Failed"
        res_data = "Unknown response"
        """1
        2 => Market Order
        3 => Stop Order (SL-M)
        4 => Stoplimit Order (SL-L)
        """
        # Prepare order parameters
        order_url = "https://api-t1.fyers.in/api/v3/orders/sync"
        if ordertype.lower()=="limit":
            order=1	
        elif ordertype.lower()=="market":
            order=2
        if transaction_type.lower()=="buy":
            side=1
        elif transaction_type.lower()=="sell":
            side=-1

        order_payload = {
            "symbol": trade_symbol,
            "qty": quantity,
            "type": order,        
            "side": side,               # 1 = Buy, 2 = Sell
            "productType": product_type,  # Use INTRADAY for options/F&O
            "limitPrice": price if ordertype.upper() == "LIMIT" else 0,
            # "stopPrice": 0,
            "validity": "DAY",
            # "disclosedQty": 0,
            # "offlineOrder": False,
            # "orderTag": "0"
        }
        headers = {
            "Authorization": f"{Api_key}:{access_token}",
            "Content-Type": "application/json"
        }    

        trading_symbol = get_trading_symbol(Exchange, trade_symbol, access_token)

        if not trading_symbol:
            logger.error(f"trading_symbol details not found for {trade_symbol}")
            message = "Instrument details not found"
            res_data = "Trading symbol not found."
            response={"data": {"status": status,"message":message}}
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, symbol, order_id, status, res_data, message,  
                    strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                    webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="fyers")
            return response

        logger.info(f"Fetched fyers trading_symbol: {trading_symbol}")

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
            
            response = requests.post(order_url, headers=headers, json=order_payload)
            order_response = response.json()

            if order_response.get("s") == "ok":
                print(" Order submitted successfully.")
                print(" Order ID:", order_response.get("id"))
                order_id=order_response.get("id")
            else:
                print(" Order failed:", order_response.get("message", "Unknown error"))
                print("Details:", order_response)
                

            if not order_id:
                logger.error("Order ID is not returned")
                status = "Failed"
                message = "No order ID returned"
                res_data = "No order ID returned"
                response={"data": {"status": status,"message":message}}
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, symbol, order_id, status, res_data, message,
                                         strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                         webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="fyers")
                return response

            # Ensure that get_order_details is defined or handled properly
            order_history_response = get_order_details(order_id, access_token)
            
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
                                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="fyers")
                    return response

            # order_history_response = order_history_response[-1]  # Assuming the last item is the most recent
            # status = order_history_response.get("status", "").lower()
            # res_data=order_history_response
            # Inside your place_zerodha_orders function, modify the status handling part:

            elif isinstance(order_history_response, list) and order_history_response:
                
                status = order_history_response.get("status", "").upper()  # Convert to uppercase for consistent comparison
                res_data = order_history_response
                print("status>>>>>>>>>>>>>>>", status)
                print("Entry_price, Exit_price, >>",Entry_price, Exit_price, )
               
                print("::::::::::::::::")
                # Handle terminal statuses
                if status ==  2:  #status == 'COMPLETE' or status =='complete' OR :
                    message = order_history_response.get('status_message', "Order completed successfully")
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
                    
                elif status == 5:# status == 'REJECTED' or status=='rejected':
                    status='rejected'
                    message = order_history_response.get('status_message', "Order rejected")
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
                    
                elif status ==1:#status == 'CANCELLED' or status =='cancelled':
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
                    message = order_history_response.get('status_message', "Order cancelled")
                    logger.warning(f"Order cancelled. Reason: {message}")
                    response = {"data": {"status": "cancelled", "message": message}}
        
                elif status == 6:#status=='PENDING' or status =="pending":
                    status ="pending"
                    # Handle pending statuses - you might want to poll again later
                    message = f"Order is in pending state: {status}"
                    logger.info(message)
                    response = {"data": {"status": "pending", "message": message}}
                if res_data is not None:
                    
                    # You might want to save this as a pending status or wait for terminal status
                    save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, 
                                        user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, 
                                        EntryQty, ExitQty, webhook_signal, Exchange, Segment, 
                                        Index_Symbol, order_params, broker="fyers")
                    return response
        

                else:
                    message = order_history_response.get('status_message', "Success")
                    response = {"data": {"status": status, "message": message}}
                    save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="fyers")
                    return response
            else:
                logger.error("Unknown order response format")
                status = "Failed"
                message = "Unknown response format from get_order_details"
                response = {"data": {"status": status, "message": message}}
                save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol, order_id, status, None, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="fyers")
                return response
        except Exception as e:
            error_message = f"Failed to place order: {str(e)}"
            logger.error(error_message)
            order_id = 0
            response={"data": {"status": status,"message": str(e)}}
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, "Failed", None, str(e),
                                     strategy, Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal, Exchange,
                                     Segment, Index_Symbol, order_params, broker="fyers")
            return response

    except Exception as e:
        logger.error(f"Exception in fyers order placement: {str(e)}")
        error_message = f"Failed to place order: {str(e)}"
        logger.error(error_message)
        order_id = 0
        response={"data": {"status": status,"message": str(e)}}
        save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, "Failed", None, str(e),
                        strategy, Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal, Exchange,
                                    Segment, Index_Symbol, order_params, broker="fyers")
        return response

    
def get_trading_symbol(exchange, symbol, kite):
    try:
        # Fetch the list of instruments for the specified exchange
        instruments = kite.instruments(exchange)
        # csv_file = "/home/digiprima/Desktop/jyoti/Django/AlgoView-Devlopment/Backend/zerodhaNFO.csv"
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

