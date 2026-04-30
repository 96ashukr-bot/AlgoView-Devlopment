"""
Angel One upgraded compatibility facade.

This module stays intentionally thin. It preserves the legacy function names
used across Django views while delegating all real work to the modular
service/manager layer under ``main.angelone``.
"""

from datetime import timedelta
from typing import Optional

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from main.angelone.constants import (
    DEFAULT_BUFFER_PERCENTAGE,
    MAX_BUFFER_PERCENTAGE,
    MIN_BUFFER_PERCENTAGE,
)
from main.angelone.managers.contract_manager import ContractMasterManager
from main.angelone.services.auth_service import AuthService
from main.angelone.services.ltp_service import LTPService
from main.angelone.services.order_service import OrderService
from main.services.login_activity_service import LoginActivityService
from main.angelone.utils.expiry_handler import get_expiry_handler
from main.angelone.utils.logging_utils import TradingLogger

logger = TradingLogger("angleapi_upgraded")


def validate_buffer_percentage(buffer_percentage: Optional[float]) -> tuple[bool, str, float]:
    """Validate and normalize the configured Angel One LTP buffer."""
    if buffer_percentage is None:
        return True, "", DEFAULT_BUFFER_PERCENTAGE

    try:
        buffer = float(buffer_percentage)
    except (TypeError, ValueError):
        return False, "Buffer percentage must be a number", DEFAULT_BUFFER_PERCENTAGE

    if buffer < MIN_BUFFER_PERCENTAGE:
        return False, f"Buffer cannot be less than {MIN_BUFFER_PERCENTAGE}%", MIN_BUFFER_PERCENTAGE
    if buffer > MAX_BUFFER_PERCENTAGE:
        return False, f"Buffer cannot exceed {MAX_BUFFER_PERCENTAGE}%", MAX_BUFFER_PERCENTAGE
    return True, "", buffer


def fetch_contract_master(force_refresh: bool = False):
    """Return the current contract master snapshot from the shared manager."""
    manager = ContractMasterManager.get_instance()
    manager.initialize(blocking=True)
    if force_refresh:
        manager._refresh_contracts()
    return manager._raw_data


def get_symbol_token(symbol: str, strike: str, option_type: str, exchange: str = "NFO") -> tuple:
    """Resolve Angel One trading symbol and token using strict contract lookup."""
    try:
        contract_manager = ContractMasterManager.get_instance()
        contract_manager.initialize(blocking=True)

        expiry_handler = get_expiry_handler()
        expiry_handler.set_available_expiries(
            symbol,
            contract_manager.get_expiries_for_underlying(symbol),
        )
        expiry_info = expiry_handler.get_nearest_expiry(symbol, prefer_weekly=True)
        if not expiry_info:
            return None, None

        contract, _resolution = contract_manager.resolve_option_contract(
            underlying=symbol,
            strike=float(strike),
            option_type=option_type,
            exchange=exchange,
            expiry=expiry_info.date,
            prefer_weekly=True,
        )
        if not contract:
            return None, None
        return contract.symbol, contract.token
    except Exception as exc:
        logger.error("Failed to resolve symbol token", symbol=symbol, strike=strike, option_type=option_type, error=str(exc))
        return None, None


def get_ltp(symbol_token: str, exchange: str = "NSE", tradingsymbol: str = "", broker_details=None) -> float:
    """Fetch LTP through the shared LTP service using exact tradingsymbol + token."""
    try:
        client_code = None
        api_key = None
        if broker_details is not None:
            client_code = getattr(broker_details, "broker_Demate_User_Name", None) or getattr(broker_details, "broker_API_UID", None)
            api_key = getattr(broker_details, "broker_API_KEY", None)

        if not tradingsymbol:
            contract = ContractMasterManager.get_instance().get_contract_by_token(symbol_token)
            tradingsymbol = contract.symbol if contract else ""

        if not all([client_code, api_key, tradingsymbol]):
            return 0.0

        ensure = AuthService().ensure_valid_session(
            client_id=client_code,
            api_key=api_key,
            broker_details=broker_details,
        )
        session = ensure.get("session")
        if ensure.get("status") != "success" or not session or not session.smart_connect:
            return 0.0

        ltp = LTPService.get_instance().get_ltp(
            smart_connect=session.smart_connect,
            exchange=exchange,
            token=symbol_token,
            symbol=tradingsymbol,
        )
        return float(ltp) if ltp and ltp > 0 else 0.0
    except Exception as exc:
        logger.error("Failed to fetch LTP", symboltoken=symbol_token, tradingsymbol=tradingsymbol, error=str(exc))
        return 0.0


