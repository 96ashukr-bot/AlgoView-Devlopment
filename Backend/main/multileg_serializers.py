from __future__ import annotations

from rest_framework import serializers

from main.models import StrategyExecution, StrategyExecutionLog, StrategyLeg


class MultiLegExecuteSerializer(serializers.Serializer):
    strategy_name = serializers.ChoiceField(
        choices=[
            "BULL_CALL_SPREAD",
            "BEAR_CALL_SPREAD",
            "BEAR_PUT_SPREAD",
            "SHORT_STRADDLE",
            "LONG_CALL_BUTTERFLY",
            "SHORT_CALL_BUTTERFLY",
            "LONG_CALL_CONDOR",
            "SHORT_CALL_CONDOR",
            "LONG_IRON_CONDOR",
            "SHORT_IRON_BUTTERFLY",
            "CUSTOM_BASKET",
        ]
    )
    client_id = serializers.IntegerField(required=False)
    broker = serializers.CharField()
    underlying = serializers.CharField()
    expiry = serializers.CharField(required=False, allow_blank=True)
    lower_strike = serializers.FloatField(required=False)
    higher_strike = serializers.FloatField(required=False)
    quantity_lots = serializers.IntegerField(min_value=1)
    order_type = serializers.ChoiceField(choices=["LIMIT", "MARKET", "SL", "SL-M"], default="LIMIT")
    product_type = serializers.CharField(required=False, allow_blank=True, default="INTRADAY")
    buffer_percentage = serializers.FloatField(required=False)
    sell_leg_stop_loss_percentage = serializers.FloatField(required=False)
    combined_trailing_start = serializers.FloatField(required=False)
    combined_trailing_gap = serializers.FloatField(required=False)
    entry_time = serializers.CharField(required=False, allow_blank=True)
    exit_time = serializers.CharField(required=False, allow_blank=True)
    allow_reentry = serializers.BooleanField(required=False, default=False)
    idempotency_key = serializers.CharField(required=False, allow_blank=True)
    group_service = serializers.CharField(required=False, allow_blank=True)
    legs = serializers.ListField(child=serializers.DictField(), required=False)

    def validate(self, attrs):
        strategy_name = attrs.get("strategy_name")
        two_strike_strategies = {"BULL_CALL_SPREAD", "BEAR_CALL_SPREAD", "BEAR_PUT_SPREAD"}
        if strategy_name in two_strike_strategies:
            if attrs.get("lower_strike") is None or attrs.get("higher_strike") is None:
                raise serializers.ValidationError("This strategy requires lower_strike and higher_strike.")
        if strategy_name == "SHORT_STRADDLE" and attrs.get("lower_strike") is None:
            raise serializers.ValidationError("Short Straddle requires lower_strike as the ATM strike.")
        four_leg_strategies = {
            "LONG_CALL_BUTTERFLY",
            "SHORT_CALL_BUTTERFLY",
            "LONG_CALL_CONDOR",
            "SHORT_CALL_CONDOR",
            "LONG_IRON_CONDOR",
            "SHORT_IRON_BUTTERFLY",
        }
        if strategy_name in four_leg_strategies and not attrs.get("legs"):
            raise serializers.ValidationError("This strategy requires configured legs.")
        if strategy_name == "CUSTOM_BASKET" and not attrs.get("legs"):
            raise serializers.ValidationError("Custom multi-leg basket requires legs.")
        return attrs


class StrategyLegSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyLeg
        fields = [
            "id",
            "leg_name",
            "transaction_type",
            "option_type",
            "strike_price",
            "symbol",
            "token",
            "lot_size",
            "quantity",
            "order_type",
            "limit_price",
            "broker_order_id",
            "entry_price",
            "exit_price",
            "status",
            "pnl",
            "stop_loss",
            "exchange",
            "created_at",
            "updated_at",
        ]


class StrategyExecutionSerializer(serializers.ModelSerializer):
    legs = StrategyLegSerializer(many=True, read_only=True)

    class Meta:
        model = StrategyExecution
        fields = [
            "id",
            "client",
            "broker",
            "strategy_name",
            "underlying",
            "expiry",
            "status",
            "entry_time",
            "exit_time",
            "total_quantity",
            "combined_pnl",
            "max_pnl_seen",
            "trailing_stop_level",
            "exit_reason",
            "created_at",
            "updated_at",
            "legs",
        ]


class StrategyExecutionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyExecutionLog
        fields = ["id", "event_type", "message", "metadata", "created_at"]


class MultiLegExitSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="Manual exit")


class MultiLegKillSwitchSerializer(serializers.Serializer):
    client_id = serializers.IntegerField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True, default="Kill switch")
