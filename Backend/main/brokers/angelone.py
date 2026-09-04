from __future__ import annotations

from datetime import datetime

from main.angleapi_upgraded import (
    cancel_angel_one_order,
    get_angel_one_holdings,
    get_angel_one_order_book,
    get_angel_one_positions,
    place_angel_one_order,
)
from main.brokers.base import BaseBroker
from main.brokers.exchange_mapping import normalize_broker_exchange
from main.brokers.position_guard import mark_open_position_closed, prepare_close_order_from_open_position


def _parse_expiry_override(order):
    expiry = order.get("expiry") or order.get("expiry_date")
    if expiry:
        expiry_text = str(expiry).split("T", 1)[0]
        for date_format in ("%Y-%m-%d", "%d%b%Y", "%d%b%y"):
            try:
                return datetime.strptime(expiry_text.upper(), date_format)
            except ValueError:
                continue

    day = order.get("day")
    month = order.get("month")
    fullyear = order.get("fullyear") or order.get("full_year")
    if day and month and fullyear:
        try:
            return datetime.strptime(f"{str(day).zfill(2)}{str(month)[:3].upper()}{fullyear}", "%d%b%Y")
        except ValueError:
            return None
    return None


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
        nested_order_params = order.get("order_params") if isinstance(order.get("order_params"), dict) else {}
        order, open_position, close_error = prepare_close_order_from_open_position(
            self.broker_details.client, order, self.broker_name
        )
        if close_error:
            return close_error

        transaction_type = str(order.get("transaction_type") or "").upper()
        if transaction_type == "SELL":
            cancellation_error = self._cancel_matching_pending_exits(order, proxy_config=proxy_config)
            if cancellation_error:
                return cancellation_error
        response = place_angel_one_order(
            broker_details=self.broker_details,
            symbol=order.get("symbol") or order.get("underlying") or order.get("Index_Symbol"),
            strike=str(order.get("strike") or order.get("strike_price") or ""),
            option_type=order.get("option_type") or order.get("Type"),
            quantity=int(order.get("quantity") or 0),
            transaction_type=str(order.get("transaction_type") or "").upper(),
            buffer_percentage=float(
                order.get("buffer_percentage")
                if order.get("buffer_percentage") is not None
                else (
                    self.broker_details.buffer_percentage
                    if self.broker_details.buffer_percentage is not None
                    else 0.001
                )
            ),
            order_type=order.get("order_type") or order.get("ordertype") or "LIMIT",
            price=order.get("price"),
            exchange=normalize_broker_exchange(
                self.broker_name,
                exchange=order.get("exchange") or order.get("Exchange"),
                underlying=order.get("symbol") or order.get("underlying") or order.get("Index_Symbol"),
            ),
            product_type=order.get("product_type") or order.get("product") or "INTRADAY",
            request_id=order.get("request_id") or order.get("idempotency_key"),
            expiry_override=_parse_expiry_override(order),
            proxy_config=proxy_config,
            symbol_token=order.get("symboltoken") or nested_order_params.get("symboltoken"),
            trading_symbol=(
                order.get("broker_tradingsymbol")
                or nested_order_params.get("broker_tradingsymbol")
                or order.get("tradingsymbol")
                or nested_order_params.get("tradingsymbol")
            ),
        )
        mark_open_position_closed(open_position, response)
        return response

    def _cancel_matching_pending_exits(self, order, proxy_config=None):
        """Release quantity reserved by an older, unfilled exit before replacing it.

        Angel One treats a second SELL as a new short while an earlier SELL still
        reserves the long position.  Only exact-contract, unfilled SELL orders are
        cancelled; a partial fill or an ambiguous contract fails closed.
        """
        nested = order.get("order_params") if isinstance(order.get("order_params"), dict) else {}
        trading_symbol = str(
            order.get("broker_tradingsymbol")
            or order.get("original_broker_trading_symbol")
            or nested.get("broker_tradingsymbol")
            or order.get("tradingsymbol")
            or nested.get("tradingsymbol")
            or order.get("trading_symbol")
            or ""
        ).strip().upper()
        symbol_token = str(
            order.get("symboltoken")
            or order.get("original_broker_instrument_key")
            or nested.get("symboltoken")
            or ""
        ).strip()
        product_type = str(order.get("product_type") or order.get("product") or "INTRADAY").strip().upper()
        normalized_product = {"MIS": "INTRADAY", "INTRA": "INTRADAY"}.get(product_type, product_type)
        if not trading_symbol or not symbol_token:
            return None

        result = self.get_orderbook(proxy_config=proxy_config)
        if result.get("status") != "success":
            return {
                "data": {
                    "status": "Failed",
                    "message": "Could not verify pending Angel One exit orders before submitting the replacement exit.",
                }
            }

        pending_statuses = {"open", "pending", "put order req received", "trigger pending", "validation pending"}
        for broker_order in result.get("orders") or []:
            if not isinstance(broker_order, dict):
                continue
            if str(broker_order.get("transactiontype") or "").upper() != "SELL":
                continue
            if str(broker_order.get("tradingsymbol") or "").upper() != trading_symbol:
                continue
            if str(broker_order.get("symboltoken") or "") != symbol_token:
                continue
            broker_product = str(broker_order.get("producttype") or "").upper()
            broker_product = {"MIS": "INTRADAY", "INTRA": "INTRADAY"}.get(broker_product, broker_product)
            if broker_product and broker_product != normalized_product:
                continue
            status = str(broker_order.get("orderstatus") or broker_order.get("status") or "").strip().lower()
            if status not in pending_statuses:
                continue
            try:
                filled = int(float(broker_order.get("filledshares") or 0))
            except (TypeError, ValueError):
                filled = 0
            if filled:
                return {
                    "data": {
                        "status": "Failed",
                        "message": "A matching Angel One exit is partially filled. Reconciliation is required before another exit.",
                    }
                }
            order_id = broker_order.get("orderid") or broker_order.get("order_id")
            if not order_id:
                return {
                    "data": {
                        "status": "Failed",
                        "message": "A matching pending Angel One exit has no broker order ID and cannot be replaced safely.",
                    }
                }
            cancelled = self.cancel_order(
                {"order_id": str(order_id), "variety": broker_order.get("variety") or "NORMAL"},
                proxy_config=proxy_config,
            )
            if cancelled.get("status") != "success":
                return {
                    "data": {
                        "status": "Failed",
                        "message": cancelled.get("message") or "The matching pending Angel One exit could not be cancelled.",
                    }
                }
        return None

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