def angel_one_login(client_code: str, password: str, totp_secret: str, api_key: str, broker_details=None, enforce_compliance: bool = True) -> dict:
    """Legacy-auth facade routed to AuthService."""
    result = AuthService().login(
        client_id=client_code,
        password=password,
        totp_secret=totp_secret,
        api_key=api_key,
        broker_details=broker_details,
        force_new=False,
    )
    result.setdefault("regulatory_flags", [])
    result["session_mode"] = "smartapi_session"
    return result


def angel_one_refresh_token(client_code: str, api_key: str, refresh_token: str = None, broker_details=None) -> dict:
    """Legacy refresh facade routed to AuthService."""
    result = AuthService().refresh_session(client_id=client_code, api_key=api_key)
    if result.get("status") == "success" and broker_details:
        broker_details.set_session_tokens(
            access_token=result.get("access_token"),
            refresh_token=result.get("refresh_token") or broker_details.get_refresh_token_secure(),
            feed_token=result.get("feed_token") or broker_details.get_feed_token_secure(),
            expiry=getattr(broker_details, "access_token_expiry", None),
        )
        broker_details.save(update_fields=[
            "encrypted_access_token",
            "encrypted_refresh_token",
            "encrypted_feed_token",
            "access_token_expiry",
            "isTokenExpired",
        ])
    return result


def angel_one_logout(client_code: str, api_key: str) -> dict:
    """Legacy logout facade routed to AuthService."""
    return AuthService().logout(client_id=client_code, api_key=api_key)


def place_angel_one_order(
    broker_details,
    symbol: str,
    strike: str,
    option_type: str,
    quantity: int,
    transaction_type: str = "BUY",
    buffer_percentage: float = DEFAULT_BUFFER_PERCENTAGE,
    order_type: str = "LIMIT",
    price: float = None,
    order_variety: str = "NORMAL",
    exchange: str = "NFO",
    product_type: str = "INTRADAY",
    duration: str = "DAY",
    request_id: str = None,
) -> dict:
    """Legacy order facade routed to OrderService."""
    api_key = getattr(broker_details, "broker_API_KEY", None)
    client_code = getattr(broker_details, "broker_Demate_User_Name", None) or getattr(broker_details, "broker_API_UID", None)
    if not all([broker_details, api_key, client_code]):
        return {"status": "error", "message": "Missing broker credentials"}

    is_valid, error_message, normalized_buffer = validate_buffer_percentage(buffer_percentage)
    if not is_valid:
        return {"status": "error", "message": error_message}

    return OrderService().place_order(
        client_id=client_code,
        api_key=api_key,
        symbol=symbol,
        side=transaction_type.upper(),
        quantity=int(quantity),
        product_type=product_type,
        order_type=order_type,
        price=price,
        buffer_percentage=normalized_buffer,
        exchange=exchange,
        variety=order_variety,
        duration=duration,
        underlying=symbol,
        strike=float(strike) if strike is not None else None,
        option_type=option_type,
        request_id=request_id,
        broker_details=broker_details,
    )


def _ensure_session_for_broker(broker_details, verify_remote: bool = True):
    """Internal helper to obtain a valid SmartConnect-backed session."""
    client_code = getattr(broker_details, "broker_Demate_User_Name", None) or getattr(broker_details, "broker_API_UID", None)
    api_key = getattr(broker_details, "broker_API_KEY", None)
    if not all([client_code, api_key]):
        return None, {"status": "error", "message": "Missing broker credentials"}

    result = AuthService().ensure_valid_session(
        client_id=client_code,
        api_key=api_key,
        broker_details=broker_details,
        verify_remote=verify_remote,
    )
    return result.get("session"), result


