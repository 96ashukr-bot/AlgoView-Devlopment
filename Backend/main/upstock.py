
import requests
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from main.Alice_Blue_Api import save_trade_order_history
from main.models import ClientBrokerdetails
# from django.urls import reverse
import logging
logger = logging.getLogger('main')
import gzip
import json
from io import BytesIO
from django.http import JsonResponse
from datetime import datetime
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# # Constants (You can keep these in settings.py for better management)
# CLIENT_ID = 'your_client_id'  # Replace with your Upstox Client ID
# CLIENT_SECRET = 'your_api_secret'  # Replace with your Upstox API Secret
# REDIRECT_URI = 'https://yourdomain.com/callback'  # Make sure it matches the registered redirect URI
AUTHORIZATION_URL = 'https://login.upstox.com/login/v2/oauth/authorize'

#UPSTOX
CLIENT_KEY = '5fc50c51-44a3-43bc-98d5-8258e3ddfea1'  
CLIENT_SECRET = 'ajpiqe2sgh' 
REDIRECT_URI = 'https://software.alcrafttechnology.com/login' 
TOKEN_URL = 'https://api.upstox.com/v2/login/authorization/token'
AUTH_URL = "https://api.upstox.com/v2/login/authorization/dialog"

# Base URL for Upstox API
BASE_URL = "https://api.upstox.com"
PLACE__ORDER_URL="https://api-hft.upstox.com/v2/order/place"

def get_upstox_login_url(request):
    try:
        # Add a broker identifier in the state
        state = "upstox" 
        # The lowercase field (tradingsymbol) is deprecated and will be removed in future versions. Use the snake_case versions for consistency.
        # trading_symbol
        login_url = (
            f"{AUTH_URL}?client_id={CLIENT_KEY}&"
            f"redirect_uri={REDIRECT_URI}&"
            f"response_type=Auth_code&"
            f"state={state}"
        )
        # state = "alice_blue"
        # app_code =""# broker_details.broker_API_UID  # Replace with the Alice Blue App Code
        # redirect_uri = "https://software.algosparks.co.in/#/login"  # Your callback URL
        # login_url = (
        #     f"https://ant.aliceblueonline.com/oauth2/auth?client_id={app_code}&"
        #     f"redirect_uri={redirect_uri}&response_type=code&state={state}"
        # )
        return redirect(login_url)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def callback_upstox(request):
    try:
        auth_code ="qhssBZ"
        if not auth_code:
            return JsonResponse({"error": "Authorization code not provided"}, status=400)
        
        data = {
                'code': auth_code,
                'client_id': CLIENT_KEY,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': REDIRECT_URI,
                'grant_type': 'authorization_code'
            }

        # Send POST request to get the access token
        response = requests.post(TOKEN_URL, data=data)

        # Check the response status and print the access token
        if response.status_code == 200:
            print("Access Token Response:", response.json())
            access_token = response.json().get('access_token')
            return JsonResponse({"access_token": access_token}, status=200)
        else:
            return JsonResponse({"error": response.json()}, status=response.status_code)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def place_upstox_orders(
    access_token, trade_symbol, transaction_type, symbol, quantity, strategy, ordertype,
    product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price, EntryQty,ExitQty,webhook_signal, Exchange,
    Segment, Index_Symbol, triggerPrice,trade_order_status):
    try:
        # Fetch instrument details
        result = fetch_instrument_details(trade_symbol, "NSE")
        status="Failed"
        order_id=0
        message=""
        instrument_key = result.get("instrument_key")
        if not instrument_key:
            logger.error(f"Instrument details not found for {trade_symbol}. Response: {result}")
            status="Failed"
            message="Instrument details not found"
            res_data=result
            save_trade_order_history(trade_order_status,user,symbol, order_id, status, res_data, message,  
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
            webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="upstox")
            return {
                "data": {
                    "status": "error", "message": "Instrument details not found.",  "error_details": result,}
                }
        logger.info(f"Fetched Instrument Key: {instrument_key}")

        # Map product types to API-compatible values
        product_mapping = {"NRML": "N", "MIS": "I", "CNC": "D"}
        product_code = product_mapping.get(product_type.upper(), product_type)
        # Construct the order payload
        order_params = {
            "quantity": quantity,
            "product": product_code,
            "price": price if ordertype.upper() == "LIMIT" else 0,
            "instrument_token": instrument_key,
            "order_type": ordertype.upper(),
            "transaction_type": transaction_type.upper(),
            'validity': 'DAY',  # Order validity (DAY)
            # 'disclosed_quantity': 0,  # Not disclosing partial quantity
            'trigger_price': 0,  # Not required for market orders
            # 'is_amo': False  # Not an After Market Order
        }
        
        headers = {"Authorization": f"Bearer {access_token}"}
        print("order_params>>>>>>>",order_params)
        # Place the order
        response = requests.post(PLACE__ORDER_URL, headers=headers, json=order_params)
        response_data = response.json()

        logger.info(f"Order API response: {response_data} status code ::{response.status_code}")

        # Handle response based on status
        if response.status_code == 200 and response_data.get("status") == "success":
            order_id = response_data["data"]["order_id"]
            logger.info(f"Order placed successfully get the Order details for Order ID: {order_id}")
            return handle_successful_order(
                order_id, user, trade_symbol, strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal,
                Exchange, Segment, Index_Symbol, order_params, access_token,trade_order_status
            )
        elif response.status_code == 401:
            logger.error(f"Unauthorized access for user {user}. Reason: {response_data.get('message', 'Unknown')}")
            status= "Unauthorized"
            message="Unauthorized access"
            res_data=response
            save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message,  
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
            webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="upstox")
            return {
                "data": {  "status": "Unauthorized", "message": "Unauthorized access. Please check your token."}
            }
        elif response.status_code == 404:
            res_data=response_data.get('errors', 'Unknown')
            logger.error(f"Resource not Found. Reason: {res_data}")
            status= "errors"
            message="Resource not Found 404"
            save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
            webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="upstox")
            return { "data": {"status": "error","message":res_data}}
               
        else:
            logger.error(f"Order placement Failed. Response: {response_data}")
            status="error"
            message="Order placement Failed"
            res_data=response_data
            save_trade_order_history(trade_order_status,user,symbol, order_id, status, res_data, message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
            webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="upstox")          
            return {"data": { "status": "Failed", "message": "Order placement Failed.",  "error_details": response_data}}
    except Exception as e:
        logger.exception(f"Unexpected error while placing order for {symbol}: {str(e)}")
        return {
            "data": { "status": "error","message": "Unexpected error occurred.","error_details": str(e)}
            }
