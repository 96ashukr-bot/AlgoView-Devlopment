from __future__ import annotations

from main.brokers.base import BaseBroker
from main.brokers.utils import build_trade_symbol, common_order_kwargs, get_access_token, get_order_payload
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
        values = common_order_kwargs(order)
        return place_zerodha_orders(
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
            values["Exchange"],
            values["Segment"],
            values["Index_Symbol"],
            values["triggerPrice"],
            values["trade_order_status"],
            values["history_id"],
            proxy_config=proxy_config,
        )
