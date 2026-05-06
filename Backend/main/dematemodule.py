
import csv
from django.forms import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
import time
import requests
import logging
from django.db.models import Q
from main.Alice_Blue_Api import place_alice_orders
from main.dhanapi import place_dhan_orders
from main.fivepaisa import fetch_access_token_5paisa, place_5paisa_order
from main.fyersapi import place_fyers_orders
from main.models import ClientBrokerdetails, Tradeorderhistory
from main.upstock import place_upstox_orders
from main.zerodha import place_zerodha_orders
from main.broker_registry import get_broker_setup_spec, broker_field_is_configured
from main.angelone.services.state_service import CallbackStateService
from main.angelone.utils.redaction import redact_secrets
from main.services.login_activity_service import LoginActivityService
from main.trade_history_service import save_trade_order_history
logger = logging.getLogger('main')
from datetime import datetime, timedelta  
import os
from django.conf import settings
import hashlib
import json
import secrets
from rest_framework import permissions, status
from urllib.parse import urlencode, urlparse, urlunparse
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
        logger.info(f"{trade.client} : Trading Symbol (Alice Blue): %s", trade_symbol)
    elif trade.broker.lower() in {'angel one', 'angle one'}:
        trade_symbol = f"{symbols}{day}{month}{year}{default_price}{Type}"
        logger.info(f"{trade.client} : Trading Symbol (Angel One): %s", trade_symbol)
    elif trade.broker.lower() == "upstox":
        trade_symbol = f"{symbols}{default_price}{Type}{day}{month}{year}"
        logger.info(f"{trade.client} : Trading Symbol (Upstox): %s", trade_symbol)
    elif trade.broker.lower() == "zerodha":
        trade_symbol = f"{symbols}{year}{month}{default_price}{Type}"
        logger.info(f"{trade.client} : Trading Symbol (Zerodha): %s", trade_symbol)
    
    # Return the generated trading symbol
    return trade_symbol
from django.http import JsonResponse


def _normalize_broker_name_for_redirect(name):
    normalized = str(name or "").strip().lower()
    if normalized in {"angle one", "angleone", "angelone"}:
        return "angel one"
    if normalized in {"5 paisa", "five paisa"}:
        return "5paisa"
    return normalized


class LoginDematAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        return BrokerLoginRedirectView().get(request, *args, **kwargs)


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
            Segment,Index_Symbol,triggerPrice,trade, history_id):
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
                webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="5paisa", history_id=history_id)
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
                EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice,trade_order_status, history_id): 
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
                webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha", history_id=history_id)
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

 

