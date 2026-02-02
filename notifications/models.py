# notifications/models.py
from __future__ import annotations

from django.conf import settings
from django.db import models


class NotificationPreference(models.Model):
    """
    Locking means: when locked=True, user cannot change channels from client.
    (Only admin/server can unlock.)
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )

    # Channels
    webpush_enabled = models.BooleanField(default=True)
    telegram_enabled = models.BooleanField(default=False)

    # What to notify about
    signal_alerts_enabled = models.BooleanField(default=True)
    execution_alerts_enabled = models.BooleanField(default=True)

    # Lock switch
    locked = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"NotificationPreference(user_id={self.user_id}, locked={self.locked})"


class PushSubscription(models.Model):
    """
    One row per device/browser subscription.
    endpoint must be unique per browser subscription.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )

    endpoint = models.TextField(unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)

    user_agent = models.CharField(max_length=256, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def as_webpush_dict(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "keys": {"p256dh": self.p256dh, "auth": self.auth},
        }

    def __str__(self) -> str:
        return f"PushSubscription(user_id={self.user_id})"


class SignalEvent(models.Model):
    """
    Stores Alex signals so we can notify + audit later.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="signal_events",
    )
    symbol = models.CharField(max_length=32)
    timeframe = models.CharField(max_length=16)
    action = models.CharField(max_length=8)  # BUY/SELL/WAIT
    confidence = models.IntegerField(default=0)

    sl = models.FloatField(null=True, blank=True)
    tp1 = models.FloatField(null=True, blank=True)
    tp2 = models.FloatField(null=True, blank=True)
    tp3 = models.FloatField(null=True, blank=True)

    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"SignalEvent({self.symbol} {self.timeframe} {self.action})"


class NotificationDelivery(models.Model):
    """
    Optional audit of outgoing notifications (per channel).
    """
    CHANNEL_CHOICES = (
        ("WEBPUSH", "WEBPUSH"),
        ("TELEGRAM", "TELEGRAM"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_deliveries",
    )
    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES)
    title = models.CharField(max_length=120)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)

    ok = models.BooleanField(default=False)
    error = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
