
import requests
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from django.http import HttpResponse, HttpResponseRedirect

from main.Alice_Blue_Api import save_trade_order_history
from main.models import ClientBrokerdetails
# from django.urls import reverse

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

import logging
logger = logging.getLogger('main')
import requests
import gzip
import json
from io import BytesIO
def get_upstox_login_url(request):
    try:
        # Construct the login URL
        login_url = (
            f"{AUTH_URL}?client_id={CLIENT_KEY}&"
            f"redirect_uri={REDIRECT_URI}&"
            f"response_type=Auth_code"
        )
        
        # Redirect to the Upstox login URL
        return redirect(login_url)
    
    except Exception as e:
        # Handle exceptions and return an error response
        return JsonResponse({"error": str(e)}, status=500)
def callback_upstox(request):
    try:
        auth_code ="dUL2OU"
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

import requests
import requests
from django.http import JsonResponse
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import logging
import requests

# Initialize logger
logger = logging.getLogger(__name__)
def place_upstox_orders(
    access_token, trade_symbol, transaction_type, symbol, quantity, strategy, ordertype,
    product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price, webhook_signal, Exchange,
    Segment, Index_Symbol, triggerPrice
):
    try:
        # Fetch instrument details
        result = fetch_instrument_details(trade_symbol, "NSE")
        instrument_key = result.get("instrument_key")
        if not instrument_key:
            logger.error(f"Instrument details not found for {trade_symbol}. Response: {result}")
            save_trade_order_history(
                user, symbol, 0, "error", result, "Instrument details not found",
                strategy, Entry_type, Exit_type,Entry_price,Exit_price, webhook_signal, Exchange, Segment,
                Index_Symbol, None, broker="Upstox"
            )
            return {
                "data": {
                    "status": "error",
                    "message": "Instrument details not found.",
                    "error_details": result,
                }
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
        }

        # Define API endpoint and headers
        order_url = f"{BASE_URL}/orders/place"
        headers = {"Authorization": f"Bearer {access_token}"}

        # Place the order
        response = requests.post(order_url, headers=headers, json=order_params)
        response_data = response.json()

        logger.info(f"Order API response: {response_data} status code ::{response.status_code}")

        # Handle response based on status
        if response.status_code == 200 and response_data.get("status") == "success":
            order_id = response_data["data"]["order_id"]
            logger.info(f"Order placed successfully. Order ID: {order_id}")
            return handle_successful_order(
                order_id, user, symbol, strategy, Entry_type, Exit_type,Entry_price,Exit_price, webhook_signal,
                Exchange, Segment, Index_Symbol, order_params, access_token
            )
        elif response.status_code == 401:
            logger.error(f"Unauthorized access for user {user}. Reason: {response_data.get('message', 'Unknown')}")
            save_trade_order_history(
                user, symbol, 0, "Unauthorized", response_data, "Unauthorized access",
                strategy, Entry_type, Exit_type,Entry_price,Exit_price, webhook_signal, Exchange, Segment,
                Index_Symbol, order_params, broker="Upstox"
            )
            return {
                "data": {
                    "status": "Unauthorized",
                    "message": "Unauthorized access. Please check your token.",
                }
            }
        elif response.status_code == 404:
            resp=response_data.get('errors', 'Unknown')
            logger.error(f"Resource not Found. Reason: {resp}")
            save_trade_order_history(
                user, symbol, 0, "errors", response_data, "Resource not Found",
                strategy, Entry_type, Exit_type,Entry_price,Exit_price, webhook_signal, Exchange, Segment,
                Index_Symbol, order_params, broker="Upstox"
            )
            return {
                "data": {
                    "status": "error",
                    "message":resp,
                }
            }
        else:
            logger.error(f"Order placement failed. Response: {response_data}")
            save_trade_order_history(
                user, symbol, 0, "error", response_data, "Order placement failed",
                strategy, Entry_type, Exit_type,Entry_price,Exit_price, webhook_signal, Exchange, Segment,
                Index_Symbol, order_params, broker="Upstox"
            )
            return {
                "data": {
                    "status": "error",
                    "message": "Order placement failed.",
                    "error_details": response_data,
                }
            }
    except Exception as e:
        logger.exception(f"Unexpected error while placing order for {symbol}: {str(e)}")
        return {
            "data": {
                "status": "error",
                "message": "Unexpected error occurred.",
                "error_details": str(e),
            }
        }
def handle_successful_order(
    order_id, user, symbol, strategy, Entry_type, Exit_type,Entry_price,Exit_price, webhook_signal, Exchange,
    Segment, Index_Symbol, order_params, access_token
):
    try:
        order_details = get_order_details(order_id, access_token)
        if order_details.get("status") == "success":
            logger.info(f"Order details fetched successfully for Order ID: {order_id}")
            save_trade_order_history(
                user, symbol, order_id, "complete", order_details, "Order executed successfully",
                strategy, Entry_type, Exit_type,Entry_price,Exit_price, webhook_signal, Exchange, Segment,
                Index_Symbol, order_params, broker="Upstox"
            )
            return {
                "data": {
                    "status": "complete",
                    "message": "Order placed and details saved successfully.",
                    "order_details": order_details,
                }
            }
        else:
            logger.warning(f"Failed to fetch order details for Order ID {order_id}")
            save_trade_order_history(
                user, symbol, order_id, "error", order_details, "Failed to fetch order details",
                strategy, Entry_type, Exit_type,Entry_price,Exit_price, webhook_signal, Exchange, Segment,
                Index_Symbol, order_params, broker="Upstox"
            )
            return {
                "data": {
                    "status": "error",
                    "message": "Order placed but details could not be fetched.",
                    "error_details": order_details,
                }
            }
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

        # Request the gzipped JSON data
        response = requests.get(url)
        
        # Check for successful response
        if response.status_code != 200:
            return {"error": f"Failed to fetch instruments data. Status code: {response.status_code}"}

        # Decompress the gzipped content
        with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
            instruments_data = json.load(f)

        # Search for the trading symbol
        for instrument in instruments_data:
            if instrument.get("trading_symbol", "").replace(" ", "") == symbol_name:
                return {"instrument_key": instrument.get("instrument_key")}

        # If no matching instruments found
        return {"error": f"No instruments found for symbol {symbol_name} on exchange {exchange}."}

    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}

import requests

def get_order_details(order_id, access_token):
    try:
        # Define the URL for order details
        url = f"https://api.upstox.com/v2/order/details?order_id={order_id}"
        
        # Headers with Authorization
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        # Make a GET request to fetch order details
        response = requests.get(url, headers=headers)

        # Check if the response is successful
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Failed to fetch order details. Status code: {response.status_code}",
                "details": response.text
            }
    
    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}

