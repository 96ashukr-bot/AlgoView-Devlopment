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
        values = common_order_kwargs(order)
        trade_symbol = build_trade_symbol(order, self.broker_name)

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
            values["webhook_signal"],
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
