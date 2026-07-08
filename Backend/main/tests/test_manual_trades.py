from datetime import timedelta
from unittest import mock

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from main.models import (
    Broker, ClientBrokerdetails, ClientTradeSetting, ExecutionNode, GroupService,
    ManualTradeBatch, ManualTradeResult, Role, Segment, SubSegment, User,
)


class ManualTradeTests(APITestCase):
    def setUp(self):
        admin_role, _ = Role.objects.get_or_create(name="Admin")
        client_role, _ = Role.objects.get_or_create(name="Client")
        self.admin = User.objects.create_user(
            email="manual-admin@example.com", firstName="Manual", lastName="Admin",
            phoneNumber="9330000001", password="Pass@123", role=admin_role,
        )
        segment = Segment.objects.create(name="Index Options", short_name="OPT")
        subsegment = SubSegment.objects.create(segment=segment, name="NIFTY", short_name="NIFTY", Exchange="NFO")
        self.group = GroupService.objects.create(
            group_name="Manual Group", segment=segment, json_data=[{"ScriptName": "NIFTY"}],
        )
        self.client_user = User.objects.create_user(
            email="manual-client@example.com", firstName="Manual", lastName="Client",
            phoneNumber="9330000002", password="Pass@123", role=client_role,
            Group_service=self.group, type_of_user="is_client", is_client="True",
        )
        setting = ClientTradeSetting.objects.create(
            client=self.client_user, segment=segment, sub_segment=subsegment, symbol="NIFTY",
            group_service=self.group.group_name, broker="Zerodha", product_type="INTRADAY",
            order_type="LIMIT", quantity=50, expiry_date=timezone.now() + timedelta(days=7),
            is_tread_status=True,
        )
        broker = Broker.objects.create(broker_name="Zerodha", is_active=True)
        node = ExecutionNode.objects.create(
            name="Manual Node", ip_address="192.0.2.101", assigned_client=self.client_user,
            status=ExecutionNode.STATUS_ASSIGNED, execution_type=ExecutionNode.EXECUTION_TYPE_VPS_NODE,
            server_url="https://node.example.test", is_active=True, is_verified_with_broker=True,
        )
        ClientBrokerdetails.objects.create(
            client=self.client_user, broker_name=broker, broker_API_KEY="api-key",
            access_token="access-token", execution_node=node, isTokenExpired=False,
            access_token_expiry=timezone.now() + timedelta(days=1),
        )
        self.setting = setting
        self.client.force_authenticate(self.admin)

    def test_preview_uses_saved_client_settings(self):
        response = self.client.post(reverse("manual-trade-preview"), {
            "group_service_id": self.group.id, "symbol": "NIFTY",
            "action": "BUY_CE", "strike_price": "22900",
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["preview_count"], 1)
        self.assertEqual(response.data["eligible_count"], 1)
        result = response.data["results"][0]
        self.assertEqual(result["client_id"], self.client_user.id)
        self.assertEqual(result["request_snapshot"]["quantity"], 50)
        self.assertEqual(result["request_snapshot"]["order_type"], "LIMIT")

    @mock.patch("main.tasks.process_manual_trade_batch_task.delay")
    def test_execute_can_only_be_confirmed_once(self, mock_delay):
        mock_delay.return_value.id = "task-1"
        preview = self.client.post(reverse("manual-trade-preview"), {
            "group_service_id": self.group.id, "symbol": "NIFTY",
            "action": "BUY_PE", "strike_price": "22800",
        }, format="json")
        batch_id = preview.data["id"]

        first = self.client.post(reverse("manual-trade-execute", args=[batch_id]), {}, format="json")
        second = self.client.post(reverse("manual-trade-execute", args=[batch_id]), {}, format="json")

        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(mock_delay.call_count, 1)
        self.assertEqual(ManualTradeBatch.objects.get(pk=batch_id).status, ManualTradeBatch.STATUS_QUEUED)
        self.assertEqual(ManualTradeResult.objects.filter(batch_id=batch_id, status=ManualTradeResult.STATUS_PENDING).count(), 1)

    @mock.patch("main.tasks.process_manual_trade_batch_task.delay")
    def test_execute_only_queues_selected_clients(self, mock_delay):
        mock_delay.return_value.id = "task-selected"
        second_client = User.objects.create_user(
            email="manual-client-two@example.com", firstName="Second", lastName="Client",
            phoneNumber="9330000003", password="Pass@123", role=self.client_user.role,
            Group_service=self.group, type_of_user="is_client", is_client="True",
        )
        second_setting = ClientTradeSetting.objects.create(
            client=second_client, segment=self.setting.segment, sub_segment=self.setting.sub_segment,
            symbol="NIFTY", group_service=self.group.group_name, broker="Zerodha",
            product_type="INTRADAY", order_type="LIMIT", quantity=25,
            expiry_date=timezone.now() + timedelta(days=7), is_tread_status=True,
        )
        node = ExecutionNode.objects.create(
            name="Second Node", ip_address="192.0.2.102", assigned_client=second_client,
            status=ExecutionNode.STATUS_ASSIGNED, execution_type=ExecutionNode.EXECUTION_TYPE_VPS_NODE,
            server_url="https://node-two.example.test", is_active=True, is_verified_with_broker=True,
        )
        ClientBrokerdetails.objects.create(
            client=second_client, broker_name=Broker.objects.filter(broker_name="Zerodha").first(),
            broker_API_KEY="api-key-two", access_token="access-token-two", execution_node=node,
            isTokenExpired=False, access_token_expiry=timezone.now() + timedelta(days=1),
        )
        preview = self.client.post(reverse("manual-trade-preview"), {
            "group_service_id": self.group.id, "symbol": "NIFTY",
            "action": "BUY_CE", "strike_price": "22950",
        }, format="json")

        response = self.client.post(
            reverse("manual-trade-execute", args=[preview.data["id"]]),
            {"client_ids": [second_client.id]}, format="json",
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["eligible_count"], 1)
        self.assertEqual(response.data["skipped_count"], 1)
        self.assertEqual(
            ManualTradeResult.objects.get(batch_id=preview.data["id"], client=self.client_user).status,
            ManualTradeResult.STATUS_SKIPPED,
        )
        self.assertEqual(second_setting.manual_trade_results.get(batch_id=preview.data["id"]).status, ManualTradeResult.STATUS_PENDING)
