import requests

from main.brokers.base import BaseBroker
from main.brokers.position_guard import mark_open_position_closed, prepare_close_order_from_open_position
from main.brokers.utils import broker_order_exchange, build_trade_symbol, common_order_kwargs, get_access_token, get_order_payload
from main.upstock import get_order_details, place_upstox_orders


class UpstoxBroker(BaseBroker):
    broker_name = "upstox"
    supports_proxy = True

    def validate_credentials(self, proxy_config=None):
        if not get_access_token(self.broker_details):
            return {"status": "failed", "message": "Missing Upstox access token."}
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
                return {"data": {"status": "Failed", "message": "Matching Upstox broker position could not be verified; exit was not submitted.", "error_code": "BROKER_POSITION_NOT_FOUND"}}
            try:
                live_quantity = int(float(live_position.get("quantity") or 0))
            except (TypeError, ValueError):
                live_quantity = 0
            if live_quantity <= 0:
                exit_price = live_position.get("sell_price") or live_position.get("day_sell_price")
                response = {
                    "data": {
                        "status": "reconciled_closed",
                        "message": "Matching Upstox broker position was already flat; panel reconciled without submitting another SELL.",
                        "error_code": "POSITION_ALREADY_FLAT",
                        "executed_price": exit_price,
                        "average_fill_price": exit_price,
                        "filled_quantity": int(open_position.EntryQty or order.get("quantity") or 0),
                        "instrument_key": live_position.get("instrument_token"),
                        "resolved_trading_symbol": live_position.get("trading_symbol") or live_position.get("tradingsymbol"),
                        "product_type": live_position.get("product"),
                    }
                }
                mark_open_position_closed(open_position, response)
                return response
            order["quantity"] = min(int(order.get("quantity") or live_quantity), live_quantity)
            order["product_type"] = live_position.get("product") or order.get("product_type")
            order["product"] = order["product_type"]
            order["original_broker_instrument_key"] = live_position.get("instrument_token")
            order["original_broker_trading_symbol"] = live_position.get("trading_symbol") or live_position.get("tradingsymbol")
        values = common_order_kwargs(order)
        trade_symbol = build_trade_symbol(order, self.broker_name)
        webhook_signal = dict(values["webhook_signal"] or {})
        for key in ("order_action", "original_broker_trading_symbol", "original_broker_instrument_key"):
            value = order.get(key)
            if value not in (None, "", "None"):
                webhook_signal[key] = value

        response = place_upstox_orders(
            values["LivePrice"],
            values["group_service"],
            get_access_token(self.broker_details),
            trade_symbol,
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
            webhook_signal,
            broker_order_exchange(order, self.broker_name),
            values["Segment"],
            values["Index_Symbol"],
            values["triggerPrice"],
            values["trade_order_status"],
            values["history_id"],
            proxy_config=proxy_config,
        )
        mark_open_position_closed(open_position, response)
        return response

    @staticmethod
    def _compact_symbol(value):
        return "".join(ch for ch in str(value or "").upper() if ch.isalnum())

    def _matching_live_position(self, order, proxy_config=None):
        target_token = str(order.get("original_broker_instrument_key") or order.get("instrument_key") or "").strip()
        target_symbol = self._compact_symbol(order.get("original_broker_trading_symbol") or order.get("tradingsymbol") or order.get("trading_symbol") or order.get("trade_symbol"))
        response = self.get_positions(proxy_config=proxy_config)
        records = response.get("data") if isinstance(response, dict) else None
        if not isinstance(records, list):
            return None
        matches = []
        underlying = self._compact_symbol(order.get("symbol") or order.get("underlying") or order.get("Index_Symbol"))
        option_type = str(order.get("option_type") or order.get("Type") or "").strip().upper()
        try:
            strike = str(int(float(order.get("strike") or order.get("strike_price"))))
        except (TypeError, ValueError):
            strike = ""
        month = str(order.get("month") or "").strip().upper()[:3]
        year = str(order.get("year") or order.get("fullyear") or "").strip()[-2:]
        for record in records:
            if not isinstance(record, dict):
                continue
            same_token = target_token and str(record.get("instrument_token") or "").strip() == target_token
            record_symbol = self._compact_symbol(record.get("trading_symbol") or record.get("tradingsymbol"))
            same_symbol = target_symbol and record_symbol == target_symbol
            same_contract = bool(
                underlying and strike and option_type in {"CE", "PE"} and month and year
                and record_symbol.startswith(underlying)
                and record_symbol.endswith(f"{strike}{option_type}")
                and f"{year}{month}" in record_symbol
            )
            if same_token or same_symbol or same_contract:
                matches.append(record)
        for record in matches:
            try:
                if int(float(record.get("quantity") or 0)) > 0:
                    return record
            except (TypeError, ValueError):
                continue
        return matches[0] if matches else None

    def get_order_details(self, order_id, trade_order=None, proxy_config=None):
        access_token = get_access_token(self.broker_details)
        if not access_token:
            return {"status": "failed", "message": "Missing Upstox access token."}
        return get_order_details(order_id, access_token, proxy_config=proxy_config)

    def _get(self, path, proxy_config=None):
        access_token = get_access_token(self.broker_details)
        if not access_token:
            return {"status": "failed", "message": "Missing Upstox access token."}
        response = requests.get(
            f"https://api.upstox.com{path}",
            headers={"Accept": "application/json", "Authorization": f"Bearer {access_token}"},
            proxies=self.require_proxy_config(proxy_config),
            timeout=10,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"status": "failed", "message": response.text}
        if response.status_code >= 400 and isinstance(payload, dict):
            payload.setdefault("status", "failed")
        return payload

    def get_positions(self, proxy_config=None):
        return self._get("/v2/portfolio/short-term-positions", proxy_config=proxy_config)

    def get_orderbook(self, proxy_config=None):
        return self._get("/v2/order/retrieve-all", proxy_config=proxy_config)
