"""
Angel One API Views - Upgraded Version
======================================
Updated login flow and order placement with compliance checks.
"""

import logging
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlparse

from django.http import JsonResponse
from django.shortcuts import redirect
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_GET
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.angelone.services.state_service import CallbackStateService

logger = logging.getLogger(__name__)


def _parse_bool(value):
    """Parse boolean-like values from JSON/form payloads."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


# =========================
# ANGEL ONE LOGIN VIEWS
# =========================


def _get_angel_broker_details_for_user(user):
    from main.models import ClientBrokerdetails

    return next(
        (
            broker_details
            for broker_details in ClientBrokerdetails.objects.filter(client=user).select_related("broker_name")
            if broker_details.is_angel_one_broker()
        ),
        None,
    )


def _calculate_session_expiry():
    current_time = timezone.now()
    if current_time.hour < 3 or (current_time.hour == 3 and current_time.minute < 30):
        expiry_date = current_time.date()
    else:
        expiry_date = current_time.date() + timedelta(days=1)
    return datetime.combine(expiry_date, datetime.min.time(), tzinfo=current_time.tzinfo) + timedelta(hours=3, minutes=30)


def _is_public_browser_origin(origin):
    if not origin:
        return False
    try:
        parsed = urlparse(origin)
        hostname = (parsed.hostname or "").strip().lower()
        if not hostname:
            return False
        if hostname == "0.0.0.0":
            return False
        if hostname.startswith("192.168.") or hostname.startswith("10."):
            return False
        if hostname.startswith("172."):
            second_octet = int(hostname.split(".")[1])
            if 16 <= second_octet <= 31:
                return False
        return True
    except Exception:
        return False


def _resolve_frontend_return_url(request):
    configured_frontend = getattr(settings, "FRONTEND_APP_URL", "").rstrip("/")
    request_origin = ""
    if request is not None:
        request_origin = (request.headers.get("Origin") or "").rstrip("/")
        if not request_origin:
            referer = (request.headers.get("Referer") or "").strip()
            if referer:
                try:
                    parsed = urlparse(referer)
                    if parsed.scheme and parsed.netloc:
                        request_origin = f"{parsed.scheme}://{parsed.netloc}"
                except Exception:
                    request_origin = ""
    base = request_origin or configured_frontend
    if base:
        return f"{base}/dashboard/algoviewtech/user"
    return None


def _broker_callback_url(request):
    configured_redirect = getattr(settings, "REDIRECT_URL", "").strip()
    if configured_redirect:
        parsed = urlparse(configured_redirect)
        if parsed.scheme and parsed.netloc:
            if parsed.path.rstrip("/") in {"/callback", "/auth-callback", "/callback-angelone"}:
                return f"{parsed.scheme}://{parsed.netloc}/api/broker/callback/"
            return configured_redirect

    if request is not None:
        candidate = request.build_absolute_uri("/api/broker/callback/")
        if _is_public_browser_origin(candidate):
            return candidate

    return "/api/broker/callback/"


def build_angelone_redirect_payload(user, broker_details=None, request=None):
    if not user or not user.is_authenticated:
        raise ValueError("User not authenticated")

    broker_details = broker_details or _get_angel_broker_details_for_user(user)
    if not broker_details:
        raise LookupError("Angel One broker settings not found")

    client_code = broker_details.broker_Demate_User_Name or broker_details.broker_API_UID
    missing_fields = []
    if not broker_details.broker_API_KEY:
        missing_fields.append("broker_API_KEY")
    if not client_code:
        missing_fields.append("broker_Demate_User_Name")

    if missing_fields:
        error = ValueError("Angel One credentials are incomplete")
        setattr(error, "missing_fields", missing_fields)
        raise error

    state = secrets.token_urlsafe(24)
    CallbackStateService().create(
        state=state,
        user_id=user.id,
        broker_details_id=broker_details.id,
        client_code=client_code,
        frontend_redirect_url=_resolve_frontend_return_url(request),
    )

    params = urlencode(
        {
            "api_key": broker_details.broker_API_KEY,
            "redirect_url": _broker_callback_url(request),
            "state": state,
        }
    )
    return {
        "redirect_url": f"https://smartapi.angelone.in/publisher-login?{params}",
        "mode": "publisher_login",
        "compliance_mode": "token_only",
    }

def login_angelone_redirect(request):
    """
    Deprecated compatibility shim for older clients.
    """
    return redirect("/broker_auth_login/?broker=angel%20one")


@require_GET
def angelone_callback(request):
    """
    Secure Angel One publisher callback.

    Angel One returns tokens directly to the callback URL. We only accept those
    tokens when they are tied to a one-time state that was generated during the
    authenticated broker login flow.
    """
    from main.angelone.services.auth_service import AuthService
    from main.models import ClientBrokerdetails

    django_request = getattr(request, "_request", request)
    query_params = getattr(django_request, "GET", None) or getattr(request, "GET", {})
    allowed_params = {"state", "access_token", "auth_token", "jwtToken", "refreshToken", "refresh_token", "feedToken", "feed_token"}
    unexpected = set(query_params.keys()) - allowed_params
    if unexpected:
        return JsonResponse(
            {
                "status": "error",
                "message": "Unexpected callback parameters received.",
                "unexpected_parameters": sorted(unexpected),
            },
            status=400,
        )

    state = str(query_params.get("state") or "").strip()
    if not state:
        return JsonResponse({"status": "error", "message": "Missing mandatory callback state."}, status=400)

    state_record = CallbackStateService().consume(state)
    if not state_record:
        return JsonResponse(
            {"status": "error", "message": "Callback state is invalid, expired, or already used."},
            status=400,
        )

    request_user = getattr(django_request, "user", None) or getattr(request, "user", None)
    if request_user and getattr(request_user, "is_authenticated", False) and request_user.id != state_record.user_id:
        return JsonResponse({"status": "error", "message": "Callback user does not match broker login state."}, status=403)

    access_token = (
        query_params.get("access_token")
        or query_params.get("auth_token")
        or query_params.get("jwtToken")
    )
    refresh_token = query_params.get("refreshToken") or query_params.get("refresh_token")
    feed_token = query_params.get("feedToken") or query_params.get("feed_token")
    if not access_token:
        return JsonResponse({"status": "error", "message": "Access token missing in Angel One callback."}, status=400)

    broker_details = (
        ClientBrokerdetails.objects.select_related("broker_name")
        .filter(id=state_record.broker_details_id, client_id=state_record.user_id)
        .first()
    )
    if not broker_details or not broker_details.is_angel_one_broker():
        return JsonResponse({"status": "error", "message": "Angel One broker details not found for callback state."}, status=400)

    client_code = broker_details.broker_Demate_User_Name or broker_details.broker_API_UID or state_record.client_code
    if not client_code or not broker_details.broker_API_KEY:
        return JsonResponse({"status": "error", "message": "Angel One credentials are incomplete."}, status=400)

    expiry = _calculate_session_expiry()
    broker_details.access_token_expiry = expiry
    auth_result = AuthService().register_existing_tokens(
        client_id=client_code,
        api_key=broker_details.broker_API_KEY,
        access_token=access_token,
        refresh_token=refresh_token,
        feed_token=feed_token,
        broker_details=broker_details,
        verify_remote=True,
    )
    if auth_result.get("status") != "success":
        return JsonResponse(
            {
                "status": "error",
                "message": auth_result.get("message", "Angel One token verification failed."),
            },
            status=400,
        )

    return redirect(state_record.frontend_redirect_url or "/dashboard/algoviewtech/user")


def angelone_callbackaa(request):
    """
    Legacy callback handler intentionally routes to the secure implementation.
    """
    return angelone_callback(request)


# =========================
# ANGEL ONE TRADE SETTINGS API
# =========================

class AngelOneSettingsView(APIView):
    """
    API to get/update Angel One broker settings.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get Angel One settings for the authenticated user."""
        try:
            broker_details = _get_angel_broker_details_for_user(request.user)
            if not broker_details:
                raise LookupError("Angel One not configured for this user")

            client_code = broker_details.broker_Demate_User_Name or broker_details.broker_API_UID
            return Response({
                "status": "success",
                "data": {
                    "client_code": client_code,
                    "buffer_percentage": float(broker_details.buffer_percentage) if broker_details.buffer_percentage else 2.5,
                    "enable_market_orders": bool(broker_details.enable_market_orders),
                    "is_configured": bool(
                        broker_details.broker_API_KEY
                        and client_code
                    ),
                    "compliance_mode": "token_only_default_limit",
                }
            })

        except LookupError:
            return Response({
                "status": "error",
                "message": "Angel One not configured for this user"
            }, status=404)

        except Exception as e:
            logger.error(f"Angel One settings get error: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=500)

    def patch(self, request):
        """Update Angel One settings."""
        try:
            broker_details = _get_angel_broker_details_for_user(request.user)
            if not broker_details:
                raise LookupError("Angel One not configured for this user")

            buffer_percentage = request.data.get("buffer_percentage")
            if buffer_percentage is not None:
                try:
                    buffer = float(buffer_percentage)
                    if 0.1 <= buffer <= 10.0:
                        broker_details.buffer_percentage = buffer
                    else:
                        return Response({
                            "status": "error",
                            "message": "Buffer percentage must be between 0.1 and 10.0"
                        }, status=400)
                except ValueError:
                    return Response({
                        "status": "error",
                        "message": "Invalid buffer percentage value"
                    }, status=400)

            if "enable_market_orders" in request.data:
                broker_details.enable_market_orders = _parse_bool(request.data.get("enable_market_orders"))

            broker_details.save(update_fields=["buffer_percentage", "enable_market_orders"])

            return Response({
                "status": "success",
                "message": "Settings updated successfully",
                "data": {
                    "buffer_percentage": float(broker_details.buffer_percentage),
                    "enable_market_orders": broker_details.enable_market_orders,
                    "compliance_mode": "limit_default_market_optional",
                }
            })

        except LookupError:
            return Response({
                "status": "error",
                "message": "Angel One not configured for this user"
            }, status=404)

        except Exception as e:
            logger.error(f"Angel One settings update error: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=500)


# =========================
# ANGEL ONE TOKEN STATUS API
# =========================

class AngelOneTokenStatusView(APIView):
    """
    Check Angel One token validity and expiry.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get token status for the authenticated user's Angel One account."""
        try:
            from main.angleapi_upgraded import get_token_details

            broker_details = _get_angel_broker_details_for_user(request.user)
            if not broker_details:
                raise LookupError("Angel One not configured for this user")

            token_info = get_token_details(broker_details)

            return Response({
                "status": "success",
                "data": token_info
            })

        except LookupError:
            return Response({
                "status": "error",
                "message": "Angel One not configured for this user"
            }, status=404)

        except Exception as e:
            logger.error(f"Angel One token status error: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=500)


# =========================
# ANGEL ONE LOGOUT API
# =========================

class AngelOneLogoutView(APIView):
    """
    Logout from Angel One and clear session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Logout from Angel One."""
        try:
            from main.angleapi_upgraded import angel_one_logout

            broker_details = _get_angel_broker_details_for_user(request.user)
            if not broker_details:
                raise LookupError("Angel One not configured for this user")

            angel_one_logout(
                client_code=broker_details.get_canonical_client_code(),
                api_key=broker_details.broker_API_KEY
            )

            broker_details.clear_session_tokens()
            broker_details.mark_broker_logout()
            broker_details.request_token = None
            broker_details.save(
                update_fields=[
                    "encrypted_access_token",
                    "encrypted_refresh_token",
                    "encrypted_feed_token",
                    "access_token_expiry",
                    "isTokenExpired",
                    "broker_last_logout_at",
                    "request_token",
                ]
            )

            return Response({
                "status": "success",
                "message": "Logged out from Angel One successfully"
            })

        except LookupError:
            return Response({
                "status": "error",
                "message": "Angel One not configured for this user"
            }, status=404)

        except Exception as e:
            logger.error(f"Angel One logout error: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=500)


# =========================
# HELPER FUNCTIONS
# =========================

def place_angel_one_trade(request_data, user, broker_details):
    """
    Helper function to place Angel One trade with client-level execution settings.

    This function integrates with the upgraded angleapi_upgraded module
    and uses the user's configured buffer percentage.
    """
    try:
        from main.angleapi_upgraded import place_angel_one_order

        symbol = request_data.get("symbol")
        strike = request_data.get("strike")
        option_type = request_data.get("option_type")
        quantity = request_data.get("quantity")
        transaction_type = request_data.get("transaction_type", "BUY")
        order_type = request_data.get("order_type", "LIMIT")

        if not all([symbol, strike, option_type, quantity]):
            return {
                "status": "error",
                "message": "Missing required trade parameters"
            }

        requested_buffer = request_data.get("buffer_percentage")
        if requested_buffer is None:
            buffer_percentage = float(broker_details.buffer_percentage) if broker_details.buffer_percentage else 2.5
        else:
            buffer_percentage = requested_buffer

        result = place_angel_one_order(
            broker_details=broker_details,
            symbol=symbol,
            strike=str(strike),
            option_type=option_type,
            quantity=int(quantity),
            transaction_type=transaction_type.upper(),
            order_type=order_type.upper(),
            price=request_data.get("price"),
            buffer_percentage=buffer_percentage,
            product_type=request_data.get("product_type", "INTRADAY"),
            exchange=request_data.get("exchange", "NFO"),
            request_id=request_data.get("request_id"),
        )

        if result.get("status") == "success":
            result["buffer_percentage_used"] = float(buffer_percentage)
            result["order_params"] = result.get("order_params", {})
            result["order_params"]["buffer_percentage"] = float(buffer_percentage)
            result["compliance_mode"] = "limit_default_market_optional"

        return result

    except Exception as e:
        logger.error(f"Angel One trade error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
