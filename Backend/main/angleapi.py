import json
import os
import csv
from rest_framework.views import APIView
from rest_framework.response import Response
import time
from django.conf import settings
import pandas as pd
import pyotp
from SmartApi import SmartConnect
from SmartApi.smartExceptions import DataException
from time import sleep
import numpy as np
import logging
import requests
from main.Alice_Blue_Api import save_trade_order_history
from main.dematemodule import get_lot_size
from main.models import CompanySmtpDetails, Tradeorderhistory
from main.tasks import send_trade_email_async
logger = logging.getLogger('main')
from django.db.models import Q
# API_KEY = 'FNqcDPCk'#'Xp6znI3s'
# USERNAME = 'A1420760'
# Totp     = "7DFMHZE3BDRCIHMLFT4N3QVCPU"
# PASSWORD="1986"
# smart_client = SmartConnect(api_key=API_KEY)
# totp = pyotp.TOTP(Totp).now()
def place_Angle_order(LivePrice,api_key,demate_user_name,totp,angle_pass,usertrade,tradingsymbol, quantity, product_type, transactiontype, 
        price, ordertype,lot_size, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal, Exchange,trade_order_status,
        Segment,Index_Symbol ,user=None, strategy=None):

    try:
        order_id=0
        status="Failed"
        tokendata = get_token_details(tradingsymbol) 
        if tokendata["status"] == "success":  
            token = tokendata.get("token")
            token_symbol = tokendata.get("symbol")
            print("**********")

            if not token or not token_symbol:
                logger.error(f"Missing token or symbol for trading symbol: {usertrade.symbol}")
                response= {"data":{"status": "error", "message": "token symbole not found"}}
                return response# continue
        else:
            message= f"trading symbol is not found for this :{tradingsymbol}"
            res_data="no trading symbol found"
            order_params={}
            save_trade_order_history(LivePrice,transactiontype,trade_order_status,user,tradingsymbol, order_id, status, res_data,
                                     message, strategy,  Entry_type,Exit_type, Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal , 
                                     Exchange, Segment,Index_Symbol, order_params,broker="Angle One")
                
            logger.info(f"No token data found for trading symbol: {usertrade.symbol}")
            response= {"data":{"status": "error", "message": "token symbole not found"}}
            return response
        print("Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty>>>",Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty)
        smtp_details=CompanySmtpDetails.objects.first()
        default_from_email=smtp_details.email_host_user if smtp_details else   "no-reply@example.com" 
        logger.info(f"Angle one api order placement for user: {user} & trading symbol is: {tradingsymbol}")
        print("product_type>>>",product_type)
        if product_type:
            if product_type.upper() =="NRML":
               product_type= "CARRYFORWARD"
            elif product_type.upper() =="MIS":
                product_type="INTRADAY"
            elif product_type.upper() =="CNC":      
                product_type ="DELIVERY"
        print("_----------------")
        order_params = {
            "variety": "NORMAL",
            "tradingsymbol": tradingsymbol,
            "symboltoken": token,
            "transactiontype": transactiontype,
            "exchange": Exchange,
            "ordertype": ordertype,
            "producttype": product_type,
            "duration": "DAY",
            "price":price if ordertype.upper() == "LIMIT" else 0,
            "squareoff": "0",
            "triggerprice": "0",
            "stoploss": "0",
            # "lotsize": lot_size,
            "quantity": quantity,
        }
                
        print("order_params...........",order_params)
        api_key = api_key
        username = demate_user_name
        Totp_Secret     = totp
        password=angle_pass
        # smart_client = SmartConnect(api_key=API_KEY)
        # totp = pyotp.TOTP(Totp).now()
        logging.info("Sending Order Request: %s", json.dumps(order_params, indent=4))
        # max_retries = 3
        # for attempt in range(max_retries):
        lot_size = get_lot_size(tradingsymbol)  # Implement this function to fetch lot size
        lot = int(lot_size.get("lot_size", 0))  # Convert lot_size to an integer (default to 0 if not found)
        # Check if the order quantity is a multiple of the lot size
        order_id=0
        status="Failed"
        res_data="unknown response",
        if order_params['quantity'] % lot != 0:
            logger.error(f"Invalid quantity {tradingsymbol}, it should be in multiples of lot size: {lot}")
            message=f"Invalid quantity {tradingsymbol}, it should be in multiples of lot size: {lot}"
            save_trade_order_history(LivePrice,transactiontype,trade_order_status,user,tradingsymbol, order_id, status, res_data, message,  strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol , order_params,broker="Angle One")

            return {"data": {"status": "Failed", "message": f"Quantity must be a multiple of lot size: {lot}"}}

        try:
            smartApi = SmartConnect(api_key=api_key)
            if not smartApi:
                logger.error("Failed to initialize SmartConnect client.")
                return {"data": {"status": "Unauthorized", "message": "API client initialization Failed."}}
            try:
                print("username", username, "password", password, "totp", Totp_Secret)
                session_data = login_user(username, password, Totp_Secret, smartApi)
                if not session_data or not session_data.get("status"):
                    error_message = session_data.get("message", "Unknown error occurred during login.")
                    logger.error("Failed to log in: %s", error_message)
                    res_data = "Invalid API key or invalid credentials"
                    message = error_message
                    save_trade_order_history(LivePrice,transactiontype,
                        trade_order_status, user, tradingsymbol, order_id, status, res_data, message,
                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="Angle One"
                    )
                    return {"data": {"status": "Failed", "message": error_message}}
            except Exception as e:
                # Handle exceptions during the entire process
                logger.error("An error occurred: %s", e)
                res_data = "An exception occurred during login."
                message = str(e)
                save_trade_order_history(LivePrice,transactiontype,
                    trade_order_status, user, tradingsymbol, order_id, status, res_data, message,
                    strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                    webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="Angle One"
                )
                return {"data": {"status": "Failed", "message": f"Exception: {message}"}}
            # If login is successful, proceed further
            logger.info("Login successful.......................")
            response = smartApi.placeOrderFullResponse(order_params)
            logger.info(f"Angle API Response: {response}")
            if response is None:
                logger.error("Received None response from API.")
                message = f"somthing wrong or token is invalid"
                res_data="None response from API"
                save_trade_order_history(LivePrice,transactiontype,trade_order_status,user,tradingsymbol, order_id, status, res_data, message,  strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol , order_params,broker="Angle One")
                return {"data": {"status": "Failed", "message": message}}

            uniqueorderid = response.get('data', {}).get('uniqueorderid', None)
            if not uniqueorderid:
                logger.error(f"Order response does not contain valid uniqueorderid: {response}")
                return {"data": {"status": "Failed", "message": "Failed to retrieve order ID."}}

            responsedetails = smartApi.individual_order_details(uniqueorderid)
            # print("responsedetails>>>",responsedetails)
            if responsedetails is None:
                logger.error("No details found for the order.")
                return {"data": {"status": "Failed", "message": "Failed to retrieve order details."}}

            status = responsedetails['data'].get('status', 'unknown')
            order_id = responsedetails['data'].get('orderid', 'unknown')
            message = responsedetails['data'].get('text', 'No message provided')

            res_data=responsedetails 
            logger.info(f"responsedetails>>>>{responsedetails}")
            if responsedetails['data']['status'] =="completed":
                trasaction_type=responsedetails['data'].get('transactiontype', '')
                if trasaction_type == "BUY":
                    trade_order_status="OPEN"
                    Entry_type="LE"
                    Entry_price=responsedetails['data'].get('averageprice', 0.0)
                    EntryQty=responsedetails['data'].get('quantity', 0)
                elif trasaction_type == "SELL": 
                    trade_order_status="CLOSE"
                    Exit_type="LX"
                    Exit_price=responsedetails['data'].get('averageprice', 0.0) 
                    ExitQty= responsedetails['data'].get('quantity', 0)#disclosedquantity
                order_id=responsedetails['data']['orderid']
                if not order_id:
                    order_id=uniqueorderid
                logger.info(f"Order placed successfully for user {user}. Order ID: {order_id}")
                # log_order(order_data, "orders_placed.csv")  
                message = responsedetails['data'].get('text', 'completed successfully ')
                status=responsedetails['data'].get('status', 'completed')
                save_trade_order_history(LivePrice,transactiontype,trade_order_status,user,tradingsymbol, order_id, status, res_data, message,   strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="Angle One")
                # from_email = default_from_email,
                # send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                # save_webhook_signals_logs(order_params['transactiontype'], symbol, price, strategy, user, status=responsedetails['data'].get('status'),failure_reason="your order place succesfully", json=json)
                response = {"data": {"status": status,"message":message}}
                return response
            
            elif responsedetails['data']['status'] == "open":
                order_id=responsedetails['data']['orderid']
                if not order_id:
                    order_id=uniqueorderid     
                logger.info(f"Order is pending or open state, Order ID: {order_id}")
                trasaction_type=responsedetails['data'].get('transactiontype', '')
                if trasaction_type == "BUY":
                    Entry_type="LE"
                    Entry_price=responsedetails['data'].get('averageprice', 0.0)
                    EntryQty=responsedetails['data'].get('quantity', 0)
                elif trasaction_type == "SELL": 
                    Exit_type="LX"
                    Exit_price=responsedetails['data'].get('averageprice', 0.0) 
                    ExitQty= responsedetails['data'].get('quantity', 0)#disclosedquantity
                # log_order(order_data, "orders_placed.csv")  
                # send massage email aleart to client your order is trade 
                from_email = default_from_email,
                # Send rejection email
                message = responsedetails['data'].get('text', 'Unknown  reason')
                status=responsedetails['data'].get('status', 'pending')
                # print("user.firstName>>>>>",user.firstName)
                # send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                logger.info(f"Order is pending or in process reason is !!!::{message}")
                save_trade_order_history(LivePrice,transactiontype,trade_order_status,user,tradingsymbol, order_id, status, res_data, message,  strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol ,order_params, broker="Angle One")
                response = {"data": {"status": status,"message":message}}
                return response
            
            elif responsedetails['data']['status'] == "rejected":
                rejection_message = responsedetails['data'].get('text', 'Unknown rejection reason')
                status=responsedetails['data'].get('status', 'rejected')
                order_id=responsedetails['data']['orderid']  
                order_id=""
                if not order_id:
                    order_id=uniqueorderid  
                trasaction_type=responsedetails['data'].get('transactiontype', '')
                if trasaction_type == "BUY":
                    Entry_type="LE"
                    Entry_price=responsedetails['data'].get('averageprice', 0.0)
                    EntryQty=responsedetails['data'].get('quantity', 0)
                elif trasaction_type == "SELL": 
                    Exit_type="LX"
                    Exit_price=responsedetails['data'].get('averageprice', 0.0) 
                    ExitQty= responsedetails['data'].get('quantity', 0)#disclosedquantity 
                    print("enrty exit price ",Entry_price,Exit_price,"entry and type",Entry_type,Exit_type)
                logger.info(f"Order Rejected reason!!!::{rejection_message} Order ID: {order_id}")
                from_email = default_from_email,
                # Send rejection email
                print("user.firstName>>>>>",user.firstName)
                send_trade_email_async.delay(user.email, from_email,user.firstName,status, rejection_message)
                save_trade_order_history(LivePrice,transactiontype,trade_order_status,user,tradingsymbol, order_id, status, res_data, rejection_message,  strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol ,order_params ,broker="Angle One")
                # save_webhook_signals_logs(order_params['transactiontype'], symbol, price, strategy, user, status=responsedetails['data'].get('status'),
                response = {"data": {"status": status,"message":message}}
                return response
                
            else:
                rejection_message = responsedetails['data'].get('text', 'Unknown rejection reason')
                status=responsedetails['data'].get('status', 'Failed')
                order_id=responsedetails['data']['orderid']     
                logger.info(f"Order Rejected reason!!!::{rejection_message} Order ID: {order_id}")
                save_trade_order_history(LivePrice,transactiontype,trade_order_status,user,tradingsymbol, order_id, status, res_data, rejection_message,  strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol ,order_params ,broker="Angle One")
                response = {"data": {"status": status,"message":message}}
                return response
        except Exception as e:
            logging.error(f"Order could not be placed  !!!!!!!!!!!{e}")
            msg=f"error in order place angle one {str(e)}"
            # logging.error("Error while placing order on attempt %d/%d: %s", attempt + 1, max_retries, e)
            sleep(1)
            response = {"data": {"status": "Failed","message":msg}}
            return response
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        msg=f"An unexpected error occurred: {str(e)}"
        response = {"data": {"status": "Failed","message":msg}}
        return response

