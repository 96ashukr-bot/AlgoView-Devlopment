from datetime import datetime
from decimal import Decimal
import re

from django.db import transaction
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
    "sending",
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


def _is_option_trade_symbol(*values):
    for value in values:
        if isinstance(value, dict):
            option_type = str(value.get("option_type") or value.get("Type") or "").strip().upper()
            strike = value.get("strike") if value.get("strike") not in (None, "") else value.get("strike_price")
            if option_type in {"CE", "PE", "CALL", "PUT"} and strike not in (None, ""):
                return True
            value = _first_non_empty(
                value.get("tradingsymbol"),
                value.get("trading_symbol"),
                value.get("resolved_trading_symbol"),
                value.get("symbol"),
                value.get("underlying"),
            )
        normalized = _compact_symbol(value)
        if re.search(r"\d+(?:\.\d+)?(CE|PE)$", normalized):
            return True
    return False


def _format_compact_contract_symbol(value):
    text = str(value or "").strip().upper()
    formatted_match = re.match(
        r"^([A-Z]+)\s+(\d{1,2})(?:ST|ND|RD|TH)?\s+([A-Z]{3})\s+(\d+(?:\.\d+)?)\s+(CE|PE|CALL|PUT)$",
        text,
    )
    if formatted_match:
        symbol, day, month, strike, option_type = formatted_match.groups()
        option_type = {"CALL": "CE", "PUT": "PE"}.get(option_type, option_type)
        year = timezone.localdate().strftime("%y")
        return f"{symbol}{day.zfill(2)}{month}{year}{int(float(strike))}{option_type}"

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

    candidates = [response_payload]
    data = response_payload.get("data")
    if isinstance(data, list):
        candidates.extend(item for item in data if isinstance(item, dict))
    elif isinstance(data, dict):
        candidates.append(data)

    meta = response_payload.get("meta")
    if isinstance(meta, dict):
        candidates.append(meta)

    for candidate in candidates:
        normalized_candidate = {str(key).lower(): value for key, value in candidate.items()}
        for key in ("formattedinstrumentname", "trading_symbol", "tradingsymbol", "tradingsymbol_name", "symbol"):
            contract_symbol = _format_compact_contract_symbol(normalized_candidate.get(key))
            if contract_symbol:
                return contract_symbol
    return None


def _extract_response_contract_details(response_payload):
    if not isinstance(response_payload, dict):
        return None
    for candidate in _walk_payload_dicts(response_payload):
        normalized = {str(key).lower(): value for key, value in candidate.items()}
        formatted = normalized.get("formattedinstrumentname")
        match = re.match(
            r"^([A-Z]+)\s+(\d{1,2})(?:ST|ND|RD|TH)?\s+([A-Z]{3})\s+(\d+(?:\.\d+)?)\s+(CE|PE|CALL|PUT)$",
            str(formatted or "").strip().upper(),
        )
        if not match:
            continue
        underlying, day, month, strike, option_type = match.groups()
        option_type = {"CALL": "CE", "PUT": "PE"}.get(option_type, option_type)
        year = timezone.localdate().year
        expiry = datetime.strptime(f"{day.zfill(2)}{month}{year}", "%d%b%Y").date()
        return {
            "underlying": underlying,
            "strike": float(strike),
            "option_type": option_type,
            "expiry": expiry.isoformat(),
            "resolved_trading_symbol": f"{underlying}{day.zfill(2)}{month}{str(year)[-2:]}{int(float(strike))}{option_type}",
        }
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


def normalize_broker_confirmed_contract(history, save=True):
    details = _extract_response_contract_details(history.response_data)
    if not details:
        return False
    order_payload = dict(history.order_params) if isinstance(history.order_params, dict) else {}
    metadata = dict(history.sltp_metadata) if isinstance(history.sltp_metadata, dict) else {}
    changed = (
        str(order_payload.get("expiry") or "") != details["expiry"]
        or str(metadata.get("expiry") or "") != details["expiry"]
        or history.Index_Symbol != details["resolved_trading_symbol"]
    )
    if not changed:
        return False
    confirmed = {
        "symbol": details["underlying"],
        "underlying": details["underlying"],
        "strike": details["strike"],
        "strike_price": details["strike"],
        "option_type": details["option_type"],
        "expiry": details["expiry"],
        "resolved_trading_symbol": details["resolved_trading_symbol"],
    }
    order_payload.update(confirmed)
    metadata.update(details)
    history.order_params = order_payload
    history.sltp_metadata = metadata
    history.Index_Symbol = details["resolved_trading_symbol"]
    if save:
        history.save(update_fields=["order_params", "sltp_metadata", "Index_Symbol"])
    return True


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


def _walk_payload_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_payload_dicts(child)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_payload_dicts(item)


