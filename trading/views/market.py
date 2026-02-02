from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .. import mt5
from ..mt5.service import get_market_tick

from ..mt5.service import MT5Service
from django.http import JsonResponse


class LiveMarketDataView(APIView):


    def get(self, request):
        symbol = request.query_params.get("symbol", "EURUSD")

        mt5_service = MT5Service()
        permission_classes = [IsAuthenticated]
        svc = MT5Service()
        svc._ensure_connected()
        tick = mt5.symbol_info_tick(symbol)
        try:
            data = mt5_service.get_symbol_tick(symbol)
            return Response({
                "status": "success",
                "data": data
            })
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=400)
@api_view(["GET"])
def mt5_market_view(request):
    symbol = request.GET.get("symbol", "EURUSD")
    data = get_market_tick(symbol)
    status = 200 if "error" not in data else data.get("status", 400)
    return Response(data, status=status)