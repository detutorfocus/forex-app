from decimal import Decimal, InvalidOperation

from rest_framework.views import APIView

#from trading.mt5.service import MT5Service
from trading.constants import MAX_LOT, ALLOWED_SYMBOLS
from trading.models import Trade, TradeExecutionAudit
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from trading.utils import json_safe
from trading.mt5.service import MT5Service
from trading.models import Trade, TradeExecutionAudit
from trading.serializers import TradeSerializer, TradeAuditEventSerializer
from .._service_old import execute_trade
from trading.audit import AuditCtx
import csv
import json
from django.http import StreamingHttpResponse
from django.utils.timezone import is_aware
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from trading.models import TradeAuditEvent

@api_view(["GET"])
def market_live(request):
    return Response({"status": "ok", "message": "market live"})
ALLOWED_SYMBOLS = {"GBPUSD", "EURUSD", "USDJPY", "XAUUSD"}
MIN_LOT = Decimal("0.01")
MAX_LOT = Decimal("1.00")  # keep conservative for now


def _to_decimal(value, field_name: str):
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid {field_name}: {value}")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def execute_trade(request):
    symbol = request.data.get("symbol")
    side = request.data.get("side")
    lot = request.data.get("lot")

    if not symbol or not side or lot is None:
        return Response({"error": "symbol, side, lot are required"}, status=400)

    trade = Trade.objects.create(
        user=request.user,
        symbol=symbol,
        side=side,
        lot=float(lot),
        status=Trade.STATUS_PENDING,
    )

    data = request.data

    symbol = data.get("symbol")
    side = data.get("side")
    lot = data.get("lot")

    sl_raw = data.get("sl")
    tp_raw = data.get("tp")

    sl = float(sl_raw) if sl_raw not in (None, "", "null") else None
    tp = float(tp_raw) if tp_raw not in (None, "", "null") else None

    try:
        svc = MT5Service()
        result = svc.place_market_order(
            symbol=symbol,
            side=side,
            lot=float(lot),
            sl=sl,
            tp=tp,
            max_slippage_pips=2.0,
            magic=900001,
            comment="SniperATR",
        )

        TradeExecutionAudit.objects.create(
            trade=trade,
            user=request.user,
            ok=bool(result.get("ok")),
            action="execute",
            request_json=json_safe(result.get("request")),
            response_json=json_safe(result.get("raw") or result),
            error=result.get("error"),
        )

        # also update Trade status + ticket if ok
        if result.get("ok"):
            trade.status = "open"
            trade.order_ticket = result.get("order") or None
            trade.entry_price = result["request"]["price"]
        else:
            trade.status = "failed"

        trade.raw_response = json_safe(result)
        trade.save()

        # Expect result dict contains order + position (we’ll store both)
        trade.order_ticket = result.get("order") or result.get("order_ticket")
        trade.position_ticket = result.get("position") or result.get("position_ticket")
        trade.retcode = result.get("retcode")
        trade.mt5_comment = result.get("comment") or result.get("details")

        # Mark open if position ticket exists
        trade.status = Trade.STATUS_OPEN if trade.position_ticket else Trade.STATUS_PENDING
        trade.save()

        return Response({"trade_id": trade.id, "mt5": result}, status=200)


    except Exception as e:

        return Response(

            {"ok": False, "error": "Trade execution failed", "details": str(e)},

            status=status.HTTP_400_BAD_REQUEST,

        )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def trade_list(request):
    """
    GET /trading/live/trades/
    Lists the authenticated user's trades (latest first)
    """
    qs = Trade.objects.filter(user=request.user).order_by("-created_at")[:100]
    data = [
        {
            "id": t.id,
            "symbol": t.symbol,
            "side": t.side,
            "lot": str(t.lot),
            "ticket": t.ticket,
            "status": t.status,
            "entry_price": str(t.entry_price) if t.entry_price is not None else None,
            "sl": str(t.sl) if t.sl is not None else None,
            "tp": str(t.tp) if t.tp is not None else None,
            "created_at": t.created_at.isoformat(),
        }
        for t in qs
    ]
    return Response({"results": data})