from datetime import datetime, timedelta    
# Order logging function
def log_order(data, filename):
    """Log order details to a CSV file."""
    file_path = os.path.join(log_dir, filename)
    df = pd.DataFrame([data])
    if not os.path.isfile(file_path):
        df.to_csv(file_path, index=False)
    else:
        df.to_csv(file_path, mode='a', header=False, index=False)
# Initialize directory for logging orders
log_dir = "order_logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

import logging
import requests
import json
import os
from datetime import datetime, timedelta

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CACHE_FILE = "angel_token_cache.json"
CACHE_EXPIRY = timedelta(hours=1)

def fetch_and_cache_token_data():
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    
    try:
        logger.info("Fetching token data from API...")
        response = requests.get(url, timeout=10)  
        response.raise_for_status()
        data = response.json()

        with open(CACHE_FILE, "w") as f:
            json.dump({"timestamp": datetime.utcnow().isoformat(), "data": data}, f)

        logger.info("Token data successfully cached.")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching token data: {e}")
        return None

def load_cached_token_data():
    if os.path.exists(CACHE_FILE):
        print("CACHE_FILE>>>>",CACHE_FILE)
        with open(CACHE_FILE, "r") as f:
            cached_data = json.load(f)
            timestamp = datetime.fromisoformat(cached_data["timestamp"])

            if datetime.utcnow() - timestamp < CACHE_EXPIRY:
                logger.info("Using cached token data.")
                return cached_data["data"]
            else:
                logger.info("Cache expired. Fetching new token data.")

    return fetch_and_cache_token_data()

