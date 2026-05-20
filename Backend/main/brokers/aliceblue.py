from __future__ import annotations

from django.utils import timezone

from main.Alice_Blue_Api import get_alice_a3_orderbook, get_alice_saved_session, place_alice_orders
from main.brokers.base import BaseBroker
from main.brokers.utils import build_trade_symbol, get_access_token


class AliceBlueBroker(BaseBroker):
    broker_name = "alice blue"
    supports_proxy = True

    def validate_credentials(self, proxy_config=None):
        if not self.broker_details.broker_API_KEY or not self.broker_details.broker_API_UID:
            return {"status": "failed", "message": "Missing Alice Blue API key or user id."}
        access_token = get_access_token(self.broker_details)
        if not access_token:
            return {"status": "failed", "message": "Alice Blue session token is missing. Connect to Alice Blue again before trading."}
        expiry = getattr(self.broker_details, "access_token_expiry", None)
        if expiry:
            if timezone.is_naive(expiry):
                expiry = timezone.make_aware(expiry)
            if expiry <= timezone.now():
                return {"status": "failed", "message": "Alice Blue session token has expired. Connect to Alice Blue again through the assigned proxy before trading."}
        return {"status": "success"}

    def place_order(self, payload, proxy_config=None):
        order = payload.get("order", payload)
        trade_symbol = (
            order.get("trade_symbol")
            or order.get("trading_symbol")
            or order.get("tradingsymbol")
            or build_trade_symbol(order, self.broker_name)
        )
        return place_alice_orders(
            order.get("LivePrice"),
            order.get("group_service"),
            self.broker_details.broker_API_KEY,
            self.broker_details.broker_API_UID,
            trade_symbol,
            str(order.get("transaction_type") or "").upper(),
            order.get("symbol"),
            int(order.get("quantity") or 0),
            order.get("strategy"),
            order.get("order_type") or order.get("ordertype") or "LIMIT",
            order.get("product_type") or order.get("product"),
            order.get("price"),
            self.broker_details.client,
            order.get("Lots") or 1,
            order.get("trade_order_status"),
            order.get("Entry_type"),
            order.get("Exit_type"),
            order.get("Entry_price"),
            order.get("Exit_price"),
            order.get("EntryQty"),
            order.get("ExitQty"),
            order.get("webhook_signal"),
            order.get("Exchange") or order.get("exchange"),
            order.get("Segment"),
            order.get("Index_Symbol"),
            order.get("history_id"),
            order.get("triggerPrice"),
            proxy_config=proxy_config,
            session_id=get_access_token(self.broker_details),
            allow_direct_node_execution=bool(payload.get("_allow_direct_node_execution")),
        )

    def get_orderbook(self, proxy_config=None):
        validation = self.validate_credentials(proxy_config=proxy_config)
        if validation.get("status") != "success":
            return validation
        alice, error = get_alice_saved_session(
            self.broker_details.broker_API_UID,
            self.broker_details.broker_API_KEY,
            get_access_token(self.broker_details),
            proxy_config=proxy_config,
            return_error=True,
        )
        if not alice:
            return {"status": "failed", "message": error or "Alice Blue saved session could not be prepared."}
        response = get_alice_a3_orderbook(get_access_token(self.broker_details), proxy_config=proxy_config)
        status = str(response.get("stat") or response.get("status") or "").strip().lower() if isinstance(response, dict) else ""
        if status in {"ok", "success"}:
            return {"status": "success", "response": response}
        return {
            "status": "failed",
            "message": response.get("emsg") if isinstance(response, dict) else str(response),
            "response": response,
        }
