"""Durable 60-second timeout for system-owned pending BUY and SELL orders."""
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import uuid

from django.conf import settings
from django.db import transaction
from django.db.models import Q, Exists, OuterRef
from django.db.models.functions import Lower, Trim
from django.utils import timezone

from main.models import PendingOrderTimeout, Tradeorderhistory, BrokerOrderIntent
from main.services.daily_broker_sessions import session_policy_error
from main.services.external_position_reconciliation import _broker_details_for_trade
from main.services.proxy_utils import build_requests_proxy_config
from main.services.pending_order_brokers import PendingOrderClient, PENDING, CANCELLING, CANCELLED, FILLED

TIMEOUT_SECONDS = 60
POLL_SECONDS = 5
LEASE_SECONDS = 90
MAX_CANCEL_ATTEMPTS = 3


def enabled():
    return bool(getattr(settings, 'PENDING_ORDER_TIMEOUT_ENABLED', False))


def _pending_filter():
    query = Q()
    for status in PENDING | CANCELLING:
        query |= Q(order_status__iexact=status) | Q(order_status__iexact=status.replace('_',' '))
    return query


def discover_and_dispatch(limit=200):
    """Recover work after restart; only system history IDs enter the monitor."""
    if not enabled():
        return {'status':'disabled','queued':0}
    from main.tasks import expire_pending_order_task
    now=timezone.now()
    watched=PendingOrderTimeout.objects.filter(
        client_id=OuterRef('client_id'),broker=Lower(Trim(OuterRef('broker'))),
        broker_order_id=OuterRef('order_id'),
    )
    candidates=Tradeorderhistory.objects.filter(_pending_filter()).filter(
        Q(transaction_type__iexact='BUY') | Q(transaction_type__iexact='SELL'),
        order_id__isnull=False,
    ).exclude(order_id__in=['','0']).exclude(broker__iexact='Demo Broker').annotate(
        timeout_exists=Exists(watched),
    ).filter(timeout_exists=False).order_by('id')[:limit]
    for trade in candidates:
        PendingOrderTimeout.objects.get_or_create(
            client_id=trade.client_id, broker=str(trade.broker or '').strip().lower(), broker_order_id=str(trade.order_id),
            defaults={'trade':trade,'side':str(trade.transaction_type).upper(),'first_seen_at':now,'next_check_at':now},
        )
    due=PendingOrderTimeout.objects.filter(state__in=['WAITING','CANCEL_REQUESTED','RETRY'],next_check_at__lte=now).filter(
        Q(lease_until__isnull=True) | Q(lease_until__lte=now),
    ).order_by('next_check_at','id').values_list('id',flat=True)[:limit]
    queued=0
    for pk in due:
        # Reserve the dispatch slot so consecutive sweeps do not enqueue duplicates.
        if PendingOrderTimeout.objects.filter(pk=pk,next_check_at__lte=now).update(next_check_at=now+timedelta(seconds=15)):
            try:
                expire_pending_order_task.apply_async(kwargs={'timeout_id':pk},queue='pending_order_timeout')
                queued+=1
            except Exception:
                PendingOrderTimeout.objects.filter(pk=pk).update(next_check_at=now)
                raise
    return {'status':'scheduled','queued':queued}


def decide(record, *, first_seen_at, pending_since, now):
    """No cancellation before a verified 60-second age, even across restarts."""
    if record.status in FILLED:
        if record.remaining != 0:
            raise ValueError('Broker reports complete with an unfilled remainder.')
        return 'TERMINAL', pending_since or first_seen_at
    if record.status in CANCELLED:
        return 'TERMINAL', pending_since or first_seen_at
    if record.status not in PENDING | CANCELLING:
        raise ValueError('Broker status is not a recognized pending or terminal state.')
    if record.remaining <= 0:
        raise ValueError('Awaiting terminal confirmation for a fully filled order.')
    since=pending_since
    if since is None:
        # Broker creation time is authoritative. Unknown time waits a full
        # minute from first observation; an old BUY time never dates a SELL.
        since=record.created_at or first_seen_at
    if since > now:
        raise ValueError('Broker order time is in the future; cancellation withheld.')
    if record.status in CANCELLING:
        return 'CONFIRM', since
    return ('CANCEL' if now >= since+timedelta(seconds=TIMEOUT_SECONDS) else 'WAIT'), since