def exit_existing_buy_position_fyers_order(default_price,LivePrice,group_service,Type,day,month,year,access_token,Api_key,trade_symbol, transaction_type, symbol, quantity,strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price,
                EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice,trade_order_status, history_id): 
    try:
        logger.info(f'{user} : exit_existing_buy position_fyers_order is start now !')
        open_buy_order = Tradeorderhistory.objects.filter(
            client=user, 
            Index_Symbol=symbol,
            transaction_type="BUY",
            # strategy=strategy,
            GroupService=group_service,
            order_id__gt=0
        ).filter(Q(order_status="rejected")| Q(order_status="completed") |Q(order_status="complete")| Q(order_status="open")
                |Q(order_status="pending")| Q(order_status="Transit")).last()

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
                message=f"{user} : Existing BUY order already closed for {Index_Symbol}."
                order_id=0
                status="Failed"
                order_params={}
                res_data=message
                logger.info(f"{message}")
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, old_trade_symbol, order_id, status, res_data, message,strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="fyers", history_id=history_id)
                return {"data": {"status": "error", "message": f"Existing BUY order already closed for {old_trade_symbol} for user {user}"}}

            symbol=symbol.upper()
            trade_symbol = f"{symbol}{year}{month}{day}{default_price}{Type}"

            if trade_symbol != old_trade_symbol:
                msg=f"{user} : sell request not matching with existing order :{old_trade_symbol} new symbol: {trade_symbol}"
                logger.info(f"{msg}")  
                return {"data": {"status": "error", "message": msg}}
            logger.info(f"{user} : Previous order {oid} entry price: {Entry_price}. Found open BUY order for {symbol}. Exiting position. Order ID: {oid}")
            try:
                sell_response = place_fyers_orders(LivePrice,group_service,access_token,Api_key,trade_symbol, transaction_type, symbol, quantity,
                    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price,
                    EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice,trade_order_status)
                
            except Exception as e:
                logger.error(f"{user} : Error placing sell order: {str(e)}")
                return {"data": {"status": "error", "message": f"Error placing sell order: {str(e)}"}}

            status_value = sell_response.get("data", {}).get("status")
            if status_value in ["completed","complete","rejected", "Transit"]:
                try:
                    trade_order = Tradeorderhistory.objects.get(order_id=oid)
                    trade_order.trade_order_status = "CLOSE"
                    trade_order.save()
                    logger.info(f"{user} : Existing BUY position successfully exited for {symbol}.")
                    return sell_response
                except Exception as e:
                    logger.error(f"{user} : Error updating trade order status: {str(e)}")
                    return {"data": {"status": "error", "message": "Error updating trade order status."}}

            else:
                logger.error(f"{user} : Failed to exit existing BUY position for {symbol}. Response: {sell_response}")
                return {"data": {"status": "error", "message": "Failed to exit existing position."}}
        else:
            logger.info(f"{user} : No open BUY position found for {symbol} for user {user}.")
            message=f"No open BUY position found for {symbol} for user {user}."
            
            return {"data": {"status": "error", "message": "No open BUY position found."}} 
    except Exception as e:
        logger.error(f"{user} : Unexpected error in exit_existing_buy_position_DhanOrder: {str(e)}")
        return {"data": {"status": "error", "message": f"Unexpected error: {str(e)}"}}

from django.utils import timezone
from django.utils.timezone import now
from kiteconnect import KiteConnect


def _broker_callback_url():
    configured_url = getattr(settings, "REDIRECT_URL", "").strip()
    if not configured_url:
        return configured_url

    parsed = urlparse(configured_url)
    if parsed.path.rstrip("/") in {"/callback", "/auth-callback", "/callback-angelone"}:
        parsed = parsed._replace(path="/api/broker/callback/")
        return urlunparse(parsed)
    return configured_url


def _resolve_frontend_return_url(request):
    configured_frontend = getattr(settings, "FRONTEND_APP_URL", "").rstrip("/")
    request_origin = ""
    if request is not None:
        request_origin = (request.headers.get("Origin") or "").rstrip("/")
        if not request_origin:
            referer = (request.headers.get("Referer") or "").strip()
            if referer:
                try:
                    from urllib.parse import urlparse

                    parsed = urlparse(referer)
                    if parsed.scheme and parsed.netloc:
                        request_origin = f"{parsed.scheme}://{parsed.netloc}"
                except Exception:
                    request_origin = ""
    base = request_origin or configured_frontend
    return f"{base}/dashboard/algoviewtech/user" if base else None


def _create_broker_callback_state(request, broker_details, broker_name):
    state = secrets.token_urlsafe(24)
    client_code = broker_details.get_canonical_client_code() or f"{broker_name}-{broker_details.client_id}"
    CallbackStateService().create(
        state=state,
        user_id=broker_details.client_id,
        broker_details_id=broker_details.id,
        client_code=client_code,
        frontend_redirect_url=_resolve_frontend_return_url(request),
    )
    return state


def _save_session_tokens_compat(broker_details, request_token, access_token, refresh_token=None, feed_token=None, expiry=None):
    broker_details.request_token = request_token
    broker_details.set_session_tokens(
        access_token=access_token,
        refresh_token=refresh_token,
        feed_token=feed_token,
        expiry=expiry,
        mark_token_created=True,
    )
    broker_details.access_token = access_token or None
    broker_details.refreshToken = refresh_token or None
    broker_details.feed_token = feed_token or None
    broker_details.isTokenExpired = not bool(access_token)
    broker_details.tokenCreatedAt = now()
    broker_details.save()


