import csv
import json
from django.http import StreamingHttpResponse, JsonResponse
from django.utils import timezone
from rest_framework.views import APIView
from trading.models import TradeAuditEvent
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

class Echo:
    def write(self, value):
        return value


def _get_format(request) -> str:
    qp = getattr(request, "query_params", None)  # DRF Request has query_params
    if qp is not None:
        fmt = qp.get("format", "json")
    else:
        fmt = request.GET.get("format", "json")  # Django request uses GET
    return (fmt or "json").lower()


def audit_export(request):
    fmt = _get_format(request)

    qs = (
        TradeAuditEvent.objects
        .select_related("trade")
        .order_by("trade_id", "seq")
    )

    if fmt == "csv":
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)

        def row_iter():
            yield writer.writerow([
                "id", "trade_id", "seq", "event_type", "at",
                "actor_id", "ip", "user_agent", "request_id",
                "payload", "hash", "prev_hash",
            ])

            for e in qs.iterator(chunk_size=2000):
                yield writer.writerow([
                    e.id,
                    e.trade_id,
                    e.seq,
                    e.event_type,
                    e.at.isoformat() if e.at else "",
                    e.actor_id or "",
                    e.ip or "",
                    e.user_agent or "",
                    e.request_id or "",
                    json.dumps(e.payload or {}, ensure_ascii=False),
                    e.hash or "",
                    e.prev_hash or "",
                ])

        filename = f"audit_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        resp = StreamingHttpResponse(row_iter(), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp

    # default JSON
    data = [
        {
            "id": e.id,
            "trade_id": e.trade_id,
            "seq": e.seq,
            "event_type": e.event_type,
            "at": e.at.isoformat() if e.at else None,
            "actor_id": e.actor_id,
            "ip": e.ip,
            "user_agent": e.user_agent,
            "request_id": e.request_id,
            "payload": e.payload,
            "hash": e.hash,
            "prev_hash": e.prev_hash,
        }
        for e in qs[:5000]  # safety cap
    ]
    return JsonResponse({"count": qs.count(), "results": data})

class AuditVerifyView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Verify hash chaining integrity per trade.
        Returns first broken event (if any).
        """
        trade_id = request.query_params.get("trade_id")
        qs = TradeAuditEvent.objects.all().order_by("trade_id", "seq", "id")
        if trade_id:
            qs = qs.filter(trade_id=trade_id)

        broken = []
        last_by_trade = {}

        for e in qs.iterator(chunk_size=2000):
            prev = last_by_trade.get(e.trade_id)
            expected_prev_hash = prev.event_hash if prev else None

            if e.prev_hash != expected_prev_hash:
                broken.append({
                    "trade_id": e.trade_id,
                    "event_id": e.id,
                    "seq": e.seq,
                    "expected_prev_hash": expected_prev_hash,
                    "actual_prev_hash": e.prev_hash,
                })
                break

            last_by_trade[e.trade_id] = e

        return Response({
            "ok": len(broken) == 0,
            "broken": broken[:1],
        })