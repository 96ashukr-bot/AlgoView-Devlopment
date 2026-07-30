from unittest import mock

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.utils import timezone

from main.models import License, Role, User, get_business_local_date
from main.serializers import CustomLoginSerializer


class ClientServiceDateTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="User", status=Role.ACTIVE)
        self.live_license = License.objects.create(name="Live", status=True, period="months")

    def _client(self, email, *, start_date, end_date):
        return User.objects.create_user(
            email=email,
            firstName="Service",
            lastName="Client",
            phoneNumber=email.split("@", 1)[0][-10:].rjust(10, "9"),
            password="Pass@1234",
            role=self.role,
            type_of_user="is_client",
            is_client="true",
            external_user="true",
            client_status=True,
            is_enable=True,
            license=self.live_license,
            to_month=1,
            start_date_client=start_date,
            end_date_client=end_date,
        )

    def test_service_start_date_does_not_move_on_normal_save(self):
        start_date = timezone.datetime(2026, 7, 1).date()
        end_date = timezone.datetime(2026, 8, 1).date()
        client = self._client("stable-start@example.com", start_date=start_date, end_date=end_date)

        client.firstName = "Updated"
        client.save()
        client.refresh_from_db()

        self.assertEqual(client.start_date_client, start_date)
        self.assertEqual(client.end_date_client, end_date)

    def test_expired_live_license_renewal_uses_renewal_date(self):
        today = get_business_local_date()
        original_start = today - timezone.timedelta(days=90)
        expired_end = today - timezone.timedelta(days=2)
        client = self._client(
            "expired-renewal@example.com",
            start_date=original_start,
            end_date=expired_end,
        )

        client.to_month = 2
        client.save()
        client.refresh_from_db()

        self.assertEqual(client.start_date_client, original_start)
        self.assertEqual(
            client.end_date_client,
            today + relativedelta(months=2),
        )
        self.assertFalse(client.client_expiry_status)

    @mock.patch("main.serializers.EmailService.send_login_email_otp")
    def test_client_can_login_on_service_end_date_ist(self, mock_send_otp):
        today = get_business_local_date()
        client = self._client("end-today@example.com", start_date=today, end_date=today)

        data = CustomLoginSerializer(data={"email": client.email, "password": "Pass@1234"})

        self.assertTrue(data.is_valid(), data.errors)
        mock_send_otp.assert_called_once()

    def test_client_cannot_login_after_service_end_date_ist(self):
        yesterday = get_business_local_date() - timezone.timedelta(days=1)
        client = self._client("expired-client@example.com", start_date=yesterday, end_date=yesterday)

        data = CustomLoginSerializer(data={"email": client.email, "password": "Pass@1234"})

        self.assertFalse(data.is_valid())
        self.assertIn("expired", str(data.errors).lower())