def get_angel_one_order_book(broker_details) -> dict:
    """Fetch order book through the validated SmartConnect session."""
    session, ensure = _ensure_session_for_broker(broker_details)
    if not session or ensure.get("status") != "success":
        return {"status": "error", "message": ensure.get("message", "Session expired")}

    data = session.smart_connect.orderBook()
    return {"status": "success", "orders": data.get("data", []) if isinstance(data, dict) else []}


def get_angel_one_trade_book(broker_details) -> dict:
    """Fetch trade book through the validated SmartConnect session."""
    session, ensure = _ensure_session_for_broker(broker_details)
    if not session or ensure.get("status") != "success":
        return {"status": "error", "message": ensure.get("message", "Session expired")}

    data = session.smart_connect.tradeBook()
    return {"status": "success", "trades": data.get("data", []) if isinstance(data, dict) else []}


def cancel_angel_one_order(broker_details, order_id: str, variety: str = "NORMAL") -> dict:
    """Cancel an Angel One order through SmartConnect."""
    session, ensure = _ensure_session_for_broker(broker_details)
    if not session or ensure.get("status") != "success":
        return {"status": "error", "message": ensure.get("message", "Session expired")}

    response = session.smart_connect.cancelOrder(order_id, variety)
    if response and isinstance(response, dict) and response.get("status"):
        return {"status": "success", "message": "Order cancelled", "order_id": order_id}
    return {"status": "error", "message": response.get("message", "Cancel failed") if isinstance(response, dict) else "Cancel failed"}


def get_angel_one_holdings(broker_details) -> dict:
    """Fetch holdings using the shared authenticated session."""
    session, ensure = _ensure_session_for_broker(broker_details)
    if not session or ensure.get("status") != "success":
        return {"status": "error", "message": ensure.get("message", "Session expired")}

    data = session.smart_connect.holding()
    return {"status": "success", "holdings": data.get("data", []) if isinstance(data, dict) else []}


def get_angel_one_positions(broker_details) -> dict:
    """Fetch live positions using the shared authenticated session."""
    session, ensure = _ensure_session_for_broker(broker_details)
    if not session or ensure.get("status") != "success":
        return {"status": "error", "message": ensure.get("message", "Session expired")}

    data = session.smart_connect.position()
    raw_positions = data.get("data", []) if isinstance(data, dict) else []

    if isinstance(raw_positions, dict):
        positions = []
        for key in ("net", "day", "positions"):
            value = raw_positions.get(key)
            if isinstance(value, list):
                positions.extend(value)
        if not positions:
            positions = [raw_positions]
    elif isinstance(raw_positions, list):
        positions = raw_positions
    else:
        positions = []

    return {"status": "success", "positions": positions}


def get_angel_one_profile(broker_details) -> dict:
    """Fetch Angel One profile through AuthService."""
    client_code = getattr(broker_details, "broker_Demate_User_Name", None) or getattr(broker_details, "broker_API_UID", None)
    api_key = getattr(broker_details, "broker_API_KEY", None)
    return AuthService().get_profile(client_id=client_code, api_key=api_key)


def get_angel_one_margin(broker_details) -> dict:
    """Fetch Angel One RMS/margin through AuthService."""
    client_code = getattr(broker_details, "broker_Demate_User_Name", None) or getattr(broker_details, "broker_API_UID", None)
    api_key = getattr(broker_details, "broker_API_KEY", None)
    return AuthService().get_margin(client_id=client_code, api_key=api_key)


