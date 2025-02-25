
import csv
from rest_framework.views import APIView
from rest_framework.response import Response
import time
import requests
import logging
from django.db.models import Q
from main.Alice_Blue_Api import place_alice_orders, save_trade_order_history
from main.dhanapi import place_dhan_orders
from main.fivepaisa import place_5paisa_order
from main.models import ClientBrokerdetails, Tradeorderhistory
from main.upstock import place_upstox_orders
from main.zerodha import place_zerodha_orders
logger = logging.getLogger('main')
from datetime import datetime, timedelta    
def get_lot_size(trading_symbol):
    # URL to fetch instrument details (for example, for Angel One)
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        for item in data:
            # print("item.get("")>>>",item)
            if item.get("symbol") == trading_symbol:
                # print("**********",item.get("lotsize", None))
                return {"status":"success" ,"lot_size":item.get("lotsize", None)}  # Fetch lot size from the item
        
        return {"status":"False"}  # If no matching symbol is found
    except requests.exceptions.RequestException as e:
        logger.error(f"Error occurred while fetching data: {str(e)}")
        return None
    
def trading_Symbol_sum(trade, symbols, day, month, year, Type, default_price):
    # Ensure day, month, year are correctly formatted as strings with leading zeros if needed
    day = str(day).zfill(2)
    month = str(month).zfill(2)
    year = str(year)
    trade_symbol = ""
    if trade.broker.lower() == 'alice blue':
        trade_symbol = f"{symbols}{day}{month}{year}{Type[0]}{default_price}"
        logger.info("Trading Symbol (Alice Blue): %s", trade_symbol)
    elif trade.broker.lower() == 'angle one':
        trade_symbol = f"{symbols}{day}{month}{year}{default_price}{Type}"
        logger.info("Trading Symbol (Angle One): %s", trade_symbol)
    elif trade.broker.lower() == "upstox":
        trade_symbol = f"{symbols}{default_price}{Type}{day}{month}{year}"
        logger.info("Trading Symbol (Upstox): %s", trade_symbol)
    elif trade.broker.lower() == "zerodha":
        trade_symbol = f"{symbols}{year}{month}{default_price}{Type}"
        logger.info("Trading Symbol (Zerodha): %s", trade_symbol)
    
    # Return the generated trading symbol
    return trade_symbol
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.http import JsonResponse
# https://software.algosparks.co.in/?type=login&status=success&request_token=Thk7L77Phj3AuNjOY3FmGCgvhIZ8416L&action=login#/login
# https://software.alcrafttechnology.com/login?code=YNJ5jw
#UPSTOX 
AUTHORIZATION_URL = 'https://login.upstox.com/login/v2/oauth/authorize'
REDIRECT_URI_UPSTOX = 'https://software.alcrafttechnology.com/login' 
TOKEN_URL_UPSTOX = 'https://api.upstox.com/v2/login/authorization/token'
AUTH_URL_UPSTOX = "https://api.upstox.com/v2/login/authorization/dialog"
AUTH_URL_ZERODHA="https://kite.zerodha.com/connect/login"
# Base URL for Upstox API
BASE_URL = "https://api.upstox.com"
class LoginDematAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            # Get the logged-in user
            user = request.user
            print(">>>>>>>>",user)
            # Retrieve broker details for the user
            broker_details = ClientBrokerdetails.objects.filter(client=user).first()
            if not broker_details:
                raise NotFound("Broker details not found for the user.")
            
            broker = broker_details.broker_name
            print("broker>>>>>>",broker)
            # Generate login URL based on broker
            if str(broker).lower() == "upstox":
                state = "upstox"
                client_key = broker_details.broker_API_KEY
                login_url = (
                    f"{AUTH_URL_UPSTOX}?client_id={client_key}&"
                    f"redirect_uri={REDIRECT_URI_UPSTOX}&"
                    f"response_type=Auth_code&"
                    f"state={state}"
                )
                print("login_url???????",login_url)
            elif broker.lower() == "zerodha":
                state = "zerodha"
                api_key = "jsdgh8p7k3yvfii8"  # Replace with your API Key
                redirect_url = "https://software.algosparks.co.in/#/login"  # Your callback URL
                login_url = (
                    f"{AUTH_URL_ZERODHA}?api_key={api_key}&v=3"
                    f"&redirect_url={redirect_url}&state={state}"
                )
            elif broker == "alice blue":
                state = "alice_blue"
                app_code = broker_details.broker_API_UID  # Replace with the Alice Blue App Code
                redirect_uri = "https://software.algosparks.co.in/#/login"  # Your callback URL
                login_url = (
                    f"https://ant.aliceblueonline.com/oauth2/auth?client_id={app_code}&"
                    f"redirect_uri={redirect_uri}&response_type=code&state={state}"
                )
            elif broker.lower() == "angel one":
                state = "angel_one"
                client_code = broker_details.broker_API_UID
                redirect_uri = "https://software.algosparks.co.in/#/login"  # Replace with your callback URL
                login_url = (
                    f"https://smartapi.angelbroking.com/publisher-login?api_key={client_code}&"
                    f"redirect_url={redirect_uri}&state={state}"
                )
            else:
                return JsonResponse(
                    {"error": f"Unsupported broker: {broker_details.broker_name}"}, 
                    status=400
                )
            
            # Return the login URL in the response
            return JsonResponse({"login_url": login_url}, status=200)

        except NotFound as e:
            return JsonResponse({"error": str(e)}, status=404)
        except Exception as e:
            return JsonResponse({"error": "An error occurred. Please try again later.", "details": str(e)}, status=500)


