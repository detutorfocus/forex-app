# trading/models.py
import uuid
from django.conf import settings
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone
import hashlib
import json

from django.apps import apps

SIDE_CHOICES = (
    ("buy", "BUY"),
    ("sell", "SELL"),
)

STATUS_CHOICES = (
    ("pending", "PENDING"),
    ("open", "OPEN"),
    ("closed", "CLOSED"),
    ("failed", "FAILED"),
)

class Trade(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trades",
        null=True,
        blank=True,
    )

    STATUS_PENDING = "pending"
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
        (STATUS_FAILED, "Failed"),
    )
    audit_seq = models.PositiveIntegerField(default=0, db_index=True)
    # used to allocate strict per-trade event ordering safely
    #audit_seq = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Trade#{self.pk} {getattr(self, 'symbol', '')}"

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)

    symbol = models.CharField(max_length=20, db_index=True)
    side = models.CharField(max_length=10, choices=SIDE_CHOICES)
    lot = models.DecimalField(max_digits=10, decimal_places=2)

    order_ticket = models.BigIntegerField(null=True, blank=True, unique=True, db_index=True)
    position_ticket = models.BigIntegerField(null=True, blank=True, unique=True, db_index=True)
    magic = models.IntegerField(default=900001)
    comment = models.CharField(max_length=64, blank=True, default="SniperATR-Live")

    entry_price = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    sl = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    tp = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending", db_index=True)

    opened_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    close_price = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    profit = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    raw_response = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.symbol} {self.side} {self.lot} ({self.status})"

    def mark_opened(self, price):
        self.status = "opened"
        self.entry_price = price
        self.opened_at = timezone.now()
        self.save(update_fields=["status", "entry_price", "opened_at"])

    def mark_closed(self, price, profit):
        self.status = "closed"
        self.close_price = price
        self.profit = profit
        self.closed_at = timezone.now()
        self.save(update_fields=[
            "status", "close_price", "profit", "closed_at"
            ])


        # (keep your existing fields)
        # Example fields (adjust to yours):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=32)
    side = models.CharField(max_length=8)  # buy/sell
    lot = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=32, default="pending")

        # Optional but recommended:
    correlation_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TradeAuditEvent(models.Model):
    payload = models.JSONField(default=dict, blank=True)
    """
    Append-only audit log: immutable, chronological per Trade.
    """

    action = models.CharField(max_length=32)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    hash = models.CharField(max_length=64, blank=True, default="")
    prev_hash = models.CharField(max_length=64, blank=True, default="")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    # Event types (add more as you like)
    CREATED = "created"
    VALIDATED = "validated"
    MT5_REQUEST_BUILT = "mt5_request_built"
    MT5_SEND_ATTEMPT = "mt5_send_attempt"
    MT5_RESULT = "mt5_result"
    TRADE_UPDATED = "trade_updated"
    ERROR = "error"

    EVENT_CHOICES = [
        (CREATED, "Created"),
        (VALIDATED, "Validated"),
        (MT5_REQUEST_BUILT, "MT5 Request Built"),
        (MT5_SEND_ATTEMPT, "MT5 Send Attempt"),
        (MT5_RESULT, "MT5 Result"),
        (TRADE_UPDATED, "Trade Updated"),
        (ERROR, "Error"),
    ]

    id = models.BigAutoField(primary_key=True)
    trade = models.ForeignKey("Trade", on_delete=models.CASCADE, related_name="audit_events")

    # Strict ordering per trade
    seq = models.PositiveIntegerField()

    event_type = models.CharField(max_length=64, choices=EVENT_CHOICES)
    at = models.DateTimeField(default=timezone.now, db_index=True)

    # Who/where (optional but pro)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="trade_audit_events"
    )

    class Meta:
        ordering = ["created_at"]

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    # Snapshots (JSON-safe dicts)
    request = models.JSONField(null=True, blank=True)
    response = models.JSONField(null=True, blank=True)
    meta = models.JSONField(null=True, blank=True)

    # Immutable enforcement flags
    _immutable = True


    class EventType(models.TextChoices):
        TRADE_CREATED = "TRADE_CREATED", "Trade created"
        VALIDATION_OK = "VALIDATION_OK", "Validation ok"
        VALIDATION_FAILED = "VALIDATION_FAILED", "Validation failed"

        MT5_CONNECT_START = "MT5_CONNECT_START", "MT5 connect start"
        MT5_CONNECT_OK = "MT5_CONNECT_OK", "MT5 connect ok"
        MT5_CONNECT_FAIL = "MT5_CONNECT_FAIL", "MT5 connect fail"

        SYMBOL_RESOLVE_START = "SYMBOL_RESOLVE_START", "Symbol resolve start"
        SYMBOL_RESOLVED = "SYMBOL_RESOLVED", "Symbol resolved"
        SYMBOL_NOT_FOUND = "SYMBOL_NOT_FOUND", "Symbol not found"
        SYMBOL_NOT_SELECTABLE = "SYMBOL_NOT_SELECTABLE", "Symbol not selectable"

        TICK_FETCH = "TICK_FETCH", "Tick fetch"
        PRICE_SELECTED = "PRICE_SELECTED", "Price selected"
        SLIPPAGE_COMPUTED = "SLIPPAGE_COMPUTED", "Slippage computed"

        ORDER_REQUEST_BUILT = "ORDER_REQUEST_BUILT", "Order request built"
        ORDER_SEND_ATTEMPT = "ORDER_SEND_ATTEMPT", "Order send attempt"
        ORDER_SEND_RESULT = "ORDER_SEND_RESULT", "Order send result"

        TRADE_STATUS_UPDATED = "TRADE_STATUS_UPDATED", "Trade status updated"
        ERROR = "ERROR", "Error"

       # TRADE_CREATED = "TRADE_CREATED", "Trade Created"
        TRADE_UPDATED = "TRADE_UPDATED", "Trade Updated"
        #ERROR = "ERROR", "Error"
        #MT5_CONNECT_START = "MT5_CONNECT_START", "MT5 Connect Start"
        #MT5_CONNECT_OK = "MT5_CONNECT_OK", "MT5 Connect OK"
        MT5_ORDER_REQUEST = "MT5_ORDER_REQUEST", "MT5 Order Request"
        MT5_ORDER_RESULT = "MT5_ORDER_RESULT", "MT5 Order Result"
        MT5_ORDER_FAILED = "MT5_ORDER_FAILED", "MT5 Order Failed"

    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name="audit_events")
    seq = models.PositiveIntegerField()  # strict ordering per trade
    event_type = models.CharField(max_length=64, choices=EventType.choices)
    at = models.DateTimeField(default=timezone.now, db_index=True)

    # Optional “who/where”
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    # JSON payload: safe place for MT5 request/response + extra context
    payload = models.JSONField(default=dict, blank=True)

    id = models.BigAutoField(primary_key=True)
    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name="audit_events")

    # Strict ordering per trade
    seq = models.PositiveIntegerField()

    event_type = models.CharField(max_length=64, choices=EventType.choices, db_index=True)
    at = models.DateTimeField(default=timezone.now, db_index=True)

    # Who/where (optional)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="trade_audit_events"
    )
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    # Correlation
    request_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    # Payload
    payload = models.JSONField(default=dict, blank=True)

    # Tamper-evidence (hash chaining)
    prev_hash = models.CharField(max_length=64, blank=True, default="")
    hash = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        unique_together = (("trade", "seq"),)
        indexes = [
            models.Index(fields=["trade", "seq"]),
            models.Index(fields=["event_type", "at"]),
        ]
        ordering = ["trade_id", "seq"]

    def __str__(self):
        return f"TradeAuditEvent(trade={self.trade_id}, seq={self.seq}, type={self.event_type})"

    @staticmethod
    def _canonical_json(data) -> str:
        # stable json for hashing
        return json.dumps(data or {}, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)

    def _compute_hash(self) -> str:
        base = {
            "trade_id": self.trade_id,
            "seq": self.seq,
            "event_type": self.event_type,
            "at": self.at.isoformat(),
            "actor_id": self.actor_id,
            "ip": self.ip,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "payload": self.payload,
            "prev_hash": self.prev_hash or "",
        }
        s = self._canonical_json(base)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def save(self, *args, **kwargs):
        """
        Append-only:
        - If pk exists => refuse updates (tamper protection)
        - For new rows => ensure seq & prev_hash are set, then compute hash
        """
        if self.pk:
            raise ValueError("TradeAuditEvent is append-only. Updates are not allowed.")

        with transaction.atomic():
            # Ensure seq if not set
            if not self.seq:
                last_seq = (
                    TradeAuditEvent.objects.select_for_update()
                    .filter(trade_id=self.trade_id)
                    .aggregate(models.Max("seq"))
                    .get("seq__max")
                )
                self.seq = (last_seq or 0) + 1

            # Set prev_hash from last event of same trade
            last = (
                TradeAuditEvent.objects.select_for_update()
                .filter(trade_id=self.trade_id)
                .order_by("-seq", "-id")
                .first()
            )
            self.prev_hash = last.hash if last else ""

            # Compute this event hash
            self.hash = self._compute_hash()

            super().save(*args, **kwargs)

class Meta:
    indexes = [
        models.Index(fields=["trade", "seq"]),
        models.Index(fields=["trade", "at"]),
        models.Index(fields=["event_type", "at"]),
    ]
    constraints = [
        models.UniqueConstraint(fields=["trade", "seq"], name="uniq_trade_seq"),
    ]
    ordering = ["trade_id", "seq"]

    def save(self, *args, **kwargs):
        # Block updates: append-only
        if self.pk is not None:
            raise RuntimeError("TradeAuditEvent is append-only. Updates are not allowed.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("TradeAuditEvent is append-only. Deletes are not allowed.")

class TradeExecutionAudit(models.Model):
    trade = models.ForeignKey("Trade", on_delete=models.CASCADE, related_name="audits")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    ok = models.BooleanField(default=False)
    action = models.CharField(max_length=32, default="execute")

    request_json = models.JSONField(null=True, blank=True)
    response_json = models.JSONField(null=True, blank=True)

    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]







