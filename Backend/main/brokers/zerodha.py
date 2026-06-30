from __future__ import annotations

from kiteconnect import KiteConnect

from main.brokers.base import BaseBroker
from main.brokers.position_guard import mark_open_position_closed, prepare_close_order_from_open_position
from main.brokers.utils import broker_order_exchange, build_trade_symbol, common_order_kwargs, get_access_token, get_order_payload
from main.zerodha import place_zerodha_orders


class ZerodhaBroker(BaseBroker):
    broker_name = "zerodha"
    supports_proxy = True

    def validate_credentials(self, proxy_config=None):
        if not get_access_token(self.broker_details):
            return {"status": "failed", "message": "Missing Zerodha access token."}
        if not self.broker_details.broker_API_KEY:
            return {"status": "failed", "message": "Missing Zerodha API key."}
        return {"status": "success"}

    def place_order(self, payload, proxy_config=None):
        order = get_order_payload(payload)
        order, open_position, close_error = prepare_close_order_from_open_position(
            self.broker_details.client, order, self.broker_name
        )
        if close_error:
            return close_error
        values = common_order_kwargs(order)
        response = place_zerodha_orders(
            values["LivePrice"],
            values["group_service"],
            get_access_token(self.broker_details),
            self.broker_details.broker_API_KEY,
            build_trade_symbol(order, self.broker_name),
            values["transaction_type"],
            values["symbol"],
            values["quantity"],
            values["strategy"],
            values["ordertype"],
            values["product_type"],
            values["price"],
            self.broker_details.client,
            values["Lots"],
            values["Entry_type"],
            values["Exit_type"],
            values["Entry_price"],
            values["Exit_price"],
            values["EntryQty"],
            values["ExitQty"],
            values["webhook_signal"],
            broker_order_exchange(order, self.broker_name),
            values["Segment"],
            values["Index_Symbol"],
            values["triggerPrice"],
            values["trade_order_status"],
            values["history_id"],
            proxy_config=proxy_config,
            buffer_percentage=values["buffer_percentage"],
        )
        mark_open_position_closed(open_position, response)
        return response

    def get_orderbook(self, proxy_config=None):
        proxy_config = self.require_proxy_config(proxy_config)
        kite = KiteConnect(api_key=self.broker_details.broker_API_KEY, proxies=proxy_config)
        kite.set_access_token(get_access_token(self.broker_details))
        return kite.orders()

    def get_positions(self, proxy_config=None):
        proxy_config = self.require_proxy_config(proxy_config)
        kite = KiteConnect(api_key=self.broker_details.broker_API_KEY, proxies=proxy_config)
        kite.set_access_token(get_access_token(self.broker_details))
        return kite.positions()