def exit_existing_buy_position_Upstox(
    broker, LivePrice, Type, day, month, year, access_token, trade_symbol, transaction_type, symbol, quantity,
    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price,
    EntryQty, ExitQty, webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice, trade_order_status
):
    """
    Checks if there is an open BUY order for the given user and symbol.
    If found, places a SELL order to exit that position.
    Always returns a dict with a "data" key.
    """
    try:
        print("symbol...", symbol, "user>>>>", user)
        print("trade_symbol...", trade_symbol)

        open_buy_order = Tradeorderhistory.objects.filter(
            client=user,
            Index_Symbol=symbol,
            transaction_type="BUY",
            strategy=strategy,
            order_id__gt=0
        ).filter(Q(order_status="rejected") | Q(order_status="completed") | Q(order_status="complete") | Q(order_status="open")).last()

        print("open_buy_order>>>>>>>", open_buy_order)

        if open_buy_order:
            try:
                # Extract existing order details
                Entry_price = open_buy_order.Entry_Price
                Entry_type = open_buy_order.Entry_type
                EntryQty = open_buy_order.EntryQty
                oid = open_buy_order.order_id
                price_of_order = open_buy_order.LivePrice
                LivePrice = open_buy_order.LivePrice
                old_trade_symbol = open_buy_order.trading_symbol
                buy_order_close_status = open_buy_order.trade_order_status
                print("price_of_order>>>", int(price_of_order))
                
                symbol = symbol.upper()
                trade_symbol = f"{symbol}{int(price_of_order)}{Type}{day}{month}{year}"
                print("trade_symbol>>>>", trade_symbol)
                if trade_symbol != old_trade_symbol:
                    msg=f"sell request not matching with existing order :{old_trade_symbol} new symbol: {trade_symbol} client: {user}"
                    logger.info(f"{msg}")  
                    return {"data": {"status": "error", "message": msg}}
                logger.info(f"Previous order {oid} entry price is {Entry_price}. Found open BUY order for {symbol}. Exiting position. Order ID: {open_buy_order.order_id}")
                
                if buy_order_close_status == "CLOSE":
                    message = f"Existing BUY order already closed for {Index_Symbol} for user {user}."
                    logger.info(message)
                    return {"data": {"status": "error", "message": message}}

                # Place SELL order
                sell_response = place_upstox_orders(
                    LivePrice, access_token, trade_symbol, transaction_type, symbol, quantity, strategy, ordertype,
                    product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                    webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice, trade_order_status
                )

                status_value = sell_response.get("data", {}).get("status")
                if status_value in ["completed", "rejected", "closed", "open"]:
                    trade_order = Tradeorderhistory.objects.get(order_id=oid)
                    trade_order.trade_order_status = "CLOSE"
                    trade_order.save()
                    logger.info(f"Existing BUY position successfully exited for {symbol}.")
                    return sell_response
                else:
                    logger.error(f"Failed to exit existing BUY position for {symbol}. Response: {sell_response}")
                    return {"data": {"status": "error", "message": "Failed to exit existing position."}}

            except Exception as e:
                logger.error(f"Error while processing existing BUY order exit: {str(e)}")
                return {"data": {"status": "error", "message": "Unexpected error occurred while exiting position."}}
        else:
            message = f"No open BUY position found for {symbol} for user {user}."
            logger.info(message)
            return {"data": {"status": "none", "message": message}}

    except Exception as e:
        logger.error(f"Error in exit_existing_buy_position_Upstox: {str(e)}")
        return {"data": {"status": "error", "message": "Unexpected error occurred."}}

    
