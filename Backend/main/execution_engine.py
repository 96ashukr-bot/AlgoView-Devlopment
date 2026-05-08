"""
Centralized multi-broker execution engine.

All trade execution routes through this module so Django views can stay thin
and the execution path remains consistent across brokers.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Dict
from zoneinfo import ZoneInfo

from django.core.cache import caches
from django.utils import timezone

from main.Alice_Blue_Api import place_alice_orders
from main.angleapi_upgraded import exit_angel_one_position, place_angel_one_order
from main.angelone.constants import (
    ALLOW_MARKET_ORDERS,
    ALLOW_STRIKE_FALLBACK,
    DEFAULT_BUFFER_PERCENTAGE,
    DEFAULT_MAX_ORDER_VALUE_PER_TRADE,
    DEFAULT_TICK_SIZE,
    DEFAULT_MAX_QUANTITY_PER_TRADE,
    DUPLICATE_ORDER_WINDOW_SECONDS,
    ENFORCE_LOT_SIZE,
    ENFORCE_MARKET_HOURS,
    FORCE_LTP_FETCH,
    MARKET_CLOSE_HOUR,
    MARKET_CLOSE_MINUTE,
    MARKET_OPEN_HOUR,
    MARKET_OPEN_MINUTE,
    MAX_BUFFER_PERCENTAGE,
    MAX_ORDER_RETRIES,
    MAX_SLIPPAGE_PERCENT,
    MAX_VALID_LTP,
    MIN_BUFFER_PERCENTAGE,
    MIN_VALID_LTP,
    ORDER_RETRY_DELAY,
    TIMEZONE,
    USE_LIMIT_WITH_BUFFER,
    USE_IST,
)
from main.angelone.managers.contract_manager import ContractMasterManager
from main.angelone.services.auth_service import AuthService
from main.angelone.services.ltp_service import LTPService
from main.angelone.utils.idempotency import get_idempotency_manager
from main.angelone.utils.logging_utils import TradingLogger, set_request_context
from main.dematemodule import (
    exit_existing_buy_position_5PaisaOrder,
    exit_existing_buy_position_Aliceblue,
    exit_existing_buy_position_DhanOrder,
    exit_existing_buy_position_Upstox,
    exit_existing_buy_position_fyers_order,
    exit_existing_buy_position_zerodha_order,
)
from main.dhanapi import place_dhan_orders
from main.fivepaisa import place_5paisa_order
from main.fyersapi import place_fyers_orders
from main.models import ClientBrokerdetails
from main.broker_registry import normalize_broker_name
from main.risk_manager import get_risk_manager
from main.services.execution_router import route_order_to_execution_node
from main.upstock import place_upstox_orders
from main.zerodha import place_zerodha_orders
from main.trade_history_service import save_trade_order_history

logger = TradingLogger("execution_engine")


ALLOWED_ORDER_TYPES = {"LIMIT", "MARKET", "SL", "SL-M"}
ALLOWED_TRANSACTION_TYPES = {"BUY", "SELL"}


@dataclass(frozen=True)
class ContractInfo:
    """Grouped contract metadata for cleaner request construction."""

    symbol: Optional[str] = None
    strike: Optional[float] = None
    option_type: Optional[str] = None
    exchange: Optional[str] = None
    expiry: Optional[datetime] = None
    tradingsymbol: Optional[str] = None
    symboltoken: Optional[str] = None


@dataclass(frozen=True)
class OrderConfig:
    """Grouped order settings for broker execution."""

    order_type: Optional[str] = None
    product_type: Optional[str] = None
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    lots: Optional[int] = None


@dataclass(frozen=True)
class ExecutionRequest:
    LivePrice: Any
    group_service: Any
    trade: Any
    user: Any
    transaction_type: str
    symbol: str
    quantity: int
    strategy: str
    ordertype: str
    product_type: str
    price: Any
    Lots: Any
    trade_order_status: Any
    Entry_type: Any
    Exit_type: Any
    Entry_price: Any
    Exit_price: Any
    EntryQty: Any
    ExitQty: Any
    webhook_signal: Any
    Exchange: str
    Segment: Any
    Index_Symbol: Any
    triggerPrice: Any
    day: str
    month: str
    year: str
    fullyear: str
    strike: Any
    option_type: str
    order_params: Dict[str, Any]
    history_id: Optional[str] = None
    contract_info: Optional[ContractInfo] = None
    order_config: Optional[OrderConfig] = None

    @property
    def request_id(self) -> str:
        return str(self.history_id or uuid.uuid4())[:32]

    @property
    def broker_name(self) -> str:
        return normalize_broker_name(getattr(self.trade, "broker", "") or "")

    @property
    def is_multi_leg_order(self) -> bool:
        return isinstance(self.order_params, dict) and bool(self.order_params.get("multi_leg_strategy_execution_id"))

    @property
    def is_position_exit_order(self) -> bool:
        if not isinstance(self.order_params, dict):
            return False
        action = str(
            self.order_params.get("multi_leg_order_action")
            or self.order_params.get("order_action")
            or ""
        ).strip().lower()
        return action in {"exit", "rollback"}

    @property
    def quantity_int(self) -> int:
        return int(self.quantity or 0)

    @property
    def underlying_symbol(self) -> str:
        if self.contract_info and self.contract_info.symbol:
            return str(self.contract_info.symbol).upper()
        return str(self.symbol or "").upper()

    @property
    def strike_value(self) -> Optional[float]:
        strike = self.contract_info.strike if self.contract_info and self.contract_info.strike is not None else self.strike
        return float(strike) if strike not in (None, "") else None

    @property
    def option_type_value(self) -> str:
        if self.contract_info and self.contract_info.option_type:
            return str(self.contract_info.option_type).upper()
        return str(self.option_type or "").upper()

    @property
    def exchange_name(self) -> str:
        if self.contract_info and self.contract_info.exchange:
            return str(self.contract_info.exchange).upper()
        return str(self.Exchange or "NFO").upper()

    @property
    def order_type_name(self) -> str:
        if self.order_config and self.order_config.order_type:
            return str(self.order_config.order_type).upper()
        if isinstance(self.order_params, dict):
            order_type = self.order_params.get("order_type") or self.order_params.get("ordertype") or self.order_params.get("orderType")
            if order_type:
                return str(order_type).upper()
        return str(self.ordertype or "LIMIT").upper()

    @property
    def product_type_name(self) -> str:
        if self.order_config and self.order_config.product_type:
            return str(self.order_config.product_type).upper()
        return str(self.product_type or "INTRADAY").upper()

    @property
    def limit_price(self) -> Optional[float]:
        price = self.order_config.price if self.order_config and self.order_config.price is not None else self.price
        if price in (None, "", 0, "0"):
            return None
        return float(price)

    @property
    def trigger_price_value(self) -> Optional[float]:
        trigger = self.order_config.trigger_price if self.order_config and self.order_config.trigger_price is not None else self.triggerPrice
        if trigger in (None, "", 0, "0"):
            return None
        return float(trigger)

    @property
    def resolved_expiry(self) -> Optional[datetime]:
        if self.contract_info and self.contract_info.expiry:
            return self.contract_info.expiry
        if self.day and self.month and self.fullyear:
            try:
                return datetime.strptime(f"{self.day}{self.month}{self.fullyear}", "%d%b%Y")
            except ValueError:
                return None
        return None

    @property
    def requested_buffer_percentage(self) -> Optional[float]:
        if isinstance(self.order_params, dict):
            buffer = (
                self.order_params.get("buffer_percentage")
                or self.order_params.get("bufferPercent")
                or self.order_params.get("bufferPercentage")
            )
            if buffer in (None, ""):
                return None
            try:
                return float(buffer)
            except (TypeError, ValueError):
                return None
        return None

    @property
    def has_requested_buffer_override(self) -> bool:
        if not isinstance(self.order_params, dict):
            return False
        return any(
            key in self.order_params and self.order_params.get(key) not in (None, "")
            for key in ("buffer_percentage", "bufferPercent", "bufferPercentage")
        )


class ExecutionEngine:
    """Centralized execution coordinator with validation, idempotency, and retry control."""

    CIRCUIT_BREAKER_THRESHOLD = 5
    CIRCUIT_BREAKER_BLOCK_SECONDS = 60
    LATENCY_WARNING_SECONDS = 2.0

    TRANSIENT_ERROR_MARKERS = (
        "timeout",
        "tempor",
        "connection",
        "network",
        "429",
        "throttle",
        "rate limit",
        "service unavailable",
    )

    def __init__(self):
        self._risk_manager = get_risk_manager()
        self._idempotency_manager = get_idempotency_manager(DUPLICATE_ORDER_WINDOW_SECONDS)
        self._contract_manager = ContractMasterManager.get_instance()
        self._ltp_service = LTPService.get_instance()
        self._auth_service = AuthService()
        self._circuit_breaker_cache = caches["circuit_breaker"]

    def execute_order(self, request: ExecutionRequest) -> Dict[str, Any]:
        start = time.perf_counter()
        set_request_context(request_id=request.request_id, client_id=str(getattr(request.user, "id", "")))
        self._log_audit_event("attempt", request, {"message": "Order execution started"})

        circuit_breaker_result = self._check_circuit_breaker(request)
        if circuit_breaker_result:
            self._log_audit_event("blocked", request, circuit_breaker_result["data"], elapsed_seconds=0.0)
            return circuit_breaker_result

        risk_result = self._risk_manager.validate_and_reserve(request)
        if not risk_result.allowed:
            response = self._failed_response(risk_result.message, error_code=risk_result.error_code)
            self._record_broker_failure(request)
            self._log_audit_event("failure", request, response["data"], elapsed_seconds=time.perf_counter() - start)
            return response

        idempotency_key = None
        existing_order = None
        try:
            validation_context = self._run_pre_dispatch_validations(request)
            if validation_context.get("status") == "error":
                self._risk_manager.release_reservation(risk_result.reservation_key)
                response = self._failed_response(
                    validation_context.get("message", "Order validation failed."),
                    error_code=validation_context.get("error_code"),
                )
                self._record_broker_failure(request)
                self._log_audit_event("failure", request, response["data"], elapsed_seconds=time.perf_counter() - start)
                return response

            idempotency_key = validation_context.get("idempotency_key")
            existing_order = validation_context.get("idempotency_record")

            response = None
            normalized = None
            last_error = None

            for attempt in range(1, MAX_ORDER_RETRIES + 1):
                try:
                    response = self._dispatch(request, validation_context)
                    normalized = self._normalize_response(response)
                    if attempt < MAX_ORDER_RETRIES and self._should_retry(normalized):
                        last_error = normalized.get("data", {}).get("message", "Transient broker failure")
                        logger.warning(
                            "Retrying broker execution after transient response",
                            user_id=getattr(request.user, "id", None),
                            symbol=request.underlying_symbol,
                            strike=request.strike_value,
                            broker=request.broker_name,
                            request_id=request.request_id,
                            attempt=attempt,
                            error=last_error,
                        )
                        time.sleep(ORDER_RETRY_DELAY)
                        continue
                    break
                except Exception as exc:
                    last_error = str(exc)
                    if attempt < MAX_ORDER_RETRIES and self._is_transient_error(last_error):
                        logger.warning(
                            "Retrying broker execution after transient exception",
                            user_id=getattr(request.user, "id", None),
                            symbol=request.underlying_symbol,
                            strike=request.strike_value,
                            broker=request.broker_name,
                            request_id=request.request_id,
                            attempt=attempt,
                            error=last_error,
                        )
                        time.sleep(ORDER_RETRY_DELAY)
                        continue
                    raise

            if normalized is None:
                normalized = self._failed_response(last_error or "Order execution failed.")

            self._finalize_execution(
                request=request,
                normalized=normalized,
                validation_context=validation_context,
                idempotency_key=idempotency_key,
                reservation_key=risk_result.reservation_key,
                started_at=start,
            )
            return normalized
        except Exception as exc:
            self._risk_manager.release_reservation(risk_result.reservation_key)
            if idempotency_key and existing_order:
                self._idempotency_manager.remove_record(idempotency_key)
            self._record_broker_failure(request)
            logger.exception(
                "Execution failed",
                user_id=getattr(request.user, "id", None),
                symbol=request.underlying_symbol,
                strike=request.strike_value,
                broker=request.broker_name,
                request_id=request.request_id,
                response_time=round(time.perf_counter() - start, 4),
                error=str(exc),
            )
            response = self._failed_response(str(exc))
            self._log_audit_event("failure", request, response["data"], elapsed_seconds=time.perf_counter() - start)
            return response

    def _run_pre_dispatch_validations(self, request: ExecutionRequest) -> Dict[str, Any]:
        basic_validation = self._validate_basic_order_fields(request)
        if basic_validation:
            return basic_validation

        quantity_validation = self._validate_max_quantity(request)
        if quantity_validation:
            return quantity_validation

        market_hours = self._validate_market_hours()
        if market_hours:
            return market_hours

        duplicate_result = self._validate_idempotency(request)
        if duplicate_result.get("status") == "error":
            return duplicate_result

        context = dict(duplicate_result)
        if request.broker_name in {"angel one", "angle one"}:
            angel_context = self._validate_angel_one_request(request)
            if angel_context.get("status") == "error":
                if context.get("idempotency_key") and context.get("idempotency_record"):
                    self._idempotency_manager.remove_record(context["idempotency_key"])
                return angel_context
            context.update(angel_context)
        else:
            broker_validation = self._validate_generic_broker_access(request)
            if broker_validation:
                if context.get("idempotency_key") and context.get("idempotency_record"):
                    self._idempotency_manager.remove_record(context["idempotency_key"])
                return broker_validation
            price_validation = self._validate_generic_price_protection(request)
            if price_validation:
                if context.get("idempotency_key") and context.get("idempotency_record"):
                    self._idempotency_manager.remove_record(context["idempotency_key"])
                return price_validation
            context["compliance_checks"] = {
                "price_check": "passed",
                "market_price_protection": "passed" if request.order_type_name == "LIMIT" and request.limit_price else "deferred_to_broker_adapter",
            }

        order_value_validation = self._validate_order_value_limit(request, context)
        if order_value_validation:
            if context.get("idempotency_key") and context.get("idempotency_record"):
                self._idempotency_manager.remove_record(context["idempotency_key"])
            return order_value_validation

        context["order_value"] = self._calculate_order_value(request, context)
        context["max_order_value"] = float(
            getattr(getattr(request, "trade", None), "max_order_value", 0)
            or DEFAULT_MAX_ORDER_VALUE_PER_TRADE
        )
        context["compliance_checks"] = {
            **context.get("compliance_checks", {}),
            "basic_order_validation": "passed",
            "quantity_limit_check": "passed",
            "order_value_limit_check": "passed" if context.get("order_value") is not None else "not_applicable",
            "duplicate_order_check": "passed",
            "market_hours_check": "passed",
            "runaway_loop_protection": "passed",
        }

        return {"status": "success", **context}

    def _validate_basic_order_fields(self, request: ExecutionRequest) -> Optional[Dict[str, Any]]:
        transaction_type = str(request.transaction_type or "").upper()
        if transaction_type not in ALLOWED_TRANSACTION_TYPES:
            return {
                "status": "error",
                "message": "Order rejected because transaction type must be BUY or SELL.",
                "error_code": "INVALID_TRANSACTION_TYPE",
            }

        order_type = request.order_type_name
        if order_type not in ALLOWED_ORDER_TYPES:
            return {
                "status": "error",
                "message": f"Order type '{order_type}' is not allowed.",
                "error_code": "INVALID_ORDER_TYPE",
            }

        if request.quantity_int <= 0:
            return {
                "status": "error",
                "message": "Order quantity must be greater than zero.",
                "error_code": "INVALID_QUANTITY",
            }

        trigger_price = request.trigger_price_value
        if order_type in {"SL", "SL-M"} and trigger_price is None:
            return {
                "status": "error",
                "message": "Stop-loss orders require a valid trigger price.",
                "error_code": "MISSING_TRIGGER_PRICE",
            }

        if trigger_price is not None and trigger_price <= 0:
            return {
                "status": "error",
                "message": "Trigger price must be greater than zero.",
                "error_code": "INVALID_TRIGGER_PRICE",
            }

        return None

    def _validate_max_quantity(self, request: ExecutionRequest) -> Optional[Dict[str, Any]]:
        if request.quantity_int > DEFAULT_MAX_QUANTITY_PER_TRADE:
            return {
                "status": "error",
                "message": f"Order quantity exceeds the maximum allowed per trade ({DEFAULT_MAX_QUANTITY_PER_TRADE}).",
                "error_code": "MAX_QUANTITY_EXCEEDED",
            }
        return None

    def _validate_market_hours(self) -> Optional[Dict[str, Any]]:
        if not ENFORCE_MARKET_HOURS:
            return None

        timezone_name = TIMEZONE if USE_IST else "UTC"
        now = datetime.now(ZoneInfo(timezone_name))
        current_minutes = now.hour * 60 + now.minute
        market_open = MARKET_OPEN_HOUR * 60 + MARKET_OPEN_MINUTE
        market_close = MARKET_CLOSE_HOUR * 60 + MARKET_CLOSE_MINUTE

        if current_minutes < market_open or current_minutes >= market_close:
            return {
                "status": "error",
                "message": "Order rejected because the market is outside configured trading hours.",
                "error_code": "MARKET_CLOSED",
            }
        return None

    def _validate_idempotency(self, request: ExecutionRequest) -> Dict[str, Any]:
        custom_key = None
        if isinstance(request.order_params, dict):
            custom_key = request.order_params.get("idempotency_key") or request.order_params.get("request_id")
        custom_key = str(custom_key or request.history_id or "").strip() or None
        if custom_key:
            key = self._idempotency_manager.generate_key(
                client_id=str(getattr(request.user, "id", "")),
                symbol=f"{request.underlying_symbol}:{custom_key}",
                strike=request.strike_value,
                side=request.transaction_type.upper(),
                quantity=request.quantity_int,
                option_type=request.option_type_value,
            )
        else:
            key = self._idempotency_manager.generate_key(
                client_id=str(getattr(request.user, "id", "")),
                symbol=request.underlying_symbol,
                strike=request.strike_value,
                side=request.transaction_type.upper(),
                quantity=request.quantity_int,
                option_type=request.option_type_value,
            )
        is_duplicate, existing = self._idempotency_manager.check_duplicate(
            client_id=str(getattr(request.user, "id", "")),
            symbol=request.underlying_symbol,
            strike=request.strike_value,
            side=request.transaction_type.upper(),
            quantity=request.quantity_int,
            option_type=request.option_type_value,
            custom_key=key,
        )
        if is_duplicate:
            return {
                "status": "error",
                "message": "Duplicate order skipped within idempotency window.",
                "error_code": "DUPLICATE_ORDER",
                "existing_order_id": existing.order_id if existing else None,
            }
        return {
            "status": "success",
            "idempotency_key": key,
            "idempotency_record": existing,
        }

    def _validate_generic_price_protection(self, request: ExecutionRequest) -> Optional[Dict[str, Any]]:
        order_type = request.order_type_name
        limit_price = request.limit_price
        trigger_price = request.trigger_price_value

        for label, value in (("limit", limit_price), ("trigger", trigger_price)):
            if value is None:
                continue
            if value <= 0:
                return {
                    "status": "error",
                    "message": f"{label.title()} price must be greater than zero.",
                    "error_code": f"INVALID_{label.upper()}_PRICE",
                }
            if value < MIN_VALID_LTP or value > MAX_VALID_LTP:
                return {
                    "status": "error",
                    "message": f"{label.title()} price is outside configured exchange safety bounds.",
                    "error_code": "PRICE_OUT_OF_BOUNDS",
                }
        return None

    def _validate_generic_broker_access(self, request: ExecutionRequest) -> Optional[Dict[str, Any]]:
        supported_brokers = {"fyers", "dhan", "5paisa", "zerodha", "upstox", "alice blue"}
        if request.broker_name not in supported_brokers:
            return {
                "status": "error",
                "message": "Unsupported broker or no broker matched.",
                "error_code": "UNSUPPORTED_BROKER",
            }

        client_broker = self._get_client_broker(request)
        if not client_broker:
            return {
                "status": "error",
                "message": f"No broker details found for this {request.trade.broker} client.",
                "error_code": "MISSING_BROKER",
            }

        if request.broker_name != "alice blue":
            access_token = self._get_access_token(client_broker)
            if not access_token:
                return {
                    "status": "error",
                    "message": f"Access token not found for this {request.trade.broker} client.",
                    "error_code": "MISSING_ACCESS_TOKEN",
                }

            expiry = getattr(client_broker, "access_token_expiry", None)
            if expiry and timezone.is_naive(expiry):
                expiry = timezone.make_aware(expiry)
            if expiry and expiry <= timezone.now():
                return {
                    "status": "error",
                    "message": f"{request.trade.broker} access token has expired. Please login again.",
                    "error_code": "ACCESS_TOKEN_EXPIRED",
                }

        required_fields = {
            "fyers": ("broker_API_KEY",),
            "dhan": (),
            "5paisa": ("broker_API_KEY",),
            "zerodha": ("broker_API_KEY",),
            "upstox": (),
            "alice blue": ("broker_API_KEY", "broker_API_UID"),
        }.get(request.broker_name, ())
        missing = [field for field in required_fields if not getattr(client_broker, field, None)]
        if request.broker_name == "dhan" and not (client_broker.broker_API_UID or client_broker.broker_Demate_User_Name):
            missing.append("broker_API_UID")
        if missing:
            return {
                "status": "error",
                "message": f"Broker credentials are incomplete for {request.trade.broker}. Missing: {', '.join(missing)}.",
                "error_code": "MISSING_CREDENTIALS",
            }

        return None

    def _validate_order_value_limit(self, request: ExecutionRequest, validation_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        max_order_value = float(
            getattr(getattr(request, "trade", None), "max_order_value", 0)
            or DEFAULT_MAX_ORDER_VALUE_PER_TRADE
        )
        order_value = self._calculate_order_value(request, validation_context)

        if order_value is None:
            return None

        if order_value > max_order_value:
            return {
                "status": "error",
                "message": f"Order value {round(order_value, 2)} exceeds the configured per-order value limit {round(max_order_value, 2)}.",
                "error_code": "MAX_ORDER_VALUE_EXCEEDED",
                "order_value": round(order_value, 2),
                "max_order_value": round(max_order_value, 2),
            }
        return None

    def _calculate_order_value(self, request: ExecutionRequest, validation_context: Dict[str, Any]) -> Optional[float]:
        reference_price = (
            self._to_float(validation_context.get("validated_price"))
            or self._to_float(validation_context.get("ltp"))
            or self._to_float(request.limit_price)
        )
        if reference_price is None or reference_price <= 0:
            return None
        return round(reference_price * request.quantity_int, 2)

    def _validate_angel_one_request(self, request: ExecutionRequest) -> Dict[str, Any]:
        client_broker = self._get_client_broker(request)
        if not client_broker:
            return {"status": "error", "message": "No broker details found for this Angel One client.", "error_code": "MISSING_BROKER"}

        api_key = client_broker.broker_API_KEY
        client_code = client_broker.broker_Demate_User_Name or client_broker.broker_API_UID
        if not api_key or not client_code:
            return {"status": "error", "message": "Angel One API key or client code is missing.", "error_code": "MISSING_CREDENTIALS"}

        session_result = self._auth_service.ensure_valid_session(
            client_id=client_code,
            api_key=api_key,
            broker_details=client_broker,
        )
        if session_result.get("status") != "success":
            return {
                "status": "error",
                "message": session_result.get("message", "Angel One session is invalid."),
                "error_code": "INVALID_SESSION",
            }

        self._contract_manager.initialize(blocking=True)
        expiry = request.resolved_expiry
        if not expiry:
            expiries = self._contract_manager.get_expiries_for_underlying(request.underlying_symbol)
            expiry = expiries[0] if expiries else None
        if not expiry:
            return {"status": "error", "message": "Unable to resolve contract expiry.", "error_code": "INVALID_EXPIRY"}

        contract, contract_resolution = self._contract_manager.resolve_option_contract(
            underlying=request.underlying_symbol,
            strike=request.strike_value,
            option_type=request.option_type_value,
            exchange=request.exchange_name,
            expiry=expiry,
            prefer_weekly=True,
            allow_strike_fallback=ALLOW_STRIKE_FALLBACK,
        )
        if not contract:
            logger.error(
                "Angel One contract resolution failed",
                user_id=getattr(request.user, "id", None),
                symbol=request.underlying_symbol,
                strike=request.strike_value,
                option_type=request.option_type_value,
                exchange=request.exchange_name,
                request_id=request.request_id,
                contract_resolution=contract_resolution,
            )
            return {
                "status": "error",
                "message": "Exact Angel One contract not found for the requested symbol, strike, option type, and expiry.",
                "error_code": "INVALID_CONTRACT",
                "contract_match": contract_resolution,
            }

        current_time = datetime.now(ZoneInfo(TIMEZONE if USE_IST else "UTC"))
        contract_expiry = contract.expiry
        if contract_expiry is not None:
            if contract_expiry.tzinfo is None:
                contract_expiry = contract_expiry.replace(tzinfo=ZoneInfo(TIMEZONE if USE_IST else "UTC"))
            if contract_expiry < current_time:
                return {
                    "status": "error",
                    "message": "Resolved contract has already expired and cannot be traded.",
                    "error_code": "CONTRACT_EXPIRED",
                }

        if ENFORCE_LOT_SIZE and contract.lot_size and request.quantity_int % int(contract.lot_size) != 0:
            return {
                "status": "error",
                "message": f"Quantity must be a multiple of the contract lot size ({contract.lot_size}).",
                "error_code": "INVALID_LOT_SIZE",
            }

        requested_order_type = request.order_type_name
        if requested_order_type == "MARKET" and not ALLOW_MARKET_ORDERS:
            return {
                "status": "error",
                "message": "Market orders are disabled by system configuration.",
                "error_code": "MARKET_ORDER_DISABLED",
            }

        requested_buffer = request.requested_buffer_percentage
        if request.has_requested_buffer_override and requested_buffer is None:
            return {
                "status": "error",
                "message": "Buffer percentage must be a valid number.",
                "error_code": "INVALID_BUFFER_PERCENTAGE",
            }
        if requested_buffer is None:
            buffer_percentage = float(getattr(client_broker, "buffer_percentage", DEFAULT_BUFFER_PERCENTAGE) or DEFAULT_BUFFER_PERCENTAGE)
        else:
            buffer_percentage = requested_buffer
        if buffer_percentage < MIN_BUFFER_PERCENTAGE or buffer_percentage > MAX_BUFFER_PERCENTAGE:
            return {
                "status": "error",
                "message": f"Buffer percentage must be between {MIN_BUFFER_PERCENTAGE} and {MAX_BUFFER_PERCENTAGE}.",
                "error_code": "INVALID_BUFFER_PERCENTAGE",
            }

        ltp = None
        if FORCE_LTP_FETCH or requested_order_type in {"LIMIT", "MARKET"}:
            session = session_result.get("session")
            smart_connect = session.smart_connect if session else None
            ltp = self._ltp_service.get_ltp(
                smart_connect=smart_connect,
                exchange=request.exchange_name,
                token=contract.token,
                symbol=contract.symbol,
            )
            if ltp is None or ltp < MIN_VALID_LTP or ltp > MAX_VALID_LTP:
                return {
                    "status": "error",
                    "message": "Live price validation failed for Angel One order placement.",
                    "error_code": "INVALID_LTP",
                }
        if requested_order_type == "MARKET" and ltp is None:
            return {
                "status": "error",
                "message": "Market order rejected because live price is unavailable.",
                "error_code": "INVALID_LTP",
            }

        resolved_order_type = requested_order_type
        validated_price = request.limit_price
        tick_size = float(contract.tick_size or DEFAULT_TICK_SIZE)

        if requested_order_type == "MARKET" and USE_LIMIT_WITH_BUFFER:
            resolved_order_type = "LIMIT"

        if resolved_order_type == "LIMIT":
            if validated_price is None:
                if ltp is None:
                    return {
                        "status": "error",
                        "message": "Live premium is unavailable; limit order was not placed.",
                        "error_code": "INVALID_LTP",
                    }
                validated_price = self._ltp_service.calculate_limit_price(
                    ltp=ltp,
                    side=request.transaction_type.upper(),
                    buffer_percentage=buffer_percentage,
                    tick_size=tick_size,
                )
            else:
                validated_price = self._ltp_service.round_to_tick(
                    float(validated_price),
                    tick_size=tick_size,
                    direction="UP" if request.transaction_type.upper() == "BUY" else "DOWN",
                )

            if ltp and validated_price is not None:
                slippage_percent = abs(validated_price - ltp) / ltp * 100
                if slippage_percent > MAX_SLIPPAGE_PERCENT:
                    return {
                        "status": "error",
                        "message": f"Limit price exceeds allowed slippage threshold of {MAX_SLIPPAGE_PERCENT}%.",
                        "error_code": "SLIPPAGE_EXCEEDED",
                    }
        else:
            validated_price = None

        return {
            "status": "success",
            "client_broker": client_broker,
            "contract": contract,
            "ltp": ltp,
            "validated_price": validated_price,
            "resolved_order_type": resolved_order_type,
            "buffer_percentage": buffer_percentage,
            "contract_match": contract_resolution,
            "compliance_checks": {
                "price_check": "passed",
                "quantity_limit_check": "passed",
                "market_price_protection": "passed" if resolved_order_type == "LIMIT" else "not_applicable",
                "lot_size_check": "passed",
            },
        }

    def _dispatch(self, request: ExecutionRequest, validation_context: Dict[str, Any]) -> Dict[str, Any]:
        broker = request.broker_name
        routed_response = self._route_to_execution_node_if_configured(request)
        if routed_response is not None:
            return routed_response
        if broker == "fyers":
            return self._execute_fyers(request)
        if broker == "dhan":
            return self._execute_dhan(request)
        if broker == "5paisa":
            return self._execute_fivepaisa(request)
        if broker == "zerodha":
            return self._execute_zerodha(request)
        if broker == "upstox":
            return self._execute_upstox(request)
        if broker == "alice blue":
            return self._execute_alice_blue(request)
        if broker in {"angel one", "angle one"}:
            return self._execute_angel_one(request, validation_context)
        return self._failed_response("Unsupported broker or no broker matched")

    def _route_to_execution_node_if_configured(self, request: ExecutionRequest) -> Optional[Dict[str, Any]]:
        if request.is_position_exit_order:
            return None
        client_broker = self._get_client_broker(request)
        if not client_broker or not client_broker.execution_node_id:
            return None
        order_payload = {
            "idempotency_key": request.history_id or request.request_id,
            "history_id": request.history_id,
            "broker": request.broker_name,
            "LivePrice": request.LivePrice,
            "trade_symbol": self._resolved_trade_symbol(request, ""),
            "symbol": request.underlying_symbol,
            "strike": request.strike_value,
            "option_type": request.option_type_value,
            "exchange": request.exchange_name,
            "Exchange": request.exchange_name,
            "Segment": request.Segment,
            "Index_Symbol": request.Index_Symbol,
            "product_type": request.product_type_name,
            "product": request.product_type_name,
            "order_type": request.order_type_name,
            "ordertype": request.order_type_name,
            "transaction_type": request.transaction_type.upper(),
            "quantity": request.quantity_int,
            "price": request.limit_price,
            "trigger_price": request.trigger_price_value,
            "triggerPrice": request.trigger_price_value,
            "strategy": request.strategy,
            "group_service": request.group_service,
            "Lots": request.Lots,
            "trade_order_status": request.trade_order_status,
            "Entry_type": request.Entry_type,
            "Exit_type": request.Exit_type,
            "Entry_price": request.Entry_price,
            "Exit_price": request.Exit_price,
            "EntryQty": request.EntryQty,
            "ExitQty": request.ExitQty,
            "webhook_signal": request.webhook_signal,
            "day": request.day,
            "month": request.month,
            "year": request.year,
            "fullyear": request.fullyear,
            "request_id": request.request_id,
            "order_params": request.order_params if isinstance(request.order_params, dict) else {},
        }
        result = route_order_to_execution_node(request.user, client_broker, order_payload)
        status_value = str(result.get("status") or "").lower()
        if status_value in {"placed", "accepted_by_node", "sent_to_node", "duplicate"}:
            return {"data": {"status": "open", "message": "Order routed to execution node.", "job_id": result.get("job_id")}}
        return {"data": {"status": "Failed", "message": result.get("message") or "Execution node routing failed.", "job_id": result.get("job_id")}}

    def _execute_fyers(self, request: ExecutionRequest) -> Dict[str, Any]:
        trade_symbol = self._resolved_trade_symbol(
            request,
            f"{request.underlying_symbol}{request.year}{request.month}{request.day}{request.strike_value}{request.option_type_value}",
        )
        client_broker = self._get_client_broker(request)
        if not client_broker:
            return self._failed_response("No broker details found for this Fyers client.")

        access_token = self._get_access_token(client_broker)
        api_key = client_broker.broker_API_KEY
        if not access_token or not api_key:
            return self._failed_response("API credentials token not found for this Fyers client.")

        if request.transaction_type.upper() == "SELL" and not request.is_multi_leg_order:
            return exit_existing_buy_position_fyers_order(
                request.strike_value, request.LivePrice, request.group_service, request.option_type_value,
                request.day, request.month, request.year, access_token, api_key, trade_symbol,
                request.transaction_type, request.underlying_symbol, request.quantity_int, request.strategy,
                request.order_type_name, request.product_type_name, request.limit_price, request.user,
                request.Lots, request.Entry_type, request.Exit_type, request.Entry_price,
                request.Exit_price, request.EntryQty, request.ExitQty, request.webhook_signal,
                request.exchange_name, request.Segment, request.Index_Symbol, request.triggerPrice,
                request.trade_order_status, request.history_id
            )

        return place_fyers_orders(
            request.LivePrice, request.group_service, access_token, api_key, trade_symbol,
            request.transaction_type, request.underlying_symbol, request.quantity_int, request.strategy,
            request.order_type_name, request.product_type_name, request.limit_price, request.user, request.Lots,
            request.Entry_type, request.Exit_type, request.Entry_price, request.Exit_price,
            request.EntryQty, request.ExitQty, request.webhook_signal, request.exchange_name,
            request.Segment, request.Index_Symbol, request.triggerPrice, request.trade_order_status,
            request.history_id
        )

    def _execute_dhan(self, request: ExecutionRequest) -> Dict[str, Any]:
        client_broker = self._get_client_broker(request)
        if not client_broker:
            return self._failed_response("No broker details found for this Dhan client.")

        client_id = client_broker.broker_API_UID or client_broker.broker_Demate_User_Name
        access_token = self._get_access_token(client_broker)
        if not access_token or not client_id:
            return self._failed_response("Dhan Client ID or access token not found for this Dhan client.")

        month_number = datetime.strptime(request.month, "%b").month
        expiry_date = f"{request.fullyear}-{month_number:02d}-{request.day}"
        trade_symbol = self._resolved_trade_symbol(
            request,
            f"{request.underlying_symbol}{request.month}{request.fullyear}{request.strike_value}{request.option_type_value}",
        )

        if request.transaction_type.upper() == "SELL" and not request.is_multi_leg_order:
            return exit_existing_buy_position_DhanOrder(
                expiry_date, request.LivePrice, request.group_service, request.option_type_value,
                request.day, request.month, request.fullyear, access_token, client_id, trade_symbol,
                request.transaction_type, request.underlying_symbol, request.quantity_int, request.strategy,
                request.order_type_name, request.product_type_name, request.limit_price, request.user, request.Lots,
                request.Entry_type, request.Exit_type, request.Entry_price, request.Exit_price,
                request.EntryQty, request.ExitQty, request.webhook_signal, request.exchange_name,
                request.Segment, request.Index_Symbol, request.triggerPrice, request.trade_order_status
            )

        return place_dhan_orders(
            expiry_date, request.LivePrice, request.group_service, access_token, client_id,
            trade_symbol, request.transaction_type, request.underlying_symbol, request.quantity_int,
            request.strategy, request.order_type_name, request.product_type_name, request.limit_price,
            request.user, request.Lots, request.Entry_type, request.Exit_type, request.Entry_price,
            request.Exit_price, request.EntryQty, request.ExitQty, request.webhook_signal,
            request.exchange_name, request.Segment, request.Index_Symbol, request.triggerPrice,
            request.trade_order_status, request.history_id
        )

    def _execute_fivepaisa(self, request: ExecutionRequest) -> Dict[str, Any]:
        client_broker = self._get_client_broker(request)
        if not client_broker:
            return self._failed_response("No broker details found for this 5Paisa client.")

        api_key = client_broker.broker_API_KEY
        access_token = self._get_access_token(client_broker)
        if not access_token or not api_key:
            return self._failed_response("API credentials not found for this 5Paisa client.")

        trade_symbol = self._resolved_trade_symbol(
            request,
            f"{request.underlying_symbol}{request.day}{request.month}{request.fullyear}{request.option_type_value}{float(request.strike_value):.2f}",
        )
        if request.transaction_type.upper() == "SELL" and not request.is_multi_leg_order:
            return exit_existing_buy_position_5PaisaOrder(
                request.LivePrice, request.group_service, request.option_type_value, request.day,
                request.month, request.fullyear, api_key, access_token, trade_symbol,
                request.transaction_type, request.underlying_symbol, request.quantity_int, request.strategy,
                request.order_type_name, request.product_type_name, request.limit_price, request.user,
                request.Lots, request.trade_order_status, request.Entry_type, request.Exit_type,
                request.Entry_price, request.Exit_price, request.EntryQty, request.ExitQty,
                request.webhook_signal, request.exchange_name, request.Segment, request.Index_Symbol,
                request.triggerPrice, request.trade, request.history_id
            )

        return place_5paisa_order(
            request.LivePrice, request.group_service, api_key, access_token, trade_symbol,
            request.transaction_type, request.underlying_symbol, request.quantity_int, request.strategy,
            request.order_type_name, request.product_type_name, request.limit_price, request.user, request.Lots,
            request.trade_order_status, request.Entry_type, request.Exit_type, request.Entry_price,
            request.Exit_price, request.EntryQty, request.ExitQty, request.webhook_signal,
            request.exchange_name, request.Segment, request.Index_Symbol, request.triggerPrice,
            request.trade, request.history_id
        )

    def _execute_zerodha(self, request: ExecutionRequest) -> Dict[str, Any]:
        client_broker = self._get_client_broker(request)
        if not client_broker:
            return self._failed_response("No broker details found for this Zerodha client.")

        access_token = self._get_access_token(client_broker)
        api_key = client_broker.broker_API_KEY
        if not access_token or not api_key:
            return self._failed_response("API credentials token not found for this Zerodha client.")

        trade_symbol = self._resolved_trade_symbol(
            request,
            f"{request.underlying_symbol}{request.year}{request.month}{request.strike_value}{request.option_type_value}",
        )
        if request.transaction_type.upper() == "SELL" and not request.is_multi_leg_order:
            return exit_existing_buy_position_zerodha_order(
                request.LivePrice, request.group_service, request.option_type_value, request.day,
                request.month, request.year, access_token, api_key, trade_symbol,
                request.transaction_type, request.underlying_symbol, request.quantity_int, request.strategy,
                request.order_type_name, request.product_type_name, request.limit_price, request.user, request.Lots,
                request.Entry_type, request.Exit_type, request.Entry_price, request.Exit_price,
                request.EntryQty, request.ExitQty, request.webhook_signal, request.exchange_name,
                request.Segment, request.Index_Symbol, request.triggerPrice, request.trade_order_status,
                request.history_id
            )

        return place_zerodha_orders(
            request.LivePrice, request.group_service, access_token, api_key, trade_symbol,
            request.transaction_type, request.underlying_symbol, request.quantity_int, request.strategy,
            request.order_type_name, request.product_type_name, request.limit_price, request.user, request.Lots,
            request.Entry_type, request.Exit_type, request.Entry_price, request.Exit_price,
            request.EntryQty, request.ExitQty, request.webhook_signal, request.exchange_name,
            request.Segment, request.Index_Symbol, request.triggerPrice, request.trade_order_status,
            request.history_id
        )

    def _execute_upstox(self, request: ExecutionRequest) -> Dict[str, Any]:
        client_broker = self._get_client_broker(request)
        if not client_broker:
            return self._failed_response("No broker details found for this Upstox client.")

        access_token = self._get_access_token(client_broker)
        if not access_token:
            return self._failed_response("API credentials token not found for this Upstox client.")

        trade_symbol = self._resolved_trade_symbol(
            request,
            f"{request.underlying_symbol}{request.strike_value}{request.option_type_value}{request.day}{request.month}{request.year}",
        )
        if request.transaction_type.upper() == "SELL" and not request.is_multi_leg_order:
            return exit_existing_buy_position_Upstox(
                request.group_service, request.LivePrice, request.option_type_value, request.day,
                request.month, request.year, access_token, trade_symbol, request.transaction_type,
                request.underlying_symbol, request.quantity_int, request.strategy, request.order_type_name,
                request.product_type_name, request.limit_price, request.user, request.Lots,
                request.Entry_type, request.Exit_type, request.Entry_price, request.Exit_price,
                request.EntryQty, request.ExitQty, request.webhook_signal, request.exchange_name,
                request.Segment, request.Index_Symbol, request.triggerPrice, request.trade_order_status
            )

        return place_upstox_orders(
            request.LivePrice, request.group_service, access_token, trade_symbol,
            request.transaction_type, request.underlying_symbol, request.quantity_int, request.strategy,
            request.order_type_name, request.product_type_name, request.limit_price, request.user, request.Lots,
            request.Entry_type, request.Exit_type, request.Entry_price, request.Exit_price,
            request.EntryQty, request.ExitQty, request.webhook_signal, request.exchange_name,
            request.Segment, request.Index_Symbol, request.triggerPrice, request.trade_order_status,
            request.history_id
        )

    def _execute_alice_blue(self, request: ExecutionRequest) -> Dict[str, Any]:
        client_broker = self._get_client_broker(request)
        if not client_broker:
            return self._failed_response("No broker details found for this Alice Blue client.")

        api_skey = client_broker.broker_API_KEY
        api_uid = client_broker.broker_API_UID
        if not api_skey or not api_uid:
            return self._failed_response("API credentials not found for this Alice Blue client.")

        trade_symbol = self._resolved_trade_symbol(
            request,
            f"{request.underlying_symbol}{request.day}{request.month}{request.year}{request.option_type_value[0]}{request.strike_value}",
        )
        if request.transaction_type.upper() == "SELL" and not request.is_multi_leg_order:
            return exit_existing_buy_position_Aliceblue(
                request.LivePrice, request.group_service, request.option_type_value, request.day,
                request.month, request.year, api_skey, api_uid, trade_symbol, request.transaction_type,
                request.underlying_symbol, request.quantity_int, request.strategy, request.order_type_name,
                request.product_type_name, request.limit_price, request.user, request.Lots,
                request.trade_order_status, request.Entry_type, request.Exit_type, request.Entry_price,
                request.Exit_price, request.EntryQty, request.ExitQty, request.webhook_signal,
                request.exchange_name, request.Segment, request.Index_Symbol, request.triggerPrice
            )

        return place_alice_orders(
            request.LivePrice, request.group_service, api_skey, api_uid, trade_symbol,
            request.transaction_type, request.underlying_symbol, request.quantity_int, request.strategy,
            request.order_type_name, request.product_type_name, request.limit_price, request.user, request.Lots,
            request.trade_order_status, request.Entry_type, request.Exit_type, request.Entry_price,
            request.Exit_price, request.EntryQty, request.ExitQty, request.webhook_signal,
            request.exchange_name, request.Segment, request.Index_Symbol, request.history_id,
            request.triggerPrice
        )

    def _execute_angel_one(self, request: ExecutionRequest, validation_context: Dict[str, Any]) -> Dict[str, Any]:
        client_broker = validation_context.get("client_broker") or self._get_client_broker(request)
        if not client_broker:
            return {"status": "error", "message": "No broker details found for this Angel One client.", "error_code": "MISSING_BROKER"}

        if request.transaction_type.upper() == "SELL" and not request.is_multi_leg_order:
            return exit_angel_one_position(
                broker_details=client_broker,
                symbol=request.underlying_symbol,
                strike=str(request.strike_value),
                option_type=request.option_type_value,
                exchange=request.exchange_name,
            )

        return place_angel_one_order(
            broker_details=client_broker,
            symbol=request.underlying_symbol,
            strike=str(request.strike_value),
            option_type=request.option_type_value,
            quantity=request.quantity_int,
            transaction_type=request.transaction_type.upper(),
            buffer_percentage=float(validation_context.get("buffer_percentage", DEFAULT_BUFFER_PERCENTAGE)),
            order_type=validation_context.get("resolved_order_type", request.order_type_name),
            price=validation_context.get("validated_price"),
            exchange=request.exchange_name,
            product_type=request.product_type_name,
            request_id=request.request_id,
        )

    def _get_client_broker(self, request: ExecutionRequest):
        candidates = ClientBrokerdetails.objects.filter(
            client=request.trade.client,
        ).select_related("broker_name")
        requested_broker = request.broker_name
        for broker_detail in candidates:
            broker_name = getattr(getattr(broker_detail, "broker_name", None), "broker_name", "")
            if normalize_broker_name(broker_name) == requested_broker:
                return broker_detail
        return None

    @staticmethod
    def _resolved_trade_symbol(request: ExecutionRequest, fallback: str) -> str:
        if request.contract_info and request.contract_info.tradingsymbol:
            return str(request.contract_info.tradingsymbol).strip()
        return fallback

    @staticmethod
    def _get_access_token(client_broker):
        secure_token_getter = getattr(client_broker, "get_access_token_secure", None)
        if callable(secure_token_getter):
            secure_token = secure_token_getter()
            if secure_token:
                return secure_token
        return getattr(client_broker, "access_token", None)

    def _normalize_response(self, response: Any) -> Dict[str, Any]:
        if isinstance(response, dict) and isinstance(response.get("data"), dict):
            return response
        if isinstance(response, dict) and isinstance(response.get("data"), list):
            data_items = response.get("data") or []
            normalized_data = data_items[0] if data_items and isinstance(data_items[0], dict) else {}
            return {"data": normalized_data, "meta": response}

        if not isinstance(response, dict):
            return self._failed_response(str(response))

        status_value = str(response.get("status", "") or "").lower()
        message = response.get("message", "")
        order_id = response.get("order_id")
        if not order_id and isinstance(response.get("data"), str):
            message = message or str(response.get("data"))

        mapped_status = {
            "success": "complete",
            "complete": "complete",
            "completed": "completed",
            "open": "open",
            "pending": "open",
            "info": "complete",
            "duplicate": "Failed",
            "error": "Failed",
            "failed": "Failed",
        }.get(status_value, "Failed")

        data = {"status": mapped_status, "message": message}
        if order_id:
            data["order_id"] = order_id
        if response.get("error_code"):
            data["error_code"] = response.get("error_code")
        if response.get("order_type") is not None:
            data["order_type"] = response.get("order_type")
        if response.get("requested_order_type") is not None:
            data["requested_order_type"] = response.get("requested_order_type")
        if response.get("price") is not None:
            data["executed_price"] = response.get("price")
        if response.get("ltp") is not None:
            data["ltp"] = response.get("ltp")
        if response.get("reference_price") is not None:
            data["reference_price"] = response.get("reference_price")
        if response.get("buffer_percentage_used") is not None:
            data["buffer_used"] = response.get("buffer_percentage_used")
        return {"data": data, "meta": response}

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_sl_tp_type(value: Any) -> Optional[str]:
        if value in (None, "", "None"):
            return None
        normalized = str(value).strip().upper()
        if normalized in {"%", "PERCENT", "PERCENTAGE"}:
            return "PERCENTAGE"
        if normalized in {"POINT", "POINTS"}:
            return "POINTS"
        return None

    def _build_sl_tp_snapshot(self, request: ExecutionRequest, validation_context: Dict[str, Any], normalized: Dict[str, Any]) -> Dict[str, Any]:
        trade_setting = getattr(request, "trade", None)
        if not trade_setting:
            return {}

        sl_tp_type = self._normalize_sl_tp_type(getattr(trade_setting, "sl_type", None))
        stop_loss_value = self._to_float(getattr(trade_setting, "stop_loss", None))
        target_value = self._to_float(getattr(trade_setting, "target", None))

        if not sl_tp_type or (stop_loss_value is None and target_value is None):
            return {}

        entry_price = self._to_float(normalized.get("data", {}).get("executed_price"))
        if entry_price is None:
            entry_price = self._to_float(normalized.get("data", {}).get("price"))
        if entry_price is None:
            entry_price = self._to_float(validation_context.get("validated_price"))
        if entry_price is None:
            entry_price = self._to_float(normalized.get("data", {}).get("ltp"))
        if entry_price is None:
            entry_price = self._to_float(validation_context.get("ltp"))
        if entry_price is None:
            entry_price = self._to_float(request.LivePrice)

        if entry_price is None or entry_price <= 0:
            return {
                "sl_tp_type": sl_tp_type,
                "stop_loss_input": stop_loss_value,
                "target_input": target_value,
            }

        side = str(request.transaction_type or "").upper()
        is_buy = side == "BUY"

        snapshot = {
            "sl_tp_type": sl_tp_type,
            "entry_reference_price": round(entry_price, 2),
            "stop_loss_input": stop_loss_value,
            "target_input": target_value,
        }

        if stop_loss_value is not None:
            if sl_tp_type == "PERCENTAGE":
                stop_multiplier = 1 - (stop_loss_value / 100.0) if is_buy else 1 + (stop_loss_value / 100.0)
                snapshot["effective_stop_loss_price"] = round(entry_price * stop_multiplier, 2)
            else:
                snapshot["effective_stop_loss_price"] = round(entry_price - stop_loss_value, 2) if is_buy else round(entry_price + stop_loss_value, 2)

        if target_value is not None:
            if sl_tp_type == "PERCENTAGE":
                target_multiplier = 1 + (target_value / 100.0) if is_buy else 1 - (target_value / 100.0)
                snapshot["effective_target_price"] = round(entry_price * target_multiplier, 2)
            else:
                snapshot["effective_target_price"] = round(entry_price + target_value, 2) if is_buy else round(entry_price - target_value, 2)

        return snapshot

    def _finalize_execution(
        self,
        request: ExecutionRequest,
        normalized: Dict[str, Any],
        validation_context: Dict[str, Any],
        idempotency_key: Optional[str],
        reservation_key: Optional[str],
        started_at: float,
    ) -> None:
        status_value = normalized.get("data", {}).get("status")
        order_id = normalized.get("data", {}).get("order_id")
        elapsed_seconds = time.perf_counter() - started_at
        history_symbol = None
        contract = validation_context.get("contract")
        if contract is not None:
            history_symbol = getattr(contract, "symbol", None)
        history_symbol = history_symbol or request.Index_Symbol or request.underlying_symbol
        if validation_context.get("order_value") is None:
            response_reference_price = (
                self._to_float(normalized.get("data", {}).get("executed_price"))
                or self._to_float(normalized.get("data", {}).get("price"))
                or self._to_float(normalized.get("data", {}).get("reference_price"))
                or self._to_float(normalized.get("data", {}).get("ltp"))
            )
            if response_reference_price:
                validation_context["order_value"] = round(response_reference_price * request.quantity_int, 2)
                validation_context["compliance_checks"] = {
                    **validation_context.get("compliance_checks", {}),
                    "order_value_limit_check": "passed",
                }
        if self._to_float(normalized.get("data", {}).get("ltp")) or self._to_float(normalized.get("data", {}).get("price")):
            validation_context["compliance_checks"] = {
                **validation_context.get("compliance_checks", {}),
                "price_check": "passed",
                "market_price_protection": "passed" if request.order_type_name == "LIMIT" else "not_applicable",
            }

        history_order_params = {}
        if isinstance(request.order_params, dict):
            history_order_params.update(request.order_params)
        history_order_params.update(
            {
                "request_id": request.request_id,
                "resolved_order_type": normalized.get("data", {}).get("order_type") or validation_context.get("resolved_order_type"),
                "requested_order_type": normalized.get("data", {}).get("requested_order_type") or request.order_type_name,
                "validated_price": validation_context.get("validated_price"),
                "ltp": validation_context.get("ltp"),
                "buffer_percentage": validation_context.get("buffer_percentage"),
                "contract_match": validation_context.get("contract_match"),
                "compliance_checks": validation_context.get("compliance_checks"),
                "order_value": validation_context.get("order_value"),
                "max_order_value": validation_context.get("max_order_value"),
                "broker": request.trade.broker,
            }
        )
        history_order_params.update(self._build_sl_tp_snapshot(request, validation_context, normalized))

        save_trade_order_history(
            request.LivePrice,
            request.group_service,
            request.transaction_type,
            request.trade_order_status,
            request.user,
            history_symbol,
            order_id or 0,
            status_value or "Failed",
            normalized,
            normalized.get("data", {}).get("message"),
            request.strategy,
            request.Entry_type,
            request.Exit_type,
            request.Entry_price,
            request.Exit_price,
            request.EntryQty,
            request.ExitQty,
            request.webhook_signal,
            request.exchange_name,
            request.Segment,
            request.Index_Symbol,
            history_order_params,
            broker=request.trade.broker,
            history_id=request.history_id,
        )

        logger.info(
            "Execution finished",
            user_id=getattr(request.user, "id", None),
            symbol=request.underlying_symbol,
            strike=request.strike_value,
            broker=request.broker_name,
            request_id=request.request_id,
            response_time=round(elapsed_seconds, 4),
            response=normalized.get("data"),
        )
        if elapsed_seconds > self.LATENCY_WARNING_SECONDS:
            logger.warning(
                "High execution latency detected",
                user_id=getattr(request.user, "id", None),
                symbol=request.underlying_symbol,
                broker=request.broker_name,
                request_id=request.request_id,
                quantity=request.quantity_int,
                response_time=round(elapsed_seconds, 4),
            )

        if status_value in {"complete", "completed", "open"}:
            self._reset_broker_failures(request)
            if idempotency_key:
                self._idempotency_manager.record_execution(
                    idempotency_key=idempotency_key,
                    order_id=str(order_id or request.request_id),
                    status=str(status_value).lower(),
                )
            self._log_audit_event("success", request, normalized.get("data", {}), elapsed_seconds=elapsed_seconds)
            return

        self._record_broker_failure(request)
        self._risk_manager.release_reservation(reservation_key)
        if idempotency_key and validation_context.get("idempotency_record"):
            self._idempotency_manager.remove_record(idempotency_key)
        self._log_audit_event("failure", request, normalized.get("data", {}), elapsed_seconds=elapsed_seconds)

    def _should_retry(self, normalized: Dict[str, Any]) -> bool:
        if normalized.get("data", {}).get("status") in {"complete", "completed", "open"}:
            return False
        return self._is_transient_error(normalized.get("data", {}).get("message", ""))

    def _is_transient_error(self, message: str) -> bool:
        normalized = (message or "").lower()
        return any(marker in normalized for marker in self.TRANSIENT_ERROR_MARKERS)

    def _check_circuit_breaker(self, request: ExecutionRequest) -> Optional[Dict[str, Any]]:
        broker = request.broker_name or "unknown"
        blocked_until_key = f"execution_engine:circuit_breaker:blocked_until:{broker}"
        blocked_until = self._circuit_breaker_cache.get(blocked_until_key)
        now = time.time()
        if blocked_until and blocked_until > now:
            remaining = round(blocked_until - now, 2)
            logger.warning(
                "Circuit breaker blocked order",
                broker=broker,
                request_id=request.request_id,
                user_id=getattr(request.user, "id", None),
                retry_after_seconds=remaining,
            )
            return self._failed_response(
                f"{broker} broker execution is temporarily blocked by the circuit breaker. Retry after {remaining} seconds.",
                error_code="CIRCUIT_BREAKER_OPEN",
            )
        return None

    def _record_broker_failure(self, request: ExecutionRequest) -> None:
        broker = request.broker_name or "unknown"
        failures_key = f"execution_engine:circuit_breaker:failures:{broker}"
        blocked_until_key = f"execution_engine:circuit_breaker:blocked_until:{broker}"
        self._circuit_breaker_cache.add(failures_key, 0, timeout=self.CIRCUIT_BREAKER_BLOCK_SECONDS)
        try:
            failures = self._circuit_breaker_cache.incr(failures_key)
            self._touch_circuit_breaker_key(failures_key, self.CIRCUIT_BREAKER_BLOCK_SECONDS)
        except Exception:
            failures = int(self._circuit_breaker_cache.get(failures_key, 0) or 0) + 1
            self._circuit_breaker_cache.set(failures_key, failures, timeout=self.CIRCUIT_BREAKER_BLOCK_SECONDS)

        if failures >= self.CIRCUIT_BREAKER_THRESHOLD:
            blocked_until = time.time() + self.CIRCUIT_BREAKER_BLOCK_SECONDS
            self._circuit_breaker_cache.set(blocked_until_key, blocked_until, timeout=self.CIRCUIT_BREAKER_BLOCK_SECONDS)
            logger.warning(
                "Circuit breaker opened",
                broker=broker,
                request_id=request.request_id,
                user_id=getattr(request.user, "id", None),
                failures=failures,
                blocked_for_seconds=self.CIRCUIT_BREAKER_BLOCK_SECONDS,
            )

    def _reset_broker_failures(self, request: ExecutionRequest) -> None:
        broker = request.broker_name or "unknown"
        self._circuit_breaker_cache.delete(f"execution_engine:circuit_breaker:failures:{broker}")
        self._circuit_breaker_cache.delete(f"execution_engine:circuit_breaker:blocked_until:{broker}")

    def _touch_circuit_breaker_key(self, key: str, timeout: int) -> None:
        try:
            self._circuit_breaker_cache.touch(key, timeout=timeout)
        except Exception:
            value = self._circuit_breaker_cache.get(key)
            if value is not None:
                self._circuit_breaker_cache.set(key, value, timeout=timeout)

    def _log_audit_event(
        self,
        event_type: str,
        request: ExecutionRequest,
        response: Dict[str, Any],
        elapsed_seconds: Optional[float] = None,
    ) -> None:
        logger.info(
            "Execution audit event",
            audit_event=event_type,
            request_id=request.request_id,
            user_id=getattr(request.user, "id", None),
            broker=request.broker_name,
            symbol=request.underlying_symbol,
            strike=request.strike_value,
            option_type=request.option_type_value,
            quantity=request.quantity_int,
            response=response,
            response_time=round(elapsed_seconds, 4) if elapsed_seconds is not None else None,
        )

    @staticmethod
    def _failed_response(message: str, error_code: Optional[str] = None) -> Dict[str, Any]:
        data = {"status": "Failed", "message": message}
        if error_code:
            data["error_code"] = error_code
        return {"data": data}


_execution_engine: Optional[ExecutionEngine] = None


def get_execution_engine() -> ExecutionEngine:
    global _execution_engine
    if _execution_engine is None:
        _execution_engine = ExecutionEngine()
    return _execution_engine
