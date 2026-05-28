
from main.models import *
from rest_framework.views import APIView
from main.serializers import *
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from main.serializers import *#CompanyProfileSerializer
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now, timedelta
from .models import WebsocketDetails
from django.core.mail import EmailMultiAlternatives
from main.utils import get_smtp_connection
from main.angelone.services.state_service import CallbackStateService
from main.permissions import is_superadmin_user
from django.conf import settings
from urllib.parse import urlencode, urlparse, urlunparse
import secrets


class UpdateWebSocketToken(APIView):
    def put(self, request, *args, **kwargs):
        """Update the token or create a new one, and set expiry time."""
        data = request.data
        auth_token = data.get("auth_token")

        if not auth_token:
            return Response(
                {"status": "failed", "message": "Auth token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create or update the latest token
        token, created = WebsocketDetails.objects.update_or_create(
            id=WebsocketDetails.objects.order_by("-id").first().id
            if WebsocketDetails.objects.exists()
            else None,
            defaults={"Auth_token": auth_token}
        )

        # Set expiry for next day's 3:30 AM
        now_time = now()
        if now_time.hour < 3 or (now_time.hour == 3 and now_time.minute < 30):
            expiry_date = now_time.date()
        else:
            expiry_date = now_time.date() + timedelta(days=1)

        token.expiry_time = datetime.combine(expiry_date, datetime.min.time()) + timedelta(
            hours=3, minutes=30
        )

        # ✅ Forcefully update token status to active
        token.token_status = 'active'
        token.save()

        return Response(
            {
                "status": "success",
                "message": "Token updated successfully." if not created else "New token created.",
                "data": {"auth_token": token.Auth_token, "token_status": token.token_status},
            },
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
        )

class WebsocketTokenView(APIView):
    def get(self, request, *args, **kwargs):
        """Retrieve the latest valid token or mark expired ones."""
        token = WebsocketDetails.objects.order_by("-id").first()

        if token:
            # Check and update the token status
            if token.expiry_time and now() > token.expiry_time:
                token.token_status = "inactive"
                token.save()

            return Response(
                {
                    "status": "success" if token.token_status == "active" else "failed",
                    "auth_token": token.Auth_token,
                    "token_status": token.token_status,
                },
                status=status.HTTP_200_OK #if token.token_status == "active" else status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"status": "failed", "message": "No token found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    def delete(self, request, *args, **kwargs):
        """Update the token or create a new one, and set expiry time."""
        data = request.data
        auth_token = data.get("auth_token")

        if not auth_token:
            return Response(
                {"status": "failed", "message": "Auth token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token, created = WebsocketDetails.objects.update_or_create(
            id=WebsocketDetails.objects.order_by("-id").first().id
            if WebsocketDetails.objects.exists()
            else None,
            defaults={"Auth_token": auth_token, "token_status": "active"},
        )

        now_time = now()
        if now_time.hour < 3 or (now_time.hour == 3 and now_time.minute < 30):
            expiry_date = now_time.date()
        else:
            expiry_date = now_time.date() + timedelta(days=1)

        token.expiry_time = datetime.combine(expiry_date, datetime.min.time()) + timedelta(
            hours=3, minutes=30
        )
        token.save()

        return Response(
            {
                "status": "success",
                "message": "Token updated successfully." if not created else "New token created.",
                "data": {"auth_token": token.Auth_token, "token_status": token.token_status},
            },
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
        )


def _broker_callback_url():
    configured_url = getattr(settings, "REDIRECT_URL", "").strip()
    if not configured_url:
        return configured_url
    parsed = urlparse(configured_url)
    if parsed.path.rstrip("/") in {"/callback", "/auth-callback", "/callback-angelone"}:
        parsed = parsed._replace(path="/api/broker/callback/")
        return urlunparse(parsed)
    return configured_url


def _market_data_return_url(request):
    configured_frontend = getattr(settings, "FRONTEND_APP_URL", "").rstrip("/")
    origin = (request.headers.get("Origin") or "").rstrip("/")
    if not origin:
        referer = (request.headers.get("Referer") or "").strip()
        if referer:
            parsed = urlparse(referer)
            if parsed.scheme and parsed.netloc:
                origin = f"{parsed.scheme}://{parsed.netloc}"
    base = origin or configured_frontend
    return f"{base}/settings/websocket" if base else None


def _market_data_payload(credential):
    node = credential.execution_node
    return {
        "provider": credential.provider,
        "api_key": credential.api_key or "",
        "api_secret_configured": bool(credential.get_api_secret()),
        "execution_node": node.id if node else None,
        "execution_node_name": node.name if node else "",
        "is_active": bool(credential.is_active),
        "token_status": credential.token_status or "inactive",
        "token_configured": bool(credential.get_access_token_secure()),
        "access_token_expiry": credential.access_token_expiry.isoformat() if credential.access_token_expiry else None,
        "tokenCreatedAt": credential.tokenCreatedAt.isoformat() if credential.tokenCreatedAt else None,
    }


class MarketDataUpstoxSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def _require_superadmin(self, request):
        if not is_superadmin_user(request.user):
            return Response({"detail": "Only superadmin can manage market data settings."}, status=status.HTTP_403_FORBIDDEN)
        return None

    def get(self, request, *args, **kwargs):
        denied = self._require_superadmin(request)
        if denied:
            return denied
        credential, _ = MarketDataCredential.objects.get_or_create(provider=MarketDataCredential.PROVIDER_UPSTOX)
        if credential.access_token_expiry and credential.access_token_expiry <= now():
            credential.token_status = "inactive"
            credential.save(update_fields=["token_status", "updated_at"])
        return Response({"status": "success", "data": _market_data_payload(credential)})

    def put(self, request, *args, **kwargs):
        denied = self._require_superadmin(request)
        if denied:
            return denied
        credential, _ = MarketDataCredential.objects.get_or_create(provider=MarketDataCredential.PROVIDER_UPSTOX)
        api_key = str(request.data.get("api_key") or "").strip()
        api_secret = request.data.get("api_secret")
        is_active = request.data.get("is_active", True)

        if not api_key:
            return Response({"status": "failed", "message": "Upstox API Key is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not credential.get_api_secret() and not api_secret:
            return Response({"status": "failed", "message": "Upstox API Secret Key is required."}, status=status.HTTP_400_BAD_REQUEST)

        credential.api_key = api_key
        if api_secret:
            credential.set_api_secret(str(api_secret))
        credential.is_active = str(is_active).lower() not in {"false", "0", "no", "off"}
        credential.updated_by = request.user
        credential.save()
        return Response({"status": "success", "message": "Market data account saved.", "data": _market_data_payload(credential)})


class MarketDataUpstoxConnectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not is_superadmin_user(request.user):
            return Response({"detail": "Only superadmin can generate the market data token."}, status=status.HTTP_403_FORBIDDEN)
        credential = MarketDataCredential.objects.filter(provider=MarketDataCredential.PROVIDER_UPSTOX).select_related("execution_node").first()
        if not credential or not credential.api_key or not credential.get_api_secret():
            return Response({"status": "failed", "message": "Save Upstox API Key and Secret first."}, status=status.HTTP_400_BAD_REQUEST)

        state = secrets.token_urlsafe(24)
        CallbackStateService().create(
            state=state,
            user_id=request.user.id,
            broker_details_id=0,
            client_code="market-data-upstox",
            frontend_redirect_url=_market_data_return_url(request),
        )
        params = {
            "response_type": "code",
            "client_id": credential.api_key,
            "redirect_uri": _broker_callback_url(),
            "state": state,
        }
        return Response({
            "status": "success",
            "redirect_url": f"https://api.upstox.com/v2/login/authorization/dialog?{urlencode(params)}",
        })
class WebsocketTokenViewww(APIView):
    def get(self, request, *args, **kwargs):
        """Retrieve the latest valid token from the database."""
        token = WebsocketDetails.objects.order_by("-id").first()

        if token and token.token_status not in ["inactive", "not valid"]:
            return Response(
                {"status": "success", "auth_token": token.Auth_token, "token_status": token.token_status},
                status=status.HTTP_200_OK
            )
        return Response(
            {"status": "failed", "message": "No valid token found."},
            status=status.HTTP_404_NOT_FOUND
        )

    def put(self, request, *args, **kwargs):
        """Update or create the token when it's expired or unauthorized."""
        data = request.data
        auth_token = data.get("auth_token")
     
        if not auth_token:
            return Response(
                {"status": "failed", "message": "Auth token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update if exists or create a new entry if not also updtae token status 
        token, created = WebsocketDetails.objects.update_or_create(
            id=WebsocketDetails.objects.order_by("-id").first().id if WebsocketDetails.objects.exists() else None,
            defaults={"Auth_token": auth_token, "token_status": token_status},
        )
        # Calculate Expiry Time (Fixed at 3:30 AM the Next Day)
        now_time = now()
        expiry_date = now_time.date() if now_time.hour < 3 or (now_time.hour == 3 and now_time.minute < 30) else now_time.date() + timedelta(days=1)
        expiry_time = datetime.combine(expiry_date, datetime.min.time()) + timedelta(hours=3, minutes=30)
        print("expiry_time>>>>",expiry_time)
        token_status=WebsocketDetails.save()

        return Response(
            {
                "status": "success",
                "message": "Token updated successfully." if not created else "New token created.",
                "data": {"auth_token": token.Auth_token, "token_status": token.token_status},
            },
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED
        )

def _company_profile_has_branding_data(company):
    if not company:
        return False
    fields = (
        "company_name",
        "company_email",
        "company_support_email",
        "company_phone_number",
        "company_logo",
        "company_favicon",
        "login_link",
        "help_center_link",
        "company_website",
        "company_sender_name",
    )
    return any(bool(getattr(company, field, None)) for field in fields)


def _get_company_profile_for_user(user, *, create=False):
    user_company = CompanyProfileDetails.objects.filter(user=user).first()
    role_name = getattr(getattr(user, "role", None), "name", "") or ""
    is_super_admin = role_name.lower() == "super-admin" or getattr(user, "is_superuser", False)

    if user_company and (not is_super_admin or _company_profile_has_branding_data(user_company)):
        return user_company

    if is_super_admin:
        canonical_company = (
            CompanyProfileDetails.objects.filter(user__role__name__iexact="Super-Admin")
            .exclude(company_email__isnull=True)
            .exclude(company_email="")
            .order_by("id")
            .first()
            or CompanyProfileDetails.objects.exclude(company_email__isnull=True)
            .exclude(company_email="")
            .order_by("id")
            .first()
            or CompanyProfileDetails.objects.exclude(company_logo="")
            .order_by("id")
            .first()
            or user_company
        )
        if canonical_company:
            return canonical_company

    if user_company:
        return user_company
    if create:
        return CompanyProfileDetails.objects.create(user=user)
    return None


class CompanyProfileDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user = request.user if request.user and request.user.is_authenticated else None
        """Retrieve a single company by ID or all companies if no ID is provided."""
        try:
            company = _get_company_profile_for_user(user) if user else None
            if company is None:
                company = (
                    CompanyProfileDetails.objects.filter(user__role__name__iexact="Super-Admin")
                    .exclude(company_logo="")
                    .order_by("id")
                    .first()
                    or CompanyProfileDetails.objects.exclude(company_logo="")
                    .order_by("id")
                    .first()
                    or CompanyProfileDetails.objects.order_by("id").first()
                )
            if company is None:
                raise CompanyProfileDetails.DoesNotExist
            serializer = CompanyProfileSerializer(company)
            return Response(
                {"status": "success", "message": "Company retrieved successfully.", "data": serializer.data},
                status=status.HTTP_200_OK
            )

        except CompanyProfileDetails.DoesNotExist:
            return Response(
                {"status": "failed", "message": "Company not found.", "data": None},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": "An unexpected error occurred.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class CompanyProfileUpdateView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def put(self, request, *args, **kwargs):
        """
        Retrieve or create the company profile for the authenticated user.
        If it exists, update the provided fields.
        """
        user = request.user

        company = _get_company_profile_for_user(user, create=True)
        created = company.created_at == company.updated_at if hasattr(company, "created_at") else False

        serializer = CompanyProfileSerializer(company, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            message = "Company profile created successfully." if created else "Company details updated successfully."
            return Response(
                {"status": "success", "message": message, "data": serializer.data},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )

        return Response(
            {"status": "failed", "message": "Validation error.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    
class CompanySmtpDetailView(APIView):    
    def get(self, request, *args, **kwargs):
        try:
            user=request.user
            # smtp_details=None
            smtp_details = CompanySmtpDetails.objects.get(user=user)
            serializer = CompanySmtpDetailsSerializer(smtp_details)
            return Response({
                "status": "success",
                "message": "SMTP configuration retrieved successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except CompanySmtpDetails.DoesNotExist:
            return Response({
                "status": "failed",
                "message": "SMTP configuration not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class CompanySmtpUpdateView(APIView):             
    def put(self, request, *args, **kwargs):
        try:
            user=request.user
            smtp_details, created = CompanySmtpDetails.objects.get_or_create(user=user)
            serializer = CompanySmtpSerializer(smtp_details, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": "success",
                    "message": "SMTP configuration updated successfully.",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                "status": "failed",
                "message": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except CompanySmtpDetails.DoesNotExist:
            return Response({
                "status": "failed",
                "message": "SMTP configuration not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompanySmtpTestView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            smtp_details = CompanySmtpDetails.objects.get(user=request.user)
        except CompanySmtpDetails.DoesNotExist:
            return Response({
                "status": "failed",
                "message": "SMTP configuration not found.",
            }, status=status.HTTP_404_NOT_FOUND)

        connection = get_smtp_connection(smtp_details=smtp_details, open_connection=True)
        if not connection:
            return Response({
                "status": "failed",
                "message": "SMTP connection could not be established. Please verify host, port, username, and password.",
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            recipient = request.data.get("recipient") or smtp_details.default_from_email or smtp_details.email_host_user
            sender = smtp_details.default_from_email or smtp_details.email_host_user
            email_message = EmailMultiAlternatives(
                "AlgoView SMTP Test",
                "SMTP test email from AlgoView. If you received this, your email account is working.",
                sender,
                [recipient],
                connection=connection,
            )
            email_message.send()
            return Response({
                "status": "success",
                "message": f"SMTP test email sent to {recipient}.",
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({
                "status": "failed",
                "message": f"SMTP test failed: {str(exc)}",
            }, status=status.HTTP_400_BAD_REQUEST)
        finally:
            try:
                connection.close()
            except Exception:
                pass

   
