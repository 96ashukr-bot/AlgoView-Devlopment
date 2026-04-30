from datetime import datetime
from decimal import Decimal

from django.utils import timezone

from main.models import Tradeorderhistory


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

        response_payload = _serialize_trade_history_value(res_data)
        order_payload = _serialize_trade_history_value(order_params if isinstance(order_params, dict) else {})
        nested_response = response_payload.get("data", {}) if isinstance(response_payload, dict) else {}
        meta_response = response_payload.get("meta", {}) if isinstance(response_payload, dict) else {}

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

        effective_price = _to_decimal(
            _first_non_empty(
                nested_response.get("executed_price") if isinstance(nested_response, dict) else None,
                nested_response.get("price") if isinstance(nested_response, dict) else None,
                nested_response.get("average_price") if isinstance(nested_response, dict) else None,
                nested_response.get("averageprice") if isinstance(nested_response, dict) else None,
                meta_response.get("price") if isinstance(meta_response, dict) else None,
                meta_response.get("executed_price") if isinstance(meta_response, dict) else None,
                meta_response.get("average_price") if isinstance(meta_response, dict) else None,
                meta_response.get("averageprice") if isinstance(meta_response, dict) else None,
                order_payload.get("price") if isinstance(order_payload, dict) else None,
                Entry_price if not is_exit_signal else Exit_price,
            )
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
        resolved_order_id = _first_non_empty(
            order_id,
            nested_response.get("order_id") if isinstance(nested_response, dict) else None,
            response_payload.get("order_id") if isinstance(response_payload, dict) else None,
        )

        defaults = {
            "client": user,
            "GroupService": group_service,
            "trading_symbol": trade_symbol,
            "Index_Symbol": Index_Symbol or trade_symbol,
            "order_id": str(resolved_order_id) if resolved_order_id not in (None, "", "0", 0) else None,
            "order_status": str(resolved_status),
            "response_data": response_payload,
            "failure_reason": resolved_message,
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

        if is_exit_signal:
            defaults["Exit_Price"] = effective_price or _to_decimal(Exit_price)
            defaults["ExitQty"] = effective_quantity or _to_int(ExitQty)
            defaults["Exit_status"] = str(resolved_status)
            defaults["SignalExit_time"] = signal_exit_time or timezone.now()
        else:
            defaults["Entry_Price"] = effective_price or _to_decimal(Entry_price)
            defaults["EntryQty"] = effective_quantity or _to_int(EntryQty)
            defaults["Entry_status"] = str(resolved_status)
            defaults["SignalEntry_time"] = signal_entry_time

        if history_id:
            history, _ = Tradeorderhistory.objects.get_or_create(
                history_id=str(history_id),
                defaults=defaults,
            )
            for field_name, field_value in defaults.items():
                if field_value in (None, "", {}, []):
                    continue
                if field_name == "SignalEntry_time" and getattr(history, field_name, None):
                    continue
                setattr(history, field_name, field_value)
            history.save()
            return history

        return Tradeorderhistory.objects.create(**defaults)
    except Exception as exc:
        if logger:
            logger.exception("Failed to save trade history: %s", exc)
        return None
