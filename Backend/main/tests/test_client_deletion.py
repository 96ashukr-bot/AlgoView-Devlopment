from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from main.models import ClientAgreementAcceptance, LegalAgreement, User


class ClientDeletionTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="deletion-admin@example.com",
            firstName="Deletion",
            lastName="Admin",
            phoneNumber="9000000001",
            password="Pass@123",
            is_superuser=True,
        )
        self.client_user = User.objects.create_user(
            email="deletion-client@example.com",
            firstName="Deletion",
            lastName="Client",
            phoneNumber="9000000002",
            password="Pass@123",
            type_of_user="is_client",
            is_client="True",
        )
        self.agreement = LegalAgreement.objects.create(
            title="Test agreement",
            version="deletion-test-v1",
            content="Test legal terms.",
            is_active=True,
            created_by=self.admin,
        )
        self.acceptance = ClientAgreementAcceptance.objects.create(
            client=self.client_user,
            agreement=self.agreement,
            agreement_version=self.agreement.version,
            terms_version_hash=self.agreement.content_hash,
            client_name="Deletion Client",
            client_email=self.client_user.email,
            client_mobile=self.client_user.phoneNumber,
            accepted_at=timezone.now(),
        )
        self.client.force_authenticate(self.admin)

    def test_delete_client_preserves_legal_acceptance_snapshot(self):
        response = self.client.delete(reverse("delete-client", args=[self.client_user.id]))

        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(id=self.client_user.id).exists())

        self.acceptance.refresh_from_db()
        self.assertIsNone(self.acceptance.client_id)
        self.assertEqual(self.acceptance.client_email, "deletion-client@example.com")
        self.assertEqual(self.acceptance.client_name, "Deletion Client")
