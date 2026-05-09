import os
import requests
import pandas as pd
from main.models import *
from main.tasks import send_trade_email_async
from main.broker_order_utils import normalize_order_type, resolve_limit_price
from main.trade_history_service import save_trade_order_history
from main.broker_instrument_cache import ensure_fivepaisa_scrip_master_file
import logging
import uuid
logger = logging.getLogger('main')
PLACE_ORDER_URL = "https://Openapi.5paisa.com/VendorsAPI/Service1.svc/V1/PlaceOrderRequest"  # Example URL (change to actual API endpoint)
MARKET_FEED_URL = "https://Openapi.5paisa.com/VendorsAPI/Service1.svc/MarketFeed"

"""
The access token  generated after successful login request remains valid thought a day from 
the time of its generation. Token expires every day at 11:59 PM.
"""

ACCESS_TOKEN_URL = "https://Openapi.5paisa.com/VendorsAPI/Service1.svc/GetAccessToken"
def fetch_access_token_5paisa(request_token,broker_details, proxy_config=None):
        if not proxy_config:
            logger.error("Proxy/static-IP execution route is required for 5Paisa token generation.")
            return None
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
            response = requests.post(ACCESS_TOKEN_URL, json=payload, headers=headers, timeout=10, proxies=proxy_config)
            if response.status_code == 200:
                response_data = response.json()  
                if "body" in response_data and "AccessToken" in response_data["body"]:
                    return response_data["body"]["AccessToken"]
                logger.warning("5Paisa access token response did not include AccessToken")
            else:
                logger.warning("5Paisa access token request failed with status %s", response.status_code)

        except Exception as e:
            logger.exception("5Paisa access token request failed")

        return None
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

def get_symbol_scriptcode(symbol, segment, Exch, csv_dir, user=None):
    """
    Get the ScripCode for a symbol and exchange. Download or update the CSV if necessary.
    :param symbol: The symbol to search for.
    :param Exch: The exchange (e.g., "N").
    :param segment: The segment for which to fetch the data.
    :param csv_dir: The directory where the CSV files are stored.
    :return: A dictionary with the status and ScripCode or an error message.
    """
    try:
        normalized_symbol = str(symbol or "").replace(" ", "").replace("-", "").upper()
        try:
            csv_file_path = ensure_fivepaisa_scrip_master_file(segment)
        except Exception as exc:
            return {"status": "error", "message": f"5Paisa scrip master unavailable: {str(exc)}"}

        df = pd.read_csv(csv_file_path)
        df['Name'] = df['Name'].astype(str).str.replace(" ", "").str.replace("-", "").str.upper()
        filtered_df = df[(df['Name'] == normalized_symbol) & (df['Exch'] == Exch)]

        if not filtered_df.empty:
            # Return the first matching record's ScripCode
            scrip_code = filtered_df.iloc[0]['ScripCode']
            logger.info(f"{user}: filtered_df.empty is not empty in 5 paisa !!")
            return {"status": "success", "ScripCode": scrip_code}
        else:
            # No matching records found
            logger.info(f"{user}: No records found matching the given symbol and exchange for 5 paisa ??")
            return {"status": "error", "message": "No records found matching the given symbol and exchange."}
    except Exception as e:
        logger.info(f"{user}: An error occurred for 5 paisa : {e}")
        return {"status": "error", "message": "An error occurred.", "details": str(e)}

def get_order_details(access_token, ClientCode, api_key, RemoteOrderID, user=None, proxy_config=None):
    if not proxy_config:
        return {"status": "error", "message": "Proxy/static-IP execution route is required for 5Paisa order details."}
    logger.info(f"{user} : Get Order Details Api is calling")
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
        response = requests.post(url, json=order_status_request, headers=headers, proxies=proxy_config, timeout=10)
        logger.info(f"{user} : Get Order Details Api has responed : {response}")
        if response.status_code == 200:
            response_data = response.json()
            order_details = response_data.get("body", {}).get("OrderBookDetail", [])
            filtered_order = next((order for order in order_details if order["RemoteOrderID"] == RemoteOrderID), None)
            if filtered_order:
                logger.info(f"{user} : Order Details Found: {filtered_order}")
                return filtered_order
            else:
                logger.info(f"{user} : No order found with RemoteOrderID: {RemoteOrderID}")
                return None
        else:
            logger.error(f"{user} : Failed to fetch order status. HTTP Status: {response.status_code}, Response: {response.text}")
            return {"status": "error", "message": f"Failed to fetch order status: {response.status_code}"}
    except requests.RequestException as e:
        logger.error(f"{user} : Request failed: {e}")
        return {"status": "error", "message": f"Request failed: {str(e)}"}
    except Exception as e:
        logger.error(f"{user} : Unexpected error while fetching order details: {e}")
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


