
# Constants for Alice Blue API
BASE_URL = "https://ant.aliceblueonline.com/rest/AliceBlueAPIService/api/"
ORDER_PLACE_API="placeOrder/executePlaceOrder"
ALICE_ORDER_URL = BASE_URL + ORDER_PLACE_API
GET_ORDER_BOOK_API="placeOrder/fetchOrderBook"
GET_ORDER_BOOK_URL=BASE_URL+GET_ORDER_BOOK_API
GET_TREAD_BOOK_API="placeOrder/fetchTradeBook"
GET_TREAD_BOOK_URL=BASE_URL+GET_TREAD_BOOK_API
import os
from django.conf import settings
from pya3 import *
#from alice_blue import *
from decouple import config
import pytz
from main.models import *
from main.tasks import send_trade_email_async

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import pandas as pd
USER_ID=config('USER_ID')
ALICE_API_KEY=config('ALICE_API_KEY')

import logging
logger = logging.getLogger('main')
from pya3 import Aliceblue, TransactionType, OrderType, ProductType
# from pya3.enums import TransactionType  # Adjust import based on your library
def place_alice_orders(api_skey,api_uid,trading_symbol_aliceblue,transaction_type, symbol, quantity, strategy, 
    order_type, product_type, price, user,Lots, trade_order_status, Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal, Exchange, Segment,Index_Symbol, trigger_price=None):
    try:
        smtp_details=CompanySmtpDetails.objects.first()
        default_from_email=smtp_details.email_host_user if smtp_details else   "no-reply@example.com" 
        print(f"Order Type: {order_type}, Price: {price}, Trigger Price: {trigger_price}")
        # # Convert price and trigger price to float if provided
        price = float(price) if price is not None else None
        trigger_price = float(trigger_price) if trigger_price is not None else None
        # symbol = 'INFY'  # Stock symbol
        order_params = {
        "symbol":trading_symbol_aliceblue,
        "transactiontype": transaction_type,
        "quantity": quantity,
        "ordertype": order_type,
        "pCode":product_type,
        "price": price if order_type.upper() == "LIMIT" else None,
        "triggerprice": trigger_price,
        "strategy":strategy
    }
        def serialize_data(data):
            """Helper function to serialize datetime objects."""
            if isinstance(data, dict):
                return {key: (value.isoformat() if isinstance(value, datetime) else value) for key, value in data.items()}
            return data.isoformat() if isinstance(data, datetime) else data

        # Serialize `order_params` and other fields if necessary
        order_params = serialize_data(order_params)
        if transaction_type.upper() == "BUY":
           transaction_type = TransactionType.Buy
        elif transaction_type.upper()=="SELL":
            transaction_type=TransactionType.Sell
        if product_type:
            # print("product_type>>>>",product_type)
            if product_type.upper() =="NRML" or product_type.upper()=="NORMAL":
               product_type= ProductType.Normal
            elif product_type.upper() == "MIS" or product_type.upper()=="INTRADAY":
               product_type = ProductType.Intraday
            elif product_type.upper() =="CNC" or product_type.upper()=="DELIVERY":    
                product_type = ProductType.Delivery
        else:
            product_type=None

        # Initialize Aliceblue API
        # alice = Aliceblue(user_id=USER_ID, api_key=ALICE_API_KEY)
        alice = Aliceblue(user_id=api_uid, api_key=api_skey)  # Example user attributes
        # Check session validity
        session_id = alice.get_session_id()
        # print("session_id?????",session_id)
        if not session_id or not session_id.get('sessionID'):
            error_message = session_id.get('emsg', 'Invalid credentials or unauthorized access')
            print(f"Failed to establish Aliceblue session. Reason!!!!!!!!!: {error_message}")          
            response = {"data": {"status": "Unauthorized", "message": error_message}}
            order_id=0
            status="Unauthorized"
            res_data=response,
            print("error_message>>>>",error_message)
            message= f"{error_message}"
            # if status=="Unauthorized":
            save_trade_order_history(trade_order_status,user,trading_symbol_aliceblue, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker="Alice Blue")        
            logger.error(f"Unauthorized access for user {user}. Reason: {error_message}")
            return response
        
        # Place the order
        if Exchange=="NFO":
            logger.info(f"exchnage symbole....{trading_symbol_aliceblue}")
            instrument = alice.get_instrument_by_symbol("NFO", trading_symbol_aliceblue)
            logger.info(f"instrument>>>{instrument}")
        elif Exchange=="BSE":
            instrument = alice.get_instrument_by_symbol("BSE", trading_symbol_aliceblue)
        # print("instrument>>>",instrument)
        # Check if the instrument is valid
        if isinstance(instrument, Instrument):
            logger.info(f"Instrument found: {instrument.symbol}")
        elif isinstance(instrument, dict) and instrument.get("stat") == "Not_ok":
            error_message = instrument.get("emsg", "Instrument not available")
            order_id=0
            status="Failed"
            res_data="unknown response"
            message=error_message
            save_trade_order_history(trade_order_status,user,trading_symbol_aliceblue,order_id , status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker="Alice Blue")
            logger.error(f"Instrument not found for symbol: {trading_symbol_aliceblue}, Reason: {error_message}")
            return {"data":{"status": "error", "message": error_message}}
        else:
            logger.error(f"Unexpected response for instrument: {instrument}")
            return {"data":{"status": "error", "message": "Unexpected response for instrument"}}

        logger.info("Placing order with parameters:")

        # Convert the dictionary to a JSON string if needed
        # order_params_json = json.dumps(order_params, indent=4)
        # logger.info(f"order payload for alice blue...",order_params)
                
        logger.info(f"Transaction: {transaction_type}, Instrument: {instrument}, "
              f"Quantity: {quantity}, Order Type: {order_type}, Product Type: {product_type}, "
              f"Price: {price}, Trigger Price: {trigger_price}")
        response=None
        
        # lot_size = get_lot_size(trading_symbol_aliceblue)  # Implement this function to fetch lot size
        # # To get the lot size, access the correct key, which is 'lot_size'
        # lot = int(lot_size.get("lot_size", 0))  # Convert lot_size to an integer (default to 0 if not found)

        # # Check if the order quantity is a multiple of the lot size
        # if quantity % lot != 0:
        #     logger.error(f"Invalid quantity {quantity}, it should be in multiples of lot size: {lot}")
        #     order_id=0
        #     status="Failed"
        #     res_data="unknown response",
        #     message=f"Invalid quantity {quantity}, it should be in multiples of lot size: {lot}"
        #     save_trade_order_history(trade_order_status,user,trading_symbol_aliceblue, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker="Angle One")

        #     return {"data": {"status": "error", "message": f"Quantity must be a multiple of lot size: {lot}"}}
        if order_type.upper()=="LIMIT":
            order_type=OrderType.Limit
            response = alice.place_order(transaction_type = transaction_type,
                    instrument = instrument, 
                    quantity = quantity, 
                    order_type = order_type, 
                    product_type = product_type,
                    price=price,
                    )
        elif order_type.upper()=="MARKET":
            print("inside market order")
            response = alice.place_order(transaction_type = transaction_type,
                        instrument = instrument, 
                        quantity = quantity, 
                        order_type = OrderType.Market, 
                        product_type = product_type,
                        trigger_price=trigger_price)

        print(f"Order Response:::: {response}")
        if response is not None:
        # Log and save order details
            if response.get("stat") == "Ok":
                order_id=response.get("NOrdNo")
                order_his=alice.get_order_history(order_id)
                # Extract the status
                status = order_his.get('Status', '').lower()  # Retrieve 'Status' key, fallback to '' if not found
                res_data=order_his
                logger.info(f"history of alice blue order_____________{order_his}")
                logger.info(f"status......{status}")
                if status == "completed":
                    order_id=res_data.get ('Nstordno', 0)   
                    trasaction_type=res_data.get('Trantype','')
                    if trasaction_type == "B":
                        Entry_type="LE"
                        Entry_price=res_data.get ('Avgprc', 0.0)
                        EntryQty=res_data.get ('Qty', 0)
                    elif trasaction_type == "S": 
                        Exit_type="LX"
                        Exit_price=res_data.get ('Avgprc', 0.0)  
                        ExitQty= res_data.get ('Qty', 0)
                    response = {"data": {"status": "completed"}}
                    logger.info(f"Order placed successfully for user {user}. Order ID: : {order_id}")
                    print("Entry_type>>>",Entry_type)
                    message=f"Order placed successfully for user {user}. Response: {response}"
                    save_trade_order_history(trade_order_status,user,trading_symbol_aliceblue, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price ,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="Alice Blue")
                    return response
                elif status == "rejected": 
                    order_id=res_data.get ('Nstordno', 0) 
                    from_email = default_from_email,
                    message=order_his.get('RejReason', 'not any reason get').lower()
                    send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                    response = {"data": {"status": "rejected"}}
                    logger.info(f"Order is rejected  for user {user}. Order ID: {order_id}")
                    save_trade_order_history(trade_order_status,user,trading_symbol_aliceblue, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="Alice Blue")
                    return response
                elif status == "OPEN":   
                    order_id=res_data.get ('Nstordno', 0) 
                    from_email = default_from_email,
                    message=order_his.get('RejReason', 'not any reason get').lower()
                    send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                    response = {"data": {"status": "OPEN"}}
                    logger.info(f"Order  order is active and open in the market  for user {user}. Order ID:  :{order_id}")
                    save_trade_order_history(trade_order_status,user,trading_symbol_aliceblue, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="Alice Blue")
                    return response
            # elif response.get("stat") == 'Not_ok':
            #     print("Not_okNot_okNot_okNot_ok")
            #     # error_message = response.get("message", "Unknown error")
            #     response ={"data": {"status": "Failed"}}
            #     error_message="401 - Unauthorized"
            #     order_id=None
            #     status="Failed"
            #     res_data="login in"
            #     logger.error(f"Order placement Failed for user {user}. Error: {error_message}")
            #     save_trade_order_history(trade_order_status,user,trading_symbol_aliceblue, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type ,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker="Alice Blue")
            else:
                # error_message = response.get("message", "Unknown error")
                response ={"data": {"status": "Failed"}}
                error_message="error when placing order"
                order_id=None
                status="Failed"
                res_data="Not any reponse Failed"
                logger.error(f"Order placement Failed for user {user}. Error: {error_message}")
                
                save_trade_order_history(trade_order_status,user,trading_symbol_aliceblue, order_id, status, res_data, message,  strategy,   Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty  ,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker="Alice Blue")
                return response       
        else:
            # error_message = response.get("message", "Unknown error")
            response ={"data": {"status": "Failed"}}
            error_message="error when placing order"
            order_id=None
            status="Failed"
            res_data="Not any reponse Failed"
            logger.error(f"Order placement Failed for user {user}. Error: {error_message}")
            
            save_trade_order_history(trade_order_status,user,trading_symbol_aliceblue, order_id, status, res_data, message,  strategy,   Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty  ,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker="Alice Blue")
            return response 
    except ValueError as val_err:
        logger.error(f"Validation error: {val_err}")
        return {"data":{"status": "error", "message": str(val_err)}}

    except AttributeError as attr_err:
        logger.error(f"Attribute error: {attr_err}")
        return {"data":{"status": "error", "message": str(attr_err)}}

    except Exception as e:
        logger.exception(f"Unexpected error while placing order for user {user}")
        # save_webhook_signals_logs(transaction_type, symbol, price, strategy, user, "Failed", failure_reason=str(e),json=json)
        return {"data":{"status": "error", "message": "An unexpected error occurred"}}

