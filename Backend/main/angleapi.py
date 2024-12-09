import json
import os
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
from main.tasks import send_trade_email_async
logger = logging.getLogger('main')
API_KEY = 'FNqcDPCk'#'Xp6znI3s'
USERNAME = 'A1420760'
Totp     = "7DFMHZE3BDRCIHMLFT4N3QVCPU"
PASSWORD="1986"
smart_client = SmartConnect(api_key=API_KEY)
totp = pyotp.TOTP(Totp).now()

def generate_session_with_retry(username, password, totp, retries=3, delay=1):
    for attempt in range(retries):
        try:
            return smart_client.generateSession(username, password, totp)
        except smart_client.smartExceptions.DataException as e:
            if "exceeding access rate" in str(e):
                print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                raise
    raise Exception("Max retries reached. Could not generate session.")

# Attempt to generate session
data = generate_session_with_retry(USERNAME, PASSWORD, totp)
feedToken = smart_client.getfeedToken()
# api_key,demate_user_name,totp,angle_pass,
#place order using Angle one api
def place_Angle_order(token, symbol, exch_seg, quantity, product_type, transactiontype, price, ordertype, expiry,lot_size, user=None, strategy=None):
    try:
        logger.info(f"Angle one api order placement for user: {user} & trading symbol is: {symbol}")
        if product_type:
            if product_type.upper() =="NRML":
               product_type= "CARRYFORWARD"
            elif product_type.upper() =="MIS":
                product_type="INTRADAY"
            elif product_type.upper() =="CNC":      
                product_type ="DELIVERY"
        if ordertype=="LIMIT":
            order_params = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": transactiontype,
                "exchange": exch_seg,
                "ordertype": ordertype,
                "producttype": product_type,
                "duration": "DAY",
                # "price": price,
                "squareoff": "0",
                "triggerprice": "0",
                "stoploss": "0",
                "lotsize": lot_size,
                "quantity": quantity,
            }
        if ordertype=="MARKET":
              order_params = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": transactiontype,
                "exchange": exch_seg,
                "ordertype": ordertype,
                "producttype": product_type,
                "duration": "DAY",
                "squareoff": "0",
                "triggerprice": "0",
                "stoploss": "0",
                "lotsize": lot_size,
                "quantity": quantity,
            }
                
        print("order_params...........",order_params)

        # logging.info("Sending Order Request: %s", json.dumps(order_params, indent=4))
        
        # max_retries = 3
        # for attempt in range(max_retries):
        try:
            print("client typee", smart_client)
            response = smart_client.placeOrderFullResponse(order_params)
            logger.info("Raw API Response: %s", response)
            resuniqueId= response['data']['uniqueorderid']
            responsedetails= smart_client.individual_order_details(resuniqueId)
            print("Order Details: ::::::", json.dumps(responsedetails,indent=4))
            status=responsedetails['data']['status'] 
            responsedetails['data'].get('status', 'complete')
            order_id=responsedetails['data']['orderid'] 
            res_data=responsedetails 
            if responsedetails['data']['status'] =="complete":
                order_data = {
                    "order_id": "data",
                    "status": "Success",
                }
                logger.info(f"Order Placed Successfully, Order ID: {response.get('data', 'Unknown')}")
                # log_order(order_data, "orders_placed.csv")  
                message = responsedetails['data'].get('text', 'completed successfully ')

                save_trade_order_history(user,symbol, order_id, status, res_data, message, order_params,broker="Angle One")
                # from_email = settings.DEFAULT_FROM_EMAIL,
                # send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                # save_webhook_signals_logs(order_params['transactiontype'], symbol, price, strategy, user, status=responsedetails['data'].get('status'),failure_reason="your order place succesfully", json=json)
                return responsedetails
            elif responsedetails['data']['status'] == "open":
                     
                logger.info(f"Order is pending stete, Order ID: {response.get('data', 'Unknown')}")
                # log_order(order_data, "orders_placed.csv")  
                # send massage email aleart to client your order is trade 
                from_email = settings.DEFAULT_FROM_EMAIL,
                # Send rejection email
                message = responsedetails['data'].get('text', 'Unknown  reason')
                responsedetails['data'].get('status', 'pending')
                print("user.firstName>>>>>",user.firstName)
                send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                logger.info(f"Order is pending or in process reason is !!!::{message}")
                save_trade_order_history(user,symbol, order_id, status, res_data, message,order_params, broker="Angle One")
                return responsedetails
                
            else:
                rejection_message = responsedetails['data'].get('text', 'Unknown rejection reason')
                responsedetails['data'].get('status', 'rejected')
                logger.info(f"Order Rejected reason!!!::{rejection_message}")
                from_email = settings.DEFAULT_FROM_EMAIL,
                # Send rejection email
                print("user.firstName>>>>>",user.firstName)
                send_trade_email_async.delay(user.email, from_email,user.firstName,status, rejection_message)
                save_trade_order_history(user,symbol, order_id, status, res_data, rejection_message,order_params ,broker="Angle One")
                # save_webhook_signals_logs(order_params['transactiontype'], symbol, price, strategy, user, status=responsedetails['data'].get('status'),
                return responsedetails
        except Exception as e:
            logging.error(f"Order could not be placed  !!!!!!!!!!!{e}")
            # logging.error("Error while placing order on attempt %d/%d: %s", attempt + 1, max_retries, e)
            sleep(1)
            return e
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return  e

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
                    "token": item.get("token"),
                    "symbol": item.get("symbol"),
                    "expiry": item.get("expiry"),              
                }
        return f"No details found for trading symbol: {trading_symbol}"
    except requests.exceptions.RequestException as e:
        return f"An error occurred while fetching data: {str(e)}"

