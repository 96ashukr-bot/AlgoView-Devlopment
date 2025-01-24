from django.http import JsonResponse
from kiteconnect import KiteConnect
from main.Alice_Blue_Api import save_trade_order_history
from main.models import ClientBrokerdetails
import logging

logger = logging.getLogger('main')

def place_zerodha_orders(access_token, Api_key, trade_symbol, transaction_type, symbol, quantity,
    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, 
    EntryQty, ExitQty, webhook_signal, Exchange, Segment,Index_Symbol, triggerPrice, trade_order_status):
    try:
        order_id = 0
        status = "Failed"
        res_data = "Unknown response"
        kite = KiteConnect(api_key=Api_key)
        kite.set_access_token(access_token)
        trading_symbol = get_trading_symbol(Exchange, trade_symbol, kite)

        if not trading_symbol:
            logger.error(f"trading_symbol details not found for {trade_symbol}")
            status = "Failed"
            message = "Instrument details not found"
            res_data = "Trading symbol not found."
            save_trade_order_history(trade_order_status, user, symbol, order_id, status, res_data, message,  
                                     strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                     webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="upstox")
            return JsonResponse({"status": "error", "message": "Instrument details not found."})

        logger.info(f"Fetched Zerodha trading_symbol: {trading_symbol}")

        # Prepare order parameters
        order_params = {
            "tradingsymbol": trading_symbol,
            "exchange": Exchange,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "order_type": ordertype,
            "product": product_type,
            "price": price if ordertype.upper() == "LIMIT" else 0,
            "trigger_price": triggerPrice if ordertype.upper() == "SL" else None
        }

        try:
            order_response = kite.place_order(variety=kite.VARIETY_REGULAR, **order_params)
            print("order_response",order_response)
            # Fetch order ID and validate response
            order_id = order_response.get('order_id', None)
            if not order_id:
                logger.error("Order ID is not returned")
                status = "Failed"
                message = "No order ID returned"
                res_data = "No order ID returned"
                save_trade_order_history(trade_order_status, user, symbol, order_id, status, res_data, message,
                                         strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                         webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="upstox")
                return JsonResponse({"status": status, "message": message})

            # Ensure that get_order_details is defined or handled properly
            order_history_response = get_order_details(order_id, access_token, kite)
            logger.info(f"Order history response: {order_history_response}")

            res_data = order_history_response

            if order_history_response['data']['status'].lower() == 'complete':
                message = order_history_response['data'].get('status_message', "Order complete")
                status = order_history_response['data']['status']
                logger.info(f"Order placed successfully. Order ID: {order_id}")
                response = {"data": {"status": "completed", "message": "Order placed and details saved successfully."}}
                save_trade_order_history(trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                         strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                         webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                return response
            else:
                status = order_history_response['data']['status']
                message = order_history_response['data'].get('status_message', "Success")
                response = {"data": {"status": status, "message": message}}
                save_trade_order_history(trade_order_status, user, trade_symbol, order_id, status, res_data, message,
                                         strategy, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty,
                                         webhook_signal, Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
                return response

        except Exception as e:
            error_message = f"Failed to place order: {str(e)}"
            logger.error(error_message)
            order_id = 0
            save_trade_order_history(trade_order_status, user, trading_symbol, order_id, "Failed", None, str(e),
                                     strategy, Entry_type, Exit_type, EntryQty, ExitQty, webhook_signal, Exchange,
                                     Segment, Index_Symbol, order_params, broker="zerodha")
            return JsonResponse({"status": "Failed", "message": str(e)})

    except Exception as e:
        logger.error(f"Exception in Zerodha order placement: {str(e)}")
        return JsonResponse({"status": "Failed", "message": str(e)})

    
def get_trading_symbol(exchange, symbol, kite):
    try:
        # Fetch the list of instruments for the specified exchange
        instruments = kite.instruments(exchange)
        # csv_file = "/home/digiprima/Desktop/jyoti/Django/AlgoView-Devlopment/Backend/zerodhaNFO.csv"
        for instrument in instruments:
            if instrument['tradingsymbol'] == symbol:
                print("Trading Symbol Found:", instrument['tradingsymbol'])
                return instrument['tradingsymbol']
        
        return None  # Return None if the symbol is not found

    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def get_order_details(order_id, access_token,kite):
    """
    Retrieve order history for a given order ID from Zerodha Kite Connect.
    """
    api_key = "jsdgh8p7k3yvfii8"  # Replace with your API key
    try:
        kite.set_access_token(access_token)
        # Fetch order history
        try:
            order_history = kite.order_history(order_id)
            return JsonResponse({"order_history": order_history}, status=200)
        except Exception as e:
            return JsonResponse({"error": f"Failed to fetch order history: {str(e)}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Failed to initialize KiteConnect: {str(e)}"}, status=500)

    