def exit_existing_buy_position_Aliceblue(LivePrice, Type, day, month, year, api_skey, api_uid, trade_symbol, transaction_type, symbol, quantity, strategy, ordertype,
    product_type, price, user, Lots, trade_order_status, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty,
    ExitQty, webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice):

    try:
        print("symbol...", symbol, "user>>>>", user)
        print("trade_symbol...", trade_symbol, "strategy>>>", strategy)

        open_buy_order = Tradeorderhistory.objects.filter(
            client=user, 
            Index_Symbol=symbol,
            transaction_type="BUY",
            strategy=strategy,
            order_id__gt=0
        ).filter(Q(order_status="rejected") | Q(order_status="completed") | Q(order_status="complete") | Q(order_status="open")).last()

        print("open_buy_order alice blue >>>>>>>", open_buy_order)

        if open_buy_order:
            try:
                # Extract existing order details
                Entry_price = open_buy_order.Entry_Price
                Entry_type = open_buy_order.Entry_type
                EntryQty = open_buy_order.EntryQty
                oid = open_buy_order.order_id
                price_of_order = open_buy_order.LivePrice
                LivePrice = open_buy_order.LivePrice
                old_trade_symbol = open_buy_order.trading_symbol
                buy_order_close_status = open_buy_order.trade_order_status

                if buy_order_close_status == "CLOSE":
                    message = f"Existing BUY order already closed for {Index_Symbol} for user {user}."
                    logger.info(f"{message}")
                    return {"data": {"status": "error", "message": f"Existing BUY order already closed for {old_trade_symbol} for user {user}"}}

                print("price_of_order>>>", int(price_of_order))
                symbol = symbol.upper()
                trade_symbol = f"{symbol}{day}{month}{year}{Type[0]}{int(price_of_order)}"
                print("trade_symbol alice blue >>>>", trade_symbol)
                if trade_symbol != old_trade_symbol:
                    msg=f"sell request not matching with existing order :{old_trade_symbol} new symbol: {trade_symbol} client: {user}"
                    logger.info(f"{msg}")  
                    return {"data": {"status": "error", "message": msg}}
                logger.info(f"Previous order {oid}, entry price is: {Entry_price}. Found open BUY order for {symbol}. Exiting position. Order ID: {open_buy_order.order_id}")

                # Place sell order
                sell_response = place_alice_orders(LivePrice, api_skey, api_uid, trade_symbol, transaction_type, symbol, quantity, strategy, ordertype,
                                                   product_type, price, user, Lots, trade_order_status, Entry_type, Exit_type, Entry_price, Exit_price,
                                                   EntryQty, ExitQty, webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice)
                
                status_value = sell_response.get("data", {}).get("status")
                if status_value in ["completed", "rejected", "closed", "open"]:
                    try:
                        trade_order = Tradeorderhistory.objects.get(order_id=oid)
                        trade_order.trade_order_status = "CLOSE"
                        trade_order.save()
                        logger.info(f"Existing BUY position successfully exited for {symbol}.")
                        return sell_response
                    except Exception as e:
                        logger.error(f"Error updating trade order status for {symbol}: {e}")
                        return {"data": {"status": "error", "message": "Failed to update trade order status."}}
                else:
                    logger.error(f"Failed to exit existing BUY position for {symbol}. Response: {sell_response}")
                    return {"data": {"status": "error", "message": "Failed to exit existing position."}}

            except Exception as e:
                logger.error(f"Error processing open buy order for {symbol}: {e}")
                return {"data": {"status": "error", "message": "Error processing open buy order."}}

        else:
            logger.info(f"No open BUY position found for {symbol} for user {user}.")
            return {"data": {"status": "error", "message": "No open BUY position found."}}

    except Exception as e:
        logger.error(f"Unexpected error in exit_existing_buy_position_Aliceblue for {symbol}: {e}")
        return {"data": {"status": "error", "message": "Unexpected error occurred."}}

    
