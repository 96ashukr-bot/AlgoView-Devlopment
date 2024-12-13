
# Constants for Alice Blue API
BASE_URL = "https://ant.aliceblueonline.com/rest/AliceBlueAPIService/api/"
ORDER_PLACE_API="placeOrder/executePlaceOrder"
ALICE_ORDER_URL = BASE_URL + ORDER_PLACE_API
GET_ORDER_BOOK_API="placeOrder/fetchOrderBook"
GET_ORDER_BOOK_URL=BASE_URL+GET_ORDER_BOOK_API
GET_TREAD_BOOK_API="placeOrder/fetchTradeBook"
GET_TREAD_BOOK_URL=BASE_URL+GET_TREAD_BOOK_API
from django.conf import settings
from pya3 import *
from decouple import config
import pytz
from main.models import *
from main.tasks import send_trade_email_async
USER_ID=config('USER_ID')
ALICE_API_KEY=config('ALICE_API_KEY')
import logging
logger = logging.getLogger('main')
from pya3 import Aliceblue, TransactionType, OrderType, ProductType
# from pya3.enums import TransactionType  # Adjust import based on your library
def place_alice_orders(api_skey,api_uid,trading_symbol_aliceblue,transaction_type, symbol, quantity, strategy, order_type, product_type, price, user,Lots, trigger_price=None):
    try:
        print(f"Order Type: {order_type}, Price: {price}, Trigger Price: {trigger_price}")
        # # Convert price and trigger price to float if provided
        price = float(price) if price is not None else None
        trigger_price = float(trigger_price) if trigger_price is not None else None
        # symbol = 'INFY'  # Stock symbol
        order_params = {
        "transactiontype": transaction_type,
        "quantity": quantity,
        "ordertype": order_type,
        "producttype": product_type,
        "price": price,
        "triggerprice": trigger_price
    }
        print("symbol",symbol)
        if transaction_type.upper() == "BUY":
           transaction_type = TransactionType.Buy
        elif transaction_type.upper()=="SELL":
            transaction_type=TransactionType.Sell
       
        if product_type:
            if product_type.upper() =="NRML":
               product_type= ProductType.Normal
            elif product_type.upper() =="MIS":
                product_type=ProductType.MIS
            elif product_type.upper() =="INTRADAY":      
                product_type = ProductType.Intraday
        else:
            product_type=None
        # Initialize Aliceblue API
        # alice = Aliceblue(user_id=USER_ID, api_key=ALICE_API_KEY)
        alice = Aliceblue(user_id=api_uid, api_key=api_skey)  # Example user attributes
        # Check session validity
        session_id = alice.get_session_id()
        if not session_id or not session_id.get('sessionID'):
            error_message = session_id.get('emsg', 'Invalid credentials or unauthorized access')
            print(f"Failed to establish Aliceblue session. Reason!!!!!!!!!: {error_message}")
            response = {"data": {"status": "Unauthorized", "message": error_message}}
            logger.error(f"Unauthorized access for user {user}. Reason: {error_message}")
            return response
        
        # Place the order
        instrument = alice.get_instrument_by_symbol('NFO', trading_symbol_aliceblue)
        if not instrument:
            raise ValueError(f"Instrument not found for symbol: {trading_symbol_aliceblue}")

        logger.info("Placing order with parameters:")


        # Convert the dictionary to a JSON string if needed
        order_params_json = json.dumps(order_params, indent=4)
        logger.info(f"order payload for alice blue...",order_params)
                
        logger.info(f"Transaction: {transaction_type}, Instrument: {instrument.symbol}, "
              f"Quantity: {quantity}, Order Type: {order_type}, Product Type: {product_type}, "
              f"Price: {price}, Trigger Price: {trigger_price}")
        response=None
        print("order_type>>>",order_type)
        if order_type=="LIMIT":
            order_type=OrderType.Limit
            response = alice.place_order(transaction_type = transaction_type,
                        instrument = instrument, 
                        quantity = quantity, 
                        order_type = order_type, 
                        product_type = product_type,
                        # price=price,
                        )
        elif order_type=="MARKET":
            order_type= OrderType.Market
            response = alice.place_order(transaction_type = transaction_type,
                        instrument = instrument, 
                        quantity = quantity, 
                        order_type = order_type, 
                        product_type = product_type,
                        trigger_price=trigger_price)
            print("MARKET ORDER RESP...",response)
        elif order_type=="StopLossLimit":
            order_type= OrderType.StopLossLimit,     
            response = alice.place_order(transaction_type = transaction_type,
                        instrument = instrument, 
                        quantity = quantity, 
                        order_type = order_type, 
                        product_type = product_type,
                        price=price,
                        trigger_price=trigger_price,
                        stop_loss=None,
                        square_off=None,
                        trailing_sl=None,
                        is_amo=False,
                        order_tag='order1') 
        elif order_type=="StopLossMarket":
            order_type=OrderType.StopLossMarket
            response = alice.place_order(transaction_type = transaction_type,
                        instrument = instrument, 
                        quantity = quantity, 
                        order_type = order_type, 
                        product_type = product_type,
                        price=price,
                        trigger_price=trigger_price,
                        stop_loss=None,
                        square_off=None,
                        trailing_sl=None,
                        is_amo=False,
                        order_tag='order1') 

        print(f"Order Response: {response}")
        # Log and save order details
        if response.get("stat") == "Ok":
            order_id=response.get("NOrdNo")
            order_his=alice.get_order_history(order_id)
            # Extract the status
            status = order_his.get('Status', '').lower()  # Retrieve 'Status' key, fallback to '' if not found
            res_data=order_his
            logger.info(f"history of alice blue order_____________{order_his}")
            logger.info(f"status......{status}")
            if status == "success":
                response = {"data": {"status": "completed"}}
                logger.info(f"Order placed successfully for user {user}. Response: {response}")
                save_trade_order_history(user,symbol, order_id, status, res_data, message,order_params, broker="Angle One")
              
            elif status == "rejected":   
                from_email = settings.DEFAULT_FROM_EMAIL,
                message=order_his.get('RejReason', 'not any reason get').lower()
                send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                response = {"data": {"status": "rejected"}}
                logger.info(f"Order is rejected  for user {user}. Response :{response}")
                save_trade_order_history(user,symbol, order_id, status, res_data, message,order_params, broker="Angle One")
        # elif response.get("stat") == 'Not_ok':
        #     print("Not_okNot_okNot_okNot_ok")
        #     # error_message = response.get("message", "Unknown error")
        #     response ={"data": {"status": "Failed"}}
        #     error_message="401 - Unauthorized"
        #     order_id=None
        #     status="Failed"
        #     res_data="login in"
        #     logger.error(f"Order placement failed for user {user}. Error: {error_message}")
        #     save_trade_order_history(user,symbol, order_id, status, res_data, message, order_params,broker="Angle One")
        else:
            print("Not_okNot_okNot_okNot_ok")
            # error_message = response.get("message", "Unknown error")
            response ={"data": {"status": "Failed"}}
            error_message="error when placing order"
            order_id=None
            status="Failed"
            res_data="Not any reponse failed"
            logger.error(f"Order placement failed for user {user}. Error: {error_message}")
            save_trade_order_history(user,symbol, order_id, status, res_data, message, order_params,broker="Angle One")
                   
            # save_webhook_signals_logs(transaction_type, symbol, price, strategy, user, "Failed", failure_reason="somthing wrong in order place",json=json)
        # if response.get('stat') == 'Not_Ok':
        #     rejection_reason = response.get('emsg', 'Unknown error')
        #     print(f"Order rejected. Reason: {rejection_reason}")
        #     logger.error(f"Order rejected. Reason: {rejection_reason}")
        print("response>>>",response)
        return response

    except ValueError as val_err:
        logger.error(f"Validation error: {val_err}")
        # save_webhook_signals_logs(transaction_type, symbol, price, strategy, user, "Failed", failure_reason=str(val_err),json=json)
        return {"status": "error", "message": str(val_err)}

    except AttributeError as attr_err:
        logger.error(f"Attribute error: {attr_err}")
        # save_webhook_signals_logs(transaction_type, symbol, price, strategy, user, "Failed", failure_reason="Invalid API usage",json=json)
        return {"status": "error", "message": str(attr_err)}

    except Exception as e:
        logger.exception(f"Unexpected error while placing order for user {user}")
        # save_webhook_signals_logs(transaction_type, symbol, price, strategy, user, "Failed", failure_reason=str(e),json=json)
        return {"status": "error", "message": "An unexpected error occurred"}

