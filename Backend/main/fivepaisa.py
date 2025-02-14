import os
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
import requests
import pandas as pd
from io import StringIO
from main.Alice_Blue_Api import save_trade_order_history
from main.models import *
from main.tasks import send_trade_email_async
import logging
import uuid
logger = logging.getLogger('main')
PLACE_ORDER_URL = "https://Openapi.5paisa.com/VendorsAPI/Service1.svc/V1/PlaceOrderRequest"  # Example URL (change to actual API endpoint)

"""
The access token  generated after successful login request remains valid thought a day from 
the time of its generation. Token expires every day at 11:59 PM.
"""

ACCESS_TOKEN_URL = "https://Openapi.5paisa.com/VendorsAPI/Service1.svc/GetAccessToken"
AUTH_LOGIN_URL="https://dev-openapi.5paisa.com/WebVendorLogin/VLogin/Index"
# Replace with your 5Paisa credentials

REDIRECT_URL = "https://www.admin.algoview.in/callback"
STATE = "5paisa"
# Provided credentials
VENDOR_KEY = "CNh6IRx0kF8c1MSyNBPaOhcaaVmiitbm"  # Your API Key (App Key)
USER_ID = "87CUsmjf7dP"  # Your User ID
ENCRYPTION_KEY = "UFDlfZjoOsj07XipwGuFUDPAGeER61Q7"  # Your Encryption Key
def initiate_oauth_login(request):
    logger.info(f"Vendor Key: {VENDOR_KEY}")
    
    state = "5paisa"
    oauth_url = (
        f"https://dev-openapi.5paisa.com/WebVendorLogin/VLogin/Index?"
        f"VendorKey={VENDOR_KEY}&ResponseURL={REDIRECT_URL}&State={state}"
    )

    # Redirect the user to the OAuth login page
    return HttpResponseRedirect(oauth_url)

def oauth_callback(request):
    """
    Handles the callback from 5Paisa after successful login.
    """
    request_token ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6IjUxMDcyMDY3Iiwicm9sZSI6IkNOaDZJUngwa0Y4YzFNU3lOQlBhT2hjYWFWbWlpdGJtIiwiU3RhdGUiOiI1cGFpc2EiLCJuYmYiOjE3MzgxNTM1OTUsImV4cCI6MTczODE1NzE5NSwiaWF0IjoxNzM4MTUzNTk1fQ.aWHq_zv5oKF7jjMMNwaz1khlVI3Aw435Cy83eFshQaM"# request.GET.get("RequestToken")
    state = "5paisa"#request.GET.get("state")

    if not request_token:
        return JsonResponse({"error": "RequestToken is missing"}, status=400)

    # Log RequestToken and State
    # print(f"RequestToken: {request_token}")
    # print(f"State: {state}")

    # Fetch Access Token
    access_token = fetch_access_token(request_token)
    if access_token:
        return JsonResponse({"AccessToken": access_token})
    else:
        return JsonResponse({"error": "Failed to fetch AccessToken"}, status=500)
def fetch_access_token(request_token):
    payload ={
    "head": {
        "Key":VENDOR_KEY
    },
    "body": {
        "RequestToken":request_token,
        "EncryKey": ENCRYPTION_KEY,
        "UserId":USER_ID
        }
    }
    

    headers = {
        "Content-Type": "application/json"
    }

    try:
        # Make the POST request to fetch the access token
        response = requests.post(ACCESS_TOKEN_URL, json=payload, headers=headers)
        print("response.........",response.json())
        if response.status_code == 200:
            response_data = response.json()  
            if "body" in response_data and "AccessToken" in response_data["body"]:
                return response_data["body"]["AccessToken"]  # Return the access token
            else:
                print("Error in response body:", response_data)
        else:
            print(f"Error: {response.status_code}, Response: {response.text}")

    except Exception as e:
        print(f"Exception occurred: {e}")

    return None  # Return None if fetching the token failed
