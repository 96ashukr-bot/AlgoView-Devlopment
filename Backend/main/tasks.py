# # users/tasks.py
# from celery import shared_task
# from django.core.mail import send_mail
# from django.conf import settings

# @shared_task
# def send_password_email(email, password):
#     subject = 'Your account has been created'
#     message = f'Your account has been created. Your password is: {password}'
#     from_email = settings.DEFAULT_FROM_EMAIL
#     send_mail(subject, message, from_email, [email])
# tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import logging
import uuid
logger = logging.getLogger('main')
OTP_EMAIL_SUBJECT = "Your Login Otp (Don't Share with anyone)"
OTP_SUPPORT_EMAIL = "support@bridgesparkinnovation.com"
OTP_SENDER_NAME = "SparksOtp"
REGISTRATION_EMAIL_SUBJECT = "Registration Successful"
REGISTRATION_LOGIN_LINK = "https://app.sparkstechnologies.co.in/login"
REGISTRATION_SUPPORT_EMAIL = "support@bridgesparkinnovation.com"
REGISTRATION_SENDER_NAME = "SparksRegistration"
PASSWORD_RESET_APP_URL = "https://app.sparkstechnologies.co.in"
PASSWORD_RESET_SUPPORT_EMAIL = "support@bridgesparkinnovation.com"
PASSWORD_RESET_SENDER_NAME = "SparksResetPassword"

from main.models import *
from main.utils import get_smtp_connection
from django.templatetags.static import static
    # Get company profile for support email and website
# company_profile = CompanyProfileDetails.objects.first()
from main.companysmtpsetails import get_company_profile,get_smtp_details


FORCE_KILL_DISPATCH_TTL_SECONDS = 120
FORCE_KILL_SWITCH_QUEUE = "kill_switch"
WEBHOOK_EXECUTION_QUEUE = "webhook_execution"


def schedule_broker_session_warmup(broker_details_id):
    """Queue post-login warming without delaying the broker callback response."""
    try:
        broker_details_id = int(broker_details_id)
    except (TypeError, ValueError):
        return None
    try:
        result = warm_single_broker_session_task.apply_async(
            kwargs={"broker_details_id": broker_details_id},
            queue=WEBHOOK_EXECUTION_QUEUE,
        )
        return result.id
    except Exception:
        logger.exception(
            "Unable to schedule broker session warmup broker_details_id=%s",
            broker_details_id,
        )
        return None


def _force_kill_dispatch_key(trade_history_id):
    return f"force-kill-switch:dispatch:{int(trade_history_id)}"


def acquire_force_kill_dispatch(trade_history_id, token=None):
    token = token or uuid.uuid4().hex
    return token if cache.add(
        _force_kill_dispatch_key(trade_history_id),
        token,
        timeout=FORCE_KILL_DISPATCH_TTL_SECONDS,
    ) else None


def release_force_kill_dispatch(trade_history_id, token):
    key = _force_kill_dispatch_key(trade_history_id)
    if token and cache.get(key) == token:
        cache.delete(key)
company_profile = get_company_profile()
smtp_details = get_smtp_details()


@shared_task(bind=True, autoretry_for=(), max_retries=0)
def warm_single_angel_session_task(self, *, broker_details_id):
    """Validate one Angel session outside the latency-sensitive order path."""
    from main.angelone.services.auth_service import AuthService
    from main.models import ClientBrokerdetails
    from main.services.proxy_utils import build_requests_proxy_config

    broker_details = ClientBrokerdetails.objects.select_related(
        "client", "broker_name", "execution_node",
    ).filter(pk=broker_details_id, client__is_enable=True).first()
    if broker_details is None:
        return {"status": "missing", "broker_details_id": broker_details_id}

    client_code = (
        getattr(broker_details, "broker_Demate_User_Name", None)
        or getattr(broker_details, "broker_API_UID", None)
    )
    api_key = getattr(broker_details, "broker_API_KEY", None)
    if not client_code or not api_key:
        return {"status": "skipped", "reason": "missing_credentials", "broker_details_id": broker_details_id}
    if broker_details.execution_node is None:
        return {"status": "skipped", "reason": "missing_execution_node", "broker_details_id": broker_details_id}
    try:
        proxy_config = build_requests_proxy_config(broker_details.execution_node)
    except ValueError as exc:
        return {"status": "skipped", "reason": str(exc), "broker_details_id": broker_details_id}

    try:
        result = AuthService().ensure_valid_session(
            client_id=client_code,
            api_key=api_key,
            broker_details=broker_details,
            verify_remote=True,
            proxy_config=proxy_config,
        )
    except Exception as exc:
        logger.warning(
            "Angel session warmup failed broker_details_id=%s error=%s",
            broker_details_id,
            exc,
        )
        return {
            "status": "failed",
            "broker_details_id": broker_details_id,
            "reason": str(exc),
        }
    return {
        "status": result.get("status"),
        "source": result.get("source"),
        "broker_details_id": broker_details_id,
    }