def exit_angel_one_position(broker_details, symbol: str, strike: str, option_type: str, exchange: str = "NFO") -> dict:
    """Best-effort exit helper kept for backward compatibility."""
    normalized_symbol = str(symbol or "").upper()
    normalized_option_type = str(option_type or "").upper()
    strike_token = str(strike or "").replace(".0", "")

    positions_result = get_angel_one_positions(broker_details)
    holdings_result = get_angel_one_holdings(broker_details)

    candidate_sources = []
    if positions_result.get("status") == "success":
        candidate_sources.append(positions_result.get("positions", []))
    if holdings_result.get("status") == "success":
        candidate_sources.append(holdings_result.get("holdings", []))

    if not candidate_sources:
        return positions_result if positions_result.get("status") == "error" else holdings_result

    for source in candidate_sources:
        for position in source:
            trading_symbol = str(
                position.get("tradingsymbol")
                or position.get("tradingSymbol")
                or ""
            ).upper()
            position_exchange = str(
                position.get("exchange")
                or position.get("exchangeSegment")
                or exchange
            ).upper()

            if position_exchange != str(exchange or "NFO").upper():
                continue
            if normalized_symbol and normalized_symbol not in trading_symbol:
                continue
            if normalized_option_type and normalized_option_type not in trading_symbol:
                continue
            if strike_token and strike_token not in trading_symbol.replace(".0", ""):
                continue

            quantity = position.get("netqty")
            if quantity in (None, "", "None"):
                buy_qty = position.get("buyqty") or position.get("buyQty") or 0
                sell_qty = position.get("sellqty") or position.get("sellQty") or 0
                quantity = float(buy_qty or 0) - float(sell_qty or 0)
            if quantity in (None, "", "None"):
                quantity = position.get("quantity", 0)

            try:
                quantity = int(float(quantity or 0))
            except (TypeError, ValueError):
                quantity = 0

            if quantity == 0:
                continue

            transaction_type = "SELL" if quantity > 0 else "BUY"
            return place_angel_one_order(
                broker_details=broker_details,
                symbol=symbol,
                strike=strike,
                option_type=option_type,
                quantity=abs(quantity),
                transaction_type=transaction_type,
                exchange=exchange,
            )

    return {"status": "info", "message": "No position found to exit"}


def get_token_details(broker_details) -> dict:
    """Return token/session details using the shared auth/session layer."""
    client_code = getattr(broker_details, "broker_Demate_User_Name", None) or getattr(broker_details, "broker_API_UID", None)
    token_status = LoginActivityService()._token_status(
        {
            "encrypted_access_token": getattr(broker_details, "encrypted_access_token", None),
            "encrypted_refresh_token": getattr(broker_details, "encrypted_refresh_token", None),
            "encrypted_feed_token": getattr(broker_details, "encrypted_feed_token", None),
            "access_token_expiry": getattr(broker_details, "access_token_expiry", None),
            "isTokenExpired": getattr(broker_details, "isTokenExpired", None),
        }
    )
    session_status = LoginActivityService()._session_status(
        {
            "broker_Demate_User_Name": getattr(broker_details, "broker_Demate_User_Name", None),
            "broker_API_UID": getattr(broker_details, "broker_API_UID", None),
            "broker_API_KEY": getattr(broker_details, "broker_API_KEY", None),
            "encrypted_broker_password": getattr(broker_details, "encrypted_broker_password", None),
            "encrypted_broker_totp_secret": getattr(broker_details, "encrypted_broker_totp_secret", None),
            "encrypted_access_token": getattr(broker_details, "encrypted_access_token", None),
            "encrypted_refresh_token": getattr(broker_details, "encrypted_refresh_token", None),
            "encrypted_feed_token": getattr(broker_details, "encrypted_feed_token", None),
            "access_token_expiry": getattr(broker_details, "access_token_expiry", None),
            "isTokenExpired": getattr(broker_details, "isTokenExpired", None),
            "tokenCreatedAt": getattr(broker_details, "tokenCreatedAt", None),
        },
        token_status,
    )
    return {
        "status": "success",
        "is_valid": bool(session_status.get("is_active")),
        "client_code": client_code,
        "session_expiry": getattr(broker_details, "access_token_expiry", None).isoformat() if getattr(broker_details, "access_token_expiry", None) else None,
        "has_access_token": bool(broker_details.get_access_token_secure() if broker_details else None),
        "has_refresh_token": bool(broker_details.get_refresh_token_secure() if broker_details else None),
        "has_feed_token": bool(broker_details.get_feed_token_secure() if broker_details else None),
        "token_status": token_status.get("status"),
        "session_status": session_status.get("status"),
        "session_active": session_status.get("is_active"),
        "is_expired": token_status.get("is_expired", False),
        "expires_at": token_status.get("expires_at"),
        "last_activity_at": session_status.get("last_activity_at"),
        "validated_at": session_status.get("validated_at"),
        "last_login_at": getattr(broker_details, "tokenCreatedAt", None).isoformat() if getattr(broker_details, "tokenCreatedAt", None) else None,
        "last_logout_at": getattr(broker_details, "broker_last_logout_at", None).isoformat() if getattr(broker_details, "broker_last_logout_at", None) else None,
        "message": session_status.get("source", ""),
    }


