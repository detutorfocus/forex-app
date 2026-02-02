from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination

from trading.models import Trade
from trading.serializers import TradeHistorySerializer, TradeSerializer

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200

class TradeHistoryListView(generics.ListAPIView):
    """
    GET /trading/live/history/?status=open&symbol=GBPUSD
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TradeHistorySerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = Trade.objects.filter(user=self.request.user).order_by("-id")

        status_ = self.request.query_params.get("status")
        symbol = self.request.query_params.get("symbol")
        side = self.request.query_params.get("side")

        if status_:
            qs = qs.filter(status=status_)
        if symbol:
            qs = qs.filter(symbol__iexact=symbol)
        if side:
            qs = qs.filter(side__iexact=side)

        return qs


class TradeDetailView(generics.RetrieveAPIView):
    """
    GET /trading/live/trades/<id>/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TradeSerializer

    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user)