def get_token_details1111(trading_symbol):
    logger.info(f"Searching for trading symbol: {trading_symbol}")
    data = load_cached_token_data()
    if not data:
        logger.error("Failed to load token data.")
        return {"status": "Failed", "message": "Unable to fetch token data"}

    # Convert list to dictionary for faster lookup
    token_dict = {item["symbol"]: item for item in data}

    if trading_symbol in token_dict:
        item = token_dict[trading_symbol]
        logger.info(f"Found token for symbol {trading_symbol}: {item['token']}")
        return {
            "status": "success",
            "token": item.get("token"),
            "symbol": item.get("symbol"),
            "expiry": item.get("expiry"),
        }

    logger.warning(f"No token data found for trading symbol: {trading_symbol}")
    return {"status": "Failed", "message": f"No details found for trading symbol: {trading_symbol}"}


def convert_list_to_dict(data):
    return {item["symbol"]: item for item in data}

def get_token_detailsdict(trading_symbol):
    
    data = load_cached_token_data()
    if not data:
        return {"status": "Failed", "message": "Unable to fetch token data"}

    # Convert list to dictionary for O(1) lookup
    token_dict = convert_list_to_dict(data)

    if trading_symbol in token_dict:
        item = token_dict[trading_symbol]
        return {
            "status": "success",
            "token": item.get("token"),
            "symbol": item.get("symbol"),
            "expiry": item.get("expiry"),
        }

    return {"status": "Failed", "message": f"No details found for trading symbol: {trading_symbol}"}


