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
def place_dhan_orders(expiry_date,LivePrice,group_service,access_token, client_id, trade_symbol, transaction_type, symbol, quantity,
    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, 
    EntryQty, ExitQty, webhook_signal, Exchange, Segment,Index_Symbol, triggerPrice, trade_order_status):
    print("dhan api  Exchange is::",Exchange," product typweeee",product_type)
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
            print("API key and access token are valid.")
        except Exception as e:
            logger.error(f"Error validating API key or access token: {str(e)}")
            status = "Failed"
            message = f"API key and access token are Not valid for. {user}"
            res_data = f"{str(e)}"
            response={"data": {"status": status,"message":message}}
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,  
                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
            return response
        print("trade_symbol, dhan,Exchange>>>>>",trade_symbol, dhan,Exchange)
        trading_symbol = get_trading_symbol_security_id(trade_symbol, dhan,Exchange,expiry_date)
        if not trading_symbol:
            logger.error(f"trading_symbol details not found for {trade_symbol}")
            message = "Instrument details not found"
            res_data = "Trading symbol not found."
            response={"data": {"status": status,"message":message}}
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,  
                    strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                    webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
            return response

        logger.info(f"Fetched dhan trading_symbol: {trading_symbol}")
        security_id = trading_symbol.get('SECURITY_ID', 0) 
        quantity = int(quantity) 
        if Exchange=="NFO":
            Exchange=dhan.NSE_FNO
        elif Exchange=="NSE":
            Exchange= dhan.NSE    
        # Updated order_params with type casting
        # CNC  INTRA MARGIN MTF CO BO
        # print("product_type>>>>",product_type)
        # Validate and map product_type
        if product_type.upper() in ["NRML", "NORMAL"]:
            product_type = dhan.NORMAL
        elif product_type.upper() in ["MIS", "INTRADAY"]:
            product_type = dhan.INTRA
        elif product_type.upper() in ["CNC", "DELIVERY"]:
            product_type = dhan.CNC
        else:
            print("Invalid product type:", product_type)
            return {"status": "error", "message": "Invalid product type"}

        # Validate transaction_type
        if transaction_type.upper() == "BUY":
            transaction_type = dhan.BUY
        elif transaction_type.upper() == "SELL":
            transaction_type = dhan.SELL
        else:
            print("Invalid transaction type:", transaction_type)
            return {"status": "error", "message": "Invalid transaction type"}

        # Validate order_type
        if ordertype.upper() == "MARKET":
            ordertype = dhan.MARKET
        elif ordertype.upper() == "LIMIT":
            ordertype = dhan.LIMIT
        elif ordertype.upper() == "SL":
            ordertype = dhan.SL
        else:
            print("Invalid order type:", ordertype)
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

        logger.info(f"Final order_params dhan order:{order_params}")
        try:
                
            # Validate quantity against lot size using security_id
            try:
                # Load lot size data from CSV
                csv_path = "/home/digiprima/Desktop/jyoti/Django/AlgoView-Devlopment/Backend/main/dhantoken.csv"
                # csv_path="/home/ubuntu/Backend/AlgoView-Devlopment/Backend/main/dhantoken.csv"
                lot_data = pd.read_csv(csv_path, dtype={'SEM_SMST_SECURITY_ID': str})
                
                # Convert security_id to string for comparison
                security_id_str = str(int(security_id)) if security_id else None
                
                if security_id_str:
                    # Find the instrument in the CSV by security_id
                    instrument_data = lot_data[lot_data['SEM_SMST_SECURITY_ID'].astype(str) == security_id_str]
                    print("instrument_data>>>",instrument_data)
                    if not instrument_data.empty:
                        lot_size = float(instrument_data.iloc[0]['SEM_LOT_UNITS'])
                        if quantity % lot_size != 0:
                            message = f"Invalid quantity {quantity}. Must be multiple of lot size {lot_size}"
                            logger.error(message)
                            response = {"data": {"status": "Failed", "message": message}}
                            save_trade_order_history(LivePrice, group_service, transaction_type, trade_order_status, 
                                                user, trade_symbol, order_id, "Failed", None, message,
                                                strategy, Entry_type, Exit_type, Entry_price, Exit_price, 
                                                EntryQty, ExitQty, webhook_signal, Exchange, Segment, 
                                                Index_Symbol, order_params, broker="dhan")
                            return response
                    else:
                        logger.warning(f"No lot size data found for security_id {security_id_str} in CSV")
                else:
                    logger.warning("No security_id available for lot size validation")
            except Exception as e:
                logger.warning(f"Could not validate lot size: {str(e)}")
            order_response = dhan.place_order(**order_params)
            print("order_response",order_response)
            # Fetch order ID and validate response
            if order_response.get('status') == 'failure':
                message=order_response.get('remarks', {}).get('error_message', "Unknown error occurred.")
                res_data = order_response
                status='Failed'
                response={"data": {"status": status,"message":message}}
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
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
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
                return response

            # Ensure that get_order_details is defined or handled properly
            logger.info(f"order id {order_id}")
            order_history_response = fetch_order_details(order_id, dhan)
            logger.info(f"Order history response: {order_history_response}")

            # Assuming order_history_response['data'] is a list, we need to access the first element
            res_data = order_history_response['data'][0] if isinstance(order_history_response['data'], list) else order_history_response['data']
            # TRANSIT PENDING REJECTED CANCELLED TRADED EXPIRED
            status = res_data.get('orderStatus', 'UNKNOWN').lower()
            logger.info(f"status dhan api res _data {status}")
            
            if not status or status==None:
                status = "Failed"
                order_id=0
                message =  'None response from api '
                response = {"data": {"status": status,"message":message}}
                logger.info(f"Order response if None for user {user}. Order ID: {order_id}")
                # Ensure Index_Symbol is provided
                # Index_Symbol = symbol
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
                return response
            
            elif status.lower() == 'complete' or status.lower()=="traded" or status.upper()=="TRADED":
                message = res_data.get('omsErrorDescription', "Order complete")
                logger.info(f"Order placed successfully. Order ID: {order_id}")
                transaction_type = res_data.get('transactionType', '')
                status=status.lower()
                # Entry_type = Exit_type = ""
                # Entry_price = Exit_price = 0.0
                # EntryQty = ExitQty = 0
                
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

                # Ensure Index_Symbol is provided
                # Index_Symbol = res_data.get('tradingSymbol', 'UNKNOWN')


                response = {"data": {"status": "completed", "message": "Order placed and details saved successfully."}}
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
                return response
            elif status.lower() == "rejected":
                message = res_data.get('omsErrorDescription', 'not any reason get').lower()
                transaction_type = res_data.get('transactionType', '')
                
                # Entry_type = Exit_type = ""
                # Entry_price = Exit_price = 0.0
                # EntryQty = ExitQty = 0
                
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
                
                # Ensure Index_Symbol is provided
                # Index_Symbol = res_data.get('tradingSymbol', 'UNKNOWN')
                
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
                return response
            elif status.lower() == "pending":
                message = res_data.get('omsErrorDescription', 'not any reason get').lower()
                transaction_type = res_data.get('transactionType', '')
                
                # Entry_type = Exit_type = ""
                # Entry_price = Exit_price = 0.0
                # EntryQty = ExitQty = 0
                
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
                
                # Ensure Index_Symbol is provided
                #Index_Symbol = res_data.get('tradingSymbol', symbol)
                
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
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
                
                # Ensure Index_Symbol is provided
                #Index_Symbol = res_data.get('tradingSymbol', symbol)
                
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
                return response
            else:
                message = res_data.get('omsErrorDescription', 'not any reason get').lower()
                # send_trade_email_async.delay(user.email, default_from_email, user.firstName, status, message)
                response = {"data": {"status": status,"message":message}}
                if status:
                    status="Failed"
                response= {"data": {"status": "Failed","message": "Order placed but details could not be fetched."}}
                logger.info(f"Order is TRANSIT for user {user}. Order ID: {order_id}")
                
                # Ensure Index_Symbol is provided
               # Index_Symbol = res_data.get('tradingSymbol', symbol)

                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
                return response     
        except Exception as e:
            error_message = f"Failed to place order: {str(e)}"
            logger.error(error_message)
            order_id = 0
            response = {"data": {"status": "Failed", "message": str(e)}}
            print("error in dhan api :::::",{str(e)})
            # Ensure Index_Symbol is provided
            Index_Symbol = symbol
            
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trading_symbol, order_id, "Failed", None, str(e),
                                strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal, Exchange,
                                    Segment, Index_Symbol, order_params, broker="dhan")
            return response

    except Exception as e:
        logger.error(f"Exception in dhan order placement: {str(e)}")
        error_message = f"Failed to place order: {str(e)}"
        logger.error(error_message)
        order_id = 0
        response={"data": {"status": "error","message": str(e)}}
        save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trading_symbol, order_id, "Failed", None, str(e),
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
        
