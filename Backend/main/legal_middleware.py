from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication

from main.legal_services import client_has_accepted_active_agreement, get_active_agreement
from main.permissions import is_end_user


class LegalAgreementAcceptanceMiddleware:
    API_PREFIX = "/api/"
    ALLOWED_PATHS = (
        "/api/login/",
        "/api/logout/",
        "/api/verify-otp/",
        "/api/resend-otp/",
        "/api/token/refresh/",
        "/api/change-password/",
        "/api/password-reset-request/",
        "/api/password-reset-confirm/",
        "/api/legal/current-agreement/",
        "/api/legal/my-acceptance-status/",
        "/api/legal/accept-agreement/",
        "/api/legal/my-agreement/",
        "/api/get-company-profile/",
    )
    ALLOWED_PREFIXES = (
        "/api/broker/callback/",
        "/api/auth-callback/",
        "/api/payment-callback/",
        "/api/node/",
        "/api/v1/algo/webhook/",
        "/api/v2/algo/webhook/",
    )

    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authentication = JWTAuthentication()

    def __call__(self, request):
        path = request.path
        if not path.startswith(self.API_PREFIX) or self._is_allowed_path(path):
            return self.get_response(request)

        agreement = get_active_agreement()
        if not agreement:
            return self.get_response(request)

        user = self._get_user(request)
        if not user or not getattr(user, "is_authenticated", False) or not is_end_user(user):
            return self.get_response(request)

        if client_has_accepted_active_agreement(user):
            return self.get_response(request)

        return JsonResponse(
            {
                "detail": "Latest legal agreement acceptance is required before using the platform.",
                "code": "LEGAL_AGREEMENT_REQUIRED",
                "redirect_url": "/terms-acceptance",
                "agreement_version": agreement.version,
                "terms_version_hash": agreement.content_hash,
            },
            status=451,
        )

    def _is_allowed_path(self, path):
        return path in self.ALLOWED_PATHS or any(path.startswith(prefix) for prefix in self.ALLOWED_PREFIXES)

    def _get_user(self, request):
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            return user
        try:
            auth_result = self.jwt_authentication.authenticate(request)
        except Exception:
            return None
        if not auth_result:
            return None
        user, _token = auth_result
        request.user = user
        return user
