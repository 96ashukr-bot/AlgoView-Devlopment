
import requests
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from main.Alice_Blue_Api import save_trade_order_history
from main.models import ClientBrokerdetails, CompanySmtpDetails
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
# REDIRECT_URI = 'https://software.alcrafttechnology.com/login' 
TOKEN_URL = 'https://api.upstox.com/v2/login/authorization/token'
AUTH_URL = "https://api.upstox.com/v2/login/authorization/dialog"
REDIRECT_URI = "https://www.admin.algoview.in/callback"
# Base URL for Upstox API
BASE_URL = "https://api.upstox.com"
PLACE__ORDER_URL="https://api-hft.upstox.com/v2/order/place"

def get_upstox_login_url(request):
    try:
        # Add a broker identifier in the state
        state = "upstox" 
        print("CLIENT_KEY>>",CLIENT_KEY)
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

def place_upstox_orders(LivePrice,group_service,
    access_token, trade_symbol, transaction_type, symbol, quantity, strategy, ordertype,
    product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price, EntryQty,ExitQty,webhook_signal, Exchange,
    Segment, Index_Symbol, triggerPrice,trade_order_status, history_id):
    try:
        EntryQty=quantity
        smtp_details=CompanySmtpDetails.objects.first()
        default_from_email=smtp_details.email_host_user if smtp_details else   "no-reply@example.com" 
        logger.info(f"{user} : exchnage symbole....{trade_symbol}")
        if Exchange=="NFO":
            result = fetch_instrument_details(trade_symbol, "NSE", user)
        elif Exchange=="BSE":
            result = fetch_instrument_details(trade_symbol, "BSE", user)
        
        logger.info(f"{user} : The exchange result is : {result}")
        status="Failed"
        order_id=0
        message=""
        order_params = {
            "quantity": quantity,
            "price": price if ordertype.upper() == "LIMIT" else 0,
            "order_type": ordertype.upper(),
            "transaction_type": transaction_type.upper(),
            'validity': 'DAY',  
            'trigger_price': 0 }
        instrument_key = result.get("instrument_key")
        if not instrument_key:
            logger.error(f"{user} : Instrument details not found for {trade_symbol}. Response: {result}")
            status="Failed"
            message="Instrument details not found"
            res_data=result
            if not trade_symbol:
                trade_symbol=symbol
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
            webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="upstox", history_id=history_id)
            return {
                "data": {
                    "status": "error", "message": "Instrument details not found.",  "error_details": result,}
                }
        logger.info(f"{user} : Fetched Instrument Key: {instrument_key}")
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
        # Place the order
        logger.info(f"{user} : Place the order API is calling for the Upstox !!")
        response = requests.post(PLACE__ORDER_URL, headers=headers, json=order_params)
        response_data = response.json()

        logger.info(f"{user} : Order API response: {response_data} status code ::{response.status_code}")

        # Handle response based on status
        if response.status_code == 200 and response_data.get("status") == "success":
            order_id = response_data["data"]["order_id"]
            logger.info(f"{user} : Order placed successfully get the Order details for Order ID: {order_id}")
            return handle_successful_order(LivePrice,group_service,transaction_type,
                order_id, user, trade_symbol, strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty , webhook_signal,
                Exchange, Segment, Index_Symbol, order_params, access_token,trade_order_status, history_id
            )
        elif response.status_code == 401:
            logger.error(f"{user} : Unauthorized access for user {user}. Reason: {response_data.get('message', 'Unknown')}")
            status= "Unauthorized"
            message="Unauthorized access"
            res_data=response_data
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
            webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="upstox", history_id=history_id)
            return {
                "data": {  "status": "Unauthorized", "message": "Unauthorized access. Please check your token."}
            }
        elif response.status_code == 404:
            res_data=response_data.get('errors', 'Unknown')
            logger.error(f"{user} : Resource not Found. Reason: {res_data}")
            status= "errors"
            message="Resource not Found 404"
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
            webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="upstox", history_id=history_id)
            return { "data": {"status": "error","message":res_data}}
        elif response.status_code == 400:
            errors = response_data.get("errors", [])
            
            # Extract the first error message if available, otherwise use a default message
            if errors and isinstance(errors, list):
                message = errors[0].get("message", "Unknown error occurred")
            else:
                message = "Unknown error occurred"

            logger.error(f"{user} : Resource not Found. Reason: {message}")
            
            status = "errors"
            res_data = response_data if response_data else "Unknown error"

            save_trade_order_history(
                LivePrice, group_service,transaction_type, trade_order_status, user, trade_symbol, order_id,
                status, res_data, message, strategy, Entry_type, Exit_type, Entry_price, Exit_price,
                EntryQty, ExitQty, webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="upstox", history_id=history_id
            )

            return {"data": {"status": "error", "message": message}}
       
        else:
            logger.error(f"{user} : Order placement Failed. Response: {response_data}")
            status="error"
            message="Order placement Failed"
            res_data=response_data
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
            webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="upstox", history_id=history_id)          
            return {"data": { "status": "Failed", "message": "Order placement Failed.",  "error_details": response_data}}
    except Exception as e:
        logger.exception(f"{user} : Unexpected error while placing order for {symbol}: {str(e)}")
        return {
            "data": { "status": "error","message": "Unexpected error occurred.","error_details": str(e)}
            }