def fetch_access_token_5paisa(request_token,broker_details):
        api_key=broker_details.broker_API_KEY
        encreption_key=broker_details.broker_API_SKEY
        user_id=broker_details.broker_API_UID
        payload ={
        "head": {
            "Key":api_key
        },
        "body": {
            "RequestToken":request_token,
            "EncryKey": encreption_key,
            "UserId":user_id
            }
        }
        

        headers = {
            "Content-Type": "application/json"
        }

        try:
            # Make the POST request to fetch the access token
            response = requests.post(ACCESS_TOKEN_URL, json=payload, headers=headers)
            print("response.........",response.json())
            if response.status_code == 200:
                response_data = response.json()  
                if "body" in response_data and "AccessToken" in response_data["body"]:
                    return response_data["body"]["AccessToken"]  # Return the access token
                else:
                    return None
                    # print("Error in response body:", response_data)
            else:
                print(f"Error: {response.status_code}, Response: {response.text}")

        except Exception as e:
            print(f"Exception occurred: {e}")

        return None  # Return None if fetching the token failed
from datetime import datetime
def download_scrip_master(segment, save_path):
    """
    Download the Scrip Master CSV for the specified segment and save it locally.
    """
    try:
        SCRIP_MASTER_URL = f"https://Openapi.5paisa.com/VendorsAPI/Service1.svc/ScripMaster/segment/{segment}"
        response = requests.get(SCRIP_MASTER_URL)

        if response.status_code == 200 and response.text.strip():
            # Check if response contains data
            if "Exch" in response.text and "ScripCode" in response.text:
                with open(save_path, 'w') as f:
                    f.write(response.text)
                return {"status": "success", "file_path": save_path}
            else:
                return {"status": "error", "message": "CSV contains only headers or is invalid."}
        else:
            return {
                "status": "error",
                "message": f"Failed to download Scrip Master. HTTP Status: {response.status_code}",
                "details": response.text
            }
    except requests.RequestException as e:
        return {"status": "error", "message": f"Request failed: {str(e)}"}

def get_symbol_scriptcode(symbol, segment, Exch,csv_dir):
    """
    Get the ScripCode for a symbol and exchange. Download or update the CSV if necessary.
    
    :param symbol: The symbol to search for.
    :param Exch: The exchange (e.g., "N").
    :param segment: The segment for which to fetch the data.
    :param csv_dir: The directory where the CSV files are stored.
    :return: A dictionary with the status and ScripCode or an error message.
    """
    try:
        os.makedirs(csv_dir, exist_ok=True)
        # Generate the file path for the current segment
        today = datetime.today()
        csv_file_name = f"scrip_master_{segment}_{today.strftime('%Y_%m')}.csv"
        csv_file_path = os.path.join(csv_dir, csv_file_name)
        if not os.path.exists(csv_file_path):
            print("Downloading the latest Scrip Master...",csv_file_path)
            download_status = download_scrip_master(segment, csv_file_path)
            if download_status["status"] != "success":
                return download_status

        df = pd.read_csv(csv_file_path)
        df['Name'] = df['Name'].str.replace(" ", "")
        filtered_df = df[(df['Name'] == symbol) & (df['Exch'] == Exch)]

        if not filtered_df.empty:
            # Return the first matching record's ScripCode
            scrip_code = filtered_df.iloc[0]['ScripCode']
            return {"status": "success", "ScripCode": scrip_code}
        else:
            # No matching records found
            return {"status": "error", "message": "No records found matching the given symbol and exchange."}
    except Exception as e:
        return {"status": "error", "message": "An error occurred.", "details": str(e)}

def get_order_details(access_token, ClientCode, api_key, RemoteOrderID):
    url = "https://Openapi.5paisa.com/VendorsAPI/Service1.svc/V3/OrderBook"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    order_status_request = {
        "head": {
            "key": api_key
        },
        "body": {
            "ClientCode": ClientCode,
        }
    }
    try:
        response = requests.post(url, json=order_status_request, headers=headers)
        print("response...",response)
        if response.status_code == 200:
            response_data = response.json()
            order_details = response_data.get("body", {}).get("OrderBookDetail", [])
            # Filter the order with the given RemoteOrderID
            filtered_order = next((order for order in order_details if order["RemoteOrderID"] == RemoteOrderID), None)
            if filtered_order:
                logger.info(f"Order Details Found: {filtered_order}")
                return filtered_order
            else:
                logger.info(f"No order found with RemoteOrderID: {RemoteOrderID}")
                return None
        else:
            logger.error(f"Failed to fetch order status. HTTP Status: {response.status_code}, Response: {response.text}")
            return {"status": "error", "message": f"Failed to fetch order status: {response.status_code}"}
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return {"status": "error", "message": f"Request failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error while fetching order details: {e}")
        return {"status": "error", "message": "An error occurred while fetching the order details."}

