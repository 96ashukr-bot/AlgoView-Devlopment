from __future__ import annotations

from datetime import datetime, time, timedelta

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from main.models import (
    DailyTradeLimitCounter,
    DailyTradeLimitReservation,
    Tradeorderhistory,
)


SUCCESSFUL_ENTRY_STATUSES = {"complete", "completed", "executed", "traded", "success"}
RESERVATION_PREFIX = "daily-trade-limit:"


def normalized_trade_symbol(symbol) -> str:
    return str(symbol or "").strip().upper()


def _history_successful_buy_count(client, symbol, trade_date) -> int:
    successful_status_filter = Q()
    for status in SUCCESSFUL_ENTRY_STATUSES:
        successful_status_filter |= Q(order_status__iexact=status)
    return (
        Tradeorderhistory.objects.filter(
            client=client,
            date=trade_date,
            transaction_type__iexact="BUY",
        )
        .filter(successful_status_filter)
        .exclude(order_id__isnull=True)
        .exclude(order_id="")
        .exclude(order_id="0")
        .filter(
            Q(Index_Symbol__iexact=symbol)
            | Q(order_params__underlying__iexact=symbol)
            | Q(order_params__symbol__iexact=symbol)
            | Q(trading_symbol__iexact=symbol)
            | Q(trading_symbol__istartswith=symbol)
        )
        .count()
    )


def _get_or_initialize_counter(client, symbol, trade_date=None):
    symbol = normalized_trade_symbol(symbol)
    trade_date = trade_date or timezone.localdate()
    if not client or not symbol:
        return None
    initial_count = _history_successful_buy_count(client, symbol, trade_date)
    counter, _ = DailyTradeLimitCounter.objects.get_or_create(
        client=client,
        trade_date=trade_date,
        symbol=symbol,
        defaults={"successful_buy_count": initial_count},
    )
    return counter


def successful_buy_count(client, symbol, *, trade_date=None) -> int:
    counter = _get_or_initialize_counter(client, symbol, trade_date=trade_date)
    return int(counter.successful_buy_count) if counter else 0


def _reservation_expiry():
    local_now = timezone.localtime()
    tomorrow = local_now.date() + timedelta(days=1)
    return timezone.make_aware(
        datetime.combine(tomorrow, time.min),
        timezone.get_current_timezone(),
    ) + timedelta(hours=1)


def _reservation_token(reservation_id: int) -> str:
    return f"{RESERVATION_PREFIX}{reservation_id}"


def _reservation_id(reservation_key):
    value = str(reservation_key or "")
    if not value.startswith(RESERVATION_PREFIX):
        return None
    try:
        return int(value[len(RESERVATION_PREFIX):])
    except (TypeError, ValueError):
        return None


def reserve_successful_buy_slot(client, symbol, limit: int, request_id=None):
    """Reserve one indexed daily BUY slot in a short database transaction."""
    limit = int(limit or 0)
    symbol = normalized_trade_symbol(symbol)
    if not client or not symbol or limit <= 0:
        return None

    counter = _get_or_initialize_counter(client, symbol)
    request_id = str(request_id or "")[:128]
    if not counter or not request_id:
        return None

    with transaction.atomic():
        counter = DailyTradeLimitCounter.objects.select_for_update().get(pk=counter.pk)
        DailyTradeLimitReservation.objects.filter(
            counter=counter,
            status=DailyTradeLimitReservation.STATUS_RESERVED,
            expires_at__lte=timezone.now(),
        ).update(status=DailyTradeLimitReservation.STATUS_RELEASED)

        existing = DailyTradeLimitReservation.objects.filter(
            counter=counter,
            request_id=request_id,
        ).first()
        if existing and existing.status == DailyTradeLimitReservation.STATUS_RESERVED:
            return _reservation_token(existing.id)
        if existing and existing.status == DailyTradeLimitReservation.STATUS_SUCCESS:
            return None

        active_reservations = DailyTradeLimitReservation.objects.filter(
            counter=counter,
            status=DailyTradeLimitReservation.STATUS_RESERVED,
            expires_at__gt=timezone.now(),
        ).count()
        if int(counter.successful_buy_count) + active_reservations >= limit:
            return None

        if existing:
            existing.status = DailyTradeLimitReservation.STATUS_RESERVED
            existing.expires_at = _reservation_expiry()
            existing.save(update_fields=["status", "expires_at", "updated_at"])
            reservation = existing
        else:
            reservation = DailyTradeLimitReservation.objects.create(
                counter=counter,
                request_id=request_id,
                status=DailyTradeLimitReservation.STATUS_RESERVED,
                expires_at=_reservation_expiry(),
            )
        return _reservation_token(reservation.id)


def complete_successful_buy_slot(reservation_key) -> None:
    reservation_id = _reservation_id(reservation_key)
    if not reservation_id:
        return
    with transaction.atomic():
        reservation = DailyTradeLimitReservation.objects.select_for_update().filter(pk=reservation_id).first()
        if not reservation or reservation.status != DailyTradeLimitReservation.STATUS_RESERVED:
            return
        reservation.status = DailyTradeLimitReservation.STATUS_SUCCESS
        reservation.save(update_fields=["status", "updated_at"])
        DailyTradeLimitCounter.objects.filter(pk=reservation.counter_id).update(
            successful_buy_count=F("successful_buy_count") + 1,
            updated_at=timezone.now(),
        )


def release_successful_buy_slot(reservation_key) -> None:
    reservation_id = _reservation_id(reservation_key)
    if not reservation_id:
        return
    DailyTradeLimitReservation.objects.filter(
        pk=reservation_id,
        status=DailyTradeLimitReservation.STATUS_RESERVED,
    ).update(status=DailyTradeLimitReservation.STATUS_RELEASED, updated_at=timezone.now())
