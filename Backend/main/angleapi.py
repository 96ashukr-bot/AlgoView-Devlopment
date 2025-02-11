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
from main.models import CompanySmtpDetails
from main.tasks import send_trade_email_async
logger = logging.getLogger('main')
# API_KEY = 'FNqcDPCk'#'Xp6znI3s'
# USERNAME = 'A1420760'
# Totp     = "7DFMHZE3BDRCIHMLFT4N3QVCPU"
# PASSWORD="1986"
# smart_client = SmartConnect(api_key=API_KEY)
# totp = pyotp.TOTP(Totp).now()
def place_Angle_order(api_key,demate_user_name,totp,angle_pass,token, symbol, quantity, product_type, transactiontype, 
        price, ordertype,lot_size, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal, Exchange,trade_order_status,
        Segment,Index_Symbol ,user=None, strategy=None):

    try:
        
        smtp_details=CompanySmtpDetails.objects.first()
        default_from_email=smtp_details.default_from_email if smtp_details else None
        logger.info(f"Angle one api order placement for user: {user} & trading symbol is: {symbol}")
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
            "tradingsymbol": symbol,
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
        lot_size = get_lot_size(symbol)  # Implement this function to fetch lot size
        lot = int(lot_size.get("lot_size", 0))  # Convert lot_size to an integer (default to 0 if not found)
        # Check if the order quantity is a multiple of the lot size
        order_id=0
        status="Failed"
        res_data="unknown response",
        if order_params['quantity'] % lot != 0:
            logger.error(f"Invalid quantity {symbol}, it should be in multiples of lot size: {lot}")
            message=f"Invalid quantity {symbol}, it should be in multiples of lot size: {lot}"
            save_trade_order_history(trade_order_status,user,symbol, order_id, status, res_data, message,  strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol , order_params,broker="Angle One")

            return {"data": {"status": "error", "message": f"Quantity must be a multiple of lot size: {lot}"}}

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
                    save_trade_order_history(
                        trade_order_status, user, symbol, order_id, status, res_data, message,
                        strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                        webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="Angle One"
                    )
                    return {"data": {"status": "Failed", "message": error_message}}
            except Exception as e:
                # Handle exceptions during the entire process
                logger.error("An error occurred: %s", e)
                res_data = "An exception occurred during login."
                message = str(e)
                save_trade_order_history(
                    trade_order_status, user, symbol, order_id, status, res_data, message,
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
                message=f"somthing wrong or token is invalid"
                res_data="None response from API"
                save_trade_order_history(trade_order_status,user,symbol, order_id, status, res_data, message,  strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol , order_params,broker="Angle One")
                return {"data": {"status": "faild", "message": message}}

            uniqueorderid = response.get('data', {}).get('uniqueorderid', None)
            if not uniqueorderid:
                logger.error(f"Order response does not contain valid uniqueorderid: {response}")
                return {"data": {"status": "error", "message": "Failed to retrieve order ID."}}

            responsedetails = smartApi.individual_order_details(uniqueorderid)
            # print("responsedetails>>>",responsedetails)
            if responsedetails is None:
                logger.error("No details found for the order.")
                return {"data": {"status": "error", "message": "Failed to retrieve order details."}}

            status = responsedetails['data'].get('status', 'unknown')
            order_id = responsedetails['data'].get('orderid', 'unknown')
            message = responsedetails['data'].get('text', 'No message provided')

            res_data=responsedetails 
            if responsedetails['data']['status'] =="completed":
                trasaction_type=responsedetails['data'].get('transactiontype', '')
                if trasaction_type == "BUY":
                    Entry_type="LE"
                    Entry_price=responsedetails['data'].get('averageprice', 0.0)
                    EntryQty=responsedetails['data'].get('quantity', 0)
                elif trasaction_type == "SELL": 
                    Exit_type="LX"
                    Exit_price=responsedetails['data'].get('averageprice', 0.0) 
                    ExitQty= responsedetails['data'].get('quantity', 0)#disclosedquantity
                order_id=responsedetails['data']['orderid']
                logger.info(f"Order placed successfully for user {user}. Order ID: {order_id}")
                # log_order(order_data, "orders_placed.csv")  
                message = responsedetails['data'].get('text', 'completed successfully ')
                status=responsedetails['data'].get('status', 'completed')
                save_trade_order_history(trade_order_status,user,symbol, order_id, status, res_data, message,   strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="Angle One")
                # from_email = default_from_email,
                # send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                # save_webhook_signals_logs(order_params['transactiontype'], symbol, price, strategy, user, status=responsedetails['data'].get('status'),failure_reason="your order place succesfully", json=json)
                response = {"data": {"status": status}}
                return response
            
            elif responsedetails['data']['status'] == "open":
                order_id=responsedetails['data']['orderid']     
                logger.info(f"Order is pending state, Order ID: {order_id}")
                # log_order(order_data, "orders_placed.csv")  
                # send massage email aleart to client your order is trade 
                from_email = default_from_email,
                # Send rejection email
                message = responsedetails['data'].get('text', 'Unknown  reason')
                status=responsedetails['data'].get('status', 'pending')
                print("user.firstName>>>>>",user.firstName)
                send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                logger.info(f"Order is pending or in process reason is !!!::{message}")
                save_trade_order_history(trade_order_status,user,symbol, order_id, status, res_data, message,  strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol ,order_params, broker="Angle One")
                response = {"data": {"status": status}}
                return response
                
            else:
                rejection_message = responsedetails['data'].get('text', 'Unknown rejection reason')
                status=responsedetails['data'].get('status', 'rejected')
                order_id=responsedetails['data']['orderid']     
                logger.info(f"Order Rejected reason!!!::{rejection_message} Order ID: {order_id}")
                from_email = default_from_email,
                # Send rejection email
                print("user.firstName>>>>>",user.firstName)
                send_trade_email_async.delay(user.email, from_email,user.firstName,status, rejection_message)
                save_trade_order_history(trade_order_status,user,symbol, order_id, status, res_data, rejection_message,  strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol ,order_params ,broker="Angle One")
                # save_webhook_signals_logs(order_params['transactiontype'], symbol, price, strategy, user, status=responsedetails['data'].get('status'),
                response = {"data": {"status": status}}
                return response
        except Exception as e:
            logging.error(f"Order could not be placed  !!!!!!!!!!!{e}")
            # logging.error("Error while placing order on attempt %d/%d: %s", attempt + 1, max_retries, e)
            sleep(1)
            response = {"data": {"status": e}}
            return response
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return  e

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

def get_token_details(trading_symbol):
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  
        data = response.json() 
        for item in data:
            if item.get("symbol") == trading_symbol:
                # Return the token and any other details
                return {
                    "status": "success", 
                    "token": item.get("token"),
                    "symbol": item.get("symbol"),
                    "expiry": item.get("expiry"),              
                }
        return {"status": "error",  # Indicate that the symbol was not found
            "message": f"No details found for trading symbol: {trading_symbol}"}
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching data: {str(e)}") 
        return {"status": "error", "message": f"An error occurred while fetching data:  {str(e)}"}
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
class SymbolExpiryDateListView(APIView):
    CSV_FILE = "ANGLE_NFO.csv"
    def get(self, request, *args, **kwargs):
        symbol = request.query_params.get('symbol', None)
        if not symbol:
            return Response({"error": "Symbol parameter is required"}, status=400)

        # Check last update timestamp from cache (store it once per day)
        last_update = cache.get("csv_last_update")

        if last_update:
            last_update_date = datetime.strptime(last_update, "%Y-%m-%d").date()
        else:
            last_update_date = None

        today_date = datetime.now().date()

        # If the file is updated today, use it
        if last_update_date == today_date and os.path.exists(self.CSV_FILE):
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

            return Response({"symbol": symbol, "expiry_dates": filtered_expiry_dates}, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
    # def get(self, request, *args, **kwargs):
    #     # Extract symbol from query parameters
    #     symbol = request.query_params.get('symbol', None)
    #     if not symbol:
    #         return Response({"error": "Symbol parameter is required"}, status=400)

    #     # Path to the CSV file where all symbols' data is stored
    #     csv_file = "ANGLE_NFO.csv"
        
    #     # Check if the CSV file exists and if it's updated within the last month
    #     if os.path.exists(csv_file):
    #         file_mod_time = os.path.getmtime(csv_file)
    #         file_mod_date = datetime.fromtimestamp(file_mod_time)
    #         if file_mod_date.date() == datetime.now().date():
    #             # The file was updated today, use the cached file
    #             return self.get_expiry_dates_from_csv(csv_file, symbol)
        
    #         # if file_mod_date > datetime.now() - timedelta(days=30):
    #         #     # The file was updated within the last 30 days, use the cached file
    #         #     return self.get_expiry_dates_from_csv(csv_file, symbol)
        
    #     # If the file is outdated or doesn't exist, fetch fresh data
    #     return self.update_csv_and_get_expiry_dates(symbol, csv_file)

    # def get_expiry_dates_from_csv(self, csv_file, symbol):
    #     # Read expiry dates from the existing CSV file
    #     try:
    #         data = pd.read_csv(csv_file)
    #         filtered_data = data[data['name'].str.upper() == symbol.upper()]
    #         expiry_dates = sorted(set(filtered_data['expiry'].unique()), key=lambda x: datetime.strptime(x, '%d%b%Y'))
    #         current_date = datetime.now()
    #         # Filter out past expiry dates
    #         expiry_dates = [
    #             datetime.strptime(date, '%d%b%Y').strftime('%d%b%Y') 
    #             for date in expiry_dates 
    #             if datetime.strptime(date, '%d%b%Y') >= current_date
    #         ]   
    #         return Response({"symbol": symbol, "expiry_dates": expiry_dates}, status=200)
    #     except Exception as e:
    #         return Response({"error": f"Error reading CSV: {str(e)}"}, status=500)

    # def update_csv_and_get_expiry_dates(self, symbol, csv_file):
    #     try:
    #         # Fetch data from Angel One Smart API
    #         url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    #         headers = {
    #             "API_KEY": "API_KEY",
    #             "USERNAME": "USERNAME",
    #             "PASSWORD": "PASSWORD",
    #             "Totp": "Totp"
    #         }
            
    #         response = requests.get(url, headers=headers)
    #         if response.status_code != 200:
    #             return Response({"error": "Failed to retrieve data from Angel One API"}, status=response.status_code)

    #         # Parse response data
    #         data = response.json()
    #         if not data:
    #             return Response({"error": "No data received from API"}, status=404)
    #             # Filter and write to the CSV file
    #         expiry_dates = []
    #         with open(csv_file, mode='w', newline='') as file:
    #             writer = csv.writer(file)
    #             writer.writerow(['token', 'symbol', 'name', 'exch_seg', 'expiry', 'instrumenttype'])

    #             for entry in data:
    #                 if entry.get('exch_seg') == 'NFO':  # Filter only NFO segments
    #                     expiry = entry.get('expiry', '')
    #                     if expiry:
    #                         try:
    #                             # Parse the expiry date using the correct format
    #                             parsed_date = datetime.strptime(expiry, '%d%b%Y')
    #                             expiry_dates.append(parsed_date.strftime('%d%b%Y'))  # Format to a readable format
    #                         except ValueError:
    #                             continue  # Skip invalid date formats
    #                     writer.writerow([entry.get('token', ''), entry.get('symbol', ''),
    #                                      entry.get('name', ''), entry.get('exch_seg', ''),
    #                                      expiry, entry.get('instrumenttype', '')])

    #         unique_expiry_dates = sorted(set(expiry_dates), key=lambda x: datetime.strptime(x, '%d%b%Y'))
    #         filtered_expiry_dates = [expiry for expiry in unique_expiry_dates if symbol.lower() in expiry.lower()]
            
    #         return Response({"symbol": symbol, "expiry_dates": filtered_expiry_dates}, status=200)

    #     except Exception as e:
    #         return Response({"error": str(e)}, status=500)




