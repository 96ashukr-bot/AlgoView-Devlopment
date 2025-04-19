from django.http import JsonResponse
import requests
import os
from main.Alice_Blue_Api import save_trade_order_history
from main.models import ClientBrokerdetails, CompanySmtpDetails
import logging
logger = logging.getLogger('main')
import csv 
from fyers_apiv3 import fyersModel

def place_fyers_orders(LivePrice,group_service,access_token, Api_key, trade_symbol, transaction_type, symbol, quantity,
    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, 
    EntryQty, ExitQty, webhook_signal, Exchange, Segment,Index_Symbol, triggerPrice, trade_order_status):
    print("index symbolllllll",Index_Symbol)
    try:
        response={"data":{"status": "error", "message": "not return any response"}}
        EntryQty=quantity
        order_id = 0
        status = "Failed"
        res_data = "Unknown response"
        """1
        2 => Market Order
        3 => Stop Order (SL-M)
        4 => Stoplimit Order (SL-L
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
        if product_type.upper()=="MIS":
                product_type="INTRADAY"
        ordertype=ordertype.upper()
        order_params = {
            "symbol": trade_symbol,
            "qty": quantity,
            "type": ordertype ,        
            "side": transaction_type,               # 1 = Buy, 2 = Sell
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

        trading_symbol = get_instruments_symbol_from_csv(trade_symbol)

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
        order_params = {
            "symbol": trading_symbol,
            "qty": quantity,
            "type": 2 if ordertype.upper() == "MARKET" else 1,  # ✅ Fix is here
            "side": 1 if transaction_type.upper() == "BUY" else -1,
            "productType": product_type.upper(),  # e.g., "INTRADAY"
            "validity": "DAY",
            "orderTag": "tag1"
        }
        print("ordertype>>>",ordertype)
        if ordertype == "LIMIT":
            order_params["limitPrice"] = float(price)
        logger.info(f"paylod of order>>>>{order_params}")
        try:
            
            response = requests.post(order_url, headers=headers, json=order_params)
           
            logger.info(f"order_response of fyers::::::::::::{response}")
            order_response = response.json()
            if response.status_code == 401:
                logger.error("Unauthorized - Access token might have expired.")
                status = "Unauthorized"
                message = f" Authentication failed. Please refresh your access token."
                res_data = f"message"
                response={"data": {"status": status,"message":message}}
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, symbol, order_id, status, res_data, message,  
                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="fyers")
                
                return response
            if response.status_code == 400 :#or order_response.get("s") == "error":
                logger.error("error  400 status code get ")
                status = "Failed"
                message = order_response.get("message", "Unknown error")
                res_data = f"message"
                response={"data": {"status": status,"message":message}}
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, symbol, order_id, status, res_data, message,  
                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="fyers")
                
                return response   
            print("777777777777777777777777777777")
            if response.status_code == 200 and order_response.get("s") == "error":
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
            order_history_response = get_order_details(order_id,Api_key, access_token)
            
            logger.info(f"get_order_details ????????????: {order_history_response}")

            if isinstance(order_history_response, dict):
                if order_history_response.get("s") == "Failed" or order_history_response.get("s") =="error":
                    logger.error(f"Order details not found")
                    status = "Failed"
                    message = "Order details not found"
                    res_data = order_history_response.get("error")
                    response = {"data": {"status": status, "message": message}}
                    save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, user, symbol, order_id, status, res_data, message,
                                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="fyers")
                    return {"data": {"status": "Failed", "message": "Failed to retrieve order details."}}
            

                status = order_history_response.get("status")  # Fyers uses integers
                res_data = order_history_response
                logger.info(f"status code of fyers:::{status}")
                 # Handle terminal statuses
                if transaction_type.lower()=="buy":
                    transactions=1
                elif transaction_type.lower()=="sell":
                    transactions=-1
                if status == 2:#status  == 'Traded' or status =='Filled' :
                    message = order_history_response.get('message', "Order completed successfully")
                    logger.info(f"Order completed successfully. Order ID: {order_id}")
                    status='complete'
                    # Update transaction details
                    trasaction_type = res_data.get('side','')
                    if trasaction_type == 1:
                        trade_order_status="OPEN"
                        Entry_type = "LE"
                        Entry_price = res_data.get('tradedPrice', 0.0)
                        EntryQty = res_data.get('qty', 0)
                    elif trasaction_type == -1: 
                        trade_order_status="CLOSE"
                        Exit_type = "LX"
                        Exit_price = res_data.get('tradedPrice', 0.0)  
                        ExitQty = res_data.get('qty', 0)
                        
                    response = {"data": {"status": "completed", "message": message}}
                    
                elif status == 4:# status == 'Transit' or status =='Transit':
                    status='Transit'
                    trasaction_type = res_data.get('side','')
                    if trasaction_type == 1:
                        Entry_type = "LE"
                        Entry_price = res_data.get('tradedPrice', 0.0)
                        EntryQty = res_data.get('qty', 0)
                    elif trasaction_type == -1: 
                        Exit_type = "LX"
                        Exit_price = res_data.get('tradedPrice', 0.0)  
                        ExitQty = res_data.get('qty', 0)
                    message = order_history_response.get('message', "Order cancelled")
                    logger.warning(f"Order Transit. Reason: {message}")
                    response = {"data": {"status": "Transit", "message": message}}
                    
                elif status == 5: #status == 'Rejected' or status=='rejected':
                    status='rejected'
                    message = order_history_response.get('message', "Order rejected")
                    logger.error(f"Order rejected. Reason: {message}")
                    trasaction_type = res_data.get('side','')
                    if trasaction_type == 1:
                        Entry_type = "LE"
                        Entry_price = res_data.get('tradedPrice', 0.0)
                        EntryQty = res_data.get('qty', 0)
                    elif trasaction_type == -1: 
                        Exit_type = "LX"
                        Exit_price = res_data.get('tradedPrice', 0.0)  
                        ExitQty = res_data.get('qty', 0)
                    response = {"data": {"status": "rejected", "message": message}}
                    
                elif status == 6:# status=='Pending' or status =="pending":
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
                    logger.info("order status is not found")
                    message = order_history_response.get('message', "Success")
                    response = {"data": {"status": status, "message": message}}
                    res_data=order_history_response
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

    

def get_instruments_symbol_from_csv(compact_symbol_details):
    try:
        csv_path="main/fyers_instrument_symbol.csv"
        if not os.path.exists(csv_path):
            print(f" CSV file not found at: {csv_path}")
            return None

        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            print(" CSV file is empty")
            return None

        headers = rows[0]
        data_rows = rows[1:]

        # Get column indexes
        try:
            symbol_details_index = headers.index("Symbol Details")
            symbol_ticker_index = headers.index("Symbol Ticker")
        except ValueError:
            print(" Required columns not found in CSV")
            return None

        # Match the compacted "Symbol Details"
        for row in data_rows:
            raw_symbol_details = row[symbol_details_index]
            normalized_symbol_details = raw_symbol_details.replace(" ", "")
            if normalized_symbol_details.upper() == compact_symbol_details:
                return row[symbol_ticker_index]

        print(f" Symbol Details '{compact_symbol_details}' not found in CSV")
        return None

    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None


def get_order_details(order_id, client_id,access_token):
    try:
        # Initialize the FyersModel instance with your client_id, access_token, and enable async mode
        fyers = fyersModel.FyersModel(client_id=client_id, token=access_token,is_async=False, log_path="")
        order_history = fyers.orderbook()

        if order_history and "orderBook" in order_history:
            # Try to find the specific order by ID
            for order in order_history["orderBook"]:
                if order["id"] == str(order_id):
                    return order  # return the actual order dict
            # If not found
            return {"status": "Failed", "error": f"No order found with ID {order_id}"}
        else:
            return {"status": "Failed", "error": "No order history data received."}
    except Exception as e:
        return {"status": "Failed", "error": f"Failed to fetch order history: {str(e)}"}

