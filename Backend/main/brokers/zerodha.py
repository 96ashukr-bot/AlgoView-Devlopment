from __future__ import annotations

import re

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
        if open_position is not None and str(order.get("transaction_type") or "").upper() == "SELL":
            live_position = self._matching_live_position(order, proxy_config=proxy_config)
            if live_position is None:
                return {
                    "data": {
                        "status": "Failed",
                        "message": "Matching Zerodha broker position could not be verified; exit was not submitted.",
                        "error_code": "BROKER_POSITION_NOT_FOUND",
                    }
                }
            live_quantity = int(float(live_position.get("quantity") or 0))
            if live_quantity <= 0:
                response = {
                    "data": {
                        "status": "reconciled_closed",
                        "message": "Matching Zerodha broker position was already flat; panel reconciled without another SELL.",
                        "error_code": "POSITION_ALREADY_FLAT",
                        "filled_quantity": int(open_position.EntryQty or order.get("quantity") or 0),
                        "resolved_trading_symbol": live_position.get("tradingsymbol"),
                        "instrument_token": live_position.get("instrument_token"),
                        "product_type": live_position.get("product"),
                    }
                }
                mark_open_position_closed(open_position, response)
                return response
            order["quantity"] = min(int(order.get("quantity") or live_quantity), live_quantity)
            order["product_type"] = live_position.get("product") or order.get("product_type")
            order["product"] = order["product_type"]
            order["original_broker_instrument_key"] = live_position.get("instrument_token")
            order["original_broker_trading_symbol"] = live_position.get("tradingsymbol")
            order["original_broker_exchange"] = live_position.get("exchange")
            order["trade_symbol"] = live_position.get("tradingsymbol")
            order["trading_symbol"] = live_position.get("tradingsymbol")
            order["tradingsymbol"] = live_position.get("tradingsymbol")
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

    @staticmethod
    def _compact(value):
        return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())

    def _matching_live_position(self, order, proxy_config=None):
        positions = self.get_positions(proxy_config=proxy_config)
        records = positions.get("net", []) if isinstance(positions, dict) else []
        target_token = str(order.get("original_broker_instrument_key") or "").strip()
        target_symbol = self._compact(
            order.get("original_broker_trading_symbol")
            or order.get("tradingsymbol")
            or order.get("trading_symbol")
            or order.get("trade_symbol")
        )
        underlying = self._compact(order.get("symbol") or order.get("underlying") or order.get("Index_Symbol"))
        option_type = str(order.get("option_type") or order.get("Type") or "").upper()
        try:
            strike = str(int(float(order.get("strike") or order.get("strike_price"))))
        except (TypeError, ValueError):
            strike = ""

        fallback = None
        for record in records:
            record_symbol = self._compact(record.get("tradingsymbol"))
            record_token = str(record.get("instrument_token") or "").strip()
            if target_token and record_token == target_token:
                return record
            if target_symbol and record_symbol == target_symbol:
                return record
            match = re.search(r"(\d+)(CE|PE)$", record_symbol)
            if (
                match
                and underlying
                and record_symbol.startswith(underlying)
                and match.group(1) == strike
                and match.group(2) == option_type
            ):
                fallback = record
        return fallback

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