@shared_task(bind=True, autoretry_for=(), max_retries=0)
def warm_active_angel_sessions_task(self):
    """Spread active Angel session validation across a five-minute window."""
    from main.broker_registry import normalize_broker_name
    from main.models import ClientBrokerdetails

    broker_detail_ids = [
        details.id
        for details in ClientBrokerdetails.objects.select_related("broker_name").filter(client__is_enable=True)
        if normalize_broker_name(getattr(details.broker_name, "broker_name", "")) == "angel one"
    ]
    count = len(broker_detail_ids)
    spacing_seconds = (300.0 / count) if count else 0
    for index, broker_details_id in enumerate(broker_detail_ids):
        warm_single_angel_session_task.apply_async(
            kwargs={"broker_details_id": broker_details_id},
            countdown=round(index * spacing_seconds, 2),
        )
    return {"status": "scheduled", "count": count, "spacing_seconds": round(spacing_seconds, 3)}


@shared_task(bind=True, autoretry_for=(), max_retries=0, soft_time_limit=120, time_limit=150)
def warm_single_broker_session_task(self, *, broker_details_id):
    """Validate one non-Angel broker session before trading starts."""
    from main.broker_registry import normalize_broker_name
    from main.brokers import get_broker_adapter
    from main.models import ClientBrokerdetails
    from main.services.execution_nodes import mark_execution_node_broker_verified_from_valid_token
    from main.services.proxy_utils import build_requests_proxy_config

    broker_details = ClientBrokerdetails.objects.select_related(
        "client", "broker_name", "execution_node",
    ).filter(pk=broker_details_id, client__is_enable=True).first()
    if broker_details is None:
        return {"status": "missing", "broker_details_id": broker_details_id}
    if broker_details.execution_node is None:
        return {"status": "skipped", "reason": "missing_execution_node", "broker_details_id": broker_details_id}
    broker_name = normalize_broker_name(getattr(broker_details.broker_name, "broker_name", ""))
    if broker_name == "angel one":
        return warm_single_angel_session_task.run(broker_details_id=broker_details_id)
    try:
        proxy_config = build_requests_proxy_config(broker_details.execution_node)
        result = get_broker_adapter(broker_details).validate_credentials(proxy_config=proxy_config)
    except Exception as exc:
        logger.warning(
            "Broker session prewarm failed broker_details_id=%s broker=%s error=%s",
            broker_details_id,
            broker_name,
            exc,
        )
        return {
            "status": "failed",
            "broker": broker_name,
            "broker_details_id": broker_details_id,
            "reason": str(exc),
        }
    status_value = str(result.get("status") or "").strip().lower()
    if status_value == "success":
        mark_execution_node_broker_verified_from_valid_token(
            broker_details.client,
            broker_details.execution_node,
        )
    return {
        "status": status_value or "failed",
        "broker": broker_name,
        "broker_details_id": broker_details_id,
        "message": result.get("message"),
    }


@shared_task(bind=True, autoretry_for=(), max_retries=0)
def warm_active_broker_sessions_task(self):
    """Spread all active broker-session checks across the pre-market window."""
    from main.models import ClientBrokerdetails

    broker_detail_ids = list(
        ClientBrokerdetails.objects.filter(
            client__is_enable=True,
            execution_node__isnull=False,
        )
        .order_by("id")
        .values_list("id", flat=True)
    )
    count = len(broker_detail_ids)
    spacing_seconds = (900.0 / count) if count else 0
    for index, broker_details_id in enumerate(broker_detail_ids):
        warm_single_broker_session_task.apply_async(
            kwargs={"broker_details_id": broker_details_id},
            countdown=round(index * spacing_seconds, 2),
            queue=WEBHOOK_EXECUTION_QUEUE,
        )
    return {"status": "scheduled", "count": count, "spacing_seconds": round(spacing_seconds, 3)}


@shared_task(bind=True, autoretry_for=(), max_retries=0, soft_time_limit=1200, time_limit=1500)
def refresh_and_prewarm_broker_masters_task(self):
    """Refresh durable broker masters, then atomically load execution indexes."""
    from django.core.management import call_command
    from main.broker_instrument_cache import prewarm_broker_instrument_indexes

    refresh_status = "success"
    refresh_error = None
    try:
        call_command("refresh_broker_instrument_masters", verbosity=0)
    except BaseException as exc:
        # The refresh command intentionally fails when a provider is unavailable.
        # Preserve and preload the previous valid snapshots instead of leaving the
        # live execution path without an instrument index.
        refresh_status = "cached_fallback"
        refresh_error = str(exc)
        logger.warning("Pre-market broker master refresh used cached fallback: %s", exc)
    prewarm_broker_instrument_indexes()
    prewarm_webhook_instrument_indexes_task.apply_async(queue=WEBHOOK_EXECUTION_QUEUE)
    return {"status": refresh_status, "error": refresh_error}


