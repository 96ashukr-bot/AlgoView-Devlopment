from __future__ import annotations

from main.angleapi_upgraded import (
    cancel_angel_one_order,
    get_angel_one_holdings,
    get_angel_one_order_book,
    get_angel_one_positions,
    place_angel_one_order,
)
from main.brokers.base import BaseBroker


class AngelOneBroker(BaseBroker):
    broker_name = "angel one"
    supports_proxy = True

    def validate_credentials(self, proxy_config=None):
        credentials = self.broker_details.get_angel_one_login_credentials()
        missing = [key for key, value in credentials.items() if key in {"client_code", "api_key"} and not value]
        if missing:
            return {"status": "failed", "message": f"Missing Angel One credentials: {', '.join(missing)}"}
        return {"status": "success"}

    def place_order(self, payload, proxy_config=None):
        order = payload.get("order", payload)
        return place_angel_one_order(
            broker_details=self.broker_details,
            symbol=order.get("symbol") or order.get("underlying") or order.get("Index_Symbol"),
            strike=str(order.get("strike") or order.get("strike_price") or ""),
            option_type=order.get("option_type") or order.get("Type"),
            quantity=int(order.get("quantity") or 0),
            transaction_type=str(order.get("transaction_type") or "").upper(),
            buffer_percentage=float(order.get("buffer_percentage") or self.broker_details.buffer_percentage or 2.5),
            order_type=order.get("order_type") or order.get("ordertype") or "LIMIT",
            price=order.get("price"),
            exchange=order.get("exchange") or order.get("Exchange") or "NFO",
            product_type=order.get("product_type") or order.get("product") or "INTRADAY",
            request_id=order.get("request_id") or order.get("idempotency_key"),
            proxy_config=proxy_config,
        )

    def cancel_order(self, payload, proxy_config=None):
        order_id = payload.get("order_id") or payload.get("orderid")
        if not order_id:
            return {"status": "error", "message": "Angel One order_id is required"}
        return cancel_angel_one_order(
            self.broker_details,
            order_id=str(order_id),
            variety=payload.get("variety") or "NORMAL",
            proxy_config=proxy_config,
        )

    def get_orderbook(self, proxy_config=None):
        return get_angel_one_order_book(self.broker_details, proxy_config=proxy_config)

    def get_positions(self, proxy_config=None):
        return get_angel_one_positions(self.broker_details, proxy_config=proxy_config)

    def get_holdings(self, proxy_config=None):
        return get_angel_one_holdings(self.broker_details, proxy_config=proxy_config)