def _price(value):
    try:
        price=Decimal(str(value))
        return price if price.is_finite() and price > 0 else None
    except (InvalidOperation,TypeError,ValueError):
        return None


def trade_terminal_updates(side, record):
    """Preserve actual fills; zero-fill cancellation is never a closed trade."""
    price=_price(record.average_price) if record.filled else None
    full=record.status in FILLED
    updates={'order_status':'complete' if full else ('partially_filled' if record.filled else record.status.lower()),
             'failure_reason':None if record.filled else 'Pending order cancelled/terminated without a fill.',
             'Total':None}
    if side=='BUY':
        updates.update(EntryQty=record.filled,Entry_Price=price,Entry_status=updates['order_status'],
                       trade_order_status='OPEN' if record.filled else 'CANCELLED')
        if not record.filled:
            updates.update(ExitQty=None,Exit_Price=None,Exit_status=None,Exit_type=None,SignalExit_time=None,
                           sltp_status='ENTRY_CANCELLED',sltp_manual_attention=False)
    else:
        updates.update(ExitQty=record.filled,Exit_Price=price,Exit_status=updates['order_status'],
                       trade_order_status='CLOSE' if full else ('PARTIAL' if record.filled else 'CANCELLED'))
        updates['SignalExit_time']=record.executed_at if record.filled else None
    return updates


def _linked_buy(trade):
    params=trade.order_params or {};signal=trade.webhook_signal or {}
    ref=params.get('original_history_id') or signal.get('original_history_id') or params.get('matched_open_history_id')
    query=Tradeorderhistory.objects.filter(client_id=trade.client_id,transaction_type__iexact='BUY')
    if ref:
        identity=Q(history_id=str(ref))
        if str(ref).isdigit():identity |= Q(pk=int(ref))
        return query.filter(identity).first()
    intent=BrokerOrderIntent.objects.filter(client_id=trade.client_id,broker_order_id=str(trade.order_id),kind='exit').exclude(exit_trade_history_id=None).first()
    return query.filter(pk=intent.exit_trade_history_id).first() if intent else None


