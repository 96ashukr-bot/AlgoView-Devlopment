from django.contrib.auth.tokens import default_token_generator
from django.test import RequestFactory, TestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIRequestFactory

from main.models import User
from main.serializers import ChangePasswordSerializer
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