def _next_session_cutoff(hour, minute):
    now_time = now()
    expiry_date = now_time.date() if now_time.hour < hour or (now_time.hour == hour and now_time.minute < minute) else now_time.date() + timedelta(days=1)
    return datetime.combine(expiry_date, datetime.min.time(), tzinfo=now_time.tzinfo) + timedelta(hours=hour, minutes=minute)


def _get_active_broker_details_for_user(user, normalized_broker_name=None):
    queryset = (
        ClientBrokerdetails.objects.filter(client=user)
        .select_related("broker_name")
        .order_by("-tokenCreatedAt", "-id")
    )
    if normalized_broker_name:
        for broker_details in queryset:
            if broker_details.broker_name and _normalize_broker_name_for_redirect(broker_details.broker_name.broker_name) == normalized_broker_name:
                return broker_details
    return queryset.first()


class BrokerLoginRedirectView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request, *args, **kwargs):
        user = request.user  
        if not user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=403)

        try:
            broker_name_hint = _normalize_broker_name_for_redirect(request.GET.get("broker", ""))
            broker_details = _get_active_broker_details_for_user(user, broker_name_hint)
            if not broker_details or not broker_details.broker_name:
                return Response(
                    {"error": "Broker details not found for the user", "message": "Please select and save broker details first."},
                    status=404,
                )

            broker_name = _normalize_broker_name_for_redirect(broker_details.broker_name.broker_name)
            if broker_name == "zerodha":
                response = self.redirect_to_zerodha(request, broker_details)

            elif broker_name == "5paisa":
                response = self.redirect_to_5paisa(request, broker_details)

            elif broker_name == "alice blue":
                response = self.redirect_to_alice_blue(broker_details)

            elif broker_name == "upstox":
                response = self.redirect_to_upstox(request, broker_details)

            elif broker_name == "fyers":
                response = self.redirect_to_fyers(request, broker_details)

            elif broker_name == "dhan":
                response = self.redirect_to_dhan(request, broker_details)

            elif broker_name == "angel one":
                response = self.redirect_to_angel_one(request, broker_details)

            else:
                response = Response({"error": "Unsupported broker", "message": "Selected broker is not supported for login."}, status=400)
            
            try:
                log_file_path = os.path.join('logs', 'login_demat_log.csv')
                os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

                log_data = {
                    'user_id': user.id,
                    'username': user.email if user.email else "unknown",
                    'broker': str(broker_name),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'action': getattr(response, "status_code", "unknown")
                }

                file_exists = os.path.isfile(log_file_path)
                with open(log_file_path, mode='a', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=log_data.keys())
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow(log_data)
                logger.info(f"# CSV # Update Broker Login staus in log CSV")
            except Exception as log_error:
                logger.error(f"# CSV # Fail silently to avoid disrupting the API")
                pass

            return response

        except Exception as e:
            logger.exception("Broker login redirect failed for user %s", user.id)
            return Response({"error": str(e), "message": str(e)}, status=500)

    def redirect_to_zerodha(self, request, broker_details):
        api_key = broker_details.broker_API_KEY
        if not api_key or not broker_details.broker_API_SKEY:
            return Response({"error": "Zerodha credentials are incomplete."}, status=400)
        state = _create_broker_callback_state(request, broker_details, "zerodha")
        params = urlencode({"api_key": api_key, "v": "3", "redirect_params": state})
        zerodha_url = f"https://kite.zerodha.com/connect/login?{params}"
        return Response({"redirect_url": zerodha_url})

    def redirect_to_5paisa(self, request, broker_details):
        VENDOR_KEY = broker_details.broker_API_KEY
        if not VENDOR_KEY or not broker_details.broker_API_SKEY or not broker_details.broker_API_UID:
            return Response({"error": "5Paisa credentials are incomplete."}, status=400)
        state = _create_broker_callback_state(request, broker_details, "5paisa")
        params = urlencode({"VendorKey": VENDOR_KEY, "ResponseURL": _broker_callback_url(), "State": state})
        paisa_url = f"https://dev-openapi.5paisa.com/WebVendorLogin/VLogin/Index?{params}"
        return Response({"redirect_url": paisa_url})

    def redirect_to_alice_blue(self, broker_details):
        return Response(
            {
                "status": "manual_session",
                "message": (
                    "Alice Blue does not use this OAuth redirect flow in this system. "
                    "Please save Alice Blue API credentials/API UID; the session is generated during order placement."
                ),
            },
            status=200,
        )
    
    def redirect_to_fyers(self, request, broker_details):
        CLIENT_ID = broker_details.broker_API_KEY
        if not CLIENT_ID or not broker_details.broker_API_SKEY:
            return Response({"error": "FYERS credentials are incomplete."}, status=400)
        STATE = _create_broker_callback_state(request, broker_details, "fyers")
        redirect_uri = _broker_callback_url()
        try:
            from fyers_apiv3 import fyersModel

            session = fyersModel.SessionModel(
                client_id=CLIENT_ID,
                secret_key=broker_details.broker_API_SKEY,
                redirect_uri=redirect_uri,
                response_type="code",
                grant_type="authorization_code",
                state=STATE,
            )
            login_url = session.generate_authcode()
        except Exception:
            params = {
                "client_id": CLIENT_ID,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "state": STATE
            }
            login_url = f"https://api-t1.fyers.in/api/v3/generate-authcode?{urlencode(params)}"

        return Response({"redirect_url": login_url})
    
    def redirect_to_upstox(self, request, broker_details):
        CLIENT_KEY = broker_details.broker_API_KEY
        CLIENT_SECRET = broker_details.broker_API_SKEY
        if not CLIENT_KEY or not CLIENT_SECRET:
            return Response({"error": "Upstox credentials are incomplete."}, status=400)
        state = _create_broker_callback_state(request, broker_details, "upstox")
        AUTH_URL = "https://api.upstox.com/v2/login/authorization/dialog"
        params = urlencode({"client_id": CLIENT_KEY, "redirect_uri": _broker_callback_url(), "response_type": "code", "state": state})
        login_url = f"{AUTH_URL}?{params}"
        return Response({"redirect_url": login_url})

    def redirect_to_dhan(self, request, broker_details):
        app_id = broker_details.broker_API_KEY
        app_secret = broker_details.broker_API_SKEY
        dhan_client_id = broker_details.broker_API_UID or broker_details.broker_Demate_User_Name
        if not app_id or not app_secret or not dhan_client_id:
            return Response(
                {"error": "Dhan credentials are incomplete. App ID/API Key, App Secret/API Secret, and Dhan Client ID are required."},
                status=400,
            )

        try:
            response = requests.post(
                f"https://auth.dhan.co/app/generate-consent?client_id={dhan_client_id}",
                headers={"app_id": app_id, "app_secret": app_secret},
                timeout=10,
            )
            payload = response.json() if response.content else {}
        except Exception as exc:
            logger.exception("Dhan consent generation failed for broker_details=%s", broker_details.id)
            return Response({"error": "Failed to initiate Dhan consent flow.", "message": str(exc)}, status=502)

        if response.status_code >= 400 or payload.get("status") not in {None, "success"}:
            return Response(
                {
                    "error": "Dhan consent generation failed.",
                    "response": payload,
                },
                status=response.status_code if response.status_code >= 400 else 400,
            )

        consent_app_id = payload.get("consentAppId")
        if not consent_app_id:
            return Response({"error": "Dhan did not return consentAppId.", "response": payload}, status=400)

        state = _create_broker_callback_state(request, broker_details, "dhan")
        params = urlencode({"consentAppId": consent_app_id, "state": state})
        login_url = f"https://auth.dhan.co/login/consentApp-login?{params}"
        broker_details.request_token = consent_app_id
        broker_details.tokenCreatedAt = now()
        broker_details.save(update_fields=["request_token", "tokenCreatedAt"])
        return Response({"redirect_url": login_url, "consent_app_id": consent_app_id})

    def redirect_to_angel_one(self, request, broker_details):
        from main.angelone_views import build_angelone_redirect_payload

        try:
            payload = build_angelone_redirect_payload(request.user, broker_details=broker_details, request=request)
            return Response(payload)
        except LookupError as exc:
            return Response({"error": str(exc), "message": str(exc)}, status=404)
        except ValueError as exc:
            payload = {"error": str(exc), "message": str(exc)}
            missing_fields = getattr(exc, "missing_fields", None)
            if missing_fields:
                payload["missing_fields"] = missing_fields
            return Response(payload, status=400)

