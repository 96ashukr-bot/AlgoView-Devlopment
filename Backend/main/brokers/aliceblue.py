from __future__ import annotations

from django.utils import timezone

from main.Alice_Blue_Api import get_alice_a3_orderbook, get_alice_saved_session, place_alice_orders
from main.brokers.base import BaseBroker
from main.brokers.position_guard import mark_open_position_closed, prepare_close_order_from_open_position
from main.brokers.utils import broker_order_exchange, build_trade_symbol, get_access_token


class AliceBlueBroker(BaseBroker):
    broker_name = "alice blue"
    supports_proxy = True

    @staticmethod
    def _normalize_aggregated_fill_response(response, expected_quantity):
        """Treat a broker-confirmed full aggregate fill as completed."""
        if not isinstance(response, dict) or isinstance(response.get("data"), dict):
            return response
        try:
            filled_quantity = int(float(response.get("aggregated_fills") or 0))
            expected_quantity = int(float(expected_quantity or 0))
        except (TypeError, ValueError):
            return response
        if expected_quantity <= 0 or filled_quantity < expected_quantity:
            return response
        return {
            **response,
            "data": {
                "status": "complete",
                "message": "Alice Blue exit fully filled.",
                "filled_quantity": filled_quantity,
            },
        }

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

    def _recover_exit_contract(self, order, proxy_config=None):
        """Recover immutable Alice fields from the broker-confirmed BUY."""
        snapshot = order.get("broker_contract_snapshot")
        if not isinstance(snapshot, dict):
            snapshot = {}
        instrument_id = str(
            order.get("original_broker_instrument_key")
            or order.get("original_broker_symbol_token")
            or snapshot.get("broker_instrument_id")
            or ""
        ).strip()
        original_order_id = str(
            order.get("original_broker_order_id")
            or order.get("matched_open_order_id")
            or snapshot.get("buy_order_id")
            or ""
        ).strip()
        if instrument_id or not original_order_id:
            return instrument_id

        response = get_alice_a3_orderbook(
            get_access_token(self.broker_details), proxy_config=proxy_config
        )
        candidates = response.get("result") if isinstance(response, dict) else None
        for broker_order in candidates if isinstance(candidates, list) else []:
            if str(broker_order.get("brokerOrderId") or "").strip() != original_order_id:
                continue
            if str(broker_order.get("transactionType") or "").upper() != "BUY":
                continue
            instrument_id = str(broker_order.get("instrumentId") or "").strip()
            if not instrument_id:
                continue
            order["original_broker_instrument_key"] = instrument_id
            order["original_broker_trading_symbol"] = (
                broker_order.get("tradingSymbol") or order.get("symbol")
            )
            order["original_broker_exchange"] = (
                broker_order.get("exchange") or order.get("Exchange")
            )
            order["original_broker_product_type"] = (
                broker_order.get("product") or order.get("product_type")
            )
            order["product_type"] = (
                broker_order.get("product") or order.get("product_type")
            )
            return instrument_id
        return ""

    def place_order(self, payload, proxy_config=None):
        order = payload.get("order", payload)
        order, open_position, close_error = prepare_close_order_from_open_position(
            self.broker_details.client, order, self.broker_name
        )
        if close_error:
            return close_error
        is_exit = str(order.get("transaction_type") or "").upper() == "SELL"
        stored_instrument_id = (
            self._recover_exit_contract(order, proxy_config=proxy_config) if is_exit else ""
        )
        if is_exit and not stored_instrument_id:
            return {
                "data": {
                    "status": "Failed",
                    "message": (
                        "Alice Blue exit was blocked because the exact instrumentId "
                        "could not be recovered from the broker-confirmed BUY."
                    ),
                }
            }
        if is_exit and stored_instrument_id:
            # Exact-ID MARKET exits offset the position immediately. Alice
            # treated protected LIMIT exits as fresh shorts in production.
            order["order_type"] = "MARKET"
            order["ordertype"] = "MARKET"
        trade_symbol = (
            order.get("trade_symbol")
            or order.get("trading_symbol")
            or order.get("tradingsymbol")
            or build_trade_symbol(order, self.broker_name)
        )
        response = place_alice_orders(
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
            broker_order_exchange(order, self.broker_name),
            order.get("Segment"),
            order.get("Index_Symbol"),
            order.get("history_id"),
            order.get("triggerPrice"),
            proxy_config=proxy_config,
            session_id=get_access_token(self.broker_details),
            allow_direct_node_execution=bool(payload.get("_allow_direct_node_execution")),
            instrument_id_override=stored_instrument_id,
        )
        response = self._normalize_aggregated_fill_response(response, order.get("quantity"))
        mark_open_position_closed(open_position, response)
        return response

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

    def get_positions(self, proxy_config=None):
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
        try:
            return {"status": "success", "response": alice.get_netwise_positions()}
        except Exception as exc:
            return {"status": "failed", "message": str(exc)}
