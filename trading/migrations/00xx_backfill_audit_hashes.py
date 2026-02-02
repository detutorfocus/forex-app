# trading/migrations/00xx_backfill_audit_hashes.py
from django.db import migrations
import hashlib
import json


def canonical_json(data) -> str:
    return json.dumps(
        data or {},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def backfill(apps, schema_editor):

    try:
        TradeAuditEvent = apps.get_model("trading", "TradeAuditEvent")
    except LookupError:
        return  # model not present in this migration graph, skip safely

    trade_ids = (
        TradeAuditEvent.objects.order_by()
        .values_list("trade_id", flat=True)
        .distinct()
    )

    field_names = {f.name for f in TradeAuditEvent._meta.get_fields()}
    required = {"hash", "prev_hash"}  # adjust if yours differs
    if not required.issubset(field_names):
        return

    # No data? fine.
    qs = TradeAuditEvent.objects.all().order_by("id")
    if not qs.exists():
        return

    for trade_id in trade_ids:
        events = list(
            TradeAuditEvent.objects.filter(trade_id=trade_id).order_by("seq", "at", "id")
        )

        # Ensure seq is populated/continuous (only if needed)
        seq_counter = 0
        for e in events:
            if not e.seq:
                seq_counter += 1
                e.seq = seq_counter
                e.save(update_fields=["seq"])
            else:
                seq_counter = e.seq

        prev = ""
        for e in events:
            e.prev_hash = prev

            base = {
                "trade_id": e.trade_id,
                "seq": e.seq,
                "event_type": e.event_type,
                "at": e.at.isoformat(),
                "actor_id": e.actor_id,
                "ip": e.ip,
                "user_agent": e.user_agent,
                "request_id": e.request_id,
                "payload": e.payload,
                "prev_hash": e.prev_hash or "",
            }

            e.hash = sha256_hex(canonical_json(base))

            e.save(update_fields=["prev_hash", "hash"])
            prev = e.hash


class Migration(migrations.Migration):
    # IMPORTANT: replace this with YOUR real last migration name
    # Example: ("trading", "0007_add_audit_fields")
    dependencies = [
        ("trading", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
