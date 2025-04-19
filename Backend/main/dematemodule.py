
import csv
from django.forms import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
import time
import requests
import logging
from django.db.models import Q
from main.Alice_Blue_Api import place_alice_orders, save_trade_order_history
from main.dhanapi import place_dhan_orders
from main.fivepaisa import fetch_access_token_5paisa, place_5paisa_order
from main.models import ClientBrokerdetails, Tradeorderhistory
from main.upstock import place_upstox_orders
from main.zerodha import place_zerodha_orders
logger = logging.getLogger('main')
from datetime import datetime, timedelta  
from django.conf import settings
import hashlib
import json
from rest_framework import permissions, status
  
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
    group_service, LivePrice, Type, day, month, year, access_token, trade_symbol, transaction_type, symbol, quantity,
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
        logger.info(f"trade_symbol...:::{trade_symbol} or group_service strategy:::{group_service}")
        open_buy_order_get = Tradeorderhistory.objects.filter(
            client=user,
            Index_Symbol=symbol,
            transaction_type="BUY",
            # strategy=strategy,
            GroupService=group_service,
            order_id__gt=0
        ).filter(Q(order_status="rejected") | Q(order_status="completed") | Q(order_status="complete") | Q(order_status="open")).last()
        print(":::open_buy_order_get:::",open_buy_order_get)
        open_buy_order = Tradeorderhistory.objects.filter(
            client=user,
            Index_Symbol=symbol,
            transaction_type="BUY",
            # strategy=strategy,
            GroupService=group_service,
            order_id__gt=0
        ).filter(Q(order_status="rejected") | Q(order_status="completed") | Q(order_status="complete") |Q(order_status="put order req received")| Q(order_status="open")).last()

        print("open_buy_order>>>>>>>", open_buy_order)
        if not open_buy_order:
            message = f"No open BUY position found for {symbol} for user {user}."
            logger.info(message)
            return {"data": {"status": "error", "message": message}}
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
                    LivePrice, group_service,access_token, trade_symbol, transaction_type, symbol, quantity, strategy, ordertype,
                    product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                    webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice, trade_order_status
                )

                status_value = sell_response.get("data", {}).get("status")
                if status_value in ["completed","complete", "rejected", "closed", "open","put order req received"]:
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
            return {"data": {"status": "error", "message": message}}

    except Exception as e:
        logger.error(f"Error in exit_existing_buy_position_Upstox: {str(e)}")
        return {"data": {"status": "error", "message": "Unexpected error occurred."}}

    
