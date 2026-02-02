import json
import time
from datetime import timedelta
from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.core.cache import cache

from django.conf import settings
from django.utils import timezone

from .models import NotificationPreference, NotificationDelivery
from notifications.models import PushSubscription
from pywebpush import webpush, WebPushException



def _cooldown_key(user_id: int, symbol: str, action: str) -> str:
    return f"alex_notify_cd:{user_id}:{symbol}:{action}"


def allow_notify_with_cooldown(user_id: int, symbol: str, action: str) -> bool:
    cooldown = int(getattr(settings, "ALEX_NOTIFY_COOLDOWN_SECONDS", 900))
    key = _cooldown_key(user_id, symbol, action)
    if cache.get(key):
        return False
    cache.set(key, int(time.time()), timeout=cooldown)
    return True


def get_or_create_prefs(user) -> NotificationPreference:
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    return prefs


def _within_cooldown(user, symbol: str, timeframe: str, cooldown_seconds: int) -> bool:
    if cooldown_seconds <= 0:
        return False
    cutoff = timezone.now() - timedelta(seconds=cooldown_seconds)
    return NotificationDelivery.objects.filter(
        user=user,
        symbol=symbol.upper(),
        timeframe=timeframe or "",
        created_at__gte=cutoff,
    ).exists()


def _over_hourly_limit(user, max_per_hour: int) -> bool:
    if max_per_hour <= 0:
        return False
    cutoff = timezone.now() - timedelta(hours=1)
    count = NotificationDelivery.objects.filter(user=user, created_at__gte=cutoff).count()
    return count >= max_per_hour


def should_notify(
    *,
    user,
    symbol: str,
    timeframe: str,
    timeframe_bucket: str,
    confidence: int,
    confirmed: bool,
    channel: str = "webpush",
) -> tuple[bool, str]:
    """
    The "LOCK": decide if user is allowed to receive this notification.
    Returns (ok, reason).
    """
    prefs = get_or_create_prefs(user)

    if not prefs.enabled:
        return False, "prefs_disabled"

    if channel == "webpush" and not prefs.webpush_enabled:
        return False, "webpush_disabled"

    if channel == "telegram" and not prefs.telegram_enabled:
        return False, "telegram_disabled"

    if prefs.confirmed_only and not confirmed:
        return False, "not_confirmed"

    if confidence < int(prefs.min_confidence or 0):
        return False, "confidence_too_low"

    allowed = prefs.allowed_symbols_set()
    if allowed and symbol.upper() not in allowed:
        return False, "symbol_not_allowed"

    if prefs.timeframe_bucket and prefs.timeframe_bucket != (timeframe_bucket or ""):
        return False, "timeframe_bucket_filtered"

    if _within_cooldown(user, symbol, timeframe, prefs.cooldown_seconds):
        return False, "cooldown_active"

    if _over_hourly_limit(user, prefs.max_per_hour):
        return False, "hourly_limit"

    return True, "ok"


def record_delivery(*, user, symbol: str, timeframe: str, channel: str = "webpush") -> None:
    NotificationDelivery.objects.create(
        user=user,
        symbol=symbol.upper(),
        timeframe=timeframe or "",
        channel=channel,
    )


def send_webpush_to_user(*, user, title: str, body: str, data: dict | None = None) -> bool:
    subs = PushSubscription.objects.filter(user=user)
    if not subs.exists():
        return False

    payload = json.dumps(
        {
            "title": title,
            "body": body,
            "data": data or {},
        }
    )

    vapid_private = getattr(settings, "VAPID_PRIVATE_KEY", "")
    vapid_claims = {"sub": getattr(settings, "VAPID_SUBJECT", "mailto:admin@example.com")}

    if not vapid_private:
        # Don’t crash prod — just skip sending
        return False

    ok_any = False
    for s in subs:
        try:
            webpush(
                subscription_info=s.as_webpush_dict(),
                data=payload,
                vapid_private_key=vapid_private,
                vapid_claims=vapid_claims,
            )
            ok_any = True
        except WebPushException:
            # optional: delete invalid endpoints
            # s.delete()
            pass

    return ok_any