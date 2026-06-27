from django.test import TestCase
from rest_framework.test import APIClient

from main.models import Role, User


class SubadminClientAccessTests(TestCase):
    def setUp(self):
        subadmin_role, _ = Role.objects.get_or_create(name="Sub-Admin", defaults={"status": "active"})
        client_role, _ = Role.objects.get_or_create(name="Client", defaults={"status": "active"})
        self.subadmin = User.objects.create_user(
            email="subadmin-client-list@example.com",
            firstName="Sub",
            lastName="Admin",
            phoneNumber="9000000001",
            password="Pass@123",
            role=subadmin_role,
        )
        self.assigned_client = User.objects.create_user(
            email="assigned-client@example.com",
            firstName="Assigned",
            lastName="Client",
            phoneNumber="9000000002",
            password="Pass@123",
            role=client_role,
            type_of_user="is_client",
            is_client=True,
            assigned_client=self.subadmin,
        )
        self.other_client = User.objects.create_user(
            email="other-client@example.com",
            firstName="Other",
            lastName="Client",
            phoneNumber="9000000003",
            password="Pass@123",
            role=client_role,
            type_of_user="is_client",
            is_client=True,
        )
        self.api_client = APIClient()
        self.api_client.force_authenticate(self.subadmin)

    def test_subadmin_can_list_only_assigned_clients(self):
        response = self.api_client.get("/api/get-client-list/")

        self.assertEqual(response.status_code, 200)
        client_ids = {item["id"] for item in response.data["results"]}
        self.assertIn(self.assigned_client.id, client_ids)
        self.assertNotIn(self.other_client.id, client_ids)

    def test_subadmin_cannot_create_clients(self):
        response = self.api_client.post("/api/create-client/", {}, format="json")

        self.assertEqual(response.status_code, 403)
