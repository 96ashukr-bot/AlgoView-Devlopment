from django.http import JsonResponse
from kiteconnect import KiteConnect
from main.Alice_Blue_Api import save_trade_order_history
from main.models import ClientBrokerdetails, CompanySmtpDetails
import logging
logger = logging.getLogger('main')

def place_zerodha_orders(LivePrice,access_token, Api_key, trade_symbol, transaction_type, symbol, quantity,
    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, 
    EntryQty, ExitQty, webhook_signal, Exchange, Segment,Index_Symbol, triggerPrice, trade_order_status):
    print("index symbolllllll",Index_Symbol)
    try:
        
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
            status = "Failed"
            message = f"API key and access token are Not valid for. {user}"
            res_data = f"{str(e)}"
            response={"data": {"status": status,"message":message}}
            save_trade_order_history(LivePrice,transaction_type,trade_order_status, user, symbol, order_id, status, res_data, message,  
                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
            return response

        trading_symbol = get_trading_symbol(Exchange, trade_symbol, kite)

        if not trading_symbol:
            logger.error(f"trading_symbol details not found for {trade_symbol}")
            message = "Instrument details not found"
            res_data = "Trading symbol not found."
            response={"data": {"status": status,"message":message}}
            save_trade_order_history(LivePrice,transaction_type,trade_order_status, user, symbol, order_id, status, res_data, message,  
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
     
            order_id =order_response#order_response.get('order_id')
            if not order_id:
                logger.error("Order ID is not returned")
                status = "Failed"
                message = "No order ID returned"
                res_data = "No order ID returned"
                response={"data": {"status": status,"message":message}}
                save_trade_order_history(LivePrice,transaction_type,trade_order_status, user, symbol, order_id, status, res_data, message,
                                         strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                         webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                return response

            # Ensure that get_order_details is defined or handled properly
            order_history_response = get_order_details(order_id, kite)
            
            logger.info(f"Order history response: {order_history_response}")
            if order_history_response.get("error")=="Failed":
                logger.error("Order details is not found")
                status = "Failed"
                message = "order details not found"
                res_data = order_history_response.get("error")
                response={"data": {"status": status,"message":message}}
                save_trade_order_history(LivePrice,transaction_type,trade_order_status, user, symbol, order_id, status, res_data, message,
                                         strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                         webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                return response
            latest_status = order_history_response[-1]  # Assuming the last item is the most recent
            status = latest_status.get("status", "").lower()
            res_data=latest_status
            print("status>>>>>>>>>>>>>>>",status)
            if status == 'complete':
                message =  latest_status.get('status_message', "Order complete")
                logger.info(f"Order placed successfully. Order ID: {order_id}")
                trasaction_type=res_data.get('transaction_type','')
                if trasaction_type == "BUY":
                    Entry_type="LE"
                    Entry_price=res_data.get ('average_price', 0.0)
                    EntryQty=res_data.get ('quantity', 0)
                elif trasaction_type == "SELL": 
                    Exit_type="LX"
                    Exit_price=res_data.get ('average_price', 0.0)  
                    ExitQty= res_data.get ('quantity', 0)
                response = {"data": {"status": "completed", "message": "Order placed and details saved successfully."}}
                save_trade_order_history(LivePrice,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                
                return response
            elif status=="rejected":
                 # from_email = default_from_email,
            # send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
           
                message = latest_status.get('status_message', "order rejected")
                response = {"data": {"status": status, "message": message}}
                save_trade_order_history(LivePrice,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                return response
            else:
                message = latest_status.get('status_message', "Success")
                response = {"data": {"status": status, "message": message}}
                save_trade_order_history(LivePrice,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                return response

        except Exception as e:
            error_message = f"Failed to place order: {str(e)}"
            logger.error(error_message)
            order_id = 0
            response={"data": {"status": status,"message": str(e)}}
            save_trade_order_history(LivePrice,transaction_type,trade_order_status, user, trade_symbol, order_id, "Failed", None, str(e),
                                     strategy, Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal, Exchange,
                                     Segment, Index_Symbol, order_params, broker="zerodha")
            return response

    except Exception as e:
        logger.error(f"Exception in Zerodha order placement: {str(e)}")
        error_message = f"Failed to place order: {str(e)}"
        logger.error(error_message)
        order_id = 0
        response={"data": {"status": status,"message": str(e)}}
        save_trade_order_history(LivePrice,transaction_type,trade_order_status, user, trade_symbol, order_id, "Failed", None, str(e),
                        strategy, Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal, Exchange,
                                    Segment, Index_Symbol, order_params, broker="zerodha")
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
        print("order_history>>>",order_history)
        if order_history:
            return order_history
        else:
            return {"status": "Failed", "error": "No order history found for the given order ID."}
    except Exception as e:
        return {"status": "Failed", "error": f"Failed to fetch order history: {str(e)}"}