def get_token_details(trading_symbol):
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  
        data = response.json() 
        logger.info(f"trading_symbol of Angle is ::::::::::::::{trading_symbol}")
        for item in data:
            if item.get("symbol") == trading_symbol:
                logger.info(f"trading symbol found  angle one ::::::::::::{trading_symbol}")
                print("csv token from master data api>>>",item)
                # Return the token and any other details
                return {
                    "status": "success", 
                    "token": item.get("token"),
                    "symbol": item.get("symbol"),
                    "expiry": item.get("expiry"),              
                }
        return {"status": "Failed",  # Indicate that the symbol was not found
            "message": f"No details found for trading symbol: {trading_symbol}"}
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching data: {str(e)}") 
        return {"status": "Failed", "message": f"An error occurred while fetching data:  {str(e)}"}
def save_data_to_file(self, data, filename="symbol_data.json"):
    """
    Save JSON data to a file in the specified directory.
    """
    try:
        os.makedirs(self.target_directory, exist_ok=True)  # Ensure the directory exists
        file_path = os.path.join(self.target_directory, filename)

        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

        logger.info(f"Data successfully saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving data to file: {e}")
# Function to generate TOTP
def generate_totp(token_secret):
    try:
        totp = pyotp.TOTP(token_secret).now()
        logger.info("TOTP generated successfully.")
        return totp
    except Exception as e:
        logger.error("Error generating TOTP: %s", e)
        return None

