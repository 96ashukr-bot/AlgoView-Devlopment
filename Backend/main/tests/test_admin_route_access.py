from django.urls import reverse
from rest_framework.test import APITestCase

from main.models import CompanySmtpDetails, User


class AdminRouteAccessTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="route-admin@example.com",
            firstName="Route",
            lastName="Admin",
            phoneNumber="9000000101",
            password="Pass@123",
            is_superuser=True,
            is_staff=True,
        )
        self.client_user = User.objects.create_user(
            email="route-client@example.com",
            firstName="Route",
            lastName="Client",
            phoneNumber="9000000102",
            password="Pass@123",
            type_of_user="is_client",
            is_client="True",
        )
        CompanySmtpDetails.objects.create(
            user=self.admin,
            email_host="smtp.example.com",
            email_port=587,
            email_host_user="admin@example.com",
            default_from_email="admin@example.com",
        )

    def test_client_cannot_access_admin_client_list(self):
        self.client.force_authenticate(self.client_user)

        response = self.client.get(reverse("get-client"))

        self.assertEqual(response.status_code, 403)

    def test_client_cannot_access_company_smtp_settings(self):
        self.client.force_authenticate(self.client_user)

        detail_response = self.client.get(reverse("get-company-smtp-detail"))
        update_response = self.client.put(
            reverse("put-company-smtp-detail"),
            {"email_host": "smtp.attacker.example.com"},
            format="json",
        )
        test_response = self.client.post(
            reverse("test-company-smtp"),
            {"to_email": "client@example.com"},
            format="json",
        )

        self.assertEqual(detail_response.status_code, 403)
        self.assertEqual(update_response.status_code, 403)
        self.assertEqual(test_response.status_code, 403)

    def test_admin_can_still_access_client_list_and_smtp_settings(self):
        self.client.force_authenticate(self.admin)

        client_list_response = self.client.get(reverse("get-client"))
        smtp_response = self.client.get(reverse("get-company-smtp-detail"))

        self.assertEqual(client_list_response.status_code, 200)
        self.assertEqual(smtp_response.status_code, 200)