def exit_existing_buy_position_Aliceblue(LivePrice,group_service, Type, day, month, year, api_skey, api_uid, trade_symbol, transaction_type, symbol, quantity, strategy, ordertype,
    product_type, price, user, Lots, trade_order_status, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty,
    ExitQty, webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice):

    try:
        print("symbol...", symbol, "user>>>>", user)
        print("trade_symbol...", trade_symbol, "strategy>>>", strategy)
        open_buy = Tradeorderhistory.objects.filter(
            client=user, 
            Index_Symbol=symbol,
            transaction_type="BUY",
            # strategy=strategy,
            GroupService=group_service,
            order_id__gt=0
        ).filter(Q(order_status="rejected") | Q(order_status="completed") | Q(order_status="complete") |Q(order_status="pending")
        | Q(order_status="open")).last()
        print("GROUP service open_buy_orderfffff>>>>>",open_buy)
        open_buy_order = Tradeorderhistory.objects.filter(
            client=user, 
            Index_Symbol=symbol,
            transaction_type="BUY",
            # strategy=strategy,
            GroupService=group_service,
            order_id__gt=0
        ).filter(Q(order_status="rejected") | Q(order_status="completed") | Q(order_status="complete") | Q(order_status="open")).last()

        print("open_buy_order alice blue >>>>>>>", open_buy_order)
        if not open_buy_order:
            message = f"No open BUY position found for {symbol} for user {user}."
            logger.info(message)
            return {"data": {"status": "error", "message": message}}
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
                logger.info(f"trade_symbol alice blue sell >>>>:{trade_symbol}" )
                if trade_symbol != old_trade_symbol:
                    msg=f"sell request not matching with existing order :{old_trade_symbol} new symbol: {trade_symbol} client: {user}"
                    logger.info(f"{msg}")  
                    return {"data": {"status": "error", "message": msg}}
                logger.info(f"Previous order {oid}, entry price is: {Entry_price}. Found open BUY order for {symbol}. Exiting position. Order ID: {open_buy_order.order_id}")

                # Place sell order
                sell_response = place_alice_orders(LivePrice,group_service, api_skey, api_uid, trade_symbol, transaction_type, symbol, quantity, strategy, ordertype,
                                                   product_type, price, user, Lots, trade_order_status, Entry_type, Exit_type, Entry_price, Exit_price,
                                                   EntryQty, ExitQty, webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice)
                
                status_value = sell_response.get("data", {}).get("status")
                if status_value in ["completed","complete", "rejected", "closed", "open","pending"]:
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
def exit_existing_buy_position_DhanOrder(expiry_date,LivePrice, group_service,Type, day, month, fullyear, access_token, client_id, trade_symbol, transaction_type, symbol, quantity,
                                         strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, 
                                         EntryQty, ExitQty, webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice, trade_order_status):
    try:
        print("symbol...", Index_Symbol, "user>>>>", user)
        print("trade_symbol...", trade_symbol, "strategy>>>", strategy)

        open_buy_order = Tradeorderhistory.objects.filter(
            client=user, 
            Index_Symbol=Index_Symbol,
            transaction_type="BUY",
            # strategy=strategy,
            GroupService=group_service,
            order_id__gt=0,
        ).filter(Q(order_status="rejected") | Q(order_status="traded") | Q(order_status="TRADED")
                |Q(order_status="TRANSIT")| Q(order_status="transit")| Q(order_status="completed")  
                | Q(order_status="complete") | Q(order_status="open")).last()
        
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
            sell_response = place_dhan_orders(expiry_date,LivePrice, group_service,access_token, client_id, trade_symbol, transaction_type, symbol, quantity,
                                              strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, 
                                              EntryQty, ExitQty, webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice, trade_order_status)
        except Exception as e:
            logger.error(f"Error placing sell order: {str(e)}")
            return {"data": {"status": "error", "message": f"Error placing sell order: {str(e)}"}}

        status_value = sell_response.get("data", {}).get("status")

        if status_value in ["completed","complete", "rejected", "closed", "open", "transit", "TRANSIT","TRADED","traded"]:
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