@shared_task(bind=True, autoretry_for=(), max_retries=0, soft_time_limit=300, time_limit=360)
def prewarm_webhook_instrument_indexes_task(self):
    """Load refreshed snapshots inside the dedicated webhook worker process."""
    from main.broker_instrument_cache import prewarm_broker_instrument_indexes
    from main.angelone.managers.contract_manager import ContractMasterManager

    prewarm_broker_instrument_indexes()
    angel_ready = ContractMasterManager.get_instance().initialize(blocking=True)
    return {"status": "ready" if angel_ready else "cached_fallback"}


@shared_task(bind=True, autoretry_for=(), max_retries=0)
def route_execution_order_task(self, *, client_id, broker_details_id, order_payload, correlation_id=None):
    """Proxy-safe order execution task; all broker egress stays inside the router."""
    from main.models import ClientBrokerdetails, User
    from main.services.execution_router import route_order_to_execution_node

    client = User.objects.get(pk=client_id)
    broker_details = ClientBrokerdetails.objects.select_related("execution_node", "broker_name").get(
        pk=broker_details_id,
        client=client,
    )
    payload = dict(order_payload or {})
    if correlation_id:
        payload.setdefault("correlation_id", correlation_id)
        payload.setdefault("idempotency_key", correlation_id)
    return route_order_to_execution_node(client, broker_details, payload)


@shared_task(bind=True, autoretry_for=(), max_retries=0)
def force_kill_switch_trade_task(self, *, trade_history_id, reason="", initiated_by_id=None, dispatch_token=None):
    """Run a force kill-switch exit outside the request/response cycle."""
    from django.contrib.auth import get_user_model
    from main.execution_engine import get_execution_engine
    from main.models import Tradeorderhistory
    from main.views import (
        _build_regular_trade_exit_request,
        _extract_force_exit_message,
        _mark_trade_closed_after_force_exit,
    )

    owns_dispatch = bool(dispatch_token)
    if not dispatch_token:
        dispatch_token = acquire_force_kill_dispatch(trade_history_id)
        owns_dispatch = bool(dispatch_token)
        if not dispatch_token:
            return {
                "trade_history_id": trade_history_id,
                "status": "duplicate_blocked",
                "message": "A Kill Switch exit is already in progress for this trade.",
            }

    try:
        trade_history = Tradeorderhistory.objects.select_related("client").filter(pk=trade_history_id).first()
        if trade_history is None:
            return {"trade_history_id": trade_history_id, "status": "missing", "message": "Trade history row not found."}

        initiated_by = None
        if initiated_by_id:
            initiated_by = get_user_model().objects.filter(pk=initiated_by_id).first()

        exit_request = _build_regular_trade_exit_request(
            trade_history,
            force_broker_squareoff=True,
            source="authorized_force_kill_switch",
            reason=reason,
            initiated_by=initiated_by,
        )
        response = get_execution_engine().execute_order(exit_request)
        from main.services.external_position_reconciliation import reconcile_failed_exit_response

        response = reconcile_failed_exit_response(trade_history, response)
        response_data = response.get("data", {}) if isinstance(response, dict) else {}
        response_status = str(response_data.get("status") or response.get("status") or "").lower()
        success = response_status in {"success", "complete", "completed", "open", "placed", "reconciled_closed"}
        message = _extract_force_exit_message(response)
        if not success and message.strip().lower() == "success":
            message = f"Broker rejected force exit. Broker status: {response_status or 'unknown'}."
        if success:
            _mark_trade_closed_after_force_exit(trade_history, response)
        return {
            "trade_history_id": trade_history.id,
            "client_id": trade_history.client_id,
            "client_name": getattr(trade_history.client, "fullName", None) or getattr(trade_history.client, "full_name", None),
            "status": "sent" if success else "broker_rejected",
            "broker_status": response_data.get("status") or response.get("status"),
            "message": message,
            "order_id": response_data.get("order_id"),
            "response": response,
        }
    finally:
        if owns_dispatch:
            release_force_kill_dispatch(trade_history_id, dispatch_token)


def _history_has_reconciled_price(history):
    transaction_type = str(getattr(history, "transaction_type", "") or "").strip().upper()
    price = history.Exit_Price if transaction_type == "SELL" else history.Entry_Price
    return price not in (None, "")


