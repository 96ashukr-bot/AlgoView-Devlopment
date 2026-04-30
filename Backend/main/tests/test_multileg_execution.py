from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone

from main.models import Broker, ClientBrokerdetails, ClientMultiLegStrategySetting, Strategies, StrategyExecution, StrategyLeg, User
from main.services.multileg_execution import (
    LegExecutionManager,
    MultiLegExecutionEngine,
    MultiLegExecutionError,
    MultiLegContractResolver,
    PnLMonitor,
    ResolvedContract,
    StrategyLegPlan,
    StrategyPlan,
    StrategyPlanBuilder,
)
from main.execution_engine import ExecutionEngine


TEST_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "multileg-tests"},
    "circuit_breaker": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "multileg-circuit"},
}


@override_settings(CACHES=TEST_CACHES)
class MultiLegExecutionTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email="multileg-client@example.com",
            firstName="Multi",
            lastName="Leg",
            phoneNumber="9000000001",
            password="Pass@1234",
            type_of_user="is_client",
            is_client=True,
            is_enable=True,
            client_status=True,
        )
        self.client_user.save(update_fields=["type_of_user", "is_client", "is_enable", "client_status"])

        self.admin_user = User.objects.create_user(
            email="multileg-admin@example.com",
            firstName="Admin",
            lastName="User",
            phoneNumber="9000000002",
            password="Pass@1234",
            is_staff=True,
        )

        self.broker = Broker.objects.create(broker_name="Angel One", is_active=True)
        self.broker_details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=self.broker,
            broker_API_KEY="api-key",
            broker_API_UID="A12345",
            broker_Demate_User_Name="A12345",
        )
        self.multi_leg_strategy = Strategies.objects.create(
            name="Bull Call Spread",
            execution_mode=Strategies.EXECUTION_MODE_MULTI_LEG,
            multi_leg_template=Strategies.MULTI_LEG_BULL_CALL_SPREAD,
            status=True,
        )
        self.client_user.Strategy.add(self.multi_leg_strategy)
        self.multi_leg_setting = ClientMultiLegStrategySetting.objects.create(
            client=self.client_user,
            strategy=self.multi_leg_strategy,
            broker="Angel One",
        )

        self.base_config = {
            "strategy_name": "BULL_CALL_SPREAD",
            "client_id": self.client_user.id,
            "broker": "Angel One",
            "underlying": "NIFTY",
            "expiry": "nearest",
            "lower_strike": 22500,
            "higher_strike": 22600,
            "quantity_lots": 1,
            "order_type": "LIMIT",
            "product_type": "INTRADAY",
            "buffer_percentage": 0.5,
            "sell_leg_stop_loss_percentage": 40,
            "combined_trailing_start": 1000,
            "combined_trailing_gap": 500,
            "entry_time": "09:30",
            "exit_time": "15:15",
            "allow_reentry": False,
        }

    def _contract(self, strike: float, option_type: str, *, symbol_suffix: str) -> ResolvedContract:
        expiry = timezone.now() + timezone.timedelta(days=1)
        return ResolvedContract(
            underlying="NIFTY",
            expiry=expiry,
            strike_price=strike,
            option_type=option_type,
            symbol=f"NIFTY{symbol_suffix}",
            token=f"TOKEN-{symbol_suffix}",
            lot_size=50,
            tick_size=0.05,
            exchange="NFO",
        )

    def _plan(self, *, idempotency_key: str = "idem-001") -> StrategyPlan:
        lower_contract = self._contract(22500, "CE", symbol_suffix="22500CE")
        higher_contract = self._contract(22600, "CE", symbol_suffix="22600CE")
        return StrategyPlan(
            strategy_name="BULL_CALL_SPREAD",
            client_id=self.client_user.id,
            broker="Angel One",
            underlying="NIFTY",
            expiry=lower_contract.expiry,
            quantity_lots=1,
            order_type="LIMIT",
            product_type="INTRADAY",
            buffer_percentage=0.5,
            sell_leg_stop_loss_percentage=40,
            combined_trailing_start=1000,
            combined_trailing_gap=500,
            entry_time="09:30",
            exit_time="15:15",
            allow_reentry=False,
            idempotency_key=idempotency_key,
            legs=[
                StrategyLegPlan(
                    leg_name="BUY_LOWER_CALL",
                    transaction_type="BUY",
                    option_type="CE",
                    strike_price=22500,
                    quantity=50,
                    order_type="LIMIT",
                    product_type="INTRADAY",
                    limit_price=101.5,
                    contract=lower_contract,
                ),
                StrategyLegPlan(
                    leg_name="SELL_HIGHER_CALL",
                    transaction_type="SELL",
                    option_type="CE",
                    strike_price=22600,
                    quantity=50,
                    order_type="LIMIT",
                    product_type="INTRADAY",
                    limit_price=51.5,
                    contract=higher_contract,
                ),
            ],
            raw_config=dict(self.base_config),
        )

    def _success_response(self, order_id: str, executed_price: float) -> dict:
        return {
            "status": "success",
            "data": {
                "status": "COMPLETE",
                "order_id": order_id,
                "executed_price": executed_price,
                "reference_price": executed_price,
                "ltp": executed_price,
            },
        }

    def _failed_response(self, *, message: str = "rejected") -> dict:
        return {"status": "error", "data": {"status": "FAILED", "message": message}}

    @mock.patch("main.services.multileg_execution.MultiLegContractResolver.resolve_option_contract")
    @mock.patch("main.services.multileg_execution.MultiLegContractResolver.resolve_expiry")
    def test_bull_call_spread_plan_generation(self, mock_resolve_expiry, mock_resolve_contract):
        expiry = timezone.now() + timezone.timedelta(days=1)
        mock_resolve_expiry.return_value = expiry
        mock_resolve_contract.side_effect = [
            self._contract(22500, "CE", symbol_suffix="22500CE"),
            self._contract(22600, "CE", symbol_suffix="22600CE"),
        ]

        plan = StrategyPlanBuilder().build(
            dict(self.base_config),
            client=self.client_user,
            broker_details=self.broker_details,
        )

        self.assertEqual(plan.strategy_name, "BULL_CALL_SPREAD")
        self.assertEqual(len(plan.legs), 2)
        self.assertEqual(plan.legs[0].transaction_type, "BUY")
        self.assertEqual(plan.legs[1].transaction_type, "SELL")
        self.assertEqual(plan.legs[0].quantity, 50)
        self.assertEqual(plan.total_quantity, 100)

    @mock.patch("main.services.multileg_execution.MultiLegContractResolver.resolve_option_contract")
    @mock.patch("main.services.multileg_execution.MultiLegContractResolver.resolve_expiry")
    def test_contract_resolution_keeps_same_expiry_and_lot_size(self, mock_resolve_expiry, mock_resolve_contract):
        expiry = timezone.now() + timezone.timedelta(days=2)
        first = self._contract(22500, "CE", symbol_suffix="22500CE")
        second = self._contract(22600, "CE", symbol_suffix="22600CE")
        mock_resolve_expiry.return_value = expiry
        mock_resolve_contract.side_effect = [first, second]

        plan = StrategyPlanBuilder().build(
            dict(self.base_config),
            client=self.client_user,
            broker_details=self.broker_details,
        )

        self.assertEqual(plan.expiry, expiry)
        self.assertEqual(plan.legs[0].contract.lot_size, plan.legs[1].contract.lot_size)
        self.assertEqual(plan.legs[0].contract.exchange, "NFO")

    @mock.patch("main.services.multileg_execution.load_upstox_instruments")
    def test_upstox_contract_resolution_supported_for_multileg(self, mock_load_upstox_instruments):
        expiry = timezone.now() + timezone.timedelta(days=1)
        mock_load_upstox_instruments.return_value = [
            {
                "trading_symbol": "NIFTY 22500 CE",
                "instrument_key": "NSE_FO|12345",
                "underlying_symbol": "NIFTY",
                "option_type": "CE",
                "strike_price": 22500,
                "expiry": int(expiry.timestamp() * 1000),
                "lot_size": 50,
                "tick_size": 0.05,
            }
        ]

        contract = MultiLegContractResolver().resolve_option_contract(
            broker_name="Upstox",
            underlying="NIFTY",
            strike_price=22500,
            option_type="CE",
            expiry=expiry,
            exchange="NFO",
        )

        self.assertEqual(contract.symbol, "NIFTY 22500 CE")
        self.assertEqual(contract.token, "NSE_FO|12345")
        self.assertEqual(contract.lot_size, 50)

    def test_successful_two_leg_execution_creates_active_strategy(self):
        engine = MultiLegExecutionEngine()
        plan = self._plan()

        with mock.patch.object(engine._plan_builder, "build", return_value=plan), \
             mock.patch.object(engine._risk_manager, "validate"), \
             mock.patch.object(
                 engine._leg_execution_manager,
                 "execute_leg",
                 side_effect=[
                     self._success_response("BUY-1", 100),
                     self._success_response("SELL-1", 50),
                 ],
             ):
            payload = engine.execute(config=dict(self.base_config), user=self.admin_user)

        self.assertEqual(payload["status"], StrategyExecution.STATUS_ACTIVE)
        self.assertEqual(len(payload["legs"]), 2)
        self.assertTrue(StrategyExecution.objects.filter(id=payload["id"], status=StrategyExecution.STATUS_ACTIVE).exists())

    def test_first_leg_success_second_leg_failure_rolls_back(self):
        engine = MultiLegExecutionEngine()
        plan = self._plan(idempotency_key="idem-rollback")
        rollback_mock = mock.Mock()

        with mock.patch.object(engine._plan_builder, "build", return_value=plan), \
             mock.patch.object(engine._risk_manager, "validate"), \
             mock.patch.object(
                 engine,
                 "_execute_leg_with_retry",
                 side_effect=[
                     self._success_response("BUY-1", 100),
                     self._failed_response(message="sell leg failed"),
                 ],
             ), \
             mock.patch.object(engine._rollback_manager, "rollback_completed_legs", rollback_mock):
            with self.assertRaises(MultiLegExecutionError):
                engine.execute(config=dict(self.base_config), user=self.admin_user)

        execution = StrategyExecution.objects.get(idempotency_key="idem-rollback")
        self.assertEqual(execution.status, StrategyExecution.STATUS_ROLLED_BACK)
        rollback_mock.assert_called_once()

    def test_failed_leg_persists_with_broker_error_message(self):
        engine = MultiLegExecutionEngine()
        plan = self._plan(idempotency_key="idem-leg-failure-detail")

        with mock.patch.object(engine._plan_builder, "build", return_value=plan), \
             mock.patch.object(engine._risk_manager, "validate"), \
             mock.patch.object(
                 engine,
                 "_execute_leg_with_retry",
                 return_value=self._failed_response(message="Insufficient margin for BUY leg"),
             ):
            with self.assertRaises(MultiLegExecutionError) as exc:
                engine.execute(config=dict(self.base_config), user=self.admin_user)

        self.assertIn("Insufficient margin for BUY leg", str(exc.exception))
        execution = StrategyExecution.objects.get(idempotency_key="idem-leg-failure-detail")
        leg = execution.legs.get(leg_name="BUY_LOWER_CALL")
        self.assertEqual(leg.status, StrategyLeg.STATUS_FAILED)
        self.assertEqual(leg.order_response["failure"]["data"]["message"], "Insufficient margin for BUY leg")
        self.assertTrue(
            execution.logs.filter(
                event_type="LEG_EXECUTION_FAILED",
                metadata__broker_message="Insufficient margin for BUY leg",
            ).exists()
        )

    def test_retry_logic_retries_until_success(self):
        engine = MultiLegExecutionEngine()
        plan = self._plan()
        execution = StrategyExecution.objects.create(
            client=self.client_user,
            broker="Angel One",
            strategy_name="BULL_CALL_SPREAD",
            underlying="NIFTY",
            expiry=plan.expiry,
            status=StrategyExecution.STATUS_EXECUTING,
            total_quantity=plan.total_quantity,
            idempotency_key="idem-retry",
            config_snapshot=dict(self.base_config),
        )
        responses = [
            self._failed_response(message="temporary broker issue"),
            self._success_response("BUY-RETRY", 101),
        ]

        with mock.patch.object(engine._leg_execution_manager, "execute_leg", side_effect=responses) as mocked_execute:
            response = engine._execute_leg_with_retry(
                client=self.client_user,
                broker_details=self.broker_details,
                plan=plan,
                execution=execution,
                leg_plan=plan.legs[0],
            )

        self.assertEqual(response["data"]["order_id"], "BUY-RETRY")
        self.assertEqual(mocked_execute.call_count, 2)

    def test_combined_pnl_calculation(self):
        execution = StrategyExecution.objects.create(
            client=self.client_user,
            broker="Angel One",
            strategy_name="BULL_CALL_SPREAD",
            underlying="NIFTY",
            expiry=timezone.now() + timezone.timedelta(days=1),
            status=StrategyExecution.STATUS_ACTIVE,
            total_quantity=100,
            idempotency_key="idem-pnl",
            config_snapshot=dict(self.base_config),
        )
        StrategyLeg.objects.create(
            strategy_execution=execution,
            leg_name="BUY_LOWER_CALL",
            transaction_type="BUY",
            option_type="CE",
            strike_price=22500,
            symbol="NIFTY22500CE",
            token="BUYTOKEN",
            lot_size=50,
            quantity=50,
            order_type="LIMIT",
            entry_price=Decimal("100"),
            status=StrategyLeg.STATUS_ACTIVE,
        )
        StrategyLeg.objects.create(
            strategy_execution=execution,
            leg_name="SELL_HIGHER_CALL",
            transaction_type="SELL",
            option_type="CE",
            strike_price=22600,
            symbol="NIFTY22600CE",
            token="SELLTOKEN",
            lot_size=50,
            quantity=50,
            order_type="LIMIT",
            entry_price=Decimal("50"),
            status=StrategyLeg.STATUS_ACTIVE,
        )

        monitor = PnLMonitor()
        with mock.patch.object(
            monitor._resolver,
            "fetch_ltp",
            side_effect=[112.0, 40.0],
        ):
            snapshot = monitor.refresh(execution, broker_details=self.broker_details)

        self.assertEqual(snapshot["combined_pnl"], 1100.0)
        execution.refresh_from_db()
        self.assertEqual(float(execution.combined_pnl), 1100.0)

    def test_sell_leg_stop_loss_exit_signal(self):
        execution = StrategyExecution.objects.create(
            client=self.client_user,
            broker="Angel One",
            strategy_name="BULL_CALL_SPREAD",
            underlying="NIFTY",
            expiry=timezone.now() + timezone.timedelta(days=1),
            status=StrategyExecution.STATUS_ACTIVE,
            total_quantity=100,
            idempotency_key="idem-sell-sl",
            config_snapshot=dict(self.base_config),
        )
        StrategyLeg.objects.create(
            strategy_execution=execution,
            leg_name="SELL_HIGHER_CALL",
            transaction_type="SELL",
            option_type="CE",
            strike_price=22600,
            symbol="NIFTY22600CE",
            token="SELLTOKEN",
            lot_size=50,
            quantity=50,
            order_type="LIMIT",
            entry_price=Decimal("50"),
            status=StrategyLeg.STATUS_ACTIVE,
        )

        monitor = PnLMonitor()
        with mock.patch.object(monitor._resolver, "fetch_ltp", return_value=71.0):
            snapshot = monitor.refresh(execution, broker_details=self.broker_details)

        self.assertTrue(snapshot["trigger_exit"])
        self.assertIn("Sell leg stop loss", snapshot["trigger_reason"])

    def test_trailing_pnl_exit_signal(self):
        execution = StrategyExecution.objects.create(
            client=self.client_user,
            broker="Angel One",
            strategy_name="BULL_CALL_SPREAD",
            underlying="NIFTY",
            expiry=timezone.now() + timezone.timedelta(days=1),
            status=StrategyExecution.STATUS_ACTIVE,
            total_quantity=50,
            combined_pnl=Decimal("700"),
            max_pnl_seen=Decimal("1600"),
            idempotency_key="idem-trail",
            config_snapshot=dict(self.base_config),
        )
        StrategyLeg.objects.create(
            strategy_execution=execution,
            leg_name="BUY_LOWER_CALL",
            transaction_type="BUY",
            option_type="CE",
            strike_price=22500,
            symbol="NIFTY22500CE",
            token="BUYTOKEN",
            lot_size=50,
            quantity=50,
            order_type="LIMIT",
            entry_price=Decimal("100"),
            status=StrategyLeg.STATUS_ACTIVE,
        )

        monitor = PnLMonitor()
        with mock.patch.object(monitor._resolver, "fetch_ltp", return_value=120.0):
            snapshot = monitor.refresh(execution, broker_details=self.broker_details)

        self.assertTrue(snapshot["trigger_exit"])
        self.assertEqual(snapshot["trigger_reason"], "Combined trailing P&L stop triggered")

    def test_time_exit_signal(self):
        execution = StrategyExecution.objects.create(
            client=self.client_user,
            broker="Angel One",
            strategy_name="BULL_CALL_SPREAD",
            underlying="NIFTY",
            expiry=timezone.now() + timezone.timedelta(days=1),
            status=StrategyExecution.STATUS_ACTIVE,
            total_quantity=50,
            idempotency_key="idem-time",
            config_snapshot={**self.base_config, "combined_trailing_start": None, "combined_trailing_gap": None, "exit_time": "10:00"},
        )
        StrategyLeg.objects.create(
            strategy_execution=execution,
            leg_name="BUY_LOWER_CALL",
            transaction_type="BUY",
            option_type="CE",
            strike_price=22500,
            symbol="NIFTY22500CE",
            token="BUYTOKEN",
            lot_size=50,
            quantity=50,
            order_type="LIMIT",
            entry_price=Decimal("100"),
            status=StrategyLeg.STATUS_ACTIVE,
        )

        fake_datetime = mock.Mock(wraps=datetime)
        fake_datetime.now.return_value = datetime(2026, 4, 27, 10, 30)

        monitor = PnLMonitor()
        with mock.patch.object(monitor._resolver, "fetch_ltp", return_value=100.0), \
             mock.patch("main.services.multileg_execution.datetime", fake_datetime):
            snapshot = monitor.refresh(execution, broker_details=self.broker_details)

        self.assertTrue(snapshot["trigger_exit"])
        self.assertEqual(snapshot["trigger_reason"], "Configured time exit triggered")

    def test_kill_switch_exits_all_active_strategies(self):
        engine = MultiLegExecutionEngine()
        first = StrategyExecution.objects.create(
            client=self.client_user,
            broker="Angel One",
            strategy_name="BULL_CALL_SPREAD",
            underlying="NIFTY",
            expiry=timezone.now() + timezone.timedelta(days=1),
            status=StrategyExecution.STATUS_ACTIVE,
            total_quantity=100,
            idempotency_key="idem-kill-1",
            config_snapshot=dict(self.base_config),
        )
        second = StrategyExecution.objects.create(
            client=self.client_user,
            broker="Angel One",
            strategy_name="BULL_CALL_SPREAD",
            underlying="BANKNIFTY",
            expiry=timezone.now() + timezone.timedelta(days=1),
            status=StrategyExecution.STATUS_ACTIVE,
            total_quantity=100,
            idempotency_key="idem-kill-2",
            config_snapshot=dict(self.base_config),
        )

        with mock.patch.object(engine._exit_manager, "exit_strategy", side_effect=lambda execution, **kwargs: execution) as mocked_exit:
            payload = engine.kill_switch(user=self.admin_user, client_id=self.client_user.id, reason="Emergency kill switch")

        self.assertCountEqual(payload["exited_strategy_ids"], [first.id, second.id])
        self.assertEqual(mocked_exit.call_count, 2)

    def test_no_reentry_blocks_duplicate_strategy(self):
        engine = MultiLegExecutionEngine()
        plan = self._plan(idempotency_key="idem-existing")
        StrategyExecution.objects.create(
            client=self.client_user,
            broker="Angel One",
            strategy_name=plan.strategy_name,
            underlying=plan.underlying,
            expiry=plan.expiry,
            status=StrategyExecution.STATUS_EXITED,
            total_quantity=plan.total_quantity,
            idempotency_key="past-execution",
            config_snapshot=dict(self.base_config),
        )

        with self.assertRaises(MultiLegExecutionError) as exc:
            engine._risk_manager._validate_no_reentry(plan, self.client_user)

        self.assertEqual(exc.exception.error_code, "REENTRY_DISABLED")

    def test_idempotency_duplicate_prevention(self):
        engine = MultiLegExecutionEngine()
        plan = self._plan(idempotency_key="idem-duplicate")

        with mock.patch.object(engine._plan_builder, "build", return_value=plan), \
             mock.patch.object(engine._risk_manager, "validate"), \
             mock.patch.object(
                 engine._leg_execution_manager,
                 "execute_leg",
                 side_effect=[
                     self._success_response("BUY-1", 100),
                     self._success_response("SELL-1", 50),
                 ],
             ) as mocked_execute:
            first = engine.execute(config=dict(self.base_config), user=self.admin_user)
            second = engine.execute(config=dict(self.base_config), user=self.admin_user)

        self.assertEqual(first["id"], second["id"])
        self.assertEqual(mocked_execute.call_count, 2)

    def test_unassigned_multileg_strategy_is_locked_for_client(self):
        engine = MultiLegExecutionEngine()
        ClientMultiLegStrategySetting.objects.filter(client=self.client_user).delete()
        self.client_user.Strategy.clear()
        plan = self._plan(idempotency_key="idem-locked")

        with mock.patch.object(engine._plan_builder, "build", return_value=plan):
            with self.assertRaises(MultiLegExecutionError) as exc:
                engine.execute(config=dict(self.base_config), user=self.admin_user)

        self.assertEqual(exc.exception.error_code, "MULTILEG_STRATEGY_LOCKED")

    def test_multileg_sell_entry_uses_direct_broker_order_not_legacy_exit(self):
        engine = ExecutionEngine()
        fyers_broker = Broker.objects.create(broker_name="FYERS", is_active=True)
        ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=fyers_broker,
            broker_API_KEY="FYERS-APP",
            access_token="FYERS-TOKEN",
        )
        plan = self._plan(idempotency_key="idem-fyers-sell-entry")
        sell_leg = plan.legs[1]
        fyers_plan = StrategyPlan(
            **{
                **plan.__dict__,
                "broker": "FYERS",
                "legs": [sell_leg],
            }
        )
        execution = StrategyExecution.objects.create(
            client=self.client_user,
            broker="FYERS",
            strategy_name=fyers_plan.strategy_name,
            underlying=fyers_plan.underlying,
            expiry=fyers_plan.expiry,
            status=StrategyExecution.STATUS_EXECUTING,
            total_quantity=sell_leg.quantity,
            idempotency_key="idem-fyers-entry",
            config_snapshot=dict(self.base_config),
        )
        request = LegExecutionManager()._build_execution_request(
            client=self.client_user,
            broker_details=self.broker_details,
            plan=fyers_plan,
            execution=execution,
            leg_plan=sell_leg,
            transaction_type="SELL",
            history_id_suffix="entry-1",
        )

        with mock.patch("main.execution_engine.place_fyers_orders", return_value=self._success_response("FYERS-SELL", 50)) as place_mock, \
             mock.patch("main.execution_engine.exit_existing_buy_position_fyers_order") as legacy_exit_mock:
            response = engine._execute_fyers(request)

        self.assertEqual(response["data"]["order_id"], "FYERS-SELL")
        place_mock.assert_called_once()
        legacy_exit_mock.assert_not_called()

    def test_broker_detail_resolution_accepts_aliases(self):
        engine = MultiLegExecutionEngine()
        paisa_broker = Broker.objects.create(broker_name="5Paisa", is_active=True)
        paisa_details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=paisa_broker,
            broker_API_KEY="key",
            broker_API_UID="uid",
            access_token="token",
        )

        resolved = engine._resolve_broker_details(self.client_user, "5 paisa")

        self.assertEqual(resolved.id, paisa_details.id)