def save_trade_order_history(client, trading_symbol, order_id, order_status, response_data, failure_reason, order_params=None,broker=None):
    try:
        # Create a new Tradeorderhistory record
        trade_history = Tradeorderhistory.objects.create(
            client=client,
            trading_symbol=trading_symbol,
            order_id=order_id,
            order_status=order_status,
            response_data=response_data,
            failure_reason=failure_reason,
            broker=broker,
            order_params=order_params
        )
        # Log success (optional)
        logger.info(f"Order history saved successfully for Order ID: {order_id}")
        return trade_history  # Return the created record, if needed
    except Exception as e:
        # Handle any exceptions that may occur during the save process
        logger.error(f"Error saving order history for Order ID: {order_id}. Error: {e}")
        return None  # Or handle the error as needed


import holidays
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

def is_market_open():
    print("Checking market status...")
    """
    Function to check if the market is currently open.
    Returns True if open, False otherwise.
    """
    # Define market hours (e.g., 9:15 AM to 3:30 PM for Indian stock markets)
    market_open_time = datetime.strptime("09:15", "%H:%M").time()
    market_close_time = datetime.strptime("15:30", "%H:%M").time()

    # Get the current time in the market's timezone (e.g., Asia/Kolkata)
    market_timezone = pytz.timezone("Asia/Kolkata")
    now = datetime.now(market_timezone)
    current_time = now.time()
    current_day = now.weekday()  # Monday = 0, Sunday = 6

    # Fetch holidays for India for the current year
    market_holidays = holidays.India(years=now.year)
    # print("market_holidays>>",market_holidays)
    # Log current state
    logger.info(f"Current date and time: {now}")
    logger.info(f"Market open time: {market_open_time}, Market close time: {market_close_time}")
    logger.info(f"Today is: {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][current_day]}")

    # Check if the market is closed for a holiday
    if now.date() in market_holidays:
        logger.info("Market is closed due to a holiday.")
        return False

    # Check if today is a weekday and time is within market hours
    if current_day >= 0 and current_day <= 4:  # Monday to Friday
        if market_open_time <= current_time <= market_close_time:
            logger.info("Market is open.")
            return True

    logger.info("Market is closed.")
    return False