def _reconciliation_is_terminal(history):
    status = str(getattr(history, "order_status", "") or "").strip().lower()
    if status in {"rejected", "cancelled", "canceled", "failed"}:
        return True
    if status in {"complete", "completed", "success", "traded", "filled", "executed"}:
        return _history_has_reconciled_price(history)
    return False


def _sync_manual_result_from_reconciled_history(history):
    from main.models import ManualTradeResult

    manual_result = ManualTradeResult.objects.filter(history_id=history.history_id).first()
    if manual_result is None:
        return
    broker_status = str(history.order_status or "").strip().lower()
    if broker_status in {"complete", "completed", "success", "traded", "filled", "executed"}:
        result_status = ManualTradeResult.STATUS_SUCCESS
        reason = "Broker execution confirmed."
    elif broker_status in {"rejected", "cancelled", "canceled", "failed"}:
        result_status = ManualTradeResult.STATUS_FAILED
        reason = history.failure_reason or f"Broker order was {broker_status}."
    else:
        return
    ManualTradeResult.objects.filter(pk=manual_result.pk).update(
        status=result_status,
        broker_status=broker_status,
        reason=reason,
        updated_at=timezone.now(),
    )
    try:
        from main.manual_trade_service import _finalize_manual_trade_batch

        _finalize_manual_trade_batch(manual_result.batch_id)
    except Exception:
        logger.exception(
            "Could not finalize reconciled manual trade batch",
            extra={"batch_id": manual_result.batch_id, "history_id": history.history_id},
        )


@shared_task(bind=True, autoretry_for=(), max_retries=20, acks_late=True)
def reconcile_zerodha_order_task(self, *, trade_history_id):
    """Refresh a non-terminal Zerodha order from the client's broker order book."""
    from main.broker_registry import normalize_broker_name
    from main.models import ClientBrokerdetails, Tradeorderhistory
    from main.services.broker_fill_reconciliation import refresh_trade_fill_from_broker

    terminal_statuses = {"complete", "completed", "rejected", "cancelled", "canceled"}
    trade_history = Tradeorderhistory.objects.select_related("client").filter(pk=trade_history_id).first()
    if trade_history is None:
        return {"status": "missing", "trade_history_id": trade_history_id}

    current_status = str(trade_history.order_status or "").strip().lower()
    if current_status in terminal_statuses:
        return {"status": current_status, "trade_history_id": trade_history_id}

    broker_details = next(
        (
            details
            for details in ClientBrokerdetails.objects.select_related("broker_name", "execution_node").filter(
                client=trade_history.client
            )
            if normalize_broker_name(getattr(details.broker_name, "broker_name", "")) == "zerodha"
        ),
        None,
    )
    if broker_details is None:
        return {"status": "broker_details_missing", "trade_history_id": trade_history_id}

    refresh_trade_fill_from_broker(trade_history, broker_details)
    trade_history.refresh_from_db()
    current_status = str(trade_history.order_status or "").strip().lower()
    if current_status in terminal_statuses:
        return {"status": current_status, "trade_history_id": trade_history_id}

    countdown = min(15 + (self.request.retries * 5), 60)
    raise self.retry(countdown=countdown)


@shared_task(bind=True, autoretry_for=(), max_retries=60, acks_late=True)
def reconcile_broker_order_task(self, *, trade_history_id):
    """Poll any broker order until terminal and persist the broker fill."""
    from main.broker_registry import normalize_broker_name
    from main.models import ClientBrokerdetails, Tradeorderhistory
    from main.services.broker_fill_reconciliation import refresh_trade_fill_from_broker

    history = Tradeorderhistory.objects.select_related("client").filter(pk=trade_history_id).first()
    if history is None:
        return {"status": "missing", "trade_history_id": trade_history_id}
    if _reconciliation_is_terminal(history):
        _sync_manual_result_from_reconciled_history(history)
        return {"status": str(history.order_status or "").strip().lower(), "trade_history_id": trade_history_id}

    target_broker = normalize_broker_name(history.broker)
    broker_details = next(
        (
            details
            for details in ClientBrokerdetails.objects.select_related("broker_name", "execution_node").filter(
                client=history.client
            )
            if normalize_broker_name(getattr(details.broker_name, "broker_name", "")) == target_broker
        ),
        None,
    )
    if broker_details is None:
        return {"status": "broker_details_missing", "trade_history_id": trade_history_id}

    refresh_trade_fill_from_broker(history, broker_details)
    history.refresh_from_db()
    if _reconciliation_is_terminal(history):
        _sync_manual_result_from_reconciled_history(history)
        return {"status": str(history.order_status or "").strip().lower(), "trade_history_id": trade_history_id}
    countdown = min(15 + (self.request.retries * 5), 120)
    raise self.retry(countdown=countdown)