def handle_successful_order(LivePrice,group_service,transaction_type,
    order_id, user, trade_symbol, strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal, Exchange,
    Segment, Index_Symbol, order_params, access_token,trade_order_status, history_id):
    try:
        EntryQty=order_params['quantity']
        order_details = get_order_details(order_id, access_token)
        logger.info(f"after order deatis are fetched resp::{order_details}")
        # Extract order status and ID safely
        if 'data' in order_details and isinstance(order_details['data'], dict):
            order_status = order_details['data'].get('status', '').lower()
            order_id = order_details['data'].get('order_id', '')
        else:
            print("Error: 'data' key missing in API response")
            order_status = "Failed"
            # order_id = 0
            rejection_message="error while fetching order due to network issue"
            status="success"
            res_data=order_details
            if transaction_type=="BUY":
                Entry_type="LE"
                Entry_price=LivePrice
                EntryQty=order_params['quantity']
            elif transaction_type=="SELL":
                Exit_type="LX"
                Exit_price=LivePrice
                ExitQty=order_params['quantity']    
            logger.exception(f"Error while fetching order details for Order ID {order_id}:")
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
            Segment,Index_Symbol ,order_params , broker="Upstox", history_id=history_id)
            return {
                "data": {
                    "status": "error",
                    "message": "Error while fetching order details.but order is placed successfully.",
                    # "error_details": str(e),
                }
            }

        print(f"Order Status: {order_status}, Order ID: {order_id}")

        res_data=order_details
        # order_id=order_details['data']['order_id']
        # order_status = order_details['data'].get('status', '').lower()
        logger.info(f"order_status:::{order_status}")
        # order_id = order_details['data'].get('order_id', '')
        # print("order_id>>",order_id)
        if order_details['data']['status'] =="complete"or  order_details['data']['status'] =="completed" or order_details['data']['status'] =="success" or order_details['data']['status'] =="SUCCESS":
            transaction_type=order_details['data'].get('transaction_type', '')
            if transaction_type == "BUY":
                trade_order_status="OPEN"
                Entry_type="LE"
                Entry_price=order_details['data'].get('average_price', 0.0)
                EntryQty=order_details['data'].get('quantity', 0)
            elif transaction_type == "SELL": 
                trade_order_status="CLOSE"
                Exit_type="LX"
                Exit_price=order_details['data'].get('average_price', 0.0) 
                ExitQty= order_details['data'].get('quantity', 0)#disclosedquantity
            logger.info(f"Order Placed Successfully, Order ID:{order_id}")
            # log_order(order_data, "orders_placed.csv")  
            message = order_details['data'].get('status_message', 'completed successfully ')
            res_data=order_details
            
            status=order_details['data']['status'] 
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  
                                     strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,
                                     webhook_signal , Exchange, Segment,Index_Symbol ,order_params,broker="upstox", history_id=history_id)
            response={"data": {"status": "completed","message": "Order placed and details saved successfully."}}
            # from_email = default_from_email,
            # send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
            # save_webhook_signals_logs(order_params['transactiontype'], symbol, price, strategy, user, status=order_details['data'].get('status'),failure_reason="your order place succesfully", json=json)
            return response
        elif order_details['data']['status'] == "rejected":
            rejection_message= order_details['data'].get('status_message', 'Unknown rejection reason')
            status=order_details['data'].get('status', 'rejected')
            transaction_type=order_details['data'].get('transaction_type', '')
            print("transaction_type.........",transaction_type)
            if transaction_type == "BUY":
                # trade_order_status="OPEN"
                Entry_type="LE"
                Entry_price=order_details['data'].get('average_price', 0.0)
                print("Entry_price>>>",Entry_price)
                EntryQty=order_details['data'].get('quantity', 0)
            elif transaction_type == "SELL": 
                # trade_order_status="CLOSE"
                Exit_type="LX"
                Exit_price=order_details['data'].get('average_price', 0.0) 
                ExitQty= order_details['data'].get('quantity', 0)#disclosedquantity

            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
            Segment,Index_Symbol ,order_params , broker="Upstox", history_id=history_id)
            logger.info(f"Order Rejected reason!!!::{rejection_message} Order ID: {order_id}")
            # from_email = default_from_email,
            # Send rejection email
            # print("user.firstName>>>>>",user.firstName)
            # send_trade_email_async.delay(user.email, from_email,user.firstName,status, rejection_message)
            # save_webhook_signals_logs(order_params['transactiontype'], symbol, price, strategy, user, status=responsedetails['data'].get('status'),
            response = {"data": {"status": status,"message": "Order is rejected "}}
            return response
        elif order_details['data']['status'] == "open":
            logger.info(f"Upstox order is active and open in the market. for order ID: {order_id}")
            rejection_message= order_details['data'].get('status_message', 'Unknown Open reason')
            status=order_details['data'].get('status', 'open')
            transaction_type=order_details['data'].get('transaction_type', '')
            # print("transaction_type.........",transaction_type)
            if transaction_type == "BUY":
                # trade_order_status="OPEN"
                Entry_type="LE"
                Entry_price=order_details['data'].get('average_price', 0.0)
                print("Entry_price>>>",Entry_price)
                EntryQty=order_details['data'].get('quantity', 0)
            elif transaction_type == "SELL": 
                # trade_order_status="CLOSE"
                Exit_type="LX"
                Exit_price=order_details['data'].get('average_price', 0.0) 
                ExitQty= order_details['data'].get('quantity', 0)#disclosedquantity
            status="complete"
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
            Segment,Index_Symbol ,order_params , broker="Upstox", history_id=history_id)
            logger.info(f"Order  active and open in the market reason!!!::{rejection_message} Order ID: {order_id}")
            response = {"data": {"status": status,"message": "Order is Open "}}
            return response
        elif order_details['data']['status'] == "put order req received":
            logger.info(f"Upstox order is active and open in the market. for order ID: {order_id}")
            rejection_message= order_details['data'].get('status_message', 'Unknown Open reason')
            status=order_details['data'].get('status', 'put order req received')
            transaction_type=order_details['data'].get('transaction_type', '')
            # print("transaction_type.........",transaction_type)
            if transaction_type == "BUY":
                # trade_order_status="OPEN"
                Entry_type="LE"
                Entry_price=order_details['data'].get('average_price', 0.0)
                print("Entry_price>>>",Entry_price)
                EntryQty=order_details['data'].get('quantity', 0)
            elif transaction_type == "SELL": 
                # trade_order_status="CLOSE"
                Exit_type="LX"
                Exit_price=order_details['data'].get('average_price', 0.0) 
                ExitQty= order_details['data'].get('quantity', 0)#disclosedquantity

            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
            Segment,Index_Symbol ,order_params , broker="Upstox", history_id=history_id)
            logger.info(f"Order  active and open in the market reason!!!::{rejection_message} Order ID: {order_id}")
            response = {"data": {"status": status,"message": "Order is Open "}}
            return response
        else:
            
            status=order_details['data']['status']
            rejection_message= order_details['data'].get('status_message', 'Unknown rejection reason')
            logger.warning(f"Failed to fetch order details for Order ID {order_id} with status {status} broker is :upstox")
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
            strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
            Segment,Index_Symbol ,order_params , broker="Upstox", history_id=history_id)
            return {"data": {"status": "Failed","message": "Order placed but details could not be fetched."}}
                           
    except Exception as e:
        rejection_message="error while fetching order"
        status="Failed"
        res_data=str(e)
        print("trade_symbolfff>>>",trade_symbol)
        logger.exception(f"Error while fetching order details for Order ID {order_id}: {str(e)}")
        save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, rejection_message, 
        strategy, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, 
        Segment,Index_Symbol ,order_params , broker="Upstox", history_id=history_id)
        return {
            "data": {
                "status": "error",
                "message": "Error while fetching order details.",
                "error_details": str(e),
            }
        }

