from __future__ import annotations

from types import SimpleNamespace

from main.brokers.base import BaseBroker
from main.brokers.utils import build_trade_symbol, common_order_kwargs, get_access_token, get_order_payload
from main.fivepaisa import place_5paisa_order


class FivePaisaBroker(BaseBroker):
    broker_name = "5paisa"

    def validate_credentials(self):
        if not get_access_token(self.broker_details):
            return {"status": "failed", "message": "Missing 5Paisa access token."}
        if not self.broker_details.broker_API_KEY:
            return {"status": "failed", "message": "Missing 5Paisa API key."}
        return {"status": "success"}

    def place_order(self, payload):
        order = get_order_payload(payload)
        values = common_order_kwargs(order)
        trade_context = SimpleNamespace(symbol=values["symbol"], broker=self.broker_name)
        return place_5paisa_order(
            values["LivePrice"],
            values["group_service"],
            self.broker_details.broker_API_KEY,
            get_access_token(self.broker_details),
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
            values["trade_order_status"],
            values["Entry_type"],
            values["Exit_type"],
            values["Entry_price"],
            values["Exit_price"],
            values["EntryQty"],
            values["ExitQty"],
            values["webhook_signal"],
            values["Exchange"],
            values["Segment"],
            values["Index_Symbol"],
            values["triggerPrice"],
            trade_context,
            values["history_id"],
        )