def place_5paisa_order(LivePrice,group_service,api_key,access_token,trade_symbol,transaction_type, symbol, quantity,strategy,ordertype,
        product_type, price,user, Lots,trade_order_status,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal
        ,Exchange, Segment,Index_Symbol,triggerPrice,trade, history_id, proxy_config=None):
    if not proxy_config:
        return {"data": {"status": "Failed", "message": "Proxy/static-IP execution route is required for 5Paisa orders."}}

    try:
        EntryQty=quantity
        smtp_details=CompanySmtpDetails.objects.first()
        default_from_email=smtp_details.email_host_user if smtp_details else "no-reply@example.com" 
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
                    "OrderType": transaction_type,  # Order type (Buy or Sell)
                    "price":0,
                    "Qty": quantity,  # Quantity to trade
                    "AHPlaced": "N",  # After Hours order flag
                }
        csv_dir = os.path.join(os.path.dirname(__file__))
        tokendata = get_symbol_scriptcode(trade_symbol, segment, Exch,csv_dir, user)
        if tokendata["status"] == "success":  
            logger.info(f"{user} : token data status is success now !!")
            token = tokendata.get("ScripCode")
            if not token:
                logger.error(f"{user} : Missing token or symbol for trading symbol: {trade.symbol}")
                response= {"data":{"status": "error", "message": "token symbole not found"}}
                return response# continue
        else:
            message= f"{user} : trading symbol is not found for this :{trade.symbol}"
            res_data="trading symbol token not found"
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data,
                                     message, strategy,  Entry_type,Exit_type, Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal , 
                                     Exchange, Segment,Index_Symbol, order_params,broker="5paisa", history_id=history_id)
                
            logger.info(f"{user} :No token data found for trading symbol: {trade.symbol}")
            response= {"data":{"status": "error", "message": "token symbole not found"}}
            return response
        try:
            unique_id = str(uuid.uuid4()).replace("-", "")[:15]
            requested_order_type = normalize_order_type(ordertype)
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            ltp = None
            try:
                market_feed_payload = {
                    "head": {"key": api_key},
                    "body": {
                        "MarketFeedData": [
                            {"Exch": "N", "ExchType": "D", "ScripCode": token}
                        ],
                        "LastRequestTime": "/Date(0)/",
                        "RefreshRate": "H",
                    },
                }
                ltp_response = requests.post(MARKET_FEED_URL, headers=headers, json=market_feed_payload, timeout=5, proxies=proxy_config)
                ltp_data = ltp_response.json() if ltp_response.content else {}
                feed_data = ltp_data.get("body", {}).get("Data") or ltp_data.get("body", {}).get("MarketFeedData") or []
                if feed_data:
                    quote = feed_data[0]
                    ltp = quote.get("LastRate") or quote.get("LastTradedPrice") or quote.get("ltp")
            except Exception as e:
                logger.warning(f"{user} : 5Paisa LTP fetch failed for token {token}: {str(e)}")

            if requested_order_type == "LIMIT":
                price = resolve_limit_price(price, ltp, transaction_type)
                if not price:
                    message = "Unable to calculate 5Paisa limit price because live price is unavailable."
                    save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, "Failed", "LTP unavailable", message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price ,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="5paisa", history_id=history_id)
                    return {"data": {"status": "Failed", "message": message}}
            elif requested_order_type == "MARKET":
                price = 0

            order_params = {
                "head": {
                    "key": api_key
                },
                "body": {
                    "Exchange": "N",  # NSE (National Stock Exchange)
                    "ExchangeType": "D",  # Derivatives
                    "ScripCode": token,  # Numeric Scrip Code from token
                    "OrderType": transaction_type,  # Order type (Buy or Sell)
                    "price": price if requested_order_type == "LIMIT" else 0,
                    "Qty": quantity,  # Quantity to trade
                    # "DisQty": 0,  # Disclosed Quantity
                    "IsIntraday": True,  # Intraday flag
                    "AHPlaced": "N",  # After Hours order flag
                    "RemoteOrderID": unique_id  # Unique ID for the order
                }
            }
            # Set the Authorization header with the Bearer token
            # When preparing your order_params, apply the conversion
            order_params = convert_int64_to_int(order_params)
            logger.info(f"{user} :Place order api url is called for the process !!")
            response = requests.post(PLACE_ORDER_URL, headers=headers, json=order_params, proxies=proxy_config)
            logger.info(f"{user} :Place order api has responed : {response}")

            if  response.status_code == 200:
                response=response.json()
                order_id=response['body']['BrokerOrderID']
                message = response.get('body', {}).get('Message', 'No message available')
                if order_id==0:
                    res_data = response
                    status="Failed"
                    response = {"data": {"status": status}}
                    logger.info(f"{user} : Order details for found for {user}. Order ID: : {order_id}")
                    save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price ,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="5paisa", history_id=history_id)

                    return response
                    
                ClientCode=response['body']['ClientCode']
                RemoteOrderID=response['body']['RemoteOrderID']
                order_his=get_order_details(access_token, ClientCode, api_key, RemoteOrderID, user, proxy_config=proxy_config)
                if order_his==None:
                    response = {"data": {"status": "Failed"}}
                    logger.info(f"Order details for found for {user}. Order ID: : {order_id}")
                    message=f"Order details for found for {user}. Order ID: : {order_id}"
                    save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price ,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="5paisa", history_id=history_id)

                    return response
                # Extract the status
                status = order_his.get('OrderStatus', '').lower()  # Retrieve 'Status' key, fallback to '' if not found
                res_data=order_his
                logger.info(f"{user} : status. of 5Paisa.....{status}")
                if status == "Fully Executed" or status == "Partially Executed" or status == "fully executed":
                    order_id=res_data.get ('BrokerOrderId', 0)   
                    trasaction_type=res_data.get('BuySell','')
                    if trasaction_type == "B":
                        Entry_type="LE"
                        Entry_price=res_data.get ('AveragePrice', 0.0)
                        EntryQty=res_data.get ('Qty', 0)
                        trade_order_status="OPEN"
                    elif trasaction_type == "S": 
                        trade_order_status="CLOSE"
                        Exit_type="LX"
                        Exit_price=res_data.get ('AveragePrice', 0.0)  
                        ExitQty= res_data.get ('Qty', 0)
                    status="completed"
                    response = {
                        "data": {
                            "status": status,
                            "order_id": order_id,
                            "order_type": requested_order_type,
                            "price": Entry_price or Exit_price or order_params["body"].get("price"),
                            "ltp": ltp,
                            "reference_price": ltp,
                        }
                    }
                    logger.info(f"{user} : Order placed successfully for user {user}. Order ID: : {order_id}")
                    message=f"Order placed successfully for user {user}. Response: {response}"
                    save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price ,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="5paisa", history_id=history_id)
                    return response
                elif status == "rejected by 5p":
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
                    from_email = default_from_email,
                    message=order_his.get('Reason', 'not any reason get').lower()
                    send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                    status="rejected"
                    response = {"data": {"status":status }}
                    logger.info(f"Order is rejected  for user {user}. Order ID: {order_id}")
                    save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="5paisa", history_id=history_id)
                elif status == "rejected by Exch":
                    order_id=res_data.get ('BrokerOrderId', 0) 
                    from_email = default_from_email,
                    message=order_his.get('Reason', 'not any reason get').lower()
                    send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                    status="rejected"
                    response = {"data": {"status":status }}
                    logger.info(f"Order is rejected  for user {user}. Order ID: {order_id}")
                    save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="5paisa", history_id=history_id)
                elif status == "pending":
                    order_id=res_data.get ('BrokerOrderId', 0) 
                    from_email = default_from_email,
                    message=order_his.get('Reason', 'not any reason get').lower()
                    send_trade_email_async.delay(user.email, from_email,user.firstName,status, message)
                    status="pending"
                    response = {"data": {"status":status }}
                    logger.info(f"Order is pending  for user {user}. Order ID: {order_id}")
                    save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol,order_params, broker="5paisa", history_id=history_id)
                
                logger.info(f"{user} : The final response of the status : {response}")
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
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty  ,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker="5paisa", history_id=history_id)
                return response       
      
        except Exception as e:
            logger.exception(f"{user}: Unexpected error while placing order: {e}")
            return {"data": {"status": "error", "message": "An unexpected error occurred"}}
    
    except Exception as e:
        logger.exception(f"{user}: Unexpected error while placing order for user : {e}")
        return {"data": {"status": "error", "message": "An unexpected error occurred"}}