def handle_successful_order(
    order_id, user, trade_symbol, strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal, Exchange,
    Segment, Index_Symbol, order_params, access_token,trade_order_status):
    try:
        order_details = get_order_details(order_id, access_token)
        res_data=order_details
        order_id=order_details['data']['order_id']
        if order_details['data']['status'] =="complete":
            trasaction_type=order_details['data'].get('transaction_type', '')
            if trasaction_type == "BUY":
                Entry_type="LE"
                Entry_price=order_details['data'].get('average_price', 0.0)
                EntryQty=order_details['data'].get('quantity', 0)
            elif trasaction_type == "SELL": 
                Exit_type="LX"
                Exit_price=order_details['data'].get('average_price', 0.0) 
                ExitQty= order_details['data'].get('quantity', 0)#disclosedquantity
            logger.info(f"Order Placed Successfully, Order ID:{order_id}")
            # log_order(order_data, "orders_placed.csv")  
            message = order_details['data'].get('status_message', 'completed successfully ')
            res_data=order_details
            trade_order_status="success"
            status=order_details['data']['status'] 
            save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message,  
                                     strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
                                     webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="upstox")
            response={"data": {"status": "completed","message": "Order placed and details saved successfully."}}
            # from_email = settings.DEFAULT_FROM_EMAIL,
            # send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
            # save_webhook_signals_logs(order_params['transactiontype'], symbol, price, strategy, user, status=order_details['data'].get('status'),failure_reason="your order place succesfully", json=json)
            return response
        elif order_details['data']['status'] == "rejected":
            rejection_message= order_details['data'].get('status_message', 'Unknown rejection reason')
            status=order_details['data'].get('status', 'rejected')
            save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
            Segment,Index_Symbol ,order_params , broker="Upstox")
            logger.info(f"Order Rejected reason!!!::{rejection_message} Order ID: {order_id}")
            # from_email = settings.DEFAULT_FROM_EMAIL,
            # Send rejection email
            # print("user.firstName>>>>>",user.firstName)
            # send_trade_email_async.delay(user.email, from_email,user.firstName,status, rejection_message)
            # save_webhook_signals_logs(order_params['transactiontype'], symbol, price, strategy, user, status=responsedetails['data'].get('status'),
            response = {"data": {"status": status,"message": "Order is rejected "}}
            return response
        else:
            status=order_details['data']['status']
            rejection_message= order_details['data'].get('status_message', 'Unknown rejection reason')
            logger.warning(f"Failed to fetch order details for Order ID {order_id}")
            save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
            Segment,Index_Symbol ,order_params , broker="Upstox")
            return {"data": {"status": "Failed","message": "Order placed but details could not be fetched."}}
                           
    except Exception as e:
        logger.exception(f"Error while fetching order details for Order ID {order_id}: {str(e)}")
        return {
            "data": {
                "status": "error",
                "message": "Error while fetching order details.",
                "error_details": str(e),
            }
        }

def fetch_instrument_details(symbol_name, exchange="NSE"):
    try:
        # URL of the gzipped JSON containing instruments data
        url = f"https://assets.upstox.com/market-quote/instruments/exchange/{exchange}.json.gz"

        response = requests.get(url)
        
        if response.status_code != 200:
            return {"error": f"Failed to fetch instruments data. Status code: {response.status_code}"}

        with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
            instruments_data = json.load(f)
        for instrument in instruments_data:
            if instrument.get("trading_symbol", "").replace(" ", "") == symbol_name:
                return {"instrument_key": instrument.get("instrument_key")}
        return {"error": f"No instruments found for symbol {symbol_name} on exchange {exchange}."}
    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}

def get_order_details(order_id, access_token):
    try:
        if order_id:
            url = f"https://api.upstox.com/v2/order/details?order_id={order_id}"
            
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            response = requests.get(url, headers=headers)
            try:
                response_dict = response.json()  # Use response.json() instead of json.loads(response)
                print("Response of order details>>", response_dict)
                return response_dict
            except json.JSONDecodeError:
                print("Error: Failed to parse the order details response as JSON.")
                return {
                "error": f"Failed to fetch order details. Status code: {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}

