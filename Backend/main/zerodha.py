
from django.http import JsonResponse
from kiteconnect import KiteConnect
from main.Alice_Blue_Api import save_trade_order_history
from main.models import ClientBrokerdetails
import  logging
logger = logging.getLogger('main')
def place_zerodha_orders(access_token, Api_key, trade_symbol, transaction_type, symbol, quantity,
    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type,
    webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice):
    try:
        kite = KiteConnect(api_key=Api_key)
        kite.set_access_token(access_token)
        trading_symbol = get_trading_symbol(Exchange, trade_symbol, kite)
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
            # Fetch order ID and validate response
            order_id = order_response.get('order_id', None)
            if not order_id:
                raise Exception("Order ID not returned in response.")
            order_history_response = get_order_details(order_id, access_token)

            if order_history_response['data']['status'].lower() == 'success':
                status = order_history_response['data']['status']
                message = order_history_response['data'].get('status_message', "Success")

                save_trade_order_history(user, trading_symbol, order_id, status, order_response, message,
                                         strategy, Entry_type, Exit_type, webhook_signal,
                                         Exchange, Segment, Index_Symbol, order_params, broker="zerodha")
            else:
                status = order_history_response['data']['status']
                message = order_history_response['data'].get('status_message', "Success")
                # raise Exception(order_history_response['data'].get('status_message', "Unknown error"))
                save_trade_order_history(user, trading_symbol, order_id, status, order_response, message,
                                         strategy, Entry_type, Exit_type, webhook_signal,
                                         Exchange, Segment, Index_Symbol, order_params, broker="zerodha")

            logger.info(f"Order placed successfully: {order_history_response}")
            return order_history_response

        except Exception as e:
            error_message = f"Failed to place order: {str(e)}"
            logger.error(error_message)
            order_id=0
            save_trade_order_history(user, trading_symbol, order_id, "Failed", None, str(e), strategy,
                                     Entry_type, Exit_type, webhook_signal, Exchange, Segment,
                                     Index_Symbol, order_params, broker="zerodha")

            return {"data": {"status": "Failed", "message": str(e)}}

    except Exception as e:
        logger.error(f"Exception in Zerodha order placement: {str(e)}")
        return {"data": {"status": "Failed", "message": str(e)}}
    
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


def get_order_details(order_id, access_token):
    """
    Retrieve order history for a given order ID from Zerodha Kite Connect.
    """
    api_key = "jsdgh8p7k3yvfii8"  # Replace with your API key
    try:
        # Initialize KiteConnect
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Fetch order history
        try:
            order_history = kite.order_history(order_id)
            return JsonResponse({"order_history": order_history}, status=200)
        except Exception as e:
            return JsonResponse({"error": f"Failed to fetch order history: {str(e)}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Failed to initialize KiteConnect: {str(e)}"}, status=500)

    