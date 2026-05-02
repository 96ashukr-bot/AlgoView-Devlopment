import csv
from decimal import Decimal
import json
import os
import hashlib
import hmac
import re
from numbers import Number
from amqp import NotFound
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import requests
from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
import time
from rest_framework.generics import ListAPIView,UpdateAPIView
from main.angleapi_upgraded import exit_existing_buy_position_angleone, get_token_details, place_Angle_order
from main.angelone_views import login_angelone_redirect, angelone_callback, angelone_callbackaa, place_angel_one_trade
from main.execution_engine import ExecutionRequest, get_execution_engine
from main.services.multileg_execution import get_multileg_execution_engine
from main.dematemodule import  exit_existing_buy_position_5PaisaOrder, exit_existing_buy_position_Aliceblue, exit_existing_buy_position_DhanOrder, exit_existing_buy_position_Upstox, exit_existing_buy_position_fyers_order, exit_existing_buy_position_zerodha_order, trading_Symbol_sum
from main.dhanapi import place_dhan_orders
from main.fivepaisa import fetch_access_token_5paisa, place_5paisa_order
from main.fyersapi import place_fyers_orders
from main.permissions import (
    IsAdminOrSuperadmin,
    IsAdminRole,
    can_access_client_record,
    is_admin_or_superadmin,
    is_admin_user,
    is_superadmin_user,
)
from main.services.login_activity_service import LoginActivityService
from main.broker_registry import broker_field_is_configured, get_broker_setup_spec, get_default_broker_catalog, normalize_broker_name
from main.tasks import resend_otp_email_async, send_kyc_email_async, send_trade_email_async,send_password_reset_email
from rest_framework import status
# from django.utils.timezone import make_aware
# from django.utils.timezone import localtime
from django.utils.timezone import make_aware, localtime
from pytz import timezone as pytz_timezone
from main.upstock import place_upstox_orders
from main.zerodha import place_zerodha_orders
from .models import *
from .serializers import *
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from django.contrib import messages
from pya3 import *
from decouple import config
from main.Alice_Blue_Api import ALICE_ORDER_URL,GET_ORDER_BOOK_URL,GET_TREAD_BOOK_URL, is_market_open, place_alice_orders
from main.trade_history_service import save_trade_order_history
from main.sl_tp_watcher_service import get_sl_tp_watcher_service
from rest_framework.pagination import PageNumberPagination        
from main.email import EmailService
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.db.models import Q
from django.db.models import Count, Prefetch
import pandas as pd
from datetime import datetime
from django.core.cache import cache
import pyotp
# from SmartApi import SmartConnect
# from SmartApi.smartExceptions import DataException
# from time import sleep
import numpy as np
import pytz
from main.companysmtpsetails import get_company_profile,get_smtp_details 
from rest_framework import permissions
company_profile = get_company_profile()
smtp_details = get_smtp_details()

# from main.companysmtpsetails import smtp_details,company_profile
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime
USER_ID=config('USER_ID')
ALICE_API_KEY=config('ALICE_API_KEY')
import logging
logger = logging.getLogger('main')
UserModel = get_user_model()


def _require_webhook_secret(request):
    configured_secret = str(getattr(settings, "WEBHOOK_SECRET", "") or "").strip()
    if not configured_secret:
        if getattr(settings, "IS_PRODUCTION", False):
            raise ValidationError("Webhook secret is not configured.")
        return

    request_payload = request.data if hasattr(request.data, "get") else {}
    provided_secret = (
        request.headers.get("X-Webhook-Secret")
        or request.headers.get("X-Algoview-Webhook-Secret")
        or str(request.query_params.get("webhook_secret", "") or "")
        or str(request_payload.get("webhook_secret", "") or "")
    )
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        provided_secret = auth_header.split(" ", 1)[1].strip()

    if not provided_secret or not hmac.compare_digest(str(provided_secret), configured_secret):
        raise PermissionDenied("Invalid webhook secret.")


def _get_selected_broker_detail_for_user(user):
    return (
        ClientBrokerdetails.objects.filter(client=user)
        .select_related("broker_name")
        .order_by("-tokenCreatedAt", "-id")
        .first()
    )


def _ensure_default_broker_catalog():
    for broker_item in get_default_broker_catalog():
        broker_name = broker_item["broker_name"]
        Broker.objects.get_or_create(
            broker_name=broker_name,
            defaults={
                "description": broker_item.get("description"),
                "is_active": broker_item.get("is_active", True),
            },
        )
    return Broker.objects.filter(is_active=True).order_by("broker_name")


def _resolve_order_preferences(request_data, trade_setting):
    requested_order_type = (
        request_data.get("order_type")
        or request_data.get("orderType")
        or getattr(trade_setting, "order_type", None)
        or "LIMIT"
    )
    order_type = str(requested_order_type).upper()

    requested_buffer = request_data.get("buffer_percentage")
    if requested_buffer in (None, ""):
        buffer_percentage = getattr(trade_setting, "buffer_percentage", None)
    else:
        buffer_percentage = requested_buffer

    return order_type, buffer_percentage


WEBHOOK_SYMBOL_MAPPING = {
    "NIFTY BANK": "BANKNIFTY",
    "BANK NIFTY": "BANKNIFTY",
    "BANKNIFTY": "BANKNIFTY",
    "NIFTY 50": "NIFTY",
    "NIFTY": "NIFTY",
    "NIFTY FIN SERVICE": "FINNIFTY",
    "FINNIFTY": "FINNIFTY",
    "MID CAP NIFTY": "MIDCPNIFTY",
    "NIFTY MID SELECT": "MIDCPNIFTY",
    "MIDCPNIFTY": "MIDCPNIFTY",
    "SENSEX": "SENSEX",
}


def _normalize_webhook_symbol(value):
    normalized_value = str(value or "").strip().upper()
    return WEBHOOK_SYMBOL_MAPPING.get(normalized_value, normalized_value.replace(" ", ""))


def _trade_matches_webhook_symbol(trade, webhook_symbol):
    normalized_webhook_symbol = _normalize_webhook_symbol(webhook_symbol)
    candidate_values = [
        getattr(trade, "symbol", None),
        getattr(getattr(trade, "sub_segment", None), "name", None),
        getattr(getattr(trade, "sub_segment", None), "short_name", None),
    ]
    normalized_candidates = {
        _normalize_webhook_symbol(candidate)
        for candidate in candidate_values
        if str(candidate or "").strip()
    }
    return normalized_webhook_symbol in normalized_candidates


def _get_webhook_strategy_identifier(alert_data):
    for key in ("stratergyid", "strategyid", "strategyTag"):
        value = alert_data.get(key)
        if str(value or "").strip():
            return str(value).strip()
    return ""


def _get_matching_webhook_trades(alert_data, webhook_symbol):
    strategy_identifier = _get_webhook_strategy_identifier(alert_data)
    if not strategy_identifier:
        return ClientTradeSetting.objects.none(), ""

    candidate_queryset = ClientTradeSetting.objects.filter(
        group_service__iexact=strategy_identifier,
    ).select_related("client", "segment", "sub_segment")

    ready_count = 0
    blocked_count = 0
    for trade in candidate_queryset:
        reasons = _collect_trade_skip_reasons(
            trade,
            webhook_symbol=webhook_symbol,
            strategy_identifier=strategy_identifier,
        )
        if reasons:
            blocked_count += 1
        else:
            ready_count += 1

    logger.info(
        "Webhook trade scan completed for strategy '%s' and symbol '%s': total=%s ready=%s blocked=%s",
        strategy_identifier,
        webhook_symbol,
        candidate_queryset.count(),
        ready_count,
        blocked_count,
    )

    return candidate_queryset, strategy_identifier


def _get_trade_execution_symbol(trade):
    return (
        str(getattr(trade, "symbol", "") or "").strip()
        or str(getattr(getattr(trade, "sub_segment", None), "short_name", "") or "").strip()
        or str(getattr(getattr(trade, "sub_segment", None), "name", "") or "").strip()
    )


def _get_client_broker_name(client):
    if not client:
        return None
    broker_detail = ClientBrokerdetails.objects.filter(client=client).select_related("broker_name").first()
    if broker_detail and broker_detail.broker_name:
        return broker_detail.broker_name.broker_name
    return None


def _collect_trade_skip_reasons(trade, *, webhook_symbol=None, strategy_identifier=None):
    reasons = []
    client = getattr(trade, "client", None)
    execution_symbol = _get_trade_execution_symbol(trade)
    normalized_strategy = str(strategy_identifier or "").strip()
    configured_group_service = str(getattr(trade, "group_service", "") or "").strip()
    broker_name = str(getattr(trade, "broker", "") or "").strip()
    broker_detail = ClientBrokerdetails.objects.filter(client=client).select_related("broker_name").first() if client else None

    if not client:
        reasons.append("Missing client mapping")
        return reasons

    if not getattr(client, "is_enable", False):
        reasons.append("Client trading is disabled")

    if not getattr(trade, "is_tread_status", False):
        reasons.append("Trade toggle is disabled")

    if not execution_symbol:
        reasons.append("Symbol/script is missing")

    if webhook_symbol and execution_symbol and not _trade_matches_webhook_symbol(trade, webhook_symbol):
        reasons.append("Webhook symbol does not match client script")

    if not configured_group_service:
        reasons.append("Group service is missing on trade setting")
    elif normalized_strategy and configured_group_service.casefold() != normalized_strategy.casefold():
        reasons.append("Webhook group service does not match client group service")

    if not broker_name:
        reasons.append("Broker is missing on trade setting")

    if not broker_detail or not broker_detail.broker_name:
        reasons.append("Client broker details are not configured")
    elif broker_name and broker_detail.broker_name.broker_name.casefold() != broker_name.casefold():
        reasons.append("Trade broker and client broker setup do not match")
    else:
        normalized_broker_name = normalize_broker_name(broker_name or broker_detail.broker_name.broker_name)
        setup_spec = get_broker_setup_spec(normalized_broker_name)
        if setup_spec:
            missing_fields = [
                field_spec["label"]
                for field_spec in setup_spec["fields"]
                if field_spec.get("required") and not broker_field_is_configured(broker_detail, field_spec["key"])
            ]
            if missing_fields:
                reasons.append(f"Broker credentials are incomplete: {', '.join(missing_fields)}")

        if normalized_broker_name not in {"alice blue", "angel one"}:
            access_token = None
            access_token_getter = getattr(broker_detail, "get_access_token_secure", None)
            if callable(access_token_getter):
                access_token = access_token_getter()
            access_token = access_token or getattr(broker_detail, "access_token", None)
            if not str(access_token or "").strip():
                reasons.append("Broker access token is missing")
            else:
                expiry = getattr(broker_detail, "access_token_expiry", None)
                if expiry:
                    try:
                        expiry_value = make_aware(expiry) if timezone.is_naive(expiry) else expiry
                    except Exception:
                        expiry_value = expiry
                    if expiry_value and expiry_value <= timezone.now():
                        reasons.append("Broker access token has expired")

    if not str(getattr(trade, "product_type", "") or "").strip():
        reasons.append("Product type is missing")

    quantity = _safe_positive_int(getattr(trade, "quantity", None))
    if quantity is None:
        reasons.append("Quantity is missing or invalid")

    if getattr(trade, "expiry_date", None) is None:
        reasons.append("Expiry date is missing")

    return reasons


def _get_trade_limit_skip_reason(trade, symbol):
    configured_limit = int((getattr(trade, "trade_limit", 0) or 0) * 2)
    if configured_limit <= 0:
        return "Trade limit is not configured"

    daily_trade_count = TradingLog.objects.filter(
        client=getattr(trade, "client", None),
        date=timezone.localdate(),
        symbol=symbol,
    ).count()
    if daily_trade_count >= configured_limit:
        return f"Daily trade limit reached ({daily_trade_count}/{configured_limit})"
    return None


def _build_trade_history_payload(status_value, message, *, skip_reasons=None, order_response=None):
    payload = {"status": status_value, "message": message}
    if skip_reasons:
        payload["skip_reasons"] = skip_reasons
        payload["skipped"] = True
    if order_response is not None:
        payload["order_response"] = order_response
    return {"data": payload}


def _save_webhook_trade_skip(
    *,
    trade,
    history_id,
    live_price,
    group_service,
    transaction_type,
    strategy,
    webhook_signal,
    exchange,
    segment,
    index_symbol,
    order_params,
    reason_message,
    skip_reasons,
):
    save_trade_order_history(
        live_price,
        group_service,
        transaction_type,
        "SKIPPED",
        trade.client,
        index_symbol or trade.symbol,
        0,
        "Failed",
        _build_trade_history_payload("Failed", reason_message, skip_reasons=skip_reasons),
        reason_message,
        strategy,
        None,
        None,
        None,
        None,
        None,
        None,
        webhook_signal,
        exchange,
        segment,
        index_symbol,
        order_params,
        broker=trade.broker,
        history_id=history_id,
    )


def _resolve_webhook_request_context(request_data):
    alert_data = request_data
    if not alert_data:
        raise ValidationError("No alert data received.")

    raw_symbol = request_data.get("text", "")
    signal_price = alert_data.get("signalprice", 0)
    default_price = round_price(signal_price)
    strategy_id = _get_webhook_strategy_identifier(alert_data)
    if not strategy_id:
        raise ValidationError("Webhook strategy identifier is missing.")

    transaction_type = str(request_data.get("ordertype", "BUY-O") or "BUY-O").upper()
    order_type_mapping = {
        "BUY-O": "Buy CE",
        "SELL-C": "Close CE",
        "SELL-C_O": "Close CE & Buy PE",
        "SELL-O": "BUY PE",
        "BUY-C": "Close PE",
        "BUY-C_O": "Close PE & Buy CE",
    }
    action_description = order_type_mapping.get(transaction_type)
    if not action_description:
        raise ValidationError("Invalid OrderType received.")

    if action_description == "Close CE & Buy PE":
        buy_sell = "CE PE"
    elif action_description == "Close PE & Buy CE":
        buy_sell = "PE CE"
    else:
        buy_sell = action_description.split()[-1]

    symbols = _normalize_webhook_symbol(raw_symbol)
    exch_seg = "BSE" if symbols.upper() == "SENSEX" else "NFO"

    return {
        "alert_data": alert_data,
        "strategy_id": strategy_id,
        "transaction_type": transaction_type,
        "buy_sell": buy_sell,
        "symbols": symbols,
        "exch_seg": exch_seg,
        "default_price": default_price,
        "default_ordertype": str(request_data.get("orderType") or request_data.get("order_type") or "LIMIT").upper(),
        "strategy_tag": request_data.get("strategyTag", "ce entry"),
        "limit_price": request_data.get("limitPrice", 0),
        "default_quantity": 0,
        "lots": 1,
        "trigger_price": 0,
        "live_price": default_price,
    }


def _process_webhook_trade(trade, index, context, *, history_id=None):
    history_id = history_id or f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{trade.client_id}_{trade.id}"
    alert_data = context["alert_data"]
    symbols = context["symbols"]
    exch_seg = context["exch_seg"]
    default_price = context["default_price"]
    default_quantity = context["default_quantity"]
    live_price = context["live_price"]
    lots = context["lots"]
    trigger_price = context["trigger_price"]
    buy_sell_type = context["transaction_type"]
    buy_sell = context["buy_sell"]
    limit_price = context["limit_price"]
    strategy_id = context["strategy_id"]

    transaction_type = buy_sell_type
    default_expiry = trade.expiry_date
    group_service = trade.group_service
    strategy = trade.strategy
    segment = trade.segment.name if trade.segment else None
    exchange = exch_seg
    user = trade.client
    trade_symbol = _get_trade_execution_symbol(trade) or symbols
    index_symbol = trade_symbol or None
    resolved_order_type, resolved_buffer_percentage = _resolve_order_preferences(alert_data, trade)
    order_params = serialize_to_json(
        {
            "symbol": trade_symbol,
            "Exchange": exch_seg,
            "quantity": trade.quantity or default_quantity,
            "product_type": trade.product_type,
            "transaction_type": buy_sell,
            "price": limit_price or 0,
            "ordertype": resolved_order_type,
            "order_type": resolved_order_type,
            "buffer_percentage": resolved_buffer_percentage,
            "strategy": strategy,
        }
    )

    logger.info(
        "Webhook trade evaluation started for client=%s trade_setting=%s symbol=%s history_id=%s index=%s",
        getattr(user, "id", None),
        trade.id,
        trade_symbol,
        history_id,
        index,
    )

    base_skip_reasons = _collect_trade_skip_reasons(
        trade,
        webhook_symbol=symbols,
        strategy_identifier=strategy_id,
    )
    trade_limit_reason = _get_trade_limit_skip_reason(trade, trade_symbol.upper() if trade_symbol else "")
    if trade_limit_reason:
        base_skip_reasons.append(trade_limit_reason)

    if base_skip_reasons:
        reason_message = "; ".join(base_skip_reasons)
        logger.warning(
            "Skipping webhook trade for client=%s trade_setting=%s reasons=%s",
            getattr(user, "id", None),
            trade.id,
            base_skip_reasons,
        )
        _save_webhook_trade_skip(
            trade=trade,
            history_id=history_id,
            live_price=live_price,
            group_service=group_service,
            transaction_type=transaction_type,
            strategy=strategy,
            webhook_signal=alert_data,
            exchange=exchange,
            segment=segment,
            index_symbol=index_symbol,
            order_params=order_params,
            reason_message=reason_message,
            skip_reasons=base_skip_reasons,
        )
        return {
            "history_id": history_id,
            "client_id": trade.client_id,
            "client_name": getattr(user, "fullName", None) or getattr(user, "userName", None),
            "trade_setting_id": trade.id,
            "script_name": trade_symbol,
            "status": "skipped",
            "reason": reason_message,
            "skip_reasons": base_skip_reasons,
        }

    save_trade_order_history(
        live_price,
        group_service,
        transaction_type,
        "PROCESSING",
        user,
        trade_symbol,
        0,
        "Pending",
        _build_trade_history_payload("Pending", "Trade execution started."),
        "Trade execution started.",
        strategy,
        None,
        None,
        None,
        None,
        None,
        None,
        alert_data,
        exchange,
        segment,
        index_symbol,
        order_params,
        broker=trade.broker,
        history_id=history_id,
    )

    try:
        expiry_date = None
        day = month = year = fullyear = ""
        if default_expiry:
            expiry_date = localtime(default_expiry)
            day = expiry_date.strftime("%d")
            month = expiry_date.strftime("%b").upper()
            year = expiry_date.strftime("%y")
            fullyear = expiry_date.strftime("%Y")

        quantity = trade.quantity or default_quantity
        product_type = trade.product_type
        price = limit_price
        ordertype = resolved_order_type
        entry_type = exit_type = entry_price = exit_price = entry_qty = exit_qty = None

        order_response = None
        if transaction_type == "SELL-C_O":
            transaction_type = "SELL-C"
            action, option_type = manage_order(transaction_type, buy_sell, None)
            order_response = place_order_broker(
                live_price, group_service, trade, user, action, trade_symbol, quantity, strategy, ordertype,
                product_type, price, lots, None, entry_type, exit_type, entry_price, exit_price, entry_qty, exit_qty,
                alert_data, exchange, segment, index_symbol, trigger_price, day, month, year, fullyear, default_price,
                option_type, order_params, history_id
            )
            transaction_type = "SELL-O"
            action, option_type = manage_order(transaction_type, buy_sell, option_type)
            order_response = place_order_broker(
                live_price, group_service, trade, user, action, trade_symbol, quantity, strategy, ordertype,
                product_type, price, lots, None, entry_type, exit_type, entry_price, exit_price, entry_qty, exit_qty,
                alert_data, exchange, segment, index_symbol, trigger_price, day, month, year, fullyear, default_price,
                option_type, order_params, history_id
            )
        elif transaction_type == "BUY-C_O":
            transaction_type = "BUY-C"
            action, option_type = manage_order(transaction_type, buy_sell, None)
            order_response = place_order_broker(
                live_price, group_service, trade, user, action, trade_symbol, quantity, strategy, ordertype,
                product_type, price, lots, None, entry_type, exit_type, entry_price, exit_price, entry_qty, exit_qty,
                alert_data, exchange, segment, index_symbol, trigger_price, day, month, year, fullyear, default_price,
                option_type, order_params, history_id
            )
            transaction_type = "BUY-O"
            action, option_type = manage_order(transaction_type, buy_sell, option_type)
            order_response = place_order_broker(
                live_price, group_service, trade, user, action, trade_symbol, quantity, strategy, ordertype,
                product_type, price, lots, None, entry_type, exit_type, entry_price, exit_price, entry_qty, exit_qty,
                alert_data, exchange, segment, index_symbol, trigger_price, day, month, year, fullyear, default_price,
                option_type, order_params, history_id
            )
        else:
            action, option_type = manage_order(transaction_type, buy_sell, None)
            order_response = place_order_broker(
                live_price, group_service, trade, user, action, trade_symbol, quantity, strategy, ordertype,
                product_type, price, lots, None, entry_type, exit_type, entry_price, exit_price, entry_qty, exit_qty,
                alert_data, exchange, segment, index_symbol, trigger_price, day, month, year, fullyear, default_price,
                option_type, order_params, history_id
            )

        normalized_response = order_response or {"data": {"status": "Failed", "message": "No broker response received."}}
        response_data = normalized_response.get("data", {}) if isinstance(normalized_response, dict) else {}
        broker_status = str(response_data.get("status", "Failed") or "Failed").lower()
        message = str(response_data.get("message") or response_data.get("error") or "")

        if broker_status in {"complete", "completed", "open"}:
            TradingLog.objects.create(
                client=user,
                symbol=trade_symbol.upper() if trade_symbol else trade_symbol,
                strategy=strategy,
            )
            final_status = "success"
        else:
            final_status = "failed"

        return {
            "history_id": history_id,
            "client_id": trade.client_id,
            "client_name": getattr(user, "fullName", None) or getattr(user, "userName", None),
            "trade_setting_id": trade.id,
            "script_name": trade_symbol,
            "status": final_status,
            "broker_status": broker_status,
            "reason": message or f"Broker returned status {broker_status}.",
            "response": normalized_response,
        }
    except Exception as exc:
        error_message = f"Unhandled exception while processing trade: {str(exc)}"
        logger.exception(
            "Webhook trade processing failed for client=%s trade_setting=%s history_id=%s",
            getattr(user, "id", None),
            trade.id,
            history_id,
        )
        _save_webhook_trade_skip(
            trade=trade,
            history_id=history_id,
            live_price=live_price,
            group_service=group_service,
            transaction_type=transaction_type,
            strategy=strategy,
            webhook_signal=alert_data,
            exchange=exchange,
            segment=segment,
            index_symbol=index_symbol,
            order_params=order_params,
            reason_message=error_message,
            skip_reasons=[error_message],
        )
        return {
            "history_id": history_id,
            "client_id": trade.client_id,
            "client_name": getattr(user, "fullName", None) or getattr(user, "userName", None),
            "trade_setting_id": trade.id,
            "script_name": trade_symbol,
            "status": "failed",
            "reason": error_message,
            "skip_reasons": [error_message],
        }


