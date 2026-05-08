from __future__ import annotations

from main.Alice_Blue_Api import place_alice_orders
from main.brokers.base import BaseBroker


class AliceBlueBroker(BaseBroker):
    broker_name = "alice blue"

    def validate_credentials(self):
        if not self.broker_details.broker_API_KEY or not self.broker_details.broker_API_UID:
            return {"status": "failed", "message": "Missing Alice Blue API key or user id."}
        return {"status": "success"}

    def place_order(self, payload):
        order = payload.get("order", payload)
        return place_alice_orders(
            order.get("LivePrice"),
            order.get("group_service"),
            self.broker_details.broker_API_KEY,
            self.broker_details.broker_API_UID,
            order.get("trading_symbol") or order.get("symbol"),
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
        )