def exit_existing_buy_position_5PaisaOrder(LivePrice,group_service,Type,day,month,fullyear,api_key,access_token,trade_symbol,transaction_type, symbol, quantity,strategy,ordertype,
            product_type, price,user, Lots,trade_order_status,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal ,Exchange, 
            Segment,Index_Symbol,triggerPrice,trade):
    try:
        print("symbol...",symbol,"user>>>>",user)
        print("trade_symbol...",trade_symbol,"strategy>>>",strategy)
        open_buy_order = Tradeorderhistory.objects.filter(
            client=user, 
            Index_Symbol=symbol,
            transaction_type="BUY",
            # strategy=strategy,
            GroupService=group_service,
            order_id__gt=0
        ).filter(Q(order_status="rejected")|  Q(order_status="completed") |Q(order_status="complete")| Q(order_status="open")).last()
        print("open_buy_order 5Paisa::::::::--------",open_buy_order)
        if not open_buy_order:
            message = f"No open BUY position found for {symbol} for user {user}."
            logger.info(message)
            return {"data": {"status": "error", "message": message}}
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
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, old_trade_symbol, order_id, status, res_data, message,
                strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="5paisa")
                return {"data": {"status": "error", "message": f"Existing BUY order already closed for {old_trade_symbol} for user {user}"}}

            print("price_of_order>>>",int(price_of_order))
            symbol=symbol.upper()
            formated_prc=f"{int(price_of_order):.2f}"
            trade_symbol = f"{symbol}{day}{month}{fullyear}{Type}{formated_prc}" 
            print("trade_symbol 5paisa  >>>>",trade_symbol)
            if trade_symbol != old_trade_symbol:
                msg=f"sell request not matching with existing order :{old_trade_symbol} new symbol: {trade_symbol} client: {user}"
                logger.info(f"{msg}")  
                return {"data": {"status": "error", "message": msg}}
            logger.info(f"Previous order {oid} entry price: {Entry_price}. Found open BUY order for {symbol}. Exiting position. Order ID: {oid}")
            try:
                sell_response =place_5paisa_order(LivePrice,group_service,api_key,access_token,trade_symbol,transaction_type, symbol, quantity,strategy,ordertype,
                    product_type, price,user, Lots,trade_order_status,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal ,Exchange, 
                Segment,Index_Symbol,triggerPrice,trade)
            except Exception as e:
                logger.error(f"Error placing sell order: {str(e)}")
                return {"data": {"status": "error", "message": f"Error placing sell order: {str(e)}"}}
            status_value = sell_response.get("data", {}).get("status")
            if status_value in ["completed","complete","rejected", "closed","open","Fully Executed","TRANSIT"]:
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
        else:
            logger.info(f"No open BUY position found for {symbol} for user {user}.")
            message=f"No open BUY position found for {symbol} for user {user}."
            
            return {"data": {"status": "error", "message": "No open BUY position found."}}        
    except Exception as e:
        logger.error(f"Unexpected error in exit_existing_buy_position_DhanOrder: {str(e)}")
        return {"data": {"status": "error", "message": f"Unexpected error: {str(e)}"}}

#zerodha sell order-----------------

def exit_existing_buy_position_zerodha_order(LivePrice,group_service,Type,day,month,year,access_token,Api_key,trade_symbol, transaction_type, symbol, quantity,strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price,
                EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice,trade_order_status): 
    try:
        print("symbol...",symbol,"user>>>>",user)
        print("trade_symbol...",trade_symbol,"strategy>>>",strategy)
        open_buy_order = Tradeorderhistory.objects.filter(
            client=user, 
            Index_Symbol=symbol,
            transaction_type="BUY",
            # strategy=strategy,
            GroupService=group_service,
            order_id__gt=0
        ).filter(Q(order_status="rejected")| Q(order_status="completed") |Q(order_status="complete")| Q(order_status="open")
                |Q(order_status="pending")).last()
        print("open_buy_order Zerodha order >>>>>>>",open_buy_order)
        if not open_buy_order:
            message = f"No open BUY position found for {symbol} for user {user}."
            logger.info(message)
            return {"data": {"status": "error", "message": message}}
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
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, old_trade_symbol, order_id, status, res_data, message,strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                print(">>>>>>>>777777777777777777")
                return {"data": {"status": "error", "message": f"Existing BUY order already closed for {old_trade_symbol} for user {user}"}}

            print("price_of_order>>>",int(price_of_order))
            symbol=symbol.upper()
            trade_symbol = f"{symbol}{year}{month}{int(price_of_order)}{Type}" 
            print("trade_symbol zerodha order  >>>>",trade_symbol)
            if trade_symbol != old_trade_symbol:
                msg=f"sell request not matching with existing order :{old_trade_symbol} new symbol: {trade_symbol} client: {user}"
                logger.info(f"{msg}")  
                return {"data": {"status": "error", "message": msg}}
            logger.info(f"Previous order {oid} entry price: {Entry_price}. Found open BUY order for {symbol}. Exiting position. Order ID: {oid}")
            try:
                sell_response =place_zerodha_orders(LivePrice,group_service,access_token,Api_key,trade_symbol, transaction_type, symbol, quantity,
                    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price,
                    EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice,trade_order_status)

            except Exception as e:
                logger.error(f"Error placing sell order: {str(e)}")
                return {"data": {"status": "error", "message": f"Error placing sell order: {str(e)}"}}

            status_value = sell_response.get("data", {}).get("status")
            if status_value in ["completed","complete","rejected", ]:
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
        else:
            logger.info(f"No open BUY position found for {symbol} for user {user}.")
            message=f"No open BUY position found for {symbol} for user {user}."
            
            return {"data": {"status": "error", "message": "No open BUY position found."}} 
    except Exception as e:
        logger.error(f"Unexpected error in exit_existing_buy_position_DhanOrder: {str(e)}")
        return {"data": {"status": "error", "message": f"Unexpected error: {str(e)}"}}

 