def save_trade_order_history(trade_order_status,client, trading_symbol, order_id, order_status, response_data, failure_reason,
      strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal, Exchange, Segment,Index_Symbol ,order_params=None,broker=None ):
    print("Exit_type>>>>",Exit_type,"Entry_type>>>",Entry_type)
    try:
        # Calculate signal times based on entry and exit types
        SignalEntry_time = now() if Entry_type else None
        SignalExit_time = now() if Exit_type else None
        # Create a new Tradeorderhistory record
        trade_history = Tradeorderhistory.objects.create(
        client=client,
        trading_symbol=trading_symbol,
        order_id=order_id,
        order_status=order_status,
        response_data=response_data or None,    
        failure_reason=failure_reason or None,    
        broker=broker or None,    
        order_params=order_params or None,    
        strategy= strategy or None,     
        Entry_type=Entry_type or None,  
        Exit_type=Exit_type or None   ,
        Entry_Price=Entry_price  or None,  
        Exit_Price=Exit_price or None,     
        SignalEntry_time=SignalEntry_time,     
        SignalExit_time=SignalExit_time, 
        Exchange=Exchange or None,     
        Segment=Segment or None,     
        Index_Symbol=Index_Symbol or None,
        webhook_signal=webhook_signal or None,
        trade_order_status=trade_order_status or None,
        EntryQty=EntryQty or None,
        ExitQty=ExitQty or None
    )

        # Log success (optional)
        logger.info(f"Order history saved successfully for Order ID: {order_id}")
        return trade_history  # Return the created record, if needed
    except Exception as e:
        # Handle any exceptions that may occur during the save process
        logger.error(f"Error saving order history for Order ID: {order_id}. Error: {e}")
        logger.debug(
        "Field values: "
        f"client={client}, "
        f"trading_symbol={trading_symbol}, "
        f"order_id={order_id}, "
        f"order_status={order_status}, "
        f"response_data={response_data}, "
        f"failure_reason={failure_reason}, "
        f"broker={broker}, "
        f"order_params={order_params}, "
        f"strategy={strategy}, "
        f"Entry_type={Entry_type}, "
        f"Exit_type={Exit_type}, "
        f"Exchange={Exchange}, "
        f"Segment={Segment}, "
        f"Index_Symbol={Index_Symbol}"
    )
        return None  # Or handle the error as needed