def _fill_price_from_payload(value):
    for payload in _walk_payload_dicts(value):
        price = _price_from_payload(
            payload,
            "average_price",
            "averageprice",
            "averagePrice",
            "AveragePrice",
            "avg_price",
            "avgPrice",
            "avgTradePrice",
            "averageTradePrice",
            "average_trade_price",
            "averageTradedPrice",
            "average_traded_price",
            "average_fill_price",
            "averageFillPrice",
            "traded_price",
            "tradedPrice",
            "TradedPrice",
            "tradePrice",
            "TradePrice",
            "AverageTradePrice",
            "fill_price",
            "filled_price",
        )
        if price is not None:
            return price
    return None


def _quantity_from_payload(value):
    for payload in _walk_payload_dicts(value):
        quantity = _to_int(
            _first_non_empty(
                payload.get("filled_quantity"),
                payload.get("filledQuantity"),
                payload.get("filled_qty"),
                payload.get("filledQty"),
                payload.get("filledshares"),
                payload.get("filledShares"),
                payload.get("Fillshares"),
                payload.get("quantity"),
                payload.get("Quantity"),
                payload.get("qty"),
                payload.get("Qty"),
            )
        )
        if quantity is not None:
            return quantity
    return None


def _effective_trade_price(nested_response, meta_response, order_payload, entry_price, exit_price, is_exit_signal):
    nested_response = nested_response if isinstance(nested_response, dict) else {}
    meta_response = meta_response if isinstance(meta_response, dict) else {}
    order_payload = order_payload if isinstance(order_payload, dict) else {}

    fill_price = (
        _fill_price_from_payload(nested_response)
        or _fill_price_from_payload(meta_response)
        or _price_from_payload(nested_response, "executed_price")
        or _price_from_payload(meta_response, "executed_price")
    )
    if fill_price is not None:
        return fill_price
    if order_payload.get("defer_fill_price_until_reconciled"):
        return _to_decimal(exit_price if is_exit_signal else entry_price)

    reference_price = (
        _price_from_payload(nested_response, "reference_price", "ltp")
        or _price_from_payload(meta_response, "reference_price", "ltp")
    )
    if reference_price is not None:
        return reference_price

    status = _normalize_status_value(nested_response.get("status") or meta_response.get("status"))
    if status in {"complete", "completed", "success", "traded"}:
        complete_price = _price_from_payload(nested_response, "price") or _price_from_payload(meta_response, "price")
        if complete_price is not None:
            return complete_price

    return (
        _to_decimal(exit_price if is_exit_signal else entry_price)
        or _price_from_payload(
            order_payload,
            "average_price",
            "averageprice",
            "averagePrice",
            "AveragePrice",
            "avg_price",
            "avgPrice",
            "avgTradePrice",
            "averageTradePrice",
            "average_trade_price",
            "averageTradedPrice",
            "average_traded_price",
            "average_fill_price",
            "averageFillPrice",
            "traded_price",
            "tradedPrice",
            "TradedPrice",
            "tradePrice",
            "TradePrice",
            "AverageTradePrice",
            "executed_price",
        )
        or (None if status not in {"complete", "completed", "success", "traded"} else _price_from_payload(order_payload, "price"))
    )


def _find_entry_history_for_exit(user, order_payload, webhook_signal, contract_symbol):
    references = []
    matched_order_ids = []
    for payload in (order_payload, webhook_signal):
        if isinstance(payload, dict):
            references.extend((payload.get("matched_open_history_id"), payload.get("original_history_id")))
            matched_order_ids.append(payload.get("matched_open_order_id"))

    base_queryset = Tradeorderhistory.objects.select_for_update().filter(client=user)
    for reference in references:
        if reference in (None, ""):
            continue
        entry = base_queryset.filter(history_id=str(reference)).first()
        if entry is None and str(reference).isdigit():
            entry = base_queryset.filter(pk=int(reference)).first()
        if entry is not None and entry.Entry_Price is not None:
            return entry

    for order_id in matched_order_ids:
        if order_id in (None, ""):
            continue
        entry = base_queryset.filter(order_id=str(order_id), Entry_Price__isnull=False).first()
        if entry is not None:
            return entry

    compact_contract = _compact_symbol(contract_symbol)
    if not compact_contract or not any(option_type in compact_contract for option_type in ("CE", "PE")):
        return None
    candidates = base_queryset.filter(
        Exit_Price__isnull=True,
        transaction_type__iexact="BUY",
    ).order_by("-id")[:20]
    for candidate in candidates:
        if compact_contract in {
            _compact_symbol(candidate.trading_symbol),
            _compact_symbol(candidate.Index_Symbol),
        }:
            return candidate
    return None