#DHAN ORDER sell----------------------
def exit_existing_buy_position_DhanOrder(LivePrice, Type, day, month, fullyear, access_token, client_id, trade_symbol, transaction_type, symbol, quantity,
                                         strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, 
                                         EntryQty, ExitQty, webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice, trade_order_status):
    try:
        print("symbol...", Index_Symbol, "user>>>>", user)
        print("trade_symbol...", trade_symbol, "strategy>>>", strategy)

        open_buy_order = Tradeorderhistory.objects.filter(
            client=user, 
            Index_Symbol=Index_Symbol,
            transaction_type="BUY",
            strategy=strategy,
            order_id__gt=0,
        ).filter(Q(order_status="rejected") |Q(order_status="TRANSIT")| Q(order_status="transit")| Q(order_status="completed") | Q(order_status="complete") | Q(order_status="open")).last()
        
        print("open_buy_order alice blue >>>>>>>", open_buy_order)

        if not open_buy_order:
            message = f"No open BUY position found for {symbol} for user {user}."
            logger.info(message)
            return {"data": {"status": "error", "message": message}}

        # Extract existing order details
        Entry_price = open_buy_order.Entry_Price
        Entry_type = open_buy_order.Entry_type
        EntryQty = open_buy_order.EntryQty
        oid = open_buy_order.order_id
        price_of_order = open_buy_order.LivePrice
        LivePrice = open_buy_order.LivePrice
        old_trade_symbol = open_buy_order.trading_symbol
        buy_order_close_status = open_buy_order.trade_order_status

        if buy_order_close_status == "CLOSE":
            message = f"Existing BUY order already closed for {Index_Symbol} for user {user}."
            order_id = 0
            status = "Failed"
            order_params = {}
            res_data = message
            logger.info(message)
            # save_trade_order_history(LivePrice, transaction_type, trade_order_status, user, old_trade_symbol, order_id, status, res_data, message,
            #                          strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
            #                          webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="dhan")
            return {"data": {"status": "error", "message": message}}

        print("price_of_order>>>", int(price_of_order))
        symbol = symbol.upper()
        trade_symbol = f"{symbol}{month}{fullyear}{int(price_of_order)}{Type}"
        print("trade_symbol dhan  >>>>", trade_symbol)
        if trade_symbol != old_trade_symbol:
            msg=f"sell request not matching with existing order :{old_trade_symbol} new symbol: {trade_symbol} client: {user}"
            logger.info(f"{msg}")  
            return {"data": {"status": "error", "message": msg}}
        logger.info(f"Previous order {oid} entry price: {Entry_price}. Found open BUY order for {symbol}. Exiting position. Order ID: {oid}")

        # Attempt to place sell order
        try:
            sell_response = place_dhan_orders(LivePrice, access_token, client_id, trade_symbol, transaction_type, symbol, quantity,
                                              strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, 
                                              EntryQty, ExitQty, webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice, trade_order_status)
        except Exception as e:
            logger.error(f"Error placing sell order: {str(e)}")
            return {"data": {"status": "error", "message": f"Error placing sell order: {str(e)}"}}

        status_value = sell_response.get("data", {}).get("status")

        if status_value in ["completed", "rejected", "closed", "open", "transit", "TRANSIT"]:
            try:
                trade_order = Tradeorderhistory.objects.get(order_id=oid)
                trade_order.trade_order_status = "CLOSE"
                trade_order.save()
                logger.info(f"Existing BUY position successfully exited for {symbol}.")
                return sell_response
            except Exception as e:
                logger.error(f"Error updating trade order status: {str(e)}")
                return {"data": {"status": "error", "message": "Error updating trade order status."}}

        else:
            logger.error(f"Failed to exit existing BUY position for {symbol}. Response: {sell_response}")
            return {"data": {"status": "error", "message": "Failed to exit existing position."}}

    except Exception as e:
        logger.error(f"Unexpected error in exit_existing_buy_position_DhanOrder: {str(e)}")
        return {"data": {"status": "error", "message": f"Unexpected error: {str(e)}"}}


