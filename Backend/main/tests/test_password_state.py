from datetime import timedelta

from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIRequestFactory

from main.legal_middleware import LegalAgreementAcceptanceMiddleware
from main.models import LegalAgreement, OTP, Role, User
from main.serializers import ChangePasswordSerializer, OTPVerifySerializer
from main.views import PasswordResetConfirmView


class PasswordStateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="password-state@example.com",
            firstName="Password",
            lastName="State",
            phoneNumber="9999999999",
            password="Temporary@1234",
            is_password_temporary=True,
            is_new_password=False,
        )

    def test_first_password_change_marks_password_as_permanent(self):
        request = RequestFactory().post("/api/change-password/")
        request.user = self.user
        serializer = ChangePasswordSerializer(
            data={
                "OldPassword": "Temporary@1234",
                "NewPassword": "Permanent@1234",
                "ConfirmNewPassword": "Permanent@1234",
            },
            context={"request": request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Permanent@1234"))
        self.assertTrue(self.user.is_new_password)
        self.assertFalse(self.user.is_password_temporary)

    def test_password_change_rejects_an_incorrect_old_password(self):
        request = RequestFactory().post("/api/change-password/")
        request.user = self.user
        serializer = ChangePasswordSerializer(
            data={
                "OldPassword": "Incorrect@1234",
                "NewPassword": "Permanent@1234",
                "ConfirmNewPassword": "Permanent@1234",
            },
            context={"request": request},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("OldPassword", serializer.errors)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Temporary@1234"))

    def test_password_reset_marks_password_as_permanent(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        request = APIRequestFactory().post(
            "/api/password-reset-confirm/",
            {
                "uidb64": uid,
                "token": token,
                "NewPassword": "Reset@1234",
                "ConfirmPassword": "Reset@1234",
            },
            format="json",
        )

        response = PasswordResetConfirmView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Reset@1234"))
        self.assertTrue(self.user.is_new_password)
        self.assertFalse(self.user.is_password_temporary)

    def test_change_password_is_allowed_before_agreement_acceptance(self):
        role, _ = Role.objects.get_or_create(name="Client", defaults={"status": Role.ACTIVE})
        self.user.role = role
        self.user.type_of_user = "is_client"
        self.user.is_client = True
        self.user.save(update_fields=["role", "type_of_user", "is_client"])
        LegalAgreement.objects.create(
            title="Password setup agreement",
            version="password-setup-v1",
            content="Terms accepted after initial password setup.",
            is_active=True,
        )
        request = RequestFactory().post("/api/change-password/")
        request.user = self.user
        middleware = LegalAgreementAcceptanceMiddleware(lambda _request: HttpResponse(status=204))

        response = middleware(request)

        self.assertEqual(response.status_code, 204)

    def test_otp_verification_does_not_finalize_temporary_password(self):
        otp = OTP.objects.create(
            user=self.user,
            otp_code="123456",
            is_verified=False,
            expires_at=timezone.now() + timedelta(minutes=2),
        )
        serializer = OTPVerifySerializer(data={"email": self.user.email, "otp_code": otp.otp_code})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_password_temporary)
        self.assertFalse(self.user.is_new_password)