BROKER_CALLBACK_PARAM_NAMES = (
    "request_token",
    "RequestToken",
    "auth_code",
    "authCode",
    "code",
    "state",
    "redirect_params",
    "client_id",
    "broker",
    "tokenId",
    "token_id",
)


def _safe_broker_callback_payload(query_params):
    present_params = [name for name in BROKER_CALLBACK_PARAM_NAMES if query_params.get(name)]
    broker_name = query_params.get("broker") or ""
    client_id = query_params.get("client_id") or ""
    return {
        "present_params": present_params,
        "broker": broker_name,
        "client_id": client_id,
        "state_present": bool(query_params.get("state") or query_params.get("redirect_params")),
        "token_exchange": "not_attempted",
    }


class BrokerRedirectCallbackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        callback_info = _safe_broker_callback_payload(request.GET)
        logger.info("Broker callback received: %s", redact_secrets(callback_info))

        if (
            request.GET.get("auth_token")
            or request.GET.get("access_token")
            or request.GET.get("jwtToken")
            or request.GET.get("state")
            or request.GET.get("redirect_params")
        ):
            return BrokerCallbackView.as_view()(request._request)

        broker_name = _normalize_broker_name_for_redirect(callback_info.get("broker"))
        if broker_name == "alice blue":
            callback_info["token_exchange"] = "manual_session"
            callback_info["todo"] = "Alice Blue uses saved API key/API UID credentials; no OAuth token exchange is required here."
        elif callback_info["state_present"]:
            callback_info["token_exchange"] = "available_via_existing_broker_callback"
            callback_info["todo"] = "Token exchange requires broker state and credentials; use the existing BrokerCallbackView flow when broker-specific state is present."
        elif callback_info["present_params"]:
            callback_info["todo"] = "Token exchange was not attempted because broker-specific state/credentials were not provided."
        else:
            callback_info["todo"] = "No broker callback query parameters were provided."

        return JsonResponse(
            {
                "status": "success",
                "message": "Broker callback received.",
                "callback": callback_info,
            },
            status=200,
        )


