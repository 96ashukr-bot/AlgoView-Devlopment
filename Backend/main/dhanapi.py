from datetime import datetime
import os
from dhanhq import dhanhq 
import logging
from django.conf import settings
import pandas as pd

from main.Alice_Blue_Api import save_trade_order_history
from main.models import CompanySmtpDetails
from main.tasks import send_trade_email_async
logger = logging.getLogger('main')
default_from_email="exampl@gmail.com"
# smtp_details=CompanySmtpDetails.objects.first()
# default_from_email=smtp_details.default_from_email if smtp_details else None
def place_dhan_orders(access_token, client_id, trade_symbol, transaction_type, symbol, quantity,
    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, 
    EntryQty, ExitQty, webhook_signal, Exchange, Segment,Index_Symbol, triggerPrice, trade_order_status):
    print("dhan api  Exchange is::",Exchange," product typweeee",product_type)
    try:
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
            print("API key and access token are valid.")
        except Exception as e:
            logger.error(f"Error validating API key or access token: {str(e)}")
            status = "Failed"
            message = f"API key and access token are Not valid for. {user}"
            res_data = f"{str(e)}"
            response={"data": {"status": status,"message":message}}
            save_trade_order_history(trade_order_status, user, trade_symbol, order_id, status, res_data, message,  
                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
            return response

        trading_symbol = get_trading_symbol_security_id(trade_symbol, dhan,Exchange)
        if not trading_symbol:
            logger.error(f"trading_symbol details not found for {trade_symbol}")
            message = "Instrument details not found"
            res_data = "Trading symbol not found."
            response={"data": {"status": status,"message":message}}
            save_trade_order_history(trade_order_status, user, trade_symbol, order_id, status, res_data, message,  
                    strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                    webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
            return response

        logger.info(f"Fetched dhan trading_symbol: {trading_symbol}")
        security_id = trading_symbol.get('SECURITY_ID', 0) 
        quantity = int(quantity) 
        if Exchange=="NFO":
            Exchange="NSE_FNO"
        # Updated order_params with type casting
        order_params = {
            "transaction_type": transaction_type,
            "exchange_segment": Exchange,
            "product_type": product_type,
            "order_type": ordertype,#ordertype,
            "validity": 'DAY',
            "security_id": int(security_id),  # Convert to Python int
            "quantity": int(quantity) if quantity else 0,       # Convert to Python int
            "price": float(price) if ordertype.upper() == "LIMIT" else 0,
            "trigger_price": float(triggerPrice) if ordertype.upper() == "SL" else 0,
            # "after_market_order":True,
            # "amo_time":'OPEN',
        }
    
        print("order_params>>>>>>",order_params)
        try:
            order_response = dhan.place_order(**order_params)
            print("order_response",order_response)
            # Fetch order ID and validate response
            if order_response.get('status') == 'failure':
                message=order_response.get('remarks', {}).get('error_message', "Unknown error occurred.")
                res_data = order_response
                status='Failed'
                response={"data": {"status": status,"message":message}}
                save_trade_order_history(trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
                return response
            order_id = order_response.get('data', {}).get('orderId')
            if not order_id:
                logger.error("Order ID is not returned")
                status = "Failed"
                message = order_response.get('error_message',"")
                res_data = order_response.get(order_response,"No order ID returned")
                response={"data": {"status": status,"message":message}}
                save_trade_order_history(trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
                return response

            # Ensure that get_order_details is defined or handled properly
  
            order_history_response = fetch_order_details(order_id, dhan)
            logger.info(f"Order history response: {order_history_response}")

            # Assuming order_history_response['data'] is a list, we need to access the first element
            res_data = order_history_response['data'][0] if isinstance(order_history_response['data'], list) else order_history_response['data']
            
            status = res_data.get('orderStatus', 'UNKNOWN').lower()
            
            if status == 'complete':
                message = res_data.get('omsErrorDescription', "Order complete")
                logger.info(f"Order placed successfully. Order ID: {order_id}")
                transaction_type = res_data.get('transactionType', '')
                
                Entry_type = Exit_type = ""
                Entry_price = Exit_price = 0.0
                EntryQty = ExitQty = 0
                
                if transaction_type == "BUY":
                    Entry_type = "LE"
                    Entry_price = res_data.get('averageTradedPrice', 0.0)
                    EntryQty = res_data.get('quantity', 0)
                elif transaction_type == "SELL":
                    Exit_type = "LX"
                    Exit_price = res_data.get('averageTradedPrice', 0.0)
                    ExitQty = res_data.get('quantity', 0)

                # Ensure Index_Symbol is provided
                Index_Symbol = res_data.get('tradingSymbol', 'UNKNOWN')

                response = {"data": {"status": "completed", "message": "Order placed and details saved successfully."}}
                save_trade_order_history(trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
                return response
            elif status == "rejected":
                message = res_data.get('omsErrorDescription', 'not any reason get').lower()
                send_trade_email_async.delay(user.email, default_from_email, user.firstName, status, message)
                response = {"data": {"status": status}}
                logger.info(f"Order is rejected for user {user}. Order ID: {order_id}")
                
                # Ensure Index_Symbol is provided
                Index_Symbol = res_data.get('tradingSymbol', 'UNKNOWN')
                
                save_trade_order_history(trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="5paisa")
                return response
            elif status == "pending":
                message = res_data.get('omsErrorDescription', 'not any reason get').lower()
                send_trade_email_async.delay(user.email, default_from_email, user.firstName, status, message)
                response = {"data": {"status": status}}
                logger.info(f"Order is pending for user {user}. Order ID: {order_id}")
                
                # Ensure Index_Symbol is provided
                Index_Symbol = res_data.get('tradingSymbol', 'UNKNOWN')
                
                save_trade_order_history(trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="5paisa")
                return response
        except Exception as e:
            error_message = f"Failed to place order: {str(e)}"
            logger.error(error_message)
            order_id = 0
            response = {"data": {"status": status, "message": str(e)}}
            print("error in dhan api :::::",{str(e)})
            # Ensure Index_Symbol is provided
            Index_Symbol = res_data.get('tradingSymbol', 'UNKNOWN')
            
            save_trade_order_history(trade_order_status, user, trading_symbol, order_id, "Failed", None, str(e),
                                strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal, Exchange,
                                    Segment, Index_Symbol, order_params, broker="dhan")
            return response

    except Exception as e:
        logger.error(f"Exception in dhan order placement: {str(e)}")
        error_message = f"Failed to place order: {str(e)}"
        logger.error(error_message)
        order_id = 0
        response={"data": {"status": status,"message": str(e)}}
        save_trade_order_history(trade_order_status, user, trading_symbol, order_id, "Failed", None, str(e),
                                    strategy, Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal, Exchange,
                                    Segment, Index_Symbol, order_params, broker="dhan")
        return response
    
    
def fetch_order_details(order_id,dhan):
    try:
        response = dhan.get_order_by_id(order_id)
        if response['status'] == 'success':
            return response
            # print(f"Order details fetched successfully: {response}")
        else:
            print(f"Failed to fetch order details: {response['remarks']['error_message']}")
    except Exception as e:
        print(f"Error while fetching order details: {str(e)}")
        
def get_trading_symbol_security_id(symbol, segment, Exch):
    try:
        csv_file_path = "/home/digiprima/Downloads/api-scrip-master.csv"
        df = pd.read_csv(csv_file_path, low_memory=False)
        
        df['SEM_TRADING_SYMBOL'] = df['SEM_TRADING_SYMBOL'].str.replace("-", "").str.strip()
    
        filtered_df = df[df['SEM_TRADING_SYMBOL'].str.upper() == symbol.upper()]
        
        if not filtered_df.empty:
            # Return the first matching record's ScripCode
            SECURITY_ID = filtered_df.iloc[0]['SEM_SMST_SECURITY_ID']
            return {"status": "success", "SECURITY_ID": SECURITY_ID}
        else:
            status={"status": "error", "message": "No records found matching the given symbol and exchange."}
            logger.info(f"status")
            return  None
    
    except Exception as e:
        return {"status": "error", "message": "An error occurred.", "details": str(e)}