@shared_task(bind=True, autoretry_for=(), max_retries=0, acks_late=True, soft_time_limit=300, time_limit=360)
def process_manual_trade_batch_task(self, *, batch_id):
    from main.manual_trade_service import execute_manual_trade_batch

    logger.info("Manual trade batch task started batch_id=%s task_id=%s", batch_id, getattr(self.request, "id", None))
    result = execute_manual_trade_batch(batch_id)
    logger.info("Manual trade batch task completed batch_id=%s result=%s", batch_id, result)
    return result


@shared_task(
    bind=True,
    autoretry_for=(),
    max_retries=0,
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=240,
    time_limit=300,
)
def process_single_webhook_trade_task(
    self, *, trade_id, index, context, history_mode="default", entry_order_key=None
):
    """Execute one webhook-matched trade so slow clients cannot block the batch."""
    from django.utils import timezone
    from main.models import ClientTradeSetting
    from main.views import _get_trade_execution_symbol, _process_webhook_trade, _save_webhook_trade_skip

    context = dict(context or {})
    worker_started_at = timezone.now()
    context.setdefault("entry_timing", {})["worker_started_at"] = worker_started_at.isoformat()
    published_at = context.get("entry_task_published_at")
    if published_at:
        try:
            from datetime import datetime
            queued_for = (
                worker_started_at - datetime.fromisoformat(str(published_at).replace("Z", "+00:00"))
            ).total_seconds()
            logger.info(
                "Entry worker started trade_setting=%s queue_wait_ms=%s task_id=%s",
                trade_id, max(0, round(queued_for * 1000)), getattr(self.request, "id", None),
            )
        except (TypeError, ValueError):
            pass
    trade = (
        ClientTradeSetting.objects.select_related(
            "client",
            "segment",
            "sub_segment",
        )
        .filter(pk=trade_id)
        .first()
    )
    if trade is None:
        return {
            "trade_setting_id": trade_id,
            "status": "skipped",
            "reason": "Trade setting was not found when the webhook task executed.",
        }

    signal_log_id = context.get("signal_log_id") or context.get("webhook_signal_log_id")
    history_id = None
    if signal_log_id:
        history_id = f"webhook_{signal_log_id}_{trade.client_id}_{trade.id}"
    elif history_mode == "legacy":
        history_id = f"{timezone.now().strftime('%Y%m%d%H%M%S%f')}_{trade.client_id}_{trade.id}"

    try:
        from celery.exceptions import Retry
        from main.services.entry_control import (
            EntryAccountTurnDeferred,
            account_fifo_turn,
            reserve_entry,
        )

        order_key = str(entry_order_key or history_id or f"webhook:{trade.client_id}:{trade.id}")
        reserve_entry(order_key)
        transaction_type = str(context.get("transaction_type") or "").strip().upper()
        is_exit = transaction_type in {"SELL", "EXIT", "CLOSE", "SELL_CE", "SELL_PE"}
        if is_exit:
            return _process_webhook_trade(trade, index, context, history_id=history_id)
        try:
            with account_fifo_turn(
                broker=trade.broker,
                client_id=trade.client_id,
                order_key=order_key,
            ):
                return _process_webhook_trade(trade, index, context, history_id=history_id)
        except EntryAccountTurnDeferred as exc:
            raise self.retry(exc=exc, countdown=1, max_retries=300)
    except Retry:
        raise
    except Exception as exc:
        logger.exception(
            "Webhook single trade task failed for trade_setting=%s task_id=%s",
            trade_id,
            getattr(self.request, "id", None),
        )
        fallback_history_id = history_id or f"webhook_failed_{timezone.now().strftime('%Y%m%d%H%M%S%f')}_{trade.client_id}_{trade.id}"
        reason = f"Webhook worker failed before broker execution: {str(exc)}"
        trade_symbol = _get_trade_execution_symbol(trade) or str(context.get("symbols") or "").strip()
        index_symbol = trade_symbol or str(context.get("symbols") or "").strip() or None
        order_params = {
            "symbol": trade_symbol,
            "Exchange": context.get("exch_seg"),
            "quantity": trade.quantity or context.get("default_quantity") or 0,
            "product_type": trade.product_type,
            "transaction_type": context.get("buy_sell"),
            "strike": context.get("default_price"),
            "strike_price": context.get("default_price"),
            "ordertype": context.get("default_ordertype"),
            "order_type": context.get("default_ordertype"),
            "strategy": getattr(trade, "strategy", None),
        }
        try:
            _save_webhook_trade_skip(
                trade=trade,
                history_id=fallback_history_id,
                live_price=context.get("live_price"),
                group_service=trade.group_service,
                transaction_type=context.get("transaction_type") or "UNKNOWN",
                strategy=trade.strategy,
                webhook_signal=context.get("alert_data") or {},
                exchange=context.get("exch_seg"),
                segment=trade.segment.name if trade.segment else None,
                index_symbol=index_symbol,
                order_params=order_params,
                reason_message=reason,
                skip_reasons=[reason],
            )
        except Exception:
            logger.exception(
                "Failed to save fallback webhook failure history for trade_setting=%s history_id=%s",
                trade_id,
                fallback_history_id,
            )
        return {
            "history_id": fallback_history_id,
            "trade_setting_id": trade_id,
            "status": "failed",
            "reason": reason,
        }