class BrokerCallbackView(APIView):
    permission_classes = [AllowAny]  

    def get(self, request, *args, **kwargs):
        if request.GET.get("auth_token") or request.GET.get("access_token") or request.GET.get("jwtToken"):
            from main.angelone_views import angelone_callback as secure_angelone_callback

            return secure_angelone_callback(request)

        # Get the authorization code and state from the URL
        try:
            broker_state = request.GET.get('state') or request.GET.get('redirect_params') or ""
            state_record = CallbackStateService().consume(broker_state) if broker_state else None
            if state_record:
                broker_details = ClientBrokerdetails.objects.select_related("broker_name").filter(id=state_record.broker_details_id, client_id=state_record.user_id).first()
                if not broker_details or not broker_details.broker_name:
                    raise ValidationError("Broker details not found for callback state")
                broker_name = _normalize_broker_name_for_redirect(broker_details.broker_name.broker_name)
            else:
                user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
                if not user and (request.GET.get("tokenId") or request.GET.get("token_id")):
                    broker_details = (
                        ClientBrokerdetails.objects.select_related("broker_name")
                        .filter(
                            broker_name__broker_name__iexact="dhan",
                            request_token__isnull=False,
                            tokenCreatedAt__gte=now() - timedelta(minutes=15),
                        )
                        .order_by("-tokenCreatedAt", "-id")
                        .first()
                    )
                    if broker_details:
                        broker_name = "dhan"
                    else:
                        raise ValidationError("Invalid or expired Dhan callback state")
                elif not user:
                    raise ValidationError("Invalid or expired broker callback state")
                else:
                    broker_name = _normalize_broker_name_for_redirect(broker_state)
                    broker_details = _get_active_broker_details_for_user(user, broker_name)
                    if not broker_details or not broker_details.broker_name:
                        raise ValidationError("Broker details not found for the user")

            if broker_name == "zerodha":
                request_token = request.GET.get('request_token') or request.GET.get('code')
                return self.handle_zerodha(request_token, broker_details)

            elif broker_name == "5paisa":
                request_token = request.GET.get('RequestToken') or request.GET.get('request_token') or request.GET.get('code')
                return self.handle_5paisa(request_token, broker_details)

            elif broker_name == "alice blue":
                request_token = request.GET.get('authCode') or request.GET.get('code')
                return self.handle_alice_blue(request_token, broker_details)

            elif broker_name == "upstox":
                request_token = request.GET.get('code')
                return self.handle_upstox(request_token, broker_details)
            
            elif broker_name == "fyers":
                request_token =request.GET.get('code')
                
                return self.handle_fyers(request_token, broker_details)

            elif broker_name == "dhan":
                token_id = request.GET.get("tokenId") or request.GET.get("token_id") or request.GET.get("code")
                return self.handle_dhan(token_id, broker_details)

            elif broker_name == "angel one":
                return self.handle_angle_one(request, broker_details)

            else:
                raise ValidationError("Unsupported broker")

        except Exception as e:
            logger.exception("Broker callback failed")
            return JsonResponse({"message": "Failed", "error": str(e)}, status=400)

    def handle_fyers(self, request_token, broker_details):
        try:
            if not request_token:
                return JsonResponse({"message": "Failed", "error": "Authorization code not provided"}, status=400)
            CLIENT_ID = broker_details.broker_API_KEY
            SECRET_KEY = broker_details.broker_API_SKEY
            redirect_uri = _broker_callback_url()
            try:
                from fyers_apiv3 import fyersModel

                session = fyersModel.SessionModel(
                    client_id=CLIENT_ID,
                    secret_key=SECRET_KEY,
                    redirect_uri=redirect_uri,
                    response_type="code",
                    grant_type="authorization_code",
                )
                session.set_token(request_token)
                token_data = session.generate_token()
            except Exception:
                token_url = "https://api-t1.fyers.in/api/v3/validate-authcode"
                headers = {"Content-Type": "application/json"}
                token_data = {}
                for raw_string in (f"{CLIENT_ID}{SECRET_KEY}", f"{CLIENT_ID}:{SECRET_KEY}"):
                    app_id_hash = hashlib.sha256(raw_string.encode()).hexdigest()
                    payload = {
                        "grant_type": "authorization_code",
                        "appIdHash": app_id_hash,
                        "code": request_token
                    }
                    response = requests.post(token_url, data=json.dumps(payload), headers=headers, timeout=10)
                    token_data = response.json() if response.content else {}
                    if token_data.get("access_token"):
                        break
            access_token = token_data.get("access_token")
            if access_token:
                expiry_time = _next_session_cutoff(3, 30)
                _save_session_tokens_compat(broker_details, request_token, access_token, expiry=expiry_time)

                return JsonResponse({"message": "success", "access_token": access_token})
            else:
                return JsonResponse({"message": "Failed to get access token", "response": token_data}, status=400)

        except Exception as e:
            return JsonResponse({"message": "Failed", "error": str(e)}, status=500)
  
    def handle_zerodha(self, request_token, broker_details):
        try:
            if not request_token:
                return JsonResponse({"message": "Failed", "error": "Request token not provided"}, status=400)
            kite = KiteConnect(api_key=broker_details.broker_API_KEY)
            session_data = kite.generate_session(request_token, api_secret=broker_details.broker_API_SKEY)
            access_token = session_data['access_token']
            if access_token:
                expiry_time = _next_session_cutoff(6, 0)
                _save_session_tokens_compat(broker_details, request_token, access_token, expiry=expiry_time)
         
                return JsonResponse({"message": "success", "access_token": access_token})
            else:
                return JsonResponse({"message": "success", "access_token": access_token})
        except Exception as e:
            return JsonResponse({"message":"Failed","error": str(e)}, status=500)

    def handle_5paisa(self, request_token, broker_details):
        try:
            if not request_token:
                return JsonResponse({"message": "Failed", "error": "Request token not provided"}, status=400)
            access_token = fetch_access_token_5paisa(request_token,broker_details)
            if access_token:
                expiry_time = _next_session_cutoff(23, 59)
                _save_session_tokens_compat(broker_details, request_token, access_token, expiry=expiry_time)
                return JsonResponse({"message": "success", "access_token": access_token})
            else:
                return JsonResponse({"message": "Failed"}, status=400)
        except Exception as e:
            return JsonResponse({"message":"Failed","error": str(e)}, status=500)
    def handle_alice_blue(self, request_token, broker_details):
        try: 
            return JsonResponse(
                {
                    "message": "Alice Blue uses API key and API UID session generation during order placement. No OAuth token callback is required.",
                    "status": "manual_session",
                },
                status=200,
            )
        
        except Exception as e:
            return JsonResponse({"message":"Failed","error": str(e)}, status=500)

    def handle_upstox(self, request_token, broker_details):
        try:
            TOKEN_URL = 'https://api.upstox.com/v2/login/authorization/token' 
            auth_code = request_token
            
            if not auth_code:
                return JsonResponse({"error": "Authorization code not provided"}, status=400)
            CLIENT_KEY=broker_details.broker_API_KEY
            CLIENT_SECRET=broker_details.broker_API_SKEY
            redirect_uri = _broker_callback_url()
            data = {
                'code': auth_code,
                'client_id': CLIENT_KEY,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            response = requests.post(TOKEN_URL, data=data, timeout=10)
            if response.status_code == 200:
                payload = response.json() if response.content else {}
                access_token = payload.get('access_token')
                refresh_token = payload.get('refresh_token')
                expires_in = payload.get("expires_in")
                expiry_time = None
                if expires_in:
                    try:
                        expiry_time = now() + timedelta(seconds=int(expires_in))
                    except (TypeError, ValueError):
                        expiry_time = None
                if expiry_time is None:
                    expiry_time = _next_session_cutoff(3, 30)
                _save_session_tokens_compat(broker_details, request_token, access_token, refresh_token=refresh_token, expiry=expiry_time)
                logger.info(f"Upstox callback processed successfully")
                return JsonResponse({"message": "success", "access_token": access_token})
            else:
                try:
                    error_payload = response.json() if response.content else {}
                except ValueError:
                    error_payload = {"raw": response.text}
                return JsonResponse({"message": "Failed", "response": error_payload}, status=400)
        
        except Exception as e:
            return JsonResponse({"message":"Failed","error": str(e)}, status=500)

    def handle_dhan(self, token_id, broker_details):
        try:
            if not token_id:
                return JsonResponse({"message": "Failed", "error": "Dhan tokenId not provided"}, status=400)

            app_id = broker_details.broker_API_KEY
            app_secret = broker_details.broker_API_SKEY
            if not app_id or not app_secret:
                return JsonResponse(
                    {"message": "Failed", "error": "Dhan App ID/API Key and App Secret/API Secret are required."},
                    status=400,
                )

            response = requests.get(
                f"https://auth.dhan.co/app/consumeApp-consent?tokenId={token_id}",
                headers={"app_id": app_id, "app_secret": app_secret},
                timeout=10,
            )
            payload = response.json() if response.content else {}
            if response.status_code >= 400 or payload.get("accessToken") is None:
                return JsonResponse(
                    {
                        "message": "Failed to generate Dhan access token",
                        "response": payload,
                    },
                    status=response.status_code if response.status_code >= 400 else 400,
                )

            access_token = payload.get("accessToken")
            expiry_time = None
            expiry_raw = payload.get("expiryTime")
            if expiry_raw:
                try:
                    expiry_time = datetime.fromisoformat(str(expiry_raw).replace("Z", "+00:00"))
                    if timezone.is_naive(expiry_time):
                        expiry_time = timezone.make_aware(expiry_time)
                except (TypeError, ValueError):
                    expiry_time = None
            if expiry_time is None:
                expiry_time = now() + timedelta(hours=24)

            dhan_client_id = payload.get("dhanClientId") or broker_details.broker_API_UID or broker_details.broker_Demate_User_Name
            broker_details.broker_API_UID = dhan_client_id
            _save_session_tokens_compat(broker_details, token_id, access_token, expiry=expiry_time)
            broker_details.broker_API_UID = dhan_client_id
            broker_details.save(update_fields=["broker_API_UID"])

            return JsonResponse(
                {
                    "message": "success",
                    "access_token": access_token,
                    "dhanClientId": dhan_client_id,
                    "expiryTime": expiry_time.isoformat() if expiry_time else None,
                }
            )

        except Exception as e:
            logger.exception("Dhan callback failed for broker_details=%s", getattr(broker_details, "id", None))
            return JsonResponse({"message": "Failed", "error": str(e)}, status=500)

    def handle_angle_one(self, request, broker_details):
        from main.angelone_views import angelone_callback

        return angelone_callback(request)

from rest_framework import status
class CheckTokenValidityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            summary = LoginActivityService().build_summary(request.user, request=request)
            broker_data = (summary.get("data") or {}).get("broker") or {}
            session = broker_data.get("session") or {}
            token = broker_data.get("token") or {}

            session_status = session.get("status") or "unavailable"
            token_status = token.get("status") or "unavailable"
            is_active = bool(
                session.get("is_active")
                or token.get("is_active")
                or session_status == "active"
                or token_status == "active"
            )

            if is_active:
                return Response(
                    {
                        "message": "Token is valid",
                        "isTokenExpired": False,
                        "session_status": session_status,
                        "token_status": token_status,
                    },
                    status=status.HTTP_200_OK,
                )

            if token_status == "expired":
                return Response(
                    {
                        "message": "Token has expired",
                        "isTokenExpired": True,
                        "session_status": session_status,
                        "token_status": token_status,
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(
                {
                    "message": "Please log in again to continue trading. You are not logged in yet.",
                    "isTokenExpired": True,
                    "session_status": session_status,
                    "token_status": token_status,
                },
                status=status.HTTP_200_OK,
            )
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
                status=status.HTTP_200_OK
            )

        broker_name = broker_details.broker_name.broker_name.lower() if broker_details.broker_name else ""

        spec = get_broker_setup_spec(broker_name)
        missing_fields = []

        if spec:
            for field_spec in spec["fields"]:
                if field_spec.get("required") and not broker_field_is_configured(broker_details, field_spec["key"]):
                    missing_fields.append(field_spec["key"])
            if missing_fields:
                return Response(
                    {
                        "status": False,
                        "message": f"Missing fields for broker '{broker_name}': {', '.join(missing_fields)}"
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response({"status": True, "message": f"All required fields are set for {broker_name}."})
        else:
            return Response(
                {"status": False, "message": f"Broker '{broker_name}' is not recognized."},
                status=status.HTTP_200_OK
            )
    