from django.utils.timezone import now
from django.shortcuts import redirect
from kiteconnect import KiteConnect
from django.contrib.auth.decorators import login_required
REDIRECT_URI=settings.REDIRECT_URL
class BrokerLoginRedirectView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request, *args, **kwargs):
        print("broker login api is called...................")
        user = request.user  
        if not user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=403)

        try:
            # Retrieve broker details for the logged-in user
            broker_details = ClientBrokerdetails.objects.get(client=user)
            broker_name = broker_details.broker_name.broker_name.lower()
            print("broker_name>>>",broker_name)
            # broker_name=request.GET.get('state')
            if broker_name == "zerodha":
                # request.GET.get('request_token')
                return self.redirect_to_zerodha(broker_details)

            elif broker_name == "5paisa":
                return self.redirect_to_5paisa(broker_details)

            elif broker_name == "alice blue":
                return self.redirect_to_alice_blue(broker_details)

            elif broker_name == "upstox":
                return self.redirect_to_upstox(broker_details)
            
            elif broker_name == "fyers":
                return self.redirect_to_fyers(broker_details)

            else:
                return Response({"error": "Unsupported broker"}, status=400)

        except ClientBrokerdetails.DoesNotExist:
            return Response({"error": "Broker details not found for the user"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def redirect_to_zerodha(self, broker_details):
        api_key = broker_details.broker_API_KEY
        # redirect_url ="https://www.admin.algoview.in/callback"  # Replace with your callback URL
        
        state = "zerodha"  # Include user-specific state
        zerodha_url = (
            f"https://kite.zerodha.com/connect/login?api_key={api_key}&v=3"
            f"&redirect_uri={REDIRECT_URI}&state={state}"
        )
        return Response({"redirect_url": zerodha_url})

    def redirect_to_5paisa(self, broker_details):
        # redirect_url ="https://www.admin.algoview.in/callback" 
        VENDOR_KEY = broker_details.broker_API_KEY
        state="5paisa"
        paisa_url = (f"https://dev-openapi.5paisa.com/WebVendorLogin/VLogin/Index?"f"VendorKey={VENDOR_KEY}&ResponseURL={REDIRECT_URI}&State={state}"
    )    
        return Response({"redirect_url": paisa_url})

    def redirect_to_alice_blue(self, broker_details):
        return redirect("login-aliceblue")  
    
    def redirect_to_fyers(self, broker_details):
        CLIENT_ID = broker_details.broker_API_KEY
        CLIENT_SECRET = broker_details.broker_API_SKEY
        RESPONSE_TYPE = "code"
        STATE = "fyers"

        # Fyers Authorization URL
        login_url = (
            f"https://api-t1.fyers.in/api/v3/generate-authcode?"
            f"client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
            f"&response_type={RESPONSE_TYPE}&state={STATE}"
        )

        print("CLIENT_ID >>>", CLIENT_ID)
        print("Redirect URL >>>", login_url)

        return Response({"redirect_url": login_url})
    
    def redirect_to_upstox(self, broker_details):
        CLIENT_KEY = broker_details.broker_API_KEY
        print("CLIENT_KEY>>>",CLIENT_KEY)
        CLIENT_SECRET = broker_details.broker_API_SKEY
        state="upstox"
        AUTH_URL = "https://api.upstox.com/v2/login/authorization/dialog"
        # Ensure REDIRECT_URI is properly defined
        login_url = (
            f"{AUTH_URL}?client_id={CLIENT_KEY}&"
            f"redirect_uri={REDIRECT_URI}&"
            f"response_type=Auth_code&"
            f"state={state}"
        )
        print("login_url>>", login_url)
        return Response({"redirect_url": login_url})

class BrokerCallbackView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request, *args, **kwargs):
        print("callback url calleddd......")
        # Get the authorization code and state from the URL
        try:
            user = request.user  
            broker_details = ClientBrokerdetails.objects.get(client=user)
            print("broker_details:::::::::::",broker_details)
            broker  = broker_details.broker_name.broker_name
            broker_name=request.GET.get('state',"") 

            broker_name = broker_name.lower()
            print(" Broker from State Param:", broker_name)
            if broker_name == "zerodha":
                request_token = request.GET.get('code')
                return self.handle_zerodha(request_token, broker_details)

            elif broker_name == "5paisa":
                request_token = request.GET.get('code')
                return self.handle_5paisa(request_token, broker_details)

            elif broker_name == "alice blue":
                return self.handle_alice_blue(request_token, broker_details)

            elif broker_name == "upstox":
                request_token = request.GET.get('code')
                return self.handle_upstox(request_token, broker_details)
            
            elif broker_name == "fyers":
                request_token =request.GET.get('code')
                
                return self.handle_fyers(request_token, broker_details)

            else:
                raise ValidationError("Unsupported broker")

        except ClientBrokerdetails.DoesNotExist:
            raise ValidationError("Broker details not found for the user")
        except Exception as e:
            raise ValidationError(str(e))

    def handle_fyers(self, request_token, broker_details):
        try:
            CLIENT_ID = broker_details.broker_API_KEY
            SECRET_KEY = broker_details.broker_API_SKEY
            GRANT_TYPE = "authorization_code"

            #  Correct hash: SHA256("client_id:secret_key")
            raw_string = f"{CLIENT_ID}:{SECRET_KEY}"
            app_id_hash = hashlib.sha256(raw_string.encode()).hexdigest()

            # Token exchange endpoint
            token_url = "https://api-t1.fyers.in/api/v3/validate-authcode"
            payload = {
                "grant_type": GRANT_TYPE,
                "appIdHash": app_id_hash,
                "code": request_token
            }

            headers = {"Content-Type": "application/json"}
            response = requests.post(token_url, data=json.dumps(payload), headers=headers)
            token_data = response.json()

            # print("Access Token Response:", json.dumps(token_data, indent=4))

            access_token = token_data.get("access_token")
            print("access_token>>>",access_token)
            if access_token:
                now_time = now()

                #  Set expiry to next 3:30 AM
                if now_time.hour < 3 or (now_time.hour == 3 and now_time.minute < 30):
                    expiry_date = now_time.date()
                else:
                    expiry_date = now_time.date() + timedelta(days=1)
                expiry_time = datetime.combine(expiry_date, datetime.min.time()) + timedelta(hours=3, minutes=30)

                # Save token data
                broker_details.request_token = request_token
                broker_details.access_token = access_token
                broker_details.access_token_expiry = expiry_time
                broker_details.isTokenExpired = False
                broker_details.tokenCreatedAt = now()
                broker_details.save()

                return JsonResponse({"message": "success", "access_token": access_token})
            else:
                return JsonResponse({"message": "Failed to get access token", "response": token_data}, status=400)

        except Exception as e:
            return JsonResponse({"message": "Failed", "error": str(e)}, status=500)
  
    def handle_zerodha(self, request_token, broker_details):
        try:
            kite = KiteConnect(api_key=broker_details.broker_API_KEY)
            session_data = kite.generate_session(request_token, api_secret=broker_details.broker_API_SKEY)
            access_token = session_data['access_token']
            if access_token:
                # Calculate expiry at 6 AM next day
                expiry_time = datetime.combine(now().date() + timedelta(days=1), datetime.min.time()) + timedelta(hours=6)

                # Save details
                broker_details.request_token = request_token
                broker_details.access_token = access_token
                broker_details.access_token_expiry = expiry_time
                broker_details.isTokenExpired = False
                broker_details.tokenCreatedAt = now()
                broker_details.save()
         
                return JsonResponse({"message": "success", "access_token": access_token})
            else:
                return JsonResponse({"message": "success", "access_token": access_token})
        except Exception as e:
            return JsonResponse({"message":"Failed","error": str(e)}, status=500)
            # try:
            #     AUTH_TOKEN_URL="https://api.kite.trade/session/token"
            #     headers={
            #             "api_key": broker_details.broker_API_SKEY,
            #             "request_token": request_token,
            #             "checksum": generate_checksum(broker_details.broker_API_SKEY, broker_details.broker_API_UID, request_token),
            #         }
            #     # Make a POST request to fetch the access token
            #     response = requests.post(AUTH_TOKEN_URL,headers)
            #     response_data = response.json()
            #     print("response_data>>>",response_data)
            #     return JsonResponse({
            #         "message": "Callback successful",
            #         "access_token": response_data.get("access_token"),
                    
            #     })
            # except Exception as e:
            #     return JsonResponse({"error": str(e)}, status=500)
    def handle_5paisa(self, request_token, broker_details):
        try:
            access_token = fetch_access_token_5paisa(request_token,broker_details)
            if access_token:
                now_time = now()
                expiry_date = now_time.date() if now_time.hour < 3 or (now_time.hour == 3 and now_time.minute < 30) else now_time.date() + timedelta(days=1)
                expiry_time = datetime.combine(expiry_date, datetime.min.time()) + timedelta(hours=3, minutes=30)
                broker_details.request_token = request_token
                broker_details.access_token = access_token
                broker_details.access_token_expiry =expiry_time# now() + timedelta(days=1) 
                broker_details.isTokenExpired = False
                broker_details.tokenCreatedAt = now()
                broker_details.save()
                return JsonResponse({"message": "success", "access_token": access_token})
            else:
                return JsonResponse({"message": "Failed"}, status=400)
        except Exception as e:
            return JsonResponse({"message":"Failed","error": str(e)}, status=500)
    def handle_alice_blue(self, request_token, broker_details):
        try: 
            access_token = "aliceblue_access_token_placeholder" 
            if access_token:
                # Save access token and other details
                broker_details.request_token = request_token
                broker_details.access_token = access_token
                broker_details.access_token_expiry = now() + timedelta(days=1)  # Assuming 1-day validity
                broker_details.save()
                
                return JsonResponse({"message": "success", "access_token": access_token})
            else:
                return JsonResponse({"message": "Failed"}, status=400)
        
        except Exception as e:
            return JsonResponse({"message":"Failed","error": str(e)}, status=500)

    def handle_upstox(self, request_token, broker_details):
        try:
            # Example Upstox-specific token generation logic
            TOKEN_URL = 'https://api.upstox.com/v2/login/authorization/token' 
            auth_code = request_token  # Assuming `request_token` is the auth code
            
            if not auth_code:
                return JsonResponse({"error": "Authorization code not provided"}, status=400)
            CLIENT_KEY=broker_details.broker_API_KEY
            CLIENT_SECRET=broker_details.broker_API_SKEY
            print("CLIENT_KEY>>>>",CLIENT_KEY,">>skey>>>>>",CLIENT_SECRET)
            REDIRECT_URI="https://sparks.algoview.in/callback"
            data = {
                'code': auth_code,
                'client_id': CLIENT_KEY,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': REDIRECT_URI,
                'grant_type': 'authorization_code'
            }
            response = requests.post(TOKEN_URL, data=data)
            print("response>>>>",response)
            if response.status_code == 200:
                access_token = response.json().get('access_token')
                # Calculate Expiry Time (Fixed at 3:30 AM the Next Day)
                now_time = now()
                expiry_date = now_time.date() if now_time.hour < 3 or (now_time.hour == 3 and now_time.minute < 30) else now_time.date() + timedelta(days=1)
                expiry_time = datetime.combine(expiry_date, datetime.min.time()) + timedelta(hours=3, minutes=30)
                print("expiry_time>>>>",expiry_time)
                # Save access token and expiry time
                broker_details.request_token = request_token
                broker_details.access_token = access_token
                broker_details.access_token_expiry = expiry_time
                broker_details.isTokenExpired = False
                broker_details.tokenCreatedAt = now()
                broker_details.save()
                
                # Save access token and other details
                # broker_details.request_token = request_token
                # broker_details.access_token = access_token
                # broker_details.access_token_expiry = now() + timedelta(days=1)  # Assuming 1-day validity
                # broker_details.save()
                logger.info(f"Upstox callback processed successfully")
                return JsonResponse({"message": "success", "access_token": access_token})
            else:
                return JsonResponse({"message": "Failed"}, status=400)
        
        except Exception as e:
            return JsonResponse({"message":"Failed","error": str(e)}, status=500)

from rest_framework import status
class CheckTokenValidityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user  
            broker_details = ClientBrokerdetails.objects.get(client=user)
            if not broker_details.access_token_expiry:
                broker_details.isTokenExpired = True
                broker_details.save()
                return Response({
                    "message": "Please login. You are not logged in yet.",
                    "isTokenExpired": broker_details.isTokenExpired
                }, status=status.HTTP_200_OK)
            if broker_details.access_token_expiry and now() > broker_details.access_token_expiry:
                broker_details.isTokenExpired = True
                broker_details.save()
                
                return Response({"message": "Token has expired", "isTokenExpired": broker_details.isTokenExpired}, status=status.HTTP_401_UNAUTHORIZED)
            
            return Response({"message": "Token is valid", "isTokenExpired": broker_details.isTokenExpired}, status=status.HTTP_200_OK)

        except ClientBrokerdetails.DoesNotExist:
            return Response({"error": "Broker details not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
    



class GetClientBrokerDetailsSettingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            id=request.user
            broker_details = ClientBrokerdetails.objects.get(client=id)
        except ClientBrokerdetails.DoesNotExist:
            return Response(
                {"status": False, "message": "Client has not selected any broker yet. Please select a broker."},
                status=status.HTTP_404_NOT_FOUND
            )

        broker_name = broker_details.broker_name.broker_name.lower() if broker_details.broker_name else ""

        missing_fields = []

        def check_fields(required_fields):
            for field in required_fields:
                if not getattr(broker_details, field):
                    missing_fields.append(field)

        broker_requirements = {
            "upstox": ["broker_API_KEY", "broker_API_SKEY"],
            "zerodha": ["broker_API_KEY", "broker_API_SKEY"],
            "alice blue": ["broker_API_KEY", "broker_API_UID"],
            "angle one": ["broker_API_KEY", "broker_Demate_User_Name", "broker_Totp_Authcode", "broker_pass"],
            "dhan": ["broker_API_KEY", "access_token"],
            "fyers": ["broker_API_KEY", "broker_API_SKEY"],
            "5paisa": ["broker_API_KEY", "broker_API_SKEY","broker_API_UID"],
        }

        if broker_name in broker_requirements:
            check_fields(broker_requirements[broker_name])
            if missing_fields:
                return Response(
                    {
                        "status": False,
                        "message": f"Missing fields for broker '{broker_name}': {', '.join(missing_fields)}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response({"status": True, "message": f"All required fields are set for {broker_name}."})
        else:
            return Response(
                {"status": False, "message": f"Broker '{broker_name}' is not recognized."},
                status=status.HTTP_400_BAD_REQUEST
            )
    