# Function to convert all values to native Python types
def convert_int64_to_int(obj):
    if isinstance(obj, pd.Series):
        return obj.apply(lambda x: int(x) if isinstance(x, pd._libs.tslibs.np_datetime.Timestamp) else x)
    if isinstance(obj, dict):
        return {key: convert_int64_to_int(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [convert_int64_to_int(item) for item in obj]
    if isinstance(obj, (int, float)):
        return obj
    try:
        return int(obj)  # Try converting any number to a Python integer
    except:
        return obj  # If not, return the object as is


def place_5paisa_order(api_key,access_token,trade_symbol,transaction_type, symbol, quantity,strategy,ordertype,
        product_type, price,user, Lots,trade_order_status,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal
        ,Exchange, Segment,Index_Symbol,triggerPrice,trade):
        
        print("transaction_type>>",transaction_type,ordertype)
        
        smtp_details=CompanySmtpDetails.objects.first()
        default_from_email=smtp_details.email_host_user if smtp_details else   "no-reply@example.com" 
        segment="nse_fo"
        if Exchange=="NSE" or Exchange=="NFO":
            Exch="N"
        order_id=0
        status="Failed"
        message="Failed no reason"
        res_data="unknown response"
        order_params= {
                    "Exchange": Exch,  # NSE (National Stock Exchange)
                    "ExchangeType": "D",  # Derivatives
                    "ScripCode": 0,  # Numeric Scrip Code from token
                    "OrderType": ordertype,  # Order type (Buy or Sell)
                    "price":0,
                    "Qty": quantity,  # Quantity to trade
                    # "DisQty": 0,  # Disclosed Quantity
                    # "IsIntraday": True,  # Intraday flag
                    "AHPlaced": "N",  # After Hours order flag
                    # "RemoteOrderID": unique_id  # Unique ID for the order
                }
        csv_dir = os.path.join(os.path.dirname(__file__))
        tokendata = get_symbol_scriptcode(trade_symbol, segment, Exch,csv_dir)
        if tokendata["status"] == "success":  
            token = tokendata.get("ScripCode")
            print("scritp coddeee",token)
            # symbol = tokendata.get("Name").str.replace(" ", "")
            if not token:
                logger.error(f"Missing token or symbol for trading symbol: {trade.symbol}")
                response= {"data":{"status": "error", "message": "token symbole not found"}}
                return response# continue
        else:
            message= f"trading symbol is not found for this :{trade.symbol}"
            res_data="trading symbol token not found"
            save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data,
                                     message, strategy,  Entry_type,Exit_type, Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal , 
                                     Exchange, Segment,Index_Symbol, order_params,broker="5paisa")
                
            logger.info(f"No token data found for trading symbol: {trade.symbol}")
            response= {"data":{"status": "error", "message": "token symbole not found"}}
            return response
        try:
            # token=35021
            unique_id = str(uuid.uuid4()).replace("-", "")[:15]
            order_params = {
                "head": {
                    "key": api_key
                },
                "body": {
                    "Exchange": "N",  # NSE (National Stock Exchange)
                    "ExchangeType": "D",  # Derivatives
                    "ScripCode": token,  # Numeric Scrip Code from token
                    "OrderType": ordertype,  # Order type (Buy or Sell)
                    "price":0,
                    "Qty": quantity,  # Quantity to trade
                    # "DisQty": 0,  # Disclosed Quantity
                    "IsIntraday": True,  # Intraday flag
                    "AHPlaced": "N",  # After Hours order flag
                    "RemoteOrderID": unique_id  # Unique ID for the order
                }
            }
            # Set the Authorization header with the Bearer token
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"  # Content-Type for JSON payload
            }
            # When preparing your order_params, apply the conversion
            order_params = convert_int64_to_int(order_params)
            # Place the order via a POST request
            response = requests.post(PLACE_ORDER_URL, headers=headers, json=order_params)

            # Print the response (can be used for debugging)
            print("Response:", response)

            if  response.status_code == 200:
                response=response.json()
                print("response data of 5Paisa ::::::::",response)
                order_id=response['body']['BrokerOrderID']
                message = response.get('body', {}).get('Message', 'No message available')
                if order_id==0:
                    res_data = response
                    status="Failed"
                    response = {"data": {"status": status}}
                    print("message......",message)
                    logger.info(f"Order details for found for {user}. Order ID: : {order_id}")
                    save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price ,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="5paisa")

                    return response
                    
                ClientCode=response['body']['ClientCode']
                print("ClientCode...",ClientCode)
                RemoteOrderID=response['body']['RemoteOrderID']
                order_his=get_order_details(access_token, ClientCode, api_key, RemoteOrderID)
                print("order history  5Paisa::::::::",order_his)
                if order_his==None:
                    response = {"data": {"status": "Failed"}}
                    logger.info(f"Order details for found for {user}. Order ID: : {order_id}")
                    message=f"Order details for found for {user}. Order ID: : {order_id}"
                    save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price ,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="5paisa")

                    return response
                # Extract the status
                status = order_his.get('OrderStatus', '').lower()  # Retrieve 'Status' key, fallback to '' if not found
                res_data=order_his
                # logger.info(f"history of 5paisa order_____________{order_his}")
                logger.info(f"status. of 5Paisa.....{status}")
                if status == "Fully Executed":
                    order_id=res_data.get ('BrokerOrderId', 0)   
                    trasaction_type=res_data.get('BuySell','')
                    if trasaction_type == "B":
                        Entry_type="LE"
                        Entry_price=res_data.get ('AveragePrice', 0.0)
                        EntryQty=res_data.get ('Qty', 0)
                    elif trasaction_type == "S": 
                        Exit_type="LX"
                        Exit_price=res_data.get ('AveragePrice', 0.0)  
                        ExitQty= res_data.get ('Qty', 0)
                    status="completed"
                    response = {"data": {"status":status }}
                    logger.info(f"Order placed successfully for user {user}. Order ID: : {order_id}")
                    message=f"Order placed successfully for user {user}. Response: {response}"
                    save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price ,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="5paisa")
                    return response
                elif status == "rejected by 5p":
                    order_id=res_data.get ('BrokerOrderId', 0) 
                    from_email = default_from_email,
                    message=order_his.get('Reason', 'not any reason get').lower()
                    send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                    status="rejected"
                    response = {"data": {"status":status }}
                    logger.info(f"Order is rejected  for user {user}. Order ID: {order_id}")
                    save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="5paisa")
                elif status == "rejected by Exch":
                    order_id=res_data.get ('BrokerOrderId', 0) 
                    from_email = default_from_email,
                    message=order_his.get('Reason', 'not any reason get').lower()
                    send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                    status="rejected"
                    response = {"data": {"status":status }}
                    logger.info(f"Order is rejected  for user {user}. Order ID: {order_id}")
                    save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="5paisa")
                elif status == "pending":
                    order_id=res_data.get ('BrokerOrderId', 0) 
                    from_email = default_from_email,
                    message=order_his.get('Reason', 'not any reason get').lower()
                    send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                    status="pending"
                    response = {"data": {"status":status }}
                    logger.info(f"Order is pending  for user {user}. Order ID: {order_id}")
                    save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="5paisa")

                return response
            elif  response.status_code == 401:
                # error_message = response.get("message", "Unknown error")
                response ={"data": {"status": "Unauthorized"}}
                error_message="token is invalid"
                order_id=0
                status="Failed"
                res_data="invakid token"
                logger.error(f"Order placement Failed for user {user}. Error: {error_message}")
                message="invalid token"
                save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty  ,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker="5paisa")
                return response       
      
        except Exception as e:
            logger.exception(f"Unexpected error while placing order for user {user}: {e}")
            return {"data": {"status": "error", "message": "An unexpected error occurred"}}
