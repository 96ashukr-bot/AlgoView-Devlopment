from django.test import TestCase
from rest_framework.test import APIClient
from unittest import mock

from main.models import Role, User


class SubadminClientAccessTests(TestCase):
    def setUp(self):
        subadmin_role, _ = Role.objects.get_or_create(name="Sub-Admin", defaults={"status": "active"})
        client_role, _ = Role.objects.get_or_create(name="Client", defaults={"status": "active"})
        admin_role, _ = Role.objects.get_or_create(name="Admin", defaults={"status": "active"})
        self.subadmin = User.objects.create_user(
            email="subadmin-client-list@example.com",
            firstName="Sub",
            lastName="Admin",
            phoneNumber="9000000001",
            password="Pass@123",
            role=subadmin_role,
        )
        self.other_subadmin = User.objects.create_user(
            email="other-subadmin@example.com",
            firstName="Other",
            lastName="Subadmin",
            phoneNumber="9000000004",
            password="Pass@123",
            role=subadmin_role,
        )
        self.admin = User.objects.create_user(
            email="client-list-admin@example.com",
            firstName="Main",
            lastName="Admin",
            phoneNumber="9000000005",
            password="Pass@123",
            role=admin_role,
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

    def test_subadmin_assignment_dropdown_contains_only_self(self):
        response = self.api_client.get("/api/get-subadmins-list/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [self.subadmin.id])

    @mock.patch("main.views.EmailService.send_password_email")
    def test_subadmin_created_client_is_forced_to_creator_and_visible_to_admin(self, _send_email):
        response = self.api_client.post(
            "/api/create-client/",
            {
                "email": "created-by-subadmin@example.com",
                "fullName": "Created Client",
                "userName": "created-client",
                "phoneNumber": "9000000006",
                "assigned_client": self.other_subadmin.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        created_client = User.objects.get(email="created-by-subadmin@example.com")
        self.assertEqual(created_client.assigned_client_id, self.subadmin.id)
        self.assertEqual(created_client.created_by_id, self.subadmin.id)

        creator_response = self.api_client.get("/api/get-client-list/")
        creator_ids = {item["id"] for item in creator_response.data["results"]}
        self.assertIn(created_client.id, creator_ids)

        self.api_client.force_authenticate(self.other_subadmin)
        other_subadmin_response = self.api_client.get("/api/get-client-list/")
        other_subadmin_ids = {item["id"] for item in other_subadmin_response.data["results"]}
        self.assertNotIn(created_client.id, other_subadmin_ids)

        self.api_client.force_authenticate(self.admin)
        admin_response = self.api_client.get("/api/get-client-list/")
        admin_ids = {item["id"] for item in admin_response.data["results"]}
        self.assertIn(created_client.id, admin_ids)

    def test_client_user_cannot_create_clients(self):
        self.api_client.force_authenticate(self.assigned_client)
        response = self.api_client.post("/api/create-client/", {}, format="json")

        self.assertEqual(response.status_code, 403)