import holidays
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

def is_market_open_old():
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
    return  False


def is_market_open():
    """
    Function to check if the Indian stock market is currently open.
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

    # Custom stock market holidays for the current year
    stock_market_holidays = [
        datetime(2025, 1, 26).date(),  # Republic Day
        datetime(2025, 3, 10).date(),  # Holi
        datetime(2025, 8, 15).date(),  # Independence Day
        datetime(2025, 10, 2).date(),  # Gandhi Jayanti
        datetime(2025, 11, 11).date(),  # Diwali Balipratipada
    ]

    # Log current state
    logger.info(f"Current date and time: {now}")
    logger.info(f"Market open time: {market_open_time}, Market close time: {market_close_time}")
    logger.info(f"Today is: {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][current_day]}")

    # Check if the market is closed for a holiday
    if now.date() in stock_market_holidays:
        logger.info("Market is closed due to a stock market holiday.")
        return False

    # Check if today is a weekday and time is within market hours
    if 0 <= current_day <= 4:  # Monday to Friday
        if market_open_time <= current_time <= market_close_time:
            logger.info("Market is open.")
            return True

    logger.info("Market is closed.")
    return True#False



import time

class SymbolExpirDateListView(APIView):
    # Uncomment this if authentication is required
    # permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        start_time = time.time()
        symbol = request.query_params.get('symbol', None)

        if not symbol:
            return Response({"error": "Symbol parameter is required"}, status=400)

        try:
            # Define the CSV file path
            csv_file_path = "NFO.csv"

            # Check if the file exists and is up-to-date
            if os.path.exists(csv_file_path):
                print("csv is updateddddddddddd")
                # Get the file's last modified time
                file_modified_time = datetime.fromtimestamp(os.path.getmtime(csv_file_path))
                # Check if the file is older than a month
                if datetime.now() - file_modified_time > timedelta(days=5):
                    print("File is outdated. Downloading fresh NFO.csv...")
                    self.download_nfo_csv(csv_file_path)
                else:
                    print("Using existing NFO.csv...")
            else:
                print("File not found. Downloading fresh NFO.csv...")
                self.download_nfo_csv(csv_file_path)

            # Load the CSV file
            data = pd.read_csv(csv_file_path)

            # Filter rows based on the provided symbol
            filtered_data = data[data['Symbol'].str.contains(symbol, case=False, na=False)]

            # Extract unique expiry dates
            unique_expiry_dates = filtered_data['Expiry Date'].unique()
            unique_expiry_dates = filtered_data['Expiry Date'].unique()
            # Sort the expiry dates
            unique_expiry_dates_sorted = sorted(unique_expiry_dates)

            end_time = time.time()
            total_time = end_time - start_time
            print("total_time>>>", total_time)

            # Return the sorted expiry dates as a response
            return Response({"expiry_dates": unique_expiry_dates_sorted}, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def download_nfo_csv(self, csv_file_path):
        """
        Downloads the NFO contract master data and saves it as a CSV file.
        """
        alice = Aliceblue(user_id=USER_ID, api_key=ALICE_API_KEY)
        alice.get_session_id()  # Authenticate the session
        nfo_data = alice.get_contract_master("NFO")
        
        # Save the data to a CSV file
        # with open(csv_file_path, "w") as file:
        #     file.write(nfo_data)
        print(f"Downloaded fresh NFO.csv to {nfo_data}")