def login_user(username, password, token_secret, smartApi):
    response = {"status": False, "message": "", "data": None}
    totp = generate_totp(token_secret)
    
    if not totp:
        response["message"] = "Failed to generate TOTP."
        return response
    
    try:
        # Attempt to login
        data = smartApi.generateSession(username, password, totp)
        
        if not data.get("status"):
            response["message"] = f"Login failed: {data.get('message', 'Unknown error')}"
            logger.error("Login Failed: %s", data)
            return response
        
        logger.info("Login successful")
        
        authToken = data["data"]["jwtToken"]
        refreshToken = data["data"]["refreshToken"]
        feedToken = smartApi.getfeedToken()
        user_profile = smartApi.getProfile(refreshToken)
        
        logger.info("User Exchanges: %s", user_profile["data"]["exchanges"])

        # Return session data
        response["status"] = True
        response["message"] = "Login successful."
        response["data"] = {
            "authToken": authToken,
            "refreshToken": refreshToken,
            "feedToken": feedToken,
        }
        return response

    except Exception as e:
        logger.error("Login request failed: %s", e)
        response["message"] = f"Exception occurred: {str(e)}"
        return response


from django.core.cache import cache
import time
import os
import csv
import requests
import pandas as pd
from datetime import datetime
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView
import logging

logger = logging.getLogger("main")

