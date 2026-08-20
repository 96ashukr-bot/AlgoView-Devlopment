from __future__ import annotations

import json

from dhanhq import dhanhq

from main.brokers.base import BaseBroker
from main.brokers.position_guard import mark_open_position_closed, prepare_close_order_from_open_position
from main.brokers.utils import broker_order_exchange, build_dhan_expiry_date, build_trade_symbol, common_order_kwargs, get_access_token, get_order_payload
from main.dhanapi import place_dhan_orders


class DhanBroker(BaseBroker):
    broker_name = "dhan"
    supports_proxy = True

    def validate_credentials(self, proxy_config=None):
        if not get_access_token(self.broker_details):
            return {"status": "failed", "message": "Missing Dhan access token."}
        if not (self.broker_details.broker_API_UID or self.broker_details.broker_Demate_User_Name):
            return {"status": "failed", "message": "Missing Dhan client id."}
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
                return {"data": {"status": "Failed", "message": "Matching Dhan broker position could not be verified; exit was not submitted.", "error_code": "BROKER_POSITION_NOT_FOUND"}}
            try:
                live_net_quantity = int(float(live_position.get("netQty") or 0))
            except (TypeError, ValueError):
                live_net_quantity = 0
            if live_net_quantity <= 0:
                return {"data": {"status": "Failed", "message": "Matching Dhan broker position is already flat.", "error_code": "POSITION_ALREADY_FLAT"}}
            order["quantity"] = min(int(order.get("quantity") or live_net_quantity), live_net_quantity)
            order["original_broker_security_id"] = live_position.get("securityId")
            order["original_broker_trading_symbol"] = live_position.get("tradingSymbol")
            order["product_type"] = live_position.get("productType") or order.get("product_type")
            order["product"] = order["product_type"]
        values = common_order_kwargs(order)
        client_id = self.broker_details.broker_API_UID or self.broker_details.broker_Demate_User_Name
        response = place_dhan_orders(
            build_dhan_expiry_date(order),
            values["LivePrice"],
            values["group_service"],
            get_access_token(self.broker_details),
            client_id,
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
            security_id_override=(order.get("original_broker_security_id") if str(values["transaction_type"]).upper() == "SELL" else None),
        )
        mark_open_position_closed(open_position, response)
        return response

    @staticmethod
    def _compact_symbol(value):
        return "".join(ch for ch in str(value or "").upper() if ch.isalnum())

    @classmethod
    def _position_records(cls, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (TypeError, ValueError, json.JSONDecodeError):
                return []
        if isinstance(value, (list, tuple)):
            records = []
            for item in value:
                records.extend(cls._position_records(item))
            return records
        if not isinstance(value, dict):
            return []
        if any(key in value for key in ("securityId", "tradingSymbol", "netQty")):
            return [value]
        records = []
        for key, nested in value.items():
            if key not in {"status", "remarks", "message", "errorCode"}:
                records.extend(cls._position_records(nested))
        return records

    def _matching_live_position(self, order, proxy_config=None):
        security_id = str(order.get("original_broker_security_id") or order.get("security_id") or "").strip()
        target_symbol = self._compact_symbol(order.get("original_broker_trading_symbol") or order.get("tradingsymbol") or order.get("trading_symbol") or order.get("trade_symbol"))
        positions = self._position_records(self.get_positions(proxy_config=proxy_config))
        matches = [position for position in positions if (security_id and str(position.get("securityId") or "").strip() == security_id) or (target_symbol and self._compact_symbol(position.get("tradingSymbol")) == target_symbol)]
        for position in matches:
            try:
                if int(float(position.get("netQty") or 0)) > 0:
                    return position
            except (TypeError, ValueError):
                pass
        return matches[0] if matches else None

    def get_order_details(self, order_id, trade_order=None, proxy_config=None):
        client_id = self.broker_details.broker_API_UID or self.broker_details.broker_Demate_User_Name
        token = get_access_token(self.broker_details)
        if not client_id or not token:
            return {"status": "failure", "remarks": "Missing Dhan client id or access token.", "data": ""}
        dhan = dhanhq(client_id, token)
        if proxy_config:
            dhan.session.proxies.update(proxy_config)
        return dhan.get_order_by_id(str(order_id))

    def _client(self, proxy_config=None):
        client_id = self.broker_details.broker_API_UID or self.broker_details.broker_Demate_User_Name
        token = get_access_token(self.broker_details)
        if not client_id or not token:
            return None
        dhan = dhanhq(client_id, token)
        if proxy_config:
            dhan.session.proxies.update(self.require_proxy_config(proxy_config))
        return dhan

    def get_positions(self, proxy_config=None):
        dhan = self._client(proxy_config=proxy_config)
        return dhan.get_positions() if dhan else {
            "status": "failure",
            "remarks": "Missing Dhan client id or access token.",
            "data": "",
        }

    def get_orderbook(self, proxy_config=None):
        dhan = self._client(proxy_config=proxy_config)
        return dhan.get_order_list() if dhan else {
            "status": "failure",
            "remarks": "Missing Dhan client id or access token.",
            "data": "",
        }