def fetch_instrument_details(symbol_name, exchange="NSE", user = None):
    try:
        logger.info(f"{user} : instrument details fetching for the upstox api calling !!")
        # URL of the gzipped JSON containing instruments data
        url = f"https://assets.upstox.com/market-quote/instruments/exchange/{exchange}.json.gz"

        response = requests.get(url)        
        if response.status_code != 200:
            logger.info(f"{user} : Failed to fetch instruments data. Status : {response}")
            return {"error": f"Failed to fetch instruments data. Status code: {response.status_code}"}

        with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
            instruments_data = json.load(f)
        for instrument in instruments_data:
            if instrument.get("trading_symbol", "").replace(" ", "") == symbol_name:
                logger.info(f"{user} : instrument_key is get it ?????????????========>>>>>>>")
                return {"instrument_key": instrument.get("instrument_key")}

        logger.info(f"{user} : No instruments found for symbol {symbol_name} on exchange {exchange}.")
        return {"error": f"No instruments found for symbol {symbol_name} on exchange {exchange}."}
    except Exception as e:
        logger.info(f"{user} : Exception occurred: {str(e)}")
        return {"error": f"Exception occurred: {str(e)}"}

def get_order_details(order_id, access_token):
    try:
        if not order_id:
            return {"error": "Invalid order ID"}

        url = f"https://api.upstox.com/v2/order/details?order_id={order_id}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        print(f"Making API request to: {url}")
        response = requests.get(url, headers=headers)

        logger.info(f"API Response Status Code: {response.status_code}")

        try:
            response_dict = response.json()  # Corrected JSON parsing
        except json.JSONDecodeError:
            print("Error: Failed to parse JSON response")
            return {
                "error": f"Failed to parse response. Status code: {response.status_code}",
                "details": response.text
            }

        # print("Full API Response:", json.dumps(response_dict, indent=4))  # Pretty-print JSON

        return response_dict

    except requests.RequestException as e:
        print(f"Network error: {e}")
        return {"error": "Network issue occurred", "details": str(e)}

    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"error": "Unexpected error occurred", "details": str(e)}

def get_order_details2222(order_id, access_token):
    try:
        if order_id:
            url = f"https://api.upstox.com/v2/order/details?order_id={order_id}"
            
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            response = requests.get(url, headers=headers)
            logger.info(f"response details upstox:::::{response}")
            try:
                response_dict = response.json()  # Use response.json() instead of json.loads(response)
                logger.info(f"Response of order details>>{response_dict}")
                return response_dict
            except json.JSONDecodeError:
                logger.info(f"Error: Failed to parse the order details response as JSON.")
                return {
                "error": f"Failed to fetch order details. Status code: {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        logger.info(f"Exception occurred: {str(e)}")
        return {"error":"None" }

