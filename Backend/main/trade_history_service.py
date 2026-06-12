from datetime import datetime
from decimal import Decimal
import re

from django.utils import timezone

from main.models import ClientTradeSetting, Tradeorderhistory

NON_FAILURE_ORDER_STATUSES = {
    "accepted",
    "accepted_by_node",
    "amo req received",
    "complete",
    "completed",
    "open",
    "open pending",
    "pending",
    "placed",
    "put order req received",
    "success",
    "sent_to_node",
    "transit",
    "validation pending",
}

TRANSIENT_ORDER_MESSAGES = {
    "order is placing by place order broker !!",
    "order routed to execution node.",
}


def _serialize_trade_history_value(value):
    if isinstance(value, dict):
        return {key: _serialize_trade_history_value(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_serialize_trade_history_value(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _first_non_empty(*values):
    for value in values:
        if value not in (None, "", [], {}, ()):
            return value
    return None


def _normalize_status_value(value):
    return str(value or "").strip().lower()


def _is_non_failure_status(*values):
    return any(_normalize_status_value(value) in NON_FAILURE_ORDER_STATUSES for value in values)


def _is_transient_order_message(value):
    return _normalize_status_value(value) in TRANSIENT_ORDER_MESSAGES


def resolve_trade_failure_reason(order_status, trade_order_status, reason):
    if reason in (None, "", [], {}, ()):
        return None
    if isinstance(reason, (dict, list)):
        reason = str(reason)

    if _is_transient_order_message(reason):
        return None
    if _is_non_failure_status(order_status, trade_order_status):
        return None
    return str(reason)


def _compact_symbol(value):
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def _format_compact_contract_symbol(value):
    compact = _compact_symbol(value)
    if not compact:
        return None

    spaced_match = re.match(r"^([A-Z]+)(\d+)(CE|PE)(\d{2})([A-Z]{3})(\d{2,4})$", compact)
    if spaced_match:
        symbol, strike, option_type, day, month, year = spaced_match.groups()
        return f"{symbol}{strike}{option_type}{day}{month}{year[-2:]}"

    broker_match = re.match(r"^([A-Z]+)(\d{2})([A-Z]{3})(\d+)(CE|PE)$", compact)
    if broker_match:
        symbol, day, month, strike, option_type = broker_match.groups()
        return f"{symbol}{strike}{option_type}{day}{month}"

    if "CE" in compact or "PE" in compact:
        return compact
    return None


def _extract_response_contract_symbol(response_payload):
    if not isinstance(response_payload, dict):
        return None

    candidates = []
    data = response_payload.get("data")
    if isinstance(data, list):
        candidates.extend(item for item in data if isinstance(item, dict))
    elif isinstance(data, dict):
        candidates.append(data)

    meta = response_payload.get("meta")
    if isinstance(meta, dict):
        candidates.append(meta)

    for candidate in candidates:
        for key in ("trading_symbol", "tradingsymbol", "tradingsymbol_name", "symbol"):
            contract_symbol = _format_compact_contract_symbol(candidate.get(key))
            if contract_symbol:
                return contract_symbol
    return None


def _resolved_contract_symbol(trade_symbol, response_payload, order_payload, fallback_symbol):
    return _first_non_empty(
        _format_compact_contract_symbol(trade_symbol),
        _extract_response_contract_symbol(response_payload),
        _format_compact_contract_symbol(order_payload.get("tradingsymbol") if isinstance(order_payload, dict) else None),
        _format_compact_contract_symbol(order_payload.get("trading_symbol") if isinstance(order_payload, dict) else None),
        _format_compact_contract_symbol(order_payload.get("trade_symbol") if isinstance(order_payload, dict) else None),
        trade_symbol,
        fallback_symbol,
    )


def _to_decimal(value):
    if value in (None, "", "None"):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _to_int(value):
    if value in (None, "", "None"):
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def _extract_signal_time(webhook_signal, *keys):
    if not isinstance(webhook_signal, dict):
        return None

    for key in keys:
        value = webhook_signal.get(key)
        if value in (None, "", "None"):
            continue
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            candidate = value.strip()
            if not candidate:
                continue
            try:
                parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
                if timezone.is_naive(parsed):
                    parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
                return parsed
            except Exception:
                continue
    return None


def _price_from_payload(payload, *keys):
    if not isinstance(payload, dict):
        return None
    for key in keys:
        value = payload.get(key)
        price = _to_decimal(value)
        if price is not None and price > 0:
            return price
    return None


def _effective_trade_price(nested_response, meta_response, order_payload, entry_price, exit_price, is_exit_signal):
    nested_response = nested_response if isinstance(nested_response, dict) else {}
    meta_response = meta_response if isinstance(meta_response, dict) else {}
    order_payload = order_payload if isinstance(order_payload, dict) else {}

    fill_price = (
        _price_from_payload(nested_response, "average_price", "averageprice", "traded_price", "tradedPrice", "executed_price")
        or _price_from_payload(meta_response, "average_price", "averageprice", "traded_price", "tradedPrice", "executed_price")
    )
    if fill_price is not None:
        return fill_price

    status = _normalize_status_value(nested_response.get("status") or meta_response.get("status"))
    if status in {"complete", "completed", "success", "traded"}:
        complete_price = _price_from_payload(nested_response, "price") or _price_from_payload(meta_response, "price")
        if complete_price is not None:
            return complete_price

    reference_price = (
        _price_from_payload(nested_response, "reference_price", "ltp")
        or _price_from_payload(meta_response, "reference_price", "ltp")
    )
    if reference_price is not None:
        return reference_price

    return (
        _to_decimal(exit_price if is_exit_signal else entry_price)
        or _price_from_payload(order_payload, "average_price", "averageprice", "traded_price", "tradedPrice", "executed_price")
        or (None if status not in {"complete", "completed", "success", "traded"} else _price_from_payload(order_payload, "price"))
    )


def save_trade_order_history(*args, **kwargs):
    logger = kwargs.pop("logger", None)
    try:
        if len(args) < 22:
            if logger:
                logger.error("save_trade_order_history called with insufficient arguments: %s", len(args))
            return None

        (
            LivePrice,
            group_service,
            transaction_type,
            trade_order_status,
            user,
            trade_symbol,
            order_id,
            status,
            res_data,
            message,
            strategy,
            Entry_type,
            Exit_type,
            Entry_price,
            Exit_price,
            EntryQty,
            ExitQty,
            webhook_signal,
            Exchange,
            Segment,
            Index_Symbol,
            order_params,
        ) = args[:22]

        broker = kwargs.get("broker")
        history_id = kwargs.get("history_id")
        trade_setting = kwargs.get("trade_setting")
        trade_setting_id = kwargs.get("trade_setting_id")
        sltp_metadata = kwargs.get("sltp_metadata") if isinstance(kwargs.get("sltp_metadata"), dict) else {}

        response_payload = _serialize_trade_history_value(res_data)
        order_payload = _serialize_trade_history_value(order_params if isinstance(order_params, dict) else {})
        nested_response = response_payload.get("data", {}) if isinstance(response_payload, dict) else {}
        meta_response = response_payload.get("meta", {}) if isinstance(response_payload, dict) else {}
        contract_symbol = _resolved_contract_symbol(trade_symbol, response_payload, order_payload, Index_Symbol)

        normalized_transaction_type = str(transaction_type or "").upper()
        is_exit_signal = "SELL" in normalized_transaction_type
        signal_entry_time = _extract_signal_time(
            webhook_signal,
            "signal_entry_time",
            "signalEntryTime",
            "entry_time",
            "entryTime",
            "signal_time",
            "signalTime",
        ) or timezone.now()
        signal_exit_time = _extract_signal_time(
            webhook_signal,
            "signal_exit_time",
            "signalExitTime",
            "exit_time",
            "exitTime",
        )

        effective_price = _effective_trade_price(
            nested_response,
            meta_response,
            order_payload,
            Entry_price,
            Exit_price,
            is_exit_signal,
        )
        live_price_value = _to_decimal(
            _first_non_empty(
                nested_response.get("ltp") if isinstance(nested_response, dict) else None,
                meta_response.get("ltp") if isinstance(meta_response, dict) else None,
                LivePrice,
            )
        )
        effective_quantity = _to_int(
            _first_non_empty(
                nested_response.get("filled_quantity") if isinstance(nested_response, dict) else None,
                nested_response.get("filled_qty") if isinstance(nested_response, dict) else None,
                nested_response.get("quantity") if isinstance(nested_response, dict) else None,
                nested_response.get("qty") if isinstance(nested_response, dict) else None,
                meta_response.get("quantity") if isinstance(meta_response, dict) else None,
                meta_response.get("qty") if isinstance(meta_response, dict) else None,
                order_payload.get("quantity") if isinstance(order_payload, dict) else None,
                order_payload.get("qty") if isinstance(order_payload, dict) else None,
                ExitQty if is_exit_signal else EntryQty,
            )
        )

        resolved_status = _first_non_empty(
            status,
            nested_response.get("status") if isinstance(nested_response, dict) else None,
            response_payload.get("status") if isinstance(response_payload, dict) else None,
            "Failed",
        )
        resolved_message = _first_non_empty(
            message,
            nested_response.get("message") if isinstance(nested_response, dict) else None,
            response_payload.get("message") if isinstance(response_payload, dict) else None,
        )
        resolved_failure_reason = resolve_trade_failure_reason(
            resolved_status,
            trade_order_status,
            resolved_message,
        )
        resolved_order_id = _first_non_empty(
            order_id,
            nested_response.get("order_id") if isinstance(nested_response, dict) else None,
            response_payload.get("order_id") if isinstance(response_payload, dict) else None,
        )

        defaults = {
            "client": user,
            "GroupService": group_service,
            "trading_symbol": trade_symbol,
            "Index_Symbol": contract_symbol,
            "order_id": str(resolved_order_id) if resolved_order_id not in (None, "", "0", 0) else None,
            "order_status": str(resolved_status),
            "response_data": response_payload,
            "failure_reason": resolved_failure_reason,
            "broker": broker,
            "order_params": order_payload,
            "transaction_type": transaction_type,
            "strategy": strategy,
            "Entry_type": Entry_type,
            "Exit_type": Exit_type,
            "Exchange": Exchange,
            "Segment": Segment,
            "Lot": _to_int(
                _first_non_empty(
                    order_payload.get("Lots") if isinstance(order_payload, dict) else None,
                    order_payload.get("lots") if isinstance(order_payload, dict) else None,
                    order_payload.get("lot_size") if isinstance(order_payload, dict) else None,
                )
            ),
            "LivePrice": live_price_value,
            "trade_order_status": trade_order_status or str(resolved_status),
            "webhook_signal": _serialize_trade_history_value(webhook_signal),
        }
        if trade_setting is not None:
            defaults["trade_setting"] = trade_setting
        elif trade_setting_id:
            try:
                defaults["trade_setting"] = ClientTradeSetting.objects.get(id=trade_setting_id)
            except ClientTradeSetting.DoesNotExist:
                pass
        if sltp_metadata:
            defaults["sltp_metadata"] = _serialize_trade_history_value(sltp_metadata)

        if is_exit_signal:
            defaults["Exit_Price"] = effective_price or _to_decimal(Exit_price)
            defaults["ExitQty"] = effective_quantity or _to_int(ExitQty)
            defaults["Exit_status"] = str(resolved_status)
            defaults["SignalExit_time"] = signal_exit_time or timezone.now()
            defaults["SignalEntry_time"] = None
        else:
            defaults["Entry_Price"] = effective_price or _to_decimal(Entry_price)
            defaults["EntryQty"] = effective_quantity or _to_int(EntryQty)
            defaults["Entry_status"] = str(resolved_status)
            defaults["SignalEntry_time"] = signal_entry_time
            defaults["SignalExit_time"] = None

        if history_id:
            history, _ = Tradeorderhistory.objects.get_or_create(
                history_id=str(history_id),
                defaults=defaults,
            )
            for field_name, field_value in defaults.items():
                if field_name in {"SignalEntry_time", "SignalExit_time"}:
                    setattr(history, field_name, field_value)
                    continue
                if field_name == "failure_reason":
                    setattr(history, field_name, field_value)
                    continue
                if field_value in (None, "", {}, []):
                    continue
                setattr(history, field_name, field_value)
            history.save()
            return history

        return Tradeorderhistory.objects.create(**defaults)
    except Exception as exc:
        if logger:
            logger.exception(f"Failed to save trade history: {exc}")
        return None
