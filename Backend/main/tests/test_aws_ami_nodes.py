from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from django.utils import timezone

from main.models import AwsAmiNodeClaim, Broker, ClientBrokerdetails, ExecutionNode, User
from main.services.execution_nodes import get_execution_node_for_client
from main.services.execution_router import route_order_to_execution_node
from main.services.proxy_utils import build_requests_proxy_config


@override_settings(
    AWS_AMI_NODE_ENABLED=True,
    AWS_AMI_ALLOWED_IDS={"ami-algoview-arm64"},
    AWS_AMI_ALLOWED_REGIONS={"ap-south-1"},
    AWS_AMI_PROXY_PORT=3128,
    AWS_AMI_CLAIM_TTL_SECONDS=1800,
    AWS_AMI_TRUSTED_PROXY_IPS={"127.0.0.1", "::1"},
)
class AwsAmiNodeOnboardingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email="aws-node-client@example.com",
            firstName="AWS",
            lastName="Client",
            phoneNumber="9000000001",
            password="Pass@123",
            is_enable=True,
        )
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def _claim(self, public_ip="13.233.120.45"):
        response = self.api.post(
            "/api/client/aws-ami-node/",
            {"public_ip": public_ip, "node_name": "Client AWS Node"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        return response

    @staticmethod
    def _identity(instance_id="i-0123456789abcdef0"):
        return {
            "instanceId": instance_id,
            "imageId": "ami-algoview-arm64",
            "region": "ap-south-1",
            "accountId": "123456789012",
            "architecture": "arm64",
        }

    def test_client_can_claim_public_ipv4_without_node_secret_or_server_url(self):
        response = self._claim()

        self.assertEqual(response.data["claim"]["status"], AwsAmiNodeClaim.STATUS_PENDING)
        self.assertEqual(response.data["claim"]["public_ip"], "13.233.120.45")
        self.assertNotIn("node_secret", response.data)
        self.assertIsNone(get_execution_node_for_client(self.user))

    def test_private_ip_cannot_be_claimed(self):
        response = self.api.post(
            "/api/client/aws-ami-node/",
            {"public_ip": "172.31.1.10"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("public IPv4", response.data["detail"])

    @mock.patch("main.aws_ami_node_views.verify_registered_ami_proxy")
    @mock.patch("main.aws_ami_node_views.verify_aws_instance_identity")
    def test_approved_ami_registers_and_assigns_authenticated_proxy(self, identity_verifier, proxy_verifier):
        self._claim()
        identity_verifier.return_value = self._identity()
        proxy_verifier.return_value = {"status": "success", "message": "verified"}

        anonymous = APIClient()
        response = anonymous.post(
            "/api/node/aws-ami/register/",
            {
                "proxy_username": "av_1234567890abcdef",
                "proxy_password": "a-very-long-random-proxy-password-value",
                "agent_version": "1",
                "instance_identity_pkcs7": "signed-by-aws",
            },
            format="json",
            REMOTE_ADDR="13.233.120.45",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "activated")
        node = get_execution_node_for_client(self.user)
        self.assertIsNotNone(node)
        self.assertEqual(node.execution_type, ExecutionNode.EXECUTION_TYPE_PROXY)
        self.assertEqual(node.provider, "AWS AMI")
        self.assertEqual(str(node.ip_address), "13.233.120.45")
        self.assertEqual(node.proxy_host, "13.233.120.45")
        self.assertEqual(node.proxy_port, 3128)
        self.assertEqual(node.proxy_protocol, ExecutionNode.PROXY_PROTOCOL_HTTP)
        self.assertEqual(node.get_proxy_password(), "a-very-long-random-proxy-password-value")
        proxy_config = build_requests_proxy_config(node)
        self.assertIn("13.233.120.45:3128", proxy_config["https"])
        identity_verifier.assert_called_once_with("signed-by-aws")
        proxy_verifier.assert_called_once_with(node)

    @mock.patch("main.aws_ami_node_views.verify_registered_ami_proxy")
    @mock.patch("main.aws_ami_node_views.verify_aws_instance_identity")
    def test_registration_source_ip_must_match_claim(self, identity_verifier, proxy_verifier):
        self._claim()
        identity_verifier.return_value = self._identity()

        response = APIClient().post(
            "/api/node/aws-ami/register/",
            {
                "proxy_username": "av_1234567890abcdef",
                "proxy_password": "a-very-long-random-proxy-password-value",
                "instance_identity_pkcs7": "signed-by-aws",
            },
            format="json",
            REMOTE_ADDR="13.233.120.46",
        )

        self.assertEqual(response.status_code, 404)
        self.assertIsNone(get_execution_node_for_client(self.user))
        proxy_verifier.assert_not_called()

    @mock.patch("main.aws_ami_node_views.verify_aws_instance_identity")
    def test_invalid_aws_attestation_fails_closed(self, identity_verifier):
        from django.core.exceptions import ValidationError

        self._claim()
        identity_verifier.side_effect = ValidationError("AWS instance identity signature verification failed.")
        response = APIClient().post(
            "/api/node/aws-ami/register/",
            {
                "proxy_username": "av_1234567890abcdef",
                "proxy_password": "a-very-long-random-proxy-password-value",
                "instance_identity_pkcs7": "forged",
            },
            format="json",
            REMOTE_ADDR="13.233.120.45",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIsNone(get_execution_node_for_client(self.user))

    @mock.patch("main.aws_ami_node_views.verify_registered_ami_proxy")
    @mock.patch("main.aws_ami_node_views.verify_aws_instance_identity")
    def test_release_disables_ami_route_without_affecting_manual_proxy_logic(self, identity_verifier, proxy_verifier):
        self._claim()
        identity_verifier.return_value = self._identity()
        proxy_verifier.return_value = {"status": "success"}
        APIClient().post(
            "/api/node/aws-ami/register/",
            {
                "proxy_username": "av_1234567890abcdef",
                "proxy_password": "a-very-long-random-proxy-password-value",
                "instance_identity_pkcs7": "signed-by-aws",
            },
            format="json",
            REMOTE_ADDR="13.233.120.45",
        )
        node = get_execution_node_for_client(self.user)

        response = self.api.delete("/api/client/execution-node/", format="json")

        self.assertEqual(response.status_code, 200)
        node.refresh_from_db()
        self.assertFalse(node.is_active)
        self.assertEqual(node.status, ExecutionNode.STATUS_DISABLED)
        self.assertIsNone(get_execution_node_for_client(self.user))
        claim = AwsAmiNodeClaim.objects.get(client=self.user)
        self.assertEqual(claim.status, AwsAmiNodeClaim.STATUS_CANCELLED)
        self.assertIsNone(claim.execution_node_id)

    @mock.patch("main.services.execution_router.get_broker_adapter")
    @mock.patch("main.aws_ami_node_views.verify_registered_ami_proxy")
    @mock.patch("main.aws_ami_node_views.verify_aws_instance_identity")
    def test_activated_ami_routes_trade_through_existing_proxy_engine(self, identity_verifier, proxy_verifier, adapter_factory):
        broker = Broker.objects.create(broker_name="Angel One", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.user,
            broker_name=broker,
            broker_API_KEY="key",
            broker_Demate_User_Name="client-code",
        )
        self._claim()
        identity_verifier.return_value = self._identity()
        proxy_verifier.return_value = {"status": "success"}
        APIClient().post(
            "/api/node/aws-ami/register/",
            {
                "proxy_username": "av_1234567890abcdef",
                "proxy_password": "a-very-long-random-proxy-password-value",
                "instance_identity_pkcs7": "signed-by-aws",
            },
            format="json",
            REMOTE_ADDR="13.233.120.45",
        )
        node = get_execution_node_for_client(self.user)
        node.proxy_public_ip_verified = True
        node.proxy_last_verified_at = timezone.now()
        node.proxy_last_seen_ip = node.ip_address
        node.is_verified_with_broker = True
        node.save(update_fields=["proxy_public_ip_verified", "proxy_last_verified_at", "proxy_last_seen_ip", "is_verified_with_broker", "updated_at"])
        broker_details.refresh_from_db()

        adapter = adapter_factory.return_value
        adapter.supports_proxy = True
        adapter.validate_credentials.return_value = {"status": "success"}
        adapter.place_order.return_value = {"status": "success", "order_id": "aws-order-1"}
        result = route_order_to_execution_node(
            self.user,
            broker_details,
            {"symbol": "NIFTY", "quantity": 65, "transaction_type": "BUY", "idempotency_key": "aws-route-1"},
        )

        self.assertEqual(result["status"], "placed")
        proxy_config = adapter.place_order.call_args.kwargs["proxy_config"]
        self.assertIn("13.233.120.45:3128", proxy_config["https"])
