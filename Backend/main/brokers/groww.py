from __future__ import annotations

from main.brokers.base import BaseBroker
from main.brokers.position_guard import mark_open_position_closed, prepare_close_order_from_open_position
from main.brokers.utils import broker_order_exchange, build_trade_symbol, common_order_kwargs, get_access_token, get_order_payload, order_value
from main.groww import place_groww_orders


class GrowwBroker(BaseBroker):
    broker_name = "groww"
    supports_proxy = True

    def validate_credentials(self, proxy_config=None):
        if not get_access_token(self.broker_details):
            return {"status": "failed", "message": "Missing Groww API auth token."}
        return {"status": "success"}

    def place_order(self, payload, proxy_config=None):
        order = get_order_payload(payload)
        order, open_position, close_error = prepare_close_order_from_open_position(
            self.broker_details.client, order, self.broker_name
        )
        if close_error:
            return close_error
        values = common_order_kwargs(order)

        response = place_groww_orders(
            values["LivePrice"],
            values["group_service"],
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
            day=order_value(order, "day"),
            month=order_value(order, "month"),
            fullyear=order_value(order, "fullyear", "year"),
            strike=order_value(order, "strike", "strike_price"),
            option_type=order_value(order, "option_type", "Type"),
            order_params=order,
            proxy_config=proxy_config,
        )
        mark_open_position_closed(open_position, response)
        return response