def _to_float_or_none(value, field):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {field}: {value}")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def close_trade(request):
    ticket = request.data.get("ticket")
    if not ticket:
        return Response({"error": "ticket is required"}, status=400)

    ticket = int(ticket)

    try:
        svc = MT5Service()
        result = svc.close_position(ticket)

        # Update trade record for this user (if we have it)
        trade = Trade.objects.filter(user=request.user, position_ticket=ticket).order_by("-created_at").first()
        if trade:
            trade.status = Trade.STATUS_CLOSED
            trade.closed_at = timezone.now()
            trade.retcode = result.get("retcode", trade.retcode)
            trade.mt5_comment = result.get("comment") or "closed"
            trade.profit = result.get("profit")  # optional if you add it later
            trade.save()

        return Response({"ticket": ticket, "mt5": result, "trade_id": trade.id if trade else None}, status=200)

    except ValueError as e:
        # position not found etc.
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Close failed", "details": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def modify_trade(request):
    if not getattr(settings, "TRADING_ENABLED", True):
        return Response({"error": "Trading is disabled"}, status=403)

    data = request.data or {}
    ticket = data.get("ticket")

    if not ticket:
        return Response({"error": "ticket is required"}, status=400)

    sl = _to_float_or_none(data.get("sl"), "sl")
    tp = _to_float_or_none(data.get("tp"), "tp")

    if sl is None and tp is None:
        return Response({"error": "Provide sl and/or tp"}, status=400)

    svc = MT5Service()
    result = svc.modify_position_sl_tp(int(ticket), sl=sl, tp=tp)

    trade = Trade.objects.filter(ticket=int(ticket), user=request.user).first()
    if trade:
        if sl is not None:
            trade.sl = sl
        if tp is not None:
            trade.tp = tp
        trade.raw_response = {"modify_result": result}
        trade.save()

    return Response({"message": "Trade modified", "ticket": int(ticket)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def emergency_close_all(request):
    if not getattr(settings, "TRADING_ENABLED", True):
        return Response({"error": "Trading is disabled"}, status=403)

    svc = MT5Service()
    result = svc.close_all_positions()

    Trade.objects.filter(user=request.user, status="open").update(
        status="closed",
        closed_at=timezone.now()
    )

    return Response({"message": "Emergency close all executed", "result": result})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def close_trade(request):
    data = request.data or {}
    ticket = data.get("ticket")

    if not ticket:
        return Response({"error": "ticket is required", "status": 400}, status=400)

    svc = MT5Service()
    result = svc.close_position_by_ticket(int(ticket))

    #  CRITICAL: never crash if service returns None
    if result is None:
        return Response(
            {"error": "close_position_by_ticket returned None", "status": 500},
            status=500
        )

    status_code = int(result.get("status", 200))
    return Response(result, status=status_code)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def live_orders(request):
    symbol = request.query_params.get("symbol")
    svc = MT5Service()
    data = svc.list_orders(symbol=symbol)
    return Response({"count": len(data), "orders": data})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def trade_history(request):
    qs = Trade.objects.filter(user=request.user).order_by("-created_at")
    return Response(TradeSerializer(qs, many=True).data)

@api_view(["GET"])
def live_positions(request):
    return Response({"status": "ok", "message": "live_positions endpoint placeholder"})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def execute_trade_view(request):
    result = execute_trade(user=request.user, data=request.data)
    return Response(result)



mt5_service = MT5Service()

def _audit_ctx_from_request(request) -> AuditCtx:
    user = getattr(request, "user", None)
    actor_id = user.id if user and user.is_authenticated else None
    ip = request.META.get("REMOTE_ADDR")
    ua = request.META.get("HTTP_USER_AGENT")
    return AuditCtx(actor_id=actor_id, ip=ip, user_agent=ua)


class LiveExecuteView(APIView):
    def post(self, request):
        data = request.data

        # 1Extract inputs
        symbol = data.get("symbol")
        side = data.get("side")
        lot = data.get("lot")

        if not symbol or not side or not lot:
            return Response(
                {"ok": False, "error": "symbol, side and lot are required"},
                status=400,
            )

        # 2 Create trade FIRST (needed for audit trail)
        trade = Trade.objects.create(
            user=request.user,
            symbol=symbol,
            side=side,
            lot=float(lot),
            status=Trade.Status.PENDING,
        )

        # 3Build audit context
        ctx = _audit_ctx_from_request(request)

        # 4Execute via MT5 service
        result = mt5_service.place_market_order(
            trade=trade,
            symbol=symbol,
            side=side,
            lot=float(lot),
            ctx=ctx,
        )

        return Response(result)

class Echo:
    """CSV streaming helper"""
    def write(self, value):
        return value


class AuditExportView(APIView):
    permission_classes = [IsAdminUser]

    def get_queryset(self, request):
        qs = TradeAuditEvent.objects.select_related("trade", "actor").order_by("trade_id", "seq", "id")

        trade_id = request.query_params.get("trade_id")
        request_id = request.query_params.get("request_id")
        event_type = request.query_params.get("event_type")

        if trade_id:
            qs = qs.filter(trade_id=trade_id)
        if request_id:
            qs = qs.filter(request_id=request_id)
        if event_type:
            qs = qs.filter(event_type=event_type)

        return qs

    def get(self, request):
        fmt = (request.query_params.get("format") or "json").lower().strip()
        qs = self.get_queryset(request)

        if fmt == "csv":
            return self._csv_response(qs)

        # default JSON
        ser = TradeAuditEventSerializer(qs, many=True)
        return Response(ser.data)

    def _csv_response(self, qs):
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)

        header = [
            "id", "trade_id", "seq", "event_type", "at",
            "actor_id", "ip", "user_agent", "request_id",
            "payload_json", "prev_hash", "hash",
        ]

        def row_iter():
            yield writer.writerow(header)
            for e in qs.iterator(chunk_size=2000):
                at_val = e.at.isoformat()
                payload_json = json.dumps(e.payload or {}, ensure_ascii=False)

                yield writer.writerow([
                    e.id,
                    e.trade_id,
                    e.seq,
                    e.event_type,
                    at_val,
                    e.actor_id,
                    e.ip or "",
                    e.user_agent or "",
                    e.request_id or "",
                    payload_json,
                    e.prev_hash or "",
                    e.hash or "",
                ])

        resp = StreamingHttpResponse(row_iter(), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="trade_audit_events.csv"'
        return resp