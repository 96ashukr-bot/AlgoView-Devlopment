
import csv
from rest_framework.views import APIView
from rest_framework.response import Response
import time
import requests
import logging
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
