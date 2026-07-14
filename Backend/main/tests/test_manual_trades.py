from datetime import datetime, timedelta, timezone as datetime_timezone
from unittest import mock

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from main.models import (
    Broker, ClientBrokerdetails, ClientTradeSetting, ExecutionNode, GroupService,
    ManualTradeBatch, ManualTradeResult, Role, Segment, SubSegment, User,
)
from main.manual_trade_service import _build_execution_request


class ManualTradeTests(APITestCase):
    def setUp(self):
        admin_role, _ = Role.objects.get_or_create(name="Admin")
        self.subadmin_role, _ = Role.objects.get_or_create(name="Sub-Admin")
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

    def test_subadmin_without_trade_execution_access_cannot_preview(self):
        subadmin = User.objects.create_user(
            email="manual-subadmin-denied@example.com",
            firstName="Manual",
            lastName="Subadmin",
            phoneNumber="9330000004",
            password="Pass@123",
            role=self.subadmin_role,
            type_of_user="is_user",
            can_place_manual_trades=False,
        )
        self.client_user.assigned_client = subadmin
        self.client_user.save(update_fields=["assigned_client"])
        self.client.force_authenticate(subadmin)

        response = self.client.post(reverse("manual-trade-preview"), {
            "group_service_id": self.group.id, "symbol": "NIFTY",
            "action": "BUY_CE", "strike_price": "22900",
        }, format="json")

        self.assertEqual(response.status_code, 403)

    def test_enabled_subadmin_can_preview_assigned_clients(self):
        subadmin = User.objects.create_user(
            email="manual-subadmin-allowed@example.com",
            firstName="Manual",
            lastName="Subadmin",
            phoneNumber="9330000005",
            password="Pass@123",
            role=self.subadmin_role,
            type_of_user="is_user",
            can_place_manual_trades=True,
        )
        self.client_user.assigned_client = subadmin
        self.client_user.save(update_fields=["assigned_client"])
        self.client.force_authenticate(subadmin)

        response = self.client.post(reverse("manual-trade-preview"), {
            "group_service_id": self.group.id, "symbol": "NIFTY",
            "action": "BUY_CE", "strike_price": "22900",
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["preview_count"], 1)
        self.assertEqual(response.data["results"][0]["client_id"], self.client_user.id)

    def test_enabled_subadmin_group_service_list_is_scoped_to_assigned_clients(self):
        subadmin = User.objects.create_user(
            email="manual-subadmin-groups@example.com",
            firstName="Manual",
            lastName="Subadmin",
            phoneNumber="9330000010",
            password="Pass@123",
            role=self.subadmin_role,
            type_of_user="is_user",
            can_place_manual_trades=True,
        )
        other_group = GroupService.objects.create(
            group_name="Other Manual Group",
            segment=self.group.segment,
            json_data=[{"ScriptName": "BANKNIFTY"}],
        )
        User.objects.create_user(
            email="manual-other-group-client@example.com",
            firstName="Other",
            lastName="Group",
            phoneNumber="9330000011",
            password="Pass@123",
            role=self.client_user.role,
            Group_service=other_group,
            type_of_user="is_client",
            is_client="True",
        )
        self.client_user.assigned_client = subadmin
        self.client_user.save(update_fields=["assigned_client"])
        self.client.force_authenticate(subadmin)

        response = self.client.get(reverse("group-view-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [self.group.id])

    def test_enabled_subadmin_cannot_open_unassigned_trade_execution_batch(self):
        subadmin = User.objects.create_user(
            email="manual-subadmin-scoped@example.com",
            firstName="Scoped",
            lastName="Subadmin",
            phoneNumber="9330000006",
            password="Pass@123",
            role=self.subadmin_role,
            type_of_user="is_user",
            can_place_manual_trades=True,
        )
        other_client = User.objects.create_user(
            email="manual-other-client@example.com",
            firstName="Other",
            lastName="Client",
            phoneNumber="9330000007",
            password="Pass@123",
            role=self.client_user.role,
            Group_service=self.group,
            type_of_user="is_client",
            is_client="True",
        )
        batch = ManualTradeBatch.objects.create(
            requested_by=self.admin,
            group_service=self.group,
            symbol="NIFTY",
            action=ManualTradeBatch.ACTION_BUY_CE,
            strike_price="22900",
            idempotency_key="manual-scope-test",
            preview_count=1,
            eligible_count=1,
        )
        ManualTradeResult.objects.create(batch=batch, client=other_client, status=ManualTradeResult.STATUS_PENDING)
        self.client.force_authenticate(subadmin)

        response = self.client.get(reverse("manual-trade-detail", args=[batch.id]))

        self.assertEqual(response.status_code, 404)

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

    def test_midnight_ist_expiry_does_not_shift_to_previous_utc_date(self):
        self.setting.expiry_date = datetime(2026, 7, 13, 18, 30, tzinfo=datetime_timezone.utc)
        self.setting.save(update_fields=["expiry_date", "updated_at"])
        response = self.client.post(reverse("manual-trade-preview"), {
            "group_service_id": self.group.id, "symbol": "NIFTY",
            "action": "BUY_CE", "strike_price": "22900",
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["results"][0]["request_snapshot"]["expiry_date"], "2026-07-14")
        result = ManualTradeResult.objects.select_related("batch", "trade_setting", "client").get(
            id=response.data["results"][0]["id"]
        )
        request = _build_execution_request(result)
        self.assertEqual(request.order_params["expiry"], "2026-07-14")
        self.assertEqual((request.day, request.month, request.year), ("14", "Jul", "26"))

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