def apply_terminal(watch, record, *, now):
    from main.brokers.contract_snapshot import build_snapshot, canonical_contract_fields
    from main.brokers.position_guard import remaining_open_quantity
    with transaction.atomic():
        trade=Tradeorderhistory.objects.select_for_update().get(pk=watch.trade_id,client_id=watch.client_id)
        if str(trade.order_id)!=watch.broker_order_id or str(trade.transaction_type).upper()!=watch.side:
            raise ValueError('System order identity changed; reconciliation stopped.')
        # A completed BUY may already have a completed SELL. Never reopen it.
        if watch.side=='BUY' and str(trade.trade_order_status).upper() in {'CLOSE','CLOSED'}:
            return
        params=dict(trade.order_params or {})
        params['pending_order_timeout']={**record.snapshot(),'observed_at':now.isoformat(),
                                        'timeout_seconds':TIMEOUT_SECONDS,'cancel_attempts':watch.cancel_attempts}
        if watch.side=='SELL':
            buy=_linked_buy(trade)
            if buy:
                params['original_history_id']=buy.history_id or str(buy.pk)
        updates=trade_terminal_updates(watch.side,record)
        # Keep the raw broker terminal status and fill evidence in a separate
        # snapshot; a partial position is not labelled as a failed BUY.
        trade.response_data={**record.snapshot(),'filled_quantity':record.filled,
                             'average_price':record.average_price,'raw_broker_status':record.status}
        trade.order_params=params
        for field,value in updates.items():setattr(trade,field,value)
        if watch.side=='BUY' and record.filled:
            identity={'tradingsymbol':record.symbol,'instrument_token':record.instrument_id,
                      'symboltoken':record.instrument_id,'securityId':record.instrument_id,
                      'exchange':record.exchange,'product':record.product,'filled_quantity':record.filled}
            fields=canonical_contract_fields(identity)
            snapshot=build_snapshot(broker_name=trade.broker,fields=fields,
                underlying=params.get('underlying') or params.get('symbol') or trade.Index_Symbol,
                expiry=params.get('expiry') or params.get('expiry_date'),strike=params.get('strike') or params.get('strike_price'),
                option_type=params.get('option_type') or params.get('Type'),buy_order_id=trade.order_id,filled_quantity=record.filled)
            trade.order_params['broker_contract_snapshot']=snapshot
            if not _price(record.average_price):
                trade.sltp_manual_attention=True
                trade.sltp_status='MANUAL_ATTENTION_REQUIRED'
                trade.sltp_last_failure_reason='Filled quantity confirmed; broker average price is unavailable.'
        trade.save(update_fields=list(set(updates)|{'response_data','order_params','sltp_manual_attention','sltp_status','sltp_last_failure_reason'}))
        if watch.side=='SELL' and buy:
            buy=Tradeorderhistory.objects.select_for_update().get(pk=buy.pk)
            confirmed_closed = str(buy.trade_order_status).upper() in {'CLOSE','CLOSED'} and str(buy.Exit_status).upper() not in {'PENDING','PENDING_BROKER_CONFIRMATION'}
            if not confirmed_closed:
                remaining=remaining_open_quantity(buy)
                # Only explicitly allocated SELL rows contribute to this BUY.
                refs=[str(buy.pk)] + ([buy.history_id] if buy.history_id else [])
                exits=Tradeorderhistory.objects.filter(client_id=buy.client_id,transaction_type__iexact='SELL').filter(
                    Q(order_params__original_history_id__in=refs)|Q(webhook_signal__original_history_id__in=refs)
                )
                fills=[r for r in exits if str(r.order_status).lower() in {'complete','completed','success','traded','partially_filled','partial'} and (r.ExitQty or 0)>0]
                total=sum(r.ExitQty for r in fills)
                prices_known=all(_price(r.Exit_Price) is not None for r in fills)
                if remaining==0 and total==int(buy.EntryQty or 0) and prices_known:
                    average=sum(Decimal(r.ExitQty)*_price(r.Exit_Price) for r in fills)/Decimal(total)
                    buy.trade_order_status='CLOSE';buy.Exit_status='complete';buy.ExitQty=total
                    buy.Exit_Price=average.quantize(Decimal('0.01'))
                    times=[r.SignalExit_time for r in fills if r.SignalExit_time]
                    buy.SignalExit_time=max(times) if len(times)==len(fills) else None
                    buy.Total=(average-buy.Entry_Price)*total if buy.Entry_Price is not None else None
                    buy.sltp_status='CLOSED';buy.sltp_manual_attention=False;buy.sltp_last_failure_reason=None
                else:
                    buy.trade_order_status='OPEN';buy.Exit_status='PARTIAL' if total else None
                    buy.ExitQty=total;buy.Exit_Price=None;buy.SignalExit_time=None;buy.Total=None
                    buy.sltp_manual_attention=True;buy.sltp_status='MANUAL_ATTENTION_REQUIRED'
                    buy.sltp_last_failure_reason=f'Exit order finished/cancelled after pending timeout; {remaining} quantity remains to reconcile or exit. Review before retrying.'
                buy.save(update_fields=['trade_order_status','Exit_status','ExitQty','Exit_Price','SignalExit_time','Total','sltp_manual_attention','sltp_status','sltp_last_failure_reason'])
            BrokerOrderIntent.objects.filter(client_id=watch.client_id,broker_order_id=watch.broker_order_id,kind='exit').update(
                status='cancelled' if record.status in CANCELLED else 'acknowledged',
                lifecycle_state='manual_attention' if record.remaining else 'filled',filled_quantity=record.filled,
                remaining_quantity=record.remaining,last_error='Exit remainder cancelled after 60 seconds; position is not closed.' if record.remaining else '')