class SymbolExpiryDateListView(APIView):
    CSV_FILE = "ANGLE_NFO.csv"

    def get(self, request, *args, **kwargs):
        start_time = time.time()  # Track start time
        symbol = request.query_params.get('symbol', None)
        if not symbol:
            return Response({"error": "Symbol parameter is required"}, status=400)

        # Check last update timestamp from cache
        last_update = cache.get("csv_last_update")
        logger.info(f"Last CSV update timestamp: {last_update}")

        today_date = datetime.now().date()
        last_update_date = datetime.strptime(last_update, "%Y-%m-%d").date() if last_update else None

        # If the CSV is already updated today, use it
        if last_update_date == today_date and os.path.exists(self.CSV_FILE):
            logger.info("Using today's updated CSV file.")
            response = self.get_expiry_dates_from_csv(symbol)
        else:
            logger.info("Updating CSV file with fresh expiry dates.")
            response = self.update_csv_and_get_expiry_dates(symbol)

        end_time = time.time()  # Track end time
        elapsed_time = round(end_time - start_time, 2)
        logger.info(f"Total execution time: {elapsed_time} seconds")

        return response

    def get_expiry_dates_from_csv(self, symbol):
        """ Reads expiry dates from the existing CSV file """
        try:
            data = pd.read_csv(self.CSV_FILE)
            filtered_data = data[data['name'].str.upper() == symbol.upper()]
            expiry_dates = sorted(set(filtered_data['expiry'].dropna().unique()), key=lambda x: datetime.strptime(x, '%d%b%Y'))

            # Remove past expiry dates
            current_date = datetime.now()
            expiry_dates = [date for date in expiry_dates if datetime.strptime(date, '%d%b%Y') >= current_date]

            if not expiry_dates:
                logger.warning(f"No future expiry dates found for {symbol}.")

            logger.info(f"Expiry dates found: {expiry_dates}")
            return Response({"symbol": symbol, "expiry_dates": expiry_dates}, status=200)

        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return Response({"error": f"Error reading CSV: {str(e)}"}, status=500)

    def update_csv_and_get_expiry_dates(self, symbol):
        """ Fetch fresh data from the API and update the CSV file once per day """
        try:
            url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
            logger.info("Fetching data from Angel One API.")

            response = requests.get(url)
            if response.status_code != 200:
                logger.error("Failed to retrieve data from Angel One API.")
                return Response({"error": "Failed to retrieve data from Angel One API"}, status=response.status_code)

            data = response.json()
            if not data:
                logger.warning("No data received from API.")
                return Response({"error": "No data received from API"}, status=404)

            expiry_dates = []
            with open(self.CSV_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['token', 'symbol', 'name', 'exch_seg', 'expiry', 'instrumenttype'])

                for entry in data:
                    if entry.get('exch_seg') == 'NFO':
                        expiry = entry.get('expiry', '')
                        if expiry:
                            try:
                                parsed_date = datetime.strptime(expiry, '%d%b%Y')
                                expiry_dates.append(parsed_date.strftime('%d%b%Y'))
                            except ValueError:
                                continue  
                        writer.writerow([entry.get('token', ''), entry.get('symbol', ''),
                                         entry.get('name', ''), entry.get('exch_seg', ''),
                                         expiry, entry.get('instrumenttype', '')])

            # Store update timestamp in cache (valid for 24 hours)
            cache.set("csv_last_update", datetime.now().strftime("%Y-%m-%d"), timeout=86400)

            # Process expiry dates
            unique_expiry_dates = sorted(set(expiry_dates), key=lambda x: datetime.strptime(x, '%d%b%Y'))
            filtered_expiry_dates = [expiry for expiry in unique_expiry_dates if symbol.lower() in expiry.lower()]

            if not filtered_expiry_dates:
                logger.warning(f"No expiry dates found for {symbol} after CSV update.")

            logger.info(f"Filtered expiry dates: {filtered_expiry_dates}")
            return Response({"symbol": symbol, "expiry_dates": filtered_expiry_dates}, status=200)

        except Exception as e:
            logger.error(f"Error updating CSV: {e}")
            return Response({"error": str(e)}, status=500)