@shared_task(
    bind=True,
    autoretry_for=(),
    max_retries=0,
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=60,
    time_limit=90,
)
def process_webhook_signal_task(self, *, trade_ids, context, history_mode="default"):
    """Queue webhook-matched trades outside the request/response path."""
    trade_ids = list(trade_ids or [])
    context = dict(context or {})
    queued_tasks = []
    from main.models import ClientTradeSetting
    from main.services.entry_control import enqueue_account_order
    from main.services.entry_dispatch import entry_queue_for_broker

    rows = ClientTradeSetting.objects.filter(pk__in=trade_ids).values("id", "client_id", "broker")
    accounts = {row["id"]: row for row in rows}
    transaction_type = str(context.get("transaction_type") or "").strip().upper()
    is_exit = transaction_type in {"SELL", "EXIT", "CLOSE", "SELL_CE", "SELL_PE"}
    stream_specs = []

    for index, trade_id in enumerate(trade_ids, start=1):
        account = accounts.get(trade_id, {})
        task_context = dict(context)
        task_context["entry_timing"] = dict(context.get("entry_timing") or {})
        task_context["entry_task_published_at"] = timezone.now().isoformat()
        task_context["entry_timing"]["task_published_at"] = task_context["entry_task_published_at"]
        signal_id = context.get("signal_log_id") or context.get("webhook_signal_log_id") or "legacy"
        order_key = f"webhook:{signal_id}:{account.get('client_id')}:{trade_id}"
        broker = account.get("broker")
        client_id = account.get("client_id")
        if (
            getattr(settings, "ORDER_STREAMS_ENABLED", False)
            and not is_exit
            and broker
            and client_id
        ):
            from main.models import BrokerOrderIntent
            stream_specs.append({
                "idempotency_key": order_key,
                "kind": BrokerOrderIntent.KIND_ENTRY,
                "broker": broker,
                "client_id": client_id,
                "source_type": "webhook_trade",
                "source_id": str(trade_id),
                "payload": {"index": index, "context": task_context, "history_mode": history_mode,
                            "trade_setting_id": trade_id},
            })
        if not is_exit:
            enqueue_account_order(broker=broker, client_id=client_id, order_key=order_key)
        task = process_single_webhook_trade_task.apply_async(
            kwargs={
                "trade_id": trade_id,
                "index": index,
                "context": task_context,
                "history_mode": history_mode,
                "entry_order_key": order_key,
            },
            queue=WEBHOOK_EXECUTION_QUEUE if is_exit else entry_queue_for_broker(broker),
            priority=8,
        )
        queued_tasks.append({"trade_setting_id": trade_id, "task_id": task.id})

    if stream_specs:
        from main.services.order_streams import create_intents_batch
        create_intents_batch(stream_specs)

    summary = {
        "total": len(trade_ids),
        "queued": len(queued_tasks),
    }
    logger.info("Webhook dispatch task completed task_id=%s summary=%s", getattr(self.request, "id", None), summary)
    return {"summary": summary, "queued_tasks": queued_tasks}


@shared_task(
    bind=True,
    autoretry_for=(),
    max_retries=300,
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=240,
    time_limit=300,
)
def process_single_manual_trade_result_task(
    self, *, result_id, entry_order_key=None, broker=None, client_id=None
):
    """Execute one manual BUY on its broker queue and serialize its account."""
    from main.manual_trade_service import _execute_manual_trade_result
    from main.services.entry_control import EntryAccountTurnDeferred, account_fifo_turn, reserve_entry

    order_key = str(entry_order_key or f"manual-result:{result_id}")
    reserve_entry(order_key)
    try:
        with account_fifo_turn(
            broker=str(broker or "unknown"),
            client_id=int(client_id or 0),
            order_key=order_key,
        ):
            _execute_manual_trade_result(result_id)
    except EntryAccountTurnDeferred as exc:
        raise self.retry(exc=exc, countdown=1, max_retries=300)
    return {"result_id": result_id, "status": "processed"}


@shared_task
def recover_stale_manual_trade_results_task():
    from main.manual_trade_service import recover_stale_manual_trade_results

    return recover_stale_manual_trade_results()