#5PAISA API sell ORDER---------------------



def exit_existing_buy_position_5PaisaOrder(LivePrice,Type,day,month,fullyear,api_key,access_token,trade_symbol,transaction_type, symbol, quantity,strategy,ordertype,
            product_type, price,user, Lots,trade_order_status,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal ,Exchange, 
            Segment,Index_Symbol,triggerPrice,trade):

    print("symbol...",symbol,"user>>>>",user)
    print("trade_symbol...",trade_symbol,"strategy>>>",strategy)
    open_buy_order = Tradeorderhistory.objects.filter(
        client=user, 
        Index_Symbol=symbol,
        transaction_type="BUY",
        strategy=strategy,
        order_id__gt=0
    ).filter(Q(order_status="rejected")|  Q(order_status="completed") |Q(order_status="complete")| Q(order_status="open")).last()
    print("open_buy_order alice blue >>>>>>>",open_buy_order)
    if open_buy_order:
        # Extract existing order details
        Entry_price = open_buy_order.Entry_Price
        Entry_type = open_buy_order.Entry_type
        EntryQty = open_buy_order.EntryQty
        oid = open_buy_order.order_id
        price_of_order=open_buy_order.LivePrice
        LivePrice=open_buy_order.LivePrice
        old_trade_symbol=open_buy_order.trading_symbol
        buy_order_close_status=open_buy_order.trade_order_status
        if buy_order_close_status=="CLOSE":
            message=f"Existing BUY order already closed for {Index_Symbol} for user {user}."
            order_id=0
            status="Failed"
            order_params={}
            res_data=message
            logger.info(f"{message}")
            save_trade_order_history(LivePrice,transaction_type,trade_order_status, user, old_trade_symbol, order_id, status, res_data, message,
            strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="5paisa")
            return {"data": {"status": "error", "message": f"Existing BUY order already closed for {old_trade_symbol} for user {user}"}}

        print("price_of_order>>>",int(price_of_order))
        symbol=symbol.upper()
        formated_prc=f"{int(price_of_order):.2f}"
        trade_symbol = f"{symbol}{day}{month}{fullyear}{Type}{formated_prc}" 
        print("trade_symbol 5paisa  >>>>",trade_symbol)

        logger.info(f"privious order {oid}  enrty price is::::: {Entry_price}Found open BUY order for {symbol}. Exiting position. Order ID: {open_buy_order.order_id}")

        sell_response =place_5paisa_order(LivePrice,api_key,access_token,trade_symbol,transaction_type, symbol, quantity,strategy,ordertype,
            product_type, price,user, Lots,trade_order_status,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal ,Exchange, 
            Segment,Index_Symbol,triggerPrice,trade)

        status_value = sell_response.get("data", {}).get("status")
        if status_value in ["completed","rejected", "closed","open","transit","TRANSIT"]:
            trade_order = Tradeorderhistory.objects.get(order_id=oid)
            trade_order.trade_order_status="CLOSE"
            trade_order.save()
            logger.info(f"Existing BUY position successfully exited for {symbol}.")
            return sell_response
        else:
            logger.error(f"Failed to exit existing BUY position for {symbol}. Response: {sell_response}")
            return {"data": {"status": "error", "message": "Failed to exit existing position."}}
    else:
        logger.info(f"No open BUY position found for {symbol} for user {user}.")
        message=f"No open BUY position found for {symbol} for user {user}."
        
        return {"data": {"status": "error", "message": "No open BUY position found."}}        
    
