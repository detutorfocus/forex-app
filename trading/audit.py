from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Dict

from django.db import transaction

from .models import Trade, TradeAuditEvent


@dataclass
class AuditCtx:
    actor_id: Optional[int] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None


def audit_event(
    trade: Trade,
    event_type: str,
    payload: Optional[Dict[str, Any]] = None,
    ctx: Optional[AuditCtx] = None,
) -> TradeAuditEvent:
    """
    Append-only, strict per-trade sequence, race-safe.
    """
    payload = payload or {}
    ctx = ctx or AuditCtx()

    with transaction.atomic():
        # Lock the trade row to allocate the next seq safely
        locked = Trade.objects.select_for_update().get(pk=trade.pk)
        locked.audit_seq += 1
        seq = locked.audit_seq
        locked.save(update_fields=["audit_seq"])

        ev = TradeAuditEvent.objects.create(
            trade=locked,
            seq=seq,
            event_type=event_type,
            payload=payload,
            actor_id=ctx.actor_id,
            ip_address=ctx.ip,
            user_agent=ctx.user_agent,
        )
        return ev