company_profile=company_profile if company_profile else None

support_email = company_profile.company_support_email if company_profile else "support@example.com"
company_website = company_profile.company_website if company_profile else "https://example.com"
logo_url = company_profile.company_logo if company_profile else "https://example.com/logo.png"
login_link = company_profile.login_link if company_profile else "https://www.admin.algoview.in/login"
help_center_link = company_profile.help_center_link if company_profile else "https://www.admin.algoview.in/login"  
contact_number = company_profile.company_phone_number if company_profile else None
company_name = company_profile.company_name if company_profile else "AlgoView"
company_sender_name=company_profile.company_sender_name if company_profile else "AlgoAdmin"
if company_profile and company_profile.company_logo:
    logo_url = settings.MEDIA_URL + str(company_profile.company_logo)  # Ensure full URL
else:
    logo_url = static('company_logos/download.png')  # Fallback to a default logo
smtp_details=smtp_details if smtp_details else None
# smtp_details=CompanySmtpDetails.objects.first()
default_from_email=smtp_details.email_host_user if smtp_details else   "no-reply@example.com"

def _get_default_from_email():
    smtp_details = get_smtp_details()
    return (
        getattr(smtp_details, "default_from_email", None)
        or getattr(smtp_details, "email_host_user", None)
        or settings.DEFAULT_FROM_EMAIL
    )

#client inactive and license expir ations
@shared_task
def send_client_acc_email_async(subject,messages,username,useremail):
        smtp_connection = get_smtp_connection()
        if not smtp_connection:
            print(f"SMTP connection could not be established!")
            return
        subject=subject
        from_email = _get_default_from_email()
        context = {
            'user_name': username,          
            'support_email': support_email, 
            'company_website':company_website , 
            "messages":messages,
            "company_name":company_name,
            "logo_url":logo_url
        }
        html_message = render_to_string('login_account_email.html', context)
        # print("html_message",html_message)

        email_message = EmailMultiAlternatives(subject, "", f"{company_sender_name} <{from_email}>", [useremail],connection=smtp_connection)
        email_message.attach_alternative(html_message, "text/html") 
        email_message.send()
#login opt email
@shared_task
def send_email_async(user_name, otp_code, email):
    smtp_connection = get_smtp_connection()
    if not smtp_connection:
        print(f"SMTP connection could not be established!")
        return
    subject = OTP_EMAIL_SUBJECT
    from_email = _get_default_from_email()
    # Define the context for the email template
    print("logo_url**************",logo_url)
    context = {
        'user_name': user_name,
        'otp_code': otp_code,            
        'valid_for_minutes': 2, 
        'support_email': OTP_SUPPORT_EMAIL,  
        'company_website':company_website, 
        'logo_url':logo_url,
        'help_center': help_center_link,
        'contact_number': contact_number,
        'company_name':company_name
    }
    html_message = render_to_string('login_email.html', context)
    try:
        email_message = EmailMultiAlternatives(subject, "", f"{OTP_SENDER_NAME} <{from_email}>", [email], connection=smtp_connection)
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Email sending failed: {e}")
    # send_mail(subject, message, from_email, recipient_list)
   
# tasks.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
@shared_task
def send_email_pass_async(email, password, user_name, login_link, support_email, help_center_link, company_website, contact_number):
        smtp_connection = get_smtp_connection()
        if not smtp_connection:
            print("SMTP connection could not be established!")
            return
        subject = REGISTRATION_EMAIL_SUBJECT
        # subject = "Welcome to AlgoView Technologies"
        print("email sentdd")
        from_email = _get_default_from_email()
        # Render the HTML template with context data
        context = {
            'user_name': user_name,
            'password': password,
            'login_link': REGISTRATION_LOGIN_LINK,
            'support_email': REGISTRATION_SUPPORT_EMAIL,
            'help_center': help_center_link,
            'company_website': company_website,
            'contact_number': contact_number,
            'company_name':company_name,
            'logo_url':logo_url
        }
        html_message = render_to_string('welcome_email.html', context)
        # print("html msg:::::::",html_message)
        from_email = _get_default_from_email()
        
        # Create the email
        email_message = EmailMultiAlternatives(subject, "", f"{REGISTRATION_SENDER_NAME} <{from_email}>", [email],connection=smtp_connection)
        email_message.attach_alternative(html_message, "text/html")  # Attach the HTML version

        # Send the email
        email_message.send()