# def is_market_open():
#     print("checking market status............")
#     """
#     Function to check if the market is currently open.
#     Returns True if open, False otherwise.
#     """
#     # Define market hours (e.g., 9:15 AM to 3:30 PM for Indian stock markets)
#     market_open_time = datetime.strptime("09:15", "%H:%M").time()
#     market_close_time = datetime.strptime("15:30", "%H:%M").time()

#     # Get the current time in the market's timezone (e.g., Asia/Kolkata)
#     market_timezone = pytz.timezone("Asia/Kolkata")
#     now = datetime.now(market_timezone)
#     current_time = now.time()
#     current_day = now.weekday()  # Monday = 0, Sunday = 6

#     # Define market holidays
#     market_holidays = [
#         "2024-12-25",  # Christmas
#         "2025-01-01",  # New Year's Day
#     ]

#     # Log current state
#     logger.info(f"Current date and time: {now}")
#     logger.info(f"Market open time: {market_open_time}, Market close time: {market_close_time}")
#     logger.info(f"Today is: {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][current_day]}")

#     # Check if the market is closed for a holiday
#     if now.strftime("%Y-%m-%d") in market_holidays:
#         logger.info("Market is closed due to a holiday.")
#         return False

#     # Check if today is a weekday and time is within market hours
#     if current_day >= 0 and current_day <= 4:  # Monday to Friday
#         if market_open_time <= current_time <= market_close_time:
#             logger.info("Market is open.")
#             return True

#     logger.info("Market is closed.")
#     return False