class SymbolExpiryDateListViewsssss(APIView):
    CSV_FILE = "ANGLE_NFO.csv"
    def get(self, request, *args, **kwargs):
        symbol = request.query_params.get('symbol', None)
        if not symbol:
            return Response({"error": "Symbol parameter is required"}, status=400)

        # Check last update timestamp from cache (store it once per day)
        last_update = cache.get("csv_last_update")
        logger.info(f"last_update symbol expiry date csv::{last_update}")
        if last_update:
            last_update_date = datetime.strptime(last_update, "%Y-%m-%d").date()
        else:
            last_update_date = None

        today_date = datetime.now().date()

        # If the file is updated today, use it
        if last_update_date == today_date and os.path.exists(self.CSV_FILE):
            logger.info(f"If the file is updated today, use it")
            return self.get_expiry_dates_from_csv(symbol)

        # Otherwise, update the CSV file
        return self.update_csv_and_get_expiry_dates(symbol)
    def get_expiry_dates_from_csv(self, symbol):
        """ Reads expiry dates from the existing CSV file """
        try:
            data = pd.read_csv(self.CSV_FILE)
            filtered_data = data[data['name'].str.upper() == symbol.upper()]
            expiry_dates = sorted(set(filtered_data['expiry'].unique()), key=lambda x: datetime.strptime(x, '%d%b%Y'))
            
            # Remove past expiry dates
            current_date = datetime.now()
            expiry_dates = [
                datetime.strptime(date, '%d%b%Y').strftime('%d%b%Y') 
                for date in expiry_dates 
                if datetime.strptime(date, '%d%b%Y') >= current_date
            ]
            logger.info(f"expiry_dates:::::::::",expiry_dates)
            return Response({"symbol": symbol, "expiry_dates": expiry_dates}, status=200)

        except Exception as e:
            return Response({"error": f"Error reading CSV: {str(e)}"}, status=500)

    def update_csv_and_get_expiry_dates(self, symbol):
        """ Fetch fresh data from the API and update the CSV file once per day """
        try:
            # Fetch data from Angel One API
            url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
            headers = {
                "API_KEY": "API_KEY",
                "USERNAME": "USERNAME",
                "PASSWORD": "PASSWORD",
                "Totp": "Totp"
            }
            logger.info(f"update csv file to get expiry dates")
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return Response({"error": "Failed to retrieve data from Angel One API"}, status=response.status_code)

            data = response.json()
            if not data:
                return Response({"error": "No data received from API"}, status=404)

            expiry_dates = []
            with open(self.CSV_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['token', 'symbol', 'name', 'exch_seg', 'expiry', 'instrumenttype'])

                for entry in data:
                    if entry.get('exch_seg') == 'NFO':
                        expiry = entry.get('expiry', '')
                        if expiry:
                            try:
                                parsed_date = datetime.strptime(expiry, '%d%b%Y')
                                expiry_dates.append(parsed_date.strftime('%d%b%Y'))
                            except ValueError:
                                continue  
                        writer.writerow([entry.get('token', ''), entry.get('symbol', ''),
                                         entry.get('name', ''), entry.get('exch_seg', ''),
                                         expiry, entry.get('instrumenttype', '')])

            # Store update timestamp in cache (valid for 24 hours)
            cache.set("csv_last_update", datetime.now().strftime("%Y-%m-%d"), timeout=86400)  # 1 day

            unique_expiry_dates = sorted(set(expiry_dates), key=lambda x: datetime.strptime(x, '%d%b%Y'))
            filtered_expiry_dates = [expiry for expiry in unique_expiry_dates if symbol.lower() in expiry.lower()]
            logger.info(f"filtered_expiry_dates>>>>>>>>>>>>>>{filtered_expiry_dates}")
            return Response({"symbol": symbol, "expiry_dates": filtered_expiry_dates}, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
   
   
def exit_existing_buy_position_angleone(
     LivePrice, Type, day, month, year, api_key, demate_user_name, totp, angle_pass,
    usertrade,tradingsymbol, quantity, product_type, transactiontype, price, ordertype, lot_size,
    Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty, webhook_signal,
    Exchange, trade_order_status, Segment, Index_Symbol, user, strategy
):
    try:
        print("symbol...", Index_Symbol, "user>>>>", user)
        logger.info(F"new trade_symbol...{tradingsymbol} & strategy >>>>{strategy}")

        all_order_user = Tradeorderhistory.objects.filter(
            client=user, 
            Index_Symbol=Index_Symbol,
            strategy=strategy,
            transaction_type="BUY",
            # order_status="rejected"
        ).last()
        print("all_order_user>>>",all_order_user)
        try:
            open_buy_order = Tradeorderhistory.objects.filter(
                client=user, 
                Index_Symbol=Index_Symbol,
                transaction_type="BUY",
                strategy=strategy,
                order_id__gt=0,
                order_status__in=["rejected", "completed", "complete", "open"]
            ).last()
            print("Exact Order Found angle one :", open_buy_order)
        except Tradeorderhistory.DoesNotExist:
            logger.info(f"No open BUY position found for {Index_Symbol} for user {user}.")
            return {"data": {"status": "error", "message": "No open BUY position found."}}

        order_params={}
        if open_buy_order:
            # Extract existing order details
            Entry_price = open_buy_order.Entry_Price
            Entry_type = open_buy_order.Entry_type
            EntryQty = open_buy_order.EntryQty
            oid = open_buy_order.order_id
            LivePrice=open_buy_order.LivePrice
            old_trade_symbol=open_buy_order.trading_symbol
            buy_order_close_status=open_buy_order.trade_order_status
            if buy_order_close_status=="CLOSE":
                message=f"Existing BUY order already closed for {Index_Symbol} for user {user}."
                order_id=0
                status="Failed"
                res_data=""
                logger.info(f"{message}")
                save_trade_order_history(LivePrice,transactiontype,trade_order_status,user,old_trade_symbol, order_id, status, res_data,
                    message, strategy,  Entry_type,Exit_type, Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal , 
                    Exchange, Segment,Index_Symbol, order_params,broker="Angle One")
                return {"data": {"status": "error", "message": f"Existing BUY order already closed for {old_trade_symbol} for user {user}"}}
            print("buy last order id is >>>>",oid," buy order Price>>>>",LivePrice)
            try:
                price_of_order = int(float(open_buy_order.LivePrice))  # Safe conversion
            except (ValueError, TypeError):
                price_of_order = 0  # Default to 0 if conversion fails

            print("price_of_order>>>", price_of_order)

            trading_symbol = f"{Index_Symbol}{day}{month}{year}{price_of_order}{Type}"
            print("new trade_symbol for sell prvious buy order >>>>", trading_symbol)

            logger.info(
                f"Previous order {oid} entry price is::::: {Entry_price}. Found open BUY order for {Index_Symbol}. "
                f"Exiting position. Order ID: {open_buy_order.order_id}"
            )
            sell_response = place_Angle_order(
                LivePrice, api_key, demate_user_name, totp, angle_pass, usertrade, trading_symbol,
                quantity, product_type, transactiontype, price, ordertype, lot_size,
                Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                webhook_signal, Exchange, trade_order_status, Segment, Index_Symbol,
                user, strategy
            )

            status_value = sell_response.get("data", {}).get("status", "")

            if status_value in ["completed", "rejected", "closed","open"]:
                trade_order = Tradeorderhistory.objects.get(order_id=oid)
                print("trade_order>>>",trade_order)
                trade_order.trade_order_status="CLOSE"
                trade_order.save()
                logger.info(f"Existing BUY position successfully exited for {trading_symbol}.")
                return sell_response
            elif status_value in ["Failed"]:
                logger.error(f"Failed to exit existing BUY position for {trading_symbol}. Response: {sell_response}")
                return {"data": {"status": "error", "message": "Failed to exit existing position."}}
            else:
                logger.error(f"Failed to exit existing BUY position for {trading_symbol}. Response: {sell_response}")
                return {"data": {"status": "error", "message": "Failed to exit existing position."}}
        
        else:
            logger.info(f"No open BUY position found for {Index_Symbol} for user {user}.")
            return {"data": {"status": "error", "message": "No open BUY position found."}}

    except Exception as e:
        logger.error(f"Error in exit_existing_buy_position_angleone: {str(e)}")
        return {"data": {"status": "error", "message": str(e)}}