@shared_task
def send_kyc_email_async(email, from_email, user_name, action, reason):
    smtp_connection = get_smtp_connection()
    if not smtp_connection:
        print("SMTP connection could not be established!")
        return
    if isinstance(email, list):
        email = email[0]  
    if isinstance(from_email, list):
        from_email = from_email[0]
    if action == 'approve':
        subject = "Your KYC has been approved"
    else:
        subject = "Your KYC has been rejected"

    context = {
        'user_name': user_name,
        'action': action,
        'reason': reason,
        'support_email': support_email,
        'help_center': help_center_link,
        'company_website': company_website,
        'contact_number': contact_number,
        "company_name":company_name,
        "logo_url":logo_url
    }
    html_message = render_to_string('kyc_email.html', context)
  
    # Create the email with an HTML alternative
    email_message = EmailMultiAlternatives(subject, "",f"{company_sender_name} <{from_email}>", [email],connection=smtp_connection)
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()
    

@shared_task
def send_trade_email_async(email, from_email, user_name, status, reason):
    smtp_connection = get_smtp_connection()
    if not smtp_connection:
        print("SMTP connection could not be established!")
        logger.info(f"{user_name} : SMTP connection could not be established")
        return
    if isinstance(email, list):
        email = email[0]  
    if isinstance(from_email, list):
        from_email = from_email[0]
    subject="email for trade order!!!!!!!!!!!!"
    context = {
        'user_name': user_name,
        'status':status,
        'reason': reason,
        'support_email': support_email,
        'help_center': help_center_link,
        'company_website': company_website,
        'contact_number': contact_number,
        "company_name":company_name,
        "logo_url":logo_url
    }
    html_message = render_to_string('trade.html', context)
  
    # Create the email with an HTML alternative
    email_message = EmailMultiAlternatives(subject, "", f"{company_sender_name} <{from_email}>", [email],connection=smtp_connection)
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()
    logger.info(f"{user_name} : Email has been sent !")
    
@shared_task
def resend_otp_email_async(user_email, otp_code):
    smtp_connection = get_smtp_connection()
    if not smtp_connection:
        print("SMTP connection could not be established!")
        return
    # Define the context for the email template
    context = {
        'otp_code': otp_code,
        'valid_for_minutes': 2,  # Adjust as needed
        'support_email': support_email,
        'company_website': company_website,
        'logo_url': logo_url,
        "company_name":company_name,
    }

    # Render the HTML message from the template
    html_message = render_to_string('resend_email.html', context)
    
    subject = OTP_EMAIL_SUBJECT
    from_email = _get_default_from_email()
    
    try:
        email_message = EmailMultiAlternatives(subject, "", f"{OTP_SENDER_NAME} <{from_email}>", [user_email],connection=smtp_connection)
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Email sending failed: {e}")
@shared_task
def send_login_success_email(username, email, browser, ip_address, login_time):
    smtp_connection = get_smtp_connection()
    if not smtp_connection:
        print("SMTP connection could not be established!")
        return
    subject = f"Login Alert for your {company_name} account!"
    from_email = _get_default_from_email()
    recipient_email = email  # FIXED: Use actual email, not username

    # Email context
    context = {
        'user_name': username,
        'user_email': email,
        'device': browser,
        'time': login_time,
        'ip_address': ip_address,
        'company_name': company_name,
        'company_url':company_website,
        'appstore_icon_url': "https://link-to-appstore-icon.png",
        'contact_number': contact_number,
        'address': "123 Business Street,indore M.P.",
        'logout_link': "https://sparksadmin.algoview.in/logout",
        "logo_url":logo_url
    }

    # Render HTML email
    html_message = render_to_string('login_success_email.html', context)
    print("from_email>>>>>>>",from_email)
    # Send Email
    try:
        email_message = EmailMultiAlternatives(subject, "", f"{company_sender_name} <{from_email}>", [recipient_email],connection=smtp_connection)
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()
        print(f"Login success email sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send login success email: {e}")

@shared_task
def send_password_reset_email(uid, email, username, token):
    smtp_connection = get_smtp_connection()
    if not smtp_connection:
        print("SMTP connection could not be established!")
        return
    reset_link = f'{PASSWORD_RESET_APP_URL}/pages/authentication/reset-password/{uid}/{token}/layout'
    
    subject = "Password Reset Request"
    context = {
        'user_name': username,
        'reset_link': reset_link,
        'company_name': company_name, 
        'company_url': company_website,
        'support_email': PASSWORD_RESET_SUPPORT_EMAIL,
        'logo_url':logo_url
    }
    
    html_message = render_to_string('password_reset_email.html', context)
    from_email = _get_default_from_email()
    try:
        email_message = EmailMultiAlternatives(subject, "", f"{PASSWORD_RESET_SENDER_NAME} <{from_email}>", [email],connection=smtp_connection)
      
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()
        print(f"Password reset email sent to {email}")
    except Exception as e:
        logger.error("Password reset email failed", extra={"error": str(e)})