def get_trading_symbol_security_id(symbol, segment, Exch,expiry_date):
    try:
        print("symbollll",symbol)
        # symbol="NIFTY20MAR26000CALL" 
        # csv_file_path = "/home/ubuntu/Backend/AlgoView-Devlopment/Backend/main/dhantoken.csv"
        csv_file_path ="/home/digiprima/Desktop/jyoti/Django/AlgoView-Devlopment/Backend/main/dhantoken.csv"
        df = pd.read_csv(csv_file_path, low_memory=False)
        
        # df['SEM_CUSTOM_SYMBOL'] = df['SEM_TRADING_SYMBOL'].str.replace("-", "").str.strip()
        df['SEM_TRADING_SYMBOL'] = df['SEM_TRADING_SYMBOL'].astype(str).str.strip().str.replace(r"[^\w]", "", regex=True).str.upper()
        # print(":::::::::::::::::::::::::",df['SEM_TRADING_SYMBOL'])
        df['SEM_EXPIRY_DATE'] = pd.to_datetime(df['SEM_EXPIRY_DATE']).dt.strftime('%Y-%m-%d')
        print("LLLSEM_EXPIRY_DATE===============", df['SEM_EXPIRY_DATE'])
        # filtered_df = df[df['SEM_TRADING_SYMBOL'] == symbol.upper() ]
        filtered_df = df[
            (df['SEM_TRADING_SYMBOL'] == symbol.upper()) & 
            (df['SEM_EXPIRY_DATE'] == expiry_date)
        ]
        
        if not filtered_df.empty:
            # Return the first matching record's ScripCode
            SECURITY_ID = filtered_df.iloc[0]['SEM_SMST_SECURITY_ID']
            return {"status": "success", "SECURITY_ID": SECURITY_ID}
        else:
            status={"status": "error", "message": "No records found matching the given symbol and exchange."}
            logger.info(f"{status}")
            return  None
    
    except Exception as e:
        msg= f"status is :error An error occurred.details: {str(e)}"
        logger.info(f"{msg}")
        return  None