def process_timeout(timeout_id):
    if not enabled():return {'status':'disabled'}
    now=timezone.now();lease=str(uuid.uuid4())
    acquired=PendingOrderTimeout.objects.filter(pk=timeout_id,state__in=['WAITING','RETRY','CANCEL_REQUESTED']).filter(
        Q(lease_until__isnull=True)|Q(lease_until__lte=now)).update(lease_token=lease,lease_until=now+timedelta(seconds=LEASE_SECONDS))
    if not acquired:return {'status':'busy_or_terminal'}
    owned=PendingOrderTimeout.objects.filter(pk=timeout_id,lease_token=lease)
    try:
        watch=owned.select_related('trade','trade__client').get()
        trade=watch.trade
        if trade is None:
            owned.update(state='TERMINAL',last_error='System order was consolidated or deleted; no cancellation submitted.')
            return {'status':'history_removed'}
        if str(trade.order_id)!=watch.broker_order_id or str(trade.transaction_type).upper()!=watch.side or trade.client_id!=watch.client_id:
            raise ValueError('System order identity changed.')
        details=_broker_details_for_trade(trade)
        if not details:raise ValueError('Broker details unavailable.')
        from main.broker_registry import normalize_broker_name
        if normalize_broker_name(details.broker_name.broker_name) != normalize_broker_name(watch.broker):
            raise ValueError('Assigned broker changed; cancellation withheld.')
        error=session_policy_error(details,refresh=True)
        if error:raise ValueError(error)
        proxy=build_requests_proxy_config(details.execution_node) if details.execution_node else None
        client=PendingOrderClient(details,proxy)
        params=trade.order_params or {}
        segment=str(params.get('segment') or trade.Segment or params.get('exchange') or '').upper()
        if client.broker=='groww':
            segment={'F&O':'FNO','DERIVATIVES':'FNO','NFO':'FNO','BFO':'FNO','OPTIONS':'FNO','OPTION':'FNO','FUTURES':'FNO','FUTURE':'FNO','NSE':'CASH','BSE':'CASH','EQUITY':'CASH'}.get(segment,segment)
        record=client.read(watch.broker_order_id,watch.side,segment=segment)
        now=timezone.now()
        action,since=decide(record,first_seen_at=watch.first_seen_at,pending_since=watch.pending_since,now=now)
        owned.update(pending_since=since,last_checked_at=now,last_snapshot=record.snapshot(),last_error='')
        if action=='WAIT':
            owned.update(state='WAITING',next_check_at=since+timedelta(seconds=TIMEOUT_SECONDS))
            return {'status':'waiting'}
        if action=='CANCEL':
            if watch.cancel_attempts>=MAX_CANCEL_ATTEMPTS:
                owned.update(state='ATTENTION',last_error='Cancellation not confirmed after three attempts; broker review required.')
                return {'status':'attention'}
            # Persist before sending; a worker crash cannot erase the attempt.
            watch.cancel_attempts+=1
            owned.update(state='CANCEL_REQUESTED',cancel_attempts=watch.cancel_attempts,cancel_requested_at=now)
            try:
                client.cancel(record)
            except Exception:
                # API failure/timeout is not confirmation; read exact order again.
                pass
            record=client.read(watch.broker_order_id,watch.side,segment=segment)
            action,_=decide(record,first_seen_at=watch.first_seen_at,pending_since=since,now=timezone.now())
        if action=='TERMINAL':
            # Never infer closure from cancellation ACK or net quantity alone.
            apply_terminal(watch,record,now=timezone.now())
            owned.update(state='TERMINAL',last_snapshot=record.snapshot(),last_error='',completed_at=timezone.now())
            return {'status':'terminal','broker_status':record.status,'filled':record.filled,'remaining':record.remaining}
        owned.update(state='CANCEL_REQUESTED',next_check_at=timezone.now()+timedelta(seconds=POLL_SECONDS))
        return {'status':'awaiting_broker_confirmation'}
    except Exception as exc:
        # Do not leak proxy credentials/access tokens from requests exceptions.
        message=str(exc) if isinstance(exc,ValueError) else f'Broker check unavailable ({type(exc).__name__}).'
        owned.update(state='RETRY',last_error=message,next_check_at=timezone.now()+timedelta(seconds=15))
        return {'status':'retry','message':message}
    finally:
        owned.update(lease_token='',lease_until=None)