def _get_group_service_script_name(entry):
    if not isinstance(entry, dict):
        return ""
    return str(entry.get("ScriptName") or entry.get("ServiceName") or "").strip()


def _sync_client_trade_settings_from_group_service(client, fallback_segment_id=None, fallback_subsegments=None):
    group_service = getattr(client, "Group_service", None)
    resolved_pairs = []
    seen_pairs = set()
    entry_defaults_by_pair = {}
    existing_trade_settings = {
        (int(trade.segment_id), int(trade.sub_segment_id)): trade
        for trade in ClientTradeSetting.objects.filter(client=client)
        if trade.segment_id and trade.sub_segment_id
    }

    def add_pair(segment_id, sub_segment_id):
        if not segment_id or not sub_segment_id:
            return
        pair = (int(segment_id), int(sub_segment_id))
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            resolved_pairs.append(pair)

    if group_service and isinstance(group_service.json_data, list):
        for entry in group_service.json_data:
            entry_segment_id = entry.get("segment") or getattr(group_service, "segment_id", None) or fallback_segment_id
            script_name = _get_group_service_script_name(entry)
            if not entry_segment_id or not script_name:
                continue

            sub_segment = SubSegment.objects.filter(
                segment_id=entry_segment_id
            ).filter(
                Q(name__iexact=script_name) | Q(short_name__iexact=script_name)
            ).first()

            if not sub_segment:
                sub_segment = SubSegment.objects.create(
                    segment_id=entry_segment_id,
                    name=script_name,
                    short_name=script_name,
                    status=True,
                )

            if sub_segment:
                add_pair(entry_segment_id, sub_segment.id)
                entry_defaults_by_pair[(int(entry_segment_id), int(sub_segment.id))] = {
                    "product_type": str(entry.get("ProductType") or "").strip() or None,
                    "quantity": int(entry.get("Qty")) if str(entry.get("Qty") or "").strip().isdigit() else (
                        int(entry.get("LotSize")) if str(entry.get("LotSize") or "").strip().isdigit() else None
                    ),
                }

    if fallback_segment_id and fallback_subsegments:
        for sub_segment_id in fallback_subsegments:
            add_pair(fallback_segment_id, sub_segment_id)

    group_service_name = group_service.group_name if group_service else None
    retained_pairs = set()
    for segment_id, sub_segment_id in resolved_pairs:
        retained_pairs.add((int(segment_id), int(sub_segment_id)))
        sub_segment = SubSegment.objects.filter(pk=sub_segment_id).first()
        existing_trade = existing_trade_settings.get((int(segment_id), int(sub_segment_id)))
        symbol_value = (
            (existing_trade.symbol if existing_trade else None)
            or getattr(sub_segment, "short_name", None)
            or getattr(sub_segment, "name", None)
        )
        entry_defaults = entry_defaults_by_pair.get((int(segment_id), int(sub_segment_id)), {})
        defaults = {
            "group_service": group_service_name,
            "symbol": str(symbol_value or "").strip() or None,
            "broker": (
                (existing_trade.broker if existing_trade else None)
                or _get_client_broker_name(client)
            ),
            "product_type": (
                (existing_trade.product_type if existing_trade else None)
                or entry_defaults.get("product_type")
            ),
            "quantity": (
                (existing_trade.quantity if existing_trade and existing_trade.quantity else None)
                or entry_defaults.get("quantity")
            ),
        }
        ClientTradeSetting.objects.update_or_create(
            client=client,
            segment_id=segment_id,
            sub_segment_id=sub_segment_id,
            defaults=defaults,
        )

    obsolete_ids = [
        trade.id
        for pair, trade in existing_trade_settings.items()
        if pair not in retained_pairs
    ]
    if obsolete_ids:
        ClientTradeSetting.objects.filter(id__in=obsolete_ids).delete()

    return resolved_pairs


def _sync_client_multi_leg_settings(client):
    assigned_multi_leg_strategies = Strategies.objects.filter(
        Q(client_strategy=client) | Q(clients=client),
        execution_mode=Strategies.EXECUTION_MODE_MULTI_LEG,
        is_active=True,
    ).select_related("segment").distinct()
    retained_ids = set()

    for strategy in assigned_multi_leg_strategies:
        defaults = {
            "segment": strategy.segment,
            "group_service": getattr(getattr(client, "Group_service", None), "group_name", None),
            "broker": _get_client_broker_name(client),
        }
        setting, _ = ClientMultiLegStrategySetting.objects.update_or_create(
            client=client,
            strategy=strategy,
            defaults=defaults,
        )
        retained_ids.add(setting.id)

    ClientMultiLegStrategySetting.objects.filter(client=client).exclude(id__in=retained_ids).delete()
    return retained_ids


def _parse_multi_leg_expiry_date(expiry_value):
    expiry_text = str(expiry_value or "").strip()
    if not expiry_text:
        return None

    normalized_expiry_text = expiry_text.split("T", 1)[0]
    for date_format in ("%Y-%m-%d", "%d%b%Y", "%d%b%y"):
        try:
            parsed_expiry = datetime.strptime(normalized_expiry_text.upper(), date_format)
            india_tz = pytz_timezone('Asia/Kolkata')
            return make_aware(parsed_expiry, timezone=india_tz)
        except ValueError:
            continue

    try:
        parsed_expiry = datetime.fromisoformat(expiry_text)
        india_tz = pytz_timezone('Asia/Kolkata')
        if timezone.is_naive(parsed_expiry):
            return make_aware(parsed_expiry, timezone=india_tz)
        return parsed_expiry
    except ValueError:
        return None


def _format_execution_price(value):
    if value in (None, ""):
        return 0
    if isinstance(value, Number):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


company_profile = company_profile
# company_profile=None
support_email = company_profile.company_support_email if company_profile else "support@example.com"
company_website = company_profile.company_website if company_profile else "https://example.com"
logo_url = company_profile.company_logo if company_profile else "https://example.com/logo.png"
login_link = company_profile.login_link if company_profile else "https://www.admin.algoview.in/login"
help_center_link = company_profile.help_center_link if company_profile else "https://www.admin.algoview.in/login"  
contact_number = company_profile.company_phone_number if company_profile else None

smtp_details=smtp_details
default_from_email=smtp_details.email_host_user if smtp_details else   "no-reply@example.com" 
# get Role Views
class RoleListCreateView(generics.ListCreateAPIView):
    pagination_class = None
    queryset=Role.objects.all().order_by('-id')
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

class GetRoleListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            roles = Role.objects.filter(Q(name__iexact='Sub-Admin') | Q(name__iexact='Admin')).order_by('-id')
            serializer = RoleSerializer(roles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Role.DoesNotExist:
            logger.error("No roles found.")
            return Response({
                "status": "error",
                "message": "No roles found."
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.exception("An error occurred while fetching roles.")
            return Response({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#delete role
class RoleDeleteView(generics.DestroyAPIView):
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):
        role_id = kwargs.get('id')
        role = get_object_or_404(Role, id=role_id)
        role.delete()
        return Response({
            "status": "success",
            "message": f"Role with ID {role_id} has been deleted."
        }, status=status.HTTP_200_OK)    
class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    pagination_class = None
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

# User Views create
class UserListCreateView(generics.ListCreateAPIView):
    pagination_class = None
    queryset = User.objects.filter(type_of_user='is_user').order_by('-id')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    def create(self, request, *args, **kwargs):
        # start_time=time.time()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
#login
# class CustomLoginView(generics.GenericAPIView):
#     pagination_class = None
#     serializer_class = CustomLoginSerializer
#     def post(self, request, *args, **kwargs):
#         # start_time=time.time()
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         # end_time = time.time()  # Record the end time
#         # execution_time = end_time - start_time  # Calculate the total time
#         # print(f"Login API executed in {execution_time:.4f} seconds")  # Log the execution timee
#         return Response(serializer.validated_data, status=status.HTTP_200_OK)

class CustomLoginView(generics.GenericAPIView):
    pagination_class = None
    serializer_class = CustomLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')

        # Log the login time in UserActivityLog
        if request.session and not request.session.session_key:
            request.session.save()

        UserActivityLog.objects.create(
            user=user,
            last_login_time=now(),
            session_key=request.session.session_key
        )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    
#logout api
# class LogoutView(APIView):
#     permission_classes = [IsAuthenticated]  # Ensure user is authenticated

#     def post(self, request):
#         # Get user's refresh token from request data (passed by frontend)
#         refresh_token = request.data.get('refresh_token')
        
#         try:
#             # Blacklist the refresh token (if using Simple JWT Blacklisting)
#             token = RefreshToken(refresh_token)
#             token.blacklist()

#             # Log the user's logout time in the UserActivityLog
#             session_key = request.session.session_key
#             try:
#                 activity_log = UserActivityLog.objects.filter(user=request.user,session_key=session_key).latest('last_login_time')
#                 activity_log.mark_logout()
#             except UserActivityLog.DoesNotExist:
#                 pass  # If no login entry exists, skip silently
            
#             return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def post(self, request):
        refresh_token = request.data.get('refresh_token')

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Log the user's logout time in the UserActivityLog
            session_key = request.session.session_key
            try:
                activity_log = UserActivityLog.objects.filter(user=request.user, session_key=session_key).latest('last_login_time')
                if not activity_log.last_logout_time:  # Ensure logout is only recorded once
                    activity_log.last_logout_time = now()
                    activity_log.save()
            except UserActivityLog.DoesNotExist:
                pass  # If no login entry exists, skip silently

            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

from django.utils.timezone import now


class UserActivityLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = request.GET.get('user_id')  # Get user ID from query parameters

        if user_id:
            user = get_object_or_404(UserModel, id=user_id)
            if not can_access_client_record(request.user, user):
                return Response({"error": "You are not authorized to view this user's activity."}, status=status.HTTP_403_FORBIDDEN)
        else:
            user = request.user

        # Fetch the most recent completed session (login + logout recorded)
        last_completed_session = (
            UserActivityLog.objects
            .filter(user=user, last_login_time__isnull=False, last_logout_time__isnull=False)
            .order_by('-last_login_time')
            .first()
        )

        # Fetch the most recent login entry (latest login without logout)
        current_login_session = (
            UserActivityLog.objects
            .filter(user=user, last_login_time__isnull=False, last_logout_time__isnull=True)
            .order_by('-last_login_time')
            .first()
        )

        if not current_login_session:
            current_login_session = (
                UserActivityLog.objects
                .filter(user=user, last_login_time__isnull=False)
                .order_by('-last_login_time')
                .first()
            )

        response_data = {}

        if last_completed_session:
            response_data["last_login_time"] = last_completed_session.last_login_time.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            response_data["last_logout_time"] = last_completed_session.last_logout_time.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        if current_login_session:
            response_data["current_login_time"] = current_login_session.last_login_time.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        if response_data:
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No login/logout data found."}, status=status.HTTP_404_NOT_FOUND)


class LoginActivitySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id=None, *args, **kwargs):
        target_user = request.user

        if user_id is not None and request.user.id != user_id:
            if not is_admin_or_superadmin(request.user):
                return Response(
                    {"status": "error", "message": "You do not have permission to access this user's activity."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            target_user = get_object_or_404(UserModel, id=user_id)

        summary = LoginActivityService().build_summary(target_user, request=request)
        return Response(summary, status=status.HTTP_200_OK)

#verify-otp via email
class OTPVerifyView(generics.GenericAPIView):
    serializer_class = OTPVerifySerializer
    pagination_class = None
    def post(self, request, *args, **kwargs):
        # start_time=time.time()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # end_time = time.time()  # Record the end time
        # execution_time = end_time - start_time  # Calculate the total time
        # print(f"verify otp API executed in {execution_time:.4f} seconds")
        # logger.info(f"verify otp API executed in {execution_time:.4f} seconds")  # Log the execution timee
        # return Response(serializer.validated_data, status=status.HTTP_200_OK)
        # Get the user from the serializer
        # Get the user ID or email from the serializer (not the full user object)
        user_id = serializer.validated_data['user_id']
        email = serializer.validated_data['email']

        # Check if the user has completed eKYC
        kyc_exists = KYC.objects.filter(user_id=user_id).exists()

        ekyc_status = kyc_exists  # True if KYC record exists, otherwise False

        # Add the eKYC status to the response
        response_data = serializer.validated_data
        response_data['ekyc_status'] = ekyc_status

        return Response(response_data, status=status.HTTP_200_OK)

#resend otp
class ResendOTPView(APIView):
    pagination_class = None
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')

        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get the user by email
            user = get_object_or_404(User, email=email)

            # Check if the last OTP is still valid and unverified
            otp_instance = OTP.objects.filter(user=user, is_verified=False).order_by('-expires_at', '-id').first()
            if otp_instance and not otp_instance.is_expired():
                return Response(
                    {"error": "A valid OTP already exists. Please check your email."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Generate and send a new OTP
            otp = OTP.objects.create(user=user)
            otp.generate_otp()
            try:
                EmailService.send_login_email_otp(user.email, otp.otp_code, user.firstName)
            except Exception as exc:
                return Response(
                    {"error": f"Unable to send OTP email. Please verify SMTP settings. {exc}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {"success": "A new OTP has been sent to your email."},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)

    def send_email_otp(self, email, otp_code):
        subject = 'Your OTP Code'
        message = f'Your OTP code is {otp_code}.'
        from_email = default_from_email
        send_mail(subject, message, from_email, [email]) 

#change password
class ChangePasswordView(generics.GenericAPIView):
    pagination_class = None
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]  # Ensure only authenticated users can access this view

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            if user.is_anonymous:
                return Response({'error': 'You must be logged in to change your password.'}, status=status.HTTP_401_UNAUTHORIZED)

            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            # Check if the user has completed eKYC
            kyc_exists = KYC.objects.filter(user_id=user.id).exists()

            ekyc_status = kyc_exists  # True if KYC record exists, otherwise False
            # Save the new password
            serializer.save()
            role_data = {
                'role_id': user.role.id if user.role else None,
                'role_name': user.role.name if user.role else None,
                'role_status': user.role.status if user.role else None
            }
            return Response({
                'user':user.id,
                'role':role_data,
                'ekyc_status':ekyc_status,
                'message': 'Password successfully changed please login with new password.'
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({
                'error': 'Validation error',
                'details': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': 'Something went wrong while changing the password.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Password Reset Views
class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    # permission_classes = [AllowAny]
    pagination_class = None

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data['email']
            user = UserModel.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # reset_link = request.build_absolute_uri(
            #     f'/password-reset-confirm/?uidb64={uid}&token={token}'
            # )
            # reset_link = f'https://sparks.algoview.in/pages/authentication/reset-password/:{uid}/:{token}/:layout'
            # reset_link = f'https://www.admin.algoview.in/pages/authentication/reset-password/:{uid}/:{token}/:layout'
            # reset_link = f'http://103.120.178.54:4000/pages/authentication/reset-password/:{uid}/:{token}/:layout'
            # reset_link = f'http://localhost:3000/pages/authentication/reset-password/:{uid}/:{token}/:layout'
            # subject = "Password Reset Request"
            # print("reset_link",reset_link)
            # message = (
            #     f"Hello,\n\n"
            #     f"You've requested a password reset. Click the link below to reset your password:\n"
            #     f"{reset_link}\n\n"
            #     f"If you did not request this, please ignore this email.\n\n"
            #     f"Best regards,\nYour Team"
            # )
            # send_mail(subject, message, from_email, [email])
            # Retrieve the default from email from your SMTP settings.
            dynamic_email = default_from_email 
            username = user.firstName
            print("default_from_email>>>>", dynamic_email)
            send_password_reset_email(uid,email,username ,token)
            return Response({'detail': 'Password reset link sent.'}, status=status.HTTP_200_OK)
        except UserModel.DoesNotExist:
            return Response({'detail': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uidb64 = serializer.validated_data['uidb64']
        token = serializer.validated_data['token']
        NewPassword = serializer.validated_data['NewPassword']
        
        try:
            uid = force_bytes(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(NewPassword)
        user.save()
        
        return Response({'detail': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)

#user assign role api    
class UserAssignRoleView(generics.UpdateAPIView):
    pagination_class = None
    queryset = User.objects.all()
    permission_classes = [IsAdminOrSuperadmin]
    serializer_class = UserAssignRoleSerializer
    def update(self, request, *args, **kwargs):
        try:
            user = self.get_object()  # Get the user by ID (provided in the URL)
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#pagination of users list
class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # Default page size
    page_size_query_param = 'page_size'  # Allows the client to set the page size dynamically
    max_page_size = 100  # Max limit for page size to avoid performance issues
    page_query_param = 'page_number'  # Allows the client to set the page number

class GetUser(APIView):
    permission_classes = [permissions.IsAuthenticated,  ]
    def get(self, request, pk, *args, **kwargs): 
        try:
            user = User.objects.get(pk=pk)  
            if not can_access_client_record(request.user, user):
                return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            serializer = UserSerializer(user)  
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
# All sub-admins list     
class SubadminsView(APIView):
    permission_classes = [IsAdminOrSuperadmin]
    def get(self, request, *args, **kwargs):
        user = request.user 
        try:
        #     if user.role and user.role.name == 'Super-Admin':
            subadmin = User.objects.filter(role__name='Sub-Admin').order_by('-id')
            serializer = UserSerializer(subadmin,many=True) 
        except User.DoesNotExist:
            return Response({"detail": "subadmins not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.data)
    
#user crud api for admin
class UserManagementView(APIView):
    permission_classes = [IsAdminOrSuperadmin]

    def _resolve_subadmin_role(self, requested_role_id=None):
        if requested_role_id:
            role = Role.objects.filter(id=requested_role_id).first()
            if role:
                return role

        role = (
            Role.objects.filter(name__iexact='Sub-Admin').first()
            or Role.objects.filter(name__iexact='Admin').first()
        )
        if role:
            return role

        return Role.objects.create(name='Sub-Admin', status='active')

    def get(self, request, *args, **kwargs):
        user = request.user 
        if is_superadmin_user(user):
            # Get all Sub-Admins (with role 'Sub-Admin') and prefetch their clients
            users = User.objects.filter(role__name='Sub-Admin').annotate(
                client_count=Count('assigned_users')
            ).prefetch_related(
                Prefetch('assigned_users', queryset=User.objects.all(), to_attr='assigned_users_list')
            ).order_by('-id')
        else:
            # Get Sub-Admins that the logged-in user has created, with client count and client list
            users = User.objects.filter(role__name='Sub-Admin', id=user.id)
            # .annotate(client_count=Count('assigned_users')).prefetch_related(
            #     Prefetch('assigned_users', queryset=User.objects.all(), to_attr='assigned_users_list') ).order_by('-id')
            logger.info(f"Admin:::{user.role.name}")
        search_query = request.query_params.get('q', '').strip()
        if search_query:
            users = users.filter(
                Q(firstName__icontains=search_query) |
                Q(phoneNumber__icontains=search_query) |
                Q(email__icontains=search_query)
            )
    
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(users, request)
        serializer = UserSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    # def get(self, request, *args, **kwargs):
    #     users = User.objects.all().order_by('id')
    #     paginator = CustomPageNumberPagination()
    #     result_page = paginator.paginate_queryset(users, request)
    #     serializer = UserSerializer(result_page, many=True)
    #     return paginator.get_paginated_response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        # Generate a random password
        password = get_random_string(length=12)
        role = self._resolve_subadmin_role(request.data.get('role'))
        payload = request.data.copy()
        payload['role'] = role.id
        serializer = NewUserCreateSerializer(data=payload)
        if serializer.is_valid():
            user = serializer.save(created_by=request.user,role=role) 
            # user.external_user = False
            user.type_of_user='is_user'
            user.set_password(password)  
            user.save() 
            
            if user.email:
                try:
                    EmailService.send_password_email(
                        user.email,
                        password,
                        user.firstName,
                        login_link,
                        support_email,
                        help_center_link,
                        company_website,
                        contact_number,
                    )
                except Exception as exc:
                    logger.warning(
                        "Subadmin %s created but welcome email failed: %s",
                        user.id,
                        exc,
                    )
            
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(
            {
                "detail": "Failed to add user",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


    def put(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=kwargs.get('pk'))
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = NewUserCreateSerializer(user, data=request.data, partial=True)  # partial=True allows updating only some fields
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'User updated successfully.')
            return Response({"msg":"User updated successfully.",'data':serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=kwargs.get('pk'))
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.delete()
        print(messages.success(request, 'User deleted successfully.'))
        return Response({"msg": "User deleted successfully."},status=status.HTTP_204_NO_CONTENT)
        
#sub-admin user profile api crud oprations        
# class UserProfileView(APIView):
#     pagination_class = None
#     permission_classes = [IsAuthenticated]
#     def get(self, request, *args, **kwargs):

#         try:
#             user = request.user
#             serializer = UserProfileRetrieveSerializer(user)
#             return Response(serializer.data)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def patch(self, request, *args, **kwargs):
#         user = request.user
#         try:
#             # Start transaction in case of complex updates (optional)
#             with transaction.atomic():
#                 print("____________",request.data)
#                 serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
#                 if serializer.is_valid():
#                     serializer.save()
#                     return Response(serializer.data, status=status.HTTP_200_OK)
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#         except ValidationError as ve:
#             return Response({"validation_error": ve.detail}, status=status.HTTP_400_BAD_REQUEST)
#         except ObjectDoesNotExist:
#             return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileView(APIView):
    pagination_class = None
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = UserProfileRetrieveSerializer(user)
            
            # Add `user_id` explicitly in response
            response_data = serializer.data
            response_data["client"] = user.id

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, *args, **kwargs):
        user = request.user
        try:
            with transaction.atomic():
                print("____________", request.data)
                serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    
                    # Add `user_id` in update response
                    response_data = serializer.data
                    response_data["client"] = user.id

                    return Response(response_data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as ve:
            return Response({"validation_error": ve.detail}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# get kyc list 
class GetKYCView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = None
    def get(self, request, *args, **kwargs):
        user = request.user
        
        try:
            kyc = KYC.objects.get(user=user)
            serializer = KYCSerializer(kyc)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except KYC.DoesNotExist:
            return Response({'message': 'KYC not found for this user.'}, status=status.HTTP_404_NOT_FOUND)  

class GetKYCByIdView(APIView):
    # permission_classes = [IsAuthenticated]
    pagination_class = None
    def get(self, request,pk, *args, **kwargs):
        try:
            kyc = KYC.objects.get(pk=pk)
            serializer = KYCSerializer(kyc)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except KYC.DoesNotExist:
            return Response({'message': 'KYC not found.'}, status=status.HTTP_404_NOT_FOUND)  
                
#kyc update create 
class CreateOrUpdateKYCView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = None
    def post(self, request, *args, **kwargs):
        user = request.user
        kyc, created = KYC.objects.get_or_create(user=user)

        # If it's an existing KYC, update it with the provided data
        serializer = KYCSerializer(kyc, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            message = "KYC created" if created else "KYC updated"
            return Response({
                "status": "success",
                "message": message,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

from rest_framework.exceptions import NotFound
from rest_framework.pagination import LimitOffsetPagination



# class PendingKYCListView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         try:           

#             # Fetch all pending KYC requests
#             pending_kycs = KYC.objects.all().order_by('-id')
#             search_query = request.GET.get('q', '')

#             if search_query:
#                 pending_kycs = pending_kycs.filter(
#                     Q(user__fullName__icontains=search_query) |
#                     Q(user__firstName__icontains=search_query) |
#                     Q(user__lastName__icontains=search_query)
#                 )

#             if not pending_kycs.exists():
#                 return Response({"message": "No KYC requests found."}, status=status.HTTP_200_OK)

#             paginator = CustomPageNumberPagination()
            
#             try:
#                 result_page = paginator.paginate_queryset(pending_kycs, request)
#                 if not result_page:
#                     return Response({"message": "No KYC requests found."}, status=status.HTTP_200_OK)
#             except NotFound:  # Handle invalid page numbers
#                 return Response({"message": "No KYC requests found."}, status=status.HTTP_200_OK)

#             serializer = KYCSerializer(result_page, many=True)
#             return paginator.get_paginated_response(serializer.data)

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# correct code 

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.http import urlencode 

class PendingKYCListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Fetch all KYC records (filter for pending ones if needed)
            pending_kycs = KYC.objects.all().order_by('-id')

            # Get the search query from the request
            search_query = request.GET.get('q', '').strip()

            # Apply search filter if a search query is provided
            if search_query:
                pending_kycs = pending_kycs.filter(
                    Q(user__firstName__icontains=search_query) | 
                    Q(user__lastName__icontains=search_query) | 
                    Q(user__fullName__icontains=search_query)
                )

            # 🔹 Debug: Print filtered count
            print(f"Filtered pending KYCs count: {pending_kycs.count()}")


            # ✅ Allow dynamic page size (default=10, options: 10, 25, 50)
            allowed_page_sizes = [10, 25, 50]  # Allowed values
            try:
                items_per_page = int(request.GET.get('page_size', 10))  # Get page_size from request
                if items_per_page not in allowed_page_sizes:  
                    items_per_page = 10  # If invalid, fallback to default
            except ValueError:
                items_per_page = 10  # If conversion fails, fallback to default

            # Pagination parameters
            page = request.GET.get('page_number', 1)
            paginator = Paginator(pending_kycs, items_per_page)
            paginated_kycs = paginator.get_page(page)  # Auto-handles invalid pages


            # Serialize the paginated queryset
            serializer = KYCSerializer(paginated_kycs, many=True)

            # Preserve query parameters
            query_params = request.GET.copy()
            base_url = request.build_absolute_uri(request.path)

            next_page = None
            prev_page = None

            if paginated_kycs.has_next():
                query_params['page'] = paginated_kycs.next_page_number()
                next_page = f"{base_url}?{urlencode(query_params)}"

            if paginated_kycs.has_previous():
                query_params['page'] = paginated_kycs.previous_page_number()
                prev_page = f"{base_url}?{urlencode(query_params)}"

            return Response({
                "count": paginator.count,
                "next": next_page,
                "previous": prev_page,
                "results": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#kyc verification by admin
class KYCVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated, ]  # Only admins can access KYC requests
    def post(self, request, kyc_id, *args, **kwargs):
        try:
            kyc = KYC.objects.get(id=kyc_id)
        except KYC.DoesNotExist:
            return Response({"detail": "KYC request not found."}, status=status.HTTP_404_NOT_FOUND)
        
        action = request.data.get('action')
        if not action:
            return Response({"detail": "Action is required (approve/reject)."}, status=status.HTTP_400_BAD_REQUEST)
        user_email = kyc.user.email 
        from_email = default_from_email,
        reason = request.data.get('reason', 'No reason provided')
        if action.lower() == 'approve':
            kyc.status = 'approved'
            kyc.is_verified = True  
            kyc.verified_by = request.user 
            kyc.save()
            # Send approval email
            send_kyc_email_async.delay(user_email, from_email, kyc.user.firstName, 'approve', reason)
            # Send approval email
            # send_mail(
            #     subject="Your KYC has been approved",
            #     message="Congratulations! Your KYC request has been approved.",
            #     from_email=from_email,
            #     recipient_list=[user_email],
            #     fail_silently=False,
            # )
            return Response({
                "message": "KYC approved successfully.",
                "kyc_data": KYCSerializer(kyc).data
            }, status=status.HTTP_200_OK)
            
        elif action.lower() == 'reject':
            kyc.status = 'rejected'
            kyc.is_verified = False  
            kyc.save() 
            # Send rejection email
            send_kyc_email_async.delay(user_email, from_email, kyc.user.firstName, 'reject', reason)
               
            return Response({
                "message": "KYC rejected.",
                "kyc_data": KYCSerializer(kyc).data
            }, status=status.HTTP_200_OK)

        else:
            return Response({"detail": "Invalid action. Use 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)

#store sssion logs last login
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    pagination_class = None
    ip_address = request.META.get('REMOTE_ADDR')
    session_key = request.session.session_key
    UserActivityLog.objects.create(
        user=user,
        last_login_time=timezone.now(),
        ip_address=ip_address,
        session_key=session_key
    )
#last logout time
@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    pagination_class = None
    session_key = request.session.session_key
    try:
        activity_log = UserActivityLog.objects.filter(user=user, session_key=session_key).latest('last_login_time')
        activity_log.mark_logout()
    except UserActivityLog.DoesNotExist:
        pass  

class UserActivityLogListView(ListAPIView):
    pagination_class = None
    queryset = UserActivityLog.objects.all()
    serializer_class = UserActivityLogSerializer
    permission_classes = [IsAuthenticated]  # Change if you want different permissions
    def get_queryset(self):
        user = self.request.user
        return UserActivityLog.objects.filter(user=user)  # Optional: filter logs by logged-in user    

class UserActivityLogListView(ListAPIView):
    pagination_class = None
    serializer_class = UserActivityLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return activity logs for the logged-in user
        return UserActivityLog.objects.filter(user=self.request.user).order_by('-last_login_time')

#last login api
class LastLoginoldActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            last_two_login_activities = UserActivityLog.objects.filter(
                user=request.user, action_type='login'
            ).order_by('-last_login_time')[:2]
            if last_two_login_activities:
                if len(last_two_login_activities) == 1:
                    last_login_activity = last_two_login_activities[0]
                else:
                    # If there are at least two, get the second latest
                    last_login_activity = last_two_login_activities[1]
            response_data = {
                'last_login_time': last_login_activity.last_login_time,
                'last_ip': last_login_activity.ip_address,
                'session_key': last_login_activity.session_key,
                # 'is_logged_out': last_login_activity.logout_time is not None,
            }

            return Response(response_data)
        except UserActivityLog.DoesNotExist:
            return Response({"error": "No login activity found."}, status=404)
            
class LastLoginActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        last_two_login_activities = UserActivityLog.objects.filter(
            user=request.user, action_type='login'
        ).order_by('-last_login_time')[:2]

        if not last_two_login_activities:
            return Response({"error": "No login activity found."}, status=404)

        # If only one record exists, return that, otherwise return the second most recent login
        last_login_activity = last_two_login_activities[0] if len(last_two_login_activities) == 1 else last_two_login_activities[1]

        response_data = {
            'last_login_time': last_login_activity.last_login_time,
            'last_ip': last_login_activity.ip_address,
            'session_key': last_login_activity.session_key,
            # 'is_logged_out': last_login_activity.logout_time is not None,
        }

        return Response(response_data)
#get all city names
class Get_city_data(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs): 
        try:
            city = cities.objects.all()[:10]
            serializer = CitesSerializer(city, many=True)
        except cities.DoesNotExist:
            return Response({"error": "city not found."}, status=404)   
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

#search city name
class CitySearchView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        query = request.GET.get('city', '')  
        if query:
            city = cities.objects.filter(name__icontains=query)
            serializer = CitesSerializer(city, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)

#get all states name
class GetStatesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        try:
            state=State.objects.all()    
            ser=StatesSerializers(state,many=True)
        except State.DoesNotExist:
            return Response({"error": "state not found."}, status=404)  
        return Response({
            "status":"sucess",
            "data":ser.data }, status=status.HTTP_200_OK)

class SearchStatesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        query = request.GET.get('state', '')  
        if query:
            city = State.objects.filter(name__icontains=query)
            serializer = StatesSerializers(city, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)      

#segment crud apis
class SegmentlistAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        try:
            segments = Segment.objects.all().order_by('-id')
            serializer = SegmentSerializer(segments, many=True)
        except Segment.DoesNotExist:
            return Response({"error": "Segments not found."}, status=404)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class SegmentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    # def get(self, request, *args, **kwargs):
    #     try:
    #         segments = Segment.objects.all()
    #         serializer = SegmentSerializer(segments, many=True)
    #     except Segment.DoesNotExist:
    #         return Response({"error": "Segments not found."}, status=404)
        
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    def get(self, request, *args, **kwargs):
        segments = Segment.objects.all().order_by('-id')
        search_query = request.query_params.get('q', '').strip()
        if search_query:
            segments = segments.filter(Q(name__icontains=search_query)|
                                       Q(status__icontains=search_query)|
                                       Q(short_name__icontains=search_query))
            
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(segments, request)
        serializer = SegmentSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        serializer = SegmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            segment = Segment.objects.get(pk=kwargs.get('pk'))
        except Segment.DoesNotExist:
            return Response({"detail": "Segment not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SegmentSerializer(segment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Segment updated successfully.')
            return Response({"msg": "Segment updated successfully.", 'data': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            segment = Segment.objects.get(pk=kwargs.get('pk'))
            segment.delete()
            return Response({"msg": "Segment deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Segment.DoesNotExist:
            return Response({"detail": "Segment not found."}, status=status.HTTP_404_NOT_FOUND)

class CategorylistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            category_list = categories.objects.all().order_by('-id')
            serializer = CategorySerializer(category_list, many=True)
        except categories.DoesNotExist:
            return Response({"error": "Categories not found."}, status=404)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class CategoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # def get(self, request, *args, **kwargs):
    #     try:
    #         category_list = categories.objects.all()
    #         serializer = CategorySerializer(category_list, many=True)
    #     except categories.DoesNotExist:
    #         return Response({"error": "Categories not found."}, status=404)
        
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    def get(self, request, *args, **kwargs):
        category_list = categories.objects.all().order_by('-id')
        search_query = request.query_params.get('q', '').strip()
        if search_query:
            category_list = category_list.filter(Q(name__icontains=search_query))
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(category_list, request)
        serializer = CategorySerializer(result_page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
    def post(self, request, *args, **kwargs):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            category = categories.objects.get(pk=kwargs.get('pk'))
        except categories.DoesNotExist:
            return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Category updated successfully.')
            return Response({"msg": "Category updated successfully.", 'data': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            category = categories.objects.get(pk=kwargs.get('pk'))
            category.delete()
            return Response({"msg": "Category deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except categories.DoesNotExist:
            return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)


class LicenseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            license_list = License.objects.all().order_by('-id')
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(license_list, request)
            serializer = LicenseSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except License.DoesNotExist:
            return Response({"error": "Licenses not found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        serializer = LicenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            license_obj = License.objects.get(pk=kwargs.get('pk'))
        except License.DoesNotExist:
            return Response({"detail": "License not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = LicenseSerializer(license_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "License updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            license_obj = License.objects.get(pk=kwargs.get('pk'))
            license_obj.delete()
            return Response({"msg": "License deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except License.DoesNotExist:
            return Response({"detail": "License not found."}, status=status.HTTP_404_NOT_FOUND)


#serices crud
class ServicelistAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            services = Services.objects.all().order_by('-id')
            serializer = ServiceSerializer(services, many=True)
        except Services.DoesNotExist:
            return Response({"error": "serices not found."}, status=404)
        return Response(serializer.data, status=status.HTTP_200_OK) 

class ServiceAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        services = Services.objects.all().order_by('-id')
        search_query = request.query_params.get('q', '').strip()
        if search_query:
            services = services.filter(Q(service_name__icontains=search_query))
            
        paginator = CustomPageNumberPagination()  
        result_page = paginator.paginate_queryset(services, request)  
        serializer = ServiceSerializer(result_page, many=True)  
        return paginator.get_paginated_response(serializer.data)  
    
    def post(self, request, *args, **kwargs):
        serializer = ServiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Service created successfully.", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            service = Services.objects.get(pk=kwargs.get('pk'))
        except Services.DoesNotExist:
            return Response({"detail": "Service not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ServiceSerializer(service, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Service updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, *args, **kwargs):
        try:
            service = Services.objects.get(pk=kwargs.get('pk'))
            service.delete()
            return Response({"msg": "Services deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Services.DoesNotExist:
            return Response({"detail": "Services not found."}, status=status.HTTP_404_NOT_FOUND)

#group services api
class GroupServicelistView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            logger.debug("GroupServiceView GET request received")  
            group_ser = GroupService.objects.all().order_by('-id')
            # Serialize the data
            serializer = GroupServiceSerializer(group_ser, many=True)
            serialized_data = serializer.data
            for item in serialized_data:
                json_data = item.get('json_data', None)
                if json_data is None:
                    json_data = []
                service_names = [entry.get('ServiceName') for entry in json_data if isinstance(entry, dict)]
                item['service_count'] = len(service_names)
                
            return Response(serialized_data, status=200)
        except GroupService.DoesNotExist:
            logger.error("GroupService not found.")   
            return Response({"error": "GroupService not found."}, status=404)
        except Exception as e:
            logger.critical("An unexpected error occurred: %s", str(e))
            return Response({"error": "An unexpected error occurred."}, status=500)

class GroupServiceView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            logger.debug("GroupServiceView GET request received")  # DEBUG message
            
            group_ser = GroupService.objects.all().order_by('-id')
            search_query = request.query_params.get('q', '').strip()
            group_ser = group_ser.filter(
                Q(group_name__icontains=search_query) 
            )
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(group_ser, request)
            
            # Modify the serialized data to include `service_count`
            serializer = GroupServiceSerializer(result_page, many=True)
            serialized_data = serializer.data

            # Add `service_count` to each item in the serialized data
            for item in serialized_data:
                json_data = item.get('json_data', None)
                
                # If json_data is None, set it to an empty list
                if json_data is None:
                    json_data = []
                service_names = [entry.get('ServiceName') for entry in json_data if isinstance(entry, dict)]
                item['service_count'] = len(service_names)

            # return paginator.get_paginated_response(serialized_data)
        except GroupService.DoesNotExist:
            logger.error("GroupService not found.")   
            return Response({"error": "GroupService not found."}, status=404)

        except Exception as e:
            logger.critical("An unexpected error occurred: %s", str(e))  
            return Response({"error": "An unexpected error occurred."}, status=500)

        return paginator.get_paginated_response(serialized_data)

    def post(self, request, *args, **kwargs):
        serializer = GroupServiceUpdateSerializer(data=request.data)
        if serializer.is_valid():
            group_service=serializer.save()
            group_service=GroupServiceSerializer(group_service)
            return Response(group_service.data, status=status.HTTP_201_CREATED)
        else:
            # Print errors to debug
            print(serializer.errors)  
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            group_service = GroupService.objects.get(pk=kwargs.get('pk'))
        except GroupService.DoesNotExist:
            return Response({"detail": "GroupService not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = GroupServiceUpdateSerializer(group_service, data=request.data, partial=True)
        if serializer.is_valid():
            group_services=serializer.save()
            ser=GroupServiceSerializer(group_services)
            return Response({"msg": "GroupService updated successfully.", 'data': ser.data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, *args, **kwargs):
        try:
            service = GroupService.objects.get(pk=kwargs.get('pk'))
            service.delete()
            return Response({"msg": "GroupService deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except GroupService.DoesNotExist:
            return Response({"detail": "GroupService not found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, *args, **kwargs):#delete json data 
        try:
            group_service = GroupService.objects.get(pk=kwargs.get('pk'))  # Get the group service by ID
        except GroupService.DoesNotExist:
            return Response({"detail": "GroupService not found."}, status=status.HTTP_404_NOT_FOUND)

        s_no_to_delete = request.data.get('s_no', None)

        if s_no_to_delete is None:
            return Response({"error": "S.No is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Filter out the entry from `json_data` that matches the `S.No`
        updated_json_data = [
            entry for entry in group_service.json_data 
            if entry.get('S.No') != s_no_to_delete
        ]

        # If no entry was removed, return an error
        if len(updated_json_data) == len(group_service.json_data):
            return Response({"error": f"Entry with S.No {s_no_to_delete} not found."}, status=status.HTTP_404_NOT_FOUND)

        # Update the `json_data` field and save the updated object
        group_service.json_data = updated_json_data
        group_service.save()

        return Response({
            "msg": f"Entry with S.No '{s_no_to_delete}' deleted successfully.",
            "updated_data": GroupServiceSerializer(group_service).data
        }, status=status.HTTP_200_OK)

#api for update json data inside group service
class GroupServiceJsonUpdateView(APIView):
    def patch(self, request, *args, **kwargs):
        try:
            group_service = GroupService.objects.get(pk=kwargs.get('pk'))  # Get the group service by ID
        except GroupService.DoesNotExist:
            return Response({"detail": "GroupService not found."}, status=status.HTTP_404_NOT_FOUND)

        # The identifier of the entry to be updated, in this case, 'S.No'
        s_no_to_update = request.data.get('s_no', None)
        update_data = request.data.get('update_data', None)

        if s_no_to_update is None:
            return Response({"error": "S.No is required."}, status=status.HTTP_400_BAD_REQUEST)

        if update_data is None:
            return Response({"error": "Update data is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Flag to check if entry is found
        entry_updated = False

        # Iterate through the json_data and update the relevant entry
        updated_json_data = []
        for entry in group_service.json_data:
            if entry.get('S.No') == s_no_to_update:
                entry_updated = True
                # Update the entry with new data
                entry.update(update_data)
            updated_json_data.append(entry)

        # If no entry was updated, return an error
        if not entry_updated:
            return Response({"error": f"Entry with S.No {s_no_to_update} not found."}, status=status.HTTP_404_NOT_FOUND)

        # Update the `json_data` field and save the updated object
        group_service.json_data = updated_json_data
        group_service.save()

        return Response({
            "msg": f"Entry with S.No '{s_no_to_update}' updated successfully.",
            "updated_data": GroupServiceSerializer(group_service).data
        }, status=status.HTTP_200_OK)

#get services inside group by id
class GetGroupServiceAPIView(APIView):
    def get(self, request, pk, *args, **kwargs): 
        try:
            user = GroupService.objects.get(pk=pk)  
            serializer = GroupServiceSerializer(user)
        except GroupService.DoesNotExist:
            return Response({"detail": "service not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.data, status=status.HTTP_200_OK)       

class Group_ServicesQtyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id, *args, **kwargs):
        try:
            logger.debug("GroupServiceDetailView GET request received for ID: %s", id)

            # Retrieve the GroupService object based on the provided ID
            group_service = GroupService.objects.get(id=id)
            
            # Extract the relevant fields
            json_data = group_service.json_data
            formatted_data = [
                {
                    "Qty": entry.get("Qty"),
                    "ServiceName": entry.get("ServiceName")
                }
                for entry in json_data if isinstance(entry, dict)
            ]
            
            # Prepare the response
            response_data = {
                "id": group_service.id,
                "group_name": group_service.group_name,
                "json_data": formatted_data
            }

            logger.info("Response prepared successfully for ID: %s", id)
            return Response(response_data, status=status.HTTP_200_OK)
        
        except GroupService.DoesNotExist:
            logger.error("GroupService with ID %s not found.", id)
            return Response({"error": "GroupService not found."}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.critical("An unexpected error occurred: %s", str(e))
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class StrategyAPIView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        strategies = Strategies.objects.all().order_by('-id')
        search_query = request.query_params.get('q', '').strip()
        if search_query:
            strategies = strategies.filter(Q(name__icontains=search_query))
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(strategies, request)
        serializer = GetStrategySerializer(result_page, many=True)
        # logging.info("strategy of data>>>>>",serializer.data)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = StrategySerializer(data=request.data)
        if serializer.is_valid():
            strategy_instance=serializer.save()
             # Now use the saved instance to serialize the data
            get_strategy_serializer = GetStrategySerializer(strategy_instance)

            return Response({"detail": "Strategy created successfully.", "data": get_strategy_serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, *args, **kwargs):
        try:
            strategy = Strategies.objects.get(pk=kwargs.get('pk'))
            # print("Request data:", request.data, indent=4)  # Convert request data to JSON string for printing

        except Strategies.DoesNotExist:
            return Response({"detail": "Strategy not found."}, status=status.HTTP_404_NOT_FOUND)
           
        serializer = StrategySerializer(strategy, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Strategy updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            strategy = Strategies.objects.get(pk=kwargs.get('pk'))
            strategy.delete()
            return Response({"msg": "Strategy deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Strategies.DoesNotExist:
            return Response({"detail": "Strategy not found."}, status=status.HTTP_404_NOT_FOUND)
        
class GetStrategyAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk, *args, **kwargs): 
        try:
            user = Strategies.objects.get(pk=pk)  
            serializer = GetStrategySerializer(user)  
        except Strategies.DoesNotExist:
            return Response({"detail": "Strategy not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)        

class BrokerView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        broker_id = kwargs.get('pk', None)
        
        if broker_id:
            try:
                broker = Broker.objects.get(pk=broker_id)

                serializer = GetBrokerSerializer(broker)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Broker.DoesNotExist:
                return Response({"detail": "Broker not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            brokers = _ensure_default_broker_catalog()
            search_query = request.query_params.get('q', '').strip()
            if search_query:
                brokers = brokers.filter(Q(broker_name__icontains=search_query))
            serializer = GetBrokerSerializer(brokers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = GetBrokerSerializer(data=request.data)
        if serializer.is_valid():
            broker = serializer.save()
            return Response(GetBrokerSerializer(broker).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        broker_id = kwargs.get('pk', None)
        if not broker_id:
            return Response({"detail": "Broker ID is required for updating."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            broker = Broker.objects.get(pk=broker_id)
        except Broker.DoesNotExist:
            return Response({"detail": "Broker not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetBrokerSerializer(broker, data=request.data)
        if serializer.is_valid():
            broker = serializer.save()
            return Response(GetBrokerSerializer(broker).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        broker_id = kwargs.get('pk', None)
        if not broker_id:
            return Response({"detail": "Broker ID is required for deletion."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            broker = Broker.objects.get(pk=broker_id)
            broker.delete()
            return Response({"detail": "Broker deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Broker.DoesNotExist:
            return Response({"detail": "Broker not found."}, status=status.HTTP_404_NOT_FOUND)

import time

class ClientFilterView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user 
        if is_superadmin_user(user):
            clients = User.objects.filter(type_of_user='is_client', is_client=True).order_by('-id')
        # elif user.role and user.role.name.lower() == 'sub-admin' or user.role.name=='Sub-Admin':
            # print("sub-admin.........")
            # clients = User.objects.filter(assigned_client=user).order_by('-id')
        else:
            clients = User.objects.filter(Q(type_of_user='is_client') & (Q(created_by=user) 
            | Q(assigned_client=user))).order_by('-id')
            # clients = User.objects.filter(type_of_user='is_client',is_client=True, created_by=user).order_by('-id')
                # Apply additional filters based on query parameters
                # Get the search query from request params
        search_query = request.query_params.get('q', '').strip()

        # If a search query is provided, search across multiple fields
        if search_query:
            clients = clients.filter(
                Q(userName__icontains=search_query) |
                Q(fullName__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phoneNumber__icontains=search_query)
            )
        license_type = request.query_params.get('client_type') 
        trading_status = request.query_params.get('trading_type')  
        # broker_type = request.query_params.get('broker_type') 
        
        if license_type:
            clients = clients.filter(license__name__iexact=license_type)
        
        if trading_status:
            clients = clients.filter(is_enable=(trading_status.lower() == 'on'))


        # if broker_type:
        #     clients = clients.filter(Broker__name__icontains=broker_type)
        # Apply pagination and serialize the data
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(clients, request)
        serializer = ClientListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

#Client ADD Api
class ClientCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user 
        if is_superadmin_user(user):
            clients = User.objects.filter(type_of_user='is_client', is_client=True).order_by('-id')
        # elif user.role and user.role.name.lower() == 'sub-admin' or user.role.name=='Sub-Admin':
            # print("sub-admin.........")
            # clients = User.objects.filter(assigned_client=user).order_by('-id')
        else:
            clients = User.objects.filter(Q(type_of_user='is_client') & (Q(created_by=user) 
            | Q(assigned_client=user))).order_by('-id')
            # clients = User.objects.filter(type_of_user='is_client',is_client=True, created_by=user).order_by('-id')
                # Apply additional filters based on query parameters
        search_query = request.query_params.get('q', '').strip()

        # If a search query is provided, search across multiple fields
        if search_query:
            clients = clients.filter(
                Q(userName__icontains=search_query) |
                Q(fullName__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phoneNumber__icontains=search_query)
            )        
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(clients, request)
        serializer = ClientListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        start_time=time.time()
        print("data>>>>",data)
        serializer = ClientCreateSerializer(data=data)
        password = get_random_string(length=12)
        if serializer.is_valid():
            client = serializer.save(created_by=request.user)
            client.set_password(password)  
            client.external_user=False
            client.save() 
            
                    # Handle segment and subsegment addition
            segment_id = data.get("segment")
            subsegments = data.get("subsegment", [])
            _sync_client_trade_settings_from_group_service(
                client,
                fallback_segment_id=segment_id,
                fallback_subsegments=subsegments,
            )
            _sync_client_multi_leg_settings(client)
        
            end_time = time.time()  # Record the end time
            execution_time = end_time - start_time  # Calculate the total time
            print(f"client create API executed in--------- {execution_time:.4f} seconds") 
            start_time=time.time()
            # Email is optional now, so client creation must not fail if email is
            # blank or the async email transport is unavailable.
            if client.email:
                try:
                    EmailService.send_password_email(
                        client.email,
                        password,
                        client.firstName,
                        login_link,
                        support_email,
                        help_center_link,
                        company_website,
                        contact_number,
                    )
                except Exception as exc:
                    logger.warning(
                        "Client %s created but welcome email failed: %s",
                        client.id,
                        exc,
                    )
            end_time = time.time()  # Record the end time
            execution_time = end_time - start_time  # Calculate the total time
            return Response(ClientListSerializer(client).data, status=status.HTTP_201_CREATED)
        return Response(
            {
                "detail": "Failed to add client",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def put(self, request, *args, **kwargs):
        client_id = kwargs.get('pk')
        client = get_object_or_404(User, id=client_id)

        serializer = ClientupdateListSerializer(client, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()

            segment_id = request.data.get("segment")
            subsegments = request.data.get("subsegment", [])
            _sync_client_trade_settings_from_group_service(
                client,
                fallback_segment_id=segment_id,
                fallback_subsegments=subsegments,
            )
            _sync_client_multi_leg_settings(client)

                
            return Response(ClientListSerializer(client).data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, *args, **kwargs):
        client_id = kwargs.get('pk', None)
        if not client_id:
            return Response({"detail": "client ID is required for deletion."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            broker = User.objects.get(pk=client_id)
            broker.delete()
            return Response({"detail": "client deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Broker.DoesNotExist:
            return Response({"detail": "client_id not found."}, status=status.HTTP_404_NOT_FOUND)


class ClientOnboardingStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Get the filter type from the request
            filter_type = request.GET.get('filter', None)
            today = datetime.now().date()
            start_date = None
            end_date = None

            # If no filter type is provided, return a response with null values
            if filter_type is None:
                return Response({
                    "filter_type": None,
                    "client_count": 0,
                    "start_date": None,
                    "end_date": None,
                    "data": []
                }, status=200)

            # Determine the date range based on the filter type
            if filter_type == 'today':
                start_date = today
                end_date = today
            elif filter_type == 'yesterday':
                start_date = today - timedelta(days=1)
                end_date = today - timedelta(days=1)
            elif filter_type == 'this_week':
                start_date = today - timedelta(days=today.weekday())  # Start of the week
                end_date = today
            elif filter_type == 'this_month':
                start_date = today.replace(day=1)  # Start of the month
                end_date = today
            elif filter_type == 'date_range':
                # Get custom date range from query parameters
                from_date = request.GET.get('from_date', None)
                to_date = request.GET.get('to_date', None)
                if from_date and to_date:
                    start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
                    end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
                else:
                    return Response({"message": "Both from_date and to_date are required for date range."}, status=400)
            else:
                return Response({"error": "Invalid filter type."}, status=400)

            # Query to count clients created within the specified date range
            client_counts = (
                User.objects
                .filter(
                    created_at__date__range=(start_date, end_date),
                    type_of_user='is_client'  # Filter to include only clients
                )
                .extra({'created_date': 'date(created_at)'})  # Extract the date part
                .values('created_date')  # Group by the created date
                .annotate(clients=Count('id'))  # Count clients for each date
                .order_by('created_date')  # Order by date
            )

            # Prepare the response data
            response_data = {
                "filter_type": filter_type,
                "start_date": start_date,
                "end_date": end_date,
                "data": [
                    {"date": entry['created_date'], "clients": entry['clients']}
                    for entry in client_counts
                ]
            }

            # Calculate total client count
            total_client_count = sum(entry['clients'] for entry in client_counts)

            # Add total client count to the response
            response_data["client_count"] = total_client_count

            return Response(response_data, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class ClientTradingStatusCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Determine which clients to include based on user role
        if is_superadmin_user(user):
            # Super-admin can see all clients
            clients = User.objects.filter(type_of_user='is_client', is_client=True)
        elif is_admin_user(user):
            # Sub-admin can see only their assigned clients
            clients = User.objects.filter(assigned_client=user, type_of_user='is_client', is_client=True)
        else:
            # If the user is neither super-admin nor sub-admin, return an empty response or handle accordingly
            return Response({"detail": "You do not have permission to view this data."}, status=403)

        # Count active and inactive clients based on the is_enable field
        active_count = clients.filter(is_enable=True).count()
        inactive_count = clients.filter(is_enable=False).count()

        # Prepare the response data
        response_data = {
            "active_clients": active_count,
            "inactive_clients": inactive_count
        }

        return Response(response_data, status=200)


class AssignClientToStrategyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, pk):
        strategy = get_object_or_404(Strategies, pk=pk)
        serializer = StrategyAssignSerializer(strategy, data=request.data, partial=True)
        
        if serializer.is_valid():
            strategy = serializer.save()
            for client in strategy.clients.all():
                _sync_client_multi_leg_settings(client)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetclientbyidPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request, pk, *args, **kwargs): 
        try:
            user = User.objects.get(pk=pk)  
            serializer = ClientListdetailsSerializer(user)  
        except Strategies.DoesNotExist:
            return Response({"detail": "client id not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)        

class GetStrategyClientView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user 
        try:
            if is_superadmin_user(user):
                clients = User.objects.filter(type_of_user='is_client', is_client=True).order_by('-id')
            elif is_admin_user(user):
                clients = User.objects.filter(assigned_client=user).order_by('-id')
            else:
                clients = User.objects.filter(type_of_user='is_client', created_by=user).order_by('-id')
            serializer = ClientListSerializer(clients, many=True)

        except Strategies.DoesNotExist:
            return Response({"detail": "client id not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)    
#Client penel setting
class ClientTreadSettingView(APIView):
   
    def get(self, request, pk, *args, **kwargs):
        try:
            # Fetch the client with the specified ID
            client = User.objects.get(pk=pk)
            
            # Access Group_service's json_data directly
            group_service = client.Group_service
            if not group_service:
                return Response({"detail": "Group service not found."}, status=status.HTTP_404_NOT_FOUND)
            
            # Ensure json_data is a list and extract ServiceName values
            json_data = group_service.json_data if isinstance(group_service.json_data, list) else []
            service_names = [service.get("ServiceName") for service in json_data if service.get("ServiceName")]

            return Response({"service_names": service_names}, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({"detail": "Client not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self, request, *args, **kwargs):
        client_id = kwargs.get('pk')
        client = get_object_or_404(User, id=client_id)

        serializer = ClientupdateListSerializer(client, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(ClientListSerializer(client).data, status=status.HTTP_201_CREATED)
#client expiry list
class ClientsDataView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            # Get the current date
            current_date = timezone.now().date()
            print(current_date)
            # Fetch clients whose end_date_client has expired and who are of type 'is_client'
            expiry_client = User.objects.filter(client_expiry_status=True, type_of_user='is_client',is_client=True)

            # Apply search filter
            search_query = request.query_params.get('q', '').strip()
            if search_query:
                expiry_client = expiry_client.filter(
                    Q(firstName__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(phoneNumber__icontains=search_query)
                )

            # Apply pagination
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(expiry_client, request)

            # Serialize the paginated data
            serializer = ClientListSerializer(result_page, many=True)

            # Return paginated response
            return paginator.get_paginated_response({"expiry_client_list": serializer.data})

        except User.DoesNotExist:
            return Response({"detail": "Client not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        



class SubSegmentsView(APIView):
    def post(self, request):
        """
        Create a new SubSegment.
        """
        serializer = SubSegmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        """
        Update an existing SubSegment by ID.
        """
        sub_segment = get_object_or_404(SubSegment, pk=pk)
        serializer = SubSegmentSerializer(sub_segment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Delete a SubSegment by ID.
        """
        sub_segment = get_object_or_404(SubSegment, pk=pk)
        sub_segment.delete()
        return Response({"message": "SubSegment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    def get(self, request):
        try:
            segment = SubSegment.objects.all()
        except SubSegment.DoesNotExist:
            return Response({"error": "Segment not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = SubSegmentSerializer(segment, many=True)
        
        return Response({"sub_segments": serializer.data}, status=status.HTTP_200_OK)

class UpdateClientTradeSettingAPIView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    queryset = ClientTradeSetting.objects.all()
    serializer_class = ClientTradeSettingSerializer

    def update(self, request, *args, **kwargs):
        # Get the authenticated client from the request
        client = request.user
        
        # Extract segment and sub_segment from the request data
        segment = request.data.get('segment')
        sub_segment = request.data.get('sub_segment')

        if not segment or not sub_segment:
            return Response(
                {"detail": "Both segment and sub_segment must be provided."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to fetch the existing trade setting based on client, segment, and sub_segment
        try:
            trade_setting = ClientTradeSetting.objects.get(client=client, segment=segment, sub_segment=sub_segment)
        except ClientTradeSetting.DoesNotExist:
            return Response({"detail": "TradeSetting not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize and validate the incoming data (allow partial updates)
        serializer = self.get_serializer(trade_setting, data=request.data, partial=True)
        
        if serializer.is_valid():
            expiry_date = request.data.get('expiry_date')
            print("expiry_date>>>",expiry_date)
            if expiry_date:
                # Convert to Asia/Kolkata timezone
                india_tz = pytz_timezone('Asia/Kolkata')
                expiry_date = datetime.fromisoformat(expiry_date)
                expiry_date = make_aware(expiry_date, timezone=india_tz)
                trade_setting.expiry_date = expiry_date

            if serializer.validated_data.get("order_type") == "MARKET":
                serializer.validated_data["buffer_percentage"] = None

            # Save the updated trade setting
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetTradeSettingAPIView(generics.ListAPIView):
    serializer_class = GetclientTradedataSettingSerializer#ClientTradeSettingSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        """
        This method returns the queryset filtered by client, segment, and sub_segment.
        """
        client = self.request.query_params.get('client', None)
        segment = self.request.query_params.get('segment', None)
        sub_segment = self.request.query_params.get('sub_segment', None)
        
        queryset = ClientTradeSetting.objects.all()
        
        # Apply filters if present
        if client:
            queryset = queryset.filter(client=client)
        if segment:
            queryset = queryset.filter(segment=segment)
        if sub_segment:
            queryset = queryset.filter(sub_segment=sub_segment)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        Override the list method to include a response with filtered data.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClientMultiLegTradeSettingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        client_id = request.query_params.get('client')
        strategy_id = request.query_params.get('strategy')
        include_locked = str(request.query_params.get('include_locked', '')).lower() in {'1', 'true', 'yes'}
        resolved_client = None

        queryset = ClientMultiLegStrategySetting.objects.select_related(
            'strategy',
            'segment',
            'client',
        )

        if client_id:
            if not is_admin_or_superadmin(request.user) and int(client_id) != request.user.id:
                return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            resolved_client_id = int(client_id)
            resolved_client = User.objects.filter(id=resolved_client_id).first()
            queryset = queryset.filter(client_id=client_id)
        else:
            resolved_client_id = request.user.id
            resolved_client = request.user
            queryset = queryset.filter(client=request.user)

        if resolved_client:
            _sync_client_multi_leg_settings(resolved_client)
            queryset = ClientMultiLegStrategySetting.objects.select_related(
                'strategy',
                'segment',
                'client',
            ).filter(client=resolved_client)

        if strategy_id:
            queryset = queryset.filter(strategy_id=strategy_id)

        if include_locked and not strategy_id:
            assigned_settings = {
                setting.strategy_id: setting
                for setting in queryset
            }
            all_multi_leg_strategies = Strategies.objects.filter(
                execution_mode=Strategies.EXECUTION_MODE_MULTI_LEG,
                is_active=True,
            ).select_related('segment').order_by('name')
            payload = []
            for strategy in all_multi_leg_strategies:
                setting = assigned_settings.get(strategy.id)
                if setting:
                    item = ClientMultiLegTradeSettingReadSerializer(setting).data
                    item['is_assigned'] = True
                    item['is_locked'] = False
                    payload.append(item)
                    continue

                payload.append({
                    'id': None,
                    'client': resolved_client_id,
                    'strategy': strategy.id,
                    'strategy_name': strategy.name,
                    'strategy_execution_mode': strategy.execution_mode,
                    'multi_leg_template': strategy.multi_leg_template,
                    'multi_leg_template_label': strategy.get_multi_leg_template_display() if strategy.multi_leg_template else None,
                    'segment': SegmentSerializer(strategy.segment).data if strategy.segment else None,
                    'underlying': 'NIFTY',
                    'group_service': None,
                    'broker': None,
                    'product_type': None,
                    'order_type': None,
                    'buffer_percentage': None,
                    'quantity': None,
                    'trade_limit': None,
                    'max_loss_for_day': None,
                    'max_profit_for_day': None,
                    'expiry_date': None,
                    'start_time': None,
                    'end_time': None,
                    'is_tread_status': False,
                    'sl_type': None,
                    'stop_loss': None,
                    'target': None,
                    'legs': [],
                    'created_at': None,
                    'updated_at': None,
                    'is_assigned': False,
                    'is_locked': True,
                })
            return Response(payload, status=status.HTTP_200_OK)

        serializer = ClientMultiLegTradeSettingReadSerializer(queryset.order_by('strategy__name'), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        user = request.user
        strategy_id = request.data.get('strategy')
        if not strategy_id:
            return Response({"detail": "Strategy is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            setting = ClientMultiLegStrategySetting.objects.select_related('client', 'strategy').get(
                client=user,
                strategy_id=strategy_id,
            )
        except ClientMultiLegStrategySetting.DoesNotExist:
            return Response({"detail": "Multi-leg setting not found."}, status=status.HTTP_404_NOT_FOUND)

        request_data = request.data.copy()
        expiry_date = request_data.get('expiry_date')
        if expiry_date:
            parsed_expiry = _parse_multi_leg_expiry_date(expiry_date)
            if not parsed_expiry:
                return Response(
                    {"expiry_date": ["Expiry format is invalid. Please select a valid expiry from the dropdown."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            request_data['expiry_date'] = parsed_expiry.isoformat()

        serializer = ClientMultiLegStrategySettingSerializer(setting, data=request_data, partial=True)
        if serializer.is_valid():
            if serializer.validated_data.get("order_type") == "MARKET":
                serializer.validated_data["buffer_percentage"] = None

            serializer.save()
            return Response(
                ClientMultiLegTradeSettingReadSerializer(setting).data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        user = request.user
        strategy_id = request.data.get('strategy')
        is_trade_status = request.data.get('is_trade_status')

        if not strategy_id:
            return Response({"detail": "Strategy is required."}, status=status.HTTP_400_BAD_REQUEST)
        if is_trade_status is None or not isinstance(is_trade_status, bool):
            return Response({"detail": "'is_trade_status' must be a boolean value."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            setting = ClientMultiLegStrategySetting.objects.get(client=user, strategy_id=strategy_id)
        except ClientMultiLegStrategySetting.DoesNotExist:
            return Response({"detail": "Multi-leg setting not found."}, status=status.HTTP_404_NOT_FOUND)

        setting.is_tread_status = is_trade_status
        setting.save(update_fields=['is_tread_status', 'updated_at'])
        return Response(
            ClientMultiLegTradeSettingReadSerializer(setting).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, *args, **kwargs):
        user = request.user
        strategy_id = request.query_params.get('strategy') or request.data.get('strategy')
        if not strategy_id:
            return Response({"detail": "Strategy is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            setting = ClientMultiLegStrategySetting.objects.select_related('client', 'strategy').get(
                client=user,
                strategy_id=strategy_id,
            )
        except ClientMultiLegStrategySetting.DoesNotExist:
            return Response({"detail": "Multi-leg setting not found."}, status=status.HTTP_404_NOT_FOUND)

        setting.product_type = None
        setting.order_type = "LIMIT"
        setting.buffer_percentage = None
        setting.quantity = None
        setting.trade_limit = None
        setting.max_loss_for_day = None
        setting.max_profit_for_day = None
        setting.expiry_date = None
        setting.start_time = None
        setting.end_time = None
        setting.is_tread_status = False
        setting.sl_type = None
        setting.stop_loss = None
        setting.target = None
        setting.legs = []
        setting.save(update_fields=[
            "product_type", "order_type", "buffer_percentage", "quantity", "trade_limit",
            "max_loss_for_day", "max_profit_for_day", "expiry_date", "start_time", "end_time",
            "is_tread_status", "sl_type", "stop_loss", "target", "legs", "updated_at",
        ])
        return Response(
            ClientMultiLegTradeSettingReadSerializer(setting).data,
            status=status.HTTP_200_OK,
        )
class UpdateTradeSettingStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Get the authenticated client
            client = request.user
            
            # Get the 'segment' parameter from the query string
            segment_name = request.query_params.get('segment', None)
            
            # Filter trade settings associated with the client
            client_list = ClientTradeSetting.objects.filter(client=client)
            
            # Filter further by segment if the parameter is provided
            if segment_name and str(segment_name).strip().lower() != 'option':
                client_list = client_list.filter(segment__name__iexact=segment_name)
            
            # Serialize the data
            serializer = ClientSegementsSerializer(client_list, many=True)
            
            return Response(
                {"client_segment_list": serializer.data},
                status=status.HTTP_200_OK
            )
        
        except User.DoesNotExist:
            return Response(
                {"detail": "Client not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def patch(self, request, *args, **kwargs):
        # Get the authenticated user
        user = request.user
        
        # Extract segment, sub_segment, and is_trade_status from request data
        segment = request.data.get('segment')
        sub_segment = request.data.get('sub_segment')
        is_trade_status = request.data.get('is_trade_status')

        if is_trade_status is None:
            return Response({"detail": "'is_trade_status' field is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(is_trade_status, bool):
            return Response({"detail": "'is_trade_status' must be a boolean value."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Find the trade setting for the client based on segment and sub-segment
        try:
            trade_setting = ClientTradeSetting.objects.get(client=user, segment=segment, sub_segment=sub_segment)
        except ClientTradeSetting.DoesNotExist:
            return Response({"detail": "Trade setting not found."}, status=status.HTTP_404_NOT_FOUND)

        # Update the 'is_status' field
        try:
            # Start transaction in case of complex updates
            with transaction.atomic():
                trade_setting.is_tread_status = is_trade_status
                trade_setting.save()
                # Serialize and return updated data
                                # Create a TradeLog entry to record the update
                TradeLog.objects.create(
                    client=user,
                    trade_setting=trade_setting,
                    symbol=trade_setting.symbol,
                    is_trade_status=is_trade_status,
                    trade_date=timezone.now()
                )
                serializer = ClientTradeSettingSerializer(trade_setting)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateTradeStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        # Get the authenticated user
        user = request.user
        
        # Extract query parameters
        segment_name = request.query_params.get('segment')
        sub_segment_name = request.query_params.get('sub_segment')
        is_trade_status = request.data.get('is_trade_status')

        # Validate query parameters and the required field
        if not segment_name or not sub_segment_name:
            return Response({"detail": "'segment' and 'sub_segment' query parameters are required."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if is_trade_status is None:
            return Response({"detail": "'is_trade_status' field is required."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(is_trade_status, bool):
            return Response({"detail": "'is_trade_status' must be a boolean value."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Look up the Segment and SubSegment objects by name
        try:
            segment = Segment.objects.get(name__iexact=segment_name)
            sub_segment = SubSegment.objects.get(name__iexact=sub_segment_name)
            # Find the trade setting for the client based on segment and sub-segment
            trade_setting = ClientTradeSetting.objects.get(client=user, segment=segment, sub_segment=sub_segment)
        except Segment.DoesNotExist:
            return Response({"detail": f"Segment with name '{segment_name}' not found."}, 
                            status=status.HTTP_404_NOT_FOUND)
        except SubSegment.DoesNotExist:
            return Response({"detail": f"SubSegment with name '{sub_segment_name}' not found."}, 
                            status=status.HTTP_404_NOT_FOUND)
        except ClientTradeSetting.DoesNotExist:
            return Response({"detail": "Trade setting not found."}, 
                            status=status.HTTP_404_NOT_FOUND)

        # Update the 'is_trade_status' field
        try:
            with transaction.atomic():
                trade_setting.is_tread_status = is_trade_status
                trade_setting.save()
                TradeLog.objects.create(
                    client=user,
                    trade_setting=trade_setting,
                    symbol=trade_setting.symbol,
                    is_trade_status=is_trade_status,
                    trade_date=timezone.now()
                )
                # Serialize and return updated data
                serializer = ClientTradeSettingSerializer(trade_setting)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#Active Inactive clints for specific sub-Admin
class clientActiveInactiveView(APIView):
    # Uncomment this if authentication is required
    # permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, id, *args, **kwargs):
        try:
            user = User.objects.get(id=id, role__name='Sub-Admin')
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        current_date = timezone.now().date()

        try:
            # Retrieve active clients and set client_status to "active"
            active_clients = user.assigned_users.filter(
                type_of_user='is_client', is_client=True, client_status=True)
            
            
            # Prepare list of active clients
            active_clients_list = [
                {
                    "id": client.id,
                    "email": client.email,
                    "client_name": client.fullName,
                    "assigned_client_name": user.fullName,
                    "client_status":True,
                    "client_phone": client.phoneNumber,
                    "start_date_client":client.start_date_client,
                    "end_date_client"  :  client.end_date_client,
                }
                for client in active_clients
            ]
        except Exception as e:
            return Response({"error": "Error fetching active clients", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Retrieve inactive clients and set client_status to "inactive"
            inactive_clients = user.assigned_users.filter(
                type_of_user='is_client', is_client=True,client_status=False
            )
            # inactive_clients.update(
            # Prepare list of inactive clients
            inactive_clients_list = [
                {
                    "id": client.id,
                    "email": client.email,
                    "client_name": client.fullName,
                    "assigned_client_name": user.fullName,
                    "client_status": False,
                    "client_phone": client.phoneNumber,
                    "start_date_client":client.start_date_client,
                    "end_date_client"  :  client.end_date_client,
                }
                for client in inactive_clients
            ]
        except Exception as e:
            return Response({"error": "Error fetching inactive clients", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Combine active and inactive clients into one list
            combined_clients_list = active_clients_list + inactive_clients_list
            
            # Serialize user data with combined clients list
            user_data = UserclientSerializer(user).data
            user_data['active_inactive_clients'] = combined_clients_list
        except Exception as e:
            return Response({"error": "Error serializing user data", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(user_data, status=status.HTTP_200_OK)

# clients which are using the  group service
class ClientsByGroupServiceView(APIView):
    def get(self, request, group_service_id, *args, **kwargs):
        group_service = get_object_or_404(GroupService, id=group_service_id)

        clients = User.objects.filter(Group_service=group_service, is_client=True)
        client_data = [
            {
                "id": client.id,
                "email": client.email,
                "client_name": client.fullName,
                "phone_number": client.phoneNumber,
                "service_name": client.Group_service.group_name if client.Group_service else None,
                "license": client.license.name if client.license else None, 
                "client_status": "active" if client.client_status else "inactive",
                "start_date_client":client.start_date_client,
                "end_date_client"  :  client.end_date_client,
                
            }
            for client in clients
        ]

        return Response({"group_service": group_service.group_name, "clients": client_data}, status=status.HTTP_200_OK)

#all active clients for dashboard
class ActiveClientsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        current_date = timezone.now().date()

        if is_superadmin_user(user):
            clients = User.objects.filter(
                type_of_user='is_client', is_client=True, client_status=True
            ).order_by('-id')
        else:
            # clients =User.objects.filter(
            #     type_of_user='is_client', is_client=True, end_date_client__gt=current_date,created_by=user
            # ).order_by('-id')
            clients = User.objects.filter(
                Q(type_of_user='is_client') & Q(is_client=True) & Q(client_status=True) &
                (Q(created_by=user) | Q(assigned_client=user))
            ).order_by('-id')
        search_query = request.query_params.get('q', '').strip()    
        clients = clients.filter(
            Q(firstName__icontains=search_query) |
            Q(phoneNumber__icontains=search_query) | 
            Q(email__icontains=search_query)
        )

        # Apply pagination and serialize the data
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(clients, request)
        serializer = ClientListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
#all In-active clients for dashboard
class InactiveClientsView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        current_date = timezone.now().date()

        if is_superadmin_user(user):
            clients = User.objects.filter(
                type_of_user='is_client', is_client=True, client_status=False
            ).order_by('-id')
        else:
            # clients = User.objects.filter(
            #     type_of_user='is_client', is_client=True, end_date_client__lte=current_date,created_by=user
            # ).order_by('-id')
            clients = User.objects.filter(
                Q(type_of_user='is_client') & Q(is_client=True) & Q(client_status=False) &
                (Q(created_by=user) | Q(assigned_client=user))
            ).order_by('-id')
        search_query = request.query_params.get('q', '').strip()    
        clients = clients.filter(
            Q(firstName__icontains=search_query) |
            Q(phoneNumber__icontains=search_query) |  
            Q(email__icontains=search_query)
        )

        # Apply pagination and serialize the data
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(clients, request)
        serializer = ClientListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


# expiry clients   
class ExpiryClientsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        current_date = timezone.now().date()

        if is_superadmin_user(user):
            clients = User.objects.filter(
                type_of_user='is_client', is_client=True, end_date_client__lte=current_date,
            ).order_by('-id')
        else:
            # clients = User.objects.filter(
            #     type_of_user='is_client', is_client=True, end_date_client__lte=current_date,created_by=user
            # ).order_by('-id')
            clients = User.objects.filter(
                Q(type_of_user='is_client') & Q(is_client=True) & Q(end_date_client__lte=current_date) &
                (Q(created_by=user) | Q(assigned_client=user))
            ).order_by('-id')
        
        # Apply pagination and serialize the data
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(clients, request)
        serializer = ClientListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class GetclientdataView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self,request, *args, **kwargs): 
        try:
            client_list = ClientTradeSetting.objects.filter(is_tread_status=True)
            print(client_list)
            serializer = ClientTradeSettingSerializer(client_list,many=True)
            # print(serializer)
        
        except Strategies.DoesNotExist:
            return Response({"detail": "client id not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)  

#order -logs -list
class OrderLogListView(APIView):
    pagination_class = None
    def get(self, request, *args, **kwargs):
        # Fetch all the order logs from the database
        order_logs = SignalOrderLog.objects.all().order_by('-id')
        
        # Serialize the data
        serializer = OrderLogSerializer(order_logs, many=True)
        
        # Return the serialized data as a JSON response
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

# Get Alice-Blue orders  GET_ORDER_BOOK_URL
class GetAliceOrderBook(APIView):
    pagination_class = None
    def get(self, request, *args, **kwargs):
        # Get or regenerate the session ID
        session_id_response = get_or_regenerate_session_id(USER_ID, ALICE_API_KEY)
        # Extract sessionID from the response
        sessionID = session_id_response.get('sessionID') if isinstance(session_id_response, dict) else None  
        if not sessionID:
            return Response({
                "status": "error",
                "message": "Failed to obtain a valid session ID."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {USER_ID} {sessionID}' 
        }
        try:
 
            response = requests.get(GET_ORDER_BOOK_URL, headers=headers)
            response.raise_for_status()  
            return Response({
                "status": "success",
                "data": response.json()
            }, status=status.HTTP_200_OK)

        except requests.RequestException as req_err:
            return Response({
                "status": "error",
                "message": f"Request error: {str(req_err)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            # Handle any other exceptions
            return Response({
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#Get trad history data GET_TREAD_BOOK_URL
class GetAliceTreadBook(APIView):
    pagination_class = None
    def get(self, request, *args, **kwargs):
        # Get or regenerate the session ID
        session_id_response = get_or_regenerate_session_id(USER_ID, ALICE_API_KEY)
        # Extract sessionID from the response
        sessionID = session_id_response.get('sessionID') if isinstance(session_id_response, dict) else None  
        if not sessionID:
            return Response({
                "status": "error",
                "message": "Failed to obtain a valid session ID."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {USER_ID} {sessionID}'  # Assuming session ID is used this way
        }
        try:
            # Send a GET request to the order book endpoint
            response = requests.get(GET_TREAD_BOOK_URL, headers=headers)
            print("response>>>>>>>>>>>",response)
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
            trade_history = response.json()
            # Return the successful response data
            return Response({
                "status": "success",
                "data": trade_history
            }, status=response.status_code)

        except requests.RequestException as req_err:
            # Handle request exceptions such as timeouts, bad responses, etc.
            return Response({
                "status": "error",
                "message": f"Request error: {str(req_err)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            # Handle any other exceptions
            return Response({
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Save the order log to the database
from django.utils import timezone  

def save_webhook_signals_logs(order_type,symbol,price,strategy,json=None):#user,status,failure_reason,json=None):
                                  
    """Save order details and status into the log table."""
    try:
        SignalOrderLog.objects.create(
            signal_time=timezone.now(),  # You can change this to the actual signal time
            order_type=order_type,
            symbol=symbol,
            price=price,
            strategy=strategy,
            # user=user,  # Store the client ID here
            # status=status,
            # failure_reason=failure_reason,
            json_data=json
        )
        
        logger.info(f"signal order log saved ")
    except Exception as e:
        logger.error(f"Failed to save webhook signal order log . Reason: {str(e)}")
        
def round_price(price):
    # Get the last two digits of the price before the decimal
    price=float(price)
    last_two_digits = int(price) % 100
    
    if last_two_digits > 50:
        # Round up to the next hundred
        return int(price) - last_two_digits + 100
    else:
        # Round down to the nearest hundred
        return int(price) - last_two_digits
    
# Transaction type mapping dictionary
transaction_type_dict = {
    "BUY-O": "Open a new BUY CE order",
    "SELL-C": "Close an existing SELL CE order",
    "SELL-C_O": "Close an existing SELL CE and open a new PE order",
    "SELL-O": "Open a new SELL PE order",
    "BUY-C": "Close an existing BUY PE order",
    "BUY-C_O": "Close an existing BUY PE and open a new CE order",
    "SELL-O_C": "Close an existing SELL PE and open a new CE order",
    "BUY-O_C": "Close an existing BUY CE and open a new PE order"
}

def manage_order(transaction_type, buy_sell, Type):
    try:
        if transaction_type == "BUY-O":  # Open a new BUY CE order
            buy_sell = "BUY"
            Type = "CE"
        elif transaction_type == "SELL-C":  # Close CE an existing SELL CE order
            buy_sell = "SELL"
            Type = "CE"
        elif transaction_type == "SELL-O":  # BUY PE Open a new  BUY PE order
            buy_sell = "BUY"
            Type = "PE"
        elif transaction_type == "BUY-C":  # Close PE an existing BUY PE order
            buy_sell = "SELL"
            Type = "PE"
        else:
            print(f"Invalid transaction type: {transaction_type}")
            return None, None  # Return None values if transaction type is invalid
        return buy_sell, Type  # Ensure the correct order of return values
    except Exception as e:
        print(f"Error processing transaction: {e}")
        return None, None  # Return None values in case of an exception
def place_order_broker(LivePrice,group_service,
    trade, user, transaction_type, symbol, quantity, strategy, ordertype,product_type, price, Lots, 
    trade_order_status, Entry_type, Exit_type, Entry_price,Exit_price,EntryQty,ExitQty,
    webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice, day, month, year, fullyear,default_price, Type, order_params, history_id):
    try:
        order_id = 0
        status = "Failed"
        message = "Order is placing by place order broker !!"
        save_trade_order_history(
            LivePrice, group_service, transaction_type, trade_order_status, user, None,
            order_id, status, message, message, strategy, Entry_type, Exit_type,
            Entry_price, Exit_price, EntryQty, ExitQty, webhook_signal, Exchange,
            Segment, Index_Symbol, order_params, broker=None, history_id=history_id
        )

        execution_request = ExecutionRequest(
            LivePrice=LivePrice,
            group_service=group_service,
            trade=trade,
            user=user,
            transaction_type=transaction_type,
            symbol=(symbol or "").upper(),
            quantity=quantity,
            strategy=strategy,
            ordertype=ordertype,
            product_type=product_type,
            price=price,
            Lots=Lots,
            trade_order_status=trade_order_status,
            Entry_type=Entry_type,
            Exit_type=Exit_type,
            Entry_price=Entry_price,
            Exit_price=Exit_price,
            EntryQty=EntryQty,
            ExitQty=ExitQty,
            webhook_signal=webhook_signal,
            Exchange=Exchange,
            Segment=Segment,
            Index_Symbol=Index_Symbol,
            triggerPrice=triggerPrice,
            day=day,
            month=month,
            year=year,
            fullyear=fullyear,
            strike=default_price,
            option_type=Type,
            order_params=order_params,
            history_id=history_id,
        )
        return get_execution_engine().execute_order(execution_request)
    except Exception as e:
        response = {'data': {'status': 'Failed', "message": str(e)}}
        logger.error("Place Order Broker encountered an error: %s", e)
        return response


OPEN_TRADE_ORDER_STATUSES = {"OPEN", "ENTRY", "BUY", "ACTIVE", "PENDING", ""}
CLOSED_TRADE_ORDER_STATUSES = {"CLOSE", "CLOSED", "EXIT", "EXITED", "SQUAREOFF", "SQUARED_OFF"}
FAILED_ORDER_STATUSES = {"FAILED", "REJECTED", "ERRORS", "ERROR", "UNAUTHORIZED", "CANCELLED", "CANCELED"}
MONTH_ALIASES = {
    "JAN": "Jan", "FEB": "Feb", "MAR": "Mar", "APR": "Apr", "MAY": "May", "JUN": "Jun",
    "JUL": "Jul", "AUG": "Aug", "SEP": "Sep", "OCT": "Oct", "NOV": "Nov", "DEC": "Dec",
}


def _normalize_month(value):
    return MONTH_ALIASES.get(str(value or "").strip().upper()[:3], str(value or "").strip().title()[:3])


def _parse_trade_history_contract(trade_history):
    order_params = trade_history.order_params if isinstance(trade_history.order_params, dict) else {}
    contract_match = order_params.get("contract_match") if isinstance(order_params.get("contract_match"), dict) else {}
    candidates = [
        str(trade_history.trading_symbol or ""),
        str(order_params.get("tradingsymbol") or ""),
        str(order_params.get("trading_symbol") or ""),
        str(contract_match.get("tradingsymbol") or ""),
    ]
    trading_symbol = next((candidate.strip().upper() for candidate in candidates if candidate.strip()), "")

    option_type = str(
        order_params.get("option_type")
        or order_params.get("optionType")
        or contract_match.get("option_type")
        or ""
    ).strip().upper()
    if option_type in {"C", "CALL"}:
        option_type = "CE"
    if option_type in {"P", "PUT"}:
        option_type = "PE"

    strike = order_params.get("strike") or order_params.get("strike_price") or contract_match.get("strike")
    day = order_params.get("day") or ""
    month = order_params.get("month") or ""
    year = order_params.get("year") or ""
    fullyear = order_params.get("fullyear") or order_params.get("full_year") or ""
    underlying = str(
        order_params.get("underlying")
        or order_params.get("symbol")
        or trade_history.Index_Symbol
        or ""
    ).strip().upper()

    symbol_patterns = [
        r"^([A-Z]+)(\d{2})([A-Z]{3})(\d{2})(\d+)(CE|PE)$",
        r"^([A-Z]+)([A-Z]{3})(\d{4})(\d+)(CE|PE)$",
        r"^([A-Z]+)(\d{2})([A-Z]{3})(\d{2})([CP])(\d+)$",
        r"^([A-Z]+)(\d+)(CE|PE)(\d{2})([A-Z]{3})(\d{2})$",
        r"^([A-Z]+)(\d{2})([A-Z]{3})(\d+)(CE|PE)$",
    ]
    for pattern in symbol_patterns:
        match = re.match(pattern, trading_symbol)
        if not match:
            continue
        groups = match.groups()
        if pattern == symbol_patterns[0]:
            underlying, day, month, year, strike, option_type = groups
            fullyear = f"20{year}" if len(year) == 2 else year
        elif pattern == symbol_patterns[1]:
            underlying, month, fullyear, strike, option_type = groups
            year = fullyear[-2:]
            day = day or "01"
        elif pattern == symbol_patterns[2]:
            underlying, day, month, year, option_type, strike = groups
            option_type = "CE" if option_type == "C" else "PE"
            fullyear = f"20{year}" if len(year) == 2 else year
        elif pattern == symbol_patterns[3]:
            underlying, strike, option_type, day, month, year = groups
            fullyear = f"20{year}" if len(year) == 2 else year
        elif pattern == symbol_patterns[4]:
            underlying, year, month, strike, option_type = groups
            fullyear = f"20{year}" if len(year) == 2 else year
            day = day or "01"
        break

    if option_type in {"C", "CALL"}:
        option_type = "CE"
    if option_type in {"P", "PUT"}:
        option_type = "PE"

    expiry = contract_match.get("expiry") or order_params.get("expiry")
    if expiry and (not day or not month or not fullyear):
        expiry_text = str(expiry).split("T", 1)[0]
        for date_format in ("%Y-%m-%d", "%d%b%Y", "%d%b%y"):
            try:
                parsed_expiry = datetime.strptime(expiry_text.upper(), date_format)
                day = f"{parsed_expiry.day:02d}"
                month = parsed_expiry.strftime("%b")
                fullyear = str(parsed_expiry.year)
                year = fullyear[-2:]
                break
            except ValueError:
                continue

    fullyear = str(fullyear or (f"20{year}" if year else timezone.localdate().year))
    year = str(year or fullyear[-2:])
    month = _normalize_month(month)
    day = str(day or "01").zfill(2)

    return {
        "underlying": underlying,
        "strike": strike,
        "option_type": option_type,
        "day": day,
        "month": month,
        "year": year,
        "fullyear": fullyear,
        "trading_symbol": trading_symbol,
    }


def _is_regular_trade_open(trade_history):
    trade_status = str(trade_history.trade_order_status or "").strip().upper()
    order_status = str(trade_history.order_status or "").strip().upper()
    if trade_status in CLOSED_TRADE_ORDER_STATUSES or order_status in FAILED_ORDER_STATUSES:
        return False
    if trade_history.Exit_type or trade_history.Exit_Price or trade_history.ExitQty:
        return False
    return trade_status in OPEN_TRADE_ORDER_STATUSES or order_status in {"OPEN", "COMPLETE", "COMPLETED", "TRANSIT", "PENDING"}


def _build_regular_trade_exit_request(trade_history):
    contract = _parse_trade_history_contract(trade_history)
    order_params = trade_history.order_params if isinstance(trade_history.order_params, dict) else {}
    quantity = trade_history.EntryQty or trade_history.ExitQty or order_params.get("quantity") or order_params.get("qty") or 0
    quantity = int(quantity or 0)
    if quantity <= 0:
        raise ValueError("Open trade quantity is missing.")
    if not contract["underlying"] or not contract["strike"] or contract["option_type"] not in {"CE", "PE"}:
        raise ValueError("Unable to resolve open trade contract.")

    return ExecutionRequest(
        LivePrice=trade_history.LivePrice or trade_history.Entry_Price or 0,
        group_service=trade_history.GroupService,
        trade=trade_history,
        user=trade_history.client,
        transaction_type="SELL",
        symbol=contract["underlying"],
        quantity=quantity,
        strategy=trade_history.strategy or "Kill Switch",
        ordertype="MARKET",
        product_type="INTRADAY",
        price=None,
        Lots=trade_history.Lot or 1,
        trade_order_status="CLOSE",
        Entry_type=trade_history.Entry_type,
        Exit_type=trade_history.Exit_type or "KILL_SWITCH",
        Entry_price=trade_history.Entry_Price,
        Exit_price=trade_history.Exit_Price,
        EntryQty=trade_history.EntryQty,
        ExitQty=quantity,
        webhook_signal={"source": "client_trade_history_kill_switch", "original_history_id": trade_history.history_id or trade_history.id},
        Exchange=trade_history.Exchange or "NFO",
        Segment=trade_history.Segment,
        Index_Symbol=trade_history.Index_Symbol or contract["underlying"],
        triggerPrice=0,
        day=contract["day"],
        month=contract["month"],
        year=contract["year"],
        fullyear=contract["fullyear"],
        strike=contract["strike"],
        option_type=contract["option_type"],
        order_params={
            "order_action": "kill_switch_exit",
            "source": "trade_history",
            "original_history_id": trade_history.history_id or trade_history.id,
            "tradingsymbol": contract["trading_symbol"],
        },
        history_id=f"kill_{trade_history.id}_{timezone.now().strftime('%Y%m%d%H%M%S%f')}",
    )


class ClientGlobalKillSwitchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        reason = request.data.get("reason") or "Client global kill switch"

        multi_leg_result = get_multileg_execution_engine().kill_switch(user=user, reason=reason)
        open_regular_trades = [
            trade
            for trade in Tradeorderhistory.objects.filter(client=user).exclude(order_id=0).exclude(order_id__isnull=True).order_by("-id")
            if _is_regular_trade_open(trade)
        ]

        exited_regular_ids = []
        failed_regular = []
        for trade_history in open_regular_trades:
            try:
                exit_request = _build_regular_trade_exit_request(trade_history)
                response = get_execution_engine().execute_order(exit_request)
                response_status = str(response.get("status") or response.get("data", {}).get("status") or "").lower()
                if response_status in {"success", "complete", "completed", "open"}:
                    exited_regular_ids.append(trade_history.id)
                else:
                    failed_regular.append({
                        "trade_history_id": trade_history.id,
                        "message": response.get("message") or response.get("data", {}).get("message") or "Exit failed.",
                    })
            except Exception as exc:
                failed_regular.append({"trade_history_id": trade_history.id, "message": str(exc)})

        return Response(
            {
                "client_id": user.id,
                "multi_leg_exited_strategy_ids": multi_leg_result.get("exited_strategy_ids", []),
                "regular_exit_trade_history_ids": exited_regular_ids,
                "regular_failed": failed_regular,
            },
            status=status.HTTP_200_OK if not failed_regular else status.HTTP_207_MULTI_STATUS,
        )


def serialize_to_json(data):
    """
    Convert data into a JSON-serializable format.
    If a value is a datetime object, convert it to an ISO 8601 string.
    """
    if isinstance(data, dict):
        return {key: serialize_to_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_to_json(item) for item in data]
    elif isinstance(data, Decimal):
        return float(data)  # Convert Decimal to float
    elif isinstance(data, datetime):
        return data.isoformat()  # Convert datetime to ISO 8601 string
    return data


class WebhookDiagnosticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        if not is_admin_or_superadmin(user):
            return Response({"detail": "You do not have permission to view webhook diagnostics."}, status=status.HTTP_403_FORBIDDEN)

        webhook_symbol = str(request.query_params.get("symbol", "") or "").strip()
        strategy_identifier = str(request.query_params.get("group_service", "") or "").strip()
        client_id = request.query_params.get("client_id")

        queryset = ClientTradeSetting.objects.select_related("client", "segment", "sub_segment")
        if is_superadmin_user(user):
            queryset = queryset.filter(client__type_of_user='is_client', client__is_client=True)
        elif is_admin_user(user):
            queryset = queryset.filter(
                Q(client__assigned_client=user) |
                Q(client__created_by=user)
            ).filter(client__type_of_user='is_client', client__is_client=True)

        if client_id:
            queryset = queryset.filter(client_id=client_id)

        diagnostics = []
        ready_count = 0
        blocked_count = 0

        for trade in queryset.order_by("client_id", "id"):
            reasons = _collect_trade_skip_reasons(
                trade,
                webhook_symbol=webhook_symbol,
                strategy_identifier=strategy_identifier,
            )
            trade_limit_reason = _get_trade_limit_skip_reason(trade, (_get_trade_execution_symbol(trade) or "").upper())
            if trade_limit_reason:
                reasons.append(trade_limit_reason)
            is_ready = len(reasons) == 0
            if is_ready:
                ready_count += 1
            else:
                blocked_count += 1

            diagnostics.append({
                "trade_setting_id": trade.id,
                "client_id": trade.client_id,
                "client_name": getattr(trade.client, "fullName", None) or getattr(trade.client, "userName", None),
                "client_username": getattr(trade.client, "userName", None),
                "group_service": trade.group_service,
                "segment": getattr(getattr(trade, "segment", None), "name", None),
                "script_name": _get_trade_execution_symbol(trade),
                "trade_symbol": trade.symbol,
                "broker": trade.broker,
                "product_type": trade.product_type,
                "quantity": trade.quantity,
                "trade_limit": trade.trade_limit,
                "expiry_date": trade.expiry_date,
                "client_trading_enabled": bool(getattr(trade.client, "is_enable", False)),
                "trade_toggle_enabled": bool(trade.is_tread_status),
                "status": "ready" if is_ready else "blocked",
                "skip_reasons": reasons,
            })

        return Response({
            "status": "success",
            "filters": {
                "symbol": webhook_symbol,
                "group_service": strategy_identifier,
                "client_id": client_id,
            },
            "summary": {
                "total": len(diagnostics),
                "ready": ready_count,
                "blocked": blocked_count,
            },
            "data": diagnostics,
        }, status=status.HTTP_200_OK)


class SLTPWatcherScanAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        if not is_admin_or_superadmin(user):
            return Response(
                {"detail": "You do not have permission to view the SL/TP watcher."},
                status=status.HTTP_403_FORBIDDEN,
            )

        client_id = request.query_params.get("client_id")
        history_id = request.query_params.get("history_id")
        scan_result = get_sl_tp_watcher_service().scan(
            client_id=client_id,
            history_id=history_id,
            execute_exit=False,
        )
        return Response(
            {
                "status": "success",
                **scan_result,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        user = request.user
        if not is_admin_or_superadmin(user):
            return Response(
                {"detail": "You do not have permission to run the SL/TP watcher."},
                status=status.HTTP_403_FORBIDDEN,
            )

        client_id = request.data.get("client_id")
        history_id = request.data.get("history_id")
        scan_result = get_sl_tp_watcher_service().scan(client_id=client_id, history_id=history_id)
        return Response(
            {
                "status": "success",
                **scan_result,
            },
            status=status.HTTP_200_OK,
        )

SESSION_ID = None
SESSION_EXPIRATION = None
# Webhooks-trade-Alert
class PlaceOrderWebhookView(APIView):
    def post(self, request):
        _require_webhook_secret(request)
        try:
            context = _resolve_webhook_request_context(request.data)
        except ValidationError as exc:
            logger.warning("Webhook request validation failed: %s", exc)
            return Response({"status": "error", "message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        alert_data = context["alert_data"]
        symbols = context["symbols"]
        save_webhook_signals_logs(context["buy_sell"], symbols, context["default_price"], context["strategy_tag"], json=alert_data)
        candidate_trades, strategy_id = _get_matching_webhook_trades(alert_data, symbols.upper())

        results = []
        for index, trade in enumerate(candidate_trades, start=1):
            results.append(_process_webhook_trade(trade, index, context))

        summary = {
            "total": len(results),
            "successful": sum(1 for item in results if item["status"] == "success"),
            "skipped": sum(1 for item in results if item["status"] == "skipped"),
            "failed": sum(1 for item in results if item["status"] == "failed"),
            "group_service": strategy_id,
            "symbol": symbols,
        }
        return Response({"status": "success", "summary": summary, "results": results}, status=status.HTTP_200_OK)

class MyPlaceOrderWebhookView(APIView):

    def handle_single_trade(self, trade, index, symbols, exch_seg, default_price, strategy_id,
                        alert_data, buy_sell_type, buy_sell, default_ordertype, limitPrice,
                        default_quantity, LivePrice, Lots, triggerPrice, history_id):  # Add it here
        context = {
            "alert_data": alert_data,
            "strategy_id": strategy_id,
            "transaction_type": buy_sell_type,
            "buy_sell": buy_sell,
            "symbols": symbols,
            "exch_seg": exch_seg,
            "default_price": default_price,
            "default_ordertype": default_ordertype,
            "strategy_tag": alert_data.get("strategyTag", "ce entry"),
            "limit_price": limitPrice,
            "default_quantity": default_quantity,
            "lots": Lots,
            "trigger_price": triggerPrice,
            "live_price": LivePrice,
        }
        return _process_webhook_trade(trade, index, context, history_id=history_id)


    def post(self, request):
        _require_webhook_secret(request)
        try:
            context = _resolve_webhook_request_context(request.data)
        except ValidationError as exc:
            logger.warning("Webhook request validation failed: %s", exc)
            return Response({"status": "error", "message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        alert_data = context["alert_data"]
        symbols = context["symbols"]
        save_webhook_signals_logs(context["buy_sell"], symbols, context["default_price"], context["strategy_tag"], json=alert_data)
        candidate_trades, strategy_id = _get_matching_webhook_trades(alert_data, symbols.upper())

        results = []
        for index, trade in enumerate(candidate_trades, start=1):
            history_id = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{trade.client.id}_{trade.id}"
            results.append(self.handle_single_trade(
                trade,
                index,
                symbols,
                context["exch_seg"],
                context["default_price"],
                strategy_id,
                alert_data,
                context["transaction_type"],
                context["buy_sell"],
                context["default_ordertype"],
                context["limit_price"],
                context["default_quantity"],
                context["live_price"],
                context["lots"],
                context["trigger_price"],
                history_id,
            ))

        summary = {
            "total": len(results),
            "successful": sum(1 for item in results if item["status"] == "success"),
            "skipped": sum(1 for item in results if item["status"] == "skipped"),
            "failed": sum(1 for item in results if item["status"] == "failed"),
            "group_service": strategy_id,
            "symbol": symbols,
        }
        return Response({"status": "success", "summary": summary, "results": results}, status=status.HTTP_200_OK)

#token Sesiion id for alice blue order
from datetime import datetime, timedelta
def get_or_regenerate_session_id(USER_ID, ALICE_API_KEY):
    global SESSION_ID, SESSION_EXPIRATION
    current_time = datetime.now()
    if SESSION_ID is None or SESSION_EXPIRATION is None or current_time >= SESSION_EXPIRATION:
        logger.info(f"Session ID expired or not found. Regenerating...{USER_ID}")
        alice = Aliceblue(user_id=USER_ID, api_key=ALICE_API_KEY)
        SESSION_ID = alice.get_session_id(alice)
        SESSION_EXPIRATION = current_time + timedelta(seconds=86400)
        logger.info(f"New session ID generated:")
    else:
        logger.info("Using existing session ID")
    return SESSION_ID



# Get the strategy using the strategy_id
class StrategyClientListView(APIView):
    permission_classes = [IsAdminOrSuperadmin]

    def get(self, request, strategy_id, *args, **kwargs):
        try:
            strategy = get_object_or_404(Strategies, id=strategy_id)
            clients = User.objects.filter(is_client=True)
            if not clients.exists():
                return Response({
                    "strategy_id": strategy.id,
                    "strategy_name": strategy.name,
                    "clients": []
                }, status=200)

            # Build the client data list
            client_data = [
                {
                    "client_id": client.id,
                    "client_name": f"{client.firstName} {client.lastName}",
                    "is_using_strategy": strategy.clients.filter(id=client.id).exists(),
                }
                for client in clients
            ]
            return Response({
                "strategy_id": strategy.id,
                "strategy_name": strategy.name,
                "clients": client_data,
            }, status=200)
        
        except NotFound:
            return Response({"error": "Strategy not found"}, status=404)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=500)


class ClientDashboardIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request, *args, **kwargs): 
        try:
            user=request.user
            user = User.objects.get(pk=user.id)  
            serializer = ClientListdetailsSerializer(user)  
        except Strategies.DoesNotExist:
            return Response({"detail": "client id not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)        
class ClientsTradeStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        current_date = timezone.now().date()

        if is_superadmin_user(user):
            clients = User.objects.filter(
                type_of_user='is_client', is_client=True).order_by('-id')
        else:
            # clients =User.objects.filter(
            #     type_of_user='is_client', is_client=True, end_date_client__gt=current_date,created_by=user
            # ).order_by('-id')
            clients = User.objects.filter(
                Q(type_of_user='is_client') & Q(is_client=True) &
                (Q(created_by=user) | Q(assigned_client=user))
            ).order_by('-id')
        # 🔍 **Search Filter (Client name, broker, index symbol, trading symbol)**
        search_query = request.query_params.get('q', '').strip()
        clients = clients.filter(
            Q(fullName__icontains=search_query) |
            Q(phoneNumber__icontains=search_query) | 
            Q(email__icontains=search_query)
        )


        # Apply pagination and serialize the data
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(clients, request)
        serializer = UserclientSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def patch(self, request, *args, **kwargs):
        client_id = kwargs.get('client_id')  # Get client ID from URL
        user = request.user

        # Fetch the client object
        client = get_object_or_404(User, id=client_id, type_of_user='is_client', is_client=True)

        # Check if the current user has the right permissions
        if not is_superadmin_user(user) and client.created_by != user:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        # Validate the 'is_enable' field in the request body
        is_enable = request.data.get('is_enable')
        if is_enable is None:
            return Response({"detail": "'is_enable' key is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the client's trading status
        client.is_enable = is_enable
        client.save()

        # Serialize the updated client
        serializer = UserclientSerializer(client)
        return Response({"detail": "Trading status updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)



#update client demate account details api
class ClientBrokerDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def _error_response(self, message, *, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        payload = {"status": "error", "message": message}
        if errors is not None:
            payload["errors"] = errors
        return Response(payload, status=status_code)

    def get(self, request):
        """
        Retrieve broker details for the authenticated client.
        """
        try:
            user = request.user
            broker_detail = ClientBrokerdetails.objects.filter(client_id=user.id).first()
            available_brokers = _ensure_default_broker_catalog()
            serializer = ClientBrokerDetailsSerializer(
                broker_detail or ClientBrokerdetails(client=user),
                context={"available_brokers": available_brokers},
            )
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return self._error_response(str(e))

    def put(self, request):

        """
        Create or update broker details for a specific client.
        Omitted fields are preserved to avoid accidental credential loss.
        """
        try:
            user = request.user

            # Fetch or create broker details for the client
            broker_detail, created = ClientBrokerdetails.objects.get_or_create(client_id=user.id)

            # Use the serializer with partial=True to update only provided fields
            serializer = ClientBrokerDetailsUpdateSerializer(broker_detail, data=request.data, partial=True)
            if serializer.is_valid():
                broker_detail = serializer.save()
                # Update the broker field in ClientTradeSetting
                client_trade_settings = ClientTradeSetting.objects.filter(client=user)
                for trade_setting in client_trade_settings:
                    trade_setting.broker = broker_detail.broker_name.broker_name if broker_detail.broker_name else ""
                    trade_setting.save(update_fields=["broker"])

                client_multi_leg_settings = ClientMultiLegStrategySetting.objects.filter(client=user)
                for multi_leg_setting in client_multi_leg_settings:
                    multi_leg_setting.broker = broker_detail.broker_name.broker_name if broker_detail.broker_name else ""
                    multi_leg_setting.save(update_fields=["broker", "updated_at"])

                # ⬇️ Add logging block here
                try:
                    log_file_path = os.path.join('logs', 'broker_update_log.csv')  # make sure 'logs/' exists
                    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)  # ensure the folder exists

                    log_data = {
                        'user_id': user.id,
                        'username': user.email if user.email else "unknown",
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'action': 'update_broker_details',
                        'broker': broker_detail.broker_name.broker_name
                    }

                    file_exists = os.path.isfile(log_file_path)
                    with open(log_file_path, mode='a', newline='') as file:
                        writer = csv.DictWriter(file, fieldnames=log_data.keys())
                        if not file_exists:
                            writer.writeheader()
                        writer.writerow(log_data)
                except Exception as log_error:
                    # You can optionally log this to Django logs
                    pass  # Don't disturb the main flow

                message = "Broker details created successfully!" if created else "Broker details updated successfully!"
                response_serializer = ClientBrokerDetailsSerializer(
                    broker_detail,
                    context={"available_brokers": _ensure_default_broker_catalog()},
                )
                return Response(
                    {"status": "success", "message": message, "data": response_serializer.data},
                    status=status.HTTP_200_OK,
                )

            return self._error_response(
                "Broker details validation failed.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return self._error_response(str(e))

#get broker details by Admin
class AdminClientBrokerDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieve broker details for the authenticated client.
        """
        client_id = kwargs.get("pk")  # Fetch client ID from URL params

        try:
            # Fetch broker details
            broker_detail = ClientBrokerdetails.objects.filter(client_id=client_id).first()

            if broker_detail and not can_access_client_record(request.user, broker_detail.client):
                return Response({"status": "error", "message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

            serializer = ClientBrokerDetailsSerializer(
                broker_detail or ClientBrokerdetails(client_id=client_id),
                context={"available_brokers": _ensure_default_broker_catalog()},
            )
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        
#demate status manage api for client trade
class EnableDisableBrokerView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request):
        """
        Enable or disable broker for a specific client.
        """
        # Fetch the client (User)
        try:
            user=request.user
            client = User.objects.get(id=user.id)
        except User.DoesNotExist:
            return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure 'is_enable' is provided in the request data
        is_enable = request.data.get("is_enable")
        if is_enable is None:
            return Response({"error": "Missing 'is_enable' field in request."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the 'is_enable' field
        client.is_enable = is_enable
        client.save()

        status_message = "enabled" if is_enable else "disabled"
        return Response(
            {"message": f"Broker has been {status_message} for the client."},
            status=status.HTTP_200_OK
        )
    
    def get(self, request):
        """
        Fetch broker status for the authenticated client.
        """
        try:
            user = request.user
            client = User.objects.get(id=user.id)
        except User.DoesNotExist:
            return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch and return the broker's status
        return Response(
            {
                "id": client.id,
                "username": client.fullName,
                "email": client.email,
                "is_enable": client.is_enable,  # Assuming this field exists in the User model
            },
            status=status.HTTP_200_OK
        )
#admin can get client broker status
class AdminGetClientBrokerStatusView(APIView):
    def get(self, request, *args, **kwargs):
        client_id = kwargs.get("pk")  
        try:
            client = User.objects.get(id=client_id)
        except User.DoesNotExist:
            return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch and return the broker's status
        return Response(
            {
                "id": client.id,
                "username": client.fullName,
                "email": client.email,
                "is_enable": client.is_enable,  
            },
            status=status.HTTP_200_OK
        )

class BrokerRuntimeStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            broker_details = _get_selected_broker_detail_for_user(request.user)
            setup_spec = get_broker_setup_spec(
                broker_details.broker_name.broker_name if broker_details and broker_details.broker_name else None
            )
            summary = LoginActivityService().build_summary(request.user, request=request)
            broker_data = (summary.get("data") or {}).get("broker") or {}

            return Response(
                {
                    "status": "success",
                    "data": {
                        **broker_data,
                        "auth_mode": setup_spec.get("auth_mode") if setup_spec else None,
                        "connect_action_label": setup_spec.get("connect_action_label") if setup_spec else None,
                        "save_action_label": setup_spec.get("save_action_label") if setup_spec else None,
                        "supports_redirect": bool(setup_spec.get("supports_redirect")) if setup_spec else False,
                        "supports_callback": bool(setup_spec.get("supports_callback")) if setup_spec else False,
                        "connect_path": setup_spec.get("connect_path") if setup_spec else None,
                    },
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            logger.exception("Failed to fetch broker runtime status for user %s", request.user.id)
            return Response(
                {"status": "error", "message": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class BrokerGenerateTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            broker_details = _get_selected_broker_detail_for_user(request.user)
            if not broker_details or not broker_details.broker_name:
                return Response(
                    {"status": "error", "message": "Please select and save a broker first."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            setup_spec = get_broker_setup_spec(broker_details.broker_name.broker_name)
            if not setup_spec:
                return Response(
                    {"status": "error", "message": "Selected broker is not supported."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            normalized_broker = normalize_broker_name(broker_details.broker_name.broker_name)
            auth_mode = setup_spec.get("auth_mode")

            if auth_mode == "redirect_oauth":
                return Response(
                    {
                        "status": "success",
                        "action": "redirect",
                        "message": "Broker login redirect is required for this broker.",
                        "data": {
                            "broker_name": setup_spec.get("display_name"),
                            "connect_path": setup_spec.get("connect_path"),
                            "auth_mode": auth_mode,
                        },
                    },
                    status=status.HTTP_200_OK,
                )

            if auth_mode == "manual_token":
                return Response(
                    {
                        "status": "success",
                        "action": "manual",
                        "message": "This broker uses manual token management. Save the broker credentials or token and log in on the broker side if required.",
                        "data": {
                            "broker_name": setup_spec.get("display_name"),
                            "auth_mode": auth_mode,
                        },
                    },
                    status=status.HTTP_200_OK,
                )

            if normalized_broker != "angel one":
                return Response(
                    {
                        "status": "error",
                        "message": "Direct token generation is not implemented for this broker.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            from main.angelone.services.auth_service import AuthService

            credentials = broker_details.get_angel_one_login_credentials()
            client_code = credentials.get("client_code")
            api_key = credentials.get("api_key")

            missing_fields = []
            if not api_key:
                missing_fields.append("API key")
            if not client_code:
                missing_fields.append("Client ID")
            if not credentials.get("password"):
                missing_fields.append("Password")
            if not credentials.get("totp_secret"):
                missing_fields.append("TOTP secret")

            if missing_fields:
                return Response(
                    {
                        "status": "error",
                        "message": "Saved Angel One credentials are incomplete.",
                        "missing_fields": missing_fields,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = AuthService().ensure_valid_session(
                client_id=client_code,
                api_key=api_key,
                broker_details=broker_details,
                verify_remote=True,
            )

            if result.get("status") != "success":
                return Response(
                    {
                        "status": "error",
                        "message": result.get("message", "Failed to generate broker token."),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            runtime_summary = LoginActivityService().build_summary(request.user, request=request)
            broker_runtime = (runtime_summary.get("data") or {}).get("broker") or {}

            return Response(
                {
                    "status": "success",
                    "action": "token_generated",
                    "message": "Broker token generated successfully.",
                    "data": broker_runtime,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            if normalized_broker == "angel one":
                try:
                    from main.angelone_views import build_angelone_redirect_payload

                    redirect_payload = build_angelone_redirect_payload(
                        request.user,
                        broker_details=broker_details,
                        request=request,
                    )
                    return Response(
                        {
                            "status": "success",
                            "action": "redirect",
                            "message": "Direct token generation is unavailable right now. Continuing with the Angel One login flow.",
                            "redirect_url": redirect_payload.get("redirect_url"),
                            "data": {
                                "broker_name": setup_spec.get("display_name"),
                                "auth_mode": auth_mode,
                            },
                        },
                        status=status.HTTP_200_OK,
                    )
                except Exception:
                    logger.exception("Angel One redirect fallback failed for user %s", request.user.id)
            logger.exception("Broker token generation failed for user %s", request.user.id)
            return Response(
                {"status": "error", "message": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class SubSegmentsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Get the 'segment' parameter from the query string
            segment_id = request.query_params.get('segment', None)

            # Check if the segment_id is provided
            if not segment_id:
                return Response(
                    {"detail": "Segment ID is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the Segment object
            option_segment = Segment.objects.get(id=segment_id)

            # Retrieve all related sub-segments
            related_sub_segments = option_segment.sub_segments.all()

            # Serialize the related sub-segments
            serializer = SubSegmentSerializer(related_sub_segments, many=True)
            return Response(
                {"client_segment_list": serializer.data},
                status=status.HTTP_200_OK
            )

        except Segment.DoesNotExist:
            return Response(
                {"detail": "Segment not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
#trading history api demate rejected and success status
class TradeorderhistoryListView_old(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            if is_superadmin_user(user):
                # Super-admin can see all clients' trade order histories
                clients = User.objects.filter(type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).filter(client__in=clients).order_by('-id')
            elif is_admin_user(user):
                # Sub-admin can see trade order histories of their assigned clients
                clients = User.objects.filter(assigned_client=user,created_by=user,type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).filter(client__in=clients).order_by('-id')
            else:
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).filter(client=user).order_by('-id')

            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(trade_history, request)

            serializer = TradeorderhistorySerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#CLIENT trade all history data 
class ClientTradeListView_old(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            if is_superadmin_user(user):
                # Super-admin can see all clients' trade order histories
                clients = User.objects.all()#filter(type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.filter(client__in=clients).order_by('-id')
            elif is_admin_user(user):
                print("Sub-AdminSub-AdminSub-AdminSub-Admin")
                # Sub-admin can see trade order histories of their assigned clients
                clients = User.objects.filter(assigned_client=user,created_by=user)#,type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.filter(client__in=clients).order_by('-id')
            else:
                trade_history = Tradeorderhistory.objects.filter(client=user).order_by('-id')

            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(trade_history, request)

            serializer = TradeorderhistorySerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClientDashBoardView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ClientdashboardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    
class TradeOrderHistoryFilterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Query parameters
            service = request.query_params.get('service', None)
            strategy = request.query_params.get('strategy', None)
            trade_type = request.query_params.get('type', None)
            index_symbol = request.query_params.get('index_symbol', None)
            symbol = request.query_params.get('symbol', None)
            start_date = request.query_params.get('start_date', None)
            end_date = request.query_params.get('end_date', None)
            order_status = request.query_params.get('order_status', None)  # Entry_status or Exit_status
            broker = request.query_params.get('broker', None)
            max_lot = request.query_params.get('max_lot', None)

            # Base filters
            filters = Q()
            if service:
                filters &= Q(broker__iexact=service)
            if strategy:
                filters &= Q(strategy__iexact=strategy)
            if trade_type:
                filters &= Q(Entry_type__iexact=trade_type) | Q(Exit_type__iexact=trade_type)
            if index_symbol:
                filters &= Q(Index_Symbol__iexact=index_symbol)
            if symbol:
                filters &= Q(trading_symbol__iexact=symbol)
            if start_date and end_date:
                filters &= Q(SignalEntry_time__range=[start_date, end_date])
            if order_status:
                filters &= Q(Entry_status__iexact=order_status) | Q(Exit_status__iexact=order_status)

            # User-specific filtering
            user = request.user
            if is_superadmin_user(user):
                # Super-admin sees all clients' trade histories
                clients = User.objects.filter(type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).filter(client__in=clients).filter(filters).order_by('-id')

            elif is_admin_user(user):
                # Sub-admin sees their assigned clients' histories
                clients = User.objects.filter(assigned_client=user, created_by=user, type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).filter(client__in=clients).filter(filters).order_by('-id')

            else: 
                # Regular user sees only their trade history
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).filter(client=user).filter(filters).order_by('-id')

            # Pagination
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(trade_history, request)

            # Serialization
            serializer = TradeOrderHistoryFilterSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# #sub admin license details api
import razorpay

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))

class CreateOrderView(APIView):

    def post(self, request):
        try:
            user = request.user
            license_qty = request.data.get("license_qty")
            license_price = request.data.get("license_price")

            if not license_qty or not license_price:
                return Response({"error": "License quantity and price are required"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate UPI ID before proceeding
        
            total_amount = int(license_qty) * int(license_price) * 100  # Convert to paise

            # Create Razorpay order
            order_data = {
                "amount": total_amount,
                "currency": "INR",
                "payment_capture": 1,
            }
            razorpay_order = razorpay_client.order.create(order_data)

            return Response({
                "status": "success",
                "message": "Order created successfully",
                "razorpay_order_id": razorpay_order["id"],
                "total_amount": total_amount // 100,
                "resp":razorpay_order
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentCallbackView(APIView):
    def get(self, request):
        try:
            order_id ="order_Pu1KH38Ka6STIt"# request.data.get("order_id")
            order_details = razorpay_client.order.fetch(order_id)
            
            # Check if payment is successful
            if order_details['status'] == 'paid':
                payment = Payment.objects.get(razorpay_order_id=order_id)
                payment.payment_status = True
                payment.save()

            return Response({"status": order_details['status'], "order_details": order_details})

        except razorpay.errors.BadRequestError:
            return Response({"error": "Invalid Order ID"}, status=400)

class VerifyPaymentAPIView(APIView):
    def post(self, request):
        data = request.data
        payment_id = data.get("razorpay_payment_id")
        order_id = data.get("razorpay_order_id")
        signature = data.get("razorpay_signature")
        payment_method = data.get("payment_method")
        upi_id = data.get("upi_id")

        payment = Payment.objects.filter(razorpay_order_id=order_id).first()

        if payment:
            payment.razorpay_payment_id = payment_id
            payment.razorpay_signature = signature
            payment.payment_method = payment_method
            payment.upi_id = upi_id if payment_method == "UPI" else None

            try:
                razorpay_client.utility.verify_payment_signature(data)
                payment.payment_status = "Completed"
                payment.save()
                return Response({"message": "Payment successful"})
            except:
                payment.payment_status = "Failed"
                payment.save()
                return Response({"message": "Payment verification failed"}, status=400)
        return Response({"message": "Order not found"}, status=404)
    

# get startegy of client for trade history filter
class StrategyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Fetch unique strategy names from the Strategies model
            strategies = Strategies.objects.values('name').distinct()
            
            # Prepare the list of strategy names
            strategy_list = [strategy['name'] for strategy in strategies]

            # Return the list of strategies
            return Response({"strategies": strategy_list}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# for get the client strategy

class ClientStrategyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,*args, **kwargs):
        try:
            # Fetch unique strategy names from the Strategies model
            strategies = ClientTradeSetting.objects.values('strategy').distinct()
            
            # Prepare the list of strategy names
            strategy_list = [strategy['strategy'] for strategy in strategies]

            # Return the list of strategies
            return Response({"strategies": strategy_list}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# filter api



class TradeorderhistoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            
            # Get filters from request data
            from_date = request.GET.get('from_date', None)
            to_date = request.GET.get('to_date', None)
            strategy = request.GET.get('strategy', None)
            Index_Symbol = request.GET.get('Index_symbol', None)
            order_status = request.GET.get('order_status', None)
            broker = request.GET.get('broker', None)
            
            print(f"broker: {broker} Index_Symbol: {Index_Symbol} order_status: {order_status}")
            
            # Determine which clients to include based on user role
            if is_superadmin_user(user):
                clients = User.objects.filter(type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).exclude(order_id__isnull=True).filter(client__in=clients).order_by('-id')
            elif is_admin_user(user):
                clients = User.objects.filter(assigned_client=user, type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).exclude(order_id__isnull=True).filter(client__in=clients).order_by('-id')
            else:
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).exclude(order_id__isnull=True).filter(client=user).order_by('-id')

            # Dynamically apply filters based on the provided parameters
            filters = Q()

            # Apply date filter (from_date and to_date)
            if from_date:
                try:
                    from_date = datetime.strptime(from_date, "%Y-%m-%d")
                    filters &= Q(date__gte=from_date)
                except ValueError:
                    return Response({"error": "Invalid from_date format, expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
            if to_date:
                try:
                    to_date = datetime.strptime(to_date, "%Y-%m-%d")
                    filters &= Q(date__lte=to_date)
                except ValueError:
                    return Response({"error": "Invalid to_date format, expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            # Apply symbol filter
            if strategy and strategy.lower() != 'all':
                filters &= Q(strategy__iexact=strategy)

            # Apply index_symbol filter
            if Index_Symbol and Index_Symbol.lower() != 'all':
                filters &= Q(Index_Symbol__iexact=Index_Symbol)

            # Apply broker filter
            if broker and broker.lower() != 'all':
                filters &= Q(broker__iexact=broker)

            # Apply order_status filter (Ensure it correctly filters)
            if order_status and order_status.lower() != 'all':
                filters &= Q(order_status__iexact=order_status)
                # trade_history = trade_history.filter(order_status=order_status)

            # 🔍 **Search Filter (Client name, broker, index symbol, trading symbol)**
            search_query = request.query_params.get('q', '').strip()
            if search_query:
                search_terms = search_query.split()  
                full_name_filters = Q()
                for term in search_terms:
                    full_name_filters |= Q(client__fullName__icontains=term)  

                filters &= (
                    full_name_filters |
                    Q(client__email__icontains=search_query) |
                    Q(broker__icontains=search_query) |
                    Q(Index_Symbol__icontains=search_query) |
                    Q(trading_symbol__icontains=search_query) |
                    Q(GroupService__icontains=search_query)
                )

            # Apply all filters
            trade_history = trade_history.filter(filters)

            # Check if trade_history is empty before pagination
            if not trade_history.exists():
                return Response({"message": "No trade history found for the given filters."}, status=status.HTTP_200_OK)

            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(trade_history, request)

            serializer = TradeorderhistorySerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TradeCompleteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            
            # Get filters from request data
            from_date = request.GET.get('from_date', None)
            to_date = request.GET.get('to_date', None)
            strategy = request.GET.get('strategy', None)
            Index_Symbol = request.GET.get('Index_symbol', None)
            order_status = request.GET.get('order_status', None)
            broker = request.GET.get('broker', None)
            
            print(f"broker: {broker} Index_Symbol: {Index_Symbol} order_status: {order_status}")
            
            # Determine which clients to include based on user role
            if is_superadmin_user(user):
                clients = User.objects.filter(type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.filter(
                    client__in=clients,
                    order_status__in=['completed', 'complete'],
                    trade_order_status__iexact='CLOSE',
                ).filter(Q(Entry_Price__gt=0.0) | Q(Exit_Price__gt=0.0)).exclude(
                    order_id=0,
                    order_id__isnull=True,
                    EntryQty__isnull=True,
                    ExitQty__isnull=True,
                    Entry_Price__isnull=True,
                    Exit_Price__isnull=True,
                ).order_by('-id')

               
            elif is_admin_user(user):
                clients = User.objects.filter(assigned_client=user, type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.filter(
                    client__in=clients,
                    order_status__in=['completed', 'complete'],
                    trade_order_status__iexact='CLOSE',
                ).filter(Q(Entry_Price__gt=0.0) | Q(Exit_Price__gt=0.0)).exclude(
                    order_id=0,
                    order_id__isnull=True,
                    EntryQty__isnull=True,
                    ExitQty__isnull=True,
                    Entry_Price__isnull=True,
                    Exit_Price__isnull=True,
                ).order_by('-id')
            else:
                trade_history = Tradeorderhistory.objects.filter(
                    client=user,
                    order_status__in=['completed', 'complete'],
                    trade_order_status__iexact='CLOSE',
                ).filter(Q(Entry_Price__gt=0.0) | Q(Exit_Price__gt=0.0)).exclude(
                    order_id=0,
                    order_id__isnull=True,
                    EntryQty__isnull=True,
                    ExitQty__isnull=True,
                    Entry_Price__isnull=True,
                    Exit_Price__isnull=True,
                ).order_by('-id')
            # Dynamically apply filters based on the provided parameters
            filters = Q()

            # Apply date filter (from_date and to_date)
            if from_date:
                try:
                    from_date = datetime.strptime(from_date, "%Y-%m-%d")
                    filters &= Q(date__gte=from_date)
                except ValueError:
                    return Response({"error": "Invalid from_date format, expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
            if to_date:
                try:
                    to_date = datetime.strptime(to_date, "%Y-%m-%d")
                    filters &= Q(date__lte=to_date)
                except ValueError:
                    return Response({"error": "Invalid to_date format, expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            # Apply symbol filter
            if strategy and strategy.lower() != 'all':
                filters &= Q(strategy__iexact=strategy)

            # Apply index_symbol filter
            if Index_Symbol and Index_Symbol.lower() != 'all':
                filters &= Q(Index_Symbol__iexact=Index_Symbol)

            # Apply broker filter
            if broker and broker.lower() != 'all':
                filters &= Q(broker__iexact=broker)

            # Apply order_status filter (Ensure it correctly filters)
            if order_status and order_status.lower() != 'all':
                filters &= Q(order_status__iexact=order_status)
                # trade_history = trade_history.filter(order_status=order_status)

            # 🔍 **Search Filter (Client name, broker, index symbol, trading symbol)**
            search_query = request.query_params.get('q', '').strip()
            if search_query:
                search_terms = search_query.split()  
                full_name_filters = Q()
                for term in search_terms:
                    full_name_filters |= Q(client__fullName__icontains=term)  

                filters &= (
                    full_name_filters |
                    Q(client__email__icontains=search_query) |
                    Q(broker__icontains=search_query) |
                    Q(Index_Symbol__icontains=search_query) |
                    Q(trading_symbol__icontains=search_query) |
                    Q(GroupService__icontains=search_query)
                )

            # Apply all filters
            trade_history = trade_history.filter(filters)

            # Check if trade_history is empty before pagination
            if not trade_history.exists():
                return Response({"message": "No trade history found for the given filters."}, status=status.HTTP_200_OK)

            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(trade_history, request)

            serializer = TradeorderhistorySerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClientTradeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            
            # Get filters from request data
            from_date = request.GET.get('from_date', None)
            to_date = request.GET.get('to_date', None)
            symbol = request.GET.get('symbol', None)
            Index_Symbol = request.GET.get('Index_Symbol', None)
            order_status = request.GET.get('order_status', None)
            strategy = request.GET.get('strategy', None)
            print(f"client strategy: {strategy} symbol: {Index_Symbol}")
            
            # Determine which clients to include based on user role
            if is_superadmin_user(user):
                clients = User.objects.all()  # Super-admin can see all clients' trade order histories
                trade_history = Tradeorderhistory.objects.filter(client__in=clients).order_by('-id')
            elif is_admin_user(user):
                print("Sub-Admin is called.....")
                clients = User.objects.filter(assigned_client=user)  # Sub-admin can see trade order histories of their assigned clients
                trade_history = Tradeorderhistory.objects.filter(client__in=clients).order_by('-id')
            else:
                trade_history = Tradeorderhistory.objects.filter(client=user).order_by('-id')

            # Dynamically apply filters based on the provided parameters
            filters = Q()
            search_query = request.query_params.get('q', '').strip()

            # Apply date filter (from_date and to_date)
            if from_date:
                try:
                    from_date = datetime.strptime(from_date, "%Y-%m-%d")
                    filters &= Q(date__gte=from_date)
                except ValueError:
                    return Response({"error": "Invalid from_date format, expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
            if to_date:
                try:
                    to_date = datetime.strptime(to_date, "%Y-%m-%d")
                    filters &= Q(date__lte=to_date)
                except ValueError:
                    return Response({"error": "Invalid to_date format, expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            # Apply symbol filter
            if symbol and symbol.lower() != 'all':
                filters &= Q(symbol__iexact=symbol)

            # Apply order status filter
            if order_status and order_status.lower() != 'all':
                filters &= Q(order_status__iexact=order_status)

            # Apply index_symbol filter
            if Index_Symbol and Index_Symbol.lower() != 'all':
                filters &= Q(Index_Symbol__iexact=Index_Symbol)

            # Apply strategy filter
            if strategy and strategy.lower() != 'all':
                filters &= Q(strategy__iexact=strategy)

            # 🔍 **Search Filter (Client name, broker, index symbol, trading symbol)**
            if search_query:
                # Normalize the search query by trimming whitespace
                search_query = search_query.strip()
                search_terms = search_query.split()  # Split the search query into individual terms

                # Create a Q object for each term to match against the full name
                full_name_filters = Q()
                for term in search_terms:
                    full_name_filters |= Q(client__fullName__icontains=term)  # Match any part of the full name

                filters &= (
                    full_name_filters |
                    Q(client__email__icontains=search_query) |
                    Q(broker__icontains=search_query) |
                    Q(Index_Symbol__icontains=search_query) |
                    Q(trading_symbol__icontains=search_query) |
                    Q(GroupService__icontains=search_query)
                )

            # Apply all filters
            trade_history = trade_history.filter(filters)

            # Check if trade_history is empty before pagination
            if not trade_history.exists():
                return Response({"message": "No trade history found for the given filters."}, status=status.HTTP_200_OK)

            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(trade_history, request)

            serializer = TradeorderhistorySerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL)




class TradeOrderResponseDataView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, trade_id, *args, **kwargs):
        try:
            # Get the trade order by ID
            trade_order = get_object_or_404(Tradeorderhistory, id=trade_id)

            # Return response data for the specific trade order
            return Response({"response_data": trade_order.response_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
       

class IsSuperAdminOrSubAdmin(permissions.BasePermission):
    """
    Allows access only to Super Admins or Sub Admins based on role name.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and is_admin_or_superadmin(request.user))
    
class BrokerLogActivityView(APIView):
    permission_classes = [IsSuperAdminOrSubAdmin]  # Only superadmin or subadmin can access

    def get(self, request, id, *args, **kwargs):
        target_user = get_object_or_404(UserModel, id=id)
        summary = LoginActivityService().build_summary(target_user, request=request)
        return Response(summary, status=status.HTTP_200_OK)
    
class UserBrokerLogActivityView(APIView):
    permission_classes = [IsAuthenticated]  # User must be logged in

    def get(self, request, user_id, *args, **kwargs):
        try:
            # Check if requesting user is accessing their own data
            if request.user.id != user_id:
                # Allow only superadmin or subadmin to access other users' logs
                if not is_admin_or_superadmin(request.user):
                    return Response(
                        {"detail": "You do not have permission to access this user's data."},
                        status=status.HTTP_403_FORBIDDEN
                    )

            target_user = get_object_or_404(UserModel, id=user_id)
            summary = LoginActivityService().build_summary(target_user, request=request)
            return Response(summary, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"status": "error", "message": "An error occurred while retrieving broker activity."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