#zerodha sell order-----------------

def exit_existing_buy_position_zerodha_order(LivePrice,Type,day,month,year,access_token,Api_key,trade_symbol, transaction_type, symbol, quantity,strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price,
                EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice,trade_order_status): 
    
    print("symbol...",symbol,"user>>>>",user)
    print("trade_symbol...",trade_symbol,"strategy>>>",strategy)
    open_buy_order = Tradeorderhistory.objects.filter(
        client=user, 
        Index_Symbol=symbol,
        transaction_type="BUY",
        strategy=strategy,
        order_id__gt=0
    ).filter(Q(order_status="rejected")| Q(order_status="completed") |Q(order_status="complete")| Q(order_status="open")).last()
    print("open_buy_order alice blue >>>>>>>",open_buy_order)
    if open_buy_order:
        # Extract existing order details
        Entry_price = open_buy_order.Entry_Price
        Entry_type = open_buy_order.Entry_type
        EntryQty = open_buy_order.EntryQty
        oid = open_buy_order.order_id
        price_of_order=open_buy_order.LivePrice
        LivePrice=open_buy_order.LivePrice
        old_trade_symbol=open_buy_order.trading_symbol
        buy_order_close_status=open_buy_order.trade_order_status
        if buy_order_close_status=="CLOSE":
            message=f"Existing BUY order already closed for {Index_Symbol} for user {user}."
            order_id=0
            status="Failed"
            order_params={}
            res_data=message
            logger.info(f"{message}")
            save_trade_order_history(LivePrice,transaction_type,trade_order_status, user, old_trade_symbol, order_id, status, res_data, message,strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
            webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
            return {"data": {"status": "error", "message": f"Existing BUY order already closed for {old_trade_symbol} for user {user}"}}

        print("price_of_order>>>",int(price_of_order))
        symbol=symbol.upper()
        trade_symbol = f"{symbol}{year}{month}{int(price_of_order)}{Type}" 
        print("trade_symbol zerodha  >>>>",trade_symbol)

        logger.info(f"privious order {oid}  enrty price is::::: {Entry_price}Found open BUY order for {symbol}. Exiting position. Order ID: {open_buy_order.order_id}")

        sell_response = place_zerodha_orders(LivePrice,access_token,Api_key,trade_symbol, transaction_type, symbol, quantity,
                strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price,
                EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice,trade_order_status)

        status_value = sell_response.get("data", {}).get("status")
        if status_value in ["completed","rejected", "closed","open","transit","TRANSIT"]:
            trade_order = Tradeorderhistory.objects.get(order_id=oid)
            trade_order.trade_order_status="CLOSE"
            trade_order.save()
            logger.info(f"Existing BUY position successfully exited for {symbol}.")
            return sell_response
        else:
            logger.error(f"Failed to exit existing BUY position for {symbol}. Response: {sell_response}")
            return {"data": {"status": "error", "message": "Failed to exit existing position."}}
    else:
        logger.info(f"No open BUY position found for {symbol} for user {user}.")
        message=f"No open BUY position found for {symbol} for user {user}."
        
        return {"data": {"status": "error", "message": "No open BUY position found."}}     