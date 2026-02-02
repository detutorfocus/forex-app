from typing import Any, Dict, Optional

from django.db import transaction

from .models import Trade, TradeExecutionAudit
from .utils import json_safe  # if you created it; if not, I'll include a fallback below
from .mt5.service import MT5Service


def _to_float_or_none(v):
    if v in (None, "", "null"):
        return None
    return float(v)


@transaction.atomic
def execute_trade(request):
    data = request.data if hasattr(request, "data") else request.POST

    symbol = data.get("symbol")
    side = data.get("side")
    lot = data.get("lot")


    sl_raw = data.get("sl")
    tp_raw = data.get("tp")

    sl = float(sl_raw) if sl_raw not in (None, "", "null") else None
    tp = float(tp_raw) if tp_raw not in (None, "", "null") else None

    # optional
    max_slippage_pips = float(data.get("max_slippage_pips", 2.0))
    magic = int(data.get("magic", 900001))
    comment = str(data.get("comment", "SniperATR"))

    trade = Trade.objects.create(
        user=request.user,
        symbol=symbol,
        side=side,
        lot=float(lot),
        status="pending",
    )

    try:

        svc = MT5Service()

        result = svc.place_market_order(
            symbol=symbol,
            side=side,
            lot=float(lot),
            sl=sl,
            tp=tp,
            max_slippage_pips=max_slippage_pips,
            magic=magic,
            comment=comment,
        )

        if result.get("ok"):
            return {
                "ok": True,
                "trade_id": trade.id,
                "order_id": result.get("order"),
            }

        return {
            "ok": False,
            "error": result.get("error", "Order failed"),
        }


    except Exception as e:
        return {"ok": False, "error": "Trade execution failed", "details": str(e), "trade_id": trade.id}
