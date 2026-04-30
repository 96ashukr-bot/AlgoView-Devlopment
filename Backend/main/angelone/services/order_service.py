"""
Order Service
=============
Main order execution service with all integrations.

Features:
- Sync and async order placement
- Symbol parsing and resolution
- Expiry handling
- Duplicate protection
- Position tracking
- LTP-based limit orders
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..utils.logging_utils import TradingLogger, set_request_context
from ..utils.symbol_parser import SymbolParser, get_symbol_parser
from ..utils.expiry_handler import ExpiryHandler, get_expiry_handler
from ..utils.idempotency import IdempotencyManager, get_idempotency_manager
from ..managers.session_manager import SessionManager
from ..managers.contract_manager import ContractMasterManager
from ..managers.position_manager import PositionManager, PositionSide
from .ltp_service import LTPService
from .auth_service import AuthService
from ..constants import (
    Exchange, ProductType, OrderType, TransactionType,
    Variety, Duration, DEFAULT_BUFFER_PERCENTAGE,
    MIN_BUFFER_PERCENTAGE, MAX_BUFFER_PERCENTAGE, DEFAULT_TICK_SIZE,
    ALLOW_MARKET_ORDERS, ALLOW_STRIKE_FALLBACK, ENFORCE_LOT_SIZE,
    FORCE_LTP_FETCH, MAX_SLIPPAGE_PERCENT, MIN_VALID_LTP, MAX_VALID_LTP,
    USE_LIMIT_WITH_BUFFER,
)

logger = TradingLogger("order_service")


class OrderService:
    """
    Main order service for Angel One trading.
    
    Usage:
        service = OrderService()
        
        # Place order
        result = service.place_order(
            client_id="C123",
            api_key="key",
            symbol="NIFTY05MAY2622700CE",
            side="BUY",
            quantity=50
        )
        
        # Place async order
        task = service.place_order_async(...)
    """
    
    def __init__(self):
        self._session_manager = SessionManager.get_instance()
        self._auth_service = AuthService()
        self._contract_manager = ContractMasterManager.get_instance()
        self._position_manager = PositionManager.get_instance()
        self._ltp_service = LTPService.get_instance()
        self._symbol_parser = get_symbol_parser()
        self._expiry_handler = get_expiry_handler()
        self._idempotency_manager = get_idempotency_manager()

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
    
    def place_order(
        self,
        client_id: str,
        api_key: str,
        symbol: str,
        side: str,
        quantity: int,
        product_type: str = "INTRADAY",
        order_type: str = "LIMIT",
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        expiry_override: Optional[datetime] = None,
        buffer_percentage: float = DEFAULT_BUFFER_PERCENTAGE,
        exchange: str = "NFO",
        variety: str = "NORMAL",
        duration: str = "DAY",
        underlying: Optional[str] = None,
        strike: Optional[float] = None,
        option_type: Optional[str] = None,
        allow_strike_fallback: bool = ALLOW_STRIKE_FALLBACK,
        check_duplicate: bool = True,
        check_position: bool = True,
        request_id: Optional[str] = None,
        broker_details=None,
    ) -> Dict[str, Any]:
        """
        Place an order synchronously.
        
        Args:
            client_id: Client ID
            api_key: API key
            symbol: Trading symbol (any supported format)
            side: BUY or SELL
            quantity: Order quantity
            product_type: INTRADAY, DELIVERY, etc.
            order_type: LIMIT or MARKET
            price: Limit price (auto-calculated if not provided)
            trigger_price: Trigger price for SL orders
            expiry_override: Override expiry date
            buffer_percentage: LTP buffer for limit price
            exchange: Exchange (NFO, NSE, etc.)
            variety: Order variety
            duration: Order duration
            check_duplicate: Check for duplicate orders
            check_position: Check existing positions
            request_id: Request tracking ID
            
        Returns:
            Order result dict
        """
        request_id = request_id or str(uuid.uuid4())[:8]
        set_request_context(request_id=request_id, client_id=client_id)

        logger.info(
            "Place order request",
            user_id=client_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
        )

        existing = None

        try:
            self._contract_manager.initialize(blocking=True)
            if not symbol:
                return self._error_response("Symbol is required.", request_id, error_code="INVALID_INPUT")
            if side.upper() not in {TransactionType.BUY.value, TransactionType.SELL.value}:
                return self._error_response("Transaction type must be BUY or SELL.", request_id, error_code="INVALID_INPUT")
            if int(quantity) <= 0:
                return self._error_response("Quantity must be greater than zero.", request_id, error_code="INVALID_INPUT")

            session_result = self._auth_service.ensure_valid_session(
                client_id=client_id,
                api_key=api_key,
                broker_details=broker_details,
            )
            if session_result.get("status") != "success":
                return self._error_response(session_result.get("message", "Invalid or expired session"), request_id)

            session = session_result.get("session")
            smart_connect = session.smart_connect

            parsed = None
            if underlying and option_type and strike is not None:
                underlying_symbol = str(underlying).upper()
                strike_value = self._contract_manager._normalize_strike(strike)
                option_type_value = str(option_type).upper()
                is_option = True
                parsed_expiry_date = expiry_override
                parsed_expiry_str = None
            else:
                parsed = self._symbol_parser.parse(symbol)
                underlying_symbol = parsed.underlying
                strike_value = parsed.strike
                option_type_value = parsed.option_type
                is_option = parsed.is_option
                parsed_expiry_date = parsed.expiry_date
                parsed_expiry_str = parsed.expiry_str

            self._expiry_handler.set_available_expiries(
                underlying_symbol,
                self._contract_manager.get_expiries_for_underlying(underlying_symbol),
            )
            expiry_info = None
            if is_option:
                expiry_info = self._expiry_handler.resolve_expiry(
                    underlying=underlying_symbol,
                    expiry_override=expiry_override or parsed_expiry_date,
                    expiry_str=parsed_expiry_str,
                    prefer_weekly=True,
                )
                if not expiry_info:
                    return self._error_response(f"Could not resolve expiry for {underlying_symbol}", request_id)

                contract, contract_resolution = self._contract_manager.resolve_option_contract(
                    underlying=underlying_symbol,
                    strike=strike_value,
                    option_type=option_type_value,
                    exchange=exchange,
                    expiry=expiry_info.date,
                    prefer_weekly=True,
                    allow_strike_fallback=allow_strike_fallback,
                )
            else:
                contracts = self._contract_manager.get_contracts_by_symbol(symbol)
                contract = contracts[0] if contracts else None
                contract_resolution = {"match_type": "symbol_lookup", "fallback_used": False}

            if not contract:
                return self._error_response(
                    "Exact contract not found for the requested symbol, strike, option type, and expiry.",
                    request_id,
                    error_code="INVALID_CONTRACT",
                    contract_match=contract_resolution,
                )
            if not contract.token:
                return self._error_response("Symbol token is missing for the resolved contract.", request_id, error_code="INVALID_CONTRACT")
            if ENFORCE_LOT_SIZE and contract.lot_size and int(quantity) % int(contract.lot_size) != 0:
                return self._error_response(
                    f"Quantity must be a multiple of the contract lot size ({contract.lot_size}).",
                    request_id,
                    error_code="INVALID_LOT_SIZE",
                )

            requested_order_type = (order_type or "LIMIT").upper()
            normalized_buffer = max(MIN_BUFFER_PERCENTAGE, min(MAX_BUFFER_PERCENTAGE, float(buffer_percentage or DEFAULT_BUFFER_PERCENTAGE)))

            if check_duplicate:
                is_duplicate, existing = self._idempotency_manager.check_duplicate(
                    client_id=client_id,
                    symbol=underlying_symbol,
                    strike=strike_value,
                    side=side,
                    option_type=option_type_value,
                )
                if is_duplicate:
                    logger.warning(
                        "Duplicate trade blocked",
                        user_id=client_id,
                        symbol=underlying_symbol,
                        strike=strike_value,
                        option_type=option_type_value,
                        transaction_type=side.upper(),
                        response=existing.to_dict() if existing else None,
                    )
                    return {
                        "status": "duplicate",
                        "message": "Duplicate order skipped within idempotency window.",
                        "existing_order_id": existing.order_id if existing else None,
                        "request_id": request_id,
                        "error_code": "DUPLICATE_ORDER",
                    }

            if check_position:
                can_place, reason = self._position_manager.can_place_order(
                    client_id=client_id,
                    underlying=underlying_symbol,
                    strike=strike_value,
                    option_type=option_type_value,
                    side=side,
                )
                if not can_place:
                    if existing:
                        self._idempotency_manager.remove_record(existing.idempotency_key)
                    return self._error_response(reason, request_id)

            ltp = None
            if requested_order_type == OrderType.MARKET.value and not ALLOW_MARKET_ORDERS:
                if existing:
                    self._idempotency_manager.remove_record(existing.idempotency_key)
                return self._error_response(
                    "Market orders are disabled by system configuration.",
                    request_id,
                    error_code="MARKET_ORDER_DISABLED",
                )

            if FORCE_LTP_FETCH or requested_order_type in {OrderType.LIMIT.value, OrderType.MARKET.value}:
                ltp = self._ltp_service.get_ltp(
                    smart_connect=smart_connect,
                    exchange=exchange,
                    token=contract.token,
                    symbol=contract.symbol,
                )
                if ltp is None or ltp < MIN_VALID_LTP or ltp > MAX_VALID_LTP:
                    if existing:
                        self._idempotency_manager.remove_record(existing.idempotency_key)
                    return self._error_response(
                        "Live price validation failed for Angel One order placement.",
                        request_id,
                        error_code="INVALID_LTP",
                    )

            if requested_order_type == OrderType.MARKET.value and ltp is None:
                if existing:
                    self._idempotency_manager.remove_record(existing.idempotency_key)
                return self._error_response(
                    "Market order rejected because live price is unavailable.",
                    request_id,
                    error_code="INVALID_LTP",
                )

            resolved_order_type = requested_order_type
            if requested_order_type == OrderType.MARKET.value and USE_LIMIT_WITH_BUFFER:
                resolved_order_type = OrderType.LIMIT.value

            if resolved_order_type == OrderType.LIMIT.value and price is None:
                price = self._ltp_service.calculate_limit_price(
                    ltp=ltp,
                    side=side,
                    buffer_percentage=normalized_buffer,
                    tick_size=contract.tick_size or DEFAULT_TICK_SIZE,
                )
            elif resolved_order_type == OrderType.LIMIT.value and price is not None:
                price = self._ltp_service.round_to_tick(
                    float(price),
                    tick_size=contract.tick_size or DEFAULT_TICK_SIZE,
                    direction="UP" if side.upper() == "BUY" else "DOWN",
                )
            else:
                price = None

            if resolved_order_type == OrderType.LIMIT.value and ltp and price is not None:
                slippage_percent = abs(float(price) - ltp) / ltp * 100
                if slippage_percent > MAX_SLIPPAGE_PERCENT:
                    if existing:
                        self._idempotency_manager.remove_record(existing.idempotency_key)
                    return self._error_response(
                        f"Limit price exceeds allowed slippage threshold of {MAX_SLIPPAGE_PERCENT}%.",
                        request_id,
                        error_code="SLIPPAGE_EXCEEDED",
                    )

            order_params = {
                "variety": variety,
                "tradingsymbol": contract.symbol,
                "symboltoken": contract.token,
                "transactiontype": side.upper(),
                "exchange": exchange,
                "ordertype": resolved_order_type,
                "producttype": product_type.upper(),
                "duration": duration.upper(),
                "quantity": str(quantity),
            }

            if resolved_order_type == OrderType.LIMIT.value:
                order_params["price"] = str(price)
            else:
                order_params["price"] = "0"

            if trigger_price is not None:
                order_params["triggerprice"] = str(trigger_price)

            logger.info(
                "Placing order",
                user_id=client_id,
                symbol=contract.symbol,
                strike=strike_value,
                option_type=option_type_value,
                request_id=request_id,
                order_type=resolved_order_type,
                contract_resolution=contract_resolution,
            )

            result = None
            last_error = None
            for attempt in range(1, 3):
                try:
                    result = smart_connect.placeOrder(order_params)
                    if result:
                        break
                    last_error = "Empty response from broker"
                except Exception as exc:
                    last_error = str(exc)
                    if attempt == 1 and self._is_transient_error(last_error):
                        logger.warning(
                            "Retrying order after transient failure",
                            user_id=client_id,
                            symbol=contract.symbol,
                            strike=strike_value,
                            request_id=request_id,
                            attempt=attempt,
                            error=last_error,
                        )
                        continue
                    raise

                if attempt == 1 and self._is_transient_error(last_error or ""):
                    logger.warning(
                        "Retrying order after broker returned transient failure",
                        user_id=client_id,
                        symbol=contract.symbol,
                        strike=strike_value,
                        request_id=request_id,
                        error=last_error,
                    )

            if result:
                order_id = self._extract_order_id(result)
                if check_duplicate and existing:
                    self._idempotency_manager.record_execution(existing.idempotency_key, order_id, "complete")

                self._position_manager.add_position(
                    client_id=client_id,
                    symbol=contract.symbol,
                    underlying=underlying_symbol,
                    side=PositionSide.LONG if side.upper() == "BUY" else PositionSide.SHORT,
                    quantity=quantity,
                    price=float(price) if price is not None else 0,
                    strike=strike_value,
                    option_type=option_type_value,
                    exchange=exchange,
                    order_id=order_id,
                )

                return {
                    "status": "success",
                    "order_id": order_id,
                    "message": "Order placed successfully",
                    "symbol": contract.symbol,
                    "strike": strike_value,
                    "option_type": option_type_value,
                    "price": price,
                    "quantity": quantity,
                    "side": side,
                    "request_id": request_id,
                    "order_type": resolved_order_type,
                    "requested_order_type": requested_order_type,
                    "buffer_percentage_used": normalized_buffer if resolved_order_type == OrderType.LIMIT.value else None,
                    "ltp": ltp,
                    "contract_match": contract_resolution,
                }

            error_msg = result.get("message", "Order placement failed") if isinstance(result, dict) else (last_error or "Order placement failed")
            if existing:
                self._idempotency_manager.remove_record(existing.idempotency_key)
            structured_error = self._build_error_payload(error_msg)
            logger.error(
                "Order placement failed",
                user_id=client_id,
                symbol=contract.symbol,
                strike=strike_value,
                option_type=option_type_value,
                request_id=request_id,
                response=structured_error,
            )
            return self._error_response(structured_error["message"], request_id, **structured_error)

        except Exception as e:
            if existing:
                self._idempotency_manager.remove_record(existing.idempotency_key)
            structured_error = self._build_error_payload(str(e))
            logger.exception(
                "Order placement exception",
                user_id=client_id,
                symbol=symbol,
                request_id=request_id,
                response=structured_error,
            )
            return self._error_response(structured_error["message"], request_id, **structured_error)
    
    def place_order_async(
        self,
        client_id: str,
        api_key: str,
        symbol: str,
        side: str,
        quantity: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Place order asynchronously via Celery.
        
        Returns:
            Dict with task_id for tracking
        """
        from ..tasks import place_order_async as async_task
        
        request_id = kwargs.pop('request_id', str(uuid.uuid4())[:8])
        
        # Parse symbol first for order params
        parsed = self._symbol_parser.parse(symbol)
        
        order_params = {
            "tradingsymbol": symbol,
            "transactiontype": side.upper(),
            "quantity": quantity,
            "strike": parsed.strike,
            "option_type": parsed.option_type,
            "underlying": parsed.underlying,
            **kwargs
        }
        
        # Submit to Celery
        task = async_task.delay(
            client_id=client_id,
            api_key=api_key,
            order_params=order_params,
            request_id=request_id
        )
        
        logger.info(
            "Order submitted to queue",
            task_id=task.id,
            client_id=client_id,
            symbol=symbol
        )
        
        return {
            "status": "queued",
            "task_id": task.id,
            "message": "Order submitted to queue",
            "request_id": request_id
        }
    
    def _error_response(self, message: str, request_id: str, **extra) -> Dict[str, Any]:
        """Create error response"""
        payload = {
            "status": "error",
            "message": message,
            "request_id": request_id
        }
        payload.update(extra)
        return payload

    def _is_transient_error(self, message: str) -> bool:
        normalized = (message or "").lower()
        return any(marker in normalized for marker in self.TRANSIENT_ERROR_MARKERS)

    def _build_error_payload(self, message: str) -> Dict[str, Any]:
        normalized = (message or "").lower()
        if "ag7002" in normalized:
            return {
                "error_code": "IP_NOT_WHITELISTED",
                "message": "Angel One rejected the request because this server IP is not registered/whitelisted for your SmartAPI app (AG7002).",
            }
        if "token" in normalized and ("expired" in normalized or "invalid" in normalized or "session" in normalized):
            return {
                "error_code": "TOKEN_EXPIRED",
                "message": "Angel One session is invalid or expired. Please login again.",
            }
        if "margin" in normalized or "rms" in normalized or "fund" in normalized:
            return {
                "error_code": "MARGIN_ERROR",
                "message": message,
            }
        return {
            "error_code": "ORDER_EXECUTION_FAILED",
            "message": message,
        }

    @staticmethod
    def _extract_order_id(result: Any):
        if isinstance(result, str):
            return result
        if not isinstance(result, dict):
            return None

        data = result.get("data")
        if isinstance(data, list):
            data = data[0] if data and isinstance(data[0], dict) else {}
        elif not isinstance(data, dict):
            data = {}

        return (
            data.get("orderid")
            or data.get("order_id")
            or result.get("orderid")
            or result.get("order_id")
        )
    
    def get_order_book(
        self,
        client_id: str,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get order book"""
        session = self._session_manager.get_session(client_id, api_key)
        if not session or not session.is_valid():
            return {"status": "error", "message": "Invalid session"}
        
        try:
            result = session.smart_connect.orderBook()
            return {
                "status": "success" if result.get("status") else "error",
                "data": result.get("data", []),
                "message": result.get("message", "")
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_trade_book(
        self,
        client_id: str,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get trade book"""
        session = self._session_manager.get_session(client_id, api_key)
        if not session or not session.is_valid():
            return {"status": "error", "message": "Invalid session"}
        
        try:
            result = session.smart_connect.tradeBook()
            return {
                "status": "success" if result.get("status") else "error",
                "data": result.get("data", []),
                "message": result.get("message", "")
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def cancel_order(
        self,
        client_id: str,
        order_id: str,
        variety: str = "NORMAL",
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel an order"""
        session = self._session_manager.get_session(client_id, api_key)
        if not session or not session.is_valid():
            return {"status": "error", "message": "Invalid session"}
        
        try:
            result = session.smart_connect.cancelOrder(order_id, variety)
            
            logger.info(
                "Order cancelled",
                order_id=order_id,
                client_id=client_id
            )
            
            return {
                "status": "success" if result.get("status") else "error",
                "message": result.get("message", "Order cancelled")
            }
        except Exception as e:
            logger.error(
                "Cancel order failed",
                order_id=order_id,
                error=str(e)
            )
            return {"status": "error", "message": str(e)}