class SymbolExpiryDateListView(APIView):
    """Return available expiries from the shared contract master."""

    def get(self, request):
        symbol = request.query_params.get("symbol")
        if not symbol:
            return Response({"error": "Symbol required"}, status=400)

        contract_manager = ContractMasterManager.get_instance()
        contract_manager.initialize(blocking=True)
        expiries = contract_manager.get_expiries_for_underlying(symbol)
        return Response(
            {
                "symbol": symbol,
                "expiry_dates": [expiry.strftime("%d%b%Y").upper() for expiry in expiries[:10]],
            }
        )


def exit_existing_buy_position_angleone(*args, **kwargs):
    """Legacy wrapper kept for existing Django views."""
    broker_details = kwargs.get("broker_details") or kwargs.get("client_broker") or (args[0] if args else None)
    if not broker_details:
        return {"status": "error", "message": "Broker details are required"}

    tradingsymbol = kwargs.get("tradingsymbol") or kwargs.get("symbol")
    if tradingsymbol:
        from main.angelone.utils.symbol_parser import get_symbol_parser

        parsed = get_symbol_parser().parse(str(tradingsymbol))
        if parsed.is_option:
            return exit_angel_one_position(
                broker_details=broker_details,
                symbol=parsed.underlying,
                strike=str(parsed.strike),
                option_type=parsed.option_type,
                exchange=kwargs.get("Exchange") or kwargs.get("exchange", "NFO"),
            )

    return {"status": "info", "message": "Exit logic requires an option trading symbol"}


def place_Angle_order(*args, **kwargs):
    """Legacy wrapper that supports both old and new call signatures."""
    if args and len(args) > 1 and hasattr(args[1], "broker_API_KEY"):
        broker_details = args[1]
        tradingsymbol = kwargs.get("tradingsymbol") or kwargs.get("symbol")
        quantity = kwargs.get("quantity", 0)
        transactiontype = kwargs.get("transactiontype", "BUY")
        product_type = kwargs.get("product_type", "INTRADAY")
        ordertype = kwargs.get("ordertype", "LIMIT")
        exchange = kwargs.get("Exchange") or kwargs.get("exchange", "NFO")
        requested_buffer = kwargs.get("buffer_percentage")
        if requested_buffer is None:
            buffer_percentage = float(getattr(broker_details, "buffer_percentage", DEFAULT_BUFFER_PERCENTAGE) or DEFAULT_BUFFER_PERCENTAGE)
        else:
            buffer_percentage = requested_buffer

        if not tradingsymbol:
            return {"status": "error", "message": "Trading symbol is required"}

        from main.angelone.utils.symbol_parser import get_symbol_parser

        parsed = get_symbol_parser().parse(str(tradingsymbol))
        if not parsed.is_option:
            return {"status": "error", "message": "Legacy Angel One wrapper expects an option trading symbol"}

        return place_angel_one_order(
            broker_details=broker_details,
            symbol=parsed.underlying,
            strike=str(parsed.strike),
            option_type=parsed.option_type,
            quantity=int(quantity),
            transaction_type=transactiontype,
            order_type=ordertype,
            price=kwargs.get("price"),
            product_type=product_type,
            exchange=exchange,
            buffer_percentage=buffer_percentage,
            request_id=str(kwargs.get("history_id")) if kwargs.get("history_id") else None,
        )

    return place_angel_one_order(*args, **kwargs)


def get_access_token(*args, **kwargs):
    """Legacy access-token wrapper."""
    return angel_one_login(*args, **kwargs).get("access_token")
