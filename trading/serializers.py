from rest_framework import serializers
from .models import Trade
from .models import TradeAuditEvent

class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = "__all__"
        read_only_fields = ("user", "created_at", "closed_at")

class TradeHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = [
            "id",
            "symbol",
            "side",
            "lot",
            "status",
            "order_ticket",
            "entry_price",
            "close_price",
            "profit",
            "opened_at",
            "closed_at",
        ]

class TradeAuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeAuditEvent
        fields = [
            "id",
            "trade",
            "seq",
            "event_type",
            "at",
            "actor",
            "ip",
            "user_agent",
            "request_id",
            "payload",
            "prev_hash",
            "hash",
        ]