def _merge_completed_exit_into_entry(entry, defaults, response_payload, order_payload, history_id):
    merged_order_params = dict(entry.order_params) if isinstance(entry.order_params, dict) else {}
    merged_order_params["exit"] = {
        "history_id": str(history_id or ""),
        "order_id": defaults.get("order_id"),
        "response": response_payload,
        "order_params": order_payload,
    }
    entry.order_params = merged_order_params
    entry.Exit_Price = defaults.get("Exit_Price")
    entry.ExitQty = defaults.get("ExitQty") or entry.EntryQty
    entry.Exit_type = defaults.get("Exit_type") or entry.Exit_type or "SELL"
    entry.Exit_status = defaults.get("Exit_status")
    entry.SignalExit_time = defaults.get("SignalExit_time") or timezone.now()
    entry.order_status = defaults.get("order_status")
    entry.trade_order_status = "CLOSE"
    entry.LivePrice = defaults.get("LivePrice") or entry.LivePrice
    entry.failure_reason = defaults.get("failure_reason")
    entry.save()

    if history_id:
        Tradeorderhistory.objects.filter(history_id=str(history_id)).exclude(pk=entry.pk).delete()
    return entry


def consolidate_completed_exit_history(exit_history):
    with transaction.atomic():
        exit_history = Tradeorderhistory.objects.select_for_update().get(pk=exit_history.pk)
        if (
            _normalize_status_value(exit_history.transaction_type) != "sell"
            or _normalize_status_value(exit_history.order_status)
            not in {"complete", "completed", "success", "traded", "filled", "executed"}
        ):
            return None
        order_payload = exit_history.order_params if isinstance(exit_history.order_params, dict) else {}
        webhook_signal = exit_history.webhook_signal if isinstance(exit_history.webhook_signal, dict) else {}
        entry = _find_entry_history_for_exit(
            exit_history.client,
            order_payload,
            webhook_signal,
            exit_history.trading_symbol or exit_history.Index_Symbol,
        )
        if entry is None or entry.pk == exit_history.pk:
            return None
        defaults = {
            "order_id": exit_history.order_id,
            "order_status": exit_history.order_status,
            "failure_reason": exit_history.failure_reason,
            "Exit_Price": exit_history.Exit_Price or exit_history.LivePrice,
            "ExitQty": exit_history.ExitQty or exit_history.EntryQty,
            "Exit_type": exit_history.Exit_type,
            "Exit_status": exit_history.Exit_status or exit_history.order_status,
            "SignalExit_time": exit_history.SignalExit_time,
            "LivePrice": exit_history.LivePrice,
        }
        result = _merge_completed_exit_into_entry(
            entry,
            defaults,
            exit_history.response_data if isinstance(exit_history.response_data, dict) else {},
            order_payload,
            exit_history.history_id,
        )
        Tradeorderhistory.objects.filter(pk=exit_history.pk).exclude(pk=result.pk).delete()
        return result


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
        broker_contract = _extract_response_contract_details(response_payload)
        if broker_contract:
            order_payload.update({
                "symbol": broker_contract["underlying"],
                "underlying": broker_contract["underlying"],
                "strike": broker_contract["strike"],
                "strike_price": broker_contract["strike"],
                "option_type": broker_contract["option_type"],
                "expiry": broker_contract["expiry"],
                "resolved_trading_symbol": broker_contract["resolved_trading_symbol"],
            })
            sltp_metadata.update(broker_contract)
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
                _quantity_from_payload(nested_response),
                _quantity_from_payload(meta_response),
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
        resolved_trade_order_status = trade_order_status or str(resolved_status)
        if (
            not is_exit_signal
            and _normalize_status_value(resolved_status) in {"failed", "failure", "error", "rejected", "cancelled", "canceled"}
        ):
            resolved_trade_order_status = "Failed"

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
            "trade_order_status": resolved_trade_order_status,
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

        is_option_trade = _is_option_trade_symbol(trade_symbol, contract_symbol, order_payload, sltp_metadata)
        if is_exit_signal:
            defaults["Exit_Price"] = effective_price or _to_decimal(Exit_price)
            if defaults["Exit_Price"] is None and not is_option_trade:
                defaults["Exit_Price"] = live_price_value
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

        with transaction.atomic():
            entry = None
            if is_exit_signal:
                entry = _find_entry_history_for_exit(user, order_payload, webhook_signal, contract_symbol)
                if entry is not None:
                    defaults["Entry_type"] = entry.Entry_type or defaults.get("Entry_type")
                    defaults["Entry_Price"] = entry.Entry_Price
                    defaults["EntryQty"] = entry.EntryQty
                    defaults["SignalEntry_time"] = entry.SignalEntry_time

            if entry is not None and _normalize_status_value(resolved_status) in {"complete", "completed"}:
                return _merge_completed_exit_into_entry(
                    entry,
                    defaults,
                    response_payload,
                    order_payload,
                    history_id,
                )

